# S.Y.N.A.P.S.E. ENGINE - Project Overview

**Scalable Yoked Network for Adaptive Praxial System Emergence**
**Last Updated:** November 12, 2025
**Status:** Phase 4 & 6 Complete | Prod Ready v5.0 | Host API Operational

---

## Executive Summary

S.Y.N.A.P.S.E. ENGINE is a **distributed orchestration platform for local language models** that enables sophisticated orchestration of multiple quantized LLM models. The system implements Contextually Guided Retrieval Augmented Generation (CGRAG), integrated web search, and features a dense, terminal inspired UI with real-time visualizations.

### What Problem Does S.Y.N.A.P.S.E. ENGINE Solve?

S.Y.N.A.P.S.E. ENGINE addresses the challenge of effectively utilizing multiple local LLM instances by:
- **Intelligent Query Routing** - Automatically routes queries to appropriate model tiers based on complexity assessment
- **Dynamic Model Management** - Start/stop models on demand without Docker restarts (5-second startup)
- **Context Enhancement** - CGRAG retrieval provides relevant documentation context in <100ms
- **Multi-Stage Processing** - Two stage refinement improves response quality while maintaining speed
- **Metal Acceleration** - Native GPU support on Apple Silicon for 2-3x faster inference
- **Resource Optimization** - Smart allocation across Q2/Q3/Q4 quantizations based on query needs

### Core Value Proposition

Unlike traditional single model deployments, S.Y.N.A.P.S.E. ENGINE treats your local LLMs as a distributed computing resource, intelligently orchestrating them for optimal performance, quality, and resource utilization through a sophisticated WebUI control plane governed by the NEURAL SUBSTRATE ORCHESTRATOR.

---

## Project Status

### Current State (v5.0)
- ✅ **Production-Ready Infrastructure** - Docker Compose with health checks and monitoring
- ✅ **Full Model Management** - Auto discovery, dynamic enable/disable, real time health monitoring
- ✅ **CGRAG System** - FAISS based retrieval with token budget management (35+ docs indexed)
- ✅ **Query Processing** - Simple and Two Stage modes with complexity based routing
- ✅ **Council Modes** - Consensus and Debate modes for multi model collaboration
- ✅ **Benchmark Mode** - Side by side comparison across all enabled models
- ✅ **Host API** - Automatic Metal accelerated llama-server management on macOS
- ✅ **Terminal UI** - Dense information displays with 60fps animations
- ✅ **WebSocket Updates** - Real time model status and processing events
- ✅ **Dashboard Features** - Interactive pipeline visualization (React Flow), advanced metrics (Chart.js), system topology, context window allocation
- ✅ **Comprehensive Testing** - 24 automated tests across backend/frontend/integration

### What's Working
- Complete end to end query processing pipeline
- Model auto discovery from HuggingFace cache
- Dynamic model start/stop without Docker restart
- CGRAG retrieval with <100ms latency
- Two stage query refinement with complexity routing
- Council consensus and debate modes
- Real time logs and resource monitoring
- Metal GPU acceleration on Apple Silicon
- Interactive dashboard with React Flow pipeline graphs
- Advanced metrics visualization with Chart.js time-series
- System architecture topology with health monitoring
- Context window allocation display

### What's In Progress
- Code Chat mode with file editing capabilities
- WebSocket /ws/events endpoint for real-time event streaming
- Performance optimization for >100k document indexes
- Multi chat conversational mode

---

## Architecture Overview

### High-Level System Architecture

```
┌──────────────────────────────────────────────────┐
│        Browser (CORE:INTERFACE)                  │
│  ┌────────────────────────────────────────────┐  │
│  │  Terminal UI + Real time Visualizations    │  │
│  │  - Query Interface & Response Display      │  │
│  │  - Model Management Dashboard              │  │
│  │  - System Logs & Resource Monitoring       │  │
│  │  - Settings & Configuration                │  │
│  └────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────┘
                   │ WebSocket + HTTP/REST
                   ▼
┌──────────────────────────────────────────────────┐
│    CORE:PRAXIS (NEURAL SUBSTRATE ORCHESTRATOR)   │
│  ┌─────────┐  ┌─────────┐  ┌──────────────────┐ │
│  │  Query  │  │  CGRAG  │  │  Model Manager   │ │
│  │  Router │──│  Engine │──│  - Health Checks │ │
│  │         │  │ (FAISS) │  │  - Load Balance  │ │
│  └─────────┘  └─────────┘  └──────────────────┘ │
│                    │                             │
│                    ▼                             │
│           ┌─────────────────┐                    │
│           │  NODE:NEURAL    │                    │
│           │  (Metal GPU)    │                    │
│           └─────────────────┘                    │
└──────────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│            Model Server Infrastructure           │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   FAST   │  │ BALANCED │  │  POWERFUL    │  │
│  │ (2B-7B)  │  │ (8B-14B) │  │    (>14B)    │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│         llama-server instances (Metal)           │
└──────────────────────────────────────────────────┘
```

### Service Topology

| Canonical Service | Codename | Responsibility | Port | Health Endpoint |
|-------------------|----------|----------------|------|-----------------|
| `synapse_core` | CORE:PRAXIS | Orchestrator, query routing, NEURAL SUBSTRATE ORCHESTRATOR control | 8000 | `/health/healthz`, `/health/ready` |
| `synapse_frontend` | CORE:INTERFACE | React terminal UI, WebSocket events, visualization | 5173 | `/_ping` |
| `synapse_host_api` | NODE:NEURAL | Metal server process manager, GPU orchestration | 9090 | `/healthz`, `/ready` |
| `synapse_recall` | NODE:RECALL | CGRAG preprocessor, FAISS indexing, SearXNG proxy | 8080 | `/healthz` |
| `synapse_redis` | CORE:MEMEX | Cache, session store, token budgets | 6379 | Redis `PING` |

### Key Components

1. **Frontend (React + TypeScript)**
   - Terminal aesthetic UI with phosphor orange (#ff9500) color scheme
   - Real time WebSocket updates for live model status
   - Model management interface with auto-discovery
   - Query interface with mode selection
   - System monitoring dashboards

2. **Backend (FastAPI + Python)**
   - Async request handling with WebSocket support
   - Query complexity assessment and routing
   - Model lifecycle management
   - CGRAG retrieval pipeline
   - Redis caching layer
   - Profile based configuration

3. **Host API (Python)**
   - Native llama-server process management
   - Metal GPU acceleration on Apple Silicon
   - Health monitoring and auto recovery
   - Resource allocation and tracking

4. **Infrastructure**
   - Docker Compose orchestration
   - Redis for caching and session storage
   - SearXNG for privacy respecting web search
   - FAISS for vector similarity search
   - Profile based configuration system

---

## Technology Stack

### Backend Technologies
- **Python 3.11+** - Core backend language
- **FastAPI** - Async web framework with automatic API documentation
- **FAISS** - Facebook's vector similarity search library
- **sentence-transformers** - State of the art embedding models
- **Redis** - Caching and session storage
- **WebSockets** - Real time bidirectional communication
- **Pydantic** - Data validation and settings management
- **uvicorn** - ASGI server with hot reload

### Frontend Technologies
- **React 19** - Latest React with concurrent features
- **TypeScript** - Type safe JavaScript (strict mode)
- **Vite** - Lightning fast build tool with HMR
- **TanStack Query** - Powerful data synchronization
- **Chart.js** - Performance visualizations
- **React Flow** - Pipeline graph visualization (planned)
- **CSS Modules** - Scoped styling with terminal aesthetics

### Infrastructure Technologies
- **Docker & Docker Compose** - Container orchestration
- **llama.cpp** - High performance local LLM inference
- **nginx** - Reverse proxy and static file serving
- **SearXNG** - Privacy respecting metasearch engine
- **GitHub Actions** - CI/CD pipeline (planned)

### Model Technologies
- **DeepSeek R1 Qwen3 8B** - Primary model family
- **Q2/Q3/Q4 Quantization** - Different precision/speed trade-offs
- **GGUF Format** - Efficient model storage
- **Metal Framework** - Apple GPU acceleration

---

## Key Features

### Core Capabilities

#### 1. Dynamic Model Management
- **Auto-Discovery**: Scans HuggingFace cache for GGUF models
- **One-Click Enable**: Start models without Docker restart
- **Health Monitoring**: Real time health checks and status updates
- **Resource Tracking**: VRAM usage, query count, cache hit rates
- **Metal Acceleration**: Automatic GPU support on Apple Silicon

For implementation details, see [docs/features/DYNAMIC_CONTROL.md](./docs/features/DYNAMIC_CONTROL.md).

#### 2. Query Processing Modes

**✅ Simple Mode**
- Single FAST tier model for quick responses (<2s)
- Optional CGRAG context retrieval
- Best for straightforward queries

**✅ Two-Stage Mode**
- Stage 1: FAST tier with CGRAG (500 tokens)
- Complexity assessment determines Stage 2 tier
- Stage 2: BALANCED or POWERFUL refinement
- Balances speed and quality (<8-15s)

**✅ Council Mode (Consensus)**
- Multiple models collaborate to reach agreement
- Iterative refinement across 2-3 rounds
- Reduces bias through model diversity

**✅ Council Mode (Debate)**
- Models argue opposing viewpoints
- Structured debate with rebuttals
- Synthesis of different perspectives

**✅ Benchmark Mode**
- Side by side comparison across all models
- Performance metrics and timing data
- Quality assessment tools

For detailed mode documentation, see [docs/features/MODES.md](./docs/features/MODES.md) and [docs/features/BENCHMARK_MODE.md](./docs/features/BENCHMARK_MODE.md).

#### 3. CGRAG System
- **Sub-100ms Retrieval**: Lightning fast context retrieval
- **Token Budget Management**: Smart allocation within context windows
- **FAISS Indexing**: Efficient similarity search
- **Document Chunking**: Intelligent text segmentation
- **Cache Optimization**: 70%+ cache hit rate target

#### 4. Real-Time Monitoring
- **Live Logs**: Streaming server output
- **Resource Metrics**: CPU, memory, VRAM usage
- **Query Analytics**: Processing times, cache hits
- **Model Status**: Health, state, current operations
- **WebSocket Events**: Live updates to UI

#### 5. Terminal UI Design
- **Phosphor Orange Theme**: #ff9500 primary color
- **Dense Information Display**: Maximum data density
- **60fps Animations**: Smooth transitions and updates
- **Technical Aesthetic**: Inspired by NERV panels
- **Keyboard Navigation**: Terminal style shortcuts

#### 6. Dashboard Features (v5.0)
- **ProcessingPipelinePanel**: Interactive query flow visualization using React Flow with node-based graphs
- **ContextWindowPanel**: Real-time token allocation display showing CGRAG, query, and system prompt budgets
- **AdvancedMetricsPanel**: Time-series charts with Chart.js for query rates, tier performance, and resource utilization
- **SystemArchitectureDiagram**: Live system topology with health monitoring, interactive nodes, and query path visualization
- **WebSocket Event Streaming**: Real-time event feed with 8-event rolling window (in progress)

For dashboard implementation details, see [docs/implementation/phase4/](./docs/implementation/phase4/).

---

## Development Workflow

### Docker Only Development (MANDATORY)

⚠️ **CRITICAL: ALL development MUST be done in Docker containers**

See [docker-compose.yml](./docker-compose.yml) for service configuration.

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after changes
docker-compose build --no-cache frontend
docker-compose build --no-cache backend
docker-compose up -d

# Run tests
./scripts/test-all.sh
```

**Why Docker Only?**
- Ensures environment parity
- Prevents "works on my machine" issues
- Vite environment variables embedded at build time
- Consistent behavior across development and production

For detailed Docker infrastructure information, see [docs/architecture/DOCKER_INFRASTRUCTURE.md](./docs/architecture/DOCKER_INFRASTRUCTURE.md).

### Development Guidelines

1. **Check [SESSION_NOTES.md](./SESSION_NOTES.md)** before starting work
2. **Use specialized agents** for domain-specific tasks
3. **Update documentation** after significant changes
4. **Run tests** before committing ([`./scripts/test-all.sh`](./scripts/test-all.sh))
5. **Follow terminal aesthetic** - phosphor orange (#ff9500) theme
6. **Maintain 60fps** for all animations
7. **Use async/await** patterns in backend
8. **Type everything** in TypeScript (strict mode)

### Testing Strategy

Comprehensive test suite with 24 automated checks:
- **Backend Tests** (10): API endpoints, health checks, Python tests
- **Frontend Tests** (8): React app, Vite config, asset loading
- **Integration Tests** (6): Service communication, WebSockets

```bash
# Run all tests
./scripts/test-all.sh

# Individual suites
./scripts/test-backend.sh
./scripts/test-frontend.sh
./scripts/test-integration.sh
```

See [TEST_SUITE_SUMMARY.md](./docs/TEST_SUITE_SUMMARY.md) for detailed test documentation.

---

## Recent Progress

### Latest Sessions (November 12, 2025)

#### Phase 4 (Dashboard Features) Complete
- ProcessingPipelinePanel with React Flow visualization
- ContextWindowPanel with token allocation display
- AdvancedMetricsPanel with Chart.js time-series
- SystemArchitectureDiagram with interactive topology
- reactflow library integration (49 packages)
- WebSocket client implementation complete
- Codebase organization: 46 files moved to logical structure

### Phase Completions

#### Phase 6 Complete (November 3-4, 2025)
- Docker infrastructure finalized
- Profile system implementation
- Model registry with persistence
- Dynamic model control
- Host API for Metal acceleration
- Comprehensive test suite created

#### Phase 5 Complete (November 2-3, 2025)
- Security hardening (localhost binding)
- Admin panel implementation
- Model management UI
- Settings page with persistence
- Frontend timeout implementation

#### Earlier Phases
- **Phase 3**: CGRAG implementation, query routing, ASCII UI migration
- **Phase 2**: Model integration, health checks
- **Phase 1**: Infrastructure setup, terminal UI

---

## Next Steps

### Immediate Priorities
1. **WebSocket Event Stream** - Complete /ws/events endpoint for real-time dashboard updates
2. **Code Chat Mode** - Implement code Q&A with file editing capabilities
3. **Council Mode Refinement** - Polish consensus and debate implementations
4. **Performance Optimization** - Optimize for >100k document indexes

### Future Roadmap
- Multi-chat conversational mode
- Custom query mode parameters
- A/B testing capabilities
- Advanced caching strategies
- Distributed model orchestration
- Cloud deployment options

---

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- GGUF models in `~/.cache/huggingface/hub/`
- llama-server at `/usr/local/bin/llama-server`
- 8GB+ RAM recommended

### Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd SYNAPSE_ENGINE

# 2. Configure environment
cp .env.example .env
# Edit .env - set MODEL_SCAN_PATH

# 3. Start S.Y.N.A.P.S.E. ENGINE (5-second startup)
docker-compose up -d

# 4. Access WebUI
open http://localhost:5173
```

Configure environment variables using [.env.example](./.env.example) as a template.

For complete setup instructions, see [README.md](./README.md).

### Your First Query

1. Navigate to **Model Management**
2. Browse discovered models
3. Enable desired models
4. Click **START ALL ENABLED**
5. Go to **Home** → Select query mode
6. Submit a query and watch S.Y.N.A.P.S.E. ENGINE work!

### Useful Commands

```bash
# View logs
docker-compose logs -f synapse_core

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Run tests
./scripts/test-all.sh

# Stop everything
docker-compose down
```

**Test Scripts:**
- [test-all.sh](./scripts/test-all.sh) - Run complete test suite
- [test-backend.sh](./scripts/test-backend.sh) - Backend tests only
- [test-frontend.sh](./scripts/test-frontend.sh) - Frontend tests only
- [test-integration.sh](./scripts/test-integration.sh) - Integration tests only

---

## File Structure

```
SYNAPSE_ENGINE/
├── .claude/                    # Agent definitions
│   └── agents/                 # 12 specialized agents
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py            # Application entry
│   │   ├── core/              # Config, logging
│   │   ├── models/            # Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   └── cli/               # CLI tools
│   └── tests/                 # Backend tests
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── pages/             # Route pages
│   │   ├── hooks/             # Custom hooks
│   │   ├── types/             # TypeScript types
│   │   └── api/               # API client
│   └── tests/                 # Frontend tests
├── host-api/                   # Metal acceleration
│   └── main.py                # Process manager
├── config/                     # Configuration
│   ├── profiles/              # Environment profiles
│   └── redis.conf             # Redis config
├── docs/                       # Documentation
│   ├── architecture/          # System design
│   ├── development/           # Dev notes
│   ├── features/              # Feature docs
│   ├── guides/                # User guides
│   └── implementation/        # Implementation details
├── scripts/                    # Utility scripts
│   ├── test-all.sh            # Run all tests
│   ├── test-backend.sh        # Backend tests
│   ├── test-frontend.sh       # Frontend tests
│   └── test-integration.sh    # Integration tests
├── docker-compose.yml          # Docker orchestration
├── .env.example               # Environment template
├── README.md                  # Main documentation
├── CLAUDE.md                  # Claude instructions
└── SESSION_NOTES.md           # Development history
```

**Key Files:**
- [docker-compose.yml](./docker-compose.yml) - Service orchestration and configuration
- [.env.example](./.env.example) - Environment variable template
- [README.md](./README.md) - Comprehensive project documentation
- [CLAUDE.md](./CLAUDE.md) - Development instructions for Claude Code
- [SESSION_NOTES.md](./SESSION_NOTES.md) - Chronological development history
- [TEST_SUITE_SUMMARY.md](./docs/TEST_SUITE_SUMMARY.md) - Testing quick reference

### Key Directories

- **backend/app/services/** - Core business logic (models, routing, CGRAG)
- **frontend/src/components/** - React components (terminal UI, query, models)
- **frontend/src/pages/** - Application pages (Home, Models, Settings, Admin)
- **config/profiles/** - Environment configurations (dev, prod, test)
- **[docs/](./docs/)** - Comprehensive documentation ([index](./docs/README.md))
  - **[docs/architecture/](./docs/architecture/)** - System design and specifications
  - **[docs/development/](./docs/development/)** - Development session notes
  - **[docs/features/](./docs/features/)** - Feature documentation
  - **[docs/guides/](./docs/guides/)** - Quick reference guides
  - **[docs/implementation/](./docs/implementation/)** - Phase completion docs

---

## Summary

S.Y.N.A.P.S.E. ENGINE is a sophisticated, production ready platform for orchestrating multiple local LLM instances with intelligent routing, context enhancement, and a beautiful terminal inspired interface. The system is built with modern technologies, follows best practices, and is designed for both performance and maintainability.

**Key Achievements (v5.0):**
- ✅ Complete multi model orchestration with dynamic control via NEURAL SUBSTRATE ORCHESTRATOR
- ✅ Sub-100ms CGRAG retrieval with token budget management
- ✅ Multiple query modes including two stage refinement and council modes
- ✅ Metal GPU acceleration for Apple Silicon
- ✅ Dense terminal UI with real time updates
- ✅ Advanced dashboard with React Flow pipeline graphs and Chart.js metrics
- ✅ Interactive system topology visualization with health monitoring
- ✅ Context window allocation display with token budget tracking
- ✅ Comprehensive test coverage (24 automated tests)
- ✅ Production-ready Docker infrastructure with canonical service naming
- ✅ Standardized health checks and logging with service tags

**Current Focus:**
The project is actively being developed with a focus on completing real-time WebSocket event streaming, implementing Code Chat mode for file editing, and optimizing performance for large document sets (>100k documents).

---

## Additional Resources

### Quick Reference Guides
- [Docker Quick Reference](./docs/guides/DOCKER_QUICK_REFERENCE.md) - Docker command reference
- [Model Management Quick Start](./docs/guides/QUICK_START_MODEL_MANAGEMENT.md) - Model setup guide
- [Admin Quick Reference](./docs/guides/ADMIN_QUICK_REFERENCE.md) - Admin panel guide
- [Profile Quick Reference](./docs/guides/PROFILE_QUICK_REFERENCE.md) - Configuration profiles

### Architecture Documentation
- [docs/architecture/](./docs/architecture/) - System architecture and design
- [docs/architecture/DOCKER_INFRASTRUCTURE.md](./docs/architecture/DOCKER_INFRASTRUCTURE.md) - Docker setup details

### Development Resources
- [docs/development/](./docs/development/) - Session notes and troubleshooting
- [docs/TESTING_GUIDE.md](./docs/TESTING_GUIDE.md) - Comprehensive testing guide
- [SESSION_NOTES.md](./SESSION_NOTES.md) - Recent development history

### Feature Documentation
- [docs/features/](./docs/features/) - All feature documentation
- [docs/features/MODES.md](./docs/features/MODES.md) - Query mode details
- [docs/features/SETTINGS_PAGE.md](./docs/features/SETTINGS_PAGE.md) - Settings configuration

### Complete Documentation Index
See [docs/README.md](./docs/README.md) for a complete index of all documentation.

---
