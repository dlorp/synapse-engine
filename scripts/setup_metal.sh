#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE - Setup Metal-Accelerated llama.cpp
# =============================================================================
# This script verifies that llama-server with Metal support is installed.
# For Apple Silicon Macs, this provides 2-3x faster inference using GPU.
#
# Usage:
#   ./scripts/setup_metal.sh
#
# Requirements:
#   - Apple Silicon Mac (M1/M2/M3/M4)
#   - macOS 13.0+ (for Metal 3 support)
#   - Homebrew package manager
# =============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LLAMA_BIN="/opt/homebrew/bin/llama-server"
REQUIRED_VERSION="b3000"  # Minimum llama.cpp build version

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
  echo ""
  echo -e "${CYAN}========================================${NC}"
  echo -e "${CYAN}$1${NC}"
  echo -e "${CYAN}========================================${NC}"
  echo ""
}

print_error() {
  echo -e "${RED}✗ ERROR: $1${NC}" >&2
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
  echo -e "${BLUE}→ $1${NC}"
}

# =============================================================================
# Verification Functions
# =============================================================================

check_apple_silicon() {
  print_header "Checking System Requirements"

  local arch=$(uname -m)
  if [[ "$arch" != "arm64" ]]; then
    print_error "This script requires Apple Silicon (ARM64)"
    echo "   Detected architecture: $arch"
    echo "   Metal acceleration only available on M1/M2/M3/M4 chips"
    exit 1
  fi
  print_success "Apple Silicon detected: $arch"

  local os_version=$(sw_vers -productVersion)
  print_success "macOS version: $os_version"

  # Check for Metal support
  if system_profiler SPDisplaysDataType | grep -q "Metal"; then
    print_success "Metal GPU framework available"
  else
    print_warning "Metal support not detected - this is unusual"
  fi

  echo ""
}

check_homebrew() {
  print_info "Checking for Homebrew..."

  if ! command -v brew &> /dev/null; then
    print_error "Homebrew not found"
    echo ""
    echo "Install Homebrew from: https://brew.sh"
    echo "Or run:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
  fi

  local brew_version=$(brew --version | head -1)
  print_success "Homebrew installed: $brew_version"
  echo ""
}

check_llama_server() {
  print_header "Checking llama-server Installation"

  if [[ ! -f "$LLAMA_BIN" ]]; then
    print_error "llama-server not found at: $LLAMA_BIN"
    echo ""
    echo "Install with:"
    echo "  brew install llama.cpp"
    echo ""
    read -p "Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      print_info "Installing llama.cpp via Homebrew..."
      brew install llama.cpp

      if [[ -f "$LLAMA_BIN" ]]; then
        print_success "llama-server installed successfully"
      else
        print_error "Installation failed - binary not found"
        exit 1
      fi
    else
      print_error "Cannot proceed without llama-server"
      exit 1
    fi
  else
    print_success "llama-server found: $LLAMA_BIN"
  fi

  # Check if executable
  if [[ ! -x "$LLAMA_BIN" ]]; then
    print_error "llama-server exists but is not executable"
    echo "Fix with: chmod +x $LLAMA_BIN"
    exit 1
  fi
  print_success "Binary is executable"

  echo ""
}

verify_metal_support() {
  print_header "Verifying Metal GPU Support"

  print_info "Running llama-server to detect Metal initialization..."
  echo ""

  # Run llama-server --help and capture Metal initialization output
  local metal_output=$("$LLAMA_BIN" --help 2>&1 | head -15)

  # Check for Metal library initialization
  if echo "$metal_output" | grep -q "ggml_metal_library_init"; then
    print_success "Metal library initialized successfully"

    # Extract GPU information
    local gpu_name=$(echo "$metal_output" | grep "GPU name:" | sed 's/.*GPU name: *//')
    if [[ -n "$gpu_name" ]]; then
      print_success "Detected GPU: $gpu_name"
    fi

    # Check for Metal families
    if echo "$metal_output" | grep -q "MTLGPUFamilyApple"; then
      local gpu_family=$(echo "$metal_output" | grep "MTLGPUFamilyApple" | head -1 | awk '{print $NF}')
      print_success "Metal GPU Family: $gpu_family"
    fi

    # Check for unified memory
    if echo "$metal_output" | grep -q "has unified memory.*= true"; then
      print_success "Unified memory architecture detected"
    fi

    # Check for bfloat16 support
    if echo "$metal_output" | grep -q "has bfloat.*= true"; then
      print_success "BF16 precision support available"
    fi

    echo ""
    print_success "✓ Metal GPU acceleration is ENABLED"
    echo ""
    echo -e "${GREEN}Expected performance improvement:${NC}"
    echo "  - 2-3x faster inference vs CPU-only"
    echo "  - 40-60 tokens/sec (vs 15-20 on CPU)"
    echo "  - GPU offloading with --n-gpu-layers 99"

  else
    print_error "Metal support not detected in llama-server"
    echo ""
    echo "Your llama.cpp installation may not be compiled with Metal support."
    echo "Reinstall with Metal enabled:"
    echo "  brew uninstall llama.cpp"
    echo "  brew install llama.cpp"
    echo ""
    echo "Metal initialization output:"
    echo "$metal_output"
    exit 1
  fi

  echo ""
}

check_hub_directory() {
  print_header "Checking Model Directory"

  local hub_path="/Users/dperez/Documents/LLM/llm-models/HUB"

  if [[ ! -d "$hub_path" ]]; then
    print_warning "HUB directory not found: $hub_path"
    echo "Models will need to be placed in this directory for discovery"
  else
    local model_count=$(find "$hub_path" -name "*.gguf" 2>/dev/null | wc -l)
    print_success "HUB directory found: $hub_path"
    print_info "GGUF models found: $model_count"
  fi

  echo ""
}

show_next_steps() {
  print_header "Setup Complete - Next Steps"

  echo "1. Start S.Y.N.A.P.S.E. ENGINE services:"
  echo "   ${CYAN}docker-compose up -d${NC}"
  echo ""
  echo "2. Start Metal-accelerated llama-servers:"
  echo "   ${CYAN}./scripts/start-host-llama-servers.sh${NC}"
  echo ""
  echo "3. Open WebUI:"
  echo "   ${CYAN}http://localhost:5173${NC}"
  echo ""
  echo "4. Discover models and enable them in Model Management page"
  echo ""
  echo "5. Monitor GPU usage in Activity Monitor:"
  echo "   - Open Activity Monitor app"
  echo "   - Window → GPU History"
  echo "   - Look for 'llama-server' process using GPU"
  echo ""

  print_success "Metal-accelerated llama.cpp is ready!"
  echo ""
  echo "Performance tips:"
  echo "  - Use --n-gpu-layers 99 to offload all layers to GPU"
  echo "  - Larger batch sizes improve GPU utilization"
  echo "  - Monitor GPU memory in Activity Monitor"
  echo "  - Q2/Q3 quantizations work well with Metal"
  echo ""
}

# =============================================================================
# Main Script
# =============================================================================

print_header "S.Y.N.A.P.S.E. ENGINE Metal-Accelerated Setup"
echo "This script verifies Metal GPU support for maximum performance"
echo "on Apple Silicon Macs (M1/M2/M3/M4)"
echo ""

# Run all checks
check_apple_silicon
check_homebrew
check_llama_server
verify_metal_support
check_hub_directory

# Summary
show_next_steps

exit 0
