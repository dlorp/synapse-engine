# Synapse Engine

[![License](https://img.shields.io/badge/license-PolyForm%20NC%201.0.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/dlorp/synapse-engine/ci.yml?label=CI)](https://github.com/dlorp/synapse-engine/actions)

Distributed orchestration platform for local language models.

![Screenshot](docs/screenshot-query-modes.png)

## What is this?

Synapse Engine coordinates multiple local LLMs into a unified inference system. Instead of running models one at a time, it orchestrates them across performance tiers—fast models for initial processing, powerful models for refinement—with sub-100ms contextual retrieval built in.

It runs entirely on your hardware. No API keys, no cloud dependencies, no data leaving your machine.

## Features

- **Multi-Model Orchestration** — Coordinate models across FAST/BALANCED/POWERFUL tiers
- **Query Modes** — Simple, Two-Stage, Council (Consensus/Debate), Benchmark
- **CGRAG** — Sub-100ms contextual retrieval with FAISS
- **Metal Acceleration** — Apple Silicon GPU support via Host API
- **WebUI-First** — Full control in browser, no config files to edit

## Quick Start

### Prerequisites

- Docker Desktop
- GGUF models in `~/.cache/huggingface/hub/`
- llama-server at `/usr/local/bin/llama-server`

### Install and Run

```bash
git clone https://github.com/dlorp/synapse-engine.git
cd synapse-engine

cp .env.example .env
# Edit .env - set PRAXIS_MODEL_PATH to your models directory

docker-compose up -d
```

Ready in ~5 seconds. No models loaded by default.

### First Query

1. Open http://localhost:5173
2. Go to **Model Management** → enable models → **START ALL ENABLED**
3. Select query mode (Two-Stage recommended)
4. Submit query

## Query Modes

- **Simple** — Single model, direct response
- **Two-Stage** — FAST tier + CGRAG retrieval → BALANCED/POWERFUL refinement
- **Council (Consensus)** — Multiple models collaborate toward agreement
- **Council (Debate)** — Models argue positions, then synthesize
- **Benchmark** — Compare responses from all enabled models

## Usage

### API Examples

```bash
# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain async patterns", "mode": "two-stage", "use_context": true}'

# Start all models
curl -X POST http://localhost:8000/api/models/servers/start-all

# Stop all models
curl -X POST http://localhost:8000/api/models/servers/stop-all
```

Full API documentation: http://localhost:8000/docs (when running)

### Metal Acceleration (Apple Silicon)

Get 2-3x faster inference with automatic Metal GPU support:

```bash
brew install llama.cpp
# Configure SSH (see docs/METAL.md)
```

Then click "START ALL ENABLED" in WebUI—Host API handles the rest.

## Configuration

Key environment variables in `.env`:

```bash
PRAXIS_MODEL_PATH=/Users/you/.cache/huggingface/hub/
NEURAL_LLAMA_SERVER_PATH=/usr/local/bin/llama-server
RECALL_TOKEN_BUDGET=8000
PRAXIS_DEFAULT_MODE=two-stage
USE_EXTERNAL_SERVERS=true  # Enable Metal acceleration
```

## Performance

| Operation | Time |
|-----------|------|
| Docker startup | < 5 seconds |
| Model startup (Metal) | 3-5 seconds |
| Model startup (CPU) | 10-15 seconds |
| Simple query | < 2 seconds |
| Two-stage query | < 15 seconds |
| CGRAG retrieval | < 100ms |

## Documentation

- [Metal Acceleration](docs/METAL.md) — Apple Silicon GPU setup
- [Architecture](docs/ARCHITECTURE.md) — System design and model tiers
- [CGRAG](docs/CGRAG.md) — Document indexing and retrieval
- [Security](docs/SECURITY.md) — Localhost binding, reverse proxy setup
- [API Reference](docs/API.md) — Complete endpoint documentation

## Contributing

Contributions are welcome. Please open an issue to discuss changes before submitting a PR.

## License

[PolyForm NonCommercial 1.0.0](LICENSE)
