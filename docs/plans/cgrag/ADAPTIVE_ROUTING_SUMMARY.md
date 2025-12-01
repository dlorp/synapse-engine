# Adaptive Query Routing - Quick Start Guide

**Status:** Ready for Implementation
**Design Document:** [ADAPTIVE_QUERY_ROUTING_DESIGN.md](./ADAPTIVE_QUERY_ROUTING_DESIGN.md)
**Estimated Time:** 8-12 hours

---

## What This Does

Intelligently **skips CGRAG retrieval** for simple queries (greetings, arithmetic) to reduce latency by 30-40%. Based on Russian Adaptive RAG research.

**Example:**
- **Before:** "Hello" → 2000ms (500ms retrieval + 1500ms generation)
- **After:** "Hello" → 1200ms (0ms retrieval + 1200ms generation)
- **Savings:** 800ms (40% faster)

---

## Quick Implementation Checklist

### Phase 1: Core Classification (4 hours)

- [ ] **Create** `backend/app/services/query_classifier.py`
  - Implement `QueryClassifier` class with pattern matching
  - 4 retrieval strategies: NO_RETRIEVAL, SINGLE_RETRIEVAL, MULTI_STEP, KNOWLEDGE_GRAPH

- [ ] **Modify** `backend/app/models/query.py`
  - Add `RetrievalStrategy` enum
  - Enhance `QueryComplexity` with `retrieval_strategy` and `retrieval_reasoning` fields
  - Enhance `QueryMetadata` with `retrieval_skipped` and `retrieval_passes` fields

- [ ] **Write Tests** `backend/tests/test_query_classifier.py`
  - Test NO_RETRIEVAL: greetings, arithmetic, acknowledgments
  - Test SINGLE_RETRIEVAL: factual questions
  - Test MULTI_STEP: analysis, multi-part queries

### Phase 2: Integration (3 hours)

- [ ] **Modify** `backend/app/services/routing.py`
  - Add `initialize_query_classifier()` function
  - Modify `assess_complexity()` to call classifier
  - Return retrieval strategy in `QueryComplexity`

- [ ] **Modify** `backend/app/routers/query.py`
  - Check `complexity.retrieval_strategy` before CGRAG retrieval
  - Skip retrieval if `NO_RETRIEVAL`
  - Add `_perform_single_retrieval()` helper function
  - Update metadata with retrieval strategy info

- [ ] **Modify** `backend/app/main.py`
  - Call `initialize_query_classifier()` in lifespan startup

### Phase 3: Testing & Validation (2 hours)

- [ ] **Run Unit Tests**
  ```bash
  pytest backend/tests/test_query_classifier.py -v
  ```

- [ ] **Run Integration Tests**
  ```bash
  pytest backend/tests/test_adaptive_routing_integration.py -v
  ```

- [ ] **Manual Testing** (Docker)
  ```bash
  docker-compose build --no-cache synapse_core
  docker-compose up -d
  docker-compose logs -f synapse_core
  ```

- [ ] **Test Queries:**
  - "Hello" → Should be NO_RETRIEVAL (<1.5s)
  - "What is 2+2?" → Should be NO_RETRIEVAL (<1.5s)
  - "What is Python?" → Should be SINGLE_RETRIEVAL (<5s)
  - "Analyze microservices" → Should be MULTI_STEP (or SINGLE if disabled)

### Phase 4: Monitoring (1 hour)

- [ ] **Verify Metrics**
  - Check `/api/health` endpoint
  - Review logs for classification decisions
  - Monitor latency improvements

- [ ] **Dashboard Updates** (Optional)
  - Add "Retrieval Strategy Distribution" panel
  - Add "Latency Savings" chart

---

## Key Design Decisions

### 1. Pattern-Based Classification (Fast)

Uses **simple pattern matching** (<1ms overhead) instead of ML models:

```python
NO_RETRIEVAL_PATTERNS = [
    "hello", "hi", "thank you", "goodbye",  # Greetings
    "what is", "calculate", "compute"       # Arithmetic
]
```

### 2. Four Retrieval Strategies

| Strategy | When to Use | Expected Latency |
|----------|-------------|------------------|
| **NO_RETRIEVAL** | Greetings, arithmetic, simple facts | <1.5s |
| **SINGLE_RETRIEVAL** | Factual questions, explanations | <5s |
| **MULTI_STEP** | Analysis, synthesis (Phase 2) | <15s |
| **KNOWLEDGE_GRAPH** | Entity relationships (Phase 3) | <20s |

### 3. Backward Compatible

- Existing queries continue to work
- `use_context=True` still respected (but may be skipped intelligently)
- Metadata includes both old and new fields
- No breaking changes to API

### 4. Feature Flags

```python
# Enable/disable advanced strategies
initialize_query_classifier(
    enable_multi_step=False,        # Phase 2 feature
    enable_knowledge_graph=False    # Phase 3 feature
)
```

---

## Expected Performance Gains

### Latency Improvements

| Query Type | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Greetings | 2000ms | 1200ms | **-40%** |
| Arithmetic | 2000ms | 1300ms | **-35%** |
| Factual | 5000ms | 5000ms | 0% (still retrieves) |
| Complex | 15000ms | 15000ms | 0% (still retrieves) |

### Cost Savings

**Assumptions:**
- 1000 queries/day
- 30% are simple (NO_RETRIEVAL)
- 150ms retrieval overhead per query

**Current:** 1000 × 150ms = 150s/day
**Optimized:** 700 × 150ms = 105s/day
**Savings:** **30% reduction** in retrieval compute

---

## Code Structure

### New Files

```
backend/app/services/query_classifier.py     (~400 lines)
backend/tests/test_query_classifier.py       (~200 lines)
backend/tests/test_adaptive_routing_integration.py  (~100 lines)
```

### Modified Files

```
backend/app/models/query.py                  (+50 lines)
backend/app/services/routing.py              (+80 lines)
backend/app/routers/query.py                 (+120 lines)
backend/app/main.py                          (+10 lines)
```

---

## Testing Strategy

### Unit Tests (200 lines)

```python
# Test NO_RETRIEVAL classification
def test_greeting_classification(classifier):
    strategy, reasoning = classifier.classify_query("Hello")
    assert strategy == RetrievalStrategy.NO_RETRIEVAL

# Test SINGLE_RETRIEVAL classification
def test_factual_question(classifier):
    strategy, reasoning = classifier.classify_query("What is Python?")
    assert strategy == RetrievalStrategy.SINGLE_RETRIEVAL
```

### Integration Tests (100 lines)

```python
@pytest.mark.asyncio
async def test_no_retrieval_latency():
    response = await client.post("/api/query", json={"query": "Hello"})
    assert response.json()["metadata"]["retrievalSkipped"] is True
    assert response.json()["metadata"]["processingTimeMs"] < 2000
```

### Manual Tests

| Test | Query | Expected Strategy | Expected Latency |
|------|-------|-------------------|------------------|
| TC-1 | "Hello" | NO_RETRIEVAL | <1.5s |
| TC-2 | "What is 5*5?" | NO_RETRIEVAL | <1.5s |
| TC-3 | "What is Python?" | SINGLE_RETRIEVAL | <5s |
| TC-4 | "Analyze microservices" | MULTI_STEP (if enabled) | <15s |

---

## Troubleshooting

### Issue: Classifier Not Initialized

**Symptoms:**
```
RuntimeError: Query classifier not initialized
```

**Fix:**
- Ensure `initialize_query_classifier()` called in `main.py` lifespan
- Check startup logs for "Query classifier initialized"

### Issue: No Latency Improvement

**Symptoms:**
- NO_RETRIEVAL queries still slow (>2s)

**Fix:**
- Verify `retrievalSkipped=true` in response metadata
- Check logs: should see "CGRAG retrieval skipped"
- Profile with `docker-compose logs -f synapse_core`

### Issue: Too Many Queries Skip Retrieval

**Symptoms:**
- Response quality degraded
- >50% queries are NO_RETRIEVAL

**Fix:**
- Review NO_RETRIEVAL patterns (may be too broad)
- Add stricter criteria in `_matches_no_retrieval()`
- Monitor user feedback

---

## API Response Changes

### Before

```json
{
  "metadata": {
    "modelTier": "fast",
    "processingTimeMs": 2000,
    "cgragArtifacts": 0
  }
}
```

### After

```json
{
  "metadata": {
    "modelTier": "fast",
    "processingTimeMs": 1200,  // REDUCED
    "cgragArtifacts": 0,
    "retrievalStrategy": "no_retrieval",  // NEW
    "retrievalSkipped": true,             // NEW
    "retrievalPasses": 0,                 // NEW
    "complexity": {
      "retrievalStrategy": "no_retrieval",
      "retrievalReasoning": "Greeting detected - no retrieval needed"
    }
  }
}
```

---

## Next Steps After Implementation

### Phase 2: Multi-Step Retrieval (2 weeks)

- Iterative retrieval with query refinement
- Initial retrieval → LLM reasoning → Follow-up retrieval → Final response
- Use for complex multi-faceted questions

### Phase 3: Knowledge Graph RAG (4 weeks)

- Entity extraction from query (spaCy NER)
- Knowledge graph construction from CGRAG corpus
- Graph traversal + vector retrieval hybrid
- Reduce hallucinations with structured relationships

### Phase 4: ML-Based Classification (3 weeks)

- Train classification model on query logs
- Replace pattern matching with ML predictions
- Adaptive to domain-specific patterns

---

## References

- **Full Design:** [ADAPTIVE_QUERY_ROUTING_DESIGN.md](./ADAPTIVE_QUERY_ROUTING_DESIGN.md)
- **CGRAG Enhancement Plan:** [docs/plans/CGRAG_ENHANCEMENT_PLAN.md](./docs/plans/CGRAG_ENHANCEMENT_PLAN.md)
- **Global RAG Research:** [docs/research/GLOBAL_RAG_RESEARCH.md](./docs/research/GLOBAL_RAG_RESEARCH.md)

---

## Success Criteria

- [ ] 30-40% latency reduction for simple queries
- [ ] 30% reduction in vector searches
- [ ] >95% classification accuracy (manual validation)
- [ ] All tests passing
- [ ] No response quality degradation
- [ ] Clear observability in logs and metrics

---

**Ready to implement!** Start with Phase 1 (Core Classification) and test incrementally.
