# Architecture

## Three-Tier Model Management

### 1. Discovery (Automatic)
- Scans HuggingFace cache for GGUF models
- Extracts metadata: family, size, quantization
- Auto-assigns tier based on size

### 2. Configuration (WebUI)
- Enable/disable models via checkboxes
- Select query mode
- No YAML editing required

### 3. Activation (Dynamic)
- Click "START ALL" → servers launch
- No Docker restart needed
- Graceful shutdown when stopped

## Model Tiers

| Tier | Size | Use Case |
|------|------|----------|
| FAST | 2B-7B | Quick responses, Stage 1 |
| BALANCED | 8B-14B | Moderate complexity |
| POWERFUL | >14B | Complex queries, Stage 2 |

## Execution Environment

| Component | Location |
|-----------|----------|
| Orchestration | Docker (FastAPI) |
| llama-server | Host (bind-mounted) |
| Model files | Host (HuggingFace cache) |
| Model processes | Docker or Host (Metal) |

## Two-Stage Workflow

```
Query submitted
    ↓
STAGE 1: FAST tier (2B-7B)
    - CGRAG retrieves context (<100ms)
    - Fast model generates initial response
    - Completes in <3 seconds
    ↓
STAGE 2: BALANCED or POWERFUL
    - Selected based on query complexity
    - Receives Stage 1 + original query
    - Refines with depth and accuracy
    - Completes in <12 seconds
    ↓
Final response with metadata
```

## Service Communication

```
User → Frontend (5173)
         ↓
       Backend (8000)
         ↓
       Model Servers (8080-8099)
```

- Frontend → Backend: `http://backend:8000`
- Backend → Models: `localhost:8080-8099` or `host.docker.internal`
- User → Frontend: `http://localhost:5173`

## Dashboard Components

- **ProcessingPipelinePanel** - React Flow query visualization
- **ContextWindowPanel** - Token allocation display
- **AdvancedMetricsPanel** - Chart.js time series
- **SystemArchitectureDiagram** - Topology view

## Real-Time Features

- WebSocket event streaming
- Live server logs
- Resource tracking (VRAM, queries, cache)
- 60fps UI animations
