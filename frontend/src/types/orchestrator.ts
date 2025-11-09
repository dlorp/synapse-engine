/**
 * Orchestrator status types
 * Real-time data for NEURAL SUBSTRATE ORCHESTRATOR visualization
 */

export type ComplexityLevel = 'SIMPLE' | 'MODERATE' | 'COMPLEX';
export type ModelTierLabel = 'Q2' | 'Q3' | 'Q4';

/**
 * Individual routing decision
 */
export interface RoutingDecision {
  id: string;
  query: string;
  tier: ModelTierLabel;
  complexity: ComplexityLevel;
  timestamp: string;
  score: number;
}

/**
 * Model tier utilization metrics
 */
export interface TierUtilization {
  tier: ModelTierLabel;
  utilizationPercent: number;  // 0-100
  activeRequests: number;
  totalProcessed: number;
}

/**
 * Query complexity distribution
 */
export interface ComplexityDistribution {
  simple: number;      // 0-100 percentage
  moderate: number;    // 0-100 percentage
  complex: number;     // 0-100 percentage
}

/**
 * Complete orchestrator status response
 */
export interface OrchestratorStatus {
  tierUtilization: TierUtilization[];
  recentDecisions: RoutingDecision[];
  complexityDistribution: ComplexityDistribution;
  totalDecisions: number;
  avgDecisionTimeMs: number;
  timestamp: string;
}
