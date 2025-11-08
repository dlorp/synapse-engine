#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE - Stop llama-server instances
# =============================================================================
# Companion script to start-host-llama-servers.sh
# Gracefully stops all llama-server processes launched on the host.
# =============================================================================

set -e

LOG_DIR="/tmp/synapse-llama-servers"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() {
  echo -e "${CYAN}→ $1${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_info "Stopping llama-server processes..."

# Find all llama-server processes
if pgrep -f "llama-server.*--port" > /dev/null; then
  echo ""
  echo "Found running processes:"
  pgrep -af "llama-server.*--port" | while read line; do
    echo "  $line"
  done
  echo ""

  # Kill gracefully
  print_info "Sending SIGTERM (graceful shutdown)..."
  pkill -TERM -f "llama-server.*--port" || true
  sleep 3

  # Check if any still running
  if pgrep -f "llama-server.*--port" > /dev/null; then
    print_warning "Some processes still running, sending SIGKILL..."
    pkill -KILL -f "llama-server.*--port" || true
    sleep 1
  fi

  # Clean up PID files
  if [ -d "$LOG_DIR" ]; then
    rm -f "$LOG_DIR"/*.pid
  fi

  print_success "All llama-server processes stopped"
else
  print_warning "No llama-server processes found"
fi

echo ""
echo "Logs preserved in: $LOG_DIR"
echo "To clean up logs: rm -rf $LOG_DIR"
echo ""

exit 0
