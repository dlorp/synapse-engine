# Adaptive Query Routing Flow Diagram

**System:** S.Y.N.A.P.S.E. ENGINE
**Component:** Adaptive Query Routing Enhancement
**Date:** 2025-11-30

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
│                     "Hello there!"                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Query Router Endpoint                           │
│                  POST /api/query                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Complexity Assessment (routing.py)                  │
│                                                                  │
│  1. Pattern detection (simple/moderate/complex)                 │
│  2. Structural analysis (multi-part, questions, etc.)           │
│  3. Score calculation (token count + heuristics)                │
│  4. Tier selection (fast/balanced/powerful)                     │
│  5. ⭐ NEW: Retrieval strategy classification                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         ⭐ NEW: Query Classifier (query_classifier.py)          │
│                                                                  │
│  Pattern Matching (<1ms):                                       │
│  ├─ NO_RETRIEVAL: Greetings, arithmetic, conversational        │
│  ├─ SINGLE_RETRIEVAL: Factual questions, explanations          │
│  ├─ MULTI_STEP: Analysis, synthesis (future)                   │
│  └─ KNOWLEDGE_GRAPH: Entity relationships (future)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
     NO_RETRIEVAL          SINGLE_RETRIEVAL
     (30% of queries)      (70% of queries)
              │                     │
              │                     │
              │                     ▼
              │            ┌────────────────────┐
              │            │   CGRAG Retrieval  │
              │            │                    │
              │            │ 1. Query embedding │
              │            │ 2. FAISS search    │
              │            │ 3. Token packing   │
              │            │ Time: ~500ms       │
              │            └────────┬───────────┘
              │                     │
              └──────────┬──────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Model Selection                               │
│                                                                  │
│  Tier from complexity assessment:                               │
│  ├─ FAST: 2B-7B models (<2s target)                            │
│  ├─ BALANCED: 8B-14B models (<5s target)                       │
│  └─ POWERFUL: >14B models (<15s target)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LLM Generation                                   │
│                                                                  │
│  Context assembled:                                             │
│  ├─ System prompt                                               │
│  ├─ CGRAG context (if retrieved)                               │
│  └─ User query                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Response + Metadata                             │
│                                                                  │
│  metadata: {                                                    │
│    modelTier: "fast",                                           │
│    processingTimeMs: 1200,  ⭐ REDUCED (was 2000ms)            │
│    retrievalStrategy: "no_retrieval",  ⭐ NEW                  │
│    retrievalSkipped: true,  ⭐ NEW                             │
│    retrievalPasses: 0,  ⭐ NEW                                 │
│    complexity: {                                                │
│      retrievalStrategy: "no_retrieval",  ⭐ NEW                │
│      retrievalReasoning: "Greeting detected"  ⭐ NEW           │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Retrieval Strategy Decision Tree

```
                         Query Analysis
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
         Short query (<5 tokens)?    Contains greeting pattern?
                │                           │
                ▼                           ▼
               YES ─────────────────────► NO_RETRIEVAL
                │                           │
                NO                          │
                │                           │
                ▼                           │
         Arithmetic query?                 │
         (has +, -, *, /, numbers)         │
                │                           │
                ▼                           │
               YES ─────────────────────► NO_RETRIEVAL
                │                           │
                NO                          │
                │                           │
                ▼                           │
         Acknowledgment?                   │
         (thank, bye, goodbye)             │
                │                           │
                ▼                           │
               YES ─────────────────────► NO_RETRIEVAL
                │                           │
                NO                          │
                │                           │
                ▼                           │
         Entity relationship query?        │
         (relationship, connected, etc)    │
                │                           │
                ▼                           │
               YES ─────────────► KNOWLEDGE_GRAPH (future)
                │                           │
                NO                          │
                │                           │
                ▼                           │
         Analysis/synthesis query?         │
         (analyze, evaluate, etc)          │
                │                           │
                ▼                           │
               YES ─────────────► MULTI_STEP (future)
                │                           │
                NO                          │
                │                           │
                ▼                           │
         Factual question?                 │
         (what is, define, explain)        │
                │                           │
                ▼                           │
               YES ─────────────────────► SINGLE_RETRIEVAL
                │                           │
                NO                          │
                │                           │
                ▼                           │
         Multi-part query?                 │
         (contains "and", "then", ";")     │
                │                           │
                ▼                           │
               YES ─────────────► MULTI_STEP (or SINGLE if disabled)
                │                           │
                NO                          │
                │                           │
                └───────────────────────► SINGLE_RETRIEVAL (default)
```

---

## Performance Impact Visualization

### Before Adaptive Routing

```
Query: "Hello"
├─ Complexity Assessment: 10ms
├─ CGRAG Retrieval: 500ms  ⚠️ UNNECESSARY
│  ├─ Query embedding: 100ms
│  ├─ FAISS search: 150ms
│  └─ Token packing: 250ms
├─ Model Selection: 5ms
└─ LLM Generation: 1485ms
────────────────────────────
TOTAL: 2000ms
```

### After Adaptive Routing

```
Query: "Hello"
├─ Complexity Assessment: 10ms
├─ Query Classification: 1ms  ⭐ NEW (<1ms overhead)
├─ CGRAG Retrieval: SKIPPED ⭐ 500ms SAVED
├─ Model Selection: 5ms
└─ LLM Generation: 1184ms
────────────────────────────
TOTAL: 1200ms  ⭐ 40% FASTER
```

### Query Distribution (Expected)

```
Daily Queries: 1000
├─ NO_RETRIEVAL (30%): 300 queries
│  └─ Savings: 300 × 500ms = 150s/day
├─ SINGLE_RETRIEVAL (65%): 650 queries
│  └─ No change (still retrieves)
├─ MULTI_STEP (4%): 40 queries (future)
│  └─ Enhanced retrieval (slower but more accurate)
└─ KNOWLEDGE_GRAPH (1%): 10 queries (future)
   └─ Graph + vector (slower but precise)

TOTAL SAVINGS: 150s/day = 2.5 minutes/day
SCALED (10k queries/day): 25 minutes/day = 12.5 hours/month
```

---

## Architecture Components

### New Components

```
┌────────────────────────────────────────────────────────────┐
│  Query Classifier (query_classifier.py)                    │
│                                                             │
│  - Pattern matching engine                                 │
│  - Retrieval strategy selection                            │
│  - Configuration: enable_multi_step, enable_knowledge_graph│
│  - Fast classification (<1ms)                              │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Enhanced Routing Service (routing.py)                     │
│                                                             │
│  - Complexity assessment (existing)                        │
│  - ⭐ Query classifier integration (new)                   │
│  - Tier selection (existing)                               │
│  - ⭐ Retrieval strategy decision (new)                    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Enhanced Query Router (query.py)                          │
│                                                             │
│  - Query orchestration (existing)                          │
│  - ⭐ Retrieval skip logic (new)                           │
│  - Model invocation (existing)                             │
│  - ⭐ Enhanced metadata (new)                              │
└────────────────────────────────────────────────────────────┘
```

### Enhanced Data Models

```
┌────────────────────────────────────────────────────────────┐
│  RetrievalStrategy Enum (query.py)                         │
│                                                             │
│  - NO_RETRIEVAL                                            │
│  - SINGLE_RETRIEVAL                                        │
│  - MULTI_STEP                                              │
│  - KNOWLEDGE_GRAPH                                         │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Enhanced QueryComplexity Model                            │
│                                                             │
│  - tier: str (existing)                                    │
│  - score: float (existing)                                 │
│  - reasoning: str (existing)                               │
│  - indicators: dict (existing)                             │
│  - ⭐ retrieval_strategy: RetrievalStrategy (new)         │
│  - ⭐ retrieval_reasoning: str (new)                      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Enhanced QueryMetadata Model                              │
│                                                             │
│  - ... (all existing fields)                               │
│  - ⭐ retrieval_strategy: str (new)                       │
│  - ⭐ retrieval_skipped: bool (new)                       │
│  - ⭐ retrieval_passes: int (new)                         │
└────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### With CGRAG Enhancement Plan

```
Adaptive Routing (this design)
      │
      ├─ NO_RETRIEVAL: Skip CGRAG entirely
      │
      ├─ SINGLE_RETRIEVAL: Use enhanced CGRAG
      │  ├─ Hybrid Search (BM25 + Vector) ⭐ from CGRAG plan
      │  ├─ Two-Stage Reranking ⭐ from CGRAG plan
      │  └─ Multi-Context Sources ⭐ from CGRAG plan
      │
      ├─ MULTI_STEP: Iterative CGRAG (future)
      │  └─ Query refinement + follow-up retrieval
      │
      └─ KNOWLEDGE_GRAPH: Graph + CGRAG (future)
         └─ Entity extraction + graph traversal + vector search
```

### With Existing Query Modes

```
Query Modes (existing):
├─ simple: Direct to single model
├─ two-stage: Fast model → Synthesis model
├─ council: Multi-model deliberation
└─ benchmark: Compare all models

Adaptive Routing applies to ALL modes:
├─ Determines IF retrieval happens
├─ Affects latency across all modes
└─ Transparent in metadata
```

---

## Monitoring & Observability

### New Metrics

```
┌────────────────────────────────────────────────────────────┐
│  Retrieval Strategy Distribution (Pie Chart)               │
│                                                             │
│  NO_RETRIEVAL:      30% (300/day)                          │
│  SINGLE_RETRIEVAL:  65% (650/day)                          │
│  MULTI_STEP:         4% (40/day)                           │
│  KNOWLEDGE_GRAPH:    1% (10/day)                           │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Latency Savings (Line Chart)                              │
│                                                             │
│  Avg latency with adaptive routing                         │
│  Avg latency without (estimated)                           │
│  Savings delta                                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Classification Accuracy (Manual Validation)               │
│                                                             │
│  Sample 100 queries/week                                   │
│  Manual validation: Was strategy correct?                  │
│  Target: >95% accuracy                                     │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Cost Reduction (Cumulative)                               │
│                                                             │
│  Vector searches saved                                     │
│  CPU time saved                                            │
│  Estimated cost savings                                    │
└────────────────────────────────────────────────────────────┘
```

### Log Examples

```
[prx:routing] Complexity assessment: tier=fast, score=1.5, retrieval_strategy=no_retrieval
[prx:classifier] Query classified: strategy=no_retrieval, reason="Greeting detected"
[prx:query] CGRAG retrieval skipped (strategy=no_retrieval)
[prx:query] Generating response (model=qwen_8b_fast, no_context=true)
[prx:query] Response generated in 1200ms (retrieval saved 500ms)
```

---

## Future Enhancements Roadmap

### Phase 2: Multi-Step Retrieval

```
Query → Initial Retrieval → LLM Reasoning → Follow-Up Retrieval → Final Response
         (top 5 docs)        (identify gaps)   (refined query)     (synthesis)
```

### Phase 3: Knowledge Graph RAG

```
Query → Entity Extraction → Graph Traversal → Vector Retrieval → Combined Results
        (spaCy NER)          (NetworkX)        (FAISS)            (ranked merge)
```

### Phase 4: ML-Based Classification

```
Query → Feature Extraction → ML Classifier → Strategy Selection
        (embeddings, patterns) (trained model)  (confidence score)
                                                 (if low → fallback)
```

---

**End of Diagram**

For implementation details, see:
- [ADAPTIVE_QUERY_ROUTING_DESIGN.md](../../ADAPTIVE_QUERY_ROUTING_DESIGN.md)
- [ADAPTIVE_ROUTING_SUMMARY.md](../../ADAPTIVE_ROUTING_SUMMARY.md)
