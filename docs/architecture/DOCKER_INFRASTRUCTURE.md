# Synapse Engine Docker Infrastructure

**Quick Start:** [Docker Quick Start Guide](../guides/DOCKER_QUICKSTART.md)
**Cheat Sheet:** [Docker Quick Reference](../guides/DOCKER_QUICK_REFERENCE.md)

## Overview

Complete Docker infrastructure for the Synapse Engine, supporting both development and production deployments.

## Architecture

The system consists of three containerized services:

1. **Redis** - Caching and session storage
2. **Backend** - FastAPI application server
3. **Frontend** - React application (Vite dev server or nginx)

All services are connected via a dedicated Docker bridge network (`synapse_network`) with proper health checks, resource limits, and security configurations.

---

## Files Structure

```
${PROJECT_DIR}/
├── docker-compose.yml              # Service orchestration
├── .env                            # Environment variables (from .env.example)
├── backend/
│   ├── Dockerfile                  # Multi-stage production build
│   ├── .dockerignore              # Build context exclusions
│   └── requirements.txt            # Python dependencies
└── frontend/
    ├── Dockerfile                  # Multi-stage production build (nginx)
    ├── Dockerfile.dev             # Development build (Vite)
    ├── nginx.conf                 # Production nginx configuration
    ├── .dockerignore              # Build context exclusions
    └── package.json               # Node dependencies
```

---

## Services Configuration

### Redis (redis:7-alpine)

**Purpose:** Caching and session storage with persistence

**Configuration:**
- Port: 6379
- Authentication: Password required (from REDIS_PASSWORD env var)
- Persistence: AOF (Append-Only File) with everysec fsync
- Memory: 256MB max with LRU eviction policy
- Volume: `synapse_redis_data` for data persistence

**Resource Limits:**
- CPU: 0.25-0.5 cores
- Memory: 256MB-512MB

**Health Check:**
```bash
redis-cli --raw incr ping
# Interval: 10s, Timeout: 3s, Retries: 3, Start period: 10s
```

---

### Backend (FastAPI)

**Purpose:** Python FastAPI application server with hot reload

**Build:** Multi-stage Docker build
- Stage 1 (Builder): Installs dependencies in virtual environment
- Stage 2 (Runtime): Copies venv and application code

**Configuration:**
- Port: 8000
- User: Non-root (appuser:1000)
- Working Directory: /app
- Hot Reload: Enabled (via volume mounts)

**Volumes:**
- `./backend/app:/app/app:rw` - Source code (hot reload)
- `./backend/config:/app/config:ro` - Configuration files
- `./backend/tests:/app/tests:ro` - Test files
- `./data:/app/data:rw` - Data directory (FAISS indexes)

**Environment Variables:**
- `ENVIRONMENT=development`
- `REDIS_HOST=redis`
- `MODEL_*_URL=http://host.docker.internal:808X` - Model server URLs
- See .env file for complete list

**Resource Limits:**
- CPU: 1.0-2.0 cores
- Memory: 1GB-2GB

**Health Check:**
```bash
curl -f http://localhost:8000/health
# Interval: 15s, Timeout: 5s, Retries: 3, Start period: 30s
```

**Depends On:** Redis (healthy)

---

### Frontend (React + Vite)

**Purpose:** React development server with HMR (Hot Module Replacement)

**Development Build (Dockerfile.dev):**
- Base: node:20-alpine
- Dev Server: Vite with HMR
- Port: 5173

**Production Build (Dockerfile):**
- Multi-stage build with nginx
- Stage 1: Build React app with Vite
- Stage 2: Serve with nginx:alpine
- Port: 80 (production)

**Configuration (Development):**
- Port: 5173
- Hot Reload: Enabled (via volume mounts)

**Volumes (Development):**
- `./frontend/src:/app/src:rw` - Source code (HMR)
- `./frontend/public:/app/public:ro` - Static assets
- `/app/node_modules` - Anonymous volume (prevent overwrite)

**Environment Variables:**
- `VITE_API_URL=http://localhost:8000`
- `VITE_WS_URL=ws://localhost:8000/ws`

**Resource Limits:**
- CPU: 0.5-1.0 cores
- Memory: 512MB-1GB

**Health Check:**
```bash
wget --no-verbose --tries=1 --spider http://localhost:5173
# Interval: 15s, Timeout: 5s, Retries: 3, Start period: 20s
```

**Depends On:** Backend (healthy)

---

## Network Configuration

**Network:** `synapse_network`
- Type: Bridge
- Driver: bridge
- Isolation: Services can only communicate within this network

**Service Communication:**
- Backend → Redis: `redis:6379`
- Frontend → Backend: `backend:8000`
- Backend → Host Models: `host.docker.internal:8080-8083`

---

## Volume Configuration

### Named Volumes

**redis_data:**
- Purpose: Persist Redis data across container restarts
- Driver: local
- Location: Managed by Docker

### Bind Mounts (Development)

**Backend:**
- Source code: Hot reload enabled
- Configuration: Read-only
- Data directory: Persistent storage for FAISS indexes

**Frontend:**
- Source code: HMR enabled
- node_modules: Anonymous volume (not overwritten by host)

---

## Usage

### First-Time Setup

```bash
# Navigate to project root
cd ${PROJECT_DIR}

# Ensure .env file exists (copy from .env.example if needed)
cp .env.example .env

# Edit .env and set REDIS_PASSWORD
nano .env
```

### Development Workflow

```bash
# Build all images
docker compose build

# Start all services in detached mode
docker compose up -d

# Check service status
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f redis

# Stop all services
docker compose down

# Stop and remove volumes (⚠️ destroys Redis data)
docker compose down -v

# Rebuild specific service
docker compose build backend
docker compose up -d backend

# Restart specific service
docker compose restart backend
```

### Testing Endpoints

```bash
# Backend health check
curl http://localhost:8000/health

# Backend API docs
open http://localhost:8000/api/docs

# Frontend application
open http://localhost:5173

# Redis (requires redis-cli)
redis-cli -h localhost -p 6379 -a YOUR_REDIS_PASSWORD ping
```

---

## Security Features

### Backend Container

✅ **Non-root user:** Runs as `appuser:1000`
✅ **Multi-stage build:** Build dependencies not in final image
✅ **Read-only mounts:** Config files mounted read-only
✅ **Health checks:** Automatic unhealthy container restart
✅ **Resource limits:** Prevents runaway resource consumption

### Frontend Container

✅ **Minimal base image:** Alpine Linux (small attack surface)
✅ **Production build:** Multi-stage removes build tools
✅ **Security headers:** nginx.conf includes security headers
✅ **Gzip compression:** Reduces bandwidth usage

### Redis Container

✅ **Password authentication:** Required for all connections
✅ **Memory limits:** 256MB max with LRU eviction
✅ **Data persistence:** AOF with fsync every second
✅ **Resource limits:** CPU and memory constraints

### Network Security

✅ **Bridge network:** Isolated from host network
✅ **No privileged containers:** Standard security context
✅ **CORS configuration:** Backend enforces allowed origins
✅ **Host access:** Models accessed via `host.docker.internal`

---

## Production Deployment

### Switch to Production Frontend

Edit `docker-compose.yml`:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile  # Use production Dockerfile (nginx)
  ports:
    - "80:80"              # Nginx on port 80
  # Remove development volumes
```

### Backend Production Optimizations

Edit `backend/Dockerfile`:

```dockerfile
# Change CMD to use gunicorn with multiple workers
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000"]
```

And remove `--reload` flag from current CMD.

### Environment Variables

Update `.env` for production:

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
REDIS_PASSWORD=<strong-random-password>
CORS_ORIGINS=https://yourdomain.com
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker compose logs <service-name>

# Check container status
docker compose ps

# Rebuild without cache
docker compose build --no-cache <service-name>
```

### Health Check Failing

```bash
# Check health check endpoint manually
docker compose exec backend curl http://localhost:8000/health

# Check health check logs
docker compose logs backend | grep health
```

### Redis Connection Issues

```bash
# Check Redis is running
docker compose ps redis

# Test Redis connection
docker compose exec redis redis-cli -a YOUR_PASSWORD ping

# Check Redis logs
docker compose logs redis
```

### Backend Can't Reach Host Models

**macOS/Windows:** Uses `host.docker.internal` (works by default)

**Linux:** Add to docker-compose.yml:

```yaml
backend:
  extra_hosts:
    - "host.docker.internal:172.17.0.1"
```

Or use your host's IP address in .env:
```bash
MODEL_Q2_FAST_1_URL=http://192.168.1.x:8080
```

### Volume Permission Issues

```bash
# Check volume ownership
docker compose exec backend ls -la /app/data

# Fix permissions (if needed)
docker compose exec backend chown -R appuser:appuser /app/data
```

### Hot Reload Not Working

**Backend:**
- Ensure volume mount includes `:rw` flag
- Check uvicorn is running with `--reload` flag
- Verify code is in `/app/app` directory

**Frontend:**
- Ensure `node_modules` is an anonymous volume
- Check Vite is running with `--host 0.0.0.0`
- Verify source is in `/app/src` directory

---

## Performance Optimization

### Reduce Build Time

```bash
# Use BuildKit (faster builds)
export DOCKER_BUILDKIT=1

# Build with cache
docker compose build

# Build in parallel
docker compose build --parallel
```

### Reduce Image Size

- Multi-stage builds already implemented
- Alpine base images already in use
- .dockerignore excludes unnecessary files

### Optimize Container Startup

Current startup times:
- Redis: ~2-3 seconds
- Backend: ~10-15 seconds
- Frontend: ~5-10 seconds

Total stack startup: ~30 seconds

---

## Monitoring

### Container Resource Usage

```bash
# Real-time stats
docker stats

# Specific containers
docker stats synapse_backend synapse_frontend synapse_redis
```

### Health Check Status

```bash
# All services
docker compose ps

# Detailed inspect
docker inspect --format='{{.State.Health.Status}}' synapse_backend
```

### Logs

```bash
# All services (last 100 lines)
docker compose logs --tail=100

# Follow logs with timestamps
docker compose logs -f -t

# Specific service with filter
docker compose logs backend | grep ERROR
```

---

## Backup and Recovery

### Backup Redis Data

```bash
# Create backup of Redis data
docker compose exec redis redis-cli -a YOUR_PASSWORD BGSAVE

# Copy AOF file from volume
docker cp synapse_redis:/data/appendonly.aof ./backups/redis-$(date +%Y%m%d).aof
```

### Backup FAISS Indexes

```bash
# Create backup of data directory
tar -czf backups/faiss-indexes-$(date +%Y%m%d).tar.gz ./data/faiss_indexes/
```

### Restore from Backup

```bash
# Stop services
docker compose down

# Restore Redis data to volume
docker volume create synapse_redis_data
docker run --rm -v synapse_redis_data:/data -v $(pwd)/backups:/backup alpine \
    sh -c "cp /backup/redis-20250102.aof /data/appendonly.aof"

# Restore FAISS indexes
tar -xzf backups/faiss-indexes-20250102.tar.gz -C ./data/

# Start services
docker compose up -d
```

---

## Testing Checklist

After deployment, verify:

- [ ] All containers start successfully: `docker compose ps`
- [ ] All health checks pass (healthy status)
- [ ] Redis responds: `curl http://localhost:6379` or use redis-cli
- [ ] Backend API responds: `curl http://localhost:8000/health`
- [ ] Backend API docs accessible: http://localhost:8000/api/docs
- [ ] Frontend serves content: http://localhost:5173
- [ ] Hot reload works (modify source files)
- [ ] Backend can reach host models at host.docker.internal
- [ ] Logs show no errors: `docker compose logs`
- [ ] Resource usage is within limits: `docker stats`

---

## Validation Results

Infrastructure successfully tested on 2025-11-02:

✅ **Build:** All images built successfully (backend, frontend)
✅ **Startup:** All services started and became healthy
✅ **Health Checks:** All services passing health checks
✅ **Backend API:** Responding successfully at http://localhost:8000/health
✅ **Frontend:** Serving content at http://localhost:5173
✅ **Redis:** Running with AOF persistence
✅ **Network:** Services can communicate via bridge network
✅ **Volumes:** Data persistence configured correctly
✅ **Resource Limits:** All services have CPU/memory limits
✅ **Security:** Non-root users, password auth, isolated network

---

## Next Steps

1. **Add Model Management Scripts** (Session 2)
   - Health check scripts for llama.cpp servers
   - Automated startup/shutdown scripts
   - Load balancing configuration

2. **Implement Monitoring Stack** (Session 3)
   - Prometheus for metrics collection
   - Grafana for visualization
   - Alert manager for notifications

3. **CI/CD Pipeline** (Session 4)
   - GitHub Actions for automated testing
   - Docker image building and publishing
   - Automated deployment workflows

4. **Production Hardening** (Session 5)
   - SSL/TLS with Caddy
   - Secret management with Docker secrets
   - Log aggregation with ELK or Loki
   - Automated backups

---

## References

### External Documentation
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Vite Docker Guide](https://vitejs.dev/guide/static-deploy.html)
- [Redis Docker Configuration](https://redis.io/docs/manual/config/)
- [Nginx Configuration Best Practices](https://www.nginx.com/resources/wiki/start/)

### Internal Documentation
- [Docker Quick Start Guide](../guides/DOCKER_QUICKSTART.md) - Step-by-step setup
- [Docker Quick Reference](../guides/DOCKER_QUICK_REFERENCE.md) - Command cheat sheet
- [Admin Quick Reference](../guides/ADMIN_QUICK_REFERENCE.md) - Admin panel for testing
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Overall roadmap
- [Project Status](PROJECT_STATUS.md) - Current status
- [Testing Guide](../TESTING_GUIDE.md) - Testing procedures
- [docker-compose.yml](../../docker-compose.yml) - Configuration file

---

**Last Updated:** 2025-11-02
**Author:** DevOps Engineer Agent
**Version:** 1.0.0
