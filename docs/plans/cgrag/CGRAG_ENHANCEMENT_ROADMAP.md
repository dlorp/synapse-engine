# CGRAG Enhancement Roadmap

**Date:** 2025-11-30
**Status:** Planning Complete - Ready for Implementation
**Total Duration:** 10-11 weeks

---

## Overview

This roadmap integrates **two complementary CGRAG enhancement strategies** based on global RAG research:

1. **[CGRAG Enhancement Plan](./CGRAG_ENHANCEMENT_PLAN.md)** - Infrastructure improvements (hybrid search, knowledge graph, multi-context)
2. **[CGRAG Context Enhancement Design](./CGRAG_CONTEXT_ENHANCEMENT_DESIGN.md)** - Chunk quality improvements (metadata, semantic chunking, self-RAG)

Both plans can be implemented **in parallel** or **sequentially**, with the Context Enhancement providing immediate quality gains while the Enhancement Plan builds long-term infrastructure.

---

## Implementation Strategies

### Strategy A: Sequential (Conservative)

Implement Context Enhancement first, then Enhancement Plan.

**Advantages:**
- Immediate quality gains (+15% accuracy)
- Lower risk (smaller changes first)
- Validates chunk quality before adding complexity
- Easier to measure impact of each phase

**Timeline: 10-11 weeks**

| Weeks | Phase | Focus |
|-------|-------|-------|
| 1-4 | Context Enhancement | Metadata, semantic chunking, self-RAG |
| 5-6 | Hybrid Search + Vector DB | Qdrant/FAISS, BM25, RRF |
| 7-8 | Knowledge Graph RAG | Entity extraction, graph retrieval |
| 9-10 | Multi-Context Sources | Docs, code, chat history |
| 11 | Integration & Polish | End-to-end testing, optimization |

### Strategy B: Parallel (Aggressive)

Implement both plans simultaneously with different engineers.

**Advantages:**
- Faster time to full enhancement (7-8 weeks)
- Efficient use of multiple engineers
- Both improvements land together

**Challenges:**
- Requires careful coordination
- Merge conflicts in `cgrag.py`
- More complex testing

**Timeline: 7-8 weeks**

| Weeks | Team A (Context) | Team B (Infrastructure) |
|-------|------------------|-------------------------|
| 1-2 | Enhanced models + metadata | Vector DB abstraction + BM25 |
| 3-4 | Semantic chunking | Knowledge Graph integration |
| 5-6 | Context enrichment + Self-RAG | Multi-context sources |
| 7 | Integration | Integration |
| 8 | Testing & optimization | Testing & optimization |

### Strategy C: Hybrid (Recommended)

Start with Context Enhancement Phase 1-2, then add Infrastructure in parallel.

**Advantages:**
- Best of both strategies
- Early wins establish foundation
- Parallel work minimizes total time
- Lower risk than full parallel

**Timeline: 8-9 weeks**

| Weeks | Focus | Deliverables |
|-------|-------|--------------|
| 1-2 | Context Enhancement (solo) | Enhanced models, metadata extraction, semantic chunking |
| 3-4 | Both (parallel) | Context enrichment + Hybrid search |
| 5-6 | Both (parallel) | Self-RAG + Knowledge Graph |
| 7-8 | Infrastructure (solo) | Multi-context sources, chat history |
| 9 | Integration & polish | End-to-end testing, optimization |

---

## Expected Cumulative Impact

### After Context Enhancement Only (Week 4)

| Metric | Current | After Enhancement | Improvement |
|--------|---------|-------------------|-------------|
| Retrieval Accuracy | ~70% | **85%+** | +15% |
| User Understanding | Limited | Excellent | Major |
| Context Relevance | Variable | >0.8 | Significant |
| Indexing Time | 1000/sec | 800-900/sec | -10-20% |
| Retrieval Latency | <100ms | <120ms | +20ms |

### After Full Enhancement (Week 10-11)

| Metric | Current | After Full Enhancement | Improvement |
|--------|---------|------------------------|-------------|
| Retrieval Accuracy | ~70% | **90%+** | +20-25% |
| Retrieval Latency | <100ms | **<65ms** | -35% |
| Hallucination Rate | ~10% | **<3%** | -70% |
| Context Relevance | Variable | **>0.8** | Major |
| Code Retrieval | Fair | Excellent | Major |
| Multi-Source Support | Docs only | Docs + Code + Chat | 3x sources |

---

## Feature Comparison

### Context Enhancement Features

| Feature | Description | Impact |
|---------|-------------|--------|
| **Document Metadata** | Title, description, tags, author | Better search context |
| **Section Hierarchy** | Breadcrumb navigation (e.g., "Docs > API > Auth") | User understanding |
| **Code Context** | Function/class names, docstrings, imports | Code retrieval |
| **Semantic Chunking** | Preserve document structure (sections, functions) | Logical chunks |
| **Context Enrichment** | Add surrounding chunks, same-section chunks | Better context |
| **Self-RAG Quality** | Relevance verification + query reformulation | Higher quality |

### Infrastructure Enhancement Features

| Feature | Description | Impact |
|---------|-------------|--------|
| **Hybrid Search** | Vector + BM25 with RRF | Better code/technical queries |
| **Vector DB Migration** | Qdrant (primary) + FAISS (fallback) | Metal acceleration |
| **Knowledge Graph RAG** | Entity extraction + graph traversal | Reduced hallucinations |
| **Multi-Context Sources** | Docs + Codebase + Chat History | Richer context |
| **AST Code Chunking** | Parse code by functions/classes | Better code chunks |
| **Chat History Context** | Session-aware retrieval | Conversation continuity |

---

## Dependencies & Prerequisites

### Context Enhancement

**Required:**
- Python 3.11+
- sentence-transformers (already installed)
- FAISS (already installed)

**Optional (for full features):**
- spacy (for entity extraction in section detection)

**No Breaking Changes:** Works with existing FAISS indexes.

### Infrastructure Enhancement

**Required:**
```txt
qdrant-client>=1.7.0
rank_bm25>=0.2.2
spacy>=3.7.0
networkx>=3.0
tree-sitter>=0.21.0
tree-sitter-python>=0.21.0
tree-sitter-typescript>=0.21.0
```

**Breaking Changes:** Requires re-indexing with new vector DB.

---

## Risk Assessment

### Context Enhancement Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Indexing slowdown | Low | Acceptable -10-20% for +15% accuracy |
| Metadata extraction errors | Low | Fallback to basic chunking |
| Increased storage | Low | Metadata adds ~20% to chunk size |

### Infrastructure Enhancement Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Vector DB migration issues | Medium | FAISS fallback for compatibility |
| Qdrant not available | Medium | Automatic detection + fallback |
| Graph extraction quality | Medium | Validate entity extraction quality |
| Re-indexing downtime | Medium | Blue-green deployment pattern |

---

## Testing Strategy

### Context Enhancement Testing

**Unit Tests:**
- Metadata extraction for all file types
- Semantic chunking preserves structure
- Breadcrumb generation accuracy
- Code context extraction completeness

**Integration Tests:**
- End-to-end indexing with enhanced chunks
- Retrieval with enriched context
- Self-RAG quality verification loop

**Performance Tests:**
- Indexing throughput benchmark
- Retrieval latency with enrichment overhead
- Memory usage with enhanced metadata

### Infrastructure Enhancement Testing

**Unit Tests:**
- BM25 + Vector RRF combination
- Knowledge graph entity extraction
- Multi-source context retrieval
- AST code parsing accuracy

**Integration Tests:**
- Hybrid search end-to-end
- Graph-enhanced retrieval
- Multi-source context aggregation

**Performance Tests:**
- Qdrant vs FAISS performance
- Graph traversal latency
- Multi-source retrieval overhead

---

## Rollback Strategy

### Context Enhancement

**If issues occur:**
1. Switch back to original `DocumentChunk` model
2. Use existing FAISS indexes (no re-indexing needed)
3. Disable semantic chunking (fall back to word-based)

**Impact:** Zero downtime, seamless fallback.

### Infrastructure Enhancement

**If issues occur:**
1. Switch vector DB factory to FAISS only
2. Disable hybrid search (vector only)
3. Disable knowledge graph retrieval
4. Use existing indexes

**Impact:** Minimal downtime (configuration change only).

---

## Success Metrics

### Phase Success Criteria

**Context Enhancement:**
- [ ] Retrieval accuracy >85% on test queries
- [ ] Breadcrumb navigation works for all file types
- [ ] Code context extraction >90% accurate
- [ ] Self-RAG reduces low-quality retrievals by 50%

**Infrastructure Enhancement:**
- [ ] Hybrid search improves code queries by >20%
- [ ] Knowledge graph reduces hallucinations by >50%
- [ ] Multi-source retrieval works seamlessly
- [ ] AST chunking preserves 100% of function definitions

### Overall Success Criteria

- [ ] Retrieval accuracy >90%
- [ ] Retrieval latency <65ms
- [ ] User satisfaction survey >4.5/5
- [ ] Hallucination rate <3%
- [ ] System uptime >99.5%

---

## Next Steps

1. **Choose Implementation Strategy** (A, B, or C)
2. **Assign Teams/Engineers** (if parallel implementation)
3. **Set Up Development Branches**
   - `feature/cgrag-context-enhancement`
   - `feature/cgrag-infrastructure-enhancement`
4. **Create Sprint Plan** (2-week sprints recommended)
5. **Begin Implementation** (Week 1 focus: Enhanced models or Vector DB abstraction)

---

## Related Documentation

- [CGRAG Enhancement Plan](./CGRAG_ENHANCEMENT_PLAN.md) - Infrastructure improvements (6-7 weeks)
- [CGRAG Context Enhancement Design](./CGRAG_CONTEXT_ENHANCEMENT_DESIGN.md) - Chunk quality (2-3 weeks)
- [Global RAG Research](../research/GLOBAL_RAG_RESEARCH.md) - Research findings from 7 languages
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Development history
- [Current CGRAG Implementation](${PROJECT_DIR}/backend/app/services/cgrag.py) - Existing code

---

**Recommendation:** Start with **Strategy C (Hybrid)** for optimal balance of risk and speed. Context Enhancement Weeks 1-2 provide immediate value while Infrastructure Enhancement builds in parallel from Week 3 onwards.
