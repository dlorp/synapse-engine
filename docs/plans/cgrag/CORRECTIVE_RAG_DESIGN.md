# Corrective RAG (CRAG) Design Document

**Date:** 2025-11-30
**Author:** Backend Architect Agent
**Status:** Design - Ready for Implementation
**Estimated Time:** 2-3 weeks

---

## Executive Summary

This document specifies a **Corrective RAG (CRAG)** mechanism for S.Y.N.A.P.S.E. ENGINE based on Russian and Korean research findings. CRAG self-corrects retrieval results by evaluating document relevance, filtering irrelevant context, and augmenting with web search when local context is insufficient.

### Key Research Insights

**From Russian Research (Adaptive RAG):**
- Retrieval evaluator filters/rejects irrelevant documents
- Web search augmentation when local context insufficient
- Self-reflection mechanism for quality control

**From Korean Research (AutoRAG):**
- Automated retrieval quality assessment
- Dynamic correction strategies based on relevance scores
- Confidence thresholds for fallback logic

### Expected Impact

| Metric | Current | With CRAG | Improvement |
|--------|---------|-----------|-------------|
| **Retrieval Accuracy** | ~70% | **85-90%** | +15-20% |
| **Hallucination Rate** | ~10% | **<5%** | 50% reduction |
| **Avg Latency (fast-path)** | 100ms | **<70ms** | 30% faster |
| **Avg Latency (corrected)** | - | **450ms** | Web search overhead |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CRAG Pipeline                          │
└─────────────────────────────────────────────────────────────┘

Query
  │
  ├─> Initial Retrieval (CGRAG)
  │     └─> Top K candidates (k=20)
  │
  ├─> Relevance Evaluation (Fast Heuristics)
  │     ├─> Keyword Overlap Score
  │     ├─> Semantic Coherence Score
  │     ├─> Length/Density Checks
  │     └─> Aggregate: RELEVANT | PARTIAL | IRRELEVANT
  │
  ├─> Decision Router
  │     │
  │     ├─> RELEVANT (score > 0.75)
  │     │     └─> Return artifacts (FAST PATH)
  │     │
  │     ├─> PARTIAL (0.50 < score <= 0.75)
  │     │     ├─> Query Expansion (add synonyms)
  │     │     ├─> Re-retrieve with expanded query
  │     │     └─> Merge results + Return
  │     │
  │     └─> IRRELEVANT (score <= 0.50)
  │           ├─> Web Search Augmentation (SearXNG)
  │           ├─> Web snippet extraction
  │           └─> Return web results as artifacts
  │
  └─> Final Response with CRAG metadata
```

---

## Component Design

### 1. Relevance Evaluator

**Purpose:** Fast, LLM-free evaluation of retrieval quality using heuristics.

**Evaluation Criteria:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Keyword Overlap** | 30% | Ratio of query keywords found in artifacts |
| **Semantic Coherence** | 40% | Cosine similarity distribution (mean/variance) |
| **Length Adequacy** | 15% | Sufficient content to answer query |
| **Diversity** | 15% | Multiple sources/files represented |

**Thresholds:**

- **RELEVANT:** `score > 0.75` - High confidence, use as-is
- **PARTIAL:** `0.50 < score <= 0.75` - Medium confidence, expand and retry
- **IRRELEVANT:** `score <= 0.50` - Low confidence, fallback to web search

**Implementation:**

```python
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from collections import Counter

@dataclass
class RelevanceScore:
    """Evaluation result from CRAG relevance assessment."""
    category: str  # RELEVANT | PARTIAL | IRRELEVANT
    score: float   # 0.0-1.0
    keyword_overlap: float
    semantic_coherence: float
    length_adequacy: float
    diversity: float
    reasoning: str

class CRAGEvaluator:
    """Evaluates retrieval quality using fast heuristics (LLM-free).

    Implements multi-criteria relevance assessment based on:
    - Keyword overlap between query and artifacts
    - Semantic coherence (similarity score distribution)
    - Content length adequacy
    - Source diversity
    """

    # Category thresholds
    RELEVANT_THRESHOLD = 0.75
    PARTIAL_THRESHOLD = 0.50

    # Criteria weights (must sum to 1.0)
    WEIGHTS = {
        'keyword_overlap': 0.30,
        'semantic_coherence': 0.40,
        'length_adequacy': 0.15,
        'diversity': 0.15
    }

    def __init__(self, min_keywords: int = 2, min_tokens_per_chunk: int = 100):
        """Initialize evaluator with configuration.

        Args:
            min_keywords: Minimum query keywords to consider
            min_tokens_per_chunk: Minimum tokens per chunk for adequacy
        """
        self.min_keywords = min_keywords
        self.min_tokens_per_chunk = min_tokens_per_chunk

    async def evaluate(
        self,
        query: str,
        artifacts: List['DocumentChunk'],
        relevance_scores: List[float]
    ) -> RelevanceScore:
        """Evaluate retrieval quality using multi-criteria heuristics.

        Args:
            query: Original query text
            artifacts: Retrieved document chunks
            relevance_scores: FAISS similarity scores for artifacts

        Returns:
            RelevanceScore with category and detailed metrics
        """
        # Extract query keywords (simple tokenization)
        query_keywords = self._extract_keywords(query)

        # Criterion 1: Keyword Overlap (30%)
        keyword_score = self._compute_keyword_overlap(query_keywords, artifacts)

        # Criterion 2: Semantic Coherence (40%)
        coherence_score = self._compute_semantic_coherence(relevance_scores)

        # Criterion 3: Length Adequacy (15%)
        length_score = self._compute_length_adequacy(artifacts)

        # Criterion 4: Source Diversity (15%)
        diversity_score = self._compute_diversity(artifacts)

        # Weighted aggregate score
        aggregate_score = (
            self.WEIGHTS['keyword_overlap'] * keyword_score +
            self.WEIGHTS['semantic_coherence'] * coherence_score +
            self.WEIGHTS['length_adequacy'] * length_score +
            self.WEIGHTS['diversity'] * diversity_score
        )

        # Classify into category
        if aggregate_score > self.RELEVANT_THRESHOLD:
            category = "RELEVANT"
            reasoning = f"High relevance ({aggregate_score:.2f}). Retrieved context is sufficient."
        elif aggregate_score > self.PARTIAL_THRESHOLD:
            category = "PARTIAL"
            reasoning = f"Partial relevance ({aggregate_score:.2f}). Query expansion recommended."
        else:
            category = "IRRELEVANT"
            reasoning = f"Low relevance ({aggregate_score:.2f}). Fallback to web search required."

        return RelevanceScore(
            category=category,
            score=aggregate_score,
            keyword_overlap=keyword_score,
            semantic_coherence=coherence_score,
            length_adequacy=length_score,
            diversity=diversity_score,
            reasoning=reasoning
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract query keywords using simple tokenization.

        Filters stopwords and short tokens.

        Args:
            query: Query text

        Returns:
            List of keyword strings
        """
        # Simple stopword list (English)
        stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'what', 'how'
        }

        # Tokenize and filter
        tokens = query.lower().split()
        keywords = [
            token for token in tokens
            if token not in stopwords and len(token) > 2
        ]

        return keywords

    def _compute_keyword_overlap(
        self,
        query_keywords: List[str],
        artifacts: List['DocumentChunk']
    ) -> float:
        """Compute keyword overlap ratio.

        Measures what fraction of query keywords appear in artifacts.

        Args:
            query_keywords: Query keywords
            artifacts: Retrieved chunks

        Returns:
            Overlap ratio (0.0-1.0)
        """
        if not query_keywords or not artifacts:
            return 0.0

        # Combine all artifact content
        combined_text = ' '.join(chunk.content.lower() for chunk in artifacts)

        # Count how many query keywords appear
        found_keywords = sum(
            1 for keyword in query_keywords
            if keyword in combined_text
        )

        return found_keywords / len(query_keywords)

    def _compute_semantic_coherence(self, relevance_scores: List[float]) -> float:
        """Compute semantic coherence from similarity score distribution.

        High coherence = high mean + low variance (all chunks relevant)
        Low coherence = low mean or high variance (some irrelevant chunks)

        Args:
            relevance_scores: FAISS similarity scores

        Returns:
            Coherence score (0.0-1.0)
        """
        if not relevance_scores:
            return 0.0

        scores = np.array(relevance_scores)
        mean_score = float(np.mean(scores))
        variance = float(np.var(scores))

        # Coherence = high mean, low variance
        # Penalize high variance (inconsistent relevance)
        coherence = mean_score * (1.0 - min(variance, 0.3))

        return float(np.clip(coherence, 0.0, 1.0))

    def _compute_length_adequacy(self, artifacts: List['DocumentChunk']) -> float:
        """Compute length adequacy score.

        Checks if artifacts have sufficient content to answer query.

        Args:
            artifacts: Retrieved chunks

        Returns:
            Adequacy score (0.0-1.0)
        """
        if not artifacts:
            return 0.0

        # Count tokens across all chunks
        total_tokens = sum(
            self._estimate_tokens(chunk.content)
            for chunk in artifacts
        )

        # Expect at least min_tokens_per_chunk * num_chunks
        expected_tokens = self.min_tokens_per_chunk * len(artifacts)

        if total_tokens >= expected_tokens:
            return 1.0
        else:
            return total_tokens / expected_tokens

    def _compute_diversity(self, artifacts: List['DocumentChunk']) -> float:
        """Compute source diversity score.

        Higher score = artifacts from multiple different files.

        Args:
            artifacts: Retrieved chunks

        Returns:
            Diversity score (0.0-1.0)
        """
        if not artifacts:
            return 0.0

        # Count unique file paths
        unique_files = len(set(chunk.file_path for chunk in artifacts))

        # Diversity = unique_files / total_chunks (capped at 1.0)
        diversity = unique_files / len(artifacts)

        return min(diversity, 1.0)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using word-based heuristic.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        words = len(text.split())
        return int(words * 1.3)  # tokens ≈ words * 1.3
```

---

### 2. Query Expansion Strategy

**Purpose:** Improve retrieval for PARTIAL relevance by expanding query with synonyms and related terms.

**Approach:**

- Extract query keywords
- Generate synonym expansions (local, no API calls)
- Re-retrieve with expanded query
- Merge original + expanded results using RRF (Reciprocal Rank Fusion)

**Implementation:**

```python
from typing import List, Set

class QueryExpander:
    """Expands queries with synonyms to improve retrieval (PARTIAL category).

    Uses local synonym mappings (no external API calls for privacy).
    """

    # Simple domain-specific synonym mappings
    # TODO: Load from configuration file for extensibility
    SYNONYMS = {
        'function': ['method', 'procedure', 'routine', 'callable'],
        'variable': ['parameter', 'argument', 'value', 'identifier'],
        'error': ['exception', 'failure', 'bug', 'issue'],
        'class': ['type', 'object', 'structure', 'entity'],
        'async': ['asynchronous', 'concurrent', 'non-blocking'],
        'explain': ['describe', 'clarify', 'illustrate', 'define'],
        'compare': ['contrast', 'differentiate', 'distinguish'],
        'implement': ['create', 'build', 'develop', 'code'],
        'optimize': ['improve', 'enhance', 'refactor', 'speed up']
    }

    def __init__(self, max_synonyms_per_term: int = 2):
        """Initialize expander.

        Args:
            max_synonyms_per_term: Max synonyms to add per keyword
        """
        self.max_synonyms = max_synonyms_per_term

    def expand(self, query: str) -> str:
        """Expand query with synonyms.

        Args:
            query: Original query

        Returns:
            Expanded query with synonyms added
        """
        # Extract keywords
        tokens = query.lower().split()

        # Collect synonyms
        expanded_terms: Set[str] = set(tokens)

        for token in tokens:
            if token in self.SYNONYMS:
                synonyms = self.SYNONYMS[token][:self.max_synonyms]
                expanded_terms.update(synonyms)

        # Construct expanded query (original + synonyms)
        expanded_query = ' '.join(expanded_terms)

        return expanded_query
```

---

### 3. Web Search Augmentation

**Purpose:** Fallback to web search when local CGRAG context is IRRELEVANT.

**Integration:**

- Use existing `SearXNGClient` from `backend/app/services/websearch.py`
- Convert web search results to `DocumentChunk` format
- Return as CRAG-augmented artifacts

**Implementation:**

```python
from typing import List
from app.services.websearch import get_searxng_client, WebSearchResult
from app.services.cgrag import DocumentChunk
from datetime import datetime

class WebSearchAugmenter:
    """Augments CGRAG with web search when local context is insufficient.

    Converts SearXNG results to DocumentChunk format for unified pipeline.
    """

    def __init__(self):
        """Initialize augmenter with SearXNG client."""
        self.searxng_client = get_searxng_client(
            base_url="http://searxng:8080",
            timeout=5,
            max_results=5
        )

    async def augment(self, query: str) -> List[DocumentChunk]:
        """Perform web search and convert results to DocumentChunk format.

        Args:
            query: Search query

        Returns:
            List of DocumentChunks from web search results
        """
        try:
            # Execute web search
            search_response = await self.searxng_client.search(query)

            # Convert web results to DocumentChunk format
            chunks = []
            for idx, result in enumerate(search_response.results):
                chunk = DocumentChunk(
                    file_path=result.url,  # Use URL as "file path"
                    content=f"{result.title}\n\n{result.content}",
                    chunk_index=idx,
                    start_pos=0,
                    end_pos=len(result.content),
                    language='web',  # Special marker for web results
                    modified_time=datetime.utcnow(),
                    relevance_score=result.score
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            logger.error(f"Web search augmentation failed: {e}")
            return []  # Return empty list on failure
```

---

### 4. CRAG Orchestrator

**Purpose:** Main coordinator that combines all CRAG components.

**File:** `backend/app/services/crag.py`

```python
"""Corrective RAG (CRAG) implementation.

Self-correcting retrieval mechanism that evaluates retrieval quality,
applies correction strategies (query expansion, web search), and ensures
high-quality context for model generation.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import List, Optional

from app.services.cgrag import CGRAGRetriever, CGRAGResult, DocumentChunk
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """Evaluation result from CRAG relevance assessment."""
    category: str  # RELEVANT | PARTIAL | IRRELEVANT
    score: float   # 0.0-1.0
    keyword_overlap: float
    semantic_coherence: float
    length_adequacy: float
    diversity: float
    reasoning: str


class CRAGResult(BaseModel):
    """Result from CRAG retrieval with correction metadata.

    Attributes:
        artifacts: Final retrieved/corrected artifacts
        tokens_used: Total tokens in artifacts
        retrieval_time_ms: Total retrieval + correction time
        crag_decision: Relevance category (RELEVANT/PARTIAL/IRRELEVANT)
        crag_score: Aggregate relevance score
        correction_applied: Whether correction strategy was used
        correction_strategy: Type of correction (query_expansion, web_search, none)
        original_artifacts_count: Number of artifacts before correction
        web_search_used: Whether web search was triggered
        cache_hit: Whether result was served from cache
    """
    artifacts: List[DocumentChunk]
    tokens_used: int
    retrieval_time_ms: float
    crag_decision: str = Field(..., description="RELEVANT | PARTIAL | IRRELEVANT")
    crag_score: float = Field(..., ge=0.0, le=1.0)
    correction_applied: bool
    correction_strategy: str = Field(..., description="query_expansion | web_search | none")
    original_artifacts_count: int
    web_search_used: bool = False
    cache_hit: bool = False

    # Detailed evaluation metrics
    keyword_overlap: float = 0.0
    semantic_coherence: float = 0.0
    length_adequacy: float = 0.0
    diversity: float = 0.0

    class Config:
        arbitrary_types_allowed = True


class CRAGOrchestrator:
    """Corrective RAG orchestrator integrating evaluation and correction.

    Workflow:
    1. Initial retrieval via CGRAG
    2. Relevance evaluation (fast heuristics)
    3. Decision routing:
       - RELEVANT: Return as-is (fast path)
       - PARTIAL: Query expansion + re-retrieval
       - IRRELEVANT: Web search augmentation
    4. Return corrected results with metadata
    """

    def __init__(
        self,
        cgrag_retriever: CGRAGRetriever,
        enable_web_search: bool = True,
        enable_query_expansion: bool = True
    ):
        """Initialize CRAG orchestrator.

        Args:
            cgrag_retriever: CGRAG retriever instance
            enable_web_search: Enable web search fallback (default: True)
            enable_query_expansion: Enable query expansion (default: True)
        """
        self.cgrag_retriever = cgrag_retriever
        self.evaluator = CRAGEvaluator()
        self.expander = QueryExpander() if enable_query_expansion else None
        self.augmenter = WebSearchAugmenter() if enable_web_search else None

        logger.info(
            f"Initialized CRAG: web_search={enable_web_search}, "
            f"query_expansion={enable_query_expansion}"
        )

    async def retrieve(
        self,
        query: str,
        token_budget: int = 8000,
        max_artifacts: int = 20
    ) -> CRAGResult:
        """Retrieve with corrective RAG workflow.

        Args:
            query: Query text
            token_budget: Maximum tokens for artifacts
            max_artifacts: Maximum artifacts to retrieve

        Returns:
            CRAGResult with corrected artifacts and metadata
        """
        start_time = time.time()

        # Step 1: Initial CGRAG retrieval
        logger.info(f"[CRAG] Initial retrieval: query='{query[:50]}...'")
        cgrag_result = await self.cgrag_retriever.retrieve(
            query=query,
            token_budget=token_budget,
            max_artifacts=max_artifacts
        )

        # Step 2: Relevance evaluation
        logger.info(f"[CRAG] Evaluating {len(cgrag_result.artifacts)} artifacts")
        relevance_eval = await self.evaluator.evaluate(
            query=query,
            artifacts=cgrag_result.artifacts,
            relevance_scores=cgrag_result.top_scores
        )

        logger.info(
            f"[CRAG] Evaluation: {relevance_eval.category} "
            f"(score={relevance_eval.score:.2f})"
        )

        # Step 3: Decision routing
        final_artifacts = cgrag_result.artifacts
        correction_applied = False
        correction_strategy = "none"
        web_search_used = False

        if relevance_eval.category == "RELEVANT":
            # Fast path - use original artifacts
            logger.info("[CRAG] Fast path: Using original artifacts")
            correction_strategy = "none"

        elif relevance_eval.category == "PARTIAL" and self.expander:
            # Query expansion + re-retrieval
            logger.info("[CRAG] Applying query expansion")
            expanded_query = self.expander.expand(query)
            logger.debug(f"[CRAG] Expanded query: '{expanded_query}'")

            # Re-retrieve with expanded query
            expanded_result = await self.cgrag_retriever.retrieve(
                query=expanded_query,
                token_budget=token_budget,
                max_artifacts=max_artifacts
            )

            # Merge original + expanded results
            final_artifacts = self._merge_artifacts(
                cgrag_result.artifacts,
                expanded_result.artifacts,
                token_budget
            )

            correction_applied = True
            correction_strategy = "query_expansion"
            logger.info(
                f"[CRAG] Merged {len(final_artifacts)} artifacts "
                f"(original: {len(cgrag_result.artifacts)}, "
                f"expanded: {len(expanded_result.artifacts)})"
            )

        elif relevance_eval.category == "IRRELEVANT" and self.augmenter:
            # Web search augmentation
            logger.info("[CRAG] Fallback to web search")
            web_chunks = await self.augmenter.augment(query)

            if web_chunks:
                final_artifacts = web_chunks
                correction_applied = True
                correction_strategy = "web_search"
                web_search_used = True
                logger.info(f"[CRAG] Retrieved {len(web_chunks)} web results")
            else:
                logger.warning("[CRAG] Web search failed, using original artifacts")

        else:
            # Correction disabled or failed - use original artifacts
            logger.info("[CRAG] No correction applied (disabled or unavailable)")

        # Calculate final token usage
        tokens_used = sum(
            self._estimate_tokens(chunk.content)
            for chunk in final_artifacts
        )

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"[CRAG] Complete in {elapsed_ms:.1f}ms: "
            f"{len(final_artifacts)} artifacts, {tokens_used} tokens, "
            f"correction={correction_strategy}"
        )

        return CRAGResult(
            artifacts=final_artifacts,
            tokens_used=tokens_used,
            retrieval_time_ms=elapsed_ms,
            crag_decision=relevance_eval.category,
            crag_score=relevance_eval.score,
            correction_applied=correction_applied,
            correction_strategy=correction_strategy,
            original_artifacts_count=len(cgrag_result.artifacts),
            web_search_used=web_search_used,
            cache_hit=cgrag_result.cache_hit,
            keyword_overlap=relevance_eval.keyword_overlap,
            semantic_coherence=relevance_eval.semantic_coherence,
            length_adequacy=relevance_eval.length_adequacy,
            diversity=relevance_eval.diversity
        )

    def _merge_artifacts(
        self,
        original: List[DocumentChunk],
        expanded: List[DocumentChunk],
        token_budget: int
    ) -> List[DocumentChunk]:
        """Merge original and expanded artifacts using deduplication.

        Combines results while avoiding duplicates and respecting token budget.

        Args:
            original: Original retrieval artifacts
            expanded: Query-expanded retrieval artifacts
            token_budget: Maximum tokens

        Returns:
            Merged artifact list
        """
        # Deduplicate by chunk ID
        seen_ids = set()
        merged = []
        total_tokens = 0

        # Process original artifacts first (higher priority)
        for chunk in original:
            if chunk.id not in seen_ids:
                chunk_tokens = self._estimate_tokens(chunk.content)
                if total_tokens + chunk_tokens <= token_budget:
                    merged.append(chunk)
                    seen_ids.add(chunk.id)
                    total_tokens += chunk_tokens

        # Add new artifacts from expanded results
        for chunk in expanded:
            if chunk.id not in seen_ids:
                chunk_tokens = self._estimate_tokens(chunk.content)
                if total_tokens + chunk_tokens <= token_budget:
                    merged.append(chunk)
                    seen_ids.add(chunk.id)
                    total_tokens += chunk_tokens

        return merged

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (word-based heuristic)."""
        return int(len(text.split()) * 1.3)


# Import component classes (defined earlier in this document)
from .crag_evaluator import CRAGEvaluator
from .query_expander import QueryExpander
from .web_augmenter import WebSearchAugmenter
```

---

## Integration with Query Router

**Modify:** `backend/app/routers/query.py`

**Changes:**

1. Add CRAG toggle to `QueryRequest`
2. Use `CRAGOrchestrator` instead of `CGRAGRetriever` when enabled
3. Add CRAG metadata to `QueryMetadata`

```python
# In backend/app/models/query.py
class QueryRequest(BaseModel):
    # ... existing fields ...

    use_crag: bool = Field(
        default=True,
        alias="useCrag",
        description="Enable Corrective RAG (self-correcting retrieval)"
    )

# In backend/app/models/query.py
class QueryMetadata(BaseModel):
    # ... existing fields ...

    # CRAG metadata
    crag_decision: Optional[str] = Field(
        default=None,
        alias="cragDecision",
        description="CRAG relevance category (RELEVANT/PARTIAL/IRRELEVANT)"
    )
    crag_score: Optional[float] = Field(
        default=None,
        alias="cragScore",
        description="CRAG aggregate relevance score (0.0-1.0)"
    )
    crag_correction_strategy: Optional[str] = Field(
        default=None,
        alias="cragCorrectionStrategy",
        description="Correction strategy applied (query_expansion/web_search/none)"
    )
    crag_web_search_used: bool = Field(
        default=False,
        alias="cragWebSearchUsed",
        description="Whether web search fallback was triggered"
    )

# In backend/app/routers/query.py
from app.services.crag import CRAGOrchestrator

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    # ... existing setup ...

    # Context retrieval
    cgrag_result = None
    if request.use_context:
        try:
            # Load CGRAG indexer
            index_dir, index_path, metadata_path = get_cgrag_index_paths("docs")
            indexer = CGRAGIndexer.load_index(index_path, metadata_path)

            if request.use_crag:
                # Use CRAG orchestrator
                retriever = CGRAGRetriever(indexer)
                crag_orchestrator = CRAGOrchestrator(
                    cgrag_retriever=retriever,
                    enable_web_search=request.use_web_search,
                    enable_query_expansion=True
                )
                crag_result = await crag_orchestrator.retrieve(
                    query=request.query,
                    token_budget=8000
                )
                cgrag_result = crag_result  # Use CRAG result
            else:
                # Use standard CGRAG retriever
                retriever = CGRAGRetriever(indexer)
                cgrag_result = await retriever.retrieve(
                    query=request.query,
                    token_budget=8000
                )
        except Exception as e:
            logger.error(f"CGRAG retrieval failed: {e}")

    # ... model invocation ...

    # Build metadata
    metadata = QueryMetadata(
        # ... existing fields ...

        # CRAG metadata
        crag_decision=crag_result.crag_decision if hasattr(crag_result, 'crag_decision') else None,
        crag_score=crag_result.crag_score if hasattr(crag_result, 'crag_score') else None,
        crag_correction_strategy=crag_result.correction_strategy if hasattr(crag_result, 'correction_strategy') else None,
        crag_web_search_used=crag_result.web_search_used if hasattr(crag_result, 'web_search_used') else False
    )

    # ... return response ...
```

---

## Performance Optimization

### 1. Fast-Path Caching

**Strategy:** Cache CRAG evaluation results to avoid re-evaluation for repeated queries.

```python
import redis
import json
from typing import Optional

class CRAGCache:
    """Redis cache for CRAG evaluation results."""

    def __init__(self, redis_client: redis.Redis, ttl: int = 3600):
        """Initialize cache.

        Args:
            redis_client: Redis client instance
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.ttl = ttl

    def get_evaluation(self, query: str) -> Optional[RelevanceScore]:
        """Get cached evaluation result."""
        cache_key = f"crag:eval:{hash(query)}"
        cached = self.redis.get(cache_key)

        if cached:
            data = json.loads(cached)
            return RelevanceScore(**data)

        return None

    def set_evaluation(self, query: str, evaluation: RelevanceScore):
        """Cache evaluation result."""
        cache_key = f"crag:eval:{hash(query)}"
        self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(evaluation.__dict__)
        )
```

### 2. Lazy Web Search

**Strategy:** Only trigger web search if IRRELEVANT category AND web search enabled.

Already implemented in `CRAGOrchestrator` with conditional checks.

### 3. Parallel Execution

**Strategy:** Run query expansion retrieval in parallel with original retrieval for PARTIAL category.

```python
# In CRAGOrchestrator.retrieve()
elif relevance_eval.category == "PARTIAL" and self.expander:
    expanded_query = self.expander.expand(query)

    # Run original and expanded retrieval in parallel
    original_task = self.cgrag_retriever.retrieve(query, token_budget, max_artifacts)
    expanded_task = self.cgrag_retriever.retrieve(expanded_query, token_budget, max_artifacts)

    original_result, expanded_result = await asyncio.gather(
        original_task,
        expanded_task
    )

    final_artifacts = self._merge_artifacts(
        original_result.artifacts,
        expanded_result.artifacts,
        token_budget
    )
```

---

## Testing Strategy

### Unit Tests

**File:** `backend/tests/test_crag.py`

```python
import pytest
from app.services.crag import CRAGEvaluator, QueryExpander, CRAGOrchestrator
from app.services.cgrag import DocumentChunk

@pytest.mark.asyncio
async def test_evaluator_relevant():
    """Test evaluator classifies high-quality retrieval as RELEVANT."""
    evaluator = CRAGEvaluator()

    query = "Python async patterns"
    artifacts = [
        DocumentChunk(
            file_path="docs/async.md",
            content="Async patterns in Python use asyncio library for concurrent execution",
            chunk_index=0,
            start_pos=0,
            end_pos=100
        )
    ]
    relevance_scores = [0.92]

    result = await evaluator.evaluate(query, artifacts, relevance_scores)

    assert result.category == "RELEVANT"
    assert result.score > 0.75
    assert result.keyword_overlap > 0.5

@pytest.mark.asyncio
async def test_evaluator_irrelevant():
    """Test evaluator classifies poor retrieval as IRRELEVANT."""
    evaluator = CRAGEvaluator()

    query = "Kubernetes deployment strategies"
    artifacts = [
        DocumentChunk(
            file_path="docs/frontend.md",
            content="React components use hooks for state management",
            chunk_index=0,
            start_pos=0,
            end_pos=50
        )
    ]
    relevance_scores = [0.35]

    result = await evaluator.evaluate(query, artifacts, relevance_scores)

    assert result.category == "IRRELEVANT"
    assert result.score < 0.50

def test_query_expander():
    """Test query expansion with synonyms."""
    expander = QueryExpander()

    query = "explain async function"
    expanded = expander.expand(query)

    # Should contain original terms + synonyms
    assert "async" in expanded
    assert "asynchronous" in expanded or "concurrent" in expanded
    assert "explain" in expanded
    assert "describe" in expanded or "clarify" in expanded

@pytest.mark.asyncio
async def test_crag_orchestrator_fast_path(mock_cgrag_retriever):
    """Test CRAG fast path (RELEVANT category)."""
    orchestrator = CRAGOrchestrator(
        cgrag_retriever=mock_cgrag_retriever,
        enable_web_search=False,
        enable_query_expansion=False
    )

    result = await orchestrator.retrieve(
        query="Python async patterns",
        token_budget=5000
    )

    assert result.crag_decision == "RELEVANT"
    assert result.correction_applied is False
    assert result.correction_strategy == "none"
    assert result.retrieval_time_ms < 100  # Fast path
```

### Integration Tests

**File:** `backend/tests/test_crag_integration.py`

```python
@pytest.mark.asyncio
async def test_crag_end_to_end_with_query_expansion():
    """Test full CRAG workflow with query expansion."""
    # Setup CGRAG indexer with test documents
    indexer = CGRAGIndexer()
    await indexer.index_directory(Path("tests/fixtures/docs"))

    retriever = CGRAGRetriever(indexer)
    orchestrator = CRAGOrchestrator(
        cgrag_retriever=retriever,
        enable_web_search=False,
        enable_query_expansion=True
    )

    # Query that should trigger PARTIAL -> query expansion
    result = await orchestrator.retrieve(
        query="code review best practices",
        token_budget=5000
    )

    assert result.crag_decision in ["PARTIAL", "RELEVANT"]
    assert len(result.artifacts) > 0

    if result.correction_applied:
        assert result.correction_strategy == "query_expansion"

@pytest.mark.asyncio
async def test_crag_web_search_fallback(mock_searxng):
    """Test CRAG web search fallback for IRRELEVANT queries."""
    # Setup with empty CGRAG index
    indexer = CGRAGIndexer()
    retriever = CGRAGRetriever(indexer)

    orchestrator = CRAGOrchestrator(
        cgrag_retriever=retriever,
        enable_web_search=True
    )

    # Query completely unrelated to indexed content
    result = await orchestrator.retrieve(
        query="latest SpaceX launch updates",
        token_budget=5000
    )

    assert result.crag_decision == "IRRELEVANT"
    assert result.web_search_used is True
    assert result.correction_strategy == "web_search"
```

---

## Metrics and Monitoring

### Key Metrics to Track

| Metric | Purpose | Target |
|--------|---------|--------|
| **CRAG Decision Distribution** | % of RELEVANT/PARTIAL/IRRELEVANT | 70% RELEVANT |
| **Correction Rate** | % of queries requiring correction | <30% |
| **Web Search Trigger Rate** | % of queries using web search | <10% |
| **Fast Path Latency** | P50 latency for RELEVANT path | <70ms |
| **Corrected Path Latency** | P50 latency with correction | <450ms |
| **Correction Success Rate** | % of corrections improving score | >80% |

### Logging

```python
# In CRAGOrchestrator.retrieve()
logger.info(
    f"[CRAG_METRICS] decision={relevance_eval.category} "
    f"score={relevance_eval.score:.2f} "
    f"correction={correction_strategy} "
    f"latency_ms={elapsed_ms:.1f} "
    f"artifacts={len(final_artifacts)}"
)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# CRAG decision counters
crag_decisions = Counter(
    'crag_decisions_total',
    'Total CRAG decisions by category',
    ['category']
)

# CRAG correction strategy counters
crag_corrections = Counter(
    'crag_corrections_total',
    'Total corrections by strategy',
    ['strategy']
)

# CRAG latency histogram
crag_latency = Histogram(
    'crag_retrieval_latency_seconds',
    'CRAG retrieval latency',
    ['decision', 'correction_strategy']
)

# CRAG relevance score gauge
crag_relevance_score = Gauge(
    'crag_relevance_score',
    'Current CRAG relevance score'
)
```

---

## File Structure Summary

### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/crag.py` | Main CRAG orchestrator |
| `backend/app/services/crag_evaluator.py` | Relevance evaluator (heuristics) |
| `backend/app/services/query_expander.py` | Query expansion logic |
| `backend/app/services/web_augmenter.py` | Web search augmentation |
| `backend/tests/test_crag.py` | Unit tests |
| `backend/tests/test_crag_integration.py` | Integration tests |

### Files to Modify

| File | Changes |
|------|---------|
| `backend/app/models/query.py` | Add `use_crag` field, CRAG metadata fields |
| `backend/app/routers/query.py` | Integrate CRAG orchestrator |
| `backend/requirements.txt` | No new dependencies (uses existing libs) |

---

## Migration Strategy

### Phase 1: Core Implementation (Week 1)

1. Implement `CRAGEvaluator` with heuristics
2. Implement `QueryExpander` with synonym mappings
3. Implement `WebSearchAugmenter` (thin wrapper around existing SearXNG)
4. Write unit tests for each component

### Phase 2: Integration (Week 2)

1. Implement `CRAGOrchestrator` combining all components
2. Integrate with query router
3. Add CRAG metadata to response models
4. Write integration tests

### Phase 3: Optimization & Monitoring (Week 3)

1. Add Redis caching for evaluations
2. Implement Prometheus metrics
3. Performance benchmarking
4. Documentation and user guide

### Rollout Strategy

**Enable CRAG gradually:**

1. **Week 1:** `use_crag=false` by default (opt-in)
2. **Week 2:** `use_crag=true` by default (opt-out) after validation
3. **Week 3:** Remove toggle, make CRAG mandatory

---

## Expected Results

### Before CRAG (Current System)

```
Query: "How to optimize React performance?"

[CGRAG] Retrieved 8 artifacts (5200 tokens) in 95ms
Artifacts:
  1. docs/react-basics.md (score: 0.78) - General React intro
  2. docs/python-async.md (score: 0.42) - Irrelevant
  3. docs/database-tuning.md (score: 0.38) - Irrelevant
  ...

Average Relevance: 0.53 (PARTIAL)
Irrelevant Artifacts: 40%
```

### After CRAG (With Correction)

```
Query: "How to optimize React performance?"

[CRAG] Initial retrieval: 8 artifacts
[CRAG] Evaluation: PARTIAL (score=0.58)
[CRAG] Applying query expansion
[CRAG] Expanded query: "optimize enhance improve react performance speed efficiency"
[CRAG] Re-retrieved: 12 artifacts
[CRAG] Merged: 10 artifacts (6800 tokens) in 180ms

Final Artifacts:
  1. docs/react-performance.md (score: 0.91) - Highly relevant
  2. docs/react-optimization.md (score: 0.89) - Highly relevant
  3. docs/react-memoization.md (score: 0.85) - Relevant
  ...

Average Relevance: 0.84 (RELEVANT)
Irrelevant Artifacts: 5%
Correction: query_expansion
```

---

## Limitations and Future Work

### Current Limitations

1. **Heuristic-based evaluation** - No LLM for quality assessment (fast but less accurate)
2. **Simple synonym expansion** - Limited domain coverage
3. **No reranking** - Could improve with cross-encoder reranking

### Future Enhancements

1. **LLM-based evaluator** (optional, slower) - Use small model for quality checks
2. **Learned query expansion** - Train model for domain-specific expansions
3. **Cross-encoder reranking** - Rerank retrieved chunks with cross-encoder model
4. **Adaptive thresholds** - Learn optimal thresholds from user feedback

---

## References

### Research Sources

- **Russian Research:** Adaptive RAG with retrieval evaluator and web search fallback
- **Korean Research:** AutoRAG optimization framework with quality assessment
- **Chinese Research:** QAnything 2-stage reranking (related concept)
- **German Research:** Fraunhofer Knowledge Graph RAG (future integration)

### Related Documentation

- [CGRAG Enhancement Plan](./CGRAG_ENHANCEMENT_PLAN.md) - Hybrid search + KG-RAG
- [Global RAG Research](../research/GLOBAL_RAG_RESEARCH.md) - Full research findings
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Recent development history

---

**Next Steps:**

1. Review this design document
2. Implement Phase 1 components (evaluator, expander, augmenter)
3. Write unit tests
4. Integrate with query router
5. Benchmark and optimize
6. Gradual rollout with monitoring

**Questions or concerns? Please review and provide feedback before implementation begins.**
