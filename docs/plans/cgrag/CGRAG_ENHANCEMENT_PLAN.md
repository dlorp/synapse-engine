# CGRAG Enhancement Implementation Plan

**Date:** 2025-11-30
**Status:** Approved - Ready for Implementation
**Estimated Time:** 8-10 weeks (expanded with new features)
**Index:** [README.md](./README.md)

---

## Executive Summary

This plan enhances the S.Y.N.A.P.S.E. ENGINE CGRAG system with cutting-edge techniques discovered through global research across 7 languages (English, Chinese, Japanese, Korean, German, French, Russian).

### Approved Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Enhancement Priority** | Hybrid Search + Two-Stage Reranking | +15-25% accuracy (Chinese research) |
| **Vector Database** | Qdrant primary, FAISS fallback | Performance + compatibility |
| **Reranker Model** | cross-encoder/ms-marco-MiniLM-L-6-v2 | No new deps (uses sentence-transformers) |
| **Context Sources** | Docs, Codebase, Chat History (NO web search) | Privacy compliance |
| **Retrieval Routing** | Adaptive strategy selection | 30-40% cost reduction (Russian research) |

### Expected Improvements

| Metric | Current | Target | Source | Phase |
|--------|---------|--------|--------|-------|
| Retrieval Latency | <100ms | **<65ms** | Super RAG (French) | 1 |
| Top-1 Accuracy | ~70% | **85%** | QAnything (Chinese) | 2 |
| Overall Accuracy | ~70% | **90%** | Russian Phase 3 | 3-5 |
| Hallucination Rate | ~10% | **<3%** | Fraunhofer KG-RAG | 3 |
| Context Relevance | - | **>0.8** | Mistral RAG Triad | 4 |
| Cache Hit Rate | N/A | **>75%** | Production optimizations | 1-2 |
| Cost Reduction | - | **30-40%** | Adaptive Routing (Russian) | 5 |

### Enhancement Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CGRAG Enhancement Pipeline                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Query → [Adaptive Router] → Strategy Selection                     │
│              │                                                      │
│              ├─> NO_RETRIEVAL → Direct to LLM                       │
│              │                                                      │
│              └─> RETRIEVAL:                                         │
│                    │                                                │
│                    ├─> Stage 1: Hybrid Search (Vector + BM25)       │
│                    │        ↓                                       │
│                    ├─> Stage 2: Cross-Encoder Reranking             │
│                    │        ↓                                       │
│                    ├─> Knowledge Graph Enhancement                  │
│                    │        ↓                                       │
│                    └─> CRAG Quality Check → [Corrective Actions]    │
│                              ↓                                      │
│                         Context → LLM → Response                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Hybrid Search + Vector DB Migration (Week 1-2)

**Priority:** HIGH | **Impact:** Better code/technical queries

### 1A. Migrate to Qdrant (with FAISS fallback)

- Primary: Qdrant for Metal-enabled environments (macOS, Apple Silicon)
- Fallback: FAISS for Docker containers without Metal support
- Automatic detection based on environment

```python
# Vector DB Factory Pattern
from abc import ABC, abstractmethod
from typing import List, Tuple
import os

class VectorDB(ABC):
    @abstractmethod
    async def search(self, query_embedding: List[float], k: int) -> List[Tuple[str, float]]:
        pass

    @abstractmethod
    async def add(self, doc_id: str, embedding: List[float], metadata: dict):
        pass

class VectorDBFactory:
    @staticmethod
    def create(config: 'VectorDBConfig') -> VectorDB:
        if config.use_metal and is_metal_available():
            return QdrantVectorDB(config)
        else:
            return FAISSVectorDB(config)  # Default fallback

def is_metal_available() -> bool:
    """Check if running on Apple Silicon with Metal support"""
    import platform
    return (
        platform.system() == "Darwin" and
        platform.processor() == "arm" and
        os.environ.get("ENABLE_METAL", "true").lower() == "true"
    )
```

### 1B. Add BM25 Hybrid Search

Combine vector similarity with keyword search using Reciprocal Rank Fusion:

```python
from collections import defaultdict
from rank_bm25 import BM25Okapi
from typing import List, Tuple

class HybridRetriever:
    def __init__(self, vector_db: VectorDB, chunks: List['Chunk']):
        self.vector_db = vector_db
        self.chunks = chunks
        self.bm25 = self._build_bm25_index(chunks)

    def _build_bm25_index(self, chunks: List['Chunk']) -> BM25Okapi:
        tokenized_docs = [chunk.text.lower().split() for chunk in chunks]
        return BM25Okapi(tokenized_docs)

    async def retrieve(self, query: str, query_embedding: List[float], k: int = 10) -> List['Chunk']:
        # Parallel retrieval
        vector_results = await self.vector_db.search(query_embedding, k=k*2)
        bm25_scores = self.bm25.get_scores(query.lower().split())

        # Get top BM25 results
        bm25_top_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:k*2]
        bm25_results = [(self.chunks[i].id, bm25_scores[i]) for i in bm25_top_indices]

        # Reciprocal Rank Fusion
        return self._rrf_combine(vector_results, bm25_results, k=k)

    def _rrf_combine(
        self,
        vector_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        k: int,
        constant: int = 60
    ) -> List['Chunk']:
        """Combine results using Reciprocal Rank Fusion"""
        scores = defaultdict(float)

        for rank, (doc_id, _) in enumerate(vector_results):
            scores[doc_id] += 1.0 / (constant + rank)

        for rank, (doc_id, _) in enumerate(bm25_results):
            scores[doc_id] += 1.0 / (constant + rank)

        # Sort by combined score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:k]

        # Return chunks
        chunk_map = {c.id: c for c in self.chunks}
        return [chunk_map[doc_id] for doc_id in sorted_ids if doc_id in chunk_map]
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/vector_db.py` | CREATE | Vector DB abstraction |
| `backend/app/services/cgrag.py` | MODIFY | Add hybrid retrieval |
| `backend/requirements.txt` | MODIFY | Add qdrant-client, rank_bm25 |
| `docker-compose.yml` | MODIFY | Optional Qdrant service |

### Dependencies

```txt
qdrant-client>=1.7.0
rank_bm25>=0.2.2
```

---

## Phase 1.5: Two-Stage Reranking (Week 2-3)

**Priority:** HIGH | **Impact:** +15-25% accuracy
**Design Doc:** [CGRAG_TWO_STAGE_RERANKING.md](./CGRAG_TWO_STAGE_RERANKING.md)
**Quick Start:** [CGRAG_RERANKING_QUICK_START.md](./CGRAG_RERANKING_QUICK_START.md)

Based on Chinese QAnything pattern - treat reranking as PRIMARY, not optional.

### The QAnything Pattern

```
Query → Stage 1: Coarse Retrieval (top 100) → Stage 2: Fine Reranking (threshold > 0.35)
```

**Key Insight:** "More data = better results" - opposite of pure vector search logic.

### 1.5A. Reranker Model Integration

```python
from sentence_transformers import CrossEncoder
from typing import List, Tuple
import hashlib

class RerankerModel:
    """Cross-encoder reranker with smart skip logic."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        min_query_length: int = 5,
        batch_size: int = 32
    ):
        self.model = CrossEncoder(model_name)
        self.min_query_length = min_query_length
        self.batch_size = batch_size

    def should_skip(self, query: str, num_candidates: int) -> bool:
        """Skip reranking for simple queries or few candidates."""
        word_count = len(query.split())
        return word_count < self.min_query_length or num_candidates <= 3

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, str, float]]  # (id, text, initial_score)
    ) -> List[Tuple[str, float]]:
        """Rerank candidates using cross-encoder."""
        if self.should_skip(query, len(candidates)):
            return [(c[0], c[2]) for c in candidates]  # Return original scores

        # Prepare pairs for cross-encoder
        pairs = [(query, text) for _, text, _ in candidates]

        # Batch scoring
        scores = self.model.predict(pairs, batch_size=self.batch_size)

        # Combine with IDs and sort
        results = [(candidates[i][0], float(scores[i])) for i in range(len(candidates))]
        results.sort(key=lambda x: x[1], reverse=True)

        return results
```

### 1.5B. Reranker Cache

```python
import redis
import json

class RerankerCache:
    """Redis cache for reranking results."""

    def __init__(self, redis_client: redis.Redis, ttl: int = 259200):  # 3 days
        self.redis = redis_client
        self.ttl = ttl

    def _cache_key(self, query: str, candidate_ids: List[str]) -> str:
        """Generate cache key from query and sorted candidate IDs."""
        query_hash = hashlib.sha256(query.lower().encode()).hexdigest()[:16]
        ids_hash = hashlib.sha256(",".join(sorted(candidate_ids)).encode()).hexdigest()[:16]
        return f"rerank:{query_hash}:{ids_hash}"

    def get(self, query: str, candidate_ids: List[str]) -> Optional[List[Tuple[str, float]]]:
        """Get cached reranking results."""
        key = self._cache_key(query, candidate_ids)
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    def set(self, query: str, candidate_ids: List[str], results: List[Tuple[str, float]]):
        """Cache reranking results."""
        key = self._cache_key(query, candidate_ids)
        self.redis.setex(key, self.ttl, json.dumps(results))
```

### 1.5C. Enhanced CGRAGRetriever

```python
class EnhancedCGRAGRetriever:
    """Two-stage retrieval: coarse + rerank."""

    def __init__(
        self,
        indexer: CGRAGIndexer,
        reranker: RerankerModel,
        cache: RerankerCache,
        coarse_k: int = 100,
        final_k: int = 20,
        rerank_threshold: float = 0.35
    ):
        self.indexer = indexer
        self.reranker = reranker
        self.cache = cache
        self.coarse_k = coarse_k
        self.final_k = final_k
        self.rerank_threshold = rerank_threshold

    async def retrieve(self, query: str, token_budget: int = 8000) -> CGRAGResult:
        """Two-stage retrieval with caching."""
        # Stage 1: Coarse retrieval
        coarse_results = await self._coarse_retrieve(query, k=self.coarse_k)

        # Check reranker cache
        candidate_ids = [r.id for r in coarse_results]
        cached = self.cache.get(query, candidate_ids)

        if cached:
            # Cache hit - use cached scores
            reranked = cached
            cache_hit = True
        else:
            # Stage 2: Rerank
            candidates = [(c.id, c.content, c.relevance_score) for c in coarse_results]
            reranked = self.reranker.rerank(query, candidates)
            self.cache.set(query, candidate_ids, reranked)
            cache_hit = False

        # Filter by threshold and pack
        chunk_map = {c.id: c for c in coarse_results}
        filtered = [
            (chunk_map[id], score)
            for id, score in reranked
            if score >= self.rerank_threshold and id in chunk_map
        ]

        # Token budget packing
        selected, tokens_used = self._pack_artifacts(filtered, token_budget)

        return CGRAGResult(
            artifacts=selected,
            tokens_used=tokens_used,
            candidates_considered=len(coarse_results),
            retrieval_time_ms=...,
            cache_hit=cache_hit,
            rerank_applied=True
        )
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/reranker.py` | CREATE | Reranker model wrapper |
| `backend/app/services/reranker_cache.py` | CREATE | Redis cache for reranking |
| `backend/app/services/cgrag.py` | MODIFY | Add two-stage retrieval |

### Performance Expectations

| Metric | Without Reranking | With Reranking | Impact |
|--------|------------------|----------------|--------|
| Top-1 Relevance | 0.70 | **0.85** | +21% |
| Latency (cache miss) | 30ms | 70ms | +133% |
| Latency (cache hit) | 30ms | **5ms** | -83% |
| Average Latency | 30ms | **~26ms** | -13% |

---

## Phase 2: Knowledge Graph RAG Integration (Week 3-4)

**Priority:** HIGH | **Impact:** Significantly reduced hallucinations

Based on Fraunhofer Austria research - combine vector search with symbolic graph reasoning.

### 2A. Entity Extraction During Indexing

```python
import spacy
import networkx as nx
from dataclasses import dataclass
from typing import List, Set

@dataclass
class Entity:
    text: str
    label: str
    chunk_id: str

@dataclass
class Relationship:
    source: str
    target: str
    relation_type: str
    chunk_id: str

class KnowledgeGraphBuilder:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.graph = nx.DiGraph()
        self.entity_to_chunks: dict[str, Set[str]] = {}

    def extract_entities(self, chunk: 'Chunk') -> List[Entity]:
        """Extract named entities from a chunk"""
        doc = self.nlp(chunk.text)
        entities = []

        for ent in doc.ents:
            entity = Entity(
                text=ent.text.lower(),
                label=ent.label_,
                chunk_id=chunk.id
            )
            entities.append(entity)

            # Map entity to chunks
            if entity.text not in self.entity_to_chunks:
                self.entity_to_chunks[entity.text] = set()
            self.entity_to_chunks[entity.text].add(chunk.id)

        return entities

    def build_relationships(self, entities: List[Entity]):
        """Build co-occurrence relationships between entities"""
        # Group by chunk
        chunk_entities: dict[str, List[Entity]] = {}
        for entity in entities:
            if entity.chunk_id not in chunk_entities:
                chunk_entities[entity.chunk_id] = []
            chunk_entities[entity.chunk_id].append(entity)

        # Create edges for co-occurring entities
        for chunk_id, ents in chunk_entities.items():
            for i, e1 in enumerate(ents):
                for e2 in ents[i+1:]:
                    self.graph.add_edge(
                        e1.text, e2.text,
                        type="co-occurs",
                        chunk_id=chunk_id
                    )

    def find_related_chunks(self, query_entities: List[str], hops: int = 2) -> Set[str]:
        """Find chunks related to query entities via graph traversal"""
        related_chunks = set()

        for entity in query_entities:
            entity_lower = entity.lower()
            if entity_lower in self.graph:
                # Direct chunks
                if entity_lower in self.entity_to_chunks:
                    related_chunks.update(self.entity_to_chunks[entity_lower])

                # Multi-hop neighbors
                for neighbor in nx.single_source_shortest_path_length(
                    self.graph, entity_lower, cutoff=hops
                ):
                    if neighbor in self.entity_to_chunks:
                        related_chunks.update(self.entity_to_chunks[neighbor])

        return related_chunks
```

### 2B. Graph-Enhanced Retrieval

```python
class GraphRAGRetriever:
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        knowledge_graph: KnowledgeGraphBuilder
    ):
        self.hybrid_retriever = hybrid_retriever
        self.kg = knowledge_graph
        self.nlp = spacy.load("en_core_web_sm")

    def extract_query_entities(self, query: str) -> List[str]:
        """Extract entities from the query"""
        doc = self.nlp(query)
        return [ent.text for ent in doc.ents]

    async def retrieve(self, query: str, query_embedding: List[float], k: int = 10) -> List['Chunk']:
        # Step 1: Hybrid retrieval
        vector_results = await self.hybrid_retriever.retrieve(query, query_embedding, k=k*2)

        # Step 2: Entity extraction from query
        query_entities = self.extract_query_entities(query)

        # Step 3: Graph traversal for related chunks
        graph_chunk_ids = self.kg.find_related_chunks(query_entities, hops=2)

        # Step 4: Combine and deduplicate
        result_ids = set(chunk.id for chunk in vector_results)
        combined_ids = result_ids.union(graph_chunk_ids)

        # Step 5: Rerank combined results (vector results first, then graph additions)
        chunk_map = {c.id: c for c in self.hybrid_retriever.chunks}
        final_results = []

        # Add vector results first (already ranked)
        for chunk in vector_results:
            if chunk.id in combined_ids:
                final_results.append(chunk)
                combined_ids.discard(chunk.id)

        # Add graph-only results
        for chunk_id in combined_ids:
            if chunk_id in chunk_map:
                final_results.append(chunk_map[chunk_id])

        return final_results[:k]
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/knowledge_graph.py` | CREATE | KG builder |
| `backend/app/services/cgrag.py` | MODIFY | Integrate graph retrieval |
| `backend/app/models/cgrag.py` | CREATE | Entity/Relationship models |
| `backend/requirements.txt` | MODIFY | Add spacy, networkx |

### Dependencies

```txt
spacy>=3.7.0
networkx>=3.0
```

**Post-install:** `python -m spacy download en_core_web_sm`

---

## Phase 3: Multi-Context Source Management (Week 4-5)

**Priority:** MEDIUM | **Impact:** Context source flexibility

Enable multiple context sources (NO web search for privacy).

### Context Source Registry

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ContextSourceConfig:
    name: str
    enabled: bool = True
    weight: float = 1.0
    max_chunks: int = 10

class ContextSource(ABC):
    def __init__(self, config: ContextSourceConfig):
        self.config = config

    @abstractmethod
    async def get_context(self, query: str, **kwargs) -> List['Chunk']:
        pass

    @property
    def enabled(self) -> bool:
        return self.config.enabled

class DocumentationSource(ContextSource):
    def __init__(self, config: ContextSourceConfig, index_path: str):
        super().__init__(config)
        self.index_path = index_path

    async def get_context(self, query: str, **kwargs) -> List['Chunk']:
        # Use existing CGRAG retrieval for documentation
        return await self.retriever.retrieve(query, k=self.config.max_chunks)

class CodebaseSource(ContextSource):
    def __init__(self, config: ContextSourceConfig, extensions: List[str]):
        super().__init__(config)
        self.extensions = extensions

    async def get_context(self, query: str, **kwargs) -> List['Chunk']:
        # AST-based code retrieval
        return await self.code_retriever.retrieve(query, k=self.config.max_chunks)

class ChatHistorySource(ContextSource):
    def __init__(self, config: ContextSourceConfig, max_turns: int = 10):
        super().__init__(config)
        self.max_turns = max_turns

    async def get_context(self, query: str, session_id: str = None, **kwargs) -> List['Chunk']:
        if not session_id:
            return []
        return await self.get_session_history(session_id)

class ContextSourceRegistry:
    def __init__(self):
        self.sources: Dict[str, ContextSource] = {}

    def register(self, name: str, source: ContextSource):
        self.sources[name] = source

    def get_enabled_sources(self) -> List[ContextSource]:
        return [s for s in self.sources.values() if s.enabled]

    async def get_all_context(self, query: str, **kwargs) -> List['Chunk']:
        """Retrieve context from all enabled sources"""
        all_chunks = []
        for source in self.get_enabled_sources():
            chunks = await source.get_context(query, **kwargs)
            # Weight chunks by source weight
            for chunk in chunks:
                chunk.source_weight = source.config.weight
            all_chunks.extend(chunks)

        # Sort by weighted relevance
        all_chunks.sort(key=lambda c: c.relevance * c.source_weight, reverse=True)
        return all_chunks
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/context_sources.py` | CREATE | Context source abstraction |
| `backend/app/services/cgrag.py` | MODIFY | Multi-source retrieval |
| `frontend/src/components/admin/CGRAGIndexer.tsx` | MODIFY | UI for source management |

---

## Phase 4: Chat History Context (Week 5-6)

**Priority:** MEDIUM | **Impact:** Conversation continuity

### Chat History Service

```python
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ConversationTurn:
    id: str
    session_id: str
    query: str
    response: str
    timestamp: datetime
    model_used: str
    tokens_used: int

class ChatHistoryService:
    def __init__(self, db, max_turns: int = 10, max_tokens: int = 2000):
        self.db = db
        self.max_turns = max_turns
        self.max_tokens = max_tokens

    async def add_turn(self, turn: ConversationTurn):
        """Add a conversation turn to history"""
        await self.db.insert("conversation_turns", turn.__dict__)

    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Get conversation history for a session"""
        limit = limit or self.max_turns
        rows = await self.db.query(
            "conversation_turns",
            where={"session_id": session_id},
            order_by="timestamp DESC",
            limit=limit
        )
        return [ConversationTurn(**row) for row in rows]

    async def get_context_chunks(self, session_id: str) -> List['Chunk']:
        """Convert history to context chunks"""
        history = await self.get_session_history(session_id)

        chunks = []
        total_tokens = 0

        for turn in reversed(history):  # Oldest first for context
            chunk_text = f"User: {turn.query}\nAssistant: {turn.response}"
            chunk_tokens = len(chunk_text.split()) * 1.3  # Rough estimate

            if total_tokens + chunk_tokens > self.max_tokens:
                break

            chunks.append(Chunk(
                id=f"chat_{turn.id}",
                text=chunk_text,
                source="chat_history",
                metadata={
                    "turn_id": turn.id,
                    "timestamp": turn.timestamp.isoformat(),
                    "model": turn.model_used
                }
            ))
            total_tokens += chunk_tokens

        return chunks
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/chat_history.py` | CREATE | Chat history management |
| `backend/app/models/session.py` | CREATE | Session/conversation models |
| `backend/app/routers/query.py` | MODIFY | Include chat context |

---

## Phase 5: AST-Based Code Chunking (Week 6-7)

**Priority:** MEDIUM | **Impact:** Better code retrieval

Based on Mistral research - use AST parser for meaningful code chunks.

### Code Chunker

```python
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser

@dataclass
class CodeChunk:
    id: str
    text: str
    file_path: str
    chunk_type: str  # function, class, method
    name: str
    start_line: int
    end_line: int
    language: str

class CodeChunker:
    def __init__(self):
        self.parsers = {
            ".py": self._create_python_parser(),
            ".ts": self._create_typescript_parser(),
            ".tsx": self._create_typescript_parser(),
            ".js": self._create_typescript_parser(),
            ".jsx": self._create_typescript_parser(),
        }

        self.node_types = {
            "python": ["function_definition", "class_definition", "decorated_definition"],
            "typescript": ["function_declaration", "class_declaration", "method_definition",
                          "arrow_function", "function_expression"]
        }

    def _create_python_parser(self) -> Parser:
        parser = Parser()
        parser.set_language(Language(tspython.language(), "python"))
        return parser

    def _create_typescript_parser(self) -> Parser:
        parser = Parser()
        parser.set_language(Language(tstypescript.language_typescript(), "typescript"))
        return parser

    def chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk a source file using AST parsing"""
        ext = Path(file_path).suffix
        parser = self.parsers.get(ext)

        if parser:
            return self._ast_chunk(content, parser, file_path, ext)
        else:
            return self._fallback_chunk(content, file_path)

    def _ast_chunk(
        self,
        content: str,
        parser: Parser,
        file_path: str,
        ext: str
    ) -> List[CodeChunk]:
        """Extract semantic chunks using AST"""
        tree = parser.parse(bytes(content, "utf8"))
        chunks = []
        language = "python" if ext == ".py" else "typescript"

        for node in self._walk_tree(tree.root_node):
            if node.type in self.node_types.get(language, []):
                chunk_text = content[node.start_byte:node.end_byte]
                name = self._get_node_name(node, content)

                chunks.append(CodeChunk(
                    id=f"{file_path}:{node.start_point[0]}:{name}",
                    text=chunk_text,
                    file_path=file_path,
                    chunk_type=node.type,
                    name=name,
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                    language=language
                ))

        # If no chunks found, fall back to file-level chunk
        if not chunks:
            chunks = self._fallback_chunk(content, file_path)

        return chunks

    def _walk_tree(self, node):
        """Walk AST tree yielding all nodes"""
        yield node
        for child in node.children:
            yield from self._walk_tree(child)

    def _get_node_name(self, node, content: str) -> str:
        """Extract the name of a function/class"""
        for child in node.children:
            if child.type in ["identifier", "name", "property_identifier"]:
                return content[child.start_byte:child.end_byte]
        return "anonymous"

    def _fallback_chunk(self, content: str, file_path: str) -> List[CodeChunk]:
        """Fallback: chunk by line count"""
        lines = content.split('\n')
        chunk_size = 50  # lines per chunk
        chunks = []

        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunks.append(CodeChunk(
                id=f"{file_path}:{i}:chunk",
                text='\n'.join(chunk_lines),
                file_path=file_path,
                chunk_type="file_segment",
                name=f"lines_{i}_{i + len(chunk_lines)}",
                start_line=i,
                end_line=i + len(chunk_lines),
                language="unknown"
            ))

        return chunks
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/chunkers/code_chunker.py` | CREATE | AST chunking |
| `backend/app/services/cgrag.py` | MODIFY | Use code chunker |

### Dependencies

```txt
tree-sitter>=0.21.0
tree-sitter-python>=0.21.0
tree-sitter-typescript>=0.21.0
```

---

## Summary: Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/vector_db.py` | Vector DB abstraction (Qdrant + FAISS) |
| `backend/app/services/knowledge_graph.py` | Knowledge graph builder |
| `backend/app/services/context_sources.py` | Multi-source context registry |
| `backend/app/services/chat_history.py` | Chat history context source |
| `backend/app/services/chunkers/code_chunker.py` | AST-based code chunking |
| `backend/app/models/cgrag.py` | Entity/Relationship models |
| `backend/app/models/session.py` | Session/conversation models |

## Summary: Files to Modify

| File | Changes |
|------|---------|
| `backend/app/services/cgrag.py` | Add hybrid search, graph integration |
| `backend/app/routers/cgrag.py` | Multi-source context endpoints |
| `backend/app/routers/query.py` | Include chat history context |
| `backend/requirements.txt` | Add new dependencies |
| `docker-compose.yml` | Optional Qdrant service |
| `frontend/src/components/admin/CGRAGIndexer.tsx` | UI for context sources |

## All New Dependencies

```txt
# Vector DB
qdrant-client>=1.7.0

# Hybrid Search
rank_bm25>=0.2.2

# Knowledge Graph
spacy>=3.7.0
networkx>=3.0

# Code Chunking
tree-sitter>=0.21.0
tree-sitter-python>=0.21.0
tree-sitter-typescript>=0.21.0
```

---

## Phase 6: Adaptive Routing + Corrective RAG (Week 8-10)

**Priority:** HIGH | **Impact:** 30-40% cost reduction + improved reliability
**Design Docs:**
- [ADAPTIVE_QUERY_ROUTING_DESIGN.md](./ADAPTIVE_QUERY_ROUTING_DESIGN.md)
- [CORRECTIVE_RAG_DESIGN.md](./CORRECTIVE_RAG_DESIGN.md)

### 6A. Adaptive Query Routing

Based on Russian Adaptive RAG research - skip retrieval when unnecessary.

```python
from enum import Enum
from typing import Tuple
import re

class RetrievalStrategy(Enum):
    NO_RETRIEVAL = "no_retrieval"      # Direct to LLM
    SINGLE_RETRIEVAL = "single"         # Standard CGRAG
    MULTI_STEP = "multi_step"           # Iterative retrieval
    KNOWLEDGE_GRAPH = "knowledge_graph" # Graph-enhanced

class QueryClassifier:
    """Classify queries to select retrieval strategy."""

    GREETING_PATTERNS = [
        r"^(hi|hello|hey|good morning|good afternoon|good evening)",
        r"^(thanks|thank you|thx)",
        r"^(bye|goodbye|see you)",
    ]

    ARITHMETIC_PATTERNS = [
        r"^what\s+is\s+\d+\s*[\+\-\*\/]\s*\d+",
        r"^calculate\s+\d+",
        r"^how\s+much\s+is\s+\d+",
    ]

    def classify(self, query: str) -> Tuple[RetrievalStrategy, str]:
        """Classify query and return strategy with reasoning."""
        query_lower = query.lower().strip()

        # Check greeting patterns
        for pattern in self.GREETING_PATTERNS:
            if re.match(pattern, query_lower):
                return RetrievalStrategy.NO_RETRIEVAL, "Greeting detected"

        # Check arithmetic patterns
        for pattern in self.ARITHMETIC_PATTERNS:
            if re.match(pattern, query_lower):
                return RetrievalStrategy.NO_RETRIEVAL, "Arithmetic query"

        # Check complexity indicators
        word_count = len(query.split())
        has_analysis = any(w in query_lower for w in ["analyze", "compare", "evaluate"])
        has_multi_part = " and " in query_lower or " then " in query_lower

        if word_count > 30 or (has_analysis and has_multi_part):
            return RetrievalStrategy.MULTI_STEP, "Complex query requiring multi-step"

        return RetrievalStrategy.SINGLE_RETRIEVAL, "Standard factual query"
```

### 6B. Corrective RAG (CRAG)

Based on Korean/Russian research - self-correct retrieval results.

```python
from enum import Enum
from dataclasses import dataclass

class CRAGAction(Enum):
    RELEVANT = "relevant"       # Use context as-is
    PARTIAL = "partial"         # Expand query, retry
    IRRELEVANT = "irrelevant"   # Fall back to web search

@dataclass
class CRAGDecision:
    action: CRAGAction
    confidence: float
    reasoning: str
    corrections_applied: List[str]

class CRAGEvaluator:
    """Evaluate retrieval quality and decide on corrections."""

    def __init__(
        self,
        relevance_threshold: float = 0.75,
        partial_threshold: float = 0.50,
        min_keyword_overlap: float = 0.3
    ):
        self.relevance_threshold = relevance_threshold
        self.partial_threshold = partial_threshold
        self.min_keyword_overlap = min_keyword_overlap

    def evaluate(
        self,
        query: str,
        artifacts: List[DocumentChunk]
    ) -> CRAGDecision:
        """Evaluate retrieval quality using multi-criteria scoring."""
        if not artifacts:
            return CRAGDecision(
                action=CRAGAction.IRRELEVANT,
                confidence=1.0,
                reasoning="No artifacts retrieved",
                corrections_applied=[]
            )

        # Calculate metrics
        avg_score = sum(a.relevance_score for a in artifacts) / len(artifacts)
        keyword_overlap = self._calculate_keyword_overlap(query, artifacts)
        score_variance = self._calculate_variance([a.relevance_score for a in artifacts])

        # Multi-criteria evaluation
        semantic_score = avg_score * 0.4
        keyword_score = keyword_overlap * 0.3
        coherence_score = (1 - min(score_variance, 0.5)) * 0.15
        length_score = min(len(artifacts) / 10, 1.0) * 0.15

        total_score = semantic_score + keyword_score + coherence_score + length_score

        # Decide action
        if total_score >= self.relevance_threshold:
            return CRAGDecision(
                action=CRAGAction.RELEVANT,
                confidence=total_score,
                reasoning=f"High relevance: {total_score:.2f}",
                corrections_applied=[]
            )
        elif total_score >= self.partial_threshold:
            return CRAGDecision(
                action=CRAGAction.PARTIAL,
                confidence=total_score,
                reasoning=f"Partial relevance: {total_score:.2f}",
                corrections_applied=["query_expansion"]
            )
        else:
            return CRAGDecision(
                action=CRAGAction.IRRELEVANT,
                confidence=total_score,
                reasoning=f"Low relevance: {total_score:.2f}",
                corrections_applied=["web_search_fallback"]
            )

    def _calculate_keyword_overlap(
        self,
        query: str,
        artifacts: List[DocumentChunk]
    ) -> float:
        """Calculate keyword overlap between query and artifacts."""
        query_words = set(query.lower().split())
        artifact_text = " ".join(a.content for a in artifacts).lower()
        artifact_words = set(artifact_text.split())

        if not query_words:
            return 0.0

        overlap = len(query_words & artifact_words) / len(query_words)
        return overlap
```

### 6C. CRAG Orchestrator

```python
class CRAGOrchestrator:
    """Orchestrate CRAG pipeline with corrections."""

    def __init__(
        self,
        retriever: EnhancedCGRAGRetriever,
        evaluator: CRAGEvaluator,
        query_expander: 'QueryExpander',
        web_augmenter: Optional['WebSearchAugmenter'] = None,
        max_retries: int = 2
    ):
        self.retriever = retriever
        self.evaluator = evaluator
        self.query_expander = query_expander
        self.web_augmenter = web_augmenter
        self.max_retries = max_retries

    async def retrieve_with_correction(
        self,
        query: str,
        token_budget: int = 8000
    ) -> Tuple[CGRAGResult, CRAGDecision]:
        """Retrieve with automatic quality correction."""
        # Initial retrieval
        result = await self.retriever.retrieve(query, token_budget)
        decision = self.evaluator.evaluate(query, result.artifacts)

        if decision.action == CRAGAction.RELEVANT:
            return result, decision

        # Attempt corrections
        if decision.action == CRAGAction.PARTIAL:
            # Expand query and retry
            expanded = self.query_expander.expand(query)
            result2 = await self.retriever.retrieve(expanded, token_budget)
            decision2 = self.evaluator.evaluate(query, result2.artifacts)

            if decision2.confidence > decision.confidence:
                decision2.corrections_applied.append("query_expanded")
                return result2, decision2

        elif decision.action == CRAGAction.IRRELEVANT and self.web_augmenter:
            # Fall back to web search
            web_results = await self.web_augmenter.search(query)
            if web_results:
                decision.corrections_applied.append("web_augmented")
                # Merge with any existing results
                result.artifacts.extend(web_results[:5])
                return result, decision

        return result, decision
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/query_classifier.py` | CREATE | Adaptive routing |
| `backend/app/services/crag_evaluator.py` | CREATE | CRAG quality evaluation |
| `backend/app/services/query_expander.py` | CREATE | Query expansion |
| `backend/app/services/crag.py` | CREATE | CRAG orchestrator |
| `backend/app/routers/query.py` | MODIFY | Integrate adaptive routing |
| `backend/app/models/query.py` | MODIFY | Add RetrievalStrategy enum |

### Performance Impact

| Query Type | Current | With Adaptive | Savings |
|-----------|---------|---------------|---------|
| Greetings | 2000ms | **1200ms** | 40% |
| Arithmetic | 2000ms | **1300ms** | 35% |
| Simple facts | 5000ms | 5000ms | 0% |
| Complex | 15000ms | 15000ms | 0% |

**Overall Cost Reduction:** ~30% (based on 30% simple query volume)

---

## Summary: Complete Implementation Timeline

| Phase | Weeks | Features | Impact |
|-------|-------|----------|--------|
| **1** | 1-2 | Hybrid Search + Qdrant | +15% accuracy, -35% latency |
| **1.5** | 2-3 | Two-Stage Reranking | +21% Top-1 accuracy |
| **2** | 3-4 | Knowledge Graph RAG | -70% hallucinations |
| **3** | 4-5 | Multi-Context Sources | Context flexibility |
| **4** | 5-6 | Chat History | Conversation continuity |
| **5** | 6-7 | AST Code Chunking | Better code retrieval |
| **6** | 8-10 | Adaptive Routing + CRAG | -30% costs, self-correction |

**Total Estimated Time:** 8-10 weeks

---

## Related Documentation

### Design Documents
- [Two-Stage Reranking](./CGRAG_TWO_STAGE_RERANKING.md)
- [Hybrid Search](./HYBRID_SEARCH_DESIGN.md)
- [Adaptive Routing](./ADAPTIVE_QUERY_ROUTING_DESIGN.md)
- [Corrective RAG](./CORRECTIVE_RAG_DESIGN.md)
- [Context Enhancement](./CGRAG_CONTEXT_ENHANCEMENT_DESIGN.md)

### Quick Start Guides
- [Reranking Quick Start](./CGRAG_RERANKING_QUICK_START.md)
- [Quick Start Guide](./CGRAG_QUICK_START_GUIDE.md)
- [Adaptive Routing Summary](./ADAPTIVE_ROUTING_SUMMARY.md)
- [CRAG Implementation Summary](./CRAG_IMPLEMENTATION_SUMMARY.md)

### Infrastructure
- [Infrastructure Deployment](./CGRAG_INFRASTRUCTURE_DEPLOYMENT.md)
- [Infrastructure Summary](./CGRAG_INFRASTRUCTURE_SUMMARY.md)
- [Infrastructure Quick Reference](./CGRAG_INFRASTRUCTURE_QUICKREF.md)

### Frontend
- [Visualization Guide](./CGRAG_VISUALIZATION_GUIDE.md)
- [Component Spec](./CGRAG_COMPONENT_SPEC.md)

### Research
- [Global RAG Research](../../research/GLOBAL_RAG_RESEARCH.md)
- [SESSION_NOTES.md](../../../SESSION_NOTES.md)
