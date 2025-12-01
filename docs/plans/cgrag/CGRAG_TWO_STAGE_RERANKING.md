# CGRAG Two-Stage Reranking Implementation Plan

**Date:** 2025-11-30
**Status:** Implementation Design Ready
**Estimated Time:** 1-2 weeks
**Priority:** HIGH - Foundation for Phase 1 Hybrid Search

---

## Executive Summary

Implement a production-grade Two-Stage Reranking system based on the QAnything pattern from Chinese RAG research. This enhancement will improve retrieval accuracy by 15-25% while maintaining <100ms latency targets.

### Key Design Decisions

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| **Reranker Model** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Lightweight (80MB), fast inference (~10ms/pair), good accuracy |
| **Stage 1 Candidates** | Top 100 chunks | QAnything pattern - "more data = better results" |
| **Stage 2 Threshold** | 0.35 | Chinese research standard for relevance filtering |
| **Batch Processing** | 32 pairs/batch | Balance latency vs throughput |
| **Caching Strategy** | Query + candidates hash | Avoid reranking same results |
| **Skip Logic** | Simple queries (<5 words) | Use vector-only for speed |

### Expected Improvements

| Metric | Current | Target | Source |
|--------|---------|--------|--------|
| **Accuracy** | ~70% | **85-90%** | QAnything pattern |
| **Top-1 Relevance** | ~0.7 | **>0.8** | Cross-encoder reranking |
| **Retrieval Latency** | ~50ms | **<100ms** | Batched processing |
| **Context Quality** | Good | **Excellent** | Better ordering |

---

## Part 1: Architecture Design

### 1.1 System Overview

```
Query → Embedding → Stage 1: Vector Search (top 100) → Stage 2: Reranking (threshold > 0.35) → Token Budget Packing → Response
                                ↓                                      ↓
                         FAISS Index                          Cross-Encoder Model
                         (fast, coarse)                      (slow, precise)
```

### 1.2 Integration Points

**Current Flow (cgrag.py:503-578):**
```python
async def retrieve(query, token_budget, max_artifacts=20):
    1. Embed query
    2. FAISS search (k = max_artifacts * 5)
    3. Filter by min_relevance=0.7
    4. Pack within token budget
    5. Return CGRAGResult
```

**New Flow with Two-Stage Reranking:**
```python
async def retrieve(query, token_budget, max_artifacts=20, use_reranking=True):
    1. Embed query
    2. STAGE 1: FAISS search (k = 100)  # Coarse retrieval
    3. STAGE 2: Rerank with cross-encoder (threshold > 0.35)  # Fine-grained
    4. Pack within token budget (using reranked scores)
    5. Return CGRAGResult with reranking metadata
```

### 1.3 Component Architecture

```python
# New components to add to cgrag.py

class RerankerModel:
    """Cross-encoder reranker for fine-grained relevance scoring"""
    - __init__(model_name: str)
    - async rank_pairs(query: str, candidates: List[DocumentChunk], batch_size: int) -> List[Tuple[DocumentChunk, float]]
    - _should_skip_reranking(query: str) -> bool

class RerankerCache:
    """Redis cache for reranking results"""
    - __init__(redis_client: Redis, ttl: int = 3600)
    - async get(cache_key: str) -> Optional[List[Tuple[str, float]]]
    - async set(cache_key: str, results: List[Tuple[str, float]])
    - _generate_cache_key(query: str, candidate_ids: List[str]) -> str

class CGRAGRetriever:
    """Enhanced with two-stage retrieval"""
    - reranker: Optional[RerankerModel]
    - reranker_cache: Optional[RerankerCache]
    - rerank_threshold: float = 0.35
    - stage1_candidates: int = 100
```

---

## Part 2: Implementation Details

### 2.1 RerankerModel Class

**File:** `backend/app/services/cgrag.py` (add after DocumentChunk class)

```python
import asyncio
from sentence_transformers import CrossEncoder
from typing import List, Tuple, Optional

class RerankerModel:
    """Cross-encoder reranker for fine-grained relevance scoring.

    Uses cross-encoder models that jointly encode query + document pairs
    for more accurate relevance scoring compared to bi-encoders.

    Attributes:
        model: CrossEncoder model for scoring query-document pairs
        model_name: Name of the cross-encoder model
        batch_size: Batch size for inference
    """

    # Lightweight, fast cross-encoder with good accuracy
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Minimum query length to use reranking (words)
    MIN_QUERY_LENGTH = 5

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialize reranker with cross-encoder model.

        Args:
            model_name: Name of cross-encoder model from sentence-transformers
        """
        logger.info(f"Initializing RerankerModel with: {model_name}")
        self.model_name = model_name
        self.model = CrossEncoder(model_name)
        logger.info(f"Reranker loaded: {model_name}")

    async def rank_pairs(
        self,
        query: str,
        candidates: List[DocumentChunk],
        batch_size: int = 32
    ) -> List[Tuple[DocumentChunk, float]]:
        """Rerank candidates using cross-encoder.

        Args:
            query: Query text
            candidates: Candidate chunks from Stage 1 retrieval
            batch_size: Batch size for cross-encoder inference

        Returns:
            List of (chunk, rerank_score) tuples sorted by score descending
        """
        if not candidates:
            return []

        # Check if we should skip reranking
        if self._should_skip_reranking(query):
            logger.debug("Skipping reranking for simple query")
            # Return candidates with their vector scores
            return [(c, c.relevance_score) for c in candidates]

        logger.debug(f"Reranking {len(candidates)} candidates (batch_size={batch_size})")
        start_time = time.time()

        # Create query-document pairs
        pairs = [[query, chunk.content] for chunk in candidates]

        # Run cross-encoder in batches (async execution)
        loop = asyncio.get_event_loop()
        predict_fn = lambda: self.model.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        scores = await loop.run_in_executor(None, predict_fn)

        # Combine chunks with scores
        ranked_results = [
            (chunk, float(score))
            for chunk, score in zip(candidates, scores)
        ]

        # Sort by rerank score (descending)
        ranked_results.sort(key=lambda x: x[1], reverse=True)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Reranked {len(candidates)} candidates in {elapsed_ms:.1f}ms "
            f"({len(candidates)/elapsed_ms*1000:.1f} candidates/sec)"
        )

        return ranked_results

    def _should_skip_reranking(self, query: str) -> bool:
        """Determine if reranking should be skipped for this query.

        Skip reranking for simple queries to save latency. Vector-only
        retrieval is sufficient for short, simple queries.

        Args:
            query: Query text

        Returns:
            True if reranking should be skipped
        """
        word_count = len(query.split())
        return word_count < self.MIN_QUERY_LENGTH
```

### 2.2 RerankerCache Class

**File:** `backend/app/services/cgrag.py` (add after RerankerModel)

```python
import hashlib
import json
from typing import Optional, List, Tuple

class RerankerCache:
    """Redis cache for reranking results.

    Caches reranked results to avoid redundant cross-encoder inference.
    Cache key is hash of (query + sorted_candidate_ids) to ensure cache
    hits when same query + candidates are presented.

    Attributes:
        redis_client: Redis client instance
        ttl: Cache TTL in seconds (default 1 hour)
        key_prefix: Redis key prefix for reranker cache
    """

    DEFAULT_TTL = 3600  # 1 hour
    KEY_PREFIX = "cgrag:rerank:"

    def __init__(self, redis_client, ttl: int = DEFAULT_TTL):
        """Initialize reranker cache.

        Args:
            redis_client: Redis client instance (can be None to disable caching)
            ttl: Cache TTL in seconds
        """
        self.redis_client = redis_client
        self.ttl = ttl
        self.enabled = redis_client is not None

        if self.enabled:
            logger.info(f"RerankerCache enabled (TTL={ttl}s)")
        else:
            logger.warning("RerankerCache disabled (no Redis client)")

    async def get(
        self,
        query: str,
        candidate_ids: List[str]
    ) -> Optional[List[Tuple[str, float]]]:
        """Get cached reranking results.

        Args:
            query: Query text
            candidate_ids: List of candidate chunk IDs

        Returns:
            List of (chunk_id, rerank_score) tuples if cached, None otherwise
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(query, candidate_ids)

        try:
            cached_value = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.get(cache_key)
            )

            if cached_value:
                logger.debug(f"Reranker cache HIT: {cache_key[:32]}...")
                return json.loads(cached_value)
            else:
                logger.debug(f"Reranker cache MISS: {cache_key[:32]}...")
                return None
        except Exception as e:
            logger.warning(f"Reranker cache GET failed: {e}")
            return None

    async def set(
        self,
        query: str,
        candidate_ids: List[str],
        results: List[Tuple[str, float]]
    ) -> None:
        """Cache reranking results.

        Args:
            query: Query text
            candidate_ids: List of candidate chunk IDs
            results: List of (chunk_id, rerank_score) tuples
        """
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(query, candidate_ids)

        try:
            cache_value = json.dumps(results)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.setex(cache_key, self.ttl, cache_value)
            )
            logger.debug(f"Reranker cache SET: {cache_key[:32]}...")
        except Exception as e:
            logger.warning(f"Reranker cache SET failed: {e}")

    def _generate_cache_key(self, query: str, candidate_ids: List[str]) -> str:
        """Generate cache key from query and candidate IDs.

        Args:
            query: Query text
            candidate_ids: List of candidate chunk IDs (unsorted)

        Returns:
            SHA256 hash of (query + sorted_candidate_ids)
        """
        # Sort candidate IDs for consistent cache keys
        sorted_ids = sorted(candidate_ids)

        # Create hash input
        hash_input = json.dumps({
            "query": query,
            "candidate_ids": sorted_ids
        }, sort_keys=True)

        # Generate SHA256 hash
        hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()

        return f"{self.KEY_PREFIX}{hash_digest}"
```

### 2.3 Enhanced CGRAGRetriever Class

**File:** `backend/app/services/cgrag.py` (modify existing class at line 475-636)

```python
class CGRAGRetriever:
    """Retrieves relevant context using two-stage retrieval.

    Stage 1: FAISS vector similarity search (coarse, fast, top 100)
    Stage 2: Cross-encoder reranking (fine-grained, slower, threshold > 0.35)

    Implements token budget management with greedy packing algorithm.
    Supports Redis caching for embeddings and reranking results.

    Attributes:
        indexer: CGRAGIndexer with loaded index
        min_relevance: Minimum relevance threshold for Stage 1 (0.0-1.0)
        reranker: Optional RerankerModel for Stage 2
        reranker_cache: Optional RerankerCache for caching rerank results
        rerank_threshold: Minimum threshold for Stage 2 reranking (default 0.35)
        stage1_candidates: Number of candidates to retrieve in Stage 1 (default 100)
    """

    def __init__(
        self,
        indexer: CGRAGIndexer,
        min_relevance: float = 0.7,
        use_reranking: bool = True,
        rerank_threshold: float = 0.35,
        stage1_candidates: int = 100,
        redis_client = None
    ):
        """Initialize retriever with indexer and optional reranking.

        Args:
            indexer: CGRAGIndexer instance with loaded index
            min_relevance: Minimum relevance threshold for Stage 1 filtering
            use_reranking: Enable two-stage reranking (default True)
            rerank_threshold: Minimum threshold for Stage 2 (default 0.35)
            stage1_candidates: Number of candidates from Stage 1 (default 100)
            redis_client: Redis client for caching (optional)
        """
        self.indexer = indexer
        self.min_relevance = min_relevance
        self.rerank_threshold = rerank_threshold
        self.stage1_candidates = stage1_candidates

        if self.indexer.index is None:
            raise ValueError("Indexer has no index. Load or build index first.")

        # Initialize reranker if enabled
        if use_reranking:
            try:
                self.reranker = RerankerModel()
                self.reranker_cache = RerankerCache(redis_client)
                logger.info("Two-stage reranking ENABLED")
            except Exception as e:
                logger.error(f"Failed to initialize reranker: {e}")
                logger.warning("Falling back to vector-only retrieval")
                self.reranker = None
                self.reranker_cache = None
        else:
            self.reranker = None
            self.reranker_cache = None
            logger.info("Two-stage reranking DISABLED (vector-only)")

    async def retrieve(
        self,
        query: str,
        token_budget: int = 8000,
        max_artifacts: int = 20,
        use_reranking: Optional[bool] = None
    ) -> CGRAGResult:
        """Retrieve relevant artifacts using two-stage retrieval.

        STAGE 1: FAISS vector search for initial candidates (fast, coarse)
        STAGE 2: Cross-encoder reranking for fine-grained relevance (slow, precise)

        Args:
            query: Query text
            token_budget: Maximum tokens to retrieve
            max_artifacts: Maximum number of artifacts to return
            use_reranking: Override instance setting for this query (optional)

        Returns:
            CGRAGResult with artifacts and metadata (including reranking stats)
        """
        start_time = time.time()

        # Determine if reranking should be used
        should_rerank = (
            (use_reranking if use_reranking is not None else self.reranker is not None)
            and self.reranker is not None
        )

        # Embed query
        loop = asyncio.get_event_loop()
        encode_fn = lambda: self.indexer.encoder.encode(
            [query],
            show_progress_bar=False,
            convert_to_numpy=True
        )
        query_embedding = await loop.run_in_executor(None, encode_fn)
        query_embedding = query_embedding[0].reshape(1, -1)

        # Normalize query embedding to match indexed embeddings
        faiss.normalize_L2(query_embedding)

        # === STAGE 1: COARSE VECTOR RETRIEVAL ===
        k_stage1 = self.stage1_candidates if should_rerank else min(max_artifacts * 5, len(self.indexer.chunks))
        distances, indices = self.indexer.index.search(query_embedding, k_stage1)

        # Convert normalized L2 distances to cosine similarity scores
        vector_scores = 1.0 - (distances[0] / 2.0)

        # Create candidate chunks with vector scores
        candidates = []
        for idx, score in zip(indices[0], vector_scores):
            if idx >= 0 and idx < len(self.indexer.chunks):  # Valid index
                chunk = self.indexer.chunks[idx].model_copy()
                chunk.relevance_score = float(score)
                candidates.append(chunk)

        # Filter by minimum vector relevance (Stage 1 threshold)
        candidates = [c for c in candidates if c.relevance_score >= self.min_relevance]

        logger.info(f"STAGE 1: Retrieved {len(candidates)} candidates (vector search)")

        # === STAGE 2: FINE-GRAINED RERANKING ===
        if should_rerank and candidates:
            # Check cache first
            cache_hit = False
            ranked_results = None

            if self.reranker_cache:
                candidate_ids = [c.id for c in candidates]
                cached_results = await self.reranker_cache.get(query, candidate_ids)

                if cached_results:
                    # Reconstruct chunks from cached (id, score) pairs
                    chunk_map = {c.id: c for c in candidates}
                    ranked_results = [
                        (chunk_map[chunk_id], score)
                        for chunk_id, score in cached_results
                        if chunk_id in chunk_map
                    ]
                    cache_hit = True
                    logger.info("STAGE 2: Reranking results from CACHE")

            # Run reranker if no cache hit
            if not cache_hit:
                ranked_results = await self.reranker.rank_pairs(query, candidates)

                # Cache results
                if self.reranker_cache:
                    cache_data = [(chunk.id, score) for chunk, score in ranked_results]
                    candidate_ids = [c.id for c in candidates]
                    await self.reranker_cache.set(query, candidate_ids, cache_data)

            # Filter by rerank threshold
            ranked_results = [
                (chunk, score)
                for chunk, score in ranked_results
                if score >= self.rerank_threshold
            ]

            # Update chunk relevance scores with rerank scores
            for chunk, rerank_score in ranked_results:
                chunk.relevance_score = rerank_score

            # Extract chunks (already sorted by rerank score)
            selected_candidates = [chunk for chunk, _ in ranked_results]

            logger.info(
                f"STAGE 2: Reranked to {len(selected_candidates)} candidates "
                f"(threshold={self.rerank_threshold})"
            )
        else:
            # No reranking - use vector scores (already sorted)
            selected_candidates = sorted(
                candidates,
                key=lambda c: c.relevance_score,
                reverse=True
            )
            logger.info("STAGE 2: SKIPPED (using vector scores)")

        # === TOKEN BUDGET PACKING ===
        selected_chunks, tokens_used = self._pack_artifacts(selected_candidates, token_budget)

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
            cache_hit=False,  # Query embedding cache (not implemented yet)
            top_scores=top_scores
        )

    # Keep existing _pack_artifacts and _count_tokens methods unchanged
    # (lines 580-636 in current implementation)
```

### 2.4 Enhanced CGRAGResult Model

**File:** `backend/app/services/cgrag.py` (modify existing class at line 87-104)

```python
class CGRAGResult(BaseModel):
    """Result from CGRAG retrieval operation.

    Attributes:
        artifacts: Retrieved document chunks
        tokens_used: Total tokens in retrieved artifacts
        candidates_considered: Number of candidates before filtering
        retrieval_time_ms: Retrieval operation latency
        cache_hit: Whether result was served from cache
        top_scores: Relevance scores of top artifacts
        reranking_used: Whether two-stage reranking was used
        stage1_candidates: Number of candidates from Stage 1 (if reranking)
        stage2_candidates: Number of candidates after Stage 2 (if reranking)
    """
    artifacts: List[DocumentChunk]
    tokens_used: int
    candidates_considered: int
    retrieval_time_ms: float
    cache_hit: bool = False
    top_scores: List[float] = Field(default_factory=list)

    # Reranking metadata (optional)
    reranking_used: bool = False
    stage1_candidates: int = 0
    stage2_candidates: int = 0
```

---

## Part 3: Configuration & Runtime Settings

### 3.1 Runtime Settings Schema

**File:** `backend/app/models/settings.py` (add to RuntimeSettings class)

```python
class CGRAGSettings(BaseModel):
    """CGRAG configuration settings"""
    # Existing settings
    embedding_model: str = "all-MiniLM-L6-v2"
    index_directory: str = "data/faiss_indexes"
    default_chunk_size: int = 512
    default_chunk_overlap: int = 50

    # NEW: Two-stage reranking settings
    use_reranking: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_threshold: float = 0.35
    stage1_candidates: int = 100
    reranker_cache_ttl: int = 3600  # 1 hour
    min_query_length_for_reranking: int = 5

class RuntimeSettings(BaseModel):
    # ... existing fields ...
    cgrag: CGRAGSettings = Field(default_factory=CGRAGSettings)
```

### 3.2 Profile Configuration

**File:** `config/profiles/development.yaml`

```yaml
# CGRAG Configuration
cgrag:
  embedding_model: "all-MiniLM-L6-v2"
  index_directory: "data/faiss_indexes"
  default_chunk_size: 512
  default_chunk_overlap: 50

  # Two-Stage Reranking
  use_reranking: true
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  rerank_threshold: 0.35
  stage1_candidates: 100
  reranker_cache_ttl: 3600
  min_query_length_for_reranking: 5
```

---

## Part 4: Performance Optimization

### 4.1 Latency Budget Breakdown

**Target: <100ms total retrieval time**

| Stage | Operation | Target Latency | Notes |
|-------|-----------|----------------|-------|
| **Pre-Stage** | Query embedding | ~10ms | Cached after first run |
| **Stage 1** | FAISS search (100 candidates) | ~15ms | Fast approximate search |
| **Stage 2** | Cross-encoder reranking (100 pairs) | ~40ms | Batched inference (32/batch) |
| **Post-Stage** | Token budget packing | ~5ms | Simple greedy algorithm |
| **Total** | | **~70ms** | Well under 100ms target |

### 4.2 Optimization Strategies

#### 4.2.1 Skip Reranking for Simple Queries

```python
def _should_skip_reranking(self, query: str) -> bool:
    """Skip reranking for queries with <5 words"""
    word_count = len(query.split())
    return word_count < 5  # Configurable via settings
```

**Impact:** Saves ~40ms for simple queries (57% latency reduction)

#### 4.2.2 Batch Processing

```python
# Process candidates in batches of 32 for optimal GPU utilization
scores = self.model.predict(pairs, batch_size=32)
```

**Impact:** 3-4x faster than sequential processing

#### 4.2.3 Caching Strategy

```python
# Cache key: hash(query + sorted_candidate_ids)
cache_key = sha256(json.dumps({"query": query, "candidate_ids": sorted(ids)}))
```

**Cache Hit Rate Target:** >70% (based on Chinese research standards)

**Impact:** Near-instant retrieval (<5ms) on cache hit

#### 4.2.4 Async Execution

```python
# Run cross-encoder in thread pool to avoid blocking event loop
loop = asyncio.get_event_loop()
scores = await loop.run_in_executor(None, lambda: self.model.predict(...))
```

**Impact:** Allows concurrent requests during reranking

### 4.3 Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Cross-encoder model | ~80MB | Loaded once, shared across requests |
| Batch inference (32 pairs) | ~50MB | Temporary during reranking |
| Redis cache | ~10MB | 1000 cached queries @ ~10KB each |
| **Total Additional** | **~140MB** | Acceptable for production |

---

## Part 5: Testing & Validation

### 5.1 Unit Tests

**File:** `backend/tests/test_cgrag_reranking.py` (NEW)

```python
import pytest
from app.services.cgrag import RerankerModel, RerankerCache, CGRAGRetriever, DocumentChunk

@pytest.mark.asyncio
async def test_reranker_initialization():
    """Test reranker model loads correctly"""
    reranker = RerankerModel()
    assert reranker.model is not None
    assert reranker.model_name == RerankerModel.DEFAULT_MODEL

@pytest.mark.asyncio
async def test_reranker_ranking():
    """Test reranker produces correct ordering"""
    reranker = RerankerModel()

    chunks = [
        DocumentChunk(
            file_path="test.md",
            content="Python is a programming language",
            chunk_index=0,
            start_pos=0,
            end_pos=100
        ),
        DocumentChunk(
            file_path="test.md",
            content="The weather is sunny today",
            chunk_index=1,
            start_pos=100,
            end_pos=200
        ),
    ]

    query = "python programming"
    results = await reranker.rank_pairs(query, chunks)

    # First chunk should rank higher
    assert results[0][0].content == "Python is a programming language"
    assert results[0][1] > results[1][1]

@pytest.mark.asyncio
async def test_skip_reranking_simple_query():
    """Test reranking is skipped for simple queries"""
    reranker = RerankerModel()

    chunks = [DocumentChunk(...)]

    # Simple query (<5 words)
    results = await reranker.rank_pairs("hello", chunks)

    # Should return original vector scores
    assert results[0][1] == chunks[0].relevance_score

@pytest.mark.asyncio
async def test_reranker_cache_hit_miss():
    """Test cache hit/miss behavior"""
    from unittest.mock import MagicMock

    redis_mock = MagicMock()
    redis_mock.get.return_value = None  # Cache miss

    cache = RerankerCache(redis_mock)

    # First call - cache miss
    result = await cache.get("test query", ["id1", "id2"])
    assert result is None

    # Set cache
    await cache.set("test query", ["id1", "id2"], [("id1", 0.9), ("id2", 0.7)])

    # Mock cache hit
    redis_mock.get.return_value = '[["id1", 0.9], ["id2", 0.7]]'
    result = await cache.get("test query", ["id1", "id2"])
    assert result == [["id1", 0.9], ["id2", 0.7]]

@pytest.mark.asyncio
async def test_two_stage_retrieval():
    """Test full two-stage retrieval flow"""
    # Setup indexer with test data
    indexer = CGRAGIndexer()
    # ... index test documents ...

    retriever = CGRAGRetriever(
        indexer,
        use_reranking=True,
        rerank_threshold=0.35,
        stage1_candidates=10
    )

    result = await retriever.retrieve(
        query="python programming",
        token_budget=1000
    )

    assert result.reranking_used is True
    assert result.stage1_candidates == 10
    assert result.stage2_candidates <= 10
    assert result.retrieval_time_ms < 100  # Latency target
    assert len(result.artifacts) > 0
    assert all(score >= 0.35 for score in result.top_scores)  # Threshold

@pytest.mark.asyncio
async def test_reranking_disabled():
    """Test vector-only retrieval when reranking disabled"""
    indexer = CGRAGIndexer()
    # ... index test documents ...

    retriever = CGRAGRetriever(
        indexer,
        use_reranking=False  # Disable reranking
    )

    result = await retriever.retrieve("test query", token_budget=1000)

    assert result.reranking_used is False
    assert result.stage1_candidates == 0
    assert result.stage2_candidates == 0
```

### 5.2 Integration Tests

**File:** `backend/tests/test_cgrag_integration.py` (ADD)

```python
@pytest.mark.asyncio
async def test_reranking_improves_accuracy():
    """Verify reranking improves top-1 relevance"""
    indexer = CGRAGIndexer()
    await indexer.index_directory(Path("docs"), chunk_size=512)

    # Without reranking
    retriever_no_rerank = CGRAGRetriever(indexer, use_reranking=False)
    result_no_rerank = await retriever_no_rerank.retrieve("async patterns in Python")

    # With reranking
    retriever_rerank = CGRAGRetriever(indexer, use_reranking=True)
    result_rerank = await retriever_rerank.retrieve("async patterns in Python")

    # Reranking should produce higher top-1 relevance
    assert result_rerank.top_scores[0] >= result_no_rerank.top_scores[0]

@pytest.mark.asyncio
async def test_latency_meets_target():
    """Verify retrieval latency is <100ms"""
    indexer = CGRAGIndexer()
    await indexer.index_directory(Path("docs"))

    retriever = CGRAGRetriever(indexer, use_reranking=True)

    # Run 10 queries and measure latency
    latencies = []
    for query in ["python", "fastapi", "docker", "async", "testing"] * 2:
        result = await retriever.retrieve(query, token_budget=5000)
        latencies.append(result.retrieval_time_ms)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 100, f"Average latency {avg_latency:.1f}ms exceeds 100ms target"

@pytest.mark.asyncio
async def test_cache_hit_rate():
    """Verify cache hit rate >70% for repeated queries"""
    # ... implementation ...
    pass
```

### 5.3 Performance Benchmarks

**File:** `backend/scripts/benchmark_reranking.py` (NEW)

```python
"""Benchmark script for two-stage reranking performance.

Usage:
    python -m backend.scripts.benchmark_reranking --docs /app/docs
"""

import asyncio
import time
from pathlib import Path
from statistics import mean, stdev

from app.services.cgrag import CGRAGIndexer, CGRAGRetriever

async def benchmark_reranking(docs_dir: Path, num_queries: int = 100):
    """Run reranking benchmark"""

    # Index documents
    print(f"Indexing {docs_dir}...")
    indexer = CGRAGIndexer()
    chunks = await indexer.index_directory(docs_dir)
    print(f"Indexed {chunks} chunks")

    # Test queries
    queries = [
        "async programming patterns",
        "FastAPI endpoint configuration",
        "Docker container setup",
        "pytest testing strategies",
        "Redis caching implementation",
        # ... more test queries ...
    ] * (num_queries // 10)

    # Benchmark: Vector-only
    print("\n=== Benchmark: Vector-Only Retrieval ===")
    retriever_vector = CGRAGRetriever(indexer, use_reranking=False)
    latencies_vector = []

    for query in queries:
        start = time.time()
        result = await retriever_vector.retrieve(query)
        latencies_vector.append((time.time() - start) * 1000)

    print(f"Avg Latency: {mean(latencies_vector):.1f}ms")
    print(f"Std Dev: {stdev(latencies_vector):.1f}ms")
    print(f"Min: {min(latencies_vector):.1f}ms")
    print(f"Max: {max(latencies_vector):.1f}ms")

    # Benchmark: Two-Stage Reranking
    print("\n=== Benchmark: Two-Stage Reranking ===")
    retriever_rerank = CGRAGRetriever(indexer, use_reranking=True)
    latencies_rerank = []
    cache_hits = 0

    for query in queries:
        start = time.time()
        result = await retriever_rerank.retrieve(query)
        latencies_rerank.append((time.time() - start) * 1000)
        if result.cache_hit:
            cache_hits += 1

    print(f"Avg Latency: {mean(latencies_rerank):.1f}ms")
    print(f"Std Dev: {stdev(latencies_rerank):.1f}ms")
    print(f"Min: {min(latencies_rerank):.1f}ms")
    print(f"Max: {max(latencies_rerank):.1f}ms")
    print(f"Cache Hit Rate: {cache_hits/len(queries)*100:.1f}%")

    # Comparison
    print("\n=== Comparison ===")
    latency_increase = mean(latencies_rerank) - mean(latencies_vector)
    print(f"Latency Increase: +{latency_increase:.1f}ms ({latency_increase/mean(latencies_vector)*100:.1f}%)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=str, default="/app/docs")
    parser.add_argument("--num-queries", type=int, default=100)
    args = parser.parse_args()

    asyncio.run(benchmark_reranking(Path(args.docs), args.num_queries))
```

---

## Part 6: Implementation Checklist

### Phase 1: Core Implementation (Week 1)

- [ ] Add `sentence-transformers` cross-encoder support to `requirements.txt`
- [ ] Implement `RerankerModel` class in `cgrag.py`
- [ ] Implement `RerankerCache` class in `cgrag.py`
- [ ] Enhance `CGRAGRetriever` class with two-stage logic
- [ ] Update `CGRAGResult` model with reranking metadata
- [ ] Add runtime settings for reranking configuration
- [ ] Update development profile with reranking settings

### Phase 2: Testing (Week 1-2)

- [ ] Write unit tests for `RerankerModel`
- [ ] Write unit tests for `RerankerCache`
- [ ] Write integration tests for two-stage retrieval
- [ ] Create performance benchmark script
- [ ] Run benchmarks and validate <100ms latency
- [ ] Verify cache hit rate >70%

### Phase 3: API Integration (Week 2)

- [ ] Update CGRAG router to expose reranking settings
- [ ] Add `/api/cgrag/settings` endpoint for runtime config
- [ ] Update `/api/cgrag/status` to include reranking status
- [ ] Add reranking metadata to query responses

### Phase 4: Documentation & Deployment (Week 2)

- [ ] Update `CGRAG_ENHANCEMENT_PLAN.md` with reranking implementation
- [ ] Add inline documentation to all new code
- [ ] Update `SESSION_NOTES.md` with implementation details
- [ ] Test in Docker environment
- [ ] Deploy to production

---

## Part 7: Expected Results

### 7.1 Retrieval Quality Metrics

**Before Two-Stage Reranking:**
```
Top-1 Relevance: ~0.70
Top-5 Avg Relevance: ~0.65
Precision@5: ~60%
Recall@10: ~55%
```

**After Two-Stage Reranking:**
```
Top-1 Relevance: ~0.85 (+21%)
Top-5 Avg Relevance: ~0.80 (+23%)
Precision@5: ~75% (+25%)
Recall@10: ~70% (+27%)
```

### 7.2 Performance Metrics

**Latency:**
```
Vector-only: ~30ms
Two-stage (cache miss): ~70ms (+133%)
Two-stage (cache hit): ~5ms (-83%)
Average (70% hit rate): ~26ms (-13%)
```

**Throughput:**
```
Vector-only: ~33 queries/sec
Two-stage: ~14 queries/sec (cache miss)
Two-stage: ~200 queries/sec (cache hit)
Average: ~60 queries/sec (+82%)
```

### 7.3 User Experience Impact

| Scenario | Before | After | Impact |
|----------|--------|-------|--------|
| Simple query ("python") | 30ms, good result | 30ms, good result | No change (skip reranking) |
| Complex query ("async patterns in FastAPI") | 30ms, mediocre result | 70ms, excellent result | Better accuracy, acceptable latency |
| Repeated query | 30ms | 5ms | Faster + better |

---

## Part 8: Migration Path

### 8.1 Backward Compatibility

**Existing code continues to work:**
```python
# Old usage (still works - defaults to reranking enabled)
retriever = CGRAGRetriever(indexer)
result = await retriever.retrieve(query)

# New usage (explicit control)
retriever = CGRAGRetriever(indexer, use_reranking=True)
result = await retriever.retrieve(query, use_reranking=False)  # Override
```

### 8.2 Gradual Rollout

1. **Week 1:** Deploy with reranking disabled by default
2. **Week 1-2:** A/B test with 10% traffic
3. **Week 2:** Increase to 50% traffic, monitor metrics
4. **Week 2+:** Full rollout if metrics meet targets

### 8.3 Rollback Plan

If issues occur:
```yaml
# config/profiles/production.yaml
cgrag:
  use_reranking: false  # Instant rollback to vector-only
```

No code changes needed - purely configuration-driven.

---

## Part 9: Future Enhancements

### 9.1 Advanced Reranking Models

**Current:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (80MB, general purpose)

**Potential Upgrades:**
- `cross-encoder/ms-marco-MiniLM-L-12-v2` (420MB, +5% accuracy, 2x slower)
- Domain-specific rerankers for code/docs
- Fine-tuned reranker on S.Y.N.A.P.S.E. ENGINE queries

### 9.2 Query-Adaptive Thresholds

```python
def adaptive_threshold(query: str) -> float:
    """Adjust threshold based on query characteristics"""
    if is_factual_query(query):
        return 0.5  # Higher threshold for factual queries
    elif is_exploratory_query(query):
        return 0.3  # Lower threshold for exploratory queries
    else:
        return 0.35  # Default
```

### 9.3 Multi-Stage Reranking

**Stage 3:** LLM-based relevance verification for critical queries

```python
# Only for high-stakes queries
if query_importance > 0.9:
    # Stage 3: LLM judges relevance
    final_ranking = await llm_rerank(query, stage2_results)
```

---

## Part 10: References

### Research Papers & Articles

1. **QAnything Pattern**
   - Source: [QAnything源码解析](https://blog.csdn.net/u013261578/article/details/145353349)
   - Key: Two-stage retrieval with threshold > 0.35

2. **Korean Reranker Research**
   - Source: [AWS Korean Reranker](https://aws.amazon.com/ko/blogs/tech/korean-reranker-rag/)
   - Key: Document order matters more than presence

3. **MS MARCO Cross-Encoders**
   - Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
   - Paper: [MS MARCO Passage Ranking](https://arxiv.org/abs/1611.09268)

### Performance Standards

Based on Chinese RAG research (GLOBAL_RAG_RESEARCH.md:99-108):
- Retrieval Latency: <100ms
- Cache Hit Rate: >70%
- Relevance Score: >0.8
- Rerank Threshold: >0.35
- Indexing Throughput: >1000 chunks/sec

---

## Appendix A: Dependency Changes

### requirements.txt

```diff
# CGRAG and ML dependencies
faiss-cpu==1.12.0
sentence-transformers==5.1.2
numpy==2.3.4
tiktoken==0.12.0
+ # Note: sentence-transformers 5.1.2 already includes cross-encoder support
+ # No additional dependencies needed for two-stage reranking!
```

**Good news:** `sentence-transformers>=3.0` includes `CrossEncoder` class, so no additional dependencies are needed!

---

## Appendix B: Configuration Examples

### Development Profile (Fast Iteration)

```yaml
cgrag:
  use_reranking: true
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Lightweight
  rerank_threshold: 0.30  # Lower threshold for more results
  stage1_candidates: 50  # Fewer candidates for faster testing
  min_query_length_for_reranking: 3  # Rerank even shorter queries
```

### Production Profile (Quality + Performance)

```yaml
cgrag:
  use_reranking: true
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  rerank_threshold: 0.35  # Standard threshold
  stage1_candidates: 100  # Full QAnything pattern
  reranker_cache_ttl: 3600
  min_query_length_for_reranking: 5
```

### High-Accuracy Profile (Research/Analysis)

```yaml
cgrag:
  use_reranking: true
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-12-v2"  # Larger model
  rerank_threshold: 0.40  # Higher threshold for quality
  stage1_candidates: 150  # More candidates
  reranker_cache_ttl: 7200
  min_query_length_for_reranking: 3
```

---

## Conclusion

This two-stage reranking implementation brings S.Y.N.A.P.S.E. ENGINE's CGRAG system to production quality with:

- **+15-25% accuracy** improvement (QAnything pattern)
- **<100ms latency** maintained (with smart caching)
- **>70% cache hit rate** target
- **Zero breaking changes** (fully backward compatible)
- **Configuration-driven** rollout and rollback

The implementation follows global RAG best practices from Chinese, Korean, and English research, while maintaining S.Y.N.A.P.S.E. ENGINE's performance and code quality standards.

**Next Steps:** Proceed with Phase 1 implementation checklist, starting with `RerankerModel` class.
