/**
 * Query-related TypeScript types for the Multi-Model Orchestration WebUI
 */

export type QueryMode = 'two-stage' | 'simple' | 'council' | 'benchmark';

export interface QueryRequest {
  query: string;
  mode: QueryMode;
  useContext: boolean;
  useWebSearch: boolean;
  maxTokens: number;
  temperature: number;
  councilAdversarial?: boolean;
  councilModerator?: boolean;
  councilModeratorActive?: boolean;
  councilModeratorModel?: string;
  councilModeratorCheckFrequency?: number;
  councilProModel?: string;
  councilConModel?: string;
  benchmarkSerial?: boolean;
}

export interface QueryComplexity {
  tier: string;
  score: number;
  reasoning: string;
  indicators: Record<string, any>;
}

export interface ArtifactInfo {
  filePath: string;
  relevanceScore: number;
  chunkIndex: number;
  tokenCount: number;
}

export interface WebSearchResult {
  title: string;
  url: string;
  content: string;
  engine?: string;
  score: number;
  publishedDate?: string;
}

export interface DialogueTurn {
  turnNumber: number;
  speakerId: string;
  persona: string;
  content: string;
  timestamp: string;
  tokensUsed: number;
}

export interface QueryMetadata {
  modelTier: string;
  modelId: string;
  complexity: QueryComplexity | null;
  tokensUsed: number;
  processingTimeMs: number;
  cgragArtifacts: number;
  cgragArtifactsInfo: ArtifactInfo[];
  cacheHit: boolean;

  // Two-stage processing fields
  queryMode?: string;
  stage1Response?: string;
  stage1ModelId?: string;
  stage1Tier?: string;
  stage1ProcessingTime?: number;
  stage1Tokens?: number;
  stage2ModelId?: string;
  stage2Tier?: string;
  stage2ProcessingTime?: number;
  stage2Tokens?: number;

  // Web search metadata
  webSearchResults?: WebSearchResult[];
  webSearchTimeMs?: number;
  webSearchCount?: number;

  // Council mode metadata
  councilMode?: 'consensus' | 'adversarial';
  councilParticipants?: string[];
  councilRounds?: number;
  councilResponses?: any[];

  // Moderator analysis metadata
  councilModeratorAnalysis?: string;
  councilModeratorModel?: string;
  councilModeratorTokens?: number;
  councilModeratorBreakdown?: {
    argument_strength?: any;
    logical_fallacies?: string[];
    rhetorical_techniques?: string[];
    key_turning_points?: string[];
    unanswered_questions?: string[];
    overall_winner?: 'pro' | 'con' | 'tie' | null;
  };
  councilModeratorInterjections?: number;

  // Benchmark mode metadata
  benchmarkResults?: BenchmarkResult[];
  benchmarkExecutionMode?: 'parallel' | 'serial';
  benchmarkSummary?: BenchmarkSummary;
}

export interface BenchmarkResult {
  modelId: string;
  tier: string;
  responseText: string;
  tokens: number;
  processingTimeMs: number;
  estimatedVramGb: number;
  success: boolean;
  error?: string;
}

export interface BenchmarkSummary {
  totalModels: number;
  successfulModels: number;
  failedModels: number;
  totalTimeMs: number;
  avgTokens: number;
  avgProcessingTimeMs: number;
  executionMode: 'parallel' | 'serial';
}

export interface QueryResponse {
  id: string;
  query: string;
  response: string;
  metadata: QueryMetadata;
  timestamp: string;

  // Multi-chat dialogue fields
  councilDialogue?: boolean;
  councilTurns?: DialogueTurn[];
  councilSynthesis?: string;
  councilTerminationReason?: string;
  councilTotalTurns?: number;
  councilMaxTurns?: number;
  councilPersonas?: Record<string, string>;
}
