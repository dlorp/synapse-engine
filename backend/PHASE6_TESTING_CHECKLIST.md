# Phase 6: Integration & Testing - Testing Checklist

## Overview
This checklist tracks the testing and verification of Phase 6 integration.

## Pre-Test Setup

- [ ] Model registry exists at `data/model_registry.json` (or will be created)
- [ ] Profiles exist in `config/profiles/` directory
- [ ] Environment variables configured in `.env`
- [ ] `llama-server` binary available at configured path

## Unit Tests

### StartupService
- [ ] `__init__` initializes with correct defaults
- [ ] `initialize()` completes without errors
- [ ] `_discover_models()` loads cached registry
- [ ] `_discover_models()` performs fresh discovery if no cache
- [ ] `_load_profile()` loads correct profile from environment
- [ ] `_filter_enabled_models()` returns only enabled models
- [ ] `_launch_servers()` starts servers for enabled models
- [ ] `_health_check()` validates server readiness
- [ ] `shutdown()` stops all servers gracefully

### Configuration Integration
- [ ] `ModelManagementConfig` loads from YAML
- [ ] Environment variables override config defaults
- [ ] Port range validates correctly
- [ ] Paths resolve correctly (development vs Docker)

## Integration Tests

### Startup Sequence
- [ ] Registry loads from cache on second run
- [ ] Profile loads correctly based on `PRAXIS_PROFILE` env var
- [ ] Only enabled models from profile are started
- [ ] Servers bind to correct ports
- [ ] Health checks pass for all started servers
- [ ] Startup logs are clear and informative

### Service Exposure
- [ ] `startup_service` is accessible globally
- [ ] `model_registry` is accessible in routers
- [ ] `server_manager` is accessible in routers
- [ ] `profile_manager` is accessible in routers
- [ ] `discovery_service` is accessible in routers

### Shutdown Sequence
- [ ] All servers stop gracefully
- [ ] No orphaned processes remain
- [ ] Shutdown completes within timeout
- [ ] Cleanup happens in correct order

## API Endpoint Tests

### Model Management Endpoints
- [ ] `GET /api/models/registry` returns full registry
- [ ] `GET /api/models/active` returns only running servers
- [ ] `GET /api/models/profile` returns active profile
- [ ] `PUT /api/models/profile` switches profiles
- [ ] Server status reflects actual health

### Legacy Compatibility
- [ ] `GET /api/models/status` still works (legacy ModelManager)
- [ ] Existing query endpoints still function
- [ ] WebSocket connections still work

## Profile Tests

### Development Profile
- [ ] Loads all available models
- [ ] Starts servers for all enabled models
- [ ] Resource usage is acceptable

### Production Profile
- [ ] Loads only Q3 and Q4 models
- [ ] Q2 models are NOT started
- [ ] Performance meets targets

### Fast-Only Profile
- [ ] Loads only Q2 models
- [ ] Multiple Q2 instances start correctly
- [ ] Load balancing works across instances

## Docker Integration Tests

- [ ] Container starts successfully
- [ ] Model paths mount correctly
- [ ] `llama-server` binary is accessible
- [ ] Servers bind to 0.0.0.0 (not localhost)
- [ ] Health checks work from host machine
- [ ] Environment variables propagate correctly

## Error Handling Tests

- [ ] Graceful handling when registry missing
- [ ] Graceful handling when profile missing
- [ ] Graceful handling when model files missing
- [ ] Graceful handling when `llama-server` missing
- [ ] Graceful handling when port already in use
- [ ] Graceful handling when server fails to start
- [ ] Degraded functionality mode works

## Performance Tests

- [ ] Startup completes within 2 minutes
- [ ] Concurrent server starts complete faster than sequential
- [ ] Health checks don't block startup
- [ ] Memory usage is acceptable with all models loaded
- [ ] Shutdown completes within 30 seconds

## Logging Tests

- [ ] Startup logs show clear progress (1/5, 2/5, etc.)
- [ ] Model discovery logs model counts
- [ ] Profile loading logs profile name and description
- [ ] Server launch logs each server start
- [ ] Health check logs ready/total counts
- [ ] Shutdown logs cleanup progress
- [ ] Errors include sufficient context for debugging

## Documentation Tests

- [ ] `.env.example` includes all required variables
- [ ] `default.yaml` documents model_management section
- [ ] Code docstrings are complete and accurate
- [ ] Type hints are present on all functions
- [ ] Error messages are clear and actionable

## Test Script Execution

Run the test script and verify:

```bash
cd backend
python test_full_startup.py
```

- [ ] Profile loading test passes
- [ ] Full startup sequence test passes
- [ ] Registry is loaded or created
- [ ] Profile loads correctly
- [ ] Enabled models match profile
- [ ] Servers launch successfully
- [ ] Health checks pass
- [ ] Shutdown completes cleanly
- [ ] No errors or warnings (except expected)

## Manual Verification

- [ ] Backend starts with `uvicorn app.main:app`
- [ ] Logs show complete startup sequence
- [ ] Model servers are accessible at their ports
- [ ] WebUI can connect to backend
- [ ] Query execution works end-to-end
- [ ] Profile switching works via API
- [ ] Servers restart when profile changes

## Sign-Off

- [ ] All critical tests passed
- [ ] All integration tests passed
- [ ] Performance meets requirements
- [ ] Documentation is complete
- [ ] Code review completed
- [ ] Ready for production deployment

---

## Notes

Document any issues, workarounds, or observations during testing:

```
[Add notes here]
```

## Test Results

| Test Category | Pass/Fail | Notes |
|---------------|-----------|-------|
| Unit Tests | | |
| Integration Tests | | |
| API Endpoints | | |
| Profile Tests | | |
| Docker Integration | | |
| Error Handling | | |
| Performance | | |
| Logging | | |
| Documentation | | |

---

**Tested by:** _____________
**Date:** _____________
**Sign-off:** _____________
