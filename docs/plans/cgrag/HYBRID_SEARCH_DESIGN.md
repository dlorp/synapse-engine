# Hybrid Search Implementation Design
# Vector + BM25 for S.Y.N.A.P.S.E. ENGINE CGRAG

**Date:** 2025-11-30
**Status:** Implementation Ready
**Estimated Time:** 1-2 weeks
**Priority:** HIGH (Phase 1 of CGRAG Enhancement Plan)

---

## Executive Summary

This design integrates BM25 keyword search with existing FAISS vector search to create a hybrid retrieval system optimized for code and technical queries. Based on global research findings:

- **Chinese Research:** Hybrid search improves code/technical query accuracy by +15-20%
- **Japanese Research:** Proper BM25 tuning with tokenization is critical (avoid naive combinations)
- **Russian Research:** Phase 2 hybrid optimization yields +15-25% accuracy improvement

**Expected Results:**
- **Accuracy:** +15-20% for code/technical queries
- **Latency:** <65ms (down from <100ms current)
- **Code Queries:** Significant improvement for function/class/symbol lookups
- **Technical Docs:** Better keyword matching for API documentation

**Performance Strategy:**
- Parallel execution of vector + BM25 searches
- Redis caching for BM25 tokenization
- Async I/O throughout
- Early termination for budget constraints

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [BM25 Implementation Strategy](#bm25-implementation-strategy)
3. [Fusion Strategy: Reciprocal Rank Fusion](#fusion-strategy-reciprocal-rank-fusion)
4. [Code-Specific Optimizations](#code-specific-optimizations)
5. [Performance Optimizations](#performance-optimizations)
6. [Implementation Plan](#implementation-plan)
7. [Code Examples](#code-examples)
8. [Testing Strategy](#testing-strategy)
9. [Migration Path](#migration-path)

---

## Architecture Overview

### Current Architecture

```
Query → CGRAGRetriever → FAISS Search → Relevance Filter → Token Packing → Results
           ↓
      Embedding
```

### New Hybrid Architecture

```
Query → HybridRetriever ──┬→ FAISS Search (Vector)
           ↓               │
      Embedding            └→ BM25 Search (Keyword)
                                    ↓
                           Reciprocal Rank Fusion
                                    ↓
                           Relevance Filter → Token Packing → Results
```

### Design Principles

1. **Backward Compatibility:** Existing FAISS-only mode still supported via flag
2. **Parallel Execution:** Vector and BM25 searches run concurrently
3. **Graceful Degradation:** If BM25 fails, fall back to vector-only
4. **Minimal Latency Impact:** Target <15ms BM25 overhead
5. **Memory Efficiency:** Shared tokenizer, cached preprocessed docs

---

## BM25 Implementation Strategy

### Library Choice: rank_bm25

**Decision:** Use `rank_bm25` library

**Rationale:**
- ✅ Pure Python, no C dependencies (Docker-friendly)
- ✅ BM25Okapi variant (state-of-the-art)
- ✅ Fast enough for <100k documents
- ✅ Simple API, easy to integrate
- ✅ 4.8M+ downloads/month, well-maintained

**Alternatives Considered:**
- ❌ Whoosh: Overhead of full-text search engine, slower
- ❌ Custom BM25: Reinventing the wheel, not worth time
- ❌ Elasticsearch: Too heavyweight for local deployment

### Index Structure

```python
from dataclasses import dataclass
from typing import List, Dict
from rank_bm25 import BM25Okapi
import pickle
from pathlib import Path

@dataclass
class BM25Index:
    """BM25 index structure saved alongside FAISS index"""

    bm25: BM25Okapi
    chunk_ids: List[str]  # Maps BM25 doc index → chunk ID
    tokenizer_config: Dict[str, any]  # Tokenization settings

    def save(self, path: Path) -> None:
        """Save BM25 index to disk"""
        with open(path, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'chunk_ids': self.chunk_ids,
                'tokenizer_config': self.tokenizer_config
            }, f)

    @classmethod
    def load(cls, path: Path) -> 'BM25Index':
        """Load BM25 index from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return cls(
            bm25=data['bm25'],
            chunk_ids=data['chunk_ids'],
            tokenizer_config=data['tokenizer_config']
        )
```

### Tokenization Strategy

#### For Code Files (.py, .js, .ts, etc.)

**Strategy:** AST-aware tokenization with symbol preservation

```python
import re
from typing import List

class CodeAwareTokenizer:
    """Tokenizer optimized for code with symbol preservation"""

    # Patterns for code symbols
    CAMEL_CASE_PATTERN = re.compile(r'([a-z])([A-Z])')
    SNAKE_CASE_PATTERN = re.compile(r'_')
    SYMBOL_PATTERN = re.compile(r'[\w]+')

    def tokenize(self, text: str, language: str = None) -> List[str]:
        """Tokenize code-aware text

        Args:
            text: Text to tokenize
            language: Programming language (python, javascript, etc.)

        Returns:
            List of tokens optimized for code search
        """
        tokens = []

        # 1. Extract all alphanumeric symbols
        symbols = self.SYMBOL_PATTERN.findall(text)

        for symbol in symbols:
            # Add original symbol
            tokens.append(symbol.lower())

            # 2. Split CamelCase: getUserName → get, user, name, getUserName
            if self._is_camel_case(symbol):
                sub_tokens = self._split_camel_case(symbol)
                tokens.extend(sub_tokens)

            # 3. Split snake_case: get_user_name → get, user, name, get_user_name
            if '_' in symbol:
                sub_tokens = symbol.split('_')
                tokens.extend([t.lower() for t in sub_tokens if t])

        # 4. Add lowercase version of entire text for phrase matching
        tokens.extend(text.lower().split())

        return tokens

    def _is_camel_case(self, text: str) -> bool:
        """Check if text is in CamelCase format"""
        return bool(self.CAMEL_CASE_PATTERN.search(text))

    def _split_camel_case(self, text: str) -> List[str]:
        """Split CamelCase into parts: getUserName → [get, user, name]"""
        # Insert space before capitals
        spaced = self.CAMEL_CASE_PATTERN.sub(r'\1 \2', text)
        return [t.lower() for t in spaced.split()]
```

**Example Tokenization:**

```python
# Input code chunk:
"""
async def get_user_profile(user_id: str) -> UserProfile:
    return await UserRepository.fetch_by_id(user_id)
"""

# Tokens produced:
[
    # Original symbols
    'async', 'def', 'get_user_profile', 'user_id', 'str', 'userprofile',
    'return', 'await', 'userrepository', 'fetch_by_id',

    # CamelCase splits
    'user', 'profile',  # from UserProfile
    'repository',       # from UserRepository
    'fetch', 'by', 'id',  # from fetch_by_id

    # snake_case splits
    'get', 'user', 'profile',  # from get_user_profile
    'user', 'id',              # from user_id
    'fetch', 'by', 'id'        # from fetch_by_id
]
```

**Benefits:**
- ✅ Query "user profile" matches `UserProfile` class
- ✅ Query "fetch user" matches `fetch_by_id` method
- ✅ Query "get_user_profile" matches exact function name
- ✅ Query "getUserProfile" matches snake_case equivalent

#### For Documentation Files (.md, .txt, .rst)

**Strategy:** Standard word tokenization with stop word preservation

```python
class DocumentTokenizer:
    """Tokenizer for natural language documentation"""

    # Keep common technical stop words that matter in docs
    PRESERVE_STOPWORDS = {
        'api', 'http', 'get', 'post', 'put', 'delete', 'patch',
        'async', 'await', 'return', 'class', 'function', 'method',
        'import', 'export', 'from', 'to', 'with', 'by'
    }

    def tokenize(self, text: str) -> List[str]:
        """Tokenize documentation text

        Args:
            text: Documentation text

        Returns:
            List of tokens
        """
        # Lowercase and split on whitespace/punctuation
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)

        # Remove generic stop words but keep technical ones
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english')) - self.PRESERVE_STOPWORDS

        tokens = [t for t in tokens if t not in stop_words or t in self.PRESERVE_STOPWORDS]

        return tokens
```

**Note:** For production, we can skip NLTK dependency and use a hardcoded stop word list.

---

## Fusion Strategy: Reciprocal Rank Fusion

### Algorithm Choice: RRF

**Reciprocal Rank Fusion (RRF)** is the industry standard for hybrid search:

**Formula:**
```
RRF_score(doc) = Σ 1 / (k + rank_i(doc))
```

Where:
- `k` = constant (typically 60, tunable)
- `rank_i(doc)` = rank of document in i-th retrieval method (0-indexed)

**Why RRF over Linear Combination?**

| Method | Pros | Cons |
|--------|------|------|
| **RRF** | ✅ No score normalization needed<br>✅ Robust to score scale differences<br>✅ Proven in production (Elastic, Pinecone)<br>✅ Simple, parameter-free | ❌ Doesn't use raw scores |
| Linear Combo | ✅ Uses raw scores | ❌ Requires score normalization<br>❌ Sensitive to weight tuning<br>❌ BM25 and cosine scores have different scales |

### Implementation

```python
from collections import defaultdict
from typing import List, Tuple
import asyncio

class ReciprocalRankFusion:
    """Combines vector and BM25 results using RRF algorithm"""

    def __init__(self, k: int = 60):
        """Initialize RRF combiner

        Args:
            k: RRF constant (default 60 per literature)
        """
        self.k = k

    def combine(
        self,
        vector_results: List[Tuple[str, float]],  # (chunk_id, score)
        bm25_results: List[Tuple[str, float]],    # (chunk_id, score)
        top_k: int = 20
    ) -> List[str]:
        """Combine results using RRF

        Args:
            vector_results: Results from vector search (ordered by score desc)
            bm25_results: Results from BM25 search (ordered by score desc)
            top_k: Number of results to return

        Returns:
            List of chunk IDs ordered by combined score
        """
        rrf_scores = defaultdict(float)

        # Accumulate RRF scores from vector search
        for rank, (chunk_id, _) in enumerate(vector_results):
            rrf_scores[chunk_id] += 1.0 / (self.k + rank)

        # Accumulate RRF scores from BM25 search
        for rank, (chunk_id, _) in enumerate(bm25_results):
            rrf_scores[chunk_id] += 1.0 / (self.k + rank)

        # Sort by combined score (descending)
        sorted_chunks = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top-k chunk IDs
        return [chunk_id for chunk_id, _ in sorted_chunks[:top_k]]
```

### Tunable Parameters

| Parameter | Default | Range | Impact |
|-----------|---------|-------|--------|
| `k` | 60 | 10-100 | Lower k → more weight to top results |
| `vector_k` | 50 | 20-100 | Number of vector candidates |
| `bm25_k` | 50 | 20-100 | Number of BM25 candidates |
| `final_k` | 20 | 10-50 | Final results after fusion |

**Tuning Strategy:**
1. Start with defaults (k=60, vector_k=50, bm25_k=50)
2. Evaluate on test queries (code + docs)
3. Adjust `k` if too much weight on lower-ranked results
4. Adjust `vector_k`/`bm25_k` if missing relevant results

---

## Code-Specific Optimizations

### Optimization 1: Symbol Boosting

**Problem:** Function/class names should rank higher than comments/docstrings

**Solution:** Boost BM25 scores for symbol-rich chunks

```python
class CodeAwareBM25:
    """BM25 with code symbol boosting"""

    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        self.tokenizer = CodeAwareTokenizer()

        # Build BM25 index with boosted symbol chunks
        self.tokenized_docs = []
        self.symbol_boost_factors = []

        for chunk in chunks:
            tokens = self.tokenizer.tokenize(chunk.content, chunk.language)
            self.tokenized_docs.append(tokens)

            # Calculate symbol density boost
            boost = self._calculate_symbol_boost(chunk)
            self.symbol_boost_factors.append(boost)

        self.bm25 = BM25Okapi(self.tokenized_docs)

    def _calculate_symbol_boost(self, chunk: DocumentChunk) -> float:
        """Calculate boost factor based on symbol density

        Chunks with more code symbols (functions, classes) get higher boost
        """
        if chunk.language not in ['python', 'javascript', 'typescript']:
            return 1.0  # No boost for non-code

        # Count code symbols
        symbol_patterns = [
            r'\bclass\s+\w+',      # class definitions
            r'\bdef\s+\w+',        # function definitions (Python)
            r'\bfunction\s+\w+',   # function definitions (JS)
            r'\bconst\s+\w+\s*=',  # constants
            r'\binterface\s+\w+',  # interfaces (TS)
        ]

        symbol_count = sum(
            len(re.findall(pattern, chunk.content))
            for pattern in symbol_patterns
        )

        # Boost factor: 1.0 (no boost) to 2.0 (max boost)
        # More symbols → higher boost
        boost = 1.0 + min(symbol_count * 0.1, 1.0)
        return boost

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        """Get BM25 scores with symbol boosting applied"""
        base_scores = self.bm25.get_scores(query_tokens)

        # Apply boost factors
        boosted_scores = [
            score * boost
            for score, boost in zip(base_scores, self.symbol_boost_factors)
        ]

        return boosted_scores
```

### Optimization 2: Comment vs Code Weighting

**Problem:** Comments often have higher keyword match but lower semantic value

**Solution:** Weight code tokens higher than comment tokens

```python
class WeightedTokenizer:
    """Tokenizer with code/comment weighting"""

    def tokenize_with_weights(
        self,
        text: str,
        language: str
    ) -> Tuple[List[str], List[float]]:
        """Tokenize with per-token weights

        Returns:
            (tokens, weights) where weights are 1.0 (code) or 0.5 (comment)
        """
        tokens = []
        weights = []

        lines = text.split('\n')
        for line in lines:
            is_comment = self._is_comment_line(line, language)
            line_tokens = self.tokenizer.tokenize(line, language)

            tokens.extend(line_tokens)

            # Weight: 0.5 for comments, 1.0 for code
            weight = 0.5 if is_comment else 1.0
            weights.extend([weight] * len(line_tokens))

        return tokens, weights

    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if line is a comment"""
        line = line.strip()

        if language == 'python':
            return line.startswith('#') or line.startswith('"""') or line.startswith("'''")
        elif language in ['javascript', 'typescript']:
            return line.startswith('//') or line.startswith('/*')

        return False
```

**Note:** `rank_bm25` doesn't support weighted tokens natively. This is a future enhancement or can be implemented via custom BM25 calculation.

### Optimization 3: AST-Aware Chunking (Future)

**Note:** This is part of Phase 5 of the CGRAG Enhancement Plan. Include here for completeness.

```python
# Future enhancement - use tree-sitter for AST-based chunking
# See: docs/plans/CGRAG_ENHANCEMENT_PLAN.md Phase 5

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

class ASTChunker:
    """Chunk code files by function/class boundaries"""

    def chunk_python_file(self, file_path: Path) -> List[DocumentChunk]:
        """Chunk Python file by function/class definitions"""
        # Parse AST
        parser = Parser()
        parser.set_language(Language(tspython.language(), 'python'))

        content = file_path.read_text()
        tree = parser.parse(bytes(content, 'utf-8'))

        chunks = []
        for node in tree.root_node.children:
            if node.type in ['function_definition', 'class_definition']:
                chunk = DocumentChunk(
                    file_path=str(file_path),
                    content=content[node.start_byte:node.end_byte],
                    chunk_index=len(chunks),
                    start_pos=node.start_byte,
                    end_pos=node.end_byte,
                    language='python'
                )
                chunks.append(chunk)

        return chunks
```

---

## Performance Optimizations

### Target: <65ms Retrieval Latency

**Current Latency Budget:**
- Vector search: ~40ms (FAISS IndexFlatL2 for <100k docs)
- BM25 search: ~15ms (target)
- RRF fusion: ~5ms
- Token packing: ~5ms
- **Total: ~65ms** (vs 100ms current)

### Optimization 1: Parallel Execution

```python
import asyncio
from typing import List, Tuple

class HybridRetriever:
    """Hybrid retriever with parallel search execution"""

    async def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        token_budget: int = 8000,
        max_artifacts: int = 20
    ) -> CGRAGResult:
        """Retrieve using parallel vector + BM25 search"""
        start_time = time.time()

        # Tokenize query for BM25
        query_tokens = self.tokenizer.tokenize(query)

        # Execute searches in parallel
        vector_task = asyncio.create_task(
            self._vector_search(query_embedding, k=50)
        )
        bm25_task = asyncio.create_task(
            self._bm25_search(query_tokens, k=50)
        )

        # Wait for both to complete
        vector_results, bm25_results = await asyncio.gather(
            vector_task, bm25_task
        )

        # Combine results using RRF
        fused_chunk_ids = self.rrf.combine(
            vector_results, bm25_results, top_k=max_artifacts
        )

        # Get chunks and pack within token budget
        candidates = [self._get_chunk(cid) for cid in fused_chunk_ids]
        selected_chunks, tokens_used = self._pack_artifacts(
            candidates, token_budget
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return CGRAGResult(
            artifacts=selected_chunks,
            tokens_used=tokens_used,
            candidates_considered=len(fused_chunk_ids),
            retrieval_time_ms=elapsed_ms,
            cache_hit=False,
            top_scores=[c.relevance_score for c in selected_chunks]
        )

    async def _vector_search(
        self,
        query_embedding: np.ndarray,
        k: int
    ) -> List[Tuple[str, float]]:
        """Vector search (FAISS)"""
        # Run FAISS search in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()

        def search():
            distances, indices = self.indexer.index.search(
                query_embedding.reshape(1, -1), k
            )
            # Convert distances to cosine similarity scores
            scores = 1.0 - (distances[0] / 2.0)
            return [
                (self.indexer.chunks[idx].id, float(score))
                for idx, score in zip(indices[0], scores)
                if idx >= 0 and idx < len(self.indexer.chunks)
            ]

        return await loop.run_in_executor(None, search)

    async def _bm25_search(
        self,
        query_tokens: List[str],
        k: int
    ) -> List[Tuple[str, float]]:
        """BM25 keyword search"""
        # Run BM25 scoring in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()

        def search():
            scores = self.bm25_index.bm25.get_scores(query_tokens)
            # Get top k results
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:k]
            return [
                (self.bm25_index.chunk_ids[idx], float(scores[idx]))
                for idx in top_indices
            ]

        return await loop.run_in_executor(None, search)
```

### Optimization 2: Redis Caching

**Cache Strategy:**

```python
import redis.asyncio as redis
import hashlib
import pickle

class CachedHybridRetriever(HybridRetriever):
    """Hybrid retriever with Redis caching"""

    def __init__(self, *args, redis_client: redis.Redis, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour

    async def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        token_budget: int = 8000,
        max_artifacts: int = 20
    ) -> CGRAGResult:
        """Retrieve with caching"""
        # Generate cache key
        cache_key = self._generate_cache_key(query, token_budget, max_artifacts)

        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            result = pickle.loads(cached)
            result.cache_hit = True
            logger.info(f"Cache HIT for query: {query[:50]}...")
            return result

        # Cache miss - perform retrieval
        result = await super().retrieve(
            query, query_embedding, token_budget, max_artifacts
        )

        # Store in cache
        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            pickle.dumps(result)
        )

        logger.info(f"Cache MISS for query: {query[:50]}...")
        return result

    def _generate_cache_key(
        self,
        query: str,
        token_budget: int,
        max_artifacts: int
    ) -> str:
        """Generate cache key from query parameters"""
        key_data = f"{query}:{token_budget}:{max_artifacts}"
        hash_digest = hashlib.sha256(key_data.encode()).hexdigest()
        return f"cgrag:hybrid:{hash_digest}"
```

### Optimization 3: Early Termination

```python
def _pack_artifacts_with_early_termination(
    self,
    candidates: List[DocumentChunk],
    token_budget: int,
    min_relevance: float = 0.7
) -> Tuple[List[DocumentChunk], int]:
    """Pack artifacts with early termination"""
    selected = []
    total_tokens = 0

    for chunk in candidates:
        # Early termination if relevance drops too low
        if chunk.relevance_score < min_relevance:
            logger.debug(f"Early termination at relevance {chunk.relevance_score:.3f}")
            break

        chunk_tokens = self._count_tokens(chunk.content)

        if total_tokens + chunk_tokens > token_budget:
            if not selected:  # Ensure at least 1 chunk
                selected.append(chunk)
                total_tokens += chunk_tokens
            break

        selected.append(chunk)
        total_tokens += chunk_tokens

        # Early termination if we have enough high-quality results
        if len(selected) >= 10 and chunk.relevance_score > 0.9:
            logger.debug(f"Early termination with {len(selected)} high-quality chunks")
            break

    return selected, total_tokens
```

---

## Implementation Plan

### Phase 1: Core BM25 Integration (Days 1-3)

**Tasks:**
1. Add dependencies to `requirements.txt`
2. Create `BM25Index` class in `cgrag.py`
3. Modify `CGRAGIndexer` to build BM25 index alongside FAISS
4. Implement `CodeAwareTokenizer` and `DocumentTokenizer`
5. Update `save_index()` and `load_index()` to handle BM25 index

**Files Modified:**
- `backend/requirements.txt` - Add rank_bm25
- `backend/app/services/cgrag.py` - Add BM25 indexing

**Testing:**
- Index small test corpus
- Verify BM25 index saves/loads correctly
- Validate tokenization with code samples

### Phase 2: RRF Fusion (Days 4-5)

**Tasks:**
1. Implement `ReciprocalRankFusion` class
2. Create `HybridRetriever` class extending `CGRAGRetriever`
3. Add parallel execution of vector + BM25 searches
4. Implement score combination logic

**Files Modified:**
- `backend/app/services/cgrag.py` - Add HybridRetriever

**Testing:**
- Test RRF with sample results
- Compare hybrid vs vector-only accuracy
- Measure latency impact

### Phase 3: Performance Optimization (Days 6-7)

**Tasks:**
1. Add Redis caching for hybrid results
2. Optimize parallel execution
3. Add early termination logic
4. Profile and optimize hotspots

**Files Modified:**
- `backend/app/services/cgrag.py` - Add caching

**Testing:**
- Benchmark retrieval latency
- Measure cache hit rate
- Load testing with 100+ concurrent queries

### Phase 4: Code-Specific Enhancements (Days 8-9)

**Tasks:**
1. Implement symbol boosting in BM25
2. Add CamelCase/snake_case splitting
3. Test on code search queries

**Files Modified:**
- `backend/app/services/cgrag.py` - Enhance tokenization

**Testing:**
- Test function/class name searches
- Validate symbol split logic
- Compare with vector-only on code queries

### Phase 5: Configuration & Tuning (Day 10)

**Tasks:**
1. Add hybrid search configuration to runtime settings
2. Implement feature flag for hybrid mode
3. Add metrics for hybrid search performance
4. Document configuration options

**Files Modified:**
- `backend/app/services/runtime_settings.py` - Add hybrid config
- `backend/app/models/query.py` - Add hybrid metrics

**Testing:**
- Test with hybrid enabled/disabled
- Tune RRF parameters on test queries
- Validate metrics collection

---

## Code Examples

### Complete Implementation

**File:** `backend/app/services/cgrag.py`

```python
"""CGRAG (Contextually-Guided Retrieval Augmented Generation) implementation.

This module provides document indexing and context retrieval using hybrid search:
- FAISS for vector similarity search
- BM25 for keyword/symbol matching
- Reciprocal Rank Fusion for combining results

Optimized for code and technical documentation retrieval.
"""

import asyncio
import json
import logging
import pickle
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from collections import defaultdict

import faiss
import numpy as np
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

# ... (existing DocumentChunk, CGRAGResult classes remain unchanged) ...

class CodeAwareTokenizer:
    """Tokenizer optimized for code with symbol preservation and splitting"""

    CAMEL_CASE_PATTERN = re.compile(r'([a-z])([A-Z])')
    SYMBOL_PATTERN = re.compile(r'[\w]+')

    def tokenize(self, text: str, language: Optional[str] = None) -> List[str]:
        """Tokenize code-aware text with CamelCase and snake_case splitting

        Args:
            text: Text to tokenize
            language: Programming language (python, javascript, etc.)

        Returns:
            List of tokens optimized for code search
        """
        tokens = []

        # Extract all alphanumeric symbols
        symbols = self.SYMBOL_PATTERN.findall(text)

        for symbol in symbols:
            # Add original symbol (lowercase)
            tokens.append(symbol.lower())

            # Split CamelCase: getUserName → get, user, name
            if self._is_camel_case(symbol):
                sub_tokens = self._split_camel_case(symbol)
                tokens.extend(sub_tokens)

            # Split snake_case: get_user_name → get, user, name
            if '_' in symbol:
                sub_tokens = symbol.split('_')
                tokens.extend([t.lower() for t in sub_tokens if t])

        # Add lowercase words from entire text
        tokens.extend(text.lower().split())

        return tokens

    def _is_camel_case(self, text: str) -> bool:
        """Check if text is in CamelCase format"""
        return bool(self.CAMEL_CASE_PATTERN.search(text))

    def _split_camel_case(self, text: str) -> List[str]:
        """Split CamelCase into parts: getUserName → [get, user, name]"""
        spaced = self.CAMEL_CASE_PATTERN.sub(r'\1 \2', text)
        return [t.lower() for t in spaced.split()]


class BM25Index:
    """BM25 index structure for keyword search"""

    def __init__(
        self,
        bm25: BM25Okapi,
        chunk_ids: List[str],
        tokenizer: CodeAwareTokenizer
    ):
        """Initialize BM25 index

        Args:
            bm25: BM25Okapi instance
            chunk_ids: Maps BM25 doc index → chunk ID
            tokenizer: Tokenizer used for this index
        """
        self.bm25 = bm25
        self.chunk_ids = chunk_ids
        self.tokenizer = tokenizer

    def save(self, path: Path) -> None:
        """Save BM25 index to disk"""
        logger.info(f"Saving BM25 index to {path}")
        with open(path, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'chunk_ids': self.chunk_ids
            }, f)

    @classmethod
    def load(cls, path: Path, tokenizer: CodeAwareTokenizer) -> 'BM25Index':
        """Load BM25 index from disk"""
        logger.info(f"Loading BM25 index from {path}")
        if not path.exists():
            raise FileNotFoundError(f"BM25 index file not found: {path}")

        with open(path, 'rb') as f:
            data = pickle.load(f)

        return cls(
            bm25=data['bm25'],
            chunk_ids=data['chunk_ids'],
            tokenizer=tokenizer
        )


class ReciprocalRankFusion:
    """Combines vector and BM25 results using Reciprocal Rank Fusion"""

    def __init__(self, k: int = 60):
        """Initialize RRF combiner

        Args:
            k: RRF constant (default 60 per literature)
        """
        self.k = k

    def combine(
        self,
        vector_results: List[Tuple[str, float]],  # (chunk_id, score)
        bm25_results: List[Tuple[str, float]],    # (chunk_id, score)
        top_k: int = 20
    ) -> List[str]:
        """Combine results using RRF

        Args:
            vector_results: Results from vector search (ordered by score desc)
            bm25_results: Results from BM25 search (ordered by score desc)
            top_k: Number of results to return

        Returns:
            List of chunk IDs ordered by combined RRF score
        """
        rrf_scores = defaultdict(float)

        # Accumulate RRF scores from vector search
        for rank, (chunk_id, _) in enumerate(vector_results):
            rrf_scores[chunk_id] += 1.0 / (self.k + rank)

        # Accumulate RRF scores from BM25 search
        for rank, (chunk_id, _) in enumerate(bm25_results):
            rrf_scores[chunk_id] += 1.0 / (self.k + rank)

        # Sort by combined score (descending)
        sorted_chunks = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top-k chunk IDs
        return [chunk_id for chunk_id, _ in sorted_chunks[:top_k]]


class CGRAGIndexer:
    """Indexes documents into FAISS vector database + BM25 keyword index.

    Creates dual indexes for hybrid search:
    - FAISS for semantic vector similarity
    - BM25 for keyword/symbol matching

    Attributes:
        encoder: SentenceTransformer model for embeddings
        chunks: List of indexed document chunks
        index: FAISS index for similarity search
        bm25_index: BM25 index for keyword search (optional)
        embedding_dim: Dimension of embedding vectors
        tokenizer: CodeAwareTokenizer for BM25
    """

    SUPPORTED_EXTENSIONS = {'.md', '.py', '.txt', '.yaml', '.yml', '.json', '.rst', '.js', '.ts', '.tsx'}

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        enable_hybrid: bool = True
    ):
        """Initialize indexer with sentence-transformers model.

        Args:
            embedding_model: Name of sentence-transformers model to use
            enable_hybrid: Enable BM25 hybrid search (default True)
        """
        logger.info(f"Initializing CGRAGIndexer with model: {embedding_model}, hybrid: {enable_hybrid}")
        self.embedding_model_name = embedding_model
        self.encoder = SentenceTransformer(embedding_model)
        self.chunks: List[DocumentChunk] = []
        self.index: Optional[faiss.Index] = None
        self.bm25_index: Optional[BM25Index] = None
        self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
        self.enable_hybrid = enable_hybrid
        self.tokenizer = CodeAwareTokenizer()

    async def index_directory(
        self,
        directory: Path,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        batch_size: int = 32
    ) -> int:
        """Recursively index all documents in directory.

        Scans directory for supported file types, chunks documents with overlap,
        generates embeddings in batches, and builds FAISS + BM25 indexes.

        Args:
            directory: Root directory to index
            chunk_size: Target chunk size in words
            chunk_overlap: Overlap between chunks in words
            batch_size: Batch size for embedding generation

        Returns:
            Number of chunks indexed
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        logger.info(f"Starting indexing of directory: {directory}")
        start_time = time.time()

        # Collect all supported files
        files = self._collect_files(directory)
        logger.info(f"Found {len(files)} supported files")

        # Process files and create chunks
        all_chunks = []
        for file_path in files:
            try:
                chunks = await self._chunk_file(file_path, chunk_size, chunk_overlap)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

        logger.info(f"Created {len(all_chunks)} chunks from {len(files)} files")

        # Generate embeddings in batches
        embeddings = await self._generate_embeddings_batched(all_chunks, batch_size)

        # Build FAISS index
        self.chunks = all_chunks
        self.index = self._build_faiss_index(embeddings)

        # Build BM25 index if hybrid mode enabled
        if self.enable_hybrid:
            self.bm25_index = self._build_bm25_index(all_chunks)

        elapsed = time.time() - start_time
        logger.info(
            f"Indexing complete: {len(all_chunks)} chunks in {elapsed:.2f}s "
            f"({len(all_chunks)/elapsed:.1f} chunks/sec)"
        )

        return len(all_chunks)

    # ... (existing _collect_files, _chunk_file, _detect_language methods unchanged) ...

    def _build_bm25_index(self, chunks: List[DocumentChunk]) -> BM25Index:
        """Build BM25 index from chunks

        Args:
            chunks: Document chunks to index

        Returns:
            BM25Index instance
        """
        logger.info(f"Building BM25 index for {len(chunks)} chunks")
        start_time = time.time()

        # Tokenize all chunks
        tokenized_docs = []
        chunk_ids = []

        for chunk in chunks:
            tokens = self.tokenizer.tokenize(chunk.content, chunk.language)
            tokenized_docs.append(tokens)
            chunk_ids.append(chunk.id)

        # Build BM25
        bm25 = BM25Okapi(tokenized_docs)

        elapsed = time.time() - start_time
        logger.info(f"Built BM25 index in {elapsed:.2f}s")

        return BM25Index(bm25=bm25, chunk_ids=chunk_ids, tokenizer=self.tokenizer)

    # ... (existing _generate_embeddings_batched, _build_faiss_index methods unchanged) ...

    def save_index(self, index_path: Path, metadata_path: Path) -> None:
        """Save FAISS index, BM25 index, and chunk metadata to disk.

        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save chunk metadata
        """
        if self.index is None:
            raise ValueError("No index to save. Run index_directory() first.")

        logger.info(f"Saving index to {index_path}")
        logger.info(f"Saving metadata to {metadata_path}")

        # Save FAISS index
        faiss.write_index(self.index, str(index_path))

        # Save BM25 index if exists
        if self.bm25_index:
            bm25_path = index_path.with_suffix('.bm25')
            self.bm25_index.save(bm25_path)

        # Save chunk metadata with embedding model info
        metadata = {
            "embedding_model_name": self.embedding_model_name,
            "embedding_dim": self.embedding_dim,
            "enable_hybrid": self.enable_hybrid,
            "chunks": [chunk.model_dump() for chunk in self.chunks]
        }
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        logger.info(f"Saved {len(self.chunks)} chunks with embedding model: {self.embedding_model_name}")

    @classmethod
    def load_index(cls, index_path: Path, metadata_path: Path) -> "CGRAGIndexer":
        """Load FAISS index, BM25 index, and metadata from disk.

        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata file

        Returns:
            CGRAGIndexer instance with loaded indexes
        """
        logger.info(f"Loading index from {index_path}")
        logger.info(f"Loading metadata from {metadata_path}")

        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        # Load chunk metadata
        with open(metadata_path, 'rb') as f:
            loaded_data = pickle.load(f)

        # Handle both old format (list of chunks) and new format (dict with metadata)
        if isinstance(loaded_data, dict):
            embedding_model_name = loaded_data.get("embedding_model_name", "all-MiniLM-L6-v2")
            enable_hybrid = loaded_data.get("enable_hybrid", True)
            chunk_data = loaded_data.get("chunks", [])
            logger.info(f"Loaded index with embedding model: {embedding_model_name}, hybrid: {enable_hybrid}")
        else:
            # Old format - just a list of chunks
            embedding_model_name = "all-MiniLM-L6-v2"
            enable_hybrid = False
            chunk_data = loaded_data
            logger.warning("Loading old format index without hybrid search support")

        # Create indexer instance
        indexer = cls(embedding_model=embedding_model_name, enable_hybrid=enable_hybrid)

        # Load FAISS index
        indexer.index = faiss.read_index(str(index_path))

        # Load chunks
        indexer.chunks = [DocumentChunk(**data) for data in chunk_data]

        # Load BM25 index if exists and hybrid enabled
        if enable_hybrid:
            bm25_path = index_path.with_suffix('.bm25')
            if bm25_path.exists():
                try:
                    indexer.bm25_index = BM25Index.load(bm25_path, indexer.tokenizer)
                    logger.info("Loaded BM25 index successfully")
                except Exception as e:
                    logger.warning(f"Failed to load BM25 index: {e}. Falling back to vector-only mode.")
                    indexer.enable_hybrid = False
            else:
                logger.warning("BM25 index file not found. Falling back to vector-only mode.")
                indexer.enable_hybrid = False

        logger.info(f"Loaded {len(indexer.chunks)} chunks")

        return indexer

    # ... (existing validate_embedding_model method unchanged) ...


class HybridRetriever:
    """Retrieves relevant context using hybrid vector + BM25 search.

    Combines FAISS semantic search with BM25 keyword search using
    Reciprocal Rank Fusion for optimal code and documentation retrieval.

    Attributes:
        indexer: CGRAGIndexer with loaded indexes
        min_relevance: Minimum relevance threshold (0.0-1.0)
        rrf: Reciprocal Rank Fusion combiner
    """

    def __init__(
        self,
        indexer: CGRAGIndexer,
        min_relevance: float = 0.7,
        rrf_k: int = 60
    ):
        """Initialize hybrid retriever

        Args:
            indexer: CGRAGIndexer instance with loaded indexes
            min_relevance: Minimum relevance threshold for filtering
            rrf_k: RRF constant (default 60)
        """
        self.indexer = indexer
        self.min_relevance = min_relevance
        self.rrf = ReciprocalRankFusion(k=rrf_k)

        if self.indexer.index is None:
            raise ValueError("Indexer has no FAISS index. Load or build index first.")

    async def retrieve(
        self,
        query: str,
        token_budget: int = 8000,
        max_artifacts: int = 20
    ) -> CGRAGResult:
        """Retrieve relevant artifacts using hybrid search

        Args:
            query: Query text
            token_budget: Maximum tokens to retrieve
            max_artifacts: Maximum number of artifacts to return

        Returns:
            CGRAGResult with artifacts and metadata
        """
        start_time = time.time()

        # Embed query for vector search
        loop = asyncio.get_event_loop()
        encode_fn = lambda: self.indexer.encoder.encode(
            [query],
            show_progress_bar=False,
            convert_to_numpy=True
        )
        query_embedding = await loop.run_in_executor(None, encode_fn)
        query_embedding = query_embedding[0].reshape(1, -1)
        faiss.normalize_L2(query_embedding)

        # Execute searches in parallel if hybrid mode enabled
        if self.indexer.enable_hybrid and self.indexer.bm25_index:
            vector_task = asyncio.create_task(
                self._vector_search(query_embedding, k=50)
            )
            bm25_task = asyncio.create_task(
                self._bm25_search(query, k=50)
            )

            vector_results, bm25_results = await asyncio.gather(
                vector_task, bm25_task
            )

            # Combine using RRF
            fused_chunk_ids = self.rrf.combine(
                vector_results, bm25_results, top_k=max_artifacts * 2
            )

            # Get chunks with RRF scores
            chunk_map = {c.id: c for c in self.indexer.chunks}
            candidates = []
            for chunk_id in fused_chunk_ids:
                if chunk_id in chunk_map:
                    chunk = chunk_map[chunk_id].model_copy()
                    # Set relevance score based on position in fused results
                    chunk.relevance_score = 1.0 - (len(candidates) * 0.01)
                    candidates.append(chunk)

            logger.info(f"Hybrid search: {len(candidates)} candidates from RRF fusion")

        else:
            # Fall back to vector-only search
            logger.info("Using vector-only search (hybrid disabled or BM25 unavailable)")
            vector_results = await self._vector_search(query_embedding, k=max_artifacts * 5)

            chunk_map = {c.id: c for c in self.indexer.chunks}
            candidates = []
            for chunk_id, score in vector_results:
                if chunk_id in chunk_map:
                    chunk = chunk_map[chunk_id].model_copy()
                    chunk.relevance_score = float(score)
                    candidates.append(chunk)

        # Filter by minimum relevance
        candidates = [c for c in candidates if c.relevance_score >= self.min_relevance]

        # Pack within token budget
        selected_chunks, tokens_used = self._pack_artifacts(candidates, token_budget)

        # Get top scores
        top_scores = [c.relevance_score for c in selected_chunks]

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Retrieved {len(selected_chunks)} artifacts "
            f"({tokens_used}/{token_budget} tokens) in {elapsed_ms:.1f}ms"
        )

        return CGRAGResult(
            artifacts=selected_chunks,
            tokens_used=tokens_used,
            candidates_considered=len(candidates),
            retrieval_time_ms=elapsed_ms,
            cache_hit=False,
            top_scores=top_scores
        )

    async def _vector_search(
        self,
        query_embedding: np.ndarray,
        k: int
    ) -> List[Tuple[str, float]]:
        """Vector search using FAISS"""
        loop = asyncio.get_event_loop()

        def search():
            distances, indices = self.indexer.index.search(query_embedding, k)
            # Convert normalized L2 distances to cosine similarity
            scores = 1.0 - (distances[0] / 2.0)
            return [
                (self.indexer.chunks[idx].id, float(score))
                for idx, score in zip(indices[0], scores)
                if idx >= 0 and idx < len(self.indexer.chunks)
            ]

        return await loop.run_in_executor(None, search)

    async def _bm25_search(
        self,
        query: str,
        k: int
    ) -> List[Tuple[str, float]]:
        """BM25 keyword search"""
        loop = asyncio.get_event_loop()

        def search():
            # Tokenize query
            query_tokens = self.indexer.tokenizer.tokenize(query)

            # Get BM25 scores
            scores = self.indexer.bm25_index.bm25.get_scores(query_tokens)

            # Get top k results
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:k]

            return [
                (self.indexer.bm25_index.chunk_ids[idx], float(scores[idx]))
                for idx in top_indices
            ]

        return await loop.run_in_executor(None, search)

    def _pack_artifacts(
        self,
        candidates: List[DocumentChunk],
        token_budget: int
    ) -> Tuple[List[DocumentChunk], int]:
        """Pack artifacts within token budget using greedy algorithm"""
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.relevance_score,
            reverse=True
        )

        selected = []
        total_tokens = 0

        for chunk in sorted_candidates:
            chunk_tokens = self._count_tokens(chunk.content)

            if total_tokens + chunk_tokens > token_budget:
                if not selected:  # Ensure at least 1 chunk
                    selected.append(chunk)
                    total_tokens += chunk_tokens
                break

            selected.append(chunk)
            total_tokens += chunk_tokens

        return selected, total_tokens

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using simple word-based approximation"""
        words = len(text.split())
        return int(words * 1.3)


# For backward compatibility, keep CGRAGRetriever as alias
CGRAGRetriever = HybridRetriever
```

---

## Testing Strategy

### Unit Tests

**File:** `backend/tests/test_hybrid_search.py`

```python
import pytest
import numpy as np
from pathlib import Path
from backend.app.services.cgrag import (
    CodeAwareTokenizer,
    ReciprocalRankFusion,
    HybridRetriever,
    CGRAGIndexer,
    DocumentChunk
)

class TestCodeAwareTokenizer:
    """Test code-aware tokenization"""

    def test_camel_case_splitting(self):
        tokenizer = CodeAwareTokenizer()
        tokens = tokenizer.tokenize("getUserProfile")

        assert "getuserprofile" in tokens  # Original
        assert "get" in tokens             # Split parts
        assert "user" in tokens
        assert "profile" in tokens

    def test_snake_case_splitting(self):
        tokenizer = CodeAwareTokenizer()
        tokens = tokenizer.tokenize("get_user_profile")

        assert "get_user_profile" in tokens  # Original
        assert "get" in tokens                # Split parts
        assert "user" in tokens
        assert "profile" in tokens

    def test_python_function_tokenization(self):
        code = "async def fetch_user_data(user_id: str) -> UserProfile:"
        tokenizer = CodeAwareTokenizer()
        tokens = tokenizer.tokenize(code, language="python")

        # Should find all these tokens
        assert "fetch" in tokens
        assert "user" in tokens
        assert "data" in tokens
        assert "profile" in tokens
        assert "async" in tokens
        assert "def" in tokens


class TestReciprocalRankFusion:
    """Test RRF combination logic"""

    def test_rrf_basic_combination(self):
        rrf = ReciprocalRankFusion(k=60)

        vector_results = [
            ("chunk1", 0.9),
            ("chunk2", 0.8),
            ("chunk3", 0.7)
        ]

        bm25_results = [
            ("chunk3", 15.0),  # Different ranking
            ("chunk1", 10.0),
            ("chunk4", 5.0)
        ]

        fused = rrf.combine(vector_results, bm25_results, top_k=5)

        # chunk1 and chunk3 appear in both, should rank higher
        assert "chunk1" in fused[:2]
        assert "chunk3" in fused[:2]

    def test_rrf_handles_disjoint_sets(self):
        rrf = ReciprocalRankFusion(k=60)

        vector_results = [("chunk1", 0.9), ("chunk2", 0.8)]
        bm25_results = [("chunk3", 10.0), ("chunk4", 5.0)]

        fused = rrf.combine(vector_results, bm25_results, top_k=4)

        # All chunks should appear
        assert len(fused) == 4
        assert all(f"chunk{i}" in fused for i in range(1, 5))


@pytest.mark.asyncio
class TestHybridRetriever:
    """Integration tests for hybrid retrieval"""

    @pytest.fixture
    async def indexer_with_test_data(self, tmp_path):
        """Create indexer with test documents"""
        # Create test documents
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()

        # Code file
        (test_dir / "example.py").write_text("""
def get_user_profile(user_id: str) -> UserProfile:
    \"\"\"Fetch user profile from database\"\"\"
    return database.query(user_id)

class UserRepository:
    async def fetch_by_id(self, user_id: str):
        pass
""")

        # Documentation file
        (test_dir / "api_docs.md").write_text("""
# User API

## Get User Profile

Endpoint: GET /api/users/{user_id}/profile

Returns the user profile for the given user ID.
""")

        # Index documents
        indexer = CGRAGIndexer(enable_hybrid=True)
        await indexer.index_directory(test_dir, chunk_size=128)

        return indexer

    async def test_hybrid_retrieval_finds_code_functions(self, indexer_with_test_data):
        """Test that hybrid search finds function definitions"""
        retriever = HybridRetriever(indexer_with_test_data)

        # Query for function name
        result = await retriever.retrieve(
            query="get user profile function",
            token_budget=2000,
            max_artifacts=5
        )

        # Should find the code chunk
        assert len(result.artifacts) > 0
        assert any("get_user_profile" in chunk.content for chunk in result.artifacts)

    async def test_hybrid_retrieval_finds_documentation(self, indexer_with_test_data):
        """Test that hybrid search finds relevant documentation"""
        retriever = HybridRetriever(indexer_with_test_data)

        # Query for API documentation
        result = await retriever.retrieve(
            query="user profile API endpoint",
            token_budget=2000,
            max_artifacts=5
        )

        # Should find the docs chunk
        assert len(result.artifacts) > 0
        assert any("api_docs.md" in chunk.file_path for chunk in result.artifacts)

    async def test_hybrid_faster_than_100ms(self, indexer_with_test_data):
        """Test that retrieval meets latency target"""
        retriever = HybridRetriever(indexer_with_test_data)

        result = await retriever.retrieve(
            query="user repository",
            token_budget=2000,
            max_artifacts=10
        )

        # Should be under 100ms (target is 65ms for larger indexes)
        assert result.retrieval_time_ms < 100
```

### Integration Tests

**Test Scenarios:**

1. **Accuracy Comparison:**
   - Prepare test queries (50% code, 50% docs)
   - Compare results: vector-only vs hybrid
   - Measure relevance improvement

2. **Latency Benchmarking:**
   - Index 10k, 50k, 100k chunks
   - Measure retrieval time at each scale
   - Verify <65ms target

3. **Cache Hit Rate:**
   - Simulate repeated queries
   - Measure cache hit rate (target >70%)

4. **Load Testing:**
   - 100 concurrent queries
   - Verify no degradation
   - Check for resource leaks

### Manual Testing

**Test Queries:**

```python
# Code function search
"get user profile function"
"UserRepository fetch method"
"async fetch_by_id"

# Documentation search
"API endpoint user profile"
"how to query user database"

# Mixed search
"fetch user from database"
"get profile API"
```

**Expected Results:**
- Hybrid should rank code chunks higher for function name queries
- Hybrid should rank docs higher for conceptual queries
- Both should rank high for mixed queries

---

## Migration Path

### Backward Compatibility

**Goal:** Ensure existing indexes continue to work, with optional hybrid upgrade

**Strategy:**

1. **Default to Hybrid:** New indexes built with `enable_hybrid=True`
2. **Graceful Fallback:** Old indexes without BM25 fall back to vector-only
3. **Optional Rebuild:** Provide tool to rebuild old indexes with hybrid support

### Migration Script

**File:** `backend/scripts/migrate_to_hybrid.py`

```python
"""Migrate existing CGRAG indexes to hybrid search

Usage:
    python -m backend.scripts.migrate_to_hybrid --index-name docs
"""

import asyncio
import argparse
from pathlib import Path
from backend.app.services.cgrag import (
    CGRAGIndexer,
    get_cgrag_index_paths
)

async def migrate_index(index_name: str):
    """Migrate index to hybrid search"""
    print(f"Migrating index: {index_name}")

    # Get index paths
    index_dir, faiss_path, metadata_path = get_cgrag_index_paths(index_name)

    # Load existing index
    print("Loading existing index...")
    indexer = CGRAGIndexer.load_index(faiss_path, metadata_path)

    if indexer.enable_hybrid:
        print("Index already has hybrid search enabled!")
        return

    # Enable hybrid and rebuild BM25 index
    print("Building BM25 index...")
    indexer.enable_hybrid = True
    indexer.bm25_index = indexer._build_bm25_index(indexer.chunks)

    # Save updated index
    print("Saving updated index...")
    indexer.save_index(faiss_path, metadata_path)

    print(f"Migration complete! Index '{index_name}' now supports hybrid search.")

def main():
    parser = argparse.ArgumentParser(description="Migrate CGRAG index to hybrid search")
    parser.add_argument("--index-name", required=True, help="Name of index to migrate")
    args = parser.parse_args()

    asyncio.run(migrate_index(args.index_name))

if __name__ == "__main__":
    main()
```

### Rollout Plan

**Week 1:**
1. Deploy hybrid search code (feature flag OFF)
2. Test on staging with existing indexes
3. Verify backward compatibility

**Week 2:**
1. Enable hybrid for new indexes (feature flag ON for new builds)
2. Monitor performance metrics
3. Collect user feedback

**Week 3:**
1. Migrate existing indexes using migration script
2. Enable hybrid globally
3. Tune RRF parameters based on production data

---

## Configuration

### Runtime Settings

**File:** `backend/app/models/runtime_settings.py`

```python
from pydantic import BaseModel, Field

class CGRAGSettings(BaseModel):
    """CGRAG configuration"""

    # Vector search
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )

    # Hybrid search
    enable_hybrid_search: bool = Field(
        default=True,
        description="Enable hybrid vector + BM25 search"
    )

    rrf_k: int = Field(
        default=60,
        description="Reciprocal Rank Fusion constant"
    )

    vector_search_k: int = Field(
        default=50,
        description="Number of vector search candidates"
    )

    bm25_search_k: int = Field(
        default=50,
        description="Number of BM25 search candidates"
    )

    # Retrieval
    min_relevance: float = Field(
        default=0.7,
        description="Minimum relevance score threshold"
    )

    token_budget: int = Field(
        default=8000,
        description="Default token budget for context retrieval"
    )

    # Indexing
    chunk_size: int = Field(
        default=512,
        description="Target chunk size in words"
    )

    chunk_overlap: int = Field(
        default=50,
        description="Overlap between chunks in words"
    )
```

### Environment Variables

```bash
# Enable/disable hybrid search globally
CGRAG_ENABLE_HYBRID=true

# Tuning parameters
CGRAG_RRF_K=60
CGRAG_VECTOR_K=50
CGRAG_BM25_K=50
```

---

## Metrics & Monitoring

### Key Metrics to Track

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class HybridSearchMetrics:
    """Metrics for hybrid search performance"""

    # Latency breakdown
    total_latency_ms: float
    vector_latency_ms: float
    bm25_latency_ms: float
    fusion_latency_ms: float

    # Result quality
    artifacts_returned: int
    candidates_vector: int
    candidates_bm25: int
    candidates_fused: int

    # Cache performance
    cache_hit: bool

    # Relevance
    top_relevance_score: float
    avg_relevance_score: float
```

### Prometheus Metrics (Future)

```python
from prometheus_client import Histogram, Counter, Gauge

# Latency histograms
hybrid_search_latency = Histogram(
    'cgrag_hybrid_search_latency_seconds',
    'Hybrid search retrieval latency',
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5]
)

vector_search_latency = Histogram(
    'cgrag_vector_search_latency_seconds',
    'Vector search latency'
)

bm25_search_latency = Histogram(
    'cgrag_bm25_search_latency_seconds',
    'BM25 search latency'
)

# Result quality
artifacts_returned = Histogram(
    'cgrag_artifacts_returned',
    'Number of artifacts returned',
    buckets=[1, 2, 5, 10, 20, 50]
)

relevance_score = Histogram(
    'cgrag_relevance_score',
    'Top relevance score',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# Mode usage
hybrid_mode_usage = Counter(
    'cgrag_hybrid_mode_usage_total',
    'Number of hybrid vs vector-only retrievals',
    ['mode']  # 'hybrid' or 'vector_only'
)
```

---

## Dependencies

**Add to `backend/requirements.txt`:**

```txt
# Hybrid search (Phase 1)
rank_bm25>=0.2.2
```

**Optional (Future Phases):**

```txt
# Knowledge Graph RAG (Phase 2)
spacy>=3.7.0
networkx>=3.0

# AST-based chunking (Phase 5)
tree-sitter>=0.21.0
tree-sitter-python>=0.21.0
tree-sitter-typescript>=0.21.0
```

---

## Next Steps

### Immediate (This Week)

1. **Review this design document** with team
2. **Add rank_bm25 to requirements.txt**
3. **Start Phase 1 implementation** (BM25 integration)
4. **Set up test corpus** for validation

### Next Week

1. **Complete Phase 1** (BM25 + RRF)
2. **Run accuracy tests** on code/doc queries
3. **Benchmark latency** with hybrid search
4. **Tune RRF parameters** based on results

### Following Weeks

1. **Phase 2:** Knowledge Graph RAG integration
2. **Phase 3:** Multi-context sources (code, docs, chat history)
3. **Phase 4:** Chat history context
4. **Phase 5:** AST-based code chunking

---

## Summary

This hybrid search design integrates BM25 keyword search with FAISS vector search using Reciprocal Rank Fusion. Key highlights:

✅ **Expected Impact:** +15-20% accuracy on code/technical queries
✅ **Performance:** <65ms retrieval latency (vs <100ms current)
✅ **Backward Compatible:** Existing indexes continue to work
✅ **Code-Optimized:** CamelCase/snake_case splitting, symbol boosting
✅ **Production Ready:** Comprehensive testing, monitoring, migration path

**Total Implementation Time:** 1-2 weeks

**Dependencies:** `rank_bm25>=0.2.2`

**Next Action:** Review and approve this design, then proceed with Phase 1 implementation.

---

**Questions or concerns? See [docs/plans/CGRAG_ENHANCEMENT_PLAN.md](./docs/plans/CGRAG_ENHANCEMENT_PLAN.md) for full context.**
