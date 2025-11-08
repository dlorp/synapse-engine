#!/opt/homebrew/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE - Start llama-server instances (Metal Acceleration)
# =============================================================================
# This script reads the model registry and starts enabled llama-server
# instances on the macOS host with Metal GPU acceleration.
#
# The backend container cannot launch llama-server directly because:
# - Container runs Linux, host is macOS
# - llama-server binary is macOS Mach-O executable
# - Metal GPU acceleration requires native macOS execution
#
# This script starts llama-server processes on the macOS host, which the
# Docker backend connects to via host.docker.internal.
# =============================================================================

set -e

# Configuration
PROJECT_DIR="${PROJECT_DIR}"
REGISTRY_FILE="$PROJECT_DIR/backend/data/model_registry.json"
RUNTIME_SETTINGS_FILE="$PROJECT_DIR/backend/data/runtime_settings.json"
LLAMA_BIN="/opt/homebrew/bin/llama-server"
LOG_DIR="/tmp/synapse-llama-servers"

# Docker container mount point → host path mapping
DOCKER_MOUNT="/models"
HOST_MOUNT="${PRAXIS_MODEL_PATH}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# Functions
# =============================================================================

print_header() {
  echo ""
  echo -e "${CYAN}========================================${NC}"
  echo -e "${CYAN}$1${NC}"
  echo -e "${CYAN}========================================${NC}"
  echo ""
}

print_error() {
  echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
  echo -e "${CYAN}→ $1${NC}"
}

check_prerequisites() {
  print_header "Checking Prerequisites"

  # Check jq is installed
  if ! command -v jq &> /dev/null; then
    print_error "jq not found - required for JSON parsing"
    echo "Install with: brew install jq"
    exit 1
  fi
  print_success "jq found"

  # Check llama-server binary exists
  if [ ! -f "$LLAMA_BIN" ]; then
    print_error "llama-server not found at: $LLAMA_BIN"
    echo "Install with: brew install llama.cpp"
    exit 1
  fi
  print_success "llama-server found: $LLAMA_BIN"

  # Check model registry exists
  if [ ! -f "$REGISTRY_FILE" ]; then
    print_error "Model registry not found: $REGISTRY_FILE"
    echo "Run model discovery first: docker-compose exec backend python -m app.cli.discover_models"
    exit 1
  fi
  print_success "Model registry found: $REGISTRY_FILE"

  # Check host mount directory exists
  if [ ! -d "$HOST_MOUNT" ]; then
    print_error "Model directory not found: $HOST_MOUNT"
    exit 1
  fi
  print_success "Model directory found: $HOST_MOUNT"

  # Check if any servers already running
  if pgrep -f "llama-server.*--port" > /dev/null; then
    print_warning "llama-server processes already running"
    echo ""
    pgrep -af "llama-server.*--port"
    echo ""
    # Auto-kill when run non-interactively (from SSH)
    if [ -t 0 ]; then
      read -p "Kill existing servers? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Cannot start - servers already running"
        exit 1
      fi
    fi
    print_info "Stopping existing servers..."
    pkill -f "llama-server.*--port" || true
    sleep 2
    print_success "Existing servers stopped"
  fi

  # Create log directory
  mkdir -p "$LOG_DIR"
  print_success "Log directory ready: $LOG_DIR"
  echo ""
}

convert_docker_path_to_host() {
  local DOCKER_PATH=$1
  # Replace /models with host mount path
  echo "${DOCKER_PATH/$DOCKER_MOUNT/$HOST_MOUNT}"
}

load_runtime_settings() {
  # Load global runtime settings with fallback defaults
  if [ -f "$RUNTIME_SETTINGS_FILE" ]; then
    N_GPU_LAYERS=$(jq -r '.n_gpu_layers // 99' "$RUNTIME_SETTINGS_FILE")
    CTX_SIZE=$(jq -r '.ctx_size // 32768' "$RUNTIME_SETTINGS_FILE")
    N_THREADS=$(jq -r '.n_threads // 8' "$RUNTIME_SETTINGS_FILE")
    BATCH_SIZE=$(jq -r '.batch_size // 512' "$RUNTIME_SETTINGS_FILE")
  else
    # Fallback defaults
    N_GPU_LAYERS=99
    CTX_SIZE=32768
    N_THREADS=8
    BATCH_SIZE=512
  fi

  print_info "Global runtime settings:"
  echo "   GPU layers: $N_GPU_LAYERS"
  echo "   Context size: $CTX_SIZE"
  echo "   Threads: $N_THREADS"
  echo "   Batch size: $BATCH_SIZE"
  echo ""
}

start_server() {
  local MODEL_ID=$1
  local PORT=$2
  local DOCKER_FILE_PATH=$3
  local MODEL_N_GPU=$4
  local MODEL_CTX=$5
  local MODEL_THREADS=$6
  local MODEL_BATCH=$7

  # Convert Docker path to host path
  local HOST_FILE_PATH=$(convert_docker_path_to_host "$DOCKER_FILE_PATH")
  local MODEL_NAME=$(basename "$HOST_FILE_PATH")

  print_info "Starting $MODEL_ID on port $PORT"
  echo "   Model: $MODEL_NAME"
  echo "   Path: $HOST_FILE_PATH"

  # Check if model file exists on host
  if [ ! -f "$HOST_FILE_PATH" ]; then
    print_error "Model file not found on host: $HOST_FILE_PATH"
    return 1
  fi

  # Use model-specific settings or fall back to global
  local USE_GPU=${MODEL_N_GPU:-$N_GPU_LAYERS}
  local USE_CTX=${MODEL_CTX:-$CTX_SIZE}
  local USE_THREADS=${MODEL_THREADS:-$N_THREADS}
  local USE_BATCH=${MODEL_BATCH:-$BATCH_SIZE}

  echo "   GPU layers: $USE_GPU | CTX: $USE_CTX | Threads: $USE_THREADS | Batch: $USE_BATCH"

  # Launch llama-server with Metal acceleration
  "$LLAMA_BIN" \
    --model "$HOST_FILE_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --ctx-size "$USE_CTX" \
    --n-gpu-layers "$USE_GPU" \
    --threads "$USE_THREADS" \
    --batch-size "$USE_BATCH" \
    --ubatch-size 256 \
    --flash-attn on \
    --no-mmap \
    > "$LOG_DIR/llama-server-$PORT.log" 2>&1 &

  local PID=$!
  echo "   PID: $PID"

  # Wait a moment and check if process is still running
  sleep 1
  if ps -p $PID > /dev/null; then
    print_success "Server started successfully (PID: $PID)"
    echo "$PID" > "$LOG_DIR/llama-server-$PORT.pid"
  else
    print_error "Server failed to start on port $PORT"
    echo "Check log: $LOG_DIR/llama-server-$PORT.log"
    return 1
  fi

  echo ""
}

wait_for_health() {
  local PORT=$1
  local MAX_WAIT=30
  local ELAPSED=0

  print_info "Waiting for server health check on port $PORT..."

  while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; then
      print_success "Server ready on port $PORT"
      return 0
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    echo -n "."
  done

  echo ""
  print_warning "Health check timeout on port $PORT (server may still be initializing)"
  return 1
}

# =============================================================================
# Main Script
# =============================================================================

print_header "S.Y.N.A.P.S.E. ENGINE Metal-Accelerated Server Launcher"
echo "Starting enabled models from registry with Metal GPU acceleration"
echo ""

# Prerequisites check
check_prerequisites

# Load global runtime settings
load_runtime_settings

# Read enabled models from registry
print_header "Reading Model Registry"

ENABLED_MODELS=$(jq -r '.models | to_entries[] | select(.value.enabled == true) | @json' "$REGISTRY_FILE")

if [ -z "$ENABLED_MODELS" ]; then
  print_warning "No enabled models found in registry"
  echo "Enable models via the WebUI Model Management page"
  exit 0
fi

MODEL_COUNT=$(echo "$ENABLED_MODELS" | wc -l | tr -d ' ')
print_info "Found $MODEL_COUNT enabled model(s)"
echo ""

# Start all enabled servers
print_header "Starting Metal-Accelerated Servers"

STARTED_COUNT=0
FAILED_COUNT=0

declare -a PORTS=()

while IFS= read -r MODEL_JSON; do
  MODEL_ID=$(echo "$MODEL_JSON" | jq -r '.key')
  PORT=$(echo "$MODEL_JSON" | jq -r '.value.port')
  FILE_PATH=$(echo "$MODEL_JSON" | jq -r '.value.file_path')
  N_GPU=$(echo "$MODEL_JSON" | jq -r '.value.n_gpu_layers // empty')
  CTX=$(echo "$MODEL_JSON" | jq -r '.value.ctx_size // empty')
  THREADS=$(echo "$MODEL_JSON" | jq -r '.value.n_threads // empty')
  BATCH=$(echo "$MODEL_JSON" | jq -r '.value.batch_size // empty')

  if start_server "$MODEL_ID" "$PORT" "$FILE_PATH" "$N_GPU" "$CTX" "$THREADS" "$BATCH"; then
    STARTED_COUNT=$((STARTED_COUNT + 1))
    PORTS+=("$PORT")
  else
    FAILED_COUNT=$((FAILED_COUNT + 1))
  fi
done <<< "$ENABLED_MODELS"

if [ $STARTED_COUNT -eq 0 ]; then
  print_error "All servers failed to start"
  exit 1
fi

# Wait for all servers to be healthy
if [ $STARTED_COUNT -gt 0 ]; then
  print_header "Health Check (All Servers)"

  HEALTHY_COUNT=0

  for PORT in "${PORTS[@]}"; do
    if wait_for_health "$PORT"; then
      HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi
  done
fi

# Summary
print_header "Summary"
echo "Total enabled: $MODEL_COUNT"
echo "Started: $STARTED_COUNT"
echo "Healthy: $HEALTHY_COUNT"
echo "Failed: $FAILED_COUNT"
echo ""
echo "Logs: $LOG_DIR"
echo "PID files: $LOG_DIR/*.pid"
echo ""

if [ $HEALTHY_COUNT -eq $STARTED_COUNT ] && [ $STARTED_COUNT -gt 0 ]; then
  print_success "All Metal-accelerated servers started successfully!"
  echo ""
  echo "Servers listening on localhost:"
  for PORT in "${PORTS[@]}"; do
    echo "  - http://localhost:$PORT"
  done
  echo ""
  echo "Docker backend connects via: http://host.docker.internal:<port>"
  echo ""
  echo "To stop all servers: ./scripts/stop-host-llama-servers.sh"
else
  print_warning "Some servers failed to start or health check"
  echo "Check logs for details: ls -lh $LOG_DIR"
  exit 1
fi

exit 0
