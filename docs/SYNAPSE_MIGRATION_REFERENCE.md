# S.Y.N.A.P.S.E. ENGINE Migration Reference

**Status:** Phases 1 & 2 Complete
**Date:** 2025-11-07

This document provides a quick reference for the MAGI → S.Y.N.A.P.S.E. ENGINE migration.

## Service Name Mappings

| Old Name | New Name | Component |
|----------|----------|-----------|
| `redis` | `synapse_redis` | CORE:MEMEX (Cache & Session Store) |
| `searxng` | `synapse_recall` | NODE:RECALL (CGRAG + SearXNG) |
| `host-api` | `synapse_host_api` | NODE:NEURAL (Metal Server Manager) |
| `backend` | `synapse_core` | CORE:PRAXIS (FastAPI Orchestrator) |
| `frontend` | `synapse_frontend` | CORE:INTERFACE (React Terminal UI) |

## Environment Variable Mappings

### CORE:PRAXIS (FastAPI Orchestrator)

| Old Variable | New Variable |
|--------------|--------------|
| `MAGI_PROFILE` | `PRAXIS_PROFILE` |
| `BACKEND_HOST` | `PRAXIS_HOST` |
| `BACKEND_PORT` | `PRAXIS_PORT` |
| `MODEL_SCAN_PATH` | `PRAXIS_MODEL_PATH` |
| `LLAMA_SERVER_PATH` | `PRAXIS_LLAMA_SERVER_PATH` |
| `REGISTRY_PATH` | `PRAXIS_REGISTRY_PATH` |
| `MODEL_PORT_RANGE_START` | `PRAXIS_PORT_RANGE_START` |
| `MODEL_PORT_RANGE_END` | `PRAXIS_PORT_RANGE_END` |
| `MODEL_MAX_STARTUP_TIME` | `PRAXIS_MAX_STARTUP_TIME` |
| `MODEL_CONCURRENT_STARTS` | `PRAXIS_CONCURRENT_STARTS` |

### CORE:MEMEX (Redis Cache & Session Store)

| Old Variable | New Variable |
|--------------|--------------|
| `REDIS_HOST` | `MEMEX_HOST` |
| `REDIS_PORT` | `MEMEX_PORT` |
| `REDIS_PASSWORD` | `MEMEX_PASSWORD` |
| `REDIS_DB` | `MEMEX_DB` |
| `REDIS_URL` | `MEMEX_URL` |
| N/A | `MEMEX_TTL` (new) |

### NODE:NEURAL (Host API - Metal Server Management)

| Old Variable | New Variable |
|--------------|--------------|
| `USE_EXTERNAL_SERVERS` | `NEURAL_USE_EXTERNAL` |
| `HOST_API_URL` | `NEURAL_ORCH_URL` |

### NODE:RECALL (CGRAG - Contextual Retrieval)

| Old Variable | New Variable |
|--------------|--------------|
| `CGRAG_INDEX_PATH` | `RECALL_INDEX_PATH` |
| `FAISS_INDEX_PATH` | `RECALL_FAISS_DEFAULT` |
| `EMBEDDING_MODEL` | `RECALL_EMBEDDING_MODEL` |
| `CGRAG_EMBEDDING_MODEL` | ~~(removed)~~ |
| `EMBEDDING_CACHE_ENABLED` | `RECALL_EMBEDDING_CACHE` |
| `CGRAG_CHUNK_SIZE` | `RECALL_CHUNK_SIZE` |
| `CGRAG_CHUNK_OVERLAP` | `RECALL_CHUNK_OVERLAP` |
| `CGRAG_TOKEN_BUDGET` | `RECALL_TOKEN_BUDGET` |
| `CGRAG_MIN_RELEVANCE` | `RECALL_MIN_RELEVANCE` |
| N/A | `RECALL_MAX_SHARDS` (new) |

### CORE:INTERFACE (React Frontend)

| Old Variable | New Variable |
|--------------|--------------|
| `VITE_API_BASE_URL` | `IFACE_API_BASE_URL` |
| `VITE_WS_URL` | `IFACE_WS_URL` |
| N/A | `IFACE_PORT` (new) |

## Docker Commands Update

### Old Commands
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose run --rm backend python -m app.cli.discover_models
```

### New Commands
```bash
docker-compose logs -f synapse_core
docker-compose logs -f synapse_frontend
docker-compose run --rm synapse_core python -m app.cli.discover_models
```

## Code Update Checklist

### Backend (Python)
- [ ] Replace `os.getenv("MAGI_PROFILE")` with `os.getenv("PRAXIS_PROFILE")`
- [ ] Replace `os.getenv("BACKEND_HOST")` with `os.getenv("PRAXIS_HOST")`
- [ ] Replace `os.getenv("BACKEND_PORT")` with `os.getenv("PRAXIS_PORT")`
- [ ] Update all `MODEL_*` references to `PRAXIS_*`
- [ ] Update all `REDIS_*` references to `MEMEX_*`
- [ ] Update all `CGRAG_*` references to `RECALL_*`
- [ ] Update `USE_EXTERNAL_SERVERS` to `NEURAL_USE_EXTERNAL`
- [ ] Update `HOST_API_URL` to `NEURAL_ORCH_URL`
- [ ] Update `EMBEDDING_MODEL` to `RECALL_EMBEDDING_MODEL`
- [ ] Update `EMBEDDING_CACHE_ENABLED` to `RECALL_EMBEDDING_CACHE`

### Frontend (TypeScript)
- [ ] Replace `import.meta.env.VITE_API_BASE_URL` with `import.meta.env.IFACE_API_BASE_URL`
- [ ] Replace `import.meta.env.VITE_WS_URL` with `import.meta.env.IFACE_WS_URL`
- [ ] Update vite.config.ts to read `IFACE_*` variables

### Scripts
- [ ] Update all service name references in shell scripts
- [ ] Update docker-compose commands
- [ ] Update log viewing scripts

### Documentation
- [ ] Update README.md with new service names
- [ ] Update any API documentation
- [ ] Update troubleshooting guides

## Network References

| Old Network | New Network |
|-------------|-------------|
| `magi_net` | `synapse_net` |
| `magi_network` | `synapse_network` |

## Volume References

| Old Volume | New Volume |
|------------|------------|
| `magi_redis_data` | `synapse_redis_data` |

## Validation Tests

Run these commands to verify the migration:

```bash
# Test 1: Check for old service names (should return nothing)
grep -v "^#" docker-compose.yml | grep -i "magi"

# Test 2: Check for old environment variables (should return nothing)
grep -v "^#" .env.example | grep -i "magi"

# Test 3: Validate docker-compose syntax
docker-compose config > /dev/null

# Test 4: Check all services use synapse_* pattern
grep "^  [a-z_]*:" docker-compose.yml | grep -A1 "services:" | tail -n +2
```

## Canonical Naming Scheme

**Service Naming:** `synapse_<component>`

**Environment Variables:** `<PREFIX>_<DESCRIPTOR>`

Prefixes:
- `PRAXIS_*` - Core orchestration and model management
- `MEMEX_*` - Redis cache and session storage
- `RECALL_*` - CGRAG and contextual retrieval
- `NEURAL_*` - Host API and Metal server management
- `IFACE_*` - Frontend interface configuration

## Backward Compatibility

**BREAKING CHANGE:** This is a hard cutover with NO backward compatibility.

All old variable names must be updated in:
1. Backend Python code
2. Frontend TypeScript code
3. Shell scripts
4. Documentation
5. CI/CD pipelines

## Next Steps

See [SYNAPSE_MIGRATION_PHASES.md](./SYNAPSE_MIGRATION_PHASES.md) for:
- Phase 3: Backend Code Updates
- Phase 4: Frontend Code Updates
- Phase 5: Scripts & Documentation Updates
- Phase 6: Testing & Validation
