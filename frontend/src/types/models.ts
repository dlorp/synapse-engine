/**
 * Individual model status from backend API
 * Fields match backend Pydantic model aliases (camelCase)
 */
export interface ModelStatus {
  id: string;
  name: string;
  tier: 'Q2' | 'Q3' | 'Q4';
  port: number;
  state: 'active' | 'idle' | 'processing' | 'error' | 'offline';
  memoryUsed: number;      // MB
  memoryTotal: number;     // MB
  requestCount: number;    // Total requests processed
  avgResponseTime: number; // ms
  lastActive: string;      // ISO timestamp
  errorCount: number;
  uptimeSeconds: number;
}

/**
 * Complete system status response from backend
 * Top-level fields match backend Pydantic model aliases (camelCase)
 */
export interface ModelStatusResponse {
  models: ModelStatus[];
  totalVramGb: number;       // Note: lowercase "Gb" from backend
  totalVramUsedGb: number;   // Note: lowercase "Gb" from backend
  cacheHitRate: number;      // 0.0 to 1.0
  activeQueries: number;
  totalRequests: number;
  timestamp: string;         // ISO timestamp
}

export interface QueryRequest {
  query: string;
  mode?: 'auto' | 'Q2' | 'Q3' | 'Q4';
  useContext?: boolean;
  maxTokens?: number;
}

export interface QueryResponse {
  id: string;
  query: string;
  response: string;
  modelTier: 'Q2' | 'Q3' | 'Q4';
  responseTime: number;
  tokensUsed: number;
  timestamp: string;
}

/**
 * Model tier classification
 */
export type ModelTier = 'fast' | 'balanced' | 'powerful';

/**
 * Tier configuration for profile
 */
export interface TierConfig {
  tier: ModelTier;
  modelIds: string[];
  contextSize?: number;
  temperature?: number;
  maxTokens?: number;
}

/**
 * Discovered model from HUB scan
 * Fields match backend model discovery system
 */
export interface DiscoveredModel {
  filePath: string;
  filename: string;
  family: string;
  version?: string;
  sizeParams: number;
  quantization: string;
  isThinkingModel: boolean;
  thinkingOverride?: boolean;
  isInstruct: boolean;
  isCoder: boolean;
  assignedTier: ModelTier;
  tierOverride?: ModelTier;
  port: number | null;
  enabled: boolean;
  modelId: string;

  // Phase 2: Per-model runtime settings overrides (null = use global setting)
  nGpuLayers: number | null;
  ctxSize: number | null;
  nThreads: number | null;
  batchSize: number | null;
}

/**
 * Model registry with all discovered models
 */
export interface ModelRegistry {
  models: Record<string, DiscoveredModel>;
  scanPath: string;
  lastScan: string;
  portRange: [number, number];
  tierThresholds: {
    powerfulMin: number;
    fastMax: number;
  };
}

/**
 * Server status for a running model instance
 */
export interface ServerStatus {
  modelId: string;
  displayName: string;
  port: number;
  pid: number;
  isReady: boolean;
  isRunning: boolean;
  uptimeSeconds: number;
  tier: ModelTier;
  isThinking: boolean;
}

/**
 * Complete server status response
 */
export interface ServerStatusResponse {
  totalServers: number;
  readyServers: number;
  servers: ServerStatus[];
}

/**
 * Model profile configuration
 */
export interface Profile {
  name: string;
  description?: string;
  enabledModels: string[];
  tierConfig: TierConfig[];
  twoStage: {
    enabled: boolean;
    stage1Tier: string;
    stage2Tier: string;
  };
  loadBalancing: {
    enabled: boolean;
    strategy: string;
  };
}

/**
 * Phase 2: Runtime settings update request
 * All fields are optional - only include fields to update
 */
export interface RuntimeSettingsUpdateRequest {
  nGpuLayers?: number | null;
  ctxSize?: number | null;
  nThreads?: number | null;
  batchSize?: number | null;
}

/**
 * Phase 2: Global runtime settings (defaults)
 */
export interface GlobalRuntimeSettings {
  nGpuLayers: number;
  ctxSize: number;
  nThreads: number;
  batchSize: number;
}

/**
 * Phase 2: Port update request
 */
export interface PortUpdateRequest {
  port: number;
}

/**
 * External server status item
 * Represents the health status of a single external Metal server
 */
export interface ExternalServerItem {
  port: number;
  status: 'online' | 'offline' | 'error';
  responseTimeMs: number | null;
  errorMessage: string | null;
}

/**
 * External server status response
 * Complete status information for all external Metal servers
 */
export interface ExternalServerStatusResponse {
  areReachable: boolean;
  useExternalServers: boolean;
  servers: ExternalServerItem[];
  message: string;
  checkedAt: string;
}
