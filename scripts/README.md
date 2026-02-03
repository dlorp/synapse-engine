# Scripts

Utility scripts for development, testing, and operations.

## Setup Scripts

| Script | Description |
|--------|-------------|
| `docker-setup.sh` | Initial Docker environment setup |
| `setup_metal.sh` | Apple Silicon Metal acceleration setup |
| `setup-ssh-automation.sh` | SSH key setup for Metal mode |

## Server Management

| Script | Description |
|--------|-------------|
| `start-host-llama-servers.sh` | Start llama.cpp servers on host |
| `stop-host-llama-servers.sh` | Stop all llama.cpp servers |
| `ssh-wrapper.sh` | SSH command wrapper for Metal mode |

## CGRAG Operations

| Script | Description |
|--------|-------------|
| `backup-cgrag-indexes.sh` | Backup FAISS indexes |
| `check-cgrag-health.sh` | Verify CGRAG index health |

## Testing

| Script | Description |
|--------|-------------|
| `test-all.sh` | Run complete test suite |
| `test-backend.sh` | Backend unit/integration tests |
| `test-frontend.sh` | Frontend tests |
| `test-integration.sh` | Full integration tests |
| `docker-test.sh` | Test Docker configuration |

### Specialized Tests

| Script | Description |
|--------|-------------|
| `test_moderator_modes.sh` | Test council/debate modes |
| `test_events_websocket.py` | WebSocket event testing |
| `test_timeseries_api.py` | Time-series metrics API tests |
| `test-websocket.html` | Browser-based WebSocket test |
| `test-resource-panel-performance.js` | Frontend performance test |

## Verification

| Script | Description |
|--------|-------------|
| `verify-css-layers.sh` | Verify CSS layer structure |
| `verify-vite-build.sh` | Verify Vite build output |

## Usage Examples

### Start Development Environment

```bash
# Setup Docker (first time)
./scripts/docker-setup.sh

# Start services
docker-compose up -d
```

### Run Tests

```bash
# All tests
./scripts/test-all.sh

# Backend only
./scripts/test-backend.sh

# With Docker
./scripts/docker-test.sh
```

### Metal Mode Setup (Apple Silicon)

```bash
# Setup SSH keys for Metal acceleration
./scripts/setup-ssh-automation.sh

# Configure Metal
./scripts/setup_metal.sh
```

### CGRAG Maintenance

```bash
# Check index health
./scripts/check-cgrag-health.sh

# Backup indexes
./scripts/backup-cgrag-indexes.sh
```

## Related Documentation

- [Docker Quick Reference](../docs/guides/DOCKER_QUICK_REFERENCE.md)
- [Docker Quickstart](../docs/guides/DOCKER_QUICKSTART.md)
- [Metal Acceleration](../docs/METAL.md)
- [WebSocket Testing Guide](./README-websocket-test.md)
