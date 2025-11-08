# MAGI Docker Quick Start Guide

Complete guide for running MAGI Multi-Model Orchestration WebUI in Docker with model management support.

**Quick Links:**
- [Docker Quick Reference](DOCKER_QUICK_REFERENCE.md) - One-page cheat sheet
- [Docker Infrastructure](../architecture/DOCKER_INFRASTRUCTURE.md) - Detailed architecture
- [Admin Quick Reference](ADMIN_QUICK_REFERENCE.md) - Admin panel for Docker testing
- [Project README](../../README.md) - Main documentation

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Mode](#development-mode)
- [Configuration](#configuration)
- [Model Management](#model-management)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Prerequisites

### Required Software

1. **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
   - Version 20.10.0 or higher
   - Download: https://docs.docker.com/get-docker/

2. **Docker Compose**
   - Version 2.0.0 or higher
   - Included with Docker Desktop
   - Linux: https://docs.docker.com/compose/install/

3. **llama.cpp llama-server binary**
   - Location: `/usr/local/bin/llama-server`
   - Build from: https://github.com/ggerganov/llama.cpp

### Required Data

1. **GGUF Model Files**
   - Location: `/Users/dperez/Documents/LLM/llm-models/HUB/`
   - At least one GGUF model file
   - Recommended: DeepSeek R1 Qwen3 8B in multiple quantizations

### System Requirements

- **RAM**: 8GB minimum (16GB+ recommended for multiple models)
- **CPU**: 4 cores minimum (8+ recommended)
- **Disk**: 10GB free space (more for model files)
- **OS**: macOS, Linux, or Windows with WSL2

---

## Quick Start

### 1. Automated Setup

Run the setup script to validate prerequisites and build images:

```bash
./scripts/docker-setup.sh
```

This script will:
- ✅ Check Docker and Docker Compose installation
- ✅ Validate HUB directory and llama-server binary
- ✅ Create required directories (data, logs)
- ✅ Build Docker images
- ✅ Display next steps

### 2. Discover Models

Scan your HUB directory for GGUF models:

```bash
docker-compose run --rm backend python -m app.cli.discover_models
```

This creates `backend/data/model_registry.json` with all discovered models.

### 3. Start Services

Start all services in production mode:

```bash
docker-compose up -d
```

Services started:
- **Redis**: Port 6379 (caching)
- **Backend**: Port 8000 (FastAPI)
- **Frontend**: Port 5173 (React UI)
- **Model Servers**: Ports 8080-8099 (llama.cpp)

### 4. Verify Services

Check service health:

```bash
docker-compose ps
```

All services should show status `Up` and `(healthy)`.

### 5. Access UI

Open your browser to:
- **Main UI**: http://localhost:5173
- **Model Management**: http://localhost:5173/model-management
- **API Docs**: http://localhost:8000/docs

---

## Development Mode

For local development with hot reload:

### 1. Setup for Development

```bash
./scripts/docker-setup.sh --dev
```

### 2. Start in Development Mode

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Development features:
- **Backend**: Uvicorn auto-reload on Python file changes
- **Frontend**: Vite HMR (Hot Module Replacement) for instant updates
- **Logging**: DEBUG level for detailed logs
- **Source Mounting**: Local code changes reflected immediately

### 3. Development Workflow

1. Edit code in `backend/app/` or `frontend/src/`
2. Changes auto-reload in containers
3. View logs: `docker-compose logs -f backend frontend`
4. Test changes immediately in browser

### 4. Stop Development Services

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

---

## Configuration

### Environment Variables

Create `.env` file in project root (or use defaults):

```bash
# Copy example file
cp .env.example .env

# Edit with your settings
nano .env
```

Key variables:

```bash
# Active Profile
MAGI_PROFILE=development  # or: production, fast-only

# Redis
REDIS_PASSWORD=change_this_secure_redis_password

# Model Management
MODEL_PORT_RANGE_START=8080
MODEL_PORT_RANGE_END=8099
MODEL_MAX_STARTUP_TIME=120

# Logging
LOG_LEVEL=INFO  # or: DEBUG, WARNING, ERROR

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Profile Selection

MAGI uses profiles to define which models to load. Available profiles:

#### 1. **development** (default)
- Loads Q2_FAST_1, Q2_FAST_2, Q3_SYNTH
- 4GB VRAM recommended
- Balanced performance

#### 2. **production**
- Loads all tiers (Q2_FAST_1, Q2_FAST_2, Q3_SYNTH, Q4_DEEP)
- 8GB+ VRAM recommended
- Full capabilities

#### 3. **fast-only**
- Loads only Q2_FAST_1, Q2_FAST_2
- 2GB VRAM recommended
- Quick responses only

Change profile:

```bash
# Option 1: Environment variable
export MAGI_PROFILE=production
docker-compose restart backend

# Option 2: Edit docker-compose.yml
# Change: MAGI_PROFILE=production
docker-compose restart backend

# Option 3: Runtime API call
curl -X POST http://localhost:8000/api/models/profile/activate \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "production"}'
```

### Customizing Paths

If your HUB or llama-server is in a different location, edit `docker-compose.yml`:

```yaml
services:
  backend:
    volumes:
      # Change HUB path
      - /YOUR/PATH/TO/HUB/:/models:ro

      # Change llama-server path
      - /YOUR/PATH/TO/llama-server:/usr/local/bin/llama-server:ro
```

---

## Model Management

### Discovery

Re-scan HUB directory for new models:

```bash
docker-compose run --rm backend python -m app.cli.discover_models
```

### View Discovered Models

```bash
# Via API
curl http://localhost:8000/api/models/registry | jq .

# Via CLI
docker-compose exec backend python -c "
import json
with open('data/model_registry.json') as f:
    registry = json.load(f)
    for model in registry['models']:
        print(f\"{model['name']} - {model['quantization']} - {model['size_gb']:.2f}GB\")
"
```

### Start Model Servers

```bash
# Start all models in active profile
curl -X POST http://localhost:8000/api/models/start

# Start specific model
curl -X POST http://localhost:8000/api/models/Q2_FAST_1/start

# Check server status
curl http://localhost:8000/api/models/servers | jq .
```

### Stop Model Servers

```bash
# Stop all models
curl -X POST http://localhost:8000/api/models/stop

# Stop specific model
curl -X POST http://localhost:8000/api/models/Q2_FAST_1/stop
```

### Monitor Server Health

```bash
# Check health of all servers
curl http://localhost:8000/api/models/servers | jq '.servers[] | {name, status, port}'

# Continuous monitoring
watch -n 2 'curl -s http://localhost:8000/api/models/servers | jq ".servers[] | {name, status}"'
```

---

## Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend

# Search logs
docker-compose logs backend | grep "ERROR"
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend

# Force recreate
docker-compose up -d --force-recreate backend
```

### Access Container Shells

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# Redis CLI
docker-compose exec redis redis-cli -a change_this_secure_redis_password
```

### Database Operations

```bash
# Backup model registry
cp backend/data/model_registry.json backend/data/model_registry.json.backup

# Backup FAISS indexes
tar -czf faiss_backup.tar.gz backend/data/faiss_indexes/

# Restore model registry
cp backend/data/model_registry.json.backup backend/data/model_registry.json
docker-compose restart backend
```

### Clean Up

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Full cleanup
docker-compose down -v --rmi all
docker system prune -af
```

---

## Troubleshooting

### Services Won't Start

**Problem**: `docker-compose up` fails

**Solutions**:
1. Check Docker is running: `docker info`
2. Check port availability: `lsof -i :8000 -i :5173 -i :6379`
3. View detailed logs: `docker-compose logs`
4. Rebuild images: `docker-compose build --no-cache`

### Backend Unhealthy

**Problem**: Backend shows `unhealthy` in `docker-compose ps`

**Solutions**:
1. Check backend logs: `docker-compose logs backend`
2. Check health endpoint: `curl http://localhost:8000/health`
3. Verify Redis connection: `docker-compose exec backend python -c "import redis; r = redis.Redis(host='redis', port=6379); r.ping()"`
4. Restart backend: `docker-compose restart backend`

### Models Not Discovered

**Problem**: No models in registry after discovery

**Solutions**:
1. Verify HUB path: `ls -la /Users/dperez/Documents/LLM/llm-models/HUB/`
2. Check GGUF files exist: `find /Users/dperez/Documents/LLM/llm-models/HUB/ -name "*.gguf"`
3. Verify path in docker-compose.yml matches actual HUB location
4. Run discovery with verbose output:
   ```bash
   docker-compose exec backend python -m app.cli.discover_models --verbose
   ```

### Model Servers Won't Start

**Problem**: Model servers fail to launch

**Solutions**:
1. Verify llama-server binary:
   ```bash
   docker-compose exec backend ls -la /usr/local/bin/llama-server
   docker-compose exec backend /usr/local/bin/llama-server --version
   ```
2. Check port availability: `netstat -an | grep LISTEN | grep 808`
3. Check memory limits: `docker stats`
4. View server logs: `docker-compose logs backend | grep llama-server`
5. Check permissions:
   ```bash
   docker-compose exec backend ls -l /usr/local/bin/llama-server
   ```

### Frontend Not Accessible

**Problem**: http://localhost:5173 doesn't respond

**Solutions**:
1. Check frontend logs: `docker-compose logs frontend`
2. Verify container is running: `docker-compose ps frontend`
3. Check health: `curl -I http://localhost:5173`
4. Rebuild frontend: `docker-compose build frontend && docker-compose up -d frontend`

### Permission Denied Errors

**Problem**: Permission errors in logs

**Solutions**:
1. Fix data directory permissions:
   ```bash
   chmod -R 777 backend/data backend/logs
   ```
2. Recreate directories:
   ```bash
   ./scripts/docker-setup.sh
   ```

### Out of Memory

**Problem**: Containers killed or OOM errors

**Solutions**:
1. Check resource usage: `docker stats`
2. Increase Docker memory limit (Docker Desktop → Preferences → Resources)
3. Reduce number of active models (use `fast-only` profile)
4. Adjust container limits in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G  # Reduce as needed
   ```

### Hot Reload Not Working (Dev Mode)

**Problem**: Code changes not reflected

**Solutions**:
1. Verify dev mode: `docker-compose logs backend | grep reload`
2. Check volume mounts: `docker-compose config | grep volumes -A 5`
3. Restart dev services:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart
   ```

---

## Advanced Usage

### Running Tests

Automated test suite:

```bash
# Production mode
./scripts/docker-test.sh

# Development mode
./scripts/docker-test.sh --dev

# Skip rebuild (faster)
./scripts/docker-test.sh --skip-build
```

### Custom Profiles

Create custom profile in `config/my-profile.yaml`:

```yaml
models:
  Q2_FAST_1:
    enabled: true
    model_name: my-custom-model-q2
    port: 8080
    parameters:
      ctx_size: 4096
      n_gpu_layers: 35
```

Activate:

```bash
export MAGI_PROFILE=my-profile
docker-compose restart backend
```

### Performance Tuning

Optimize for your hardware:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '8.0'      # Increase for more CPU
          memory: 16G      # Increase for more models
    environment:
      - MODEL_CONCURRENT_STARTS=true  # Parallel startup
```

### Monitoring with Prometheus

(Future enhancement - coming soon)

### Scaling with Docker Swarm

(Future enhancement - coming soon)

---

## Reference

### Port Mapping

| Service | Container Port | Host Port | Purpose |
|---------|---------------|-----------|---------|
| Backend | 8000 | 8000 | FastAPI application |
| Frontend | 80 (prod) / 5173 (dev) | 5173 | React UI |
| Redis | 6379 | 6379 | Cache/sessions |
| Model Servers | 8080-8099 | 8080-8099 | llama.cpp servers |

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `backend/data` | `/app/data` | Model registry, FAISS indexes |
| `backend/logs` | `/app/logs` | Application logs |
| `config` | `/app/config` | Profile YAML files |
| `HUB` | `/models` | GGUF model files (read-only) |
| `llama-server` | `/usr/local/bin/llama-server` | Model server binary (read-only) |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/models/registry` | GET | List discovered models |
| `/api/models/servers` | GET | List running servers |
| `/api/models/profiles` | GET | List available profiles |
| `/api/models/start` | POST | Start all servers in profile |
| `/api/models/stop` | POST | Stop all servers |
| `/api/models/{name}/start` | POST | Start specific server |
| `/api/models/{name}/stop` | POST | Stop specific server |

### Useful Commands

```bash
# Quick status check
docker-compose ps

# Resource usage
docker stats

# Inspect container
docker inspect magi_backend

# Network info
docker network inspect magi_network

# Volume info
docker volume inspect magi_redis_data

# Container logs location
docker inspect magi_backend | jq -r '.[0].LogPath'
```

---

## Getting Help

- **Documentation**: Check [docs directory](../) in project
- **API Docs**: http://localhost:8000/docs (when running)
- **Logs**: `docker-compose logs backend`
- **Issues**: Check GitHub issues or create new one

---

## Next Steps

After successful setup:

1. **Explore Model Management UI**: http://localhost:5173/model-management ([Quick Start Guide](QUICK_START_MODEL_MANAGEMENT.md))
2. **Try different profiles**: Switch between development/production/fast-only ([Profile Reference](PROFILE_QUICK_REFERENCE.md))
3. **Run queries**: Test the main query interface
4. **Monitor performance**: Watch resource usage with `docker stats`
5. **Customize**: Adjust profiles and settings for your use case

## Additional Resources

- [Docker Quick Reference](DOCKER_QUICK_REFERENCE.md) - One-page cheat sheet
- [Docker Infrastructure](../architecture/DOCKER_INFRASTRUCTURE.md) - Full architecture documentation
- [Admin Quick Reference](ADMIN_QUICK_REFERENCE.md) - No-CLI admin panel
- [Profile Quick Reference](PROFILE_QUICK_REFERENCE.md) - Profile system guide
- [Testing Guide](../TESTING_GUIDE.md) - Testing procedures
- [docker-compose.yml](../../docker-compose.yml) - Service configuration

Happy orchestrating!
