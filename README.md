# Synapse Engine

[![License](https://img.shields.io/badge/license-PolyForm%20NC%201.0.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/dlorp/synapse-engine/ci.yml?label=CI)](https://github.com/dlorp/synapse-engine/actions)

Distributed orchestration platform for local language models.

---

![Synapse Engine in action](docs/features/synapseEngine.gif)
*Multiple LLMs collaborating in real-time - this is what AI orchestration looks like.*

---

## What is this?

Synapse Engine coordinates multiple local LLMs into a unified inference system. Instead of running models one at a time, it orchestrates them across performance tiers-fast models for initial processing, powerful models for refinement-with sub-100ms contextual retrieval built in.

It runs entirely on your hardware. No API keys, no cloud dependencies, no data leaving your machine.

## Features

- **Multi-model orchestration** across FAST/BALANCED/POWERFUL tiers
- **Query modes**: Simple, Two-Stage, Council (Consensus/Debate), Benchmark
- **CGRAG**: Sub-100ms contextual retrieval with FAISS
- **Metal acceleration** for Apple Silicon (2-3x faster inference)
- **WebUI-first design** - full control in the browser, no YAML wrangling
- **Dynamic model control** - start/stop models without Docker restarts

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- GGUF models in HuggingFace cache (`~/.cache/huggingface/hub/`)
- llama-server binary at `/usr/local/bin/llama-server`

### Installation

```bash
# Clone repository
git clone https://github.com/dlorp/synapse-engine.git
cd synapse-engine

# Configure environment
cp .env.example .env
# Edit .env - set PRAXIS_MODEL_PATH to your HuggingFace cache

# Start Synapse Engine
docker-compose up -d
```

Startup completes in ~5 seconds with no models loaded.

### Your First Query

1. Open WebUI at http://localhost:5173
2. Navigate to **Model Management** and enable models you want to use
3. Click **START ALL ENABLED**
4. Go to **Home**, select a query mode (Two-Stage recommended)
5. Submit a query and watch Synapse Engine process with CGRAG + multi-stage refinement

## Usage

### Query Modes

| Mode | Description |
|------|-------------|
| **Simple** | Single model, direct response |
| **Two-Stage** | FAST tier + CGRAG → BALANCED/POWERFUL refinement |
| **Council (Consensus)** | Multiple models collaborate to reach agreement |
| **Council (Debate)** | Models argue opposing viewpoints with synthesis |
| **Benchmark** | Compare responses across all enabled models |

### Metal Acceleration (Apple Silicon)

For 2-3x faster inference on Apple Silicon, enable Metal acceleration via the Host API. See the [Metal Acceleration Guide](https://github.com/dlorp/synapse-engine/wiki/guides/DOCKER_QUICKSTART#metal-acceleration) in the wiki.

### API Endpoints

- **WebUI**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## Documentation

Full documentation is available in the [Wiki](https://github.com/dlorp/synapse-engine/wiki):

- [Docker Quick Start](https://github.com/dlorp/synapse-engine/wiki/guides/DOCKER_QUICKSTART) - Installation and setup
- [Model Management](https://github.com/dlorp/synapse-engine/wiki/guides/QUICK_START_MODEL_MANAGEMENT) - Using the web interface
- [Query Modes](https://github.com/dlorp/synapse-engine/wiki/features/MODES) - Available processing modes
- [Troubleshooting](https://github.com/dlorp/synapse-engine/wiki/guides/TROUBLESHOOTING) - Common issues and solutions

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[PolyForm NonCommercial 1.0.0](LICENSE) - free for personal and non-commercial use
