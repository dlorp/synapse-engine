# API Reference

Full interactive docs: http://localhost:8000/docs

## Query Processing

### POST `/api/query`

```json
{
  "query": "Explain async patterns in Python",
  "mode": "two-stage",
  "use_context": true,
  "max_tokens": 2048
}
```

**Response:**
```json
{
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
    "cgragArtifacts": 3
  }
}
```

## Model Management

| Endpoint | Description |
|----------|-------------|
| `GET /api/models/registry` | All discovered models |
| `GET /api/models/servers` | Running server status |
| `POST /api/models/rescan` | Re-scan for new models |
| `PUT /api/models/{id}/enabled` | Enable/disable model |

## Server Control

| Endpoint | Description |
|----------|-------------|
| `POST /api/models/servers/start-all` | Start all enabled |
| `POST /api/models/servers/stop-all` | Stop all running |
| `POST /api/models/servers/{id}/start` | Start specific model |
| `POST /api/models/servers/{id}/stop` | Stop specific model |

## Proxy Endpoints

Access models through reverse proxy:

| Endpoint | Description |
|----------|-------------|
| `POST /api/proxy/{id}/v1/chat/completions` | Chat API |
| `POST /api/proxy/{id}/v1/completions` | Completions API |
| `GET /api/proxy/{id}/health` | Health check |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PRAXIS_MODEL_PATH` | HuggingFace cache path | — |
| `NEURAL_LLAMA_SERVER_PATH` | llama-server binary | `/usr/local/bin/llama-server` |
| `NEURAL_PORT_START` | First model port | `8080` |
| `NEURAL_PORT_END` | Last model port | `8099` |
| `RECALL_INDEX_PATH` | FAISS index location | `/data/faiss_indexes/` |
| `RECALL_CHUNK_SIZE` | Document chunk size | `512` |
| `RECALL_TOKEN_BUDGET` | Max context tokens | `8000` |
| `RECALL_MIN_RELEVANCE` | Minimum relevance | `0.7` |
| `PRAXIS_DEFAULT_MODE` | Default query mode | `two-stage` |
| `USE_EXTERNAL_SERVERS` | Use Metal acceleration | `false` |
