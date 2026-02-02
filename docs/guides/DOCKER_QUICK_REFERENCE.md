# Synapse Engine Docker Quick Reference Card

One-page cheat sheet for common Docker operations.

**Full Guide:** [Docker Quick Start Guide](DOCKER_QUICKSTART.md)
**Architecture:** [Docker Infrastructure](../architecture/DOCKER_INFRASTRUCTURE.md)

---

## Quick Start (4 Steps)

```bash
# 1. Setup
./scripts/docker-setup.sh

# 2. Discover models
docker-compose run --rm backend python -m app.cli.discover_models

# 3. Start services
docker-compose up -d

# 4. Access UI
open http://localhost:5173/model-management
```

---

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend

# View service status
docker-compose ps

# View resource usage
docker stats
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Search logs
docker-compose logs backend | grep ERROR
```

### Development Mode

```bash
# Start with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Stop dev services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### Shell Access

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# Redis CLI
docker-compose exec redis redis-cli -a change_this_secure_redis_password
```

---

## Model Management

### Discovery

```bash
# Discover models
docker-compose run --rm backend python -m app.cli.discover_models

# View registry
curl http://localhost:8000/api/models/registry | jq .
```

### Server Control

```bash
# Start all servers in active profile
curl -X POST http://localhost:8000/api/models/start

# Stop all servers
curl -X POST http://localhost:8000/api/models/stop

# Start specific server
curl -X POST http://localhost:8000/api/models/Q2_FAST_1/start

# Check server status
curl http://localhost:8000/api/models/servers | jq .
```

### Profile Management

```bash
# List profiles
curl http://localhost:8000/api/models/profiles | jq .

# Switch profile
curl -X POST http://localhost:8000/api/models/profile/activate \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "production"}'

# Or via environment
export SYNAPSE_PROFILE=production
docker-compose restart backend
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker running
docker info

# Check port conflicts
lsof -i :8000 -i :5173 -i :6379

# Rebuild images
docker-compose build --no-cache

# View detailed logs
docker-compose logs backend
```

### Backend Unhealthy

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs backend

# Restart
docker-compose restart backend
```

### Models Not Discovered

```bash
# Verify HUB path
ls -la ${PRAXIS_MODEL_PATH}/

# Check mount
docker-compose exec backend ls -la /models

# Re-run discovery
docker-compose run --rm backend python -m app.cli.discover_models
```

### Permission Errors

```bash
# Fix permissions
chmod -R 777 backend/data backend/logs

# Re-run setup
./scripts/docker-setup.sh
```

---

## Testing

```bash
# Run full test suite
./scripts/docker-test.sh

# Development mode tests
./scripts/docker-test.sh --dev

# Skip rebuild (faster)
./scripts/docker-test.sh --skip-build
```

---

## Cleanup

```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker-compose down -v --rmi all
docker system prune -af
```

---

## Useful URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Main UI |
| Model Management | http://localhost:5173/model-management | Model UI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/health | Health status |

---

## Port Reference

| Port | Service | Purpose |
|------|---------|---------|
| 8000 | Backend | FastAPI |
| 5173 | Frontend | React UI |
| 6379 | Redis | Cache |
| 8080-8099 | Models | llama.cpp servers |

---

## Environment Variables

```bash
# Profile selection
SYNAPSE_PROFILE=development|production|fast-only

# Model management
MODEL_PORT_RANGE_START=8080
MODEL_PORT_RANGE_END=8099
MODEL_MAX_STARTUP_TIME=120

# Logging
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
```

---

## Data Locations

| Data | Host Path | Container Path |
|------|-----------|---------------|
| Models | `/Users/.../HUB/` | `/models` |
| Registry | `backend/data/` | `/app/data` |
| Logs | `backend/logs/` | `/app/logs` |
| Config | `config/` | `/app/config` |

---

## Quick Checks

```bash
# All services healthy?
docker-compose ps

# Backend responding?
curl http://localhost:8000/health

# Models discovered?
curl http://localhost:8000/api/models/registry | jq '.total'

# Servers running?
curl http://localhost:8000/api/models/servers | jq '.servers | length'

# Frontend accessible?
curl -I http://localhost:5173

# Resource usage OK?
docker stats --no-stream
```

---

## Emergency Recovery

```bash
# 1. Stop everything
docker-compose down

# 2. Clean up
docker system prune -f

# 3. Rebuild
./scripts/docker-setup.sh

# 4. Rediscover
docker-compose run --rm backend python -m app.cli.discover_models

# 5. Restart
docker-compose up -d
```

---

## Additional Resources

- [Docker Quick Start Guide](DOCKER_QUICKSTART.md) - Full documentation
- [Docker Infrastructure](../architecture/DOCKER_INFRASTRUCTURE.md) - Architecture details
- [Admin Quick Reference](ADMIN_QUICK_REFERENCE.md) - Browser-based testing
- [Profile Quick Reference](PROFILE_QUICK_REFERENCE.md) - Profile management
- [docker-compose.yml](../../docker-compose.yml) - Service configuration
