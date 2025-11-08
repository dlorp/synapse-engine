# Docker llama-server Cross-Platform Fix

**Date:** 2025-11-04
**Issue:** macOS llama-server binary cannot run inside Linux Docker container
**Status:** Implementation Required

---

## Problem Analysis

### Current Architecture Issue

The MAGI backend is designed to:
1. Run inside a Linux Docker container (`python:3.11-slim`)
2. Launch llama-server processes using `subprocess.Popen`
3. Mount llama-server binary from host at `/usr/local/bin/llama-server`

**Critical incompatibility:**
- Host binary: macOS Mach-O executable (ARM64)
- Container OS: Linux (Debian-based)
- **Result:** `OSError: [Errno 8] Exec format error` when trying to execute

### Why Volume Mount Won't Work

```bash
# Host binary (macOS)
$ file /opt/homebrew/bin/llama-server
/opt/homebrew/bin/llama-server: Mach-O 64-bit executable arm64

# Container OS (Linux)
$ docker exec magi_backend cat /etc/os-release
Debian GNU/Linux 11 (bullseye)
```

Linux kernel cannot execute Mach-O binaries - they have completely different executable formats (ELF vs Mach-O).

---

## Solution Options

### Option 1: Build llama.cpp Inside Docker Container ✅ RECOMMENDED

**Approach:** Compile llama.cpp from source during Docker image build.

**Pros:**
- Native Linux binary that runs in container
- Backend can manage lifecycle as designed
- Self-contained deployment
- Works across all platforms (macOS, Linux, Windows)

**Cons:**
- Longer Docker build time (5-10 minutes initial build)
- Requires build tools in container (gcc, cmake)
- Larger image size (~200MB larger)

**Implementation:**
Modify `backend/Dockerfile` to compile llama.cpp during build.

---

### Option 2: Use Pre-built Linux Binaries from llama.cpp Releases

**Approach:** Download pre-compiled Linux binary from llama.cpp GitHub releases.

**Pros:**
- Faster than compiling from source
- Known working binaries
- Smaller final image than Option 1

**Cons:**
- Requires network access during build
- Binary might not be optimized for container architecture
- Dependency on GitHub releases availability

**Implementation:**
Add download step in Dockerfile using wget/curl.

---

### Option 3: Run llama-server on Host, Backend Connects via Network

**Approach:**
- Run llama-server processes on macOS host
- Backend connects to `host.docker.internal:<port>`
- Backend becomes orchestrator, not process manager

**Pros:**
- No Docker changes needed
- Use existing optimized macOS binary
- Faster development iteration

**Cons:**
- Requires manual server management on host
- Backend cannot manage server lifecycle (start/stop/restart)
- Different behavior between dev (Docker) and prod
- Breaks architecture design (backend as orchestrator)

**Implementation:**
- Start llama-server instances manually on host ports 8080-8099
- Update backend to use `host.docker.internal` instead of `localhost`

---

## Recommended Implementation: Option 1

**Why Option 1?**
- Maintains architectural integrity (backend manages servers)
- Production-ready and platform-independent
- Works in any Docker environment
- Backend code remains unchanged

### Phase 1: Update Dockerfile

**File:** `${PROJECT_DIR}/backend/Dockerfile`

Add build stage for llama.cpp compilation:

```dockerfile
# =============================================================================
# Stage 1.5: llama.cpp Builder
# =============================================================================
FROM runtime AS llama-builder

# Install build dependencies for llama.cpp
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Clone llama.cpp repository
WORKDIR /tmp/llama.cpp
RUN git clone --depth 1 --branch master https://github.com/ggerganov/llama.cpp.git .

# Build llama-server binary
# Use cmake with optimizations for production
RUN cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_CURL=ON \
    -DLLAMA_NATIVE=ON \
    && cmake --build build --config Release -j $(nproc) \
    && strip build/bin/llama-server

# =============================================================================
# Stage 2: Runtime (modified)
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS runtime

# [... existing runtime setup ...]

# Copy llama-server binary from llama-builder stage
COPY --from=llama-builder /tmp/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server
RUN chmod +x /usr/local/bin/llama-server

# [... rest of runtime setup ...]
```

### Phase 2: Update docker-compose.yml

**File:** `${PROJECT_DIR}/docker-compose.yml`

**Remove the llama-server volume mount:**

```yaml
# Line 231-234: DELETE THIS SECTION
# BEFORE:
      # Mount llama-server binary from host (read-only)
      # Backend will use this to launch model servers
      # macOS Homebrew installs to /opt/homebrew/bin/llama-server
      - /opt/homebrew/bin/llama-server:/usr/local/bin/llama-server:ro

# AFTER: (remove entirely)
```

Update notes section:

```yaml
# Line 365-369
# 2. Model Management:
#    - Models are discovered from ${PRAXIS_MODEL_PATH}/
#    - llama-server binary compiled during Docker build (Linux-native)
#    - Model servers launched on ports 8080-8099 (configurable)
#    - Active profile: development (change via MAGI_PROFILE env var)
```

### Phase 3: Rebuild and Test

```bash
# Step 1: Stop existing containers
docker-compose down

# Step 2: Rebuild backend with llama.cpp compiled
docker-compose build --no-cache backend

# Expected output: Should see cmake compilation logs
# Build time: 5-10 minutes (first build)

# Step 3: Start all services
docker-compose up -d

# Step 4: Verify llama-server binary inside container
docker exec magi_backend ls -lh /usr/local/bin/llama-server
# Should show: Linux ELF executable

docker exec magi_backend file /usr/local/bin/llama-server
# Should show: ELF 64-bit LSB executable, [architecture]

# Step 5: Test server launch
curl -X POST http://localhost:8000/api/models/servers/start-all

# Step 6: Check logs for successful server launches
docker-compose logs -f backend

# Expected: No "Exec format error", servers start successfully
```

---

## Alternative Quick Fix: Option 3 (Temporary Development Workaround)

If you need **immediate functionality** while Option 1 is being implemented:

### Quick Workaround Steps

**1. Start llama-server instances on macOS host:**

Create script: `${PROJECT_DIR}/scripts/start-host-servers.sh`

```bash
#!/bin/bash
# Start llama-server instances on macOS host for Docker development

HUB_PATH="${PRAXIS_MODEL_PATH}"
LLAMA_BIN="/opt/homebrew/bin/llama-server"

# Model configurations (from profile)
declare -A MODELS=(
  ["8080"]="$HUB_PATH/bartowski_DeepSeek-R1-Distill-Qwen-1.5B-GGUF/DeepSeek-R1-Distill-Qwen-1.5B-Q2_K.gguf"
  ["8081"]="$HUB_PATH/bartowski_DeepSeek-R1-Distill-Qwen-1.5B-GGUF/DeepSeek-R1-Distill-Qwen-1.5B-Q2_K.gguf"
  ["8082"]="$HUB_PATH/bartowski_DeepSeek-R1-Distill-Qwen-1.5B-GGUF/DeepSeek-R1-Distill-Qwen-1.5B-Q3_K_L.gguf"
  ["8083"]="$HUB_PATH/bartowski_DeepSeek-R1-Distill-Qwen-1.5B-GGUF/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf"
)

echo "Starting llama-server instances on host..."

for PORT in "${!MODELS[@]}"; do
  MODEL="${MODELS[$PORT]}"
  echo "Starting server on port $PORT with model: $(basename $MODEL)"

  $LLAMA_BIN \
    --model "$MODEL" \
    --host 0.0.0.0 \
    --port $PORT \
    --ctx-size 32768 \
    --n-gpu-layers 99 \
    --threads 8 \
    --batch-size 512 \
    --ubatch-size 256 \
    --flash-attn \
    --no-mmap \
    > /tmp/llama-server-$PORT.log 2>&1 &

  echo "  PID: $!"
done

echo "All servers started. Check logs in /tmp/llama-server-*.log"
echo "To stop: pkill -f llama-server"
```

**2. Update backend to connect to host:**

Modify `${PROJECT_DIR}/backend/app/services/llama_server_manager.py`:

```python
# Line 113-114
def __init__(
    self,
    llama_server_path: Path = Path("/usr/local/bin/llama-server"),
    max_startup_time: int = 120,
    readiness_check_interval: int = 2,
    host: str = "0.0.0.0",
    use_host_servers: bool = False  # NEW PARAMETER
):
    self.use_host_servers = use_host_servers  # NEW ATTRIBUTE

    # Skip validation if using host servers
    if not use_host_servers and not self.llama_server_path.exists():
        logger.warning(...)
```

**3. Set environment variable:**

```yaml
# docker-compose.yml backend service
environment:
  - USE_HOST_SERVERS=true  # Signal to skip subprocess launching
```

**Limitation:** Backend cannot manage server lifecycle (start/stop/restart will not work).

---

## Testing Checklist

After implementing the solution:

- [ ] Docker build completes without errors
- [ ] llama-server binary exists in container at `/usr/local/bin/llama-server`
- [ ] Binary is Linux ELF executable (verify with `file` command)
- [ ] Backend container starts without warnings about missing binary
- [ ] Model discovery works: `curl http://localhost:8000/api/models/discovery`
- [ ] Server start works: `curl -X POST http://localhost:8000/api/models/servers/start-all`
- [ ] Servers show as running: `curl http://localhost:8000/api/models/servers`
- [ ] Health checks pass: `curl http://localhost:8080/health` (for each port)
- [ ] Query routing works end-to-end
- [ ] No "Permission denied" or "Exec format error" in logs

---

## Expected Results

### Before Fix
```bash
$ docker-compose logs backend
ERROR: Failed to start server for model Q2_FAST_1
OSError: [Errno 8] Exec format error: '/usr/local/bin/llama-server'
```

### After Fix
```bash
$ docker-compose logs backend
INFO: Starting llama.cpp server for: DeepSeek R1 Q2_K (Fast #1)
INFO:   Model file: /models/bartowski_DeepSeek-R1-Distill-Qwen-1.5B-GGUF/...
INFO:   Port: 8080
INFO:   Tier: fast
INFO: Server process started (PID: 1234)
INFO: Server ready at http://0.0.0.0:8080
```

---

## Files Modified Summary

### Option 1 (Recommended):
- **Update:** `${PROJECT_DIR}/backend/Dockerfile` (add llama.cpp build stage)
- **Update:** `${PROJECT_DIR}/docker-compose.yml` (remove volume mount, update notes)

### Option 3 (Quick Workaround):
- **Update:** `${PROJECT_DIR}/docker-compose.yml` (remove volume mount)
- **Create:** `${PROJECT_DIR}/scripts/start-host-servers.sh` (server launcher)
- **Update:** `${PROJECT_DIR}/backend/app/services/llama_server_manager.py` (host mode)

---

## Implementation Recommendation

**For immediate development:**
- Use **Option 3** (Quick Workaround) to unblock testing
- Manually start llama-server instances on host
- Backend connects via `host.docker.internal`

**For production and long-term:**
- Implement **Option 1** (Build llama.cpp in Docker)
- Self-contained, platform-independent solution
- Backend maintains full lifecycle control

---

## Next Steps

1. **Choose solution** based on urgency and requirements
2. **Implement changes** following phase breakdown
3. **Test thoroughly** using checklist above
4. **Document** in SESSION_NOTES.md with results
5. **Update CLAUDE.md** with new Docker workflow if needed

---

## References

- llama.cpp GitHub: https://github.com/ggerganov/llama.cpp
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Docker Desktop host networking: https://docs.docker.com/desktop/networking/#i-want-to-connect-from-a-container-to-a-service-on-the-host
