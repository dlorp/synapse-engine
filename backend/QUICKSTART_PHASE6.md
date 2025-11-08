# MAGI Phase 6 - Quick Start Guide

## Overview

Phase 6 completes the MAGI Model Management System with automated startup orchestration.

## Prerequisites

1. **Model files** - GGUF models in scan directory
2. **llama-server** - Binary installed and accessible
3. **Python 3.11+** - With FastAPI and dependencies
4. **Model registry** - Created via discovery (or will auto-create)
5. **Profiles** - In `config/profiles/` directory

## Quick Start

### 1. Set Environment Variables

Create `.env` from template:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Core settings
MAGI_PROFILE=development
MODEL_SCAN_PATH=${PRAXIS_MODEL_PATH}/
LLAMA_SERVER_PATH=/usr/local/bin/llama-server
```

### 2. Run Discovery (First Time Only)

Generate model registry:
```bash
cd backend
python3 -m app.services.model_discovery
```

This creates `data/model_registry.json` with all discovered models.

### 3. Verify Profiles

Check profiles exist:
```bash
ls -la config/profiles/
# Should see: development.yaml, production.yaml, fast-only.yaml
```

### 4. Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Watch startup logs:
```
MAGI STARTUP SEQUENCE
Profile: development
Time: 2025-11-03T14:30:00

[1/5] Model Discovery
✅ Discovered 8 models

[2/5] Loading profile 'development'
✅ Profile loaded: Development profile with all models

[3/5] Filtering enabled models
✅ 4 models enabled

[4/5] Launching servers
✅ Servers launched

[5/5] Health check
✅ All 4 servers ready!

MAGI STARTUP COMPLETE
```

### 5. Verify Servers Running

Check server status:
```bash
curl http://localhost:8000/api/models/management/servers
```

Should return:
```json
{
  "total_servers": 4,
  "ready_servers": 4,
  "servers": [...]
}
```

### 6. Test Query

Send a test query:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "mode": "auto"}'
```

## Running Tests

### Integration Test

Test complete startup sequence:
```bash
cd backend
python3 test_full_startup.py
```

Expected output:
```
TESTING MAGI STARTUP SEQUENCE
✅ Configuration loaded
✅ StartupService created
✅ Registry loaded: 8 models
✅ Profile loaded: development
✅ Enabled models: 4
✅ Servers running: 4
✅ Servers ready: 4
✅ Shutdown complete
ALL TESTS PASSED!
```

### Test Checklist

Follow comprehensive checklist:
```bash
cat PHASE6_TESTING_CHECKLIST.md
```

## Profile Switching

### Change Active Profile

Edit `.env`:
```bash
MAGI_PROFILE=production  # or fast-only
```

Restart backend:
```bash
uvicorn app.main:app --reload
```

### Available Profiles

**development** - All models enabled
```yaml
enabled_models:
  - deepseek-r1-qwen3-8b-q2_k
  - deepseek-r1-qwen3-8b-q3_k_m
  - deepseek-r1-qwen3-8b-q4_k_m
```

**production** - Q3 and Q4 only
```yaml
enabled_models:
  - deepseek-r1-qwen3-8b-q3_k_m
  - deepseek-r1-qwen3-8b-q4_k_m
```

**fast-only** - Q2 models only
```yaml
enabled_models:
  - deepseek-r1-qwen3-8b-q2_k
  - deepseek-r1-qwen3-8b-q2_k  # Multiple instances
```

## Common Tasks

### Add New Model

1. Place GGUF file in scan directory
2. Run discovery:
   ```bash
   python3 -m app.services.model_discovery
   ```
3. Add to profile:
   ```yaml
   enabled_models:
     - new-model-id
   ```
4. Restart backend

### Create Custom Profile

1. Create profile file:
   ```bash
   cp config/profiles/development.yaml config/profiles/custom.yaml
   ```

2. Edit profile:
   ```yaml
   name: "custom"
   description: "My custom profile"
   enabled_models:
     - model-1
     - model-2
   ```

3. Activate profile:
   ```bash
   export MAGI_PROFILE=custom
   ```

4. Restart backend

### View Registry

```bash
cat data/model_registry.json | python3 -m json.tool
```

### Check Server Logs

Individual server logs:
```bash
tail -f /tmp/llama_server_8080.log
tail -f /tmp/llama_server_8081.log
```

Backend logs:
```bash
tail -f backend/logs/app.log
```

## Troubleshooting

### "Profile not found"

```bash
# Check profile exists
ls config/profiles/development.yaml

# Check environment variable
echo $MAGI_PROFILE

# Use correct profile name
export MAGI_PROFILE=development
```

### "No models discovered"

```bash
# Check scan path
ls $MODEL_SCAN_PATH

# Verify GGUF files
find $MODEL_SCAN_PATH -name "*.gguf"

# Run discovery
python3 -m app.services.model_discovery
```

### "Server failed to start"

```bash
# Check llama-server binary
which llama-server

# Check port availability
lsof -i :8080

# Check model file
ls -la /path/to/model.gguf

# Check server logs
tail -f /tmp/llama_server_8080.log
```

### "Port already in use"

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or use different port range in config
```

## Docker Usage

### Build and Run

```bash
docker-compose up --build
```

### Environment Overrides

In `docker-compose.yml` or `.env`:
```yaml
environment:
  - MAGI_PROFILE=production
  - MODEL_SCAN_PATH=/models
  - LLAMA_SERVER_PATH=/usr/local/bin/llama-server
```

### Volume Mounts

```yaml
volumes:
  - /path/to/models:/models:ro
  - ./data:/app/data
```

## API Endpoints

### Model Management

**Get Registry:**
```bash
GET /api/models/registry
```

**Get Active Servers:**
```bash
GET /api/models/management/servers
```

**Get Active Profile:**
```bash
GET /api/models/profile
```

### Query Endpoints

**Submit Query:**
```bash
POST /api/query
{
  "query": "Your question",
  "mode": "auto"
}
```

### Health Check

```bash
GET /health
```

## Performance Tips

### Faster Startup

Use concurrent server starts (default):
```bash
MODEL_CONCURRENT_STARTS=true
```

### Reduce Startup Time

Use cached registry:
- Keep `data/model_registry.json`
- Only re-run discovery when models change

### Memory Management

Limit enabled models in profile:
- Use `fast-only` profile for low memory
- Use `production` profile for balanced load

## Key Files

```
MAGI/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   └── startup.py           # Startup orchestration
│   │   ├── models/
│   │   │   └── config.py            # Configuration models
│   │   └── main.py                   # FastAPI app with lifespan
│   ├── data/
│   │   └── model_registry.json       # Discovered models (cached)
│   ├── test_full_startup.py          # Integration test
│   └── PHASE6_TESTING_CHECKLIST.md   # Testing checklist
├── config/
│   ├── default.yaml                   # Default configuration
│   └── profiles/                      # Profile directory
│       ├── development.yaml
│       ├── production.yaml
│       └── fast-only.yaml
└── .env.example                       # Environment template
```

## Next Steps

1. ✅ Run discovery to generate registry
2. ✅ Configure environment variables
3. ✅ Test with `test_full_startup.py`
4. ✅ Start backend and verify servers
5. ✅ Test query execution
6. ✅ Integrate with WebUI
7. ✅ Deploy to production

## Support

- **Full Documentation:** `PHASE6_INTEGRATION_COMPLETE.md`
- **Testing Guide:** `PHASE6_TESTING_CHECKLIST.md`
- **Architecture:** `UPDATE_MAGI.md`

---

**Phase 6 Complete - System Ready for Production! 🚀**
