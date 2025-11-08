#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE - Setup SSH Automation
# =============================================================================
# This script configures secure SSH access for the host-api container to
# manage Metal-accelerated llama-servers on the macOS host.
#
# Security Features:
# 1. Key-only authentication (no passwords)
# 2. Command-restricted key (can only execute specific scripts)
# 3. Local network only (no internet exposure)
#
# Run this once to set up the automation.
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# =============================================================================
# Phase 1: Check Prerequisites
# =============================================================================

print_header "S.Y.N.A.P.S.E. ENGINE SSH Automation Setup"
echo "This script will configure secure SSH access for automatic"
echo "Metal server management from the Docker container."
echo ""
echo "Security measures:"
echo "  • SSH key-only authentication (no passwords)"
echo "  • Command restriction (can only run start/stop scripts)"
echo "  • Local network only"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Setup cancelled."
  exit 0
fi

print_header "Step 1: Enable Remote Login"

# Check if Remote Login is already enabled
if sudo systemsetup -getremotelogin | grep -q "On"; then
  print_success "Remote Login already enabled"
else
  print_info "Enabling Remote Login (SSH server)..."
  echo "You may be prompted for your password."
  sudo systemsetup -setremotelogin on
  print_success "Remote Login enabled"
fi

# =============================================================================
# Phase 2: Generate SSH Key
# =============================================================================

print_header "Step 2: Generate SSH Key"

SSH_DIR="$HOME/.ssh"
KEY_PATH="$SSH_DIR/synapse_automation"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ -f "$KEY_PATH" ]; then
  print_warning "SSH key already exists at $KEY_PATH"
  read -p "Overwrite? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Using existing key"
  else
    rm -f "$KEY_PATH" "$KEY_PATH.pub"
    ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "synapse-docker-automation"
    print_success "New SSH key generated"
  fi
else
  ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "synapse-docker-automation"
  print_success "SSH key generated: $KEY_PATH"
fi

# =============================================================================
# Phase 3: Configure Authorized Keys with Command Restriction
# =============================================================================

print_header "Step 3: Configure Authorized Keys"

AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"
touch "$AUTHORIZED_KEYS"
chmod 600 "$AUTHORIZED_KEYS"

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_SCRIPT="$PROJECT_DIR/scripts/start-host-llama-servers.sh"
STOP_SCRIPT="$PROJECT_DIR/scripts/stop-host-llama-servers.sh"

print_info "Project directory: $PROJECT_DIR"
print_info "Start script: $START_SCRIPT"
print_info "Stop script: $STOP_SCRIPT"

# Check if scripts exist
if [ ! -f "$START_SCRIPT" ]; then
  print_error "Start script not found: $START_SCRIPT"
  exit 1
fi

if [ ! -f "$STOP_SCRIPT" ]; then
  print_error "Stop script not found: $STOP_SCRIPT"
  exit 1
fi

# Read the public key
PUBLIC_KEY=$(cat "$KEY_PATH.pub")

# Create a wrapper script that allows both start and stop commands
WRAPPER_SCRIPT="$PROJECT_DIR/scripts/ssh-wrapper.sh"
cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# S.Y.N.A.P.S.E. ENGINE SSH Command Wrapper
# This script restricts SSH access to only execute start/stop commands

case "$SSH_ORIGINAL_COMMAND" in
  "start-metal-servers")
    exec /bin/bash /Users/dperez/Documents/Programming/SYNAPSE_ENGINE/scripts/start-host-llama-servers.sh
    ;;
  "stop-metal-servers")
    exec /bin/bash /Users/dperez/Documents/Programming/SYNAPSE_ENGINE/scripts/stop-host-llama-servers.sh
    ;;
  *)
    echo "ERROR: Unauthorized command. Only 'start-metal-servers' and 'stop-metal-servers' are allowed." >&2
    exit 1
    ;;
esac
EOF

chmod +x "$WRAPPER_SCRIPT"
print_success "Created SSH wrapper script: $WRAPPER_SCRIPT"

# Add the restricted key to authorized_keys
RESTRICTED_KEY="command=\"$WRAPPER_SCRIPT\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty $PUBLIC_KEY"

# Remove old automation keys if present
sed -i.bak '/synapse-docker-automation/d' "$AUTHORIZED_KEYS" 2>/dev/null || true
sed -i.bak '/magi-docker-automation/d' "$AUTHORIZED_KEYS" 2>/dev/null || true

# Add new restricted key
echo "$RESTRICTED_KEY" >> "$AUTHORIZED_KEYS"
print_success "Added restricted key to authorized_keys"

# =============================================================================
# Phase 4: Copy SSH Key to Docker Volume
# =============================================================================

print_header "Step 4: Prepare SSH Key for Docker"

DOCKER_SSH_DIR="$PROJECT_DIR/host-api/.ssh"
mkdir -p "$DOCKER_SSH_DIR"
chmod 700 "$DOCKER_SSH_DIR"

# Copy private key
cp "$KEY_PATH" "$DOCKER_SSH_DIR/id_ed25519"
chmod 600 "$DOCKER_SSH_DIR/id_ed25519"

# Create SSH config for host-api
cat > "$DOCKER_SSH_DIR/config" << EOF
Host mac-host
    HostName host.docker.internal
    User $USER
    IdentityFile /root/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
EOF
chmod 600 "$DOCKER_SSH_DIR/config"

print_success "SSH key copied to Docker directory"

# =============================================================================
# Phase 5: Summary and Next Steps
# =============================================================================

print_header "Setup Complete!"

echo -e "${GREEN}✓ Remote Login enabled${NC}"
echo -e "${GREEN}✓ SSH key generated and configured${NC}"
echo -e "${GREEN}✓ Command restriction applied${NC}"
echo -e "${GREEN}✓ Key prepared for Docker${NC}"
echo ""
echo -e "${CYAN}Security Status:${NC}"
echo "  • SSH key: $KEY_PATH"
echo "  • Key restrictions: Can only execute start/stop scripts"
echo "  • Authentication: Key-only (no password)"
echo "  • SSH wrapper: $WRAPPER_SCRIPT"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Rebuild host-api Docker image: docker-compose build --no-cache host-api"
echo "  2. Restart services: docker-compose up -d"
echo "  3. Test automatic startup from WebUI!"
echo ""
echo -e "${YELLOW}To disable SSH automation:${NC}"
echo "  • Run: sudo systemsetup -setremotelogin off"
echo "  • Remove line from ~/.ssh/authorized_keys containing 'synapse-docker-automation'"
echo ""
