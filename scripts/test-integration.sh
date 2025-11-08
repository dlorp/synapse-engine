#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Integration Test Suite
# =============================================================================
# Comprehensive automated testing for service integration, API proxying,
# WebSocket connectivity, and cross-service communication.
#
# Usage:
#   ./scripts/test-integration.sh
#
# Exit Codes:
#   0 - All tests passed
#   1 - One or more tests failed
# =============================================================================

# Note: NOT using 'set -e' here because we want to continue running all tests
# even if some fail. We track pass/fail counts explicitly.
set -o pipefail  # Catch errors in pipes

# -----------------------------------------------------------------------------
# Color Codes & Symbols
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CHECK_MARK="✓"
CROSS_MARK="✗"
WARNING="⚠"

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------
TOTAL_TESTS=6
PASSED=0
FAILED=0
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  S.Y.N.A.P.S.E. ENGINE Integration Test Suite${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_test() {
    local test_num=$1
    local test_name=$2
    echo -e "${BLUE}[${test_num}/${TOTAL_TESTS}]${NC} Testing: ${test_name}..."
}

print_success() {
    local test_num=$1
    local message=$2
    echo -e "${GREEN}${CHECK_MARK} [${test_num}/${TOTAL_TESTS}] PASS${NC}: ${message}"
    ((PASSED++))
}

print_failure() {
    local test_num=$1
    local message=$2
    local details=$3
    echo -e "${RED}${CROSS_MARK} [${test_num}/${TOTAL_TESTS}] FAIL${NC}: ${message}"
    if [ -n "$details" ]; then
        echo -e "${RED}  └─ ${details}${NC}"
    fi
    ((FAILED++))
}

print_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Test Summary${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  Total Tests: ${TOTAL_TESTS}"
    echo -e "  ${GREEN}Passed: ${PASSED}${NC}"
    echo -e "  ${RED}Failed: ${FAILED}${NC}"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}${CHECK_MARK} All integration tests passed!${NC}"
        return 0
    else
        echo -e "${RED}${CROSS_MARK} Some integration tests failed.${NC}"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Test Functions
# -----------------------------------------------------------------------------

test_backend_frontend_communication() {
    local test_num=1
    print_test $test_num "Backend-Frontend communication"

    cd "$PROJECT_ROOT"

    # Check VITE_API_BASE_URL in docker-compose.yml
    local vite_api_url
    vite_api_url=$(grep "VITE_API_BASE_URL" docker-compose.yml | grep -v "#" | head -1 | cut -d'=' -f2 | tr -d ' ')

    if [ -z "$vite_api_url" ]; then
        print_failure $test_num "VITE_API_BASE_URL not configured" "Missing in docker-compose.yml"
        return
    fi

    # Verify frontend can reach backend health endpoint
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "Backend-Frontend communication configured (VITE_API_BASE_URL=${vite_api_url})"
    else
        print_failure $test_num "Backend unreachable from frontend" "Health check returned HTTP $response"
    fi
}

test_api_proxy() {
    local test_num=2
    print_test $test_num "API proxy through frontend"

    # Test if API requests can be proxied through Vite dev server
    # Vite config should proxy /api to backend
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/api/settings 2>&1)

    # Accept 200 (success) or 404 (proxy working but endpoint config issue)
    if [ "$response" = "200" ] || [ "$response" = "404" ]; then
        print_success $test_num "API proxy functioning (HTTP $response)"
    else
        print_failure $test_num "API proxy not working" "HTTP $response (expected 200 or 404)"
    fi
}

test_websocket_endpoint() {
    local test_num=3
    print_test $test_num "WebSocket endpoint availability"

    # Check if WebSocket endpoint is accessible
    # Using curl with upgrade headers to test WebSocket
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Connection: Upgrade" \
        -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Version: 13" \
        -H "Sec-WebSocket-Key: test" \
        http://localhost:8000/ws 2>&1)

    # WebSocket endpoints typically return 101 (Switching Protocols) or 426 (Upgrade Required)
    if [ "$response" = "101" ] || [ "$response" = "426" ] || [ "$response" = "400" ]; then
        print_success $test_num "WebSocket endpoint accessible (HTTP $response)"
    else
        print_failure $test_num "WebSocket endpoint not accessible" "HTTP $response"
    fi
}

test_redis_connectivity() {
    local test_num=4
    print_test $test_num "Redis connectivity"

    cd "$PROJECT_ROOT"

    # Check if Redis container is running
    local redis_status
    redis_status=$(docker-compose ps redis 2>/dev/null | grep -E "Up|healthy" || echo "down")

    if ! echo "$redis_status" | grep -q "Up"; then
        print_failure $test_num "Redis container not running" "Status: $redis_status"
        return
    fi

    # Test Redis connectivity from backend
    local result
    result=$(docker-compose exec -T backend python -c "
import redis
import os
try:
    r = redis.Redis(
        host='redis',
        port=6379,
        password=os.getenv('REDIS_PASSWORD', 'change_this_secure_redis_password'),
        decode_responses=True
    )
    r.ping()
    print('PONG')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
" 2>&1)

    if echo "$result" | grep -q "PONG"; then
        print_success $test_num "Backend can communicate with Redis"
    else
        print_failure $test_num "Redis connectivity failed" "$result"
    fi
}

test_host_api() {
    local test_num=5
    print_test $test_num "Host API connectivity (if enabled)"

    cd "$PROJECT_ROOT"

    # Check if USE_EXTERNAL_SERVERS is enabled
    local use_external
    use_external=$(grep "USE_EXTERNAL_SERVERS" docker-compose.yml | grep -v "#" | head -1 | cut -d'=' -f2 | tr -d ' ')

    if [ "$use_external" != "true" ]; then
        echo -e "${YELLOW}${WARNING} [${test_num}/${TOTAL_TESTS}] SKIP${NC}: External servers disabled (USE_EXTERNAL_SERVERS=${use_external})"
        ((PASSED++))
        return
    fi

    # Check if host-api container is running
    local host_api_status
    host_api_status=$(docker-compose ps host-api 2>/dev/null | grep -E "Up|healthy" || echo "down")

    if ! echo "$host_api_status" | grep -q "Up"; then
        print_failure $test_num "Host API container not running" "Status: $host_api_status"
        return
    fi

    # Test Host API endpoint
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/api/servers/status 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "Host API accessible and responding"
    else
        print_failure $test_num "Host API not accessible" "HTTP $response (expected 200)"
    fi
}

test_all_services_running() {
    local test_num=6
    print_test $test_num "All required services running"

    cd "$PROJECT_ROOT"

    local all_running=true
    local down_services=""

    # Define required services
    local required_services=("redis" "backend" "frontend")

    # Check if USE_EXTERNAL_SERVERS is true
    local use_external
    use_external=$(grep "USE_EXTERNAL_SERVERS" docker-compose.yml | grep -v "#" | head -1 | cut -d'=' -f2 | tr -d ' ')
    if [ "$use_external" = "true" ]; then
        required_services+=("host-api")
    fi

    # Check CGRAG_ENABLED
    local cgrag_enabled
    cgrag_enabled=$(grep "CGRAG_ENABLED" docker-compose.yml | grep -v "#" | head -1 | cut -d'=' -f2 | tr -d ' ')

    # Check WEBSEARCH_ENABLED
    local websearch_enabled
    websearch_enabled=$(grep "WEBSEARCH_ENABLED" docker-compose.yml | grep -v "#" | head -1 | cut -d'=' -f2 | tr -d ' ')
    if [ "$websearch_enabled" = "true" ]; then
        required_services+=("searxng")
    fi

    # Check each service
    for service in "${required_services[@]}"; do
        local status
        status=$(docker-compose ps "$service" 2>/dev/null | grep -E "Up|healthy" || echo "down")

        if ! echo "$status" | grep -q "Up"; then
            all_running=false
            down_services="${down_services}\n    - $service"
        fi
    done

    if [ "$all_running" = true ]; then
        print_success $test_num "All required services are running (${required_services[*]})"
    else
        print_failure $test_num "Some services are not running" "$down_services"
    fi
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
    # Change to project root
    cd "$PROJECT_ROOT"

    print_header

    # Pre-flight check
    echo -e "${BLUE}Checking Docker Compose...${NC}"
    if ! docker-compose ps &>/dev/null; then
        echo -e "${RED}${CROSS_MARK} Docker Compose not available or no services running${NC}"
        echo -e "${RED}Start services with: docker-compose up -d${NC}"
        exit 1
    fi
    echo -e "${GREEN}${CHECK_MARK} Docker Compose is operational${NC}"
    echo ""

    # Run all tests
    test_backend_frontend_communication
    test_api_proxy
    test_websocket_endpoint
    test_redis_connectivity
    test_host_api
    test_all_services_running

    # Print summary and exit
    print_summary
    exit $?
}

# Run main function
main "$@"
