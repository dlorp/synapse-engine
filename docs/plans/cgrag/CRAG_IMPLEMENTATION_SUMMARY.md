# CRAG Implementation Summary

**Quick Start Guide for Next Engineer**

**Date:** 2025-11-30
**Status:** Core Implementation Complete, Integration Pending
**Estimated Integration Time:** 4-6 hours

---

## What is CRAG?

**Corrective RAG (CRAG)** is a self-correcting retrieval mechanism that evaluates retrieval quality and applies correction strategies automatically:

- **RELEVANT (>0.75):** Use as-is (fast path <70ms)
- **PARTIAL (0.50-0.75):** Query expansion + re-retrieval (~180ms)
- **IRRELEVANT (<0.50):** Web search fallback (~450ms)

**Expected Impact:**
- Retrieval accuracy: 70% → 85-90% (+15-20%)
- Hallucination rate: 10% → <5% (50% reduction)
- Fast path latency: 100ms → <70ms (30% faster)

---

## Files Implemented

### Core Components (✅ Complete)

| File | Purpose | Status |
|------|---------|--------|
| `backend/app/services/crag_evaluator.py` | Relevance evaluation (4 criteria) | ✅ Ready |
| `backend/app/services/query_expander.py` | Synonym-based query expansion | ✅ Ready |
| `backend/app/services/web_augmenter.py` | Web search fallback | ✅ Ready |
| `backend/app/services/crag.py` | Main orchestrator | ✅ Ready |
| `backend/tests/test_crag.py` | Unit tests (80%+ coverage) | ✅ Ready |

### Integration Files (❌ Pending)

| File | Changes Needed | Priority |
|------|---------------|----------|
| `backend/app/models/query.py` | Add CRAG fields | HIGH |
| `backend/app/routers/query.py` | Integrate orchestrator | HIGH |
| `backend/tests/test_crag_integration.py` | Integration tests | MEDIUM |

---

## Integration Checklist

### Step 1: Add CRAG Fields to Models (30 min)

**File:** `backend/app/models/query.py`

**In `QueryRequest` class (around line 89):**

```python
use_crag: bool = Field(
    default=True,
    alias="useCrag",
    description="Enable Corrective RAG (self-correcting retrieval)"
)
```

**In `QueryMetadata` class (around line 399):**

```python
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
# Optional: Add detailed evaluation metrics
crag_keyword_overlap: Optional[float] = Field(
    default=None,
    alias="cragKeywordOverlap",
    description="Keyword overlap score (0.0-1.0)"
)
crag_semantic_coherence: Optional[float] = Field(
    default=None,
    alias="cragSemanticCoherence",
    description="Semantic coherence score (0.0-1.0)"
)
```

---

### Step 2: Integrate CRAG into Query Router (1-2 hours)

**File:** `backend/app/routers/query.py`

**Import CRAG orchestrator (top of file):**

```python
from app.services.crag import CRAGOrchestrator
```

**Modify context retrieval section (around line 100-150):**

```python
# Context retrieval
cgrag_result = None
if request.use_context:
    try:
        # Load CGRAG indexer
        index_dir, index_path, metadata_path = get_cgrag_index_paths("docs")

        if not index_path.exists():
            logger.warning(f"CGRAG index not found at {index_path}")
        else:
            indexer = CGRAGIndexer.load_index(index_path, metadata_path)

            if request.use_crag:
                # Use CRAG orchestrator (self-correcting retrieval)
                logger.info("[QUERY] Using CRAG orchestrator")
                retriever = CGRAGRetriever(indexer)
                crag_orchestrator = CRAGOrchestrator(
                    cgrag_retriever=retriever,
                    enable_web_search=request.use_web_search,
                    enable_query_expansion=True  # Always enable for PARTIAL category
                )
                cgrag_result = await crag_orchestrator.retrieve(
                    query=request.query,
                    token_budget=8000
                )
                logger.info(
                    f"[CRAG] Decision: {cgrag_result.crag_decision}, "
                    f"Score: {cgrag_result.crag_score:.2f}, "
                    f"Strategy: {cgrag_result.correction_strategy}"
                )
            else:
                # Use standard CGRAG retriever (no correction)
                logger.info("[QUERY] Using standard CGRAG retriever")
                retriever = CGRAGRetriever(indexer)
                cgrag_result = await retriever.retrieve(
                    query=request.query,
                    token_budget=8000
                )
    except Exception as e:
        logger.error(f"CGRAG/CRAG retrieval failed: {type(e).__name__}: {e}")
```

**Update metadata construction (around line 300-350):**

```python
# Build metadata
metadata = QueryMetadata(
    # ... existing fields ...

    # CRAG metadata (conditional - only if CRAG was used)
    crag_decision=getattr(cgrag_result, 'crag_decision', None),
    crag_score=getattr(cgrag_result, 'crag_score', None),
    crag_correction_strategy=getattr(cgrag_result, 'correction_strategy', None),
    crag_web_search_used=getattr(cgrag_result, 'web_search_used', False),

    # Optional: Add detailed metrics
    crag_keyword_overlap=getattr(cgrag_result, 'keyword_overlap', None),
    crag_semantic_coherence=getattr(cgrag_result, 'semantic_coherence', None)
)
```

---

### Step 3: Test Integration (1 hour)

**Run unit tests:**

```bash
# Test CRAG components
pytest backend/tests/test_crag.py -v

# Expected output:
# test_crag.py::TestCRAGEvaluator::test_evaluator_relevant_category PASSED
# test_crag.py::TestCRAGEvaluator::test_evaluator_irrelevant_category PASSED
# test_crag.py::TestQueryExpander::test_basic_expansion PASSED
# test_crag.py::TestWebSearchAugmenter::test_augment_converts_web_results_to_chunks PASSED
# test_crag.py::TestCRAGOrchestrator::test_orchestrator_fast_path_relevant PASSED
# ... (should see 22 tests PASSED)
```

**Test end-to-end in Docker:**

```bash
# Rebuild backend with CRAG code
docker-compose build --no-cache synapse_core
docker-compose up -d

# Test via API
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python async patterns",
    "mode": "simple",
    "useContext": true,
    "useCrag": true
  }'

# Check response for CRAG metadata:
# "cragDecision": "RELEVANT" | "PARTIAL" | "IRRELEVANT"
# "cragScore": 0.85
# "cragCorrectionStrategy": "none" | "query_expansion" | "web_search"
```

**Verify logs:**

```bash
docker-compose logs -f synapse_core | grep CRAG

# Expected log output:
# [QUERY] Using CRAG orchestrator
# [CRAG] Initial retrieval: query='Python async patterns'
# [CRAG] Evaluating 8 artifacts
# [CRAG] Evaluation: RELEVANT (score=0.87)
# [CRAG] Fast path: Using original artifacts (high relevance)
# [CRAG] Complete in 68.5ms: 8 artifacts, 1200 tokens, correction=none
```

---

### Step 4: Frontend Integration (Optional, 2 hours)

**Display CRAG metadata in response UI:**

**File:** `frontend/src/components/query/ResponseDisplay.tsx`

Add CRAG decision badge:

```typescript
{metadata.cragDecision && (
  <div className={styles.cragBadge}>
    <span className={styles.cragLabel}>CRAG:</span>
    <span className={`${styles.cragCategory} ${styles[metadata.cragDecision.toLowerCase()]}`}>
      {metadata.cragDecision}
    </span>
    <span className={styles.cragScore}>
      ({(metadata.cragScore * 100).toFixed(0)}%)
    </span>
    {metadata.cragCorrectionStrategy !== 'none' && (
      <span className={styles.cragCorrection}>
        ↻ {metadata.cragCorrectionStrategy.replace('_', ' ')}
      </span>
    )}
  </div>
)}
```

**Add CSS styling:**

```css
.cragBadge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border: 1px solid #ff9500;
  border-radius: 4px;
  font-size: 12px;
}

.cragCategory.relevant {
  color: #00ff00;
}

.cragCategory.partial {
  color: #ffaa00;
}

.cragCategory.irrelevant {
  color: #ff0000;
}

.cragCorrection {
  color: #00ffff;
  font-style: italic;
}
```

---

## Testing Scenarios

### Scenario 1: Fast Path (RELEVANT)

**Query:** "Python async patterns concurrent execution"

**Expected:**
- `cragDecision: "RELEVANT"`
- `cragScore: >0.75`
- `cragCorrectionStrategy: "none"`
- Fast response (<70ms for retrieval)

### Scenario 2: Query Expansion (PARTIAL)

**Query:** "optimize performance"

**Expected:**
- `cragDecision: "PARTIAL"`
- `cragScore: 0.50-0.75`
- `cragCorrectionStrategy: "query_expansion"`
- Slower response (~180ms for retrieval + expansion)
- More artifacts returned (merged results)

### Scenario 3: Web Search Fallback (IRRELEVANT)

**Query:** "latest SpaceX launch updates"

**Expected:**
- `cragDecision: "IRRELEVANT"`
- `cragScore: <0.50`
- `cragCorrectionStrategy: "web_search"`
- `cragWebSearchUsed: true`
- Artifacts with `language: 'web'`
- Response time ~450ms (web search overhead)

---

## Monitoring & Metrics

**Log analysis:**

```bash
# Count CRAG decisions
docker-compose logs synapse_core | grep "CRAG_METRICS" | \
  awk '{print $NF}' | sort | uniq -c

# Expected distribution:
# 700 decision=RELEVANT
# 250 decision=PARTIAL
# 50 decision=IRRELEVANT
```

**Prometheus metrics (future):**

```python
# Add to backend/app/services/crag.py
from prometheus_client import Counter, Histogram

crag_decisions = Counter('crag_decisions_total', 'CRAG decisions', ['category'])
crag_latency = Histogram('crag_latency_seconds', 'CRAG latency', ['decision'])
```

---

## Troubleshooting

### Issue: Import errors

**Problem:** `ModuleNotFoundError: No module named 'app.services.crag'`

**Solution:**
1. Verify files are in correct location: `backend/app/services/`
2. Rebuild Docker: `docker-compose build --no-cache synapse_core`
3. Restart containers: `docker-compose up -d`

### Issue: Unit tests fail

**Problem:** Tests fail with mocking errors

**Solution:**
1. Install test dependencies: `pip install pytest pytest-asyncio`
2. Run from project root: `pytest backend/tests/test_crag.py -v`
3. Check mock setup in test fixtures

### Issue: Web search always fails

**Problem:** `web_search_used: false` even for IRRELEVANT queries

**Solution:**
1. Verify SearXNG is running: `docker-compose ps searxng`
2. Check SearXNG health: `curl http://localhost:8888/healthz`
3. Enable web search in query: `useWebSearch: true`

### Issue: All queries classified as IRRELEVANT

**Problem:** CRAG always triggers web search fallback

**Solution:**
1. Check CGRAG index exists: `ls -la backend/data/faiss_indexes/`
2. Re-index documents if missing: See CGRAG indexing guide
3. Verify evaluation criteria weights in `crag_evaluator.py`

---

## Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| RELEVANT rate | >70% | Count CRAG_METRICS logs |
| Correction rate | <30% | Count correction_applied=true |
| Fast path latency | <70ms | Check retrieval_time_ms for RELEVANT |
| Expansion latency | <180ms | Check retrieval_time_ms for PARTIAL |
| Web search latency | <450ms | Check retrieval_time_ms for IRRELEVANT |

---

## Next Steps After Integration

1. **Week 1:** Deploy with `useCrag: false` by default (opt-in testing)
2. **Week 2:** Monitor metrics, validate accuracy improvements
3. **Week 3:** Enable `useCrag: true` by default (opt-out)
4. **Week 4:** Remove toggle, make CRAG mandatory
5. **Future:** Add Redis caching, Prometheus metrics, learned query expansion

---

## Documentation References

**Complete Design:** [docs/plans/CORRECTIVE_RAG_DESIGN.md](./docs/plans/CORRECTIVE_RAG_DESIGN.md)
**Session Notes:** [SESSION_NOTES.md](./SESSION_NOTES.md#2025-11-30-0130---corrective-rag-crag-design--implementation)
**Research Findings:** [docs/research/GLOBAL_RAG_RESEARCH.md](./docs/research/GLOBAL_RAG_RESEARCH.md)

---

## Questions?

If you encounter issues or need clarification:

1. Check [CORRECTIVE_RAG_DESIGN.md](./docs/plans/CORRECTIVE_RAG_DESIGN.md) for detailed specifications
2. Review unit tests in `backend/tests/test_crag.py` for usage examples
3. Consult [SESSION_NOTES.md](./SESSION_NOTES.md) for implementation context
4. Check code comments in implemented files for inline documentation

**Key Design Principles:**
- Fast path optimization (avoid unnecessary corrections)
- Graceful degradation (never fail, always return something)
- Transparent decision-making (log all decisions for debugging)
- Privacy-preserving (local synonym expansion, optional web search)
