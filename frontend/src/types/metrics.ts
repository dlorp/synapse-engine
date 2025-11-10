/**
 * Query metrics types
 * Real-time query analytics data from backend
 */

export interface QueryMetrics {
  timestamps: string[];      // ISO8601 timestamps (18 datapoints)
  queryRate: number[];       // queries/sec at each timestamp
  totalQueries: number;      // Total queries processed
  avgLatencyMs: number;      // Average latency in milliseconds
  tierDistribution: {
    Q2: number;              // Count of Q2 queries
    Q3: number;              // Count of Q3 queries
    Q4: number;              // Count of Q4 queries
  };
}

/**
 * Tier comparison metrics
 * Real-time performance metrics for each model tier (Q2/Q3/Q4)
 */
export interface TierMetrics {
  tiers: Array<{
    name: "Q2" | "Q3" | "Q4";
    tokensPerSec: number[];    // last 20 samples
    latencyMs: number[];        // last 20 samples
    requestCount: number;
    errorRate: number;
  }>;
}

/**
 * Routing metrics types
 * Analytics for orchestrator routing decisions and model availability
 */
export interface RoutingMetrics {
  decisionMatrix: Array<{
    complexity: "SIMPLE" | "MODERATE" | "COMPLEX";
    tier: "Q2" | "Q3" | "Q4";
    count: number;
    avgScore: number;
  }>;
  accuracyMetrics: {
    totalDecisions: number;
    avgDecisionTimeMs: number;
    fallbackRate: number;  // 0-1 (0 = 0%, 1 = 100%)
  };
  modelAvailability: Array<{
    tier: "Q2" | "Q3" | "Q4";
    available: number;
    total: number;
  }>;
}

/**
 * Resource metrics types
 * Real-time system resource monitoring data
 */
export interface ResourceMetrics {
  vram: {
    used: number;     // GB
    total: number;    // GB
    percent: number;  // 0-100
  };
  cpu: {
    percent: number;  // 0-100
    cores: number;
  };
  memory: {
    used: number;     // GB
    total: number;    // GB
    percent: number;  // 0-100
  };
  faissIndexSize: number;      // bytes
  redisCacheSize: number;       // bytes
  activeConnections: number;
  threadPoolStatus: {
    active: number;
    queued: number;
  };
  diskIO: {
    readMBps: number;
    writeMBps: number;
  };
  networkThroughput: {
    rxMBps: number;
    txMBps: number;
  };
}
