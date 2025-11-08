#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Docker Test Script
# =============================================================================
# Automated testing suite for Docker deployment
# Tests service startup, health checks, and API endpoints
#
# Usage:
#   ./scripts/docker-test.sh [--dev] [--skip-build]
#
# Options:
#   --dev         Test development mode (docker-compose.dev.yml)
#   --skip-build  Skip image rebuild (use existing images)
#
# Exit codes:
#   0: All tests passed
#   1: Test failure or error
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
DEV_MODE=false
SKIP_BUILD=false
COMPOSE_CMD="docker-compose"
COMPOSE_FILES="-f docker-compose.yml"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dev)
            DEV_MODE=true
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--dev] [--skip-build]"
            exit 1
            ;;
    esac
done

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

cleanup() {
    print_info "Cleaning up..."
    cd "$PROJECT_ROOT"
    $COMPOSE_CMD $COMPOSE_FILES down 2>/dev/null || true
}

# Register cleanup on exit
trap cleanup EXIT

# =============================================================================
# Test Functions
# =============================================================================

test_build() {
    if [ "$SKIP_BUILD" = true ]; then
        print_info "Skipping build (--skip-build flag set)"
        return 0
    fi

    print_info "Building Docker images..."
    cd "$PROJECT_ROOT"

    if $COMPOSE_CMD $COMPOSE_FILES build; then
        print_success "Build successful"
        return 0
    else
        print_failure "Build failed"
        return 1
    fi
}

test_startup() {
    print_info "Starting services..."
    cd "$PROJECT_ROOT"

    if $COMPOSE_CMD $COMPOSE_FILES up -d; then
        print_success "Services started"
        return 0
    else
        print_failure "Failed to start services"
        return 1
    fi
}

test_wait_for_backend() {
    print_info "Waiting for backend to be healthy..."

    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is healthy (${attempt}s)"
            return 0
        fi

        if [ $attempt -eq 1 ] || [ $((attempt % 10)) -eq 0 ]; then
            echo -n "."
        fi

        sleep 1
        ((attempt++))
    done

    echo ""
    print_failure "Backend did not become healthy within ${max_attempts}s"
    print_info "Showing backend logs:"
    $COMPOSE_CMD $COMPOSE_FILES logs --tail=50 backend
    return 1
}

test_service_health() {
    print_info "Checking service health..."
    cd "$PROJECT_ROOT"

    local output=$($COMPOSE_CMD $COMPOSE_FILES ps 2>&1)
    echo "$output"

    # Check if all services are running
    if echo "$output" | grep -q "Exit"; then
        print_failure "Some services have exited"
        return 1
    fi

    print_success "All services are running"
    return 0
}

test_health_endpoint() {
    print_info "Testing /health endpoint..."

    local response=$(curl -s http://localhost:8000/health)
    local status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")

    if [ "$status" = "healthy" ]; then
        print_success "Health endpoint OK: $status"
        echo "$response" | jq . 2>/dev/null || echo "$response"
        return 0
    else
        print_failure "Health endpoint failed: $status"
        echo "$response"
        return 1
    fi
}

test_registry_endpoint() {
    print_info "Testing /api/models/registry endpoint..."

    local response=$(curl -s http://localhost:8000/api/models/registry)
    local model_count=$(echo "$response" | jq '.models | length' 2>/dev/null || echo "0")

    print_success "Registry endpoint OK: $model_count models"
    echo "  First few models:"
    echo "$response" | jq -r '.models[:3][] | "  - \(.name) (\(.quantization))"' 2>/dev/null || echo "  (No models or parse error)"
    return 0
}

test_servers_endpoint() {
    print_info "Testing /api/models/servers endpoint..."

    local response=$(curl -s http://localhost:8000/api/models/servers)
    local server_count=$(echo "$response" | jq '.servers | length' 2>/dev/null || echo "0")

    print_success "Servers endpoint OK: $server_count servers"
    if [ "$server_count" -gt 0 ]; then
        echo "  Active servers:"
        echo "$response" | jq -r '.servers[] | "  - \(.name) on port \(.port) (\(.status))"' 2>/dev/null || echo "  (Parse error)"
    fi
    return 0
}

test_profiles_endpoint() {
    print_info "Testing /api/models/profiles endpoint..."

    local response=$(curl -s http://localhost:8000/api/models/profiles)
    local profile_count=$(echo "$response" | jq '.profiles | length' 2>/dev/null || echo "0")
    local active_profile=$(echo "$response" | jq -r '.active_profile' 2>/dev/null || echo "unknown")

    print_success "Profiles endpoint OK: $profile_count profiles, active: $active_profile"
    echo "  Available profiles:"
    echo "$response" | jq -r '.profiles[] | "  - \(.name)"' 2>/dev/null || echo "  (Parse error)"
    return 0
}

test_frontend() {
    print_info "Testing frontend availability..."

    if curl -sf http://localhost:5173 > /dev/null; then
        print_success "Frontend is accessible"
        return 0
    else
        print_failure "Frontend is not accessible"
        return 1
    fi
}

test_redis() {
    print_info "Testing Redis connectivity..."

    cd "$PROJECT_ROOT"

    # Test Redis connection from backend container
    if $COMPOSE_CMD $COMPOSE_FILES exec -T backend python -c "
import redis
r = redis.Redis(host='redis', port=6379, password='change_this_secure_redis_password', db=0, socket_connect_timeout=2)
r.ping()
print('OK')
" 2>&1 | grep -q "OK"; then
        print_success "Redis is accessible from backend"
        return 0
    else
        print_failure "Redis is not accessible from backend"
        return 1
    fi
}

# =============================================================================
# Main Test Flow
# =============================================================================

main() {
    print_header "S.Y.N.A.P.S.E. ENGINE Docker Test Suite"

    if [ "$DEV_MODE" = true ]; then
        print_info "Mode: Development"
    else
        print_info "Mode: Production"
    fi

    cd "$PROJECT_ROOT"

    # Check if jq is available for JSON parsing
    if ! command -v jq &> /dev/null; then
        print_warning "jq not found - JSON responses won't be pretty-printed"
        print_info "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    fi

    local tests_passed=0
    local tests_failed=0

    # Build Test
    print_header "Build Test"
    if test_build; then
        ((tests_passed++))
    else
        ((tests_failed++))
        print_failure "Build test failed - aborting"
        exit 1
    fi

    # Startup Test
    print_header "Startup Test"
    if test_startup; then
        ((tests_passed++))
    else
        ((tests_failed++))
        print_failure "Startup test failed - aborting"
        exit 1
    fi

    # Wait for Backend
    print_header "Backend Readiness Test"
    if test_wait_for_backend; then
        ((tests_passed++))
    else
        ((tests_failed++))
        print_failure "Backend readiness test failed"
        # Don't abort - show what works
    fi

    # Service Health Test
    print_header "Service Health Test"
    if test_service_health; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi

    # API Tests
    print_header "API Endpoint Tests"

    if test_health_endpoint; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi

    if test_registry_endpoint; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi

    if test_servers_endpoint; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi

    if test_profiles_endpoint; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi

    # Frontend Test
    print_header "Frontend Test"
    if test_frontend; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi

    # Redis Test
    print_header "Redis Test"
    if test_redis; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi

    # Summary
    print_header "Test Summary"
    echo "Tests passed: $tests_passed"
    echo "Tests failed: $tests_failed"

    if [ $tests_failed -eq 0 ]; then
        print_success "All tests passed!"
        echo ""
        echo "Services are running. Access the UI at:"
        echo "  http://localhost:5173/model-management"
        echo ""
        echo "View logs:"
        echo "  $COMPOSE_CMD $COMPOSE_FILES logs -f backend"
        echo ""
        echo "Stop services:"
        echo "  $COMPOSE_CMD $COMPOSE_FILES down"
        echo ""
        return 0
    else
        print_failure "Some tests failed"
        echo ""
        echo "View logs for debugging:"
        echo "  $COMPOSE_CMD $COMPOSE_FILES logs backend"
        echo "  $COMPOSE_CMD $COMPOSE_FILES logs frontend"
        echo ""
        return 1
    fi
}

# Run main function
main
exit_code=$?

# Don't cleanup if tests failed and user might want to inspect
if [ $exit_code -ne 0 ]; then
    print_warning "Services left running for inspection"
    print_info "Stop with: $COMPOSE_CMD $COMPOSE_FILES down"
    trap - EXIT  # Remove cleanup trap
fi

exit $exit_code
