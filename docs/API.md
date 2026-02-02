# API Reference

Full interactive docs: http://localhost:8000/docs

## Overview

The Synapse Engine API is organized into functional groups:

| Prefix | Purpose |
|--------|---------|
| `/api/query` | Query processing and orchestration |
| `/api/models` | Model registry and server management |
| `/api/cgrag` | CGRAG index management |
| `/api/settings` | Runtime configuration |
| `/api/context` | Context window allocation |
| `/api/proxy` | Model proxy endpoints |
| `/health` | Health checks |

---

## Query Processing

### POST `/api/query`

Process a query through the orchestration system.

**Request Body:**
```json
{
  "query": "Explain async patterns in Python",
  "mode": "two-stage",
  "use_context": true,
  "use_web_search": false,
  "max_tokens": 2048,
  "temperature": 0.7,
  "council_mode": "consensus",
  "council_max_turns": 10,
  "council_participants": ["model_a", "model_b"],
  "council_pro_model": "model_a",
  "council_con_model": "model_b",
  "council_moderator": false,
  "instance_id": "optional-instance-id"
}
```

**Query Modes:**
- `simple` - Single model, direct response
- `two-stage` - FAST tier + CGRAG → BALANCED/POWERFUL refinement
- `council` - Multi-model collaboration (requires `council_mode`)
- `benchmark` - Compare responses from all enabled models

**Council Modes:**
- `consensus` - 3 models collaborate toward agreement
- `adversarial` - 2 models debate, then synthesize

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "Explain async patterns in Python",
  "response": "...",
  "metadata": {
    "queryMode": "two-stage",
    "stage1Response": "...",
    "stage1ModelId": "qwen_7b_fast",
    "stage1Tier": "fast",
    "stage1ProcessingTime": 2100,
    "stage2ModelId": "deepseek_14b_balanced",
    "stage2Tier": "balanced",
    "stage2ProcessingTime": 4523,
    "cgragArtifacts": 3,
    "cgragArtifactsInfo": [
      {
        "filePath": "docs/async.md",
        "relevanceScore": 0.92,
        "chunkIndex": 5,
        "tokenCount": 450
      }
    ],
    "complexityScore": 0.65,
    "processingTimeMs": 6623,
    "tokensUsed": 1250,
    "cacheHit": false
  }
}
```

---

## Model Management

### GET `/api/models/registry`

Get full model registry with all discovered models.

**Response:**
```json
{
  "models": {
    "qwen_7b_fast": {
      "modelId": "qwen_7b_fast",
      "filePath": "/models/qwen-7b-q4_k_m.gguf",
      "displayName": "Qwen 7B Q4_K_M",
      "familyName": "qwen",
      "parameterSize": "7B",
      "quantization": "Q4_K_M",
      "assignedTier": "fast",
      "tierOverride": null,
      "enabled": true,
      "port": 8080,
      "thinkingOverride": false
    }
  },
  "portRange": [8080, 8099],
  "scanTimestamp": "2025-02-01T12:00:00Z",
  "tierThresholds": {
    "fast": 7,
    "balanced": 14
  }
}
```

### GET `/api/models/servers`

Get status of all running llama.cpp servers.

**Response:**
```json
{
  "totalServers": 3,
  "readyServers": 3,
  "servers": [
    {
      "modelId": "qwen_7b_fast",
      "displayName": "Qwen 7B Q4_K_M",
      "port": 8080,
      "isReady": true,
      "uptimeSeconds": 3600,
      "pid": 12345
    }
  ]
}
```

### POST `/api/models/servers/start-all`

Start all enabled models. Returns summary with timing.

### POST `/api/models/servers/stop-all`

Stop all running servers gracefully.

### POST `/api/models/servers/{model_id}/start`

Start a specific model server.

### POST `/api/models/servers/{model_id}/stop`

Stop a specific model server.

### POST `/api/models/rescan`

Re-scan HuggingFace cache for new/removed models. Preserves user overrides.

**Response:**
```json
{
  "message": "Re-scan completed successfully",
  "modelsFound": 12,
  "modelsAdded": 2,
  "modelsRemoved": 0,
  "timestamp": "2025-02-01T12:00:00Z"
}
```

### PUT `/api/models/{model_id}/enabled`

Enable or disable a model.

**Request:**
```json
{"enabled": true}
```

### PUT `/api/models/{model_id}/tier`

Override model tier assignment.

**Request:**
```json
{"tier": "balanced"}
```

Valid tiers: `fast`, `balanced`, `powerful`

### PUT `/api/models/{model_id}/thinking`

Enable thinking capability for a model. Auto-assigns POWERFUL tier if thinking=true.

**Request:**
```json
{"thinking": true}
```

### PUT `/api/models/{model_id}/port`

Assign a specific port to a model.

**Request:**
```json
{"port": 8085}
```

### PUT `/api/models/{model_id}/runtime-settings`

Override per-model runtime settings.

**Request:**
```json
{
  "n_gpu_layers": 99,
  "ctx_size": 8192,
  "n_threads": 8,
  "batch_size": 512
}
```

### PUT `/api/models/port-range`

Update the global port range for model servers.

**Request:**
```json
{"start": 8080, "end": 8099}
```

### GET `/api/models/tiers/{tier}`

Get all models in a specific tier.

---

## CGRAG (Contextual Retrieval)

### GET `/api/cgrag/status`

Get CGRAG index status.

**Response:**
```json
{
  "indexExists": true,
  "chunksIndexed": 1523,
  "indexSizeMb": 45.2,
  "lastIndexed": "docs",
  "isIndexing": false,
  "indexingProgress": 0,
  "indexingTotal": 0,
  "indexingCurrentFile": null,
  "indexingError": null,
  "supportedExtensions": [".md", ".txt", ".py", ".js", ".ts", ".json"]
}
```

### POST `/api/cgrag/index`

Start indexing a directory (runs in background).

**Request:**
```json
{
  "directory": "/app/docs",
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

### GET `/api/cgrag/directories`

List available directories for indexing with file counts.

---

## Settings

### GET `/api/settings`

Get current runtime settings.

### PUT `/api/settings`

Update runtime settings with validation.

**Request:**
```json
{
  "settings": {
    "n_gpu_layers": 99,
    "ctx_size": 8192,
    "n_threads": 8,
    "batch_size": 512,
    "embedding_model_name": "all-MiniLM-L6-v2"
  }
}
```

### POST `/api/settings/validate`

Validate settings without saving.

### POST `/api/settings/reset`

Reset to default settings.

### GET `/api/settings/export`

Export settings as JSON.

### POST `/api/settings/import`

Import settings from JSON.

### GET `/api/settings/schema`

Get JSON schema for settings (useful for dynamic UI generation).

### GET `/api/settings/vram-estimate`

Estimate VRAM usage for a model configuration.

**Query Parameters:**
- `model_size_b` - Model size in billions (default: 8.0)
- `quantization` - Quantization type (default: Q4_K_M)

---

## Context Allocation

### GET `/api/context/allocation/{query_id}`

Get detailed context window allocation for a query.

**Response:**
```json
{
  "queryId": "550e8400-e29b-41d4-a716-446655440000",
  "modelId": "deepseek-r1:8b",
  "contextWindowSize": 8192,
  "totalTokensUsed": 7200,
  "tokensRemaining": 992,
  "utilizationPercentage": 87.9,
  "components": [
    {
      "component": "system_prompt",
      "tokensUsed": 450,
      "tokensAllocated": 450,
      "percentage": 5.5,
      "contentPreview": "You are a helpful AI assistant..."
    },
    {
      "component": "cgrag_context",
      "tokensUsed": 6000,
      "tokensAllocated": 6000,
      "percentage": 73.2,
      "contentPreview": "# Documentation..."
    }
  ],
  "cgragArtifacts": [
    {
      "artifactId": "chunk_0",
      "sourceFile": "docs/architecture.md",
      "relevanceScore": 0.95,
      "tokenCount": 1500,
      "contentPreview": "# Architecture..."
    }
  ],
  "warning": "Context window >80% utilized - response may be truncated"
}
```

### GET `/api/context/stats`

Get aggregate context allocation statistics.

---

## Proxy Endpoints

Access models through the reverse proxy (OpenAI-compatible API).

### POST `/api/proxy/{model_id}/v1/chat/completions`

OpenAI-compatible chat completions API.

### POST `/api/proxy/{model_id}/v1/completions`

OpenAI-compatible completions API.

### GET `/api/proxy/{model_id}/health`

Health check for specific model.

---

## Health Checks

### GET `/health/healthz`

Liveness probe (fast, <50ms). Returns basic status.

### GET `/health/ready`

Readiness probe. Checks all dependencies:
- PRAXIS (backend)
- MEMEX (Redis)
- RECALL (FAISS index)
- NEURAL (model servers)

**Response:**
```json
{
  "status": "ok",
  "uptime": 3600.5,
  "components": {
    "praxis": "ready",
    "memex": "ready",
    "recall": "ready",
    "neural": "3_active"
  },
  "traceId": "abc123"
}
```

### GET `/health`

Legacy endpoint (same as `/health/healthz`).

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PRAXIS_MODEL_PATH` | HuggingFace cache path | - |
| `NEURAL_LLAMA_SERVER_PATH` | llama-server binary | `/usr/local/bin/llama-server` |
| `NEURAL_PORT_START` | First model port | `8080` |
| `NEURAL_PORT_END` | Last model port | `8099` |
| `RECALL_INDEX_PATH` | FAISS index location | `/data/faiss_indexes/` |
| `RECALL_CHUNK_SIZE` | Document chunk size | `512` |
| `RECALL_TOKEN_BUDGET` | Max context tokens | `8000` |
| `RECALL_MIN_RELEVANCE` | Minimum relevance | `0.7` |
| `PRAXIS_DEFAULT_MODE` | Default query mode | `two-stage` |
| `USE_EXTERNAL_SERVERS` | Use Metal acceleration | `false` |
| `REGISTRY_PATH` | Model registry file | `data/model_registry.json` |
| `SEARXNG_URL` | SearXNG instance URL | `http://searxng:8080` |
| `WEBSEARCH_MAX_RESULTS` | Max web search results | `5` |
| `WEBSEARCH_TIMEOUT` | Web search timeout (s) | `10` |

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable description",
  "details": {
    "field": "Additional context"
  }
}
```

Common HTTP status codes:
- `400` - Bad request (validation error)
- `404` - Resource not found
- `409` - Conflict (e.g., port already in use)
- `503` - Service unavailable (dependency not initialized)
- `504` - Gateway timeout (query processing timeout)
