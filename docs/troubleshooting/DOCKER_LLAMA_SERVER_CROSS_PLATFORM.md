# Docker llama-server Cross-Platform Compatibility Fix

**Date:** 2025-11-04 (later session)
**Issue:** macOS llama-server binary cannot execute in Linux Docker container
**Status:** ⚠️ Temporary workaround implemented, permanent fix documented

---

## Problem Discovered

Backend container failing to launch llama-server processes with:
```
OSError: [Errno 8] Exec format error: '/usr/local/bin/llama-server'
```

### Root Cause Analysis

**Binary Incompatibility:**
- docker-compose.yml was mounting llama-server from macOS host: `/opt/homebrew/bin/llama-server`
- macOS binary format: **Mach-O 64-bit executable arm64**
- Backend container OS: **Linux** (Debian-based `python:3.11-slim`)
- **Result:** Linux kernel cannot execute macOS Mach-O binaries (requires ELF format)

**Verification:**
```bash
# Host binary (macOS)
$ file /opt/homebrew/bin/llama-server
/opt/homebrew/bin/llama-server: Mach-O 64-bit executable arm64

# Container OS (Linux)
$ docker exec magi_backend cat /etc/os-release
Debian GNU/Linux 11 (bullseye)
```

**Why volume mount won't work:**
- Different executable formats: ELF (Linux) vs Mach-O (macOS)
- Different OS kernels: Linux vs Darwin (macOS)
- Cannot bridge this gap with simple volume mount

---

## Solution Implemented

### Two-Track Approach

#### Track 1: Immediate Workaround (Implemented)
For development unblocking while permanent fix is prepared.

**Changes Made:**

1. **Removed incorrect volume mount from docker-compose.yml:**
   - **File:** `${PROJECT_DIR}/docker-compose.yml`
   - **Lines modified:** 231-235, 367-370, 404
   - **Change:** Removed macOS binary mount, added explanatory comments

2. **Created comprehensive fix documentation:**
   - **File:** `${PROJECT_DIR}/DOCKER_LLAMA_SERVER_FIX.md`
   - **Content:**
     - Problem analysis with technical details
     - Three solution options with trade-offs
     - Step-by-step implementation guides
     - Testing checklist

3. **Created host server launcher scripts:**
   - **File:** `${PROJECT_DIR}/scripts/start-host-llama-servers.sh` (executable)
   - **Purpose:** Start llama-server instances on macOS host
   - **Features:**
     - Prerequisites checking (binary exists, HUB directory exists)
     - Launches 4 servers on ports 8080-8083
     - Matches development.yaml profile configuration
     - Health checking for all servers
     - Colored output with detailed logging
     - Logs to `/tmp/magi-llama-servers/`

   - **File:** `${PROJECT_DIR}/scripts/stop-host-llama-servers.sh` (executable)
   - **Purpose:** Gracefully stop all host llama-server processes
   - **Features:**
     - Graceful SIGTERM with fallback to SIGKILL
     - Cleanup of PID files

#### Track 2: Permanent Solution (Documented, Not Implemented)
**Recommended: Build llama.cpp inside Docker container**

**Approach:**
- Add build stage to `backend/Dockerfile` that compiles llama.cpp from source
- Copy compiled Linux-native binary to runtime stage
- Removes dependency on host binary

**Benefits:**
- Platform-independent (works on macOS, Linux, Windows)
- Backend maintains full server lifecycle control
- Self-contained deployment
- Production-ready

**Trade-offs:**
- Longer initial Docker build time (5-10 minutes)
- Slightly larger image size (~200MB increase)

**Implementation guide:** See `DOCKER_LLAMA_SERVER_FIX.md` → Option 1

---

## Files Modified Summary

### Modified:
- ✏️ `${PROJECT_DIR}/docker-compose.yml`
  - Lines 231-235: Removed macOS binary volume mount
  - Line 367-370: Updated model management notes
  - Line 404: Updated troubleshooting section

### Created:
- ➕ `${PROJECT_DIR}/DOCKER_LLAMA_SERVER_FIX.md`
  - Complete problem analysis
  - Three solution options with implementation guides
  - Testing procedures

- ➕ `${PROJECT_DIR}/scripts/start-host-llama-servers.sh`
  - Launches llama-server on macOS host
  - 4 model configurations (Q2/Q3/Q4)
  - Health checking and error handling

- ➕ `${PROJECT_DIR}/scripts/stop-host-llama-servers.sh`
  - Graceful shutdown of host servers
  - PID file cleanup

---

## Usage: Temporary Workaround

### Step 1: Start llama-server instances on macOS host

```bash
cd ${PROJECT_DIR}
./scripts/start-host-llama-servers.sh
```

**Expected output:**
```
========================================
MAGI llama-server Host Launcher
========================================

✓ llama-server found: /opt/homebrew/bin/llama-server
✓ HUB directory found: ${PRAXIS_MODEL_PATH}
✓ Log directory ready: /tmp/magi-llama-servers

→ Starting server on port 8080
   Model: DeepSeek-R1-Distill-Qwen-1.5B-Q2_K.gguf
   PID: 12345
✓ Server started successfully (PID: 12345)

[... 3 more servers ...]

✓ All servers started successfully!

Servers listening on:
  - http://localhost:8080
  - http://localhost:8081
  - http://localhost:8082
  - http://localhost:8083

From Docker backend: http://host.docker.internal:<port>

To stop all servers: ./scripts/stop-host-llama-servers.sh
```

### Step 2: Verify servers are running

```bash
# Check server health
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health

# List running processes
pgrep -af "llama-server.*--port"
```

### Step 3: Stop servers when done

```bash
./scripts/stop-host-llama-servers.sh
```

---

## Limitations of Temporary Workaround

⚠️ **Backend lifecycle management disabled:**
- Backend cannot start/stop servers via API
- `POST /api/models/servers/start-all` endpoint will not work
- `POST /api/models/servers/start/{model_id}` will not work
- Manual server management required

⚠️ **Docker backend must connect to host:**
- Backend needs to use `host.docker.internal:<port>` instead of `localhost:<port>`
- Requires backend code modification (not yet implemented)

⚠️ **Different behavior from production:**
- Production will use Option 1 (built-in llama.cpp binary)
- Development workflow differs from deployment

---

## Next Steps

### Immediate (Unblock Development):
1. ✅ Removed incorrect volume mount from docker-compose.yml
2. ✅ Created host launcher scripts
3. ⏳ Test host launcher: `./scripts/start-host-llama-servers.sh`
4. ⏳ Verify health checks: `curl http://localhost:8080/health`
5. ⏳ Modify backend to connect via `host.docker.internal` (if needed)
6. ⏳ Test query routing end-to-end with host servers

### Short-Term (Proper Fix):
1. ⏳ Implement Option 1 from `DOCKER_LLAMA_SERVER_FIX.md`
2. ⏳ Modify `backend/Dockerfile` to compile llama.cpp
3. ⏳ Test Docker build: `docker-compose build --no-cache backend`
4. ⏳ Verify binary in container: `docker exec magi_backend file /usr/local/bin/llama-server`
5. ⏳ Test server launches from container
6. ⏳ Remove host launcher scripts (no longer needed)

### Long-Term (Production):
1. ⏳ Validate cross-platform compatibility (Linux, macOS ARM, macOS Intel, Windows)
2. ⏳ Optimize Docker build caching for faster rebuilds
3. ⏳ Document deployment procedures with built-in binary

---

## Technical Lessons Learned

1. **Binary compatibility is critical** when mounting executables into containers
   - Always verify binary format matches container OS
   - Use `file <path>` to check executable type

2. **macOS Docker quirks:**
   - Docker Desktop uses Linux VM, not native macOS kernel
   - `network_mode: host` doesn't work same as native Linux
   - `host.docker.internal` is needed for container→host communication

3. **Volume mount limitations:**
   - Can mount files but cannot change binary format
   - Executables must match container OS kernel

4. **Two-track solutions work well:**
   - Quick workaround unblocks immediate work
   - Proper long-term fix maintains architecture integrity
   - Document both approaches clearly

---

## Troubleshooting

### Issue: "llama-server not found"
```bash
# Check if llama-server installed
which llama-server

# Install if missing
brew install llama.cpp
```

### Issue: "Model file not found"
```bash
# Verify HUB directory exists
ls -la ${PRAXIS_MODEL_PATH}/

# Check model files
ls -la ${PRAXIS_MODEL_PATH}/bartowski_DeepSeek-R1-Distill-Qwen-1.5B-GGUF/
```

### Issue: "Port already in use"
```bash
# Check what's using the port
lsof -i :8080

# Kill existing servers
pkill -f "llama-server.*--port"

# Or use stop script
./scripts/stop-host-llama-servers.sh
```

### Issue: "Health check timeout"
```bash
# Check server logs
tail -f /tmp/magi-llama-servers/llama-server-8080.log

# Verify server is running
pgrep -af "llama-server.*8080"

# Check if server started but still initializing (can take 30-60s for large models)
```

---

## References

- llama.cpp GitHub: https://github.com/ggerganov/llama.cpp
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Docker Desktop host networking: https://docs.docker.com/desktop/networking/
- ELF vs Mach-O binary formats: Operating system executable format differences

---
