# Migration Guide: Phase 6 Integration

## Overview

This guide helps you migrate from manual model configuration to the new automated model management system introduced in Phase 6.

## What Changed

### Before Phase 6 (Manual Configuration)

```yaml
# config/default.yaml
models:
  Q2_FAST_1:
    name: "Q2_FAST_1"
    tier: "Q2"
    url: "http://localhost:8080/v1"
    port: 8080
    max_context_tokens: 32768
```

**Manual Steps Required:**
1. Start each llama.cpp server manually
2. Configure each server in YAML
3. Manage server lifecycle yourself
4. No automatic discovery

### After Phase 6 (Automated Management)

```yaml
# config/profiles/development.yaml
name: "development"
enabled_models:
  - deepseek-r1-qwen3-8b-q2_k
  - deepseek-r1-qwen3-8b-q3_k_m
```

```bash
export MAGI_PROFILE=development
uvicorn app.main:app
```

**Automated:**
1. Discovers models automatically
2. Starts servers based on profile
3. Manages lifecycle completely
4. Health checks included

## Migration Steps

### Step 1: Backup Current Configuration

```bash
cp config/default.yaml config/default.yaml.backup
cp .env .env.backup
```

### Step 2: Run Model Discovery

Discover all available models:

```bash
cd backend
python3 -m app.services.model_discovery
```

This creates `data/model_registry.json`:

```json
{
  "models": {
    "deepseek-r1-qwen3-8b-q2_k": {
      "model_id": "deepseek-r1-qwen3-8b-q2_k",
      "file_path": "/path/to/model.gguf",
      "file_size": 3500000000,
      "quantization": "Q2_K",
      "tier": "Q2",
      "port": 8080
    }
  }
}
```

### Step 3: Create or Verify Profiles

Check existing profiles:

```bash
ls -la config/profiles/
# development.yaml
# production.yaml
# fast-only.yaml
```

Or create custom profile:

```bash
cat > config/profiles/custom.yaml << EOF
name: "custom"
description: "My custom profile"
enabled_models:
  - deepseek-r1-qwen3-8b-q2_k
  - deepseek-r1-qwen3-8b-q3_k_m
  - deepseek-r1-qwen3-8b-q4_k_m
EOF
```

### Step 4: Update Environment Variables

Add to `.env`:

```bash
# MAGI Profile
MAGI_PROFILE=development

# Model Management
MODEL_SCAN_PATH=/Users/dperez/Documents/LLM/llm-models/HUB/
LLAMA_SERVER_PATH=/usr/local/bin/llama-server
REGISTRY_PATH=data/model_registry.json
MODEL_CONCURRENT_STARTS=true
```

### Step 5: Update docker-compose.yml (if using Docker)

Add environment variables:

```yaml
services:
  backend:
    environment:
      - MAGI_PROFILE=${MAGI_PROFILE:-development}
      - MODEL_SCAN_PATH=/models
      - LLAMA_SERVER_PATH=/usr/local/bin/llama-server
    volumes:
      - /path/to/models:/models:ro  # Mount model directory
```

### Step 6: Stop Manual Model Servers

If you were running llama.cpp servers manually:

```bash
# Find running servers
ps aux | grep llama-server

# Stop them
pkill -f llama-server

# Or kill by PID
kill -9 <PID>
```

### Step 7: Test New System

Run integration test:

```bash
cd backend
python3 test_full_startup.py
```

Expected output:
```
✅ Registry loaded: 8 models
✅ Profile loaded: development
✅ Enabled models: 4
✅ Servers running: 4
✅ Servers ready: 4
✅ ALL TESTS PASSED!
```

### Step 8: Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Watch for startup sequence in logs:
```
MAGI STARTUP SEQUENCE
[1/5] Model Discovery
[2/5] Loading profile 'development'
[3/5] Filtering enabled models
[4/5] Launching servers
[5/5] Health check
MAGI STARTUP COMPLETE
```

### Step 9: Verify API Endpoints

Check server status:

```bash
curl http://localhost:8000/api/models/management/servers
```

Test query:

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query", "mode": "auto"}'
```

### Step 10: Update Documentation

Update any internal documentation referencing:
- Manual server startup procedures
- Hardcoded model configurations
- Legacy environment variables

## Configuration Mapping

### Legacy to New Mapping

| Legacy Config | New Config | Notes |
|---------------|------------|-------|
| `models.Q2_FAST_1.name` | Profile `enabled_models` | Model ID from registry |
| `models.Q2_FAST_1.port` | Auto-assigned | From `port_range` |
| `models.Q2_FAST_1.url` | Auto-generated | `http://{host}:{port}/v1` |
| Manual server start | `startup_service` | Automatic |
| Manual health check | Built-in | Automatic |

### Environment Variable Changes

| Legacy Variable | New Variable | Default |
|-----------------|--------------|---------|
| N/A | `MAGI_PROFILE` | `development` |
| N/A | `MODEL_SCAN_PATH` | `/models` |
| N/A | `LLAMA_SERVER_PATH` | `/usr/local/bin/llama-server` |
| N/A | `REGISTRY_PATH` | `data/model_registry.json` |
| N/A | `MODEL_CONCURRENT_STARTS` | `true` |
| `MODEL_Q2_FAST_1_URL` | Generated | From registry |

## Rollback Plan

If you need to rollback:

### Option 1: Use Legacy Configuration

The system maintains backward compatibility. Legacy model configurations in `default.yaml` still work alongside the new system.

```yaml
# config/default.yaml - Legacy models still work
models:
  Q2_FAST_1:
    name: "Q2_FAST_1"
    tier: "Q2"
    url: "http://localhost:8080/v1"
    port: 8080
```

### Option 2: Restore Backup

```bash
cp config/default.yaml.backup config/default.yaml
cp .env.backup .env
rm data/model_registry.json
```

### Option 3: Disable Auto-Start

Set empty profile:

```bash
export MAGI_PROFILE=none
```

Start servers manually as before.

## Troubleshooting Migration

### Issue: "Profile not found"

**Cause:** Profile doesn't exist or wrong name

**Solution:**
```bash
# List available profiles
ls config/profiles/

# Use existing profile
export MAGI_PROFILE=development

# Or create custom profile
cp config/profiles/development.yaml config/profiles/myprofile.yaml
export MAGI_PROFILE=myprofile
```

### Issue: "No models discovered"

**Cause:** Scan path incorrect or no GGUF files

**Solution:**
```bash
# Check scan path
ls $MODEL_SCAN_PATH

# Verify GGUF files exist
find $MODEL_SCAN_PATH -name "*.gguf"

# Update scan path
export MODEL_SCAN_PATH=/correct/path/to/models

# Re-run discovery
python3 -m app.services.model_discovery
```

### Issue: "Server failed to start"

**Cause:** Port conflict, missing binary, or file permissions

**Solution:**
```bash
# Check port availability
lsof -i :8080

# Check llama-server binary
which llama-server
llama-server --version

# Check model file permissions
ls -la /path/to/model.gguf

# Check logs
tail -f /tmp/llama_server_8080.log
```

### Issue: "Models take too long to start"

**Cause:** Sequential startup or large models

**Solution:**
```bash
# Enable concurrent starts
export MODEL_CONCURRENT_STARTS=true

# Or reduce enabled models in profile
# Edit config/profiles/development.yaml
enabled_models:
  - deepseek-r1-qwen3-8b-q2_k  # Only enable needed models
```

### Issue: "Legacy endpoints broken"

**Cause:** Legacy ModelManager not initialized

**Solution:**
The system maintains both legacy and new systems. Check that `default.yaml` still has legacy model configurations for the `/api/models/status` endpoint.

## Best Practices

### Development Environment

Use `development` profile with all models:

```bash
export MAGI_PROFILE=development
```

### Staging Environment

Use `production` profile with Q3/Q4 only:

```bash
export MAGI_PROFILE=production
```

### Production Environment

Create custom profile with only required models:

```yaml
# config/profiles/production-optimized.yaml
name: "production-optimized"
description: "Production deployment - optimized"
enabled_models:
  - deepseek-r1-qwen3-8b-q3_k_m  # Primary
  - deepseek-r1-qwen3-8b-q4_k_m  # Complex queries
```

```bash
export MAGI_PROFILE=production-optimized
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Deploy Backend
  env:
    MAGI_PROFILE: ${{ secrets.MAGI_PROFILE }}
    MODEL_SCAN_PATH: /models
  run: |
    docker-compose up -d
```

## Validation Checklist

After migration, verify:

- [ ] Model discovery runs successfully
- [ ] Registry file created
- [ ] Profile loads correctly
- [ ] Servers start automatically
- [ ] Health checks pass
- [ ] Query execution works
- [ ] WebUI can connect
- [ ] Legacy endpoints still work (if needed)
- [ ] Logs show clear startup sequence
- [ ] Shutdown is graceful
- [ ] No manual intervention required

## Support

If you encounter issues during migration:

1. Check logs: `tail -f backend/logs/app.log`
2. Run test script: `python3 test_full_startup.py`
3. Follow troubleshooting guide in `QUICKSTART_PHASE6.md`
4. Review complete docs: `PHASE6_INTEGRATION_COMPLETE.md`

## Timeline

Recommended migration timeline:

- **Day 1:** Run discovery, verify registry
- **Day 2:** Test with development profile
- **Day 3:** Create custom profiles, test
- **Day 4:** Deploy to staging
- **Day 5:** Monitor and validate
- **Day 6:** Deploy to production

## Summary

Phase 6 migration brings:

- Automated model discovery
- Profile-based configuration
- Automatic server management
- Improved reliability
- Better Docker integration
- Easier deployment

Follow this guide step-by-step for a smooth migration.

---

**Questions?** See `PHASE6_INTEGRATION_COMPLETE.md` for detailed documentation.
