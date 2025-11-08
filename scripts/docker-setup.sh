#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Docker Setup Script
# =============================================================================
# Prepares the environment for running the system in Docker
# Validates prerequisites, creates directories, and builds images
#
# Usage:
#   ./scripts/docker-setup.sh [--dev]
#
# Options:
#   --dev    Setup for development mode (with hot reload)
#
# Exit codes:
#   0: Success
#   1: Missing prerequisites or setup failure
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HUB_PATH="${PRAXIS_MODEL_PATH}/"
LLAMA_PATH="/usr/local/bin/llama-server"
DEV_MODE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dev)
            DEV_MODE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            exit 1
            ;;
    esac
done

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# =============================================================================
# Validation Functions
# =============================================================================

check_docker() {
    print_info "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Please start Docker Desktop or the Docker daemon"
        exit 1
    fi

    print_success "Docker is installed and running"
}

check_docker_compose() {
    print_info "Checking Docker Compose installation..."

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi

    print_success "Docker Compose is installed"
}

check_hub_directory() {
    print_info "Checking HUB directory..."

    if [ ! -d "$HUB_PATH" ]; then
        print_error "HUB directory not found at: $HUB_PATH"
        echo ""
        echo "Please update the HUB_PATH in this script or in docker-compose.yml"
        echo "Current path: $HUB_PATH"
        exit 1
    fi

    # Check if there are any GGUF files
    GGUF_COUNT=$(find "$HUB_PATH" -name "*.gguf" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [ "$GGUF_COUNT" -eq 0 ]; then
        print_warning "No GGUF files found in HUB directory"
        echo "Models will need to be added before discovery can run"
    else
        print_success "HUB directory found with $GGUF_COUNT GGUF files"
    fi
}

check_llama_server() {
    print_info "Checking llama-server binary..."

    if [ ! -f "$LLAMA_PATH" ]; then
        print_warning "llama-server not found at: $LLAMA_PATH"
        echo ""
        echo "Model servers will not be able to launch without llama-server binary"
        echo "Please install llama.cpp and ensure llama-server is at: $LLAMA_PATH"
        echo ""
        echo "You can continue setup, but models won't run until llama-server is installed"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "llama-server binary found"
    fi
}

# =============================================================================
# Setup Functions
# =============================================================================

create_directories() {
    print_info "Creating required directories..."

    cd "$PROJECT_ROOT"

    # Backend directories
    mkdir -p backend/data/faiss_indexes
    mkdir -p backend/logs

    # Create .gitkeep files to preserve empty directories
    touch backend/data/faiss_indexes/.gitkeep
    touch backend/logs/.gitkeep

    # Set permissions (777 for Docker compatibility)
    chmod -R 777 backend/data backend/logs 2>/dev/null || true

    print_success "Directories created with proper permissions"
}

check_env_file() {
    print_info "Checking environment configuration..."

    cd "$PROJECT_ROOT"

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found, copying from .env.example"
            cp .env.example .env
            print_info "Please review and update .env file with your settings"
        else
            print_warning "No .env or .env.example file found"
            print_info "Using default environment variables from docker-compose.yml"
        fi
    else
        print_success "Environment file (.env) exists"
    fi
}

build_images() {
    print_info "Building Docker images..."

    cd "$PROJECT_ROOT"

    if [ "$DEV_MODE" = true ]; then
        print_info "Building development images..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
    else
        print_info "Building production images..."
        docker-compose build
    fi

    print_success "Docker images built successfully"
}

# =============================================================================
# Main Setup Flow
# =============================================================================

main() {
    print_header "S.Y.N.A.P.S.E. ENGINE Docker Setup"

    if [ "$DEV_MODE" = true ]; then
        print_info "Mode: Development (with hot reload)"
    else
        print_info "Mode: Production"
    fi

    echo ""

    # Validation
    print_header "Validating Prerequisites"
    check_docker
    check_docker_compose
    check_hub_directory
    check_llama_server

    echo ""

    # Setup
    print_header "Setting Up Environment"
    create_directories
    check_env_file

    echo ""

    # Build
    print_header "Building Docker Images"
    build_images

    echo ""

    # Success message
    print_header "✅ Setup Complete!"

    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Discover models from HUB:"
    if [ "$DEV_MODE" = true ]; then
        echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --rm backend python -m app.cli.discover_models"
    else
        echo "   docker-compose run --rm backend python -m app.cli.discover_models"
    fi
    echo ""
    echo "2. Start services:"
    if [ "$DEV_MODE" = true ]; then
        echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d"
    else
        echo "   docker-compose up -d"
    fi
    echo ""
    echo "3. View logs:"
    echo "   docker-compose logs -f backend"
    echo ""
    echo "4. Access UI:"
    echo "   http://localhost:5173/model-management"
    echo ""
    echo "5. Check service health:"
    echo "   docker-compose ps"
    echo ""

    if [ "$DEV_MODE" = true ]; then
        echo "Development mode features:"
        echo "  - Hot reload enabled for backend and frontend"
        echo "  - Debug logging enabled"
        echo "  - Source code mounted from host"
        echo ""
    fi
}

# Run main function
main
