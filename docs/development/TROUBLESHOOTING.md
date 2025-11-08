# MAGI Troubleshooting Guide

**Date:** 2025-11-04
**Version:** 3.0 (Post-MAGI_REWORK)
**Status:** System operational after Phase 1-12 implementation

---

## Table of Contents

1. [Quick Health Check](#quick-health-check)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Docker Container Issues](#docker-container-issues)
4. [Backend Issues](#backend-issues)
5. [Frontend Issues](#frontend-issues)
6. [Model Management Issues](#model-management-issues)
7. [CGRAG Issues](#cgrag-issues)
8. [Query Processing Issues](#query-processing-issues)
9. [Performance Issues](#performance-issues)
10. [Debugging Tools & Commands](#debugging-tools--commands)
11. [Known Issues](#known-issues)

---

## Quick Health Check

Run these commands to verify system health:

```bash
# 1. Check all containers are running
docker-compose ps

# Expected output: 3 containers (backend, frontend, redis) all "healthy"

# 2. Check backend health
curl http://localhost:8000/health

# Expected: {"status": "ok"}

# 3. Check frontend is accessible
curl http://localhost:5173

# Expected: HTML response

# 4. Check model registry
curl http://localhost:8000/api/models/registry | jq

# Expected: JSON with discovered models

# 5. Check running servers
curl http://localhost:8000/api/models/servers | jq

# Expected: Empty array [] if no models started yet
```

**All healthy?** → System is working ✅
**Any failures?** → See relevant section below 👇

---

## Common Issues & Solutions

### Issue: "Environment variable not found: MODEL_Q2_FAST_1_URL"

**Symptom:**
```
ConfigurationError: Environment variable not found: MODEL_Q2_FAST_1_URL
Application startup failed. Exiting.
```

**Cause:** The legacy Q2/Q3/Q4 model configurations in `config/default.yaml` were not removed during the MAGI_REWORK migration.

**Solution:**
1. Edit `config/default.yaml`
2. Find the `models:` section (around line 28-71)
3. Replace the entire legacy section with:
```yaml
# Legacy model configurations have been removed in favor of dynamic model management.
# The system now uses:
# 1. Model discovery (scans for GGUF files)
# 2. Profile-based configuration (enabled_models, tier_config)
# 3. Dynamic server startup via WebUI
```
4. Restart containers: `docker-compose down && docker-compose up -d`

**Prevention:** After MAGI_REWORK, only profiles (`config/profiles/*.yaml`) define model configurations. The `config/default.yaml` should NOT contain hardcoded model URLs.

---

### Issue: Admin panel not loading (stuck on "LOADING..." or 500 errors)

**Symptom:**
- Admin panel shows "LOADING SYSTEM INFO..." forever
- System Health section fails to load
- Discovery button returns 500 error
- Browser console shows network errors

**Cause:** After MAGI_REWORK implementation, two issues can occur:
1. **Backend:** Admin endpoints try to import removed `startup_service` → 500 errors
2. **Frontend:** Vite proxy uses `localhost` instead of Docker service name → connection refused

**Solution 1: Fix backend admin endpoints**

If you see 500 errors from `/api/admin/*` endpoints:

1. Check backend logs for ImportError:
```bash
docker-compose logs backend | grep "startup_service"
```

2. If you see errors, the admin.py file needs updating. The fix involves removing all references to `startup_service` in `backend/app/routers/admin.py`:
   - Line 31: Update docstring return type
   - Lines 33-37: Remove `startup_service` from import and return
   - Lines 57, 119, 211, 374, 413, 481: Remove trailing `_` from unpacking
   - Line 392: Remove `startup_service_initialized` from response

3. Restart backend:
```bash
docker-compose restart backend
```

**Solution 2: Fix frontend Vite proxy**

If you see proxy errors in frontend logs:

1. Check frontend logs for proxy errors:
```bash
docker-compose logs frontend | grep "ECONNREFUSED"
```

2. Update `frontend/vite.config.ts` proxy targets:
```typescript
proxy: {
  '/api': {
    target: 'http://backend:8000',  // NOT localhost!
    changeOrigin: true,
  },
  '/ws': {
    target: 'ws://backend:8000',    // NOT localhost!
    ws: true,
  },
}
```

3. Restart frontend:
```bash
docker-compose restart frontend
```

**Verification:**
```bash
# Test admin endpoints directly
curl http://localhost:8000/api/admin/health/detailed
curl http://localhost:8000/api/admin/system/info
curl -X POST http://localhost:8000/api/admin/discover

# All should return 200 with JSON response
```

**Prevention:** After MAGI_REWORK, `startup_service` no longer exists. Admin endpoints should only use `model_registry, server_manager, profile_manager, discovery_service`. Frontend must use Docker service names (`backend:8000`), not `localhost:8000`.

---

### Issue: Backend container is "unhealthy"

**Symptom:**
```
docker-compose ps
# Shows: backend (unhealthy)
```

**Diagnosis:**
```bash
# Check backend logs
docker-compose logs backend

# Look for startup errors
```

**Common Causes:**

1. **Config file syntax error**
   - Check YAML formatting in `config/default.yaml` and `config/profiles/development.yaml`
   - Run: `python -m yaml config/default.yaml` (requires PyYAML)

2. **Missing environment variables**
   - Ensure `.env` file exists (copy from `.env.example`)
   - Verify `MODEL_SCAN_PATH` points to valid directory
   - Verify `LLAMA_SERVER_PATH` is correct

3. **Port conflicts**
   - Ensure ports 8000, 8080-8099 are available
   - Run: `lsof -i :8000` to check port usage

4. **Model registry corruption**
   - Delete `backend/data/model_registry.json`
   - Restart containers to trigger re-discovery

**Solution:** Fix the specific error shown in logs, then restart:
```bash
docker-compose down
docker-compose up -d
```

---

### Issue: Frontend shows 404 errors

**Symptom:** Browser console shows `GET http://localhost:5173/api/models/registry 404`

**Cause:** Frontend is trying to access API but proxy is misconfigured.

**Solution:**
1. Verify `frontend/vite.config.ts` has correct proxy:
```typescript
proxy: {
  '/api': {
    target: 'http://backend:8000',
    changeOrigin: true
  }
}
```

2. Ensure both frontend and backend are on same Docker network
3. Rebuild frontend: `docker-compose build --no-cache frontend`
4. Restart: `docker-compose up -d`

---

### Issue: "ValueError: min() arg is an empty sequence"

**Symptom:** Backend logs show:
```
ERROR: Error in health check loop: min() arg is an empty sequence
```

**Cause:** Health check loop tries to find minimum interval but no models are loaded yet.

**Impact:** ⚠️ **Minor** - Does not affect functionality. System is designed to start with NO models loaded.

**Expected Behavior:** This error appears once at startup when zero models are running. It will disappear once you start models via WebUI.

**Fix (Optional):** Add guard clause in `backend/app/services/models.py` line 143:
```python
async def _health_check_loop(self):
    while True:
        try:
            if not self.models:  # Guard clause
                await asyncio.sleep(30)
                continue

            min_interval = min(
                model.health_check_interval for model in self.models.values()
            )
            # ...
```

**Status:** Known issue, low priority. System functions correctly despite this error.

---

## Docker Container Issues

### Containers won't start

```bash
# Stop all containers
docker-compose down

# Remove all volumes (CAUTION: deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up -d

# Monitor logs
docker-compose logs -f
```

### Container crashes immediately

```bash
# View crash logs
docker-compose logs <service_name>

# Common issues:
# - Port already in use → Change port in docker-compose.yml
# - Volume mount error → Verify paths exist
# - Memory limit → Increase Docker memory allocation
```

### "No such file or directory" errors

**Cause:** Volume mounts pointing to non-existent paths

**Solution:**
1. Check `docker-compose.yml` volume mounts
2. Ensure paths exist on host machine:
   - `./backend` → Backend source code
   - `./frontend` → Frontend source code
   - `./config` → Configuration files
   - `./backend/data` → Model registry and FAISS indexes

---

## Backend Issues

### Backend returns 500 errors

**Diagnosis:**
```bash
# Check recent backend logs
docker-compose logs --tail=50 backend

# Look for Python tracebacks
```

**Common Causes:**

1. **Model not found**
   - Symptom: `ModelNotFoundError: Model xyz not found`
   - Solution: Run model discovery via WebUI or API

2. **Server manager not initialized**
   - Symptom: `Server manager not initialized`
   - Solution: Check backend startup logs for initialization errors

3. **CGRAG index missing**
   - Symptom: `FAISS index not found`
   - Solution: Index documentation (see CGRAG section below)

### Backend hot reload not working

**Symptom:** Code changes don't trigger restart

**Cause:** Volume mount not configured or `--reload` flag missing

**Solution:**
1. Verify `docker-compose.yml` has:
```yaml
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  volumes:
    - ./backend:/app
```

2. Restart containers: `docker-compose down && docker-compose up -d`

### Database/Redis connection errors

**Diagnosis:**
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec backend redis-cli -h redis ping
# Expected: PONG
```

**Solution:**
```bash
# Restart Redis
docker-compose restart redis

# Or rebuild
docker-compose up -d --force-recreate redis
```

---

## Frontend Issues

### Frontend shows blank page

**Diagnosis:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Check Network tab for failed requests

**Common Causes:**

1. **Build failed**
   - Run: `docker-compose logs frontend`
   - Look for build errors
   - Solution: Fix errors, rebuild: `docker-compose build --no-cache frontend`

2. **API requests failing**
   - Check backend is running: `curl http://localhost:8000/health`
   - Check network requests in browser DevTools
   - Verify proxy configuration in `vite.config.ts`

3. **Environment variables missing**
   - Frontend uses `VITE_API_BASE_URL` and `VITE_WS_URL`
   - These are set at BUILD time in `docker-compose.yml`
   - Changes require rebuild: `docker-compose build --no-cache frontend`

### Frontend hot reload not working

**Symptom:** Changes to `.tsx` files don't appear in browser

**Cause:** Volume mount not configured

**Solution:**
1. Verify `docker-compose.yml` has:
```yaml
frontend:
  command: npm run dev -- --host 0.0.0.0
  volumes:
    - ./frontend/src:/app/src:rw
    - ./frontend/public:/app/public:ro
```

2. Restart: `docker-compose down && docker-compose up -d`

### TypeScript errors in browser

**Symptom:** Console shows `Cannot read property 'X' of undefined`

**Solution:**
1. Check `frontend/src/types/*.ts` for missing interfaces
2. Add null safety checks using optional chaining (`?.`)
3. Example fix:
```typescript
// Before (crashes if undefined)
const port = model.portRange.start

// After (safe)
const port = model.portRange?.start ?? 8080
```

---

## Model Management Issues

### No models discovered

**Symptom:** Model registry is empty (`[]`)

**Diagnosis:**
```bash
# Check model scan path
docker-compose exec backend python -c "
from app.core.config import load_config
config = load_config()
print(config.model_management.scan_path)
"

# Verify path exists and contains GGUF files
docker-compose exec backend ls /models
```

**Solution:**
1. Ensure `MODEL_SCAN_PATH` in `.env` points to valid directory
2. Verify directory contains `.gguf` files
3. Re-scan models:
```bash
curl -X POST http://localhost:8000/api/models/rescan
```

### Models won't start

**Symptom:** Click "START ALL" but servers don't launch

**Diagnosis:**
```bash
# Check backend logs during startup
docker-compose logs -f backend

# Check if llama-server binary exists
docker-compose exec backend which /usr/local/bin/llama-server

# Check if ports are available
lsof -i :8080-8099
```

**Common Causes:**

1. **llama-server binary missing**
   - Solution: Install llama.cpp and set `LLAMA_SERVER_PATH` in `.env`

2. **Port conflicts**
   - Solution: Change `MODEL_PORT_RANGE_START` and `_END` in `.env`

3. **Model file not found**
   - Solution: Verify GGUF files exist at paths in registry

4. **Insufficient memory**
   - Solution: Stop unused models, use smaller quantizations (Q2, Q4)

### Model stuck in "starting" state

**Symptom:** Model shows "STARTING" indefinitely

**Diagnosis:**
```bash
# Check backend logs for specific model
docker-compose logs backend | grep <model_id>

# Check if llama-server process exists
docker-compose exec backend ps aux | grep llama-server
```

**Solution:**
```bash
# Stop the stuck model
curl -X POST http://localhost:8000/api/models/servers/<model_id>/stop

# Wait 5 seconds, then restart
curl -X POST http://localhost:8000/api/models/servers/<model_id>/start
```

**Prevention:** Increase `MAX_STARTUP_TIME` in `.env` if models are large (>7B parameters)

---

## CGRAG Issues

### CGRAG returns no results

**Symptom:** Queries return empty `cgragArtifacts: []`

**Diagnosis:**
```bash
# Check if FAISS index exists
docker-compose exec backend ls -lh /data/faiss_indexes/

# Check backend logs for CGRAG errors
docker-compose logs backend | grep -i cgrag
```

**Solution:**
1. **Index doesn't exist** → Index documentation:
```bash
docker-compose run --rm backend python -m app.cli.index_docs /docs
```

2. **Min relevance too high** → Lower threshold in `.env`:
```bash
CGRAG_MIN_RELEVANCE=0.5  # Default: 0.7
```

3. **Token budget too small** → Increase budget:
```bash
CGRAG_TOKEN_BUDGET=12000  # Default: 8000
```

### CGRAG indexing fails

**Symptom:** `index_docs` command crashes or produces no output

**Diagnosis:**
```bash
# Run with verbose output
docker-compose run --rm backend python -m app.cli.index_docs /docs --verbose
```

**Common Causes:**

1. **No supported files found**
   - Supported: `.md`, `.py`, `.txt`, `.yaml`, `.json`, `.rst`
   - Solution: Verify documentation directory contains these file types

2. **Memory exhausted**
   - Solution: Reduce batch size in `backend/app/services/cgrag.py`

3. **Embedding model download failed**
   - Solution: Ensure internet access, retry indexing

### CGRAG retrieval is slow (>100ms)

**Diagnosis:**
```bash
# Check retrieval timing in backend logs
docker-compose logs backend | grep "CGRAG retrieval"
```

**Optimization:**
1. Use IVF index for large datasets (>100k chunks)
2. Reduce `CGRAG_MAX_ARTIFACTS` in `.env`
3. Enable Redis caching for embeddings
4. Reduce `nprobe` value in `config/default.yaml`

---

## Query Processing Issues

### Two-stage mode returns errors

**Symptom:** Query fails with "No fast tier models available"

**Cause:** Two-stage requires at least:
- 1 FAST tier model (2B-7B)
- 1 BALANCED (8B-14B) or POWERFUL (>14B) tier model

**Solution:**
1. Check available tiers:
```bash
curl http://localhost:8000/api/models/registry | jq '.models[] | {model_id, tier}'
```

2. Enable models from missing tiers
3. Start enabled models:
```bash
curl -X POST http://localhost:8000/api/models/servers/start-all
```

### Stage 2 always uses POWERFUL tier

**Symptom:** Even simple queries route to POWERFUL tier

**Diagnosis:**
```bash
# Check complexity thresholds
docker-compose exec backend python -c "
from app.core.config import load_config
config = load_config()
print(config.routing.complexity_thresholds)
"
```

**Solution:** Adjust complexity threshold in `config/default.yaml`:
```yaml
routing:
  complexity_thresholds:
    simple_max: 3.0
    moderate_max: 7.0  # Increase to route more queries to BALANCED
```

### Query timeout errors

**Symptom:** `HTTPException: Query processing timeout`

**Solution:**
1. Increase model timeout in profile config
2. Use faster model tier (FAST instead of POWERFUL)
3. Reduce `max_tokens` in query request
4. Check model health: `curl http://localhost:8000/api/models/servers`

---

## Performance Issues

### Slow Docker startup (>10 seconds)

**Expected:** ~5 seconds with no models loaded

**Diagnosis:**
```bash
# Time the startup
time docker-compose up -d

# Check if auto-start is enabled (should be FALSE)
docker-compose exec backend python -c "
from app.core.config import load_config
config = load_config()
print('Auto-start:', config.model_management.get('auto_start', False))
"
```

**Solution:** Ensure `backend/app/main.py` does NOT call `server_manager.start_server()` during startup

### Model startup is slow (>30 seconds)

**Expected:** 10-15 seconds per model

**Diagnosis:**
- Large models (>13B) take longer
- Slow disk I/O can delay loading
- Insufficient memory causes swapping

**Optimization:**
1. Use SSD for model storage
2. Increase Docker memory allocation
3. Use smaller quantizations (Q4 instead of Q8)
4. Enable concurrent startup (default in MAGI_REWORK)

### High memory usage

**Diagnosis:**
```bash
# Check container memory usage
docker stats

# Expected per model:
# - Q2_K: ~2-3GB
# - Q4_K: ~4-5GB
# - Q8: ~8-10GB
```

**Solution:**
1. Stop unused models via WebUI
2. Use smaller quantizations
3. Increase Docker memory limit
4. Don't run multiple POWERFUL models simultaneously

---

## Debugging Tools & Commands

### View live logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 50 lines
docker-compose logs --tail=50 backend

# Filter by keyword
docker-compose logs backend | grep -i error
```

### Execute commands in containers

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell (nginx doesn't have bash, use sh)
docker-compose exec frontend sh

# Run Python REPL in backend
docker-compose exec backend python

# Check backend config
docker-compose exec backend python -c "
from app.core.config import load_config
import json
config = load_config()
print(json.dumps(config.dict(), indent=2, default=str))
"
```

### Inspect model registry

```bash
# View registry JSON
docker-compose exec backend cat /app/data/model_registry.json | jq

# Count models by tier
docker-compose exec backend cat /app/data/model_registry.json | \
  jq '.models | group_by(.tier) | map({tier: .[0].tier, count: length})'
```

### Test API endpoints

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/api/models/registry | jq

# Check running servers
curl http://localhost:8000/api/models/servers | jq

# Start specific model
curl -X POST http://localhost:8000/api/models/servers/<model_id>/start

# Submit query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is MAGI?",
    "mode": "simple",
    "use_context": false
  }' | jq
```

### Monitor resource usage

```bash
# Real-time resource monitoring
docker stats

# Disk usage
docker system df

# Detailed disk usage
docker system df -v

# Clean up unused resources
docker system prune -a --volumes
```

---

## Known Issues

### 1. Health check error on startup

**Issue:** `ValueError: min() arg is an empty sequence` appears in backend logs at startup

**Status:** ⚠️ Minor - Does not affect functionality

**Impact:** Error logged once when zero models are running

**Workaround:** Ignore the error. It disappears once models are started.

**Fix:** Add guard clause in `backend/app/services/models.py` line 143 (optional)

---

### 2. Frontend hot reload requires full page refresh

**Issue:** Some React component changes require manual browser refresh

**Status:** ⚠️ Minor - Known Vite/Docker limitation

**Impact:** Occasional need to refresh browser manually

**Workaround:** Press `Ctrl+R` or `F5` to refresh browser after editing components

**Fix:** Configure Vite dev server with `server.watch.usePolling: true` (impacts performance)

---

### 3. Large model startup exceeds timeout

**Issue:** Models >13B parameters may exceed default 120s startup timeout

**Status:** ✅ Configurable

**Impact:** Startup fails with timeout error

**Solution:** Increase `MAX_STARTUP_TIME` in `.env`:
```bash
MAX_STARTUP_TIME=180  # 3 minutes for very large models
```

---

### 4. CGRAG index requires rebuild after code changes

**Issue:** Changes to chunking logic don't automatically reindex

**Status:** ⚠️ By design - Prevents accidental data loss

**Impact:** Need to manually reindex after chunking changes

**Solution:** Rebuild index when changing `CGRAG_CHUNK_SIZE` or `CGRAG_CHUNK_OVERLAP`:
```bash
# Backup old index
docker-compose exec backend cp -r /data/faiss_indexes /data/faiss_indexes.bak

# Rebuild index
docker-compose run --rm backend python -m app.cli.index_docs /docs
```

---

## Emergency Procedures

### Complete system reset

```bash
# WARNING: This deletes ALL data (registry, indexes, caches)

# 1. Stop all containers
docker-compose down -v

# 2. Remove built images
docker-compose down --rmi all

# 3. Clean Docker system
docker system prune -a --volumes

# 4. Rebuild from scratch
docker-compose build --no-cache

# 5. Start fresh
docker-compose up -d

# 6. Verify health
docker-compose ps
curl http://localhost:8000/health
```

### Restore from backup

```bash
# 1. Stop containers
docker-compose down

# 2. Restore model registry
cp backup/model_registry.json backend/data/model_registry.json

# 3. Restore FAISS indexes
cp -r backup/faiss_indexes backend/data/faiss_indexes

# 4. Restart
docker-compose up -d
```

---

## Understanding MAGI Architecture

### Where do models actually run?

**MAGI uses a hybrid Docker + host resources approach:**

```
┌─────────────────────────────────────────────────┐
│  HOST MACHINE (Your Computer)                   │
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │  Docker Container: backend             │     │
│  │                                         │     │
│  │  ┌─────────────────┐                   │     │
│  │  │ FastAPI Server  │                   │     │
│  │  │ - Routing       │                   │     │
│  │  │ - CGRAG         │                   │     │
│  │  │ - Orchestration │                   │     │
│  │  └─────────────────┘                   │     │
│  │                                         │     │
│  │  ┌─────────────────────────────────┐   │     │
│  │  │ llama-server processes          │   │     │
│  │  │ :8080, :8081, :8082...          │   │     │
│  │  │ (uses host GPU/CPU)             │   │     │
│  │  └─────────────────────────────────┘   │     │
│  │          ▲                              │     │
│  │          │ bind mount                   │     │
│  └──────────┼──────────────────────────────┘     │
│             │                                     │
│  ┌──────────▼──────────────────┐                 │
│  │ /usr/local/bin/llama-server │ ◄── Your binary │
│  └─────────────────────────────┘                 │
│                                                   │
│  ┌──────────────────────────────────┐            │
│  │ ~/.cache/huggingface/hub/        │ ◄── Models │
│  │ - model1.gguf                    │            │
│  │ - model2.gguf                    │            │
│  └──────────────────────────────────┘            │
└───────────────────────────────────────────────────┘
```

**Key Points:**

1. **Orchestration runs in Docker** - FastAPI, routing, CGRAG all containerized
2. **Models run in Docker but use host resources** - llama-server binary and GGUF files are bind-mounted from host
3. **Full GPU/CPU performance** - Models access your actual hardware, not virtualized resources
4. **No file duplication** - Model files stay on host, no copying into containers

### Docker Networking Rules

**❌ WRONG (common mistake):**
```typescript
// In vite.config.ts (inside Docker container)
target: 'http://localhost:8000'  // ❌ Points to container itself!
```

**✅ CORRECT:**
```typescript
// Use Docker service names for inter-container communication
target: 'http://backend:8000'    // ✅ Points to backend container
```

**Why?**
- Inside a Docker container, `localhost` refers to **that specific container**, not the host machine
- Docker Compose creates a network where containers communicate using **service names**
- `backend` is the service name defined in `docker-compose.yml`

**Exception:** Host machine → containers
```bash
# From your terminal (outside Docker), use localhost
curl http://localhost:8000/health  # ✅ Works! Port is exposed to host
```

---

## Getting Help

### Check documentation

1. [README.md](README.md) - Project overview and quick start
2. [MAGI_REWORK.md](MAGI_REWORK.md) - Implementation details and progress
3. [docs/features/MODES.md](docs/features/MODES.md) - Query mode documentation
4. [docs/features/DYNAMIC_CONTROL.md](docs/features/DYNAMIC_CONTROL.md) - Model management guide

### Debugging checklist

Before asking for help, verify:

- [ ] All containers are running: `docker-compose ps`
- [ ] Backend health check passes: `curl http://localhost:8000/health`
- [ ] Model registry exists: `ls backend/data/model_registry.json`
- [ ] At least one model discovered: `curl http://localhost:8000/api/models/registry | jq '.models | length'`
- [ ] Configuration files are valid YAML
- [ ] `.env` file exists and has correct paths
- [ ] Docker has sufficient memory (>=8GB recommended)
- [ ] Logs checked for specific error messages: `docker-compose logs`

### Reporting issues

Include the following information:

1. **System info:**
```bash
docker --version
docker-compose --version
uname -a
```

2. **Container status:**
```bash
docker-compose ps
```

3. **Recent logs:**
```bash
docker-compose logs --tail=100 > debug_logs.txt
```

4. **Configuration:**
```bash
cat .env  # Redact sensitive values
cat config/profiles/development.yaml
```

5. **Steps to reproduce** the issue

---

**Last Updated:** 2025-11-04
**Version:** 1.0
**Maintained by:** MAGI Engineering Team
