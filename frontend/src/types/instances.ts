/**
 * Instance management types for multi-instance model support.
 * Fields match backend Pydantic model aliases (camelCase).
 */

/**
 * Runtime status of a model instance
 */
export type InstanceStatus = 'stopped' | 'starting' | 'active' | 'stopping' | 'error';

/**
 * Configuration for a single model instance
 * Represents a running or configured instance of a base model
 */
export interface InstanceConfig {
  instanceId: string;        // Format: "model_id:NN" (e.g., "qwen3_4p0b:01")
  modelId: string;           // Reference to base DiscoveredModel
  instanceNumber: number;    // Instance number (1-99)
  displayName: string;       // User-friendly name
  systemPrompt?: string;     // System prompt injected at query time (max 4096 chars)
  webSearchEnabled: boolean; // Enable SearXNG web search for this instance
  port: number;              // Assigned port (8100-8199 range)
  status: InstanceStatus;    // Current runtime status
  createdAt: string;         // ISO timestamp
  updatedAt?: string;        // ISO timestamp of last update
}

/**
 * Request to create a new model instance
 */
export interface CreateInstanceRequest {
  modelId: string;
  displayName: string;
  systemPrompt?: string;
  webSearchEnabled: boolean;
}

/**
 * Request to update an existing instance
 * All fields are optional - only include fields to update
 */
export interface UpdateInstanceRequest {
  displayName?: string;
  systemPrompt?: string;
  webSearchEnabled?: boolean;
}

/**
 * Response containing list of instances
 */
export interface InstanceListResponse {
  instances: InstanceConfig[];
  total: number;
  byModel: Record<string, number>; // Count of instances per model_id
}

/**
 * Response containing single instance with model info
 */
export interface InstanceResponse {
  instance: InstanceConfig;
  modelDisplayName: string;
  modelTier: string;
}

/**
 * Detailed status of an instance including server info
 */
export interface InstanceStatusResponse {
  instance: InstanceConfig;
  serverRunning: boolean;
  serverPid?: number;
  serverUptime?: number;
  lastHealthCheck?: string;
}

/**
 * Predefined system prompt template
 */
export interface SystemPromptPreset {
  id: string;
  name: string;
  prompt: string;
  description: string;
  category: string;
}

/**
 * Response containing available system prompt presets
 */
export interface SystemPromptPresetsResponse {
  presets: SystemPromptPreset[];
}

/**
 * Instance grouped by base model for UI display
 */
export interface InstanceGroup {
  modelId: string;
  modelDisplayName: string;
  modelTier: string;
  instances: InstanceConfig[];
}

/**
 * Bulk operation response (start-all, stop-all)
 */
export interface BulkOperationResponse {
  success: boolean;
  started?: number;
  stopped?: number;
  failed?: number;
  errors?: string[];
}
