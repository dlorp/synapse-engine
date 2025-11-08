/**
 * Runtime settings configuration types
 *
 * These types match the backend RuntimeSettings schema with camelCase fields.
 * Settings are persisted to data/runtime_settings.json and can be modified via WebUI.
 */

/**
 * Runtime settings configuration
 * Matches backend RuntimeSettings schema with camelCase fields
 */
export interface RuntimeSettings {
  // GPU/VRAM Configuration
  n_gpu_layers: number;
  ctx_size: number;
  threads: number;
  batch_size: number;
  ubatch_size: number;
  flash_attn: boolean;
  no_mmap: boolean;

  // HuggingFace/Embeddings Configuration
  embedding_model_name: string;
  embedding_model_cache_path: string | null;
  embedding_dimension: number;

  // CGRAG Configuration
  cgrag_token_budget: number;
  cgrag_min_relevance: number;
  cgrag_chunk_size: number;
  cgrag_chunk_overlap: number;
  cgrag_max_results: number;
  cgrag_index_directory: string;

  // Benchmark Mode Defaults
  benchmark_default_max_tokens: number;
  benchmark_parallel_max_models: number;

  // Web Search Configuration
  websearch_max_results: number;
  websearch_timeout_seconds: number;
}

/**
 * File metadata for settings persistence
 */
export interface SettingsMetadata {
  exists: boolean;
  path: string;
  size_bytes: number;
  last_modified: string; // ISO 8601 timestamp
}

/**
 * Complete settings API response
 * Returned by GET/PUT/POST endpoints
 */
export interface SettingsResponse {
  success: boolean;
  settings: RuntimeSettings;
  restart_required: boolean;
  validation_errors: string[];
  message: string;
  metadata: SettingsMetadata;
}

/**
 * VRAM estimation request parameters
 */
export interface VRAMEstimateParams {
  model_size_b: number;      // Model size in billions (e.g., 8.0)
  quantization: string;       // e.g., "Q4_K_M", "Q2_K", "Q8_0"
}

/**
 * VRAM estimation response
 */
export interface VRAMEstimateResponse {
  success: boolean;
  vram_gb: number;
  model_size_b: number;
  quantization: string;
  settings: {
    n_gpu_layers: number;
    ctx_size: number;
  };
  message: string;
}

/**
 * JSON Schema response for settings validation
 * Using Record for flexible schema structure following JSON Schema spec
 */
export interface SettingsSchemaResponse {
  success: boolean;
  schema: Record<string, any>; // JSON Schema structure
  message: string;
}

/**
 * Settings export response
 */
export interface SettingsExportResponse {
  success: boolean;
  json_data: string; // JSON string of settings
  message: string;
}

/**
 * Settings import request
 */
export interface SettingsImportRequest {
  json_data: string; // JSON string to import
}

/**
 * Common context size presets (in tokens)
 */
export const CTX_SIZE_PRESETS = [
  512,
  1024,
  2048,
  4096,
  8192,
  16384,
  32768,
  65536,
  131072
] as const;

export type CtxSizePreset = typeof CTX_SIZE_PRESETS[number];

/**
 * Popular embedding models
 */
export const EMBEDDING_MODELS = [
  'all-MiniLM-L6-v2',
  'all-mpnet-base-v2',
  'all-MiniLM-L12-v2',
  'paraphrase-multilingual-MiniLM-L12-v2',
] as const;

export type EmbeddingModel = typeof EMBEDDING_MODELS[number];

/**
 * Common quantization types
 */
export const QUANTIZATION_TYPES = [
  'Q2_K',
  'Q3_K_S',
  'Q3_K_M',
  'Q3_K_L',
  'Q4_K_S',
  'Q4_K_M',
  'Q5_K_S',
  'Q5_K_M',
  'Q6_K',
  'Q8_0',
  'F16',
  'F32'
] as const;

export type QuantizationType = typeof QUANTIZATION_TYPES[number];
