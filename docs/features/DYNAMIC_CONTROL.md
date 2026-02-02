# Dynamic Model Control

## Overview

Synapse Engine allows starting, stopping, and managing LLM servers dynamically from the WebUI without restarting Docker.

## Key Benefits

1. **Fast Startup** - Docker launches in ~5 seconds with no models
2. **Flexible** - Load only the models you need, when you need them
3. **Resource Efficient** - Stop models to free memory
4. **No Restart** - All changes happen live

## How It Works

### Discovery vs. Activation

Synapse Engine separates discovery from activation:

- **Discovery:** Scans HuggingFace cache, finds all GGUF models (automatic, <5s)
- **Activation:** Launches llama-server processes (user-controlled, 10-15s per model)

This separation means:
- Docker starts instantly with zero resource usage
- Users choose which models to activate
- Models can be started/stopped without losing discovery data
- Registry persists between restarts

### User Workflow

1. **Model Management Page** → View all discovered models
2. **Check "Enabled"** on desired models
3. **Click "START ALL ENABLED"** → Servers launch dynamically
4. **Use models** in query modes
5. **Click "STOP ALL SERVERS"** when done → Free memory

### API-Driven Control

Frontend sends REST API calls:
- `POST /api/models/servers/start-all` → Start all enabled models
- `POST /api/models/servers/{model_id}/start` → Start specific model
- `POST /api/models/servers/{model_id}/stop` → Stop specific model
- `POST /api/models/servers/stop-all` → Stop all servers

Backend manages llama.cpp processes:
- Concurrent startup (parallel loading)
- Health check validation
- Graceful shutdown (SIGTERM → SIGKILL)

## Performance

- **Individual model startup:** 10-15 seconds
- **4 models concurrently:** 40-50 seconds
- **Server stop:** <5 seconds
- **Docker restart:** Not required!

## Technical Details

### Startup Sequence

**Phase 1: Discovery (Automatic)**
```
Docker starts
  ↓
ModelDiscoveryService scans MODEL_SCAN_PATH
  ↓
Parses GGUF filenames
  ↓
Extracts metadata (family, size, quantization)
  ↓
Auto-assigns tiers (FAST/BALANCED/POWERFUL)
  ↓
Saves to model_registry.json
  ↓
Ready in ~5s (no servers running)
```

**Phase 2: Activation (User-Triggered)**
```
User enables models in WebUI
  ↓
User clicks "START ALL ENABLED"
  ↓
Frontend → POST /api/models/servers/start-all
  ↓
Backend retrieves enabled models from registry
  ↓
Launches llama-server processes concurrently
  ↓
Each server:
  - Loads GGUF model into memory
  - Initializes llama.cpp context
  - Starts HTTP server on assigned port
  - Reports ready via health check
  ↓
All servers operational (40-50s for 4 models)
```

### Model Server Lifecycle

**1. Startup**
```python
# Backend: app/services/llama_server_manager.py
async def start_server(model: ModelInfo):
    # Validate model file exists
    if not model.file_path.exists():
        raise ModelNotFoundError(model.model_id)

    # Check port availability
    if not self._is_port_available(model.port):
        raise PortAlreadyInUseError(model.port)

    # Launch llama-server subprocess
    process = await asyncio.create_subprocess_exec(
        str(self.llama_server_path),
        "-m", str(model.file_path),
        "--port", str(model.port),
        "--ctx-size", str(model.context_size),
        # ... additional flags
    )

    # Wait for health check
    await self._wait_for_ready(model.model_id, model.port)

    # Register process
    self.servers[model.model_id] = ServerProcess(
        process=process,
        model=model,
        started_at=time.time()
    )
```

**2. Health Checking**
```python
async def _wait_for_ready(model_id: str, port: int):
    # Poll /health endpoint every 500ms
    # Timeout after max_startup_time (default 60s)
    # Raise exception if server fails to start
```

**3. Shutdown**
```python
async def stop_server(model_id: str):
    # Send SIGTERM (graceful shutdown)
    process.terminate()

    # Wait up to 10 seconds
    await asyncio.wait_for(process.wait(), timeout=10)

    # If still running, send SIGKILL
    if process.returncode is None:
        process.kill()
        await process.wait()

    # Deregister process
    del self.servers[model_id]
```

### Concurrency

Models start in parallel for optimal performance:

```python
async def start_all(models: List[ModelInfo]):
    # Create concurrent startup tasks
    tasks = [
        self.start_server(model)
        for model in models
    ]

    # Execute concurrently with asyncio.gather
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle individual failures gracefully
    successful = [r for r in results if not isinstance(r, Exception)]
    return successful
```

**Benefits:**
- 4 models start in ~45s (vs. 60s sequential)
- CPU cores utilized efficiently
- Failed models don't block others

## Use Cases

### Development
Load one fast model for quick testing, stop when done.

```bash
# Enable single FAST tier model
# Start via WebUI
# Test queries
# Stop to free 2-4GB memory
```

### Experimentation
Try different quantizations (Q2, Q4, Q8) without restarting.

```bash
# Day 1: Enable Q2_K models (fast, lower quality)
# Day 2: Disable Q2, enable Q4_K (balanced)
# Day 3: Disable Q4, enable Q8 (slow, high quality)
# No Docker restarts needed!
```

### Production
Load powerful models only when needed, save resources during idle time.

```bash
# Daytime: Only FAST tier running (low usage)
# Peak hours: START ALL (full capacity)
# Night: STOP ALL (zero resource usage)
```

### Benchmarking
Start/stop models to compare performance in isolation.

```bash
# Test model A alone
# Stop model A, start model B alone
# Compare response quality and latency
```

## WebUI Integration

### Model Management Page

**Components:**
- **Model Table:** Shows all discovered models with metadata
- **Enable Checkbox:** Toggle model enabled status
- **Status Indicator:** Running (green) / Stopped (gray)
- **Individual Controls:** START / STOP buttons per model
- **Bulk Controls:** START ALL ENABLED / STOP ALL SERVERS

**Implementation:**
```typescript
// frontend/src/pages/ModelManagementPage/ModelManagementPage.tsx

const handleStartAll = async () => {
  setIsStartingAll(true);
  try {
    const response = await fetch('/api/models/servers/start-all', {
      method: 'POST'
    });
    const result = await response.json();
    console.log(`Started ${result.started}/${result.total} servers`);
    await refetch(); // Refresh registry
  } finally {
    setIsStartingAll(false);
  }
};
```

### Real-Time Status Updates

**Polling Strategy:**
- Registry refetched every 30 seconds (configurable)
- Manual refresh on user actions (start/stop)
- Server status endpoint shows running processes

```typescript
const { data: registry } = useQuery({
  queryKey: ['model-registry'],
  queryFn: fetchModelRegistry,
  refetchInterval: 30000, // 30s
  staleTime: 10000 // 10s
});
```

## API Reference

### Start Single Model

```bash
POST /api/models/servers/{model_id}/start

Response:
{
  "message": "Server started for qwen_7b_fast",
  "model_id": "qwen_7b_fast",
  "display_name": "Qwen 7B (Q4_K_M)",
  "port": 8080,
  "status": "started",
  "startup_time_seconds": 12.3
}
```

### Stop Single Model

```bash
POST /api/models/servers/{model_id}/stop

Response:
{
  "message": "Server stopped for qwen_7b_fast",
  "model_id": "qwen_7b_fast",
  "status": "stopped",
  "shutdown_time_seconds": 2.1
}
```

### Start All Enabled Models

```bash
POST /api/models/servers/start-all

Response:
{
  "message": "Started 3/4 servers",
  "started": 3,
  "total": 4,
  "startup_time_seconds": 45.2,
  "models": [
    {
      "model_id": "qwen_7b_fast",
      "display_name": "Qwen 7B (Q4_K_M)",
      "port": 8080
    },
    // ...
  ]
}
```

### Stop All Servers

```bash
POST /api/models/servers/stop-all

Response:
{
  "message": "Stopped 3 servers",
  "stopped": 3,
  "shutdown_time_seconds": 5.7
}
```

### Get Running Servers

```bash
GET /api/models/servers

Response:
{
  "servers": [
    {
      "model_id": "qwen_7b_fast",
      "port": 8080,
      "status": "running",
      "uptime_seconds": 3600,
      "memory_used_mb": 3200
    },
    // ...
  ],
  "total_running": 2
}
```

## Error Handling

### Common Errors

**Model Not Found (404)**
```json
{
  "error": "Model not found: invalid_model_id",
  "detail": "Model does not exist in registry"
}
```

**Server Manager Not Initialized (503)**
```json
{
  "error": "Server manager not initialized",
  "detail": "Backend service not ready"
}
```

**Failed to Start (500)**
```json
{
  "error": "Failed to start server",
  "detail": "Port 8080 already in use"
}
```

### Recovery Strategies

**Port conflicts:**
- Check `MODEL_PORT_RANGE_START` and `END` in .env
- Ensure no other services using 8080-8099
- Use `lsof -i :8080-8099` to find conflicts

**Memory exhaustion:**
- Stop unused models first
- Check available RAM before starting large models
- Use Q2/Q4 quantizations for memory-constrained systems

**Model file not found:**
- Verify MODEL_SCAN_PATH is correct
- Re-run model discovery: Click "RE-SCAN HUB"
- Check file permissions

## Best Practices

### Memory Management

**Rule of Thumb:**
- Q2_K model: ~2GB RAM
- Q4_K model: ~4GB RAM
- Q8 model: ~8GB RAM

**Example:** 16GB RAM system
- Load max 2 Q8 models OR
- Load max 4 Q4_K models OR
- Load mix: 1 Q8 + 2 Q4_K + 1 Q2_K

### Port Assignment

Models are assigned ports sequentially:
- First model: 8080
- Second model: 8081
- Third model: 8082
- ...

**Troubleshooting:** If model won't start, check port conflicts:
```bash
lsof -i :8080
# If occupied, adjust PORT_RANGE or stop conflicting service
```

### Startup Order

For optimal startup:
1. Enable smallest models first (FAST tier)
2. Enable medium models second (BALANCED tier)
3. Enable largest models last (POWERFUL tier)

This allows quick testing with small models while large models load.

---

For more information, see [README.md](../../README.md) and [MODES.md](./MODES.md).
