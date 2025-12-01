# CGRAG Visualization Components - Quick Reference

**Quick reference for component props, types, and usage patterns.**

---

## Component Import

```typescript
import {
  RetrievalPipelineViz,
  HybridSearchPanel,
  RAGTriadDisplay,
  CRAGDecisionDisplay,
  EnhancedChunkCard,
} from '@/components/cgrag';

import type {
  RetrievalPipeline,
  HybridSearchMetrics,
  RAGTriadMetrics,
  RAGQualityTrend,
  CRAGDecision,
  EnhancedChunk,
} from '@/types/cgrag';
```

---

## 1. RetrievalPipelineViz

### Props
```typescript
interface RetrievalPipelineVizProps {
  pipeline: RetrievalPipeline;
  className?: string;
}
```

### Pipeline Type
```typescript
interface RetrievalPipeline {
  stages: PipelineStage[];
  totalTimeMs: number;
  currentStage: RetrievalStage;
  status: 'running' | 'complete' | 'error';
}

interface PipelineStage {
  stage: RetrievalStage;
  status: 'pending' | 'active' | 'complete' | 'error';
  candidateCount: number;
  executionTimeMs?: number;
  startedAt?: string;
  completedAt?: string;
  error?: string;
}

type RetrievalStage =
  | 'embedding'
  | 'vector_search'
  | 'bm25_search'
  | 'fusion'
  | 'coarse_rerank'
  | 'fine_rerank'
  | 'kg_expansion'
  | 'filtering'
  | 'complete';
```

### Usage
```tsx
<RetrievalPipelineViz pipeline={pipelineState} />
```

---

## 2. HybridSearchPanel

### Props
```typescript
interface HybridSearchPanelProps {
  metrics: HybridSearchMetrics;
  className?: string;
}
```

### Metrics Type
```typescript
interface HybridSearchMetrics {
  vectorCandidates: number;
  bm25Candidates: number;
  overlapCount: number;
  avgVectorScore: number;
  avgBm25Score: number;
  rrfConstant: number;
  topResults: HybridSearchScore[];
}

interface HybridSearchScore {
  chunkId: string;
  vectorScore: number;
  bm25Score: number;
  fusionScore: number;
  vectorRank: number;
  bm25Rank: number;
  finalRank: number;
}
```

### Usage
```tsx
<HybridSearchPanel metrics={hybridMetrics} />
```

---

## 3. RAGTriadDisplay

### Props
```typescript
interface RAGTriadDisplayProps {
  metrics: RAGTriadMetrics;
  trend?: RAGQualityTrend;
  className?: string;
}
```

### Types
```typescript
interface RAGTriadMetrics {
  contextRelevance: number;    // 0-1
  groundedness: number;         // 0-1
  answerRelevance: number;      // 0-1
  overallQuality: number;       // 0-1
  timestamp: string;
}

interface RAGQualityTrend {
  history: RAGTriadMetrics[];
  avgContextRelevance: number;
  avgGroundedness: number;
  avgAnswerRelevance: number;
  trend: 'improving' | 'declining' | 'stable';
}
```

### Usage
```tsx
<RAGTriadDisplay
  metrics={currentMetrics}
  trend={historicalTrend}  // Optional
/>
```

---

## 4. CRAGDecisionDisplay

### Props
```typescript
interface CRAGDecisionDisplayProps {
  decision: CRAGDecision;
  className?: string;
}
```

### Decision Type
```typescript
interface CRAGDecision {
  action: CRAGAction;
  reason: string;
  originalQuery?: string;
  rewrittenQuery?: string;
  filteredCount?: number;
  webResultsCount?: number;
  timestamp: string;
}

type CRAGAction =
  | 'none'              // Hidden (no correction)
  | 'query_rewrite'
  | 'web_fallback'
  | 'context_filter'
  | 'kg_expansion';
```

### Usage
```tsx
{decision.action !== 'none' && (
  <CRAGDecisionDisplay decision={decision} />
)}
```

---

## 5. EnhancedChunkCard

### Props
```typescript
interface EnhancedChunkCardProps {
  chunk: EnhancedChunk;
  rank: number;
  showScores?: boolean;     // Default: true
  showEntities?: boolean;   // Default: false
  className?: string;
}
```

### Chunk Type
```typescript
interface EnhancedChunk {
  id: string;
  text: string;
  sourcePath: string;
  breadcrumb: ChunkBreadcrumb;
  relevanceScore: number;
  hybridScore?: HybridSearchScore;
  rerankingScore?: RerankingScore;
  entities?: Entity[];
  language?: string;
  tokenCount: number;
  indexedAt: string;
}

interface ChunkBreadcrumb {
  file: string;
  sections: string[];
  lineRange?: { start: number; end: number };
}

interface RerankingScore {
  chunkId: string;
  initialScore: number;
  coarseScore?: number;
  fineScore?: number;
  initialRank: number;
  coarseRank?: number;
  finalRank: number;
  scoreDelta: number;
  rankChange: number;
}

interface Entity {
  text: string;
  label: string;
  chunkId: string;
  confidence?: number;
}
```

### Usage
```tsx
{chunks.map((chunk, index) => (
  <EnhancedChunkCard
    key={chunk.id}
    chunk={chunk}
    rank={index + 1}
    showScores={true}
    showEntities={true}
  />
))}
```

---

## WebSocket Event Type

```typescript
interface CGRAGStreamEvent {
  type:
    | 'pipeline_start'
    | 'stage_start'
    | 'stage_complete'
    | 'stage_error'
    | 'hybrid_scores'
    | 'reranking_complete'
    | 'kg_expansion'
    | 'crag_decision'
    | 'triad_metrics'
    | 'pipeline_complete';

  content?: string;
  pipeline?: RetrievalPipeline;
  stage?: PipelineStage;
  hybridMetrics?: HybridSearchMetrics;
  rerankingMetrics?: RerankingMetrics;
  kgContext?: KnowledgeGraphContext;
  cragDecision?: CRAGDecision;
  triadMetrics?: RAGTriadMetrics;
  chunks?: EnhancedChunk[];
  timestamp: string;
}
```

---

## Complete Example

```tsx
import React, { useState, useEffect } from 'react';
import {
  RetrievalPipelineViz,
  HybridSearchPanel,
  RAGTriadDisplay,
  CRAGDecisionDisplay,
  EnhancedChunkCard,
} from '@/components/cgrag';
import type { CGRAGStreamEvent } from '@/types/cgrag';

const CGRAGQueryPage: React.FC<{ queryId: string }> = ({ queryId }) => {
  const [pipeline, setPipeline] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [triad, setTriad] = useState(null);
  const [decision, setDecision] = useState(null);
  const [chunks, setChunks] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/cgrag/stream/${queryId}`);

    ws.onmessage = (event) => {
      const cgragEvent: CGRAGStreamEvent = JSON.parse(event.data);

      switch (cgragEvent.type) {
        case 'stage_start':
        case 'stage_complete':
          setPipeline(cgragEvent.pipeline);
          break;
        case 'hybrid_scores':
          setMetrics(cgragEvent.hybridMetrics);
          break;
        case 'triad_metrics':
          setTriad(cgragEvent.triadMetrics);
          break;
        case 'crag_decision':
          setDecision(cgragEvent.cragDecision);
          break;
        case 'pipeline_complete':
          setChunks(cgragEvent.chunks || []);
          break;
      }
    };

    return () => ws.close();
  }, [queryId]);

  return (
    <div>
      {pipeline && <RetrievalPipelineViz pipeline={pipeline} />}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div>
          {metrics && <HybridSearchPanel metrics={metrics} />}
          {triad && <RAGTriadDisplay metrics={triad} />}
        </div>

        <div>
          {decision && <CRAGDecisionDisplay decision={decision} />}

          {chunks.map((chunk, index) => (
            <EnhancedChunkCard
              key={chunk.id}
              chunk={chunk}
              rank={index + 1}
              showScores
              showEntities
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default CGRAGQueryPage;
```

---

## Color Reference

```css
/* Primary colors */
--phosphor-orange: #ff9500;
--cyan: #00ffff;
--green: #00ff00;
--amber: #ffaa00;
--red: #ff0000;

/* Backgrounds */
--bg-primary: #000000;
--bg-panel: #0a0a0a;

/* Score colors */
--score-high: #00ff00;    /* >70% */
--score-med: #ffaa00;     /* 40-70% */
--score-low: #ff6600;     /* <40% */

/* Hybrid search colors */
--vector-color: #00ffff;
--bm25-color: #ff9500;
--fusion-color: #00ff00;
```

---

## Animation Guidelines

```css
/* Transitions */
transition: all 0.3s ease;

/* Pulse animation (active stages) */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
animation: pulse 1.5s ease-in-out infinite;

/* Slide-in animation (CRAG decisions) */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
animation: slideIn 0.3s ease;

/* Glow animation (active pulse) */
@keyframes pulseGlow {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
}
animation: pulseGlow 1.5s ease-in-out infinite;
```

---

## Responsive Breakpoints

```css
/* Desktop: Default */

/* Tablet */
@media (max-width: 1024px) {
  /* Switch to single-column layouts */
}

/* Mobile */
@media (max-width: 768px) {
  /* Reduce font sizes, compact spacing */
}
```

---

**For full documentation, see [CGRAG_VISUALIZATION_GUIDE.md](./CGRAG_VISUALIZATION_GUIDE.md)**
