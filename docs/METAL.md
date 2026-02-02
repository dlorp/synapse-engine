# Metal Acceleration (Apple Silicon)

Get 2-3x faster inference on Apple Silicon Macs with automatic Metal GPU acceleration.

## How It Works

By default, llama-server runs inside Docker (no GPU access). **Metal acceleration** runs llama-server natively on macOS with full GPU access.

The Host API service automatically manages Metal-accelerated servers.

## Performance

| Mode | Startup | Inference |
|------|---------|-----------|
| CPU (Docker) | 15-30s | Baseline |
| Metal (Host) | 3-5s | 2-3x faster |

## Setup

### 1. Install llama.cpp

```bash
brew install llama.cpp
llama-server --version  # Verify Metal support
```

### 2. Configure SSH

```bash
# Generate key
ssh-keygen -t ed25519 -f ~/.ssh/synapse_host_api -N ""

# Add to authorized_keys with command restriction
echo "command=\"/opt/homebrew/bin/bash /path/to/synapse-engine/scripts/ssh-wrapper.sh\" $(cat ~/.ssh/synapse_host_api.pub)" >> ~/.ssh/authorized_keys

# Copy to host-api directory
mkdir -p host-api/.ssh
cp ~/.ssh/synapse_host_api host-api/.ssh/id_ed25519
cp ~/.ssh/synapse_host_api.pub host-api/.ssh/id_ed25519.pub

# Create SSH config
cat > host-api/.ssh/config <<EOF
Host mac-host
    HostName host.docker.internal
    User $USER
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
EOF
```

### 3. Enable in docker-compose.yml

```yaml
environment:
  - USE_EXTERNAL_SERVERS=true
```

### 4. Start

```bash
docker-compose up -d
```

Then click "START ALL ENABLED" in WebUI.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ macOS Host                                           │
│  llama-server (Metal) - Port 8080                   │
│  llama-server (Metal) - Port 8081                   │
│  GPU: Apple M4 Pro                                   │
│                    ▲                                 │
│                    │ SSH                             │
│  ┌─────────────────┼─────────────────────────────┐  │
│  │ Docker          │                              │  │
│  │  Host API ──────┘                              │  │
│  │      ↓                                         │  │
│  │  Backend (8000) ─→ host.docker.internal:808x  │  │
│  │      ↓                                         │  │
│  │  Frontend (5173)                               │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## What Happens

**On "START ALL ENABLED":**
1. WebUI → Backend: `POST /api/models/servers/start-all`
2. Backend → Host API: `POST /api/servers/start`
3. Host API → SSH → `start-host-llama-servers.sh`
4. Script reads `model_registry.json`, launches Metal servers
5. Backend connects via `host.docker.internal`

**On Shutdown:**
1. Docker sends SIGTERM to Host API
2. Host API runs `stop-host-llama-servers.sh`
3. Graceful Metal server shutdown

## Security

- SSH uses key-only auth (no password)
- `authorized_keys` restricts to `ssh-wrapper.sh`
- Wrapper only allows: `start-metal-servers`, `stop-metal-servers`

## Troubleshooting

**"External server not running":**
```bash
lsof -i :9090  # Check if running
curl http://localhost:9090/health  # Check health
```

**Slow inference (not using Metal):**
```bash
# Check startup logs for:
ggml_metal_device_init: GPU name: Apple M4 Pro
```

**Disable Metal (CPU-only):**
```yaml
environment:
  - USE_EXTERNAL_SERVERS=false
```
