# S.Y.N.A.P.S.E. ENGINE Testing Guide

## Automated Test Suite Overview

This document describes the comprehensive automated test suite for the S.Y.N.A.P.S.E. ENGINE Multi-Model Orchestration WebUI project. All tests run through Docker containers to ensure consistency with the production environment.

---

## Test Scripts

### 1. **test-backend.sh** - Backend API Testing

**Location:** [`../scripts/test-backend.sh`](../scripts/test-backend.sh)

**Purpose:** Verify backend FastAPI application functionality, API endpoints, Python tests, and container health.

**Tests Performed (10 checks):**

1. **Health Endpoint** - Verify `/health` returns 200 OK
2. **Model Registry API** - Test `/api/models/registry` endpoint
3. **Model Status API** - Test `/api/models/status` endpoint
4. **Server Status API** - Test `/api/models/servers` endpoint
5. **CGRAG Status API** - Test `/api/cgrag/status` endpoint
6. **Settings API** - Test `/api/settings` endpoint
7. **API Documentation** - Verify `/docs` is accessible
8. **Python Test Scripts** - Run all `test_*.py` files in `backend/` directory
9. **Backend Logs** - Scan for errors in recent logs
10. **Container Health** - Verify backend container is running and healthy

**Usage:**
```bash
./scripts/test-backend.sh
```

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

---

### 2. **test-frontend.sh** - Frontend React Testing

**Location:** [`../scripts/test-frontend.sh`](../scripts/test-frontend.sh)

**Purpose:** Verify frontend React application, Vite configuration, build setup, and container health.

**Tests Performed (8 checks):**

1. **HTTP Response** - Verify `http://localhost:5173` returns 200 OK
2. **Valid HTML** - Check for `<!DOCTYPE html>` in response
3. **React Root Element** - Verify `<div id="root"></div>` exists
4. **Vite Config Files** - Check for `vite.config.ts`, `package.json`, `tsconfig.json`
5. **npm Test** - Run `npm test -- --run` (skips if no tests defined)
6. **Static Assets** - Verify Vite client assets are loading
7. **Frontend Logs** - Scan for critical errors in logs
8. **Container Health** - Verify frontend container is running and healthy

**Usage:**
```bash
./scripts/test-frontend.sh
```

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

---

### 3. **test-integration.sh** - Integration Testing

**Location:** [`../scripts/test-integration.sh`](../scripts/test-integration.sh)

**Purpose:** Verify service integration, API proxying, WebSocket connectivity, and cross-service communication.

**Tests Performed (6 checks):**

1. **Backend-Frontend Communication** - Verify `VITE_API_BASE_URL` configuration and connectivity
2. **API Proxy** - Test API requests proxied through Vite dev server (`/api`)
3. **WebSocket Endpoint** - Verify `/ws` endpoint is accessible
4. **Redis Connectivity** - Test backend can communicate with Redis container
5. **Host API** - Test Host API connectivity (if `USE_EXTERNAL_SERVERS=true`)
6. **All Services Running** - Verify all required services are up (redis, backend, frontend, searxng, host-api)

**Usage:**
```bash
./scripts/test-integration.sh
```

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

---

### 4. **test-all.sh** - Master Test Runner

**Location:** [`../scripts/test-all.sh`](../scripts/test-all.sh)

**Purpose:** Execute all test suites with pre-flight checks and comprehensive reporting.

**Execution Flow:**

1. **Pre-Flight Checks:**
   - Docker daemon running
   - Docker Compose available
   - Project structure valid
   - Docker Compose configuration valid
   - Required services running (starts them if needed)
   - Test scripts executable

2. **Run Test Suites:**
   - Backend test suite
   - Frontend test suite
   - Integration test suite

3. **Final Summary:**
   - Per-suite pass/fail status
   - Total execution time
   - Comprehensive results display
   - Troubleshooting tips if failures

**Usage:**
```bash
./scripts/test-all.sh
```

**Exit Codes:**
- `0` - All test suites passed
- `1` - One or more test suites failed

---

## Output Format

All test scripts use:

- **Colored output:**
  - `GREEN` (✓) - Test passed
  - `RED` (✗) - Test failed
  - `YELLOW` (⚠) - Warning or skipped
  - `BLUE` - Section headers and informational messages

- **Progress indicators:**
  - `[1/10]`, `[2/10]`, etc. - Current test number / total tests

- **Test results:**
  - Clear pass/fail status for each test
  - Error details for failed tests
  - Summary at the end

---

## Quick Start

### Run All Tests (Recommended)

```bash
# From project root
./scripts/test-all.sh
```

This will:
1. Check that Docker is running
2. Verify services are up (starts them if needed)
3. Run all test suites
4. Provide comprehensive summary

### Run Individual Test Suites

```bash
# Backend only
./scripts/test-backend.sh

# Frontend only
./scripts/test-frontend.sh

# Integration only
./scripts/test-integration.sh
```

---

## Prerequisites

Before running tests, ensure:

1. **Docker Desktop is running**
   ```bash
   docker info
   ```

2. **Docker Compose is available**
   ```bash
   docker-compose version
   ```

3. **Services are running** (or let `test-all.sh` start them)
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to initialize** (typically 10-30 seconds)
   ```bash
   docker-compose ps
   ```

---

## Troubleshooting

### Services Not Running

If tests fail because services are down:
```bash
# Start all services
docker-compose up -d

# Wait for initialization
sleep 10

# Verify services are healthy
docker-compose ps
```

### Tests Failing After File Changes

If tests fail after reorganizing files:

1. **Rebuild containers:**
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Check logs for errors:**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

3. **Verify environment variables:**
   ```bash
   docker-compose config
   ```

### Port Conflicts

If services can't start due to port conflicts:
```bash
# Check what's using ports
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :6379  # Redis
lsof -i :9090  # Host API

# Kill conflicting processes or change ports in docker-compose.yml
```

See [`../docker-compose.yml`](../docker-compose.yml) to modify port mappings.

### Permission Issues

If scripts are not executable:
```bash
chmod +x scripts/test-*.sh
```

---

## Test Coverage

### What These Tests Verify

✅ **Backend:**
- All API endpoints return correct status codes
- Python integration tests run successfully
- No errors in backend logs
- Container is healthy

✅ **Frontend:**
- Vite dev server is serving content
- HTML structure is valid
- React root element exists
- Build configuration is correct
- No critical errors in logs
- Container is healthy

✅ **Integration:**
- Backend and frontend can communicate
- API proxy is configured correctly
- WebSocket endpoint is accessible
- Redis is connected and operational
- Host API is available (if enabled)
- All required services are running

### What These Tests Don't Cover

❌ **End-to-End User Flows:**
- Query submission and response
- Model switching
- Settings persistence
- CGRAG retrieval accuracy

❌ **Performance Testing:**
- Response time benchmarks
- Load testing
- Concurrent request handling

❌ **Security Testing:**
- Authentication/authorization
- Input validation
- SQL injection, XSS, etc.

For comprehensive E2E testing, use Playwright (future enhancement).

---

## CI/CD Integration

These scripts are designed to be run in CI/CD pipelines:

**GitHub Actions Example:**
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: sleep 30
      - name: Run tests
        run: ./scripts/test-all.sh
```

---

## Exit Codes Reference

All test scripts use consistent exit codes:

- **0** - Success (all tests passed)
- **1** - Failure (one or more tests failed)

This makes them suitable for CI/CD pipelines and automation.

---

## Maintenance

### Adding New Tests

**Backend Test:**
1. Add test function to [`test-backend.sh`](../scripts/test-backend.sh)
2. Increment `TOTAL_TESTS` variable
3. Call function in `main()`

**Frontend Test:**
1. Add test function to [`test-frontend.sh`](../scripts/test-frontend.sh)
2. Increment `TOTAL_TESTS` variable
3. Call function in `main()`

**Integration Test:**
1. Add test function to [`test-integration.sh`](../scripts/test-integration.sh)
2. Increment `TOTAL_TESTS` variable
3. Call function in `main()`

### Test Function Template

```bash
test_example() {
    local test_num=X
    print_test $test_num "Test description"

    # Perform test
    local result
    result=$(test_command 2>&1)

    if [ condition ]; then
        print_success $test_num "Success message"
    else
        print_failure $test_num "Failure message" "Details: $result"
    fi
}
```

---

## Best Practices

1. **Run tests before committing:**
   ```bash
   ./scripts/test-all.sh && git commit
   ```

2. **Run tests after file reorganization:**
   ```bash
   # After moving/renaming files
   docker-compose build --no-cache
   ./scripts/test-all.sh
   ```

3. **Use individual scripts during development:**
   ```bash
   # Working on backend
   ./scripts/test-backend.sh

   # Working on frontend
   ./scripts/test-frontend.sh
   ```

4. **Check logs if tests fail:**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

---

## Summary

The S.Y.N.A.P.S.E. ENGINE test suite provides comprehensive verification that:

- ✅ Backend API is functional and healthy
- ✅ Frontend is serving correctly
- ✅ Services can communicate
- ✅ Docker environment is properly configured
- ✅ File reorganization didn't break functionality

**Total Test Coverage:** 24 automated checks across 3 test suites

**Estimated Execution Time:** 30-60 seconds (depending on system performance)

**Maintenance:** Scripts are self-contained and easy to extend with new tests

For questions or issues, refer to the troubleshooting section or check Docker logs.
