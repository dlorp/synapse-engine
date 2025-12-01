/**
 * TypeScript types for CGRAG (Contextually-Guided RAG) visualization.
 *
 * Defines data structures for displaying enhanced CGRAG features:
 * - Hybrid search (vector + BM25)
 * - Two-stage reranking
 * - Knowledge graph context
 * - RAG quality triad metrics
 * - Corrective RAG actions
 */

// ============================================================================
// Retrieval Pipeline Types
// ============================================================================

/**
 * Stage in the retrieval pipeline.
 */
export type RetrievalStage =
  | 'embedding'      // Query embedding generation
  | 'vector_search'  // Vector similarity search
  | 'bm25_search'    // BM25 keyword search
  | 'fusion'         // Hybrid result fusion (RRF)
  | 'coarse_rerank'  // First-stage reranking
  | 'fine_rerank'    // Second-stage reranking
  | 'kg_expansion'   // Knowledge graph expansion
  | 'filtering'      // Final relevance filtering
  | 'complete';      // Pipeline complete

/**
 * Status of a pipeline stage.
 */
export type StageStatus = 'pending' | 'active' | 'complete' | 'error';

/**
 * A single stage in the retrieval pipeline.
 */
export interface PipelineStage {
  /** Stage identifier */
  stage: RetrievalStage;
  /** Current status */
  status: StageStatus;
  /** Number of candidates at this stage */
  candidateCount: number;
  /** Stage execution time in milliseconds */
  executionTimeMs?: number;
  /** Stage start timestamp */
  startedAt?: string;
  /** Stage completion timestamp */
  completedAt?: string;
  /** Error message if status is 'error' */
  error?: string;
}

/**
 * Complete retrieval pipeline state.
 */
export interface RetrievalPipeline {
  /** Pipeline stages in order */
  stages: PipelineStage[];
  /** Total pipeline execution time */
  totalTimeMs: number;
  /** Current active stage */
  currentStage: RetrievalStage;
  /** Overall pipeline status */
  status: 'running' | 'complete' | 'error';
}

// ============================================================================
// Hybrid Search Types
// ============================================================================

/**
 * Score breakdown for a single chunk in hybrid search.
 */
export interface HybridSearchScore {
  /** Chunk identifier */
  chunkId: string;
  /** Vector similarity score (0-1) */
  vectorScore: number;
  /** BM25 keyword score */
  bm25Score: number;
  /** Combined RRF score */
  fusionScore: number;
  /** Vector search rank (1-indexed) */
  vectorRank: number;
  /** BM25 search rank (1-indexed) */
  bm25Rank: number;
  /** Final combined rank (1-indexed) */
  finalRank: number;
}

/**
 * Aggregated hybrid search metrics.
 */
export interface HybridSearchMetrics {
  /** Total candidates from vector search */
  vectorCandidates: number;
  /** Total candidates from BM25 search */
  bm25Candidates: number;
  /** Overlap between vector and BM25 results */
  overlapCount: number;
  /** Average vector score */
  avgVectorScore: number;
  /** Average BM25 score */
  avgBm25Score: number;
  /** RRF constant used for fusion */
  rrfConstant: number;
  /** Score breakdown for top-k results */
  topResults: HybridSearchScore[];
}

// ============================================================================
// Reranking Types
// ============================================================================

/**
 * Score change during reranking stages.
 */
export interface RerankingScore {
  /** Chunk identifier */
  chunkId: string;
  /** Initial score before reranking */
  initialScore: number;
  /** Score after coarse reranking */
  coarseScore?: number;
  /** Score after fine reranking */
  fineScore?: number;
  /** Initial rank (1-indexed) */
  initialRank: number;
  /** Rank after coarse reranking */
  coarseRank?: number;
  /** Final rank after fine reranking */
  finalRank?: number;
  /** Score delta from initial to final */
  scoreDelta: number;
  /** Rank change (positive = moved up) */
  rankChange: number;
}

/**
 * Reranking stage metrics.
 */
export interface RerankingMetrics {
  /** Coarse reranking model used */
  coarseModel?: string;
  /** Fine reranking model used */
  fineModel?: string;
  /** Coarse stage execution time (ms) */
  coarseTimeMs?: number;
  /** Fine stage execution time (ms) */
  fineTimeMs?: number;
  /** Number of candidates reranked */
  candidatesReranked: number;
  /** Score changes for top results */
  scoreChanges: RerankingScore[];
}

// ============================================================================
// Knowledge Graph Types
// ============================================================================

/**
 * Entity extracted from text.
 */
export interface Entity {
  /** Entity text */
  text: string;
  /** Entity type (PERSON, ORG, CONCEPT, etc.) */
  label: string;
  /** Source chunk ID */
  chunkId: string;
  /** Confidence score (0-1) */
  confidence?: number;
}

/**
 * Relationship between entities.
 */
export interface Relationship {
  /** Source entity text */
  source: string;
  /** Target entity text */
  target: string;
  /** Relationship type (USES, IMPLEMENTS, etc.) */
  relationType: string;
  /** Source chunk ID */
  chunkId: string;
  /** Confidence score (0-1) */
  confidence?: number;
}

/**
 * Knowledge graph context for a query.
 */
export interface KnowledgeGraphContext {
  /** Entities found in query */
  queryEntities: Entity[];
  /** Related entities from graph */
  relatedEntities: Entity[];
  /** Relationships between entities */
  relationships: Relationship[];
  /** Additional chunks found via graph traversal */
  expandedChunkIds: string[];
  /** Number of graph hops performed */
  hopCount: number;
}

// ============================================================================
// RAG Quality Triad Types
// ============================================================================

/**
 * RAG Triad metric scores.
 *
 * Based on French research (Mistral AI):
 * - Context Relevance: Were retrieved docs relevant to query?
 * - Groundedness: Is response grounded in retrieved context?
 * - Answer Relevance: Does answer address the original question?
 */
export interface RAGTriadMetrics {
  /** Context relevance score (0-1) */
  contextRelevance: number;
  /** Groundedness score (0-1) */
  groundedness: number;
  /** Answer relevance score (0-1) */
  answerRelevance: number;
  /** Overall quality score (average of three) */
  overallQuality: number;
  /** Timestamp of measurement */
  timestamp: string;
}

/**
 * Historical RAG quality trend.
 */
export interface RAGQualityTrend {
  /** Recent measurements (last 20) */
  history: RAGTriadMetrics[];
  /** Average context relevance */
  avgContextRelevance: number;
  /** Average groundedness */
  avgGroundedness: number;
  /** Average answer relevance */
  avgAnswerRelevance: number;
  /** Trend direction */
  trend: 'improving' | 'declining' | 'stable';
}

// ============================================================================
// Corrective RAG (CRAG) Types
// ============================================================================

/**
 * CRAG action type.
 */
export type CRAGAction =
  | 'none'              // No correction needed
  | 'query_rewrite'     // Reformulated query
  | 'web_fallback'      // Fell back to web search
  | 'context_filter'    // Filtered low-relevance chunks
  | 'kg_expansion';     // Expanded via knowledge graph

/**
 * CRAG decision and action taken.
 */
export interface CRAGDecision {
  /** Action taken */
  action: CRAGAction;
  /** Reason for action */
  reason: string;
  /** Original query */
  originalQuery?: string;
  /** Rewritten query (if action = query_rewrite) */
  rewrittenQuery?: string;
  /** Number of chunks filtered (if action = context_filter) */
  filteredCount?: number;
  /** Web search results count (if action = web_fallback) */
  webResultsCount?: number;
  /** Decision timestamp */
  timestamp: string;
}

// ============================================================================
// Enhanced Chunk Display Types
// ============================================================================

/**
 * Document breadcrumb showing chunk location.
 */
export interface ChunkBreadcrumb {
  /** File path */
  file: string;
  /** Section/heading hierarchy */
  sections: string[];
  /** Line range (for code) */
  lineRange?: { start: number; end: number };
}

/**
 * Enhanced chunk with full metadata.
 */
export interface EnhancedChunk {
  /** Chunk identifier */
  id: string;
  /** Chunk text content */
  text: string;
  /** Source document path */
  sourcePath: string;
  /** Document breadcrumb */
  breadcrumb: ChunkBreadcrumb;
  /** Relevance score (0-1) */
  relevanceScore: number;
  /** Hybrid search scores */
  hybridScore?: HybridSearchScore;
  /** Reranking score changes */
  rerankingScore?: RerankingScore;
  /** Extracted entities */
  entities?: Entity[];
  /** Language (for syntax highlighting) */
  language?: string;
  /** Token count */
  tokenCount: number;
  /** Chunk creation timestamp */
  indexedAt: string;
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

/**
 * Real-time CGRAG event from backend.
 */
export interface CGRAGStreamEvent {
  /** Event type */
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

  /** Event content */
  content?: string;

  /** Pipeline state (for pipeline events) */
  pipeline?: RetrievalPipeline;

  /** Stage details (for stage events) */
  stage?: PipelineStage;

  /** Hybrid search metrics */
  hybridMetrics?: HybridSearchMetrics;

  /** Reranking metrics */
  rerankingMetrics?: RerankingMetrics;

  /** Knowledge graph context */
  kgContext?: KnowledgeGraphContext;

  /** CRAG decision */
  cragDecision?: CRAGDecision;

  /** RAG triad metrics */
  triadMetrics?: RAGTriadMetrics;

  /** Retrieved chunks */
  chunks?: EnhancedChunk[];

  /** Event timestamp */
  timestamp: string;
}

// ============================================================================
// Component Props Types
// ============================================================================

/**
 * Props for RetrievalPipelineViz component.
 */
export interface RetrievalPipelineVizProps {
  pipeline: RetrievalPipeline;
  className?: string;
}

/**
 * Props for HybridSearchPanel component.
 */
export interface HybridSearchPanelProps {
  metrics: HybridSearchMetrics;
  className?: string;
}

/**
 * Props for RAGTriadDisplay component.
 */
export interface RAGTriadDisplayProps {
  metrics: RAGTriadMetrics;
  trend?: RAGQualityTrend;
  className?: string;
}

/**
 * Props for CRAGDecisionDisplay component.
 */
export interface CRAGDecisionDisplayProps {
  decision: CRAGDecision;
  className?: string;
}

/**
 * Props for EnhancedChunkCard component.
 */
export interface EnhancedChunkCardProps {
  chunk: EnhancedChunk;
  rank: number;
  showScores?: boolean;
  showEntities?: boolean;
  className?: string;
}

/**
 * Props for KnowledgeGraphPanel component.
 */
export interface KnowledgeGraphPanelProps {
  context: KnowledgeGraphContext;
  className?: string;
}
