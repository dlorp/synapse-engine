# CGRAG Two-Stage Reranking - Quick Start Guide

**Full Plan:** [CGRAG_TWO_STAGE_RERANKING.md](./CGRAG_TWO_STAGE_RERANKING.md)

---

## TL;DR

Implement QAnything-style two-stage reranking to boost CGRAG accuracy by 15-25% while maintaining <100ms latency.

**Stage 1:** FAISS vector search → top 100 candidates (fast, coarse)
**Stage 2:** Cross-encoder reranking → threshold > 0.35 (slow, precise)

---

## Implementation Steps (1-2 weeks)

### Step 1: Add Dependencies (Already Done!)

`sentence-transformers==5.1.2` already includes `CrossEncoder` - no new dependencies needed!

### Step 2: Add Three New Classes to `backend/app/services/cgrag.py`

```python
# Class 1: RerankerModel (lines ~110-180)
class RerankerModel:
    """Cross-encoder for fine-grained relevance scoring"""
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    async def rank_pairs(query, candidates) -> List[Tuple[chunk, score]]
    def _should_skip_reranking(query) -> bool  # Skip if <5 words

# Class 2: RerankerCache (lines ~185-260)
class RerankerCache:
    """Redis cache for reranking results"""

    async def get(query, candidate_ids) -> Optional[results]
    async def set(query, candidate_ids, results)

# Class 3: Enhanced CGRAGRetriever (modify existing, lines 475-636)
class CGRAGRetriever:
    """Two-stage retrieval: FAISS + Cross-encoder"""

    async def retrieve(query, token_budget) -> CGRAGResult
        # STAGE 1: FAISS search (100 candidates)
        # STAGE 2: Cross-encoder reranking (threshold > 0.35)
        # TOKEN PACKING: Greedy algorithm
```

### Step 3: Update Runtime Settings

**File:** `config/profiles/development.yaml`

```yaml
cgrag:
  # NEW: Two-stage reranking
  use_reranking: true
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  rerank_threshold: 0.35
  stage1_candidates: 100
  reranker_cache_ttl: 3600
  min_query_length_for_reranking: 5
```

### Step 4: Test

```bash
# Unit tests
pytest backend/tests/test_cgrag_reranking.py

# Benchmark
python -m backend.scripts.benchmark_reranking --docs /app/docs

# Expected results:
# - Latency: ~70ms (cache miss), ~5ms (cache hit)
# - Top-1 Relevance: >0.8 (vs ~0.7 before)
# - Cache Hit Rate: >70%
```

---

## Code Examples

### Basic Usage (Backward Compatible)

```python
# Existing code works unchanged - reranking enabled by default
indexer = CGRAGIndexer()
await indexer.index_directory(Path("docs"))

retriever = CGRAGRetriever(indexer)  # Reranking enabled
result = await retriever.retrieve("async patterns in FastAPI")

print(f"Artifacts: {len(result.artifacts)}")
print(f"Top-1 Relevance: {result.top_scores[0]:.2f}")
print(f"Latency: {result.retrieval_time_ms:.1f}ms")
print(f"Reranking Used: {result.reranking_used}")
```

### Advanced Usage (Explicit Control)

```python
# Disable reranking for this retriever
retriever = CGRAGRetriever(
    indexer,
    use_reranking=False  # Vector-only mode
)

# Or override per query
result = await retriever.retrieve(
    query="simple query",
    use_reranking=False  # Skip reranking for this query
)
```

### Configuration-Driven Rollback

```yaml
# Instant rollback to vector-only (no code changes)
cgrag:
  use_reranking: false  # Done!
```

---

## Performance Targets

| Metric | Current | Target | Expected |
|--------|---------|--------|----------|
| Top-1 Relevance | ~0.70 | >0.80 | 0.85 |
| Latency (cache miss) | ~30ms | <100ms | ~70ms |
| Latency (cache hit) | ~30ms | <10ms | ~5ms |
| Cache Hit Rate | N/A | >70% | 75% |
| Accuracy Improvement | Baseline | +15-25% | +21% |

---

## Key Files

### Implementation
- `backend/app/services/cgrag.py` - Core implementation (3 classes)
- `backend/app/models/settings.py` - Runtime settings schema
- `config/profiles/development.yaml` - Configuration

### Testing
- `backend/tests/test_cgrag_reranking.py` - Unit tests
- `backend/tests/test_cgrag_integration.py` - Integration tests
- `backend/scripts/benchmark_reranking.py` - Benchmark script

### Documentation
- [CGRAG_TWO_STAGE_RERANKING.md](./CGRAG_TWO_STAGE_RERANKING.md) - Full plan (10 parts)
- [GLOBAL_RAG_RESEARCH.md](../research/GLOBAL_RAG_RESEARCH.md) - Research findings

---

## Troubleshooting

### Issue: High Latency (>100ms)

**Solution 1:** Check cache hit rate
```python
# Add logging
logger.info(f"Cache hit rate: {cache_hits/total_queries*100:.1f}%")
```

**Solution 2:** Reduce Stage 1 candidates
```yaml
cgrag:
  stage1_candidates: 50  # Instead of 100
```

**Solution 3:** Skip reranking for simple queries
```yaml
cgrag:
  min_query_length_for_reranking: 7  # Instead of 5
```

### Issue: Low Accuracy

**Solution 1:** Lower rerank threshold
```yaml
cgrag:
  rerank_threshold: 0.30  # Instead of 0.35
```

**Solution 2:** Increase Stage 1 candidates
```yaml
cgrag:
  stage1_candidates: 150  # Instead of 100
```

**Solution 3:** Upgrade reranker model
```yaml
cgrag:
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-12-v2"  # Larger, slower, more accurate
```

### Issue: Memory Usage

**Solution 1:** Reduce batch size (in code)
```python
scores = self.model.predict(pairs, batch_size=16)  # Instead of 32
```

**Solution 2:** Reduce cache TTL
```yaml
cgrag:
  reranker_cache_ttl: 1800  # 30min instead of 1 hour
```

---

## Next Steps

1. Read full plan: [CGRAG_TWO_STAGE_RERANKING.md](./CGRAG_TWO_STAGE_RERANKING.md)
2. Implement Phase 1: Core implementation (Week 1)
3. Implement Phase 2: Testing (Week 1-2)
4. Implement Phase 3: API integration (Week 2)
5. Deploy with gradual rollout (10% → 50% → 100%)

---

## References

- **QAnything Pattern:** [NetEase Research](https://blog.csdn.net/u013261578/article/details/145353349)
- **Korean Reranker:** [AWS Blog](https://aws.amazon.com/ko/blogs/tech/korean-reranker-rag/)
- **Global RAG Research:** [Full Report](../research/GLOBAL_RAG_RESEARCH.md)
- **MS MARCO Model:** [Hugging Face](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2)
