
# S.Y.N.A.P.S.E. ENGINE 


![til](docs/features/synapseEngine.gif)

**Scalable Yoked Network for Adaptive Praxial System Emergence**

> Interlinked cognition — thought in motion.

**Status:** v5.1 Prod Ready ✅ | TUI Navigation ✅ | Metal Acceleration ✅ | CGRAG Operational ✅

> **New to S.Y.N.A.P.S.E. ENGINE?** Start with [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for a high-level understanding of the project, team structure, and development context.

## Overview

S.Y.N.A.P.S.E. ENGINE is a distributed orchestration platform for local language models. It coordinates multiple quantized models across performance tiers (FAST/BALANCED/POWERFUL), performs sub 100ms contextual retrieval (CGRAG), and runs multi stage refinement, consensus, and debate workflows.

All runtime messages traverse the **NEURAL SUBSTRATE ORCHESTRATOR** — the message bus and governance layer that enforces routing, health checks, and contextual budgeting.

### Key Features

🎨 **WebUI-First** - All control happens in the browser, no YAML editing
⚡ **Fast Startup** - Launches in ~5 seconds with no models loaded (default: NO models enabled)
🔄 **Dynamic Control** - Start/stop models without Docker restart
🚀 **One-Click Metal Servers** - Automatic Metal accelerated llama-server management via Host API
🎯 **Multiple Modes** - Two Stage, Simple, Council (Consensus/Debate), Benchmark, Code Chat (planned)
📚 **CGRAG Integration** - Automatic context retrieval with FAISS (<100ms)
📊 **Real-Time Monitoring** - Live server logs, resource tracking (VRAM, queries, cache hit rate)
🔍 **Auto-Discovery** - Finds GGUF models in your Hugging Face cache
🖼️ **Advanced Visualizations** - Interactive processing pipelines (ProcessingPipelinePanel with React Flow), time-series metrics (AdvancedMetricsPanel with Chart.js), system topology diagrams (SystemArchitectureDiagram)
🎛️ **Dashboard Features** - Context window allocation display (ContextWindowPanel), advanced metrics panels, real-time event streaming (WebSocket)

### What's New in v5.1

**TUI Navigation Overhaul:**
- ✅ **Bottom Navigation Bar** - NERV-style double-border navigation replacing sidebar
- ✅ **Keyboard Navigation** - Press 1-5 to navigate between pages instantly
- ✅ **Glyph Icons** - Terminal-aesthetic icons (⌘ ◧ ◈ ⚙ ◎) for each section
- ✅ **Phosphor Orange Breathing** - Animated border with 2s breathing cycle
- ✅ **Real-Time Status** - Models, uptime, and query count in navigation bar

**Phase 4 Dashboard Features - Complete:**
- ✅ **ProcessingPipelinePanel** - Interactive React Flow visualization of query processing stages
- ✅ **ContextWindowPanel** - Live token allocation display showing context budget distribution
- ✅ **AdvancedMetricsPanel** - Chart.js time-series metrics with historical performance tracking
- ✅ **SystemArchitectureDiagram** - Interactive system topology with component relationships
- ✅ **Enhanced Real-Time Monitoring** - WebSocket event streaming for live updates across all dashboard components

**Phase 5 Security Enhancements:**
- ✅ Localhost-only model server binding (not exposed to host network)
- ✅ Reverse proxy access through FastAPI backend
- ✅ Centralized authentication foundation

### Available Query Modes

- ✅ **Simple** - Single model query (direct model invocation)
- ✅ **Two-Stage** - FAST tier + CGRAG → BALANCED/POWERFUL refinement (complexity-based)
- ✅ **Council (Consensus)** - Multiple models collaborate to reach consensus
- ✅ **Council (Debate)** - Models argue opposing viewpoints with synthesis
- ✅ **Benchmark** - Compare responses across all enabled models side by side
- 🚧 **Code Chat** - Code Q&A + File Create/Edit with CGRAG (In Development)

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- GGUF models in HuggingFace cache (`~/.cache/huggingface/hub/`)
- llama-server binary at `/usr/local/bin/llama-server`
- (Optional) Documentation to index for CGRAG

### Installation

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd SYNAPSE_ENGINE
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env - set PRAXIS_MODEL_PATH to your HuggingFace cache
   ```

   See [.env.example](./.env.example) for all available configuration options.

3. **Start S.Y.N.A.P.S.E. ENGINE**
   ```bash
   docker-compose up -d
   ```

   **Startup completes in ~5 seconds** - no models are enabled or loaded by default! You choose which models to enable via the WebUI.

4. **Access WebUI**
   - INTERFACE: http://localhost:5173
   - PRAXIS API: http://localhost:8000/docs

### Your First Query

1. **Open WebUI:** http://localhost:5173

2. **Navigate to Model Management**
   - Browse discovered models (automatically scanned from your Hugging Face cache)
   - Enable models you want to use (each launches its own llama-server instance)
   - Watch real-time logs in the System Logs panel as servers start

3. **Click "START ALL ENABLED"**
   - Wait for models to load (3-5s per model with Metal acceleration, 10-15s with CPU)
   - Each enabled model launches its own llama-server instance

4. **Go to Home** → Select query mode (Two Stage recommended)

5. **Submit a query** → Watch S.Y.N.A.P.S.E. ENGINE process with CGRAG + multi-stage refinement!

6. **Monitor Resources**
   - View VRAM usage across all models
   - Track query count and cache hit rate
   - Observe real time processing metrics

## Metal Acceleration (Apple Silicon) 🚀

**Get 2-3x faster inference on Apple Silicon Macs with automatic Metal GPU acceleration via the Host API.**

### What is Metal Acceleration?

By default, S.Y.N.A.P.S.E. ENGINE runs llama-server inside Docker containers, which can't access your Mac's Metal GPU framework. **Metal acceleration mode** runs llama-server processes natively on your macOS host with full GPU access.

**NEW in v4.0:** The **Host API service** automatically manages Metal accelerated llama-servers for you. No more manual terminal windows!

**Performance Comparison:**
- CPU-only (Docker): ~15-30 seconds per model startup, slower inference
- Metal GPU (Host API): ~3-5 seconds per model startup, 2-3x faster inference

### Automatic Metal Server Management (v4.0)

**One Click Startup** - The Host API service automatically launches Metal accelerated llama-servers when you click "START ALL ENABLED" in the WebUI.

**How It Works:**
1. Host API service runs in Docker with SSH access to your Mac
2. When you enable models and click "START ALL ENABLED":
   - Backend calls Host API: `POST /api/servers/start`
   - Host API executes [start-host-llama-servers.sh](./scripts/start-host-llama-servers.sh) via SSH
   - Script reads `model_registry.json` and launches enabled models
   - Each model launches as a native Metal accelerated llama-server process
3. Backend connects to running servers via `host.docker.internal:<port>`
4. When you stop models or shutdown Docker:
   - Host API automatically stops all Metal servers
   - Clean shutdown with graceful signal handling

**Setup Steps:**

**1. Install Prerequisites**
```bash
# Install llama.cpp with Metal support
brew install llama.cpp

# Verify Metal support
llama-server --version
```

**2. Configure SSH for Host API**
```bash
# Generate SSH key for Docker → Host communication
ssh-keygen -t ed25519 -f ~/.ssh/magi_host_api -N ""

# Add to authorized_keys with command restriction
echo "command=\"/opt/homebrew/bin/bash /Users/$USER/Documents/Programming/SYNAPSE_ENGINE/scripts/ssh-wrapper.sh\" $(cat ~/.ssh/synapse_host_api.pub)" >> ~/.ssh/authorized_keys

# Copy SSH config to host-api directory
mkdir -p host-api/.ssh
cp ~/.ssh/magi_host_api host-api/.ssh/id_ed25519
cp ~/.ssh/magi_host_api.pub host-api/.ssh/id_ed25519.pub

# Create SSH config
cat > host-api/.ssh/config <<EOF
Host mac-host
    HostName host.docker.internal
    User $USER
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
```

**3. Verify Configuration**

Edit [docker-compose.yml](./docker-compose.yml) to ensure Host API is enabled (should be enabled by default):

```yaml
services:
  synapse_host_api:
    build: ./host-api
    container_name: synapse_host_api
    environment:
      - USE_EXTERNAL_SERVERS=true
      - NEURAL_ORCH_URL=http://synapse_host_api:9090
```

**4. Start S.Y.N.A.P.S.E. ENGINE**
```bash
docker-compose up -d
```

**5. Enable Models in WebUI**
- Navigate to **Model Management**
- Check boxes next to models you want to enable
- Click **"START ALL ENABLED"**
- Watch **System Logs** panel for real time startup progress
- Models launch with Metal GPU acceleration automatically!

**That's it!** No manual llama-server commands needed.

### Architecture with Host API

**Metal Acceleration Architecture (v4.0):**

```
┌───────────────────────────────────────────────────────────┐
│ macOS Host (Apple Silicon)                                 │
│                                                            │
│  ┌────────────────────────────────────────────────┐      │
│  │ llama-server (Native Metal) - Port 8080        │      │
│  │ llama-server (Native Metal) - Port 8081        │      │
│  │ llama-server (Native Metal) - Port 8082        │      │
│  │ GPU: Apple M4 Pro (Metal) - 2-3x Performance   │      │
│  └────────────────────────────────────────────────┘      │
│                    ▲                                       │
│                    │ SSH (command restricted)              │
│  ┌─────────────────┼────────────────────────────┐         │
│  │ Docker Services │                             │         │
│  │                                                │         │
│  │  ┌─────────────┴──────────────────────┐      │         │
│  │  │ Host API (Port 9090)                │      │         │
│  │  │ - Executes start-host-llama...sh     │      │         │
│  │  │ - Executes stop-host-llama...sh      │      │         │
│  │  │ - Graceful shutdown on SIGTERM       │      │         │
│  │  └─────────────┬──────────────────────┘      │         │
│  │                │ HTTP                          │         │
│  │  ┌─────────────┴──────────────────────┐      │         │
│  │  │ Backend (Port 8000)                 │      │         │
│  │  │ - Model Management                   │      │         │
│  │  │ - Query Routing                      │      │         │
│  │  │ - CGRAG Integration                  │      │         │
│  │  │ - Connects to host.docker.internal   │      │         │
│  │  └────────────────────────────────────┘      │         │
│  │                                                │         │
│  │  ┌────────────────────────────────────┐      │         │
│  │  │ Frontend (Port 5173)                │      │         │
│  │  │ - Model Management UI                │      │         │
│  │  │ - System Logs (Real-Time)           │      │         │
│  │  │ - Resource Monitoring                │      │         │
│  │  └────────────────────────────────────┘      │         │
│  └──────────────────────────────────────────────┘         │
└───────────────────────────────────────────────────────────┘
```

**What Happens When You Click "START ALL ENABLED":**

1. **WebUI → Backend:** `POST /api/models/servers/start-all`
2. **Backend → Host API:** `POST /api/servers/start`
3. **Host API → macOS Host:** SSH executes [start-host-llama-servers.sh](./scripts/start-host-llama-servers.sh)
4. **Script Actions:**
   - Reads `model_registry.json` to find enabled models
   - Converts Docker paths to host paths
   - Launches llama-server with Metal acceleration for each model
   - Waits for health checks
5. **Backend:** Connects to running servers via `host.docker.internal:<port>`
6. **WebUI:** Displays live logs showing startup progress

**What Happens on Shutdown (`docker-compose down`):**

1. Docker sends **SIGTERM** to Host API container
2. Host API shutdown handler executes: SSH calls [stop-host-llama-servers.sh](./scripts/stop-host-llama-servers.sh)
3. Script gracefully stops all Metal llama-server processes
4. Containers exit cleanly

**Security Model:**

- SSH uses Ed25519 key only authentication (no password)
- `authorized_keys` restricts SSH to only execute [ssh-wrapper.sh](./scripts/ssh-wrapper.sh)
- [ssh-wrapper.sh](./scripts/ssh-wrapper.sh) only allows two commands: `start-metal-servers`, `stop-metal-servers`
- Any other command is rejected
- Result: Secure, automated server management without exposing shell access

### Advantages & Considerations

**Advantages:**
- ✅ 2-3x faster inference (Metal GPU vs CPU)
- ✅ **Automatic server management** via Host API (no manual commands!)
- ✅ One click startup from WebUI
- ✅ Graceful shutdown when Docker stops
- ✅ Full access to unified memory architecture
- ✅ BF16 precision support on modern Apple GPUs
- ✅ Real time logs in WebUI

**Considerations:**
- macOS/Apple Silicon only (not portable to Linux)
- Requires SSH configuration (one time setup)
- Ports managed via model registry

**When to Use:**
- ✅ You're developing on an Apple Silicon Mac
- ✅ You want maximum inference performance
- ✅ You want automated server management
- ✅ You value real time monitoring

**Alternative (CPU-Only Mode):**
- Set `USE_EXTERNAL_SERVERS=false` in [docker-compose.yml](./docker-compose.yml)
- Models run inside Docker containers (slower, but fully portable)

### Multiple Metal Servers

The Host API automatically launches multiple models simultaneously when you enable them:

**In WebUI:**
1. Go to **Model Management**
2. Enable multiple models (check boxes)
3. Click **"START ALL ENABLED"**
4. Host API launches all models concurrently with Metal acceleration

**Model Registry (auto-managed):**
```json
{
  "models": {
    "qwen3_4p0b_q4km_fast": {"port": 8080, "enabled": true},
    "deepseek_8p0b_q4km_balanced": {"port": 8081, "enabled": true},
    "qwen_14p0b_q4km_powerful": {"port": 8082, "enabled": true}
  }
}
```

**System Logs** show startup progress in real time!

### Troubleshooting

**Backend shows "External server not running" error:**
```bash
# Verify llama-server is actually running
lsof -i :9090

# Check health endpoint directly
curl http://localhost:9090/health
# Expected: {"status":"ok"}
```

**Backend tries to launch subprocess instead of connecting:**
```bash
# Verify environment variable is set
docker exec synapse_core env | grep USE_EXTERNAL_SERVERS
# Expected: USE_EXTERNAL_SERVERS=true

# Check backend logs for debug output
docker-compose logs synapse_core | grep "prx: DEBUG: USE_EXTERNAL_SERVERS"
# Expected: use_external_servers flag = True
```

**Model loads but inference is slow:**
```bash
# Verify Metal GPU is actually being used
# Check llama-server startup logs for:
ggml_metal_library_init: loaded in X.XXX sec
ggml_metal_device_init: GPU name: Apple M4 Pro
```

**Port conflicts (8080-8099 range):**
```bash
# Use ports outside Docker's default range
llama-server --port 9090  # ✅ Works
llama-server --port 8080  # ❌ Conflicts with Docker
```

### Switching Between Modes

**Enable Metal Acceleration:**

Edit [docker-compose.yml](./docker-compose.yml):
```yaml
environment:
  - USE_EXTERNAL_SERVERS=true
```
```bash
docker-compose up -d backend
```

**Disable Metal Acceleration (CPU-only):**

Edit [docker-compose.yml](./docker-compose.yml):
```yaml
environment:
  - USE_EXTERNAL_SERVERS=false
```
```bash
docker-compose up -d backend
```

No code changes required - just toggle the environment variable!

## How It Works

### Blank Canvas Startup

```
Docker starts → S.Y.N.A.P.S.E. ENGINE discovers models → Registry saved → Ready in ~5s
(No models loaded, no llama-server processes running)
```

### Dynamic Model Control

```
User visits Model Management → Checks "Enable" on models → Clicks "START ALL"
  ↓
Servers launch dynamically (user sees progress)
  ↓
Models ready for queries (can stop/restart anytime)
```

### Two Stage Workflow (Corrected)

```
User selects Two Stage mode → Submits query
  ↓
STAGE 1: FAST tier (2B-7B models)
  - CGRAG retrieves relevant documentation (<100ms)
  - Fast model generates initial response (500 tokens)
  - Uses smaller model to allow more CGRAG context allocation
  - Completes in <3 seconds
  ↓
STAGE 2: BALANCED (8B-14B) or POWERFUL (>14B) tier
  - Selection based on query complexity assessment
  - Receives Stage 1 response + original query
  - Refines with depth, accuracy, and expanded reasoning
  - Completes in <12 seconds
  ↓
Final refined response with metadata (both stages visible in UI)
```

**Why FAST → BALANCED/POWERFUL?**
- FAST tier (Stage 1) allows more CGRAG context in token budget
- Stage 2 tier adapts to query complexity
- Total latency remains <15 seconds with better quality

## Architecture

### Three-Layer Model Management

**1. DISCOVERY (Automatic)**
- Scans HuggingFace cache for GGUF models
- Parses filenames (handles multiple naming conventions)
- Extracts metadata: family, size, quantization, capabilities
- Auto assigns tier:
  - **FAST** - 2B-7B models for quick responses
  - **BALANCED** - 8B-14B models for moderate complexity
  - **POWERFUL** - >14B models or thinking enabled models for complex queries
- Saves to `model_registry.json`

**2. CONFIGURATION (WebUI Driven)**
- User enables specific models via checkboxes
- User selects query mode
- User configures tier overrides (optional)
- No YAML editing required

**3. ACTIVATION (Dynamic)**
- User clicks "START ALL" → servers launch
- User clicks checkboxes → individual servers start/stop
- No Docker restart required
- Graceful shutdown when stopped

### Model Execution Environment

**Where do models actually run?**

S.Y.N.A.P.S.E. ENGINE uses a **hybrid Docker + host resources** approach:

| Component | Location | Why |
|-----------|----------|-----|
| **Orchestration** | Docker container (`backend`) | FastAPI, routing, CGRAG, WebUI |
| **llama-server binary** | Host machine (bind-mounted) | `/usr/local/bin/llama-server` |
| **Model files (.gguf)** | Host machine (bind-mounted) | HuggingFace cache directory |
| **Model processes** | Docker container | Spawned by backend, exposed on ports 8080-8099 |
| **GPU/CPU resources** | Host machine | llama-server uses your actual hardware |

**What this means:**
- ✅ Docker orchestrates everything (no local dev servers needed)
- ✅ Models use your bare metal GPU/CPU (full performance)
- ✅ No model files copied into containers (saves space)
- ✅ Updates to llama-server binary immediately available
- ✅ Easy to add/remove models (just update HuggingFace cache)

**Docker service communication:**
- Frontend → Backend: Uses service name `http://backend:8000` (NOT `localhost`)
- Backend → Models: Uses `localhost:8080-8099` (same container)
- User → Frontend: Uses `http://localhost:5173` (exposed port)

### CGRAG System

**Already Prod Ready (2,351 lines of code)**

- Document indexing with smart chunking (512 words, 50 word overlap)
- Batched embedding generation (sentence-transformers)
- FAISS vector search (<100ms retrieval)
- Token budget management (8000 token default)
- Relevance filtering (70% threshold)
- Supported formats: .md, .py, .txt, .yaml, .json, .rst

## API Reference

### Dynamic Model Control

**POST `/api/models/servers/{model_id}/start`**
Start a specific model server (no restart required)

**POST `/api/models/servers/{model_id}/stop`**
Stop a specific model server (no restart required)

**POST `/api/models/servers/start-all`**
Start all enabled models

**POST `/api/models/servers/stop-all`**
Stop all running servers

### Query Processing

**POST `/api/query`**

```json
{
  "query": "Explain async patterns in Python",
  "mode": "two-stage",
  "use_context": true,
  "max_tokens": 2048
}
```

Response includes two-stage metadata:

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

### Model Management

**GET `/api/models/registry`** - All discovered models
**GET `/api/models/servers`** - Running server status
**POST `/api/models/rescan`** - Re scan for new models
**PUT `/api/models/{model_id}/enabled`** - Enable/disable (auto-starts/stops server)

Full API docs: http://localhost:8000/docs

## Configuration

### Environment Variables

```bash
# Model Discovery
PRAXIS_MODEL_PATH=/Users/you/.cache/huggingface/hub/
NEURAL_LLAMA_SERVER_PATH=/usr/local/bin/llama-server
NEURAL_PORT_START=8080
NEURAL_PORT_END=8099

# CGRAG
RECALL_INDEX_PATH=/data/faiss_indexes/
RECALL_CHUNK_SIZE=512
RECALL_TOKEN_BUDGET=8000
RECALL_MIN_RELEVANCE=0.7

# Query Modes
PRAXIS_DEFAULT_MODE=two-stage
```

### Indexing Documentation for CGRAG

```bash
# One-time setup
docker-compose run --rm backend python -m app.cli.index_docs /path/to/docs

# Indexes are saved to ./backend/data/faiss_indexes/
```

## Development

### Hot Reload Enabled by Default

Code changes are automatically detected:

```bash
# Edit backend Python files → Uvicorn auto-reloads
# Edit frontend React/TypeScript → Vite HMR updates browser
```

### Rebuilding After Dependency Changes

```bash
# Backend dependencies changed (requirements.txt)
docker-compose build --no-cache backend
docker-compose up -d

# Frontend dependencies changed (package.json)
docker-compose build --no-cache frontend
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Testing

S.Y.N.A.P.S.E. ENGINE includes a comprehensive test suite with **24 automated tests** covering backend, frontend, and integration layers.

### Running Tests

```bash
# Run all tests (recommended before commits)
./scripts/test-all.sh

# Individual test suites
./scripts/test-backend.sh       # Backend API tests (10 tests)
./scripts/test-frontend.sh      # Frontend build tests (8 tests)
./scripts/test-integration.sh   # Service integration tests (6 tests)
```

**Test Scripts:**
- [test-all.sh](./scripts/test-all.sh) - Run all test suites
- [test-backend.sh](./scripts/test-backend.sh) - Backend API tests
- [test-frontend.sh](./scripts/test-frontend.sh) - Frontend build tests
- [test-integration.sh](./scripts/test-integration.sh) - Service integration tests

### Test Coverage

**Backend Tests (10):**
- API endpoint health checks
- Model registry operations
- Query processing pipeline
- CGRAG retrieval functionality
- Python unit tests

**Frontend Tests (8):**
- React app build validation
- Vite configuration
- Asset loading and optimization
- TypeScript compilation
- Environment variable injection

**Integration Tests (6):**
- Docker service communication
- WebSocket connections
- Backend Frontend integration
- Model server connectivity
- End to end query workflows

### Testing Strategy

- ✅ All tests run in Docker environment (no local dependencies)
- ✅ Tests validate both development and production builds
- ✅ Automated health checks for all services
- ✅ Integration tests ensure cross service compatibility

For detailed test documentation, see [TEST_SUITE_SUMMARY.md](./docs/TEST_SUITE_SUMMARY.md).

## Troubleshooting

**Docker starts but no models visible?**
- Check `MODEL_SCAN_PATH` in [.env](./.env.example) points to HuggingFace cache
- Navigate to Model Management → Click "RE-SCAN HUB"

**Models enabled but won't start?**
- Verify llama-server exists: `ls /usr/local/bin/llama-server`
- Check backend logs: `docker-compose logs -f backend`
- Ensure ports 8080-8099 are available

**CGRAG returns no results?**
- Index your documentation first: `docker-compose run --rm backend python -m app.cli.index_docs /docs`
- Verify index exists: `ls ./backend/data/faiss_indexes/`

**Two-stage mode not working?**
- Ensure you have at least one FAST tier model enabled
- Ensure you have at least one BALANCED or POWERFUL tier model enabled
- Check backend logs for routing errors

## Future Roadmap

### Code Chat Mode (In Development)
- Code Q&A with CGRAG powered context retrieval
- File creation and editing within workspace
- Secure sandboxed file operations
- Syntax highlighting and validation

### Multi Chat Mode (Planned)
- Conversational mode with message history
- Multiple models engage in extended dialogue
- Different personas/perspectives
- User moderates discussion flow

### Advanced Features (Planned)
- Custom query mode parameters and presets
- A/B testing capabilities for model comparison
- Advanced caching strategies for improved performance
- Distributed model orchestration across multiple machines

## Performance Targets

- ✅ Docker startup: <5 seconds (no models)
- ✅ Model startup: 10-15 seconds per model (concurrent)
- ✅ Simple query: <2 seconds (FAST tier)
- ✅ Two-stage query: <15 seconds total
- ✅ CGRAG retrieval: <100ms
- ✅ UI animations: 60fps

## Security Architecture (Phase 5)

**Enhanced Security:** Model servers are now bound to localhost and only accessible through the backend reverse proxy.

### Security Features

✅ **Localhost Only Binding**
- Model servers (llama.cpp) bind to `127.0.0.1` (localhost)
- NOT directly accessible from outside the Docker container
- Ports 8080-8099 are NOT exposed to host machine

✅ **Reverse Proxy Access**
- All model access goes through FastAPI backend at `http://localhost:8000`
- Centralized authentication and authorization (future enhancement)
- Request/response logging for observability
- Rate limiting capabilities (future enhancement)

✅ **API Endpoints**
```bash
# Chat completions (preferred for conversational AI)
POST /api/proxy/{model_id}/v1/chat/completions

# Text completions (raw completion)
POST /api/proxy/{model_id}/v1/completions

# Health check
GET /api/proxy/{model_id}/health
```

### Usage Examples

**Before Phase 5 (Direct Access - No Longer Works):**
```bash
# ❌ This will now fail - ports not exposed
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

**After Phase 5 (Reverse Proxy Access):**
```bash
# ✅ Access via backend reverse proxy
curl http://localhost:8000/api/proxy/deepseek_r1_8b_q4km/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

### Benefits

1. **Enhanced Security:** Model servers not exposed to host network
2. **Centralized Control:** All access goes through authenticated backend
3. **Observability:** Request/response logging at proxy layer
4. **Future-Proof:** Foundation for authentication, rate limiting, usage quotas
5. **Production-Ready:** Industry best practice for service mesh architecture

### Verification

**Check that ports are NOT exposed:**
```bash
# Should NOT show any llama-server ports (8080-8099)
docker ps | grep synapse_core

# Only port 8000 should be exposed for backend
# Expected output: 0.0.0.0:8000->8000/tcp
```

**Test reverse proxy access:**
```bash
# Start a model via admin panel or API
curl -X POST http://localhost:8000/api/models/servers/deepseek_r1_8b_q4km/start

# Check health via proxy
curl http://localhost:8000/api/proxy/deepseek_r1_8b_q4km/health
# Expected: {"status": "ok", "model_loaded": true}

# Send query via proxy
curl -X POST http://localhost:8000/api/proxy/deepseek_r1_8b_q4km/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, who are you?"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

**Verify localhost binding (inside container):**
```bash
# Inside backend container
docker exec synapse_core netstat -tulpn | grep llama-server
# Expected: 127.0.0.1:8080, NOT 0.0.0.0:8080
```

### Migration Notes

**For Frontend Developers:**
- Update any direct model server calls to use `/api/proxy/{model_id}/...`
- All model interactions should go through the backend API

**For API Consumers:**
- Replace `http://localhost:8080` with `http://localhost:8000/api/proxy/{model_id}`
- Ensure model is started before sending requests (check `/api/models/servers/status`)


## Contributing

1. Follow Docker-only development workflow
2. Test changes in Docker environment ([./scripts/test-all.sh](./scripts/test-all.sh))
3. Update documentation with changes
4. Check [SESSION_NOTES.md](./SESSION_NOTES.md) for recent context
5. Use specialized agents for domain specific tasks
6. Test CGRAG retrieval after doc changes
7. Validate query modes if modifying routing

## License

GPLv3

---

**Last Updated:** November 29, 2025
**Version:** 5.1 (TUI Navigation Overhaul - Bottom NavBar)
**Project Name:** S.Y.N.A.P.S.E. ENGINE (Scalable Yoked Network for Adaptive Praxial System Emergence) ✅
**Host API:** Automatic Metal Server Management ✅
**CGRAG Status:** Prod Ready ✅
**Two-Stage Workflow:** FAST → BALANCED/POWERFUL ✅
**Query Modes:** Simple, Two Stage, Council (Consensus/Debate), Benchmark ✅
**Real-Time Monitoring:** System Logs + Resource Tracking ✅
**Security:** Localhost-Only + Reverse Proxy + SSH Command Restriction ✅
