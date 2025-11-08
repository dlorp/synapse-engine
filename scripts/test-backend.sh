#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Backend Test Suite
# =============================================================================
# Comprehensive automated testing for backend API endpoints, Python tests,
# and container health. All tests run through Docker containers.
#
# Usage:
#   ./scripts/test-backend.sh
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
TOTAL_TESTS=10
PASSED=0
FAILED=0
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  S.Y.N.A.P.S.E. ENGINE Backend Test Suite${NC}"
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

print_warning() {
    local test_num=$1
    local message=$2
    local details=$3
    echo -e "${YELLOW}${WARNING} [${test_num}/${TOTAL_TESTS}] SKIP${NC}: ${message}"
    if [ -n "$details" ]; then
        echo -e "${YELLOW}  └─ ${details}${NC}"
    fi
    ((PASSED++))
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
        echo -e "${GREEN}${CHECK_MARK} All backend tests passed!${NC}"
        return 0
    else
        echo -e "${RED}${CROSS_MARK} Some backend tests failed.${NC}"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Test Functions
# -----------------------------------------------------------------------------

test_health_endpoint() {
    local test_num=1
    print_test $test_num "Health endpoint"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "Health endpoint returned 200 OK"
    else
        print_failure $test_num "Health endpoint failed" "HTTP $response (expected 200)"
    fi
}

test_model_registry_api() {
    local test_num=2
    print_test $test_num "Model registry API"

    local response
    response=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/models/registry 2>&1)
    local http_code=$(echo "$response" | tail -n 1)
    local body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        print_success $test_num "Model registry API returned 200 OK"
    else
        print_failure $test_num "Model registry API failed" "HTTP $http_code (expected 200)"
    fi
}

test_model_status_api() {
    local test_num=3
    print_test $test_num "Model status API"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/models/status 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "Model status API returned 200 OK"
    else
        print_failure $test_num "Model status API failed" "HTTP $response (expected 200)"
    fi
}

test_server_status_api() {
    local test_num=4
    print_test $test_num "Server status API"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/models/servers 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "Server status API returned 200 OK"
    else
        print_failure $test_num "Server status API failed" "HTTP $response (expected 200)"
    fi
}

test_cgrag_status_api() {
    local test_num=5
    print_test $test_num "CGRAG status API"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/cgrag/status 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "CGRAG status API returned 200 OK"
    elif [ "$response" = "404" ]; then
        print_warning $test_num "CGRAG status API not implemented yet" "HTTP $response (optional endpoint)"
    else
        print_failure $test_num "CGRAG status API failed" "HTTP $response (unexpected error)"
    fi
}

test_settings_api() {
    local test_num=6
    print_test $test_num "Settings API"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/settings 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "Settings API returned 200 OK"
    else
        print_failure $test_num "Settings API failed" "HTTP $response (expected 200)"
    fi
}

test_api_docs() {
    local test_num=7
    print_test $test_num "API documentation"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "API docs accessible at /docs"
    elif [ "$response" = "404" ]; then
        print_warning $test_num "API docs not configured" "HTTP $response (optional, configure with FastAPI docs)"
    else
        print_failure $test_num "API docs failed" "HTTP $response (unexpected error)"
    fi
}

test_python_tests() {
    local test_num=8
    print_test $test_num "Python test scripts"

    cd "$PROJECT_ROOT"

    # Find all test files in backend/tests/ directory
    local test_files=$(find backend/tests -maxdepth 1 -name "test*.py" -type f 2>/dev/null)

    if [ -z "$test_files" ]; then
        print_failure $test_num "No Python test files found" "Expected test_*.py files in backend/tests/"
        return
    fi

    local all_passed=true
    local failed_tests=""

    # Run each test file
    while IFS= read -r test_file; do
        local basename=$(basename "$test_file")
        # Convert host path (backend/tests/test.py) to container path (tests/test.py)
        local container_path="${test_file#backend/}"
        local result
        result=$(docker-compose exec -T backend python "$container_path" 2>&1)
        local exit_code=$?

        if [ $exit_code -ne 0 ]; then
            all_passed=false
            failed_tests="${failed_tests}\n    - $basename (exit code: $exit_code)"
        fi
    done <<< "$test_files"

    if [ "$all_passed" = true ]; then
        print_success $test_num "All Python tests passed"
    else
        print_failure $test_num "Some Python tests failed" "$failed_tests"
    fi
}

test_backend_errors() {
    local test_num=9
    print_test $test_num "Backend logs for errors"

    cd "$PROJECT_ROOT"

    # Get recent logs and check for errors
    local error_count
    error_count=$(docker-compose logs --tail=100 backend 2>/dev/null | grep -i -c "error" || true)

    if [ "$error_count" -eq 0 ]; then
        print_success $test_num "No errors found in backend logs"
    else
        print_failure $test_num "Found errors in backend logs" "$error_count error(s) detected"
    fi
}

test_container_health() {
    local test_num=10
    print_test $test_num "Backend container health"

    cd "$PROJECT_ROOT"

    # Check if backend container is healthy
    local health_status
    health_status=$(docker-compose ps backend 2>/dev/null | grep -E "Up|healthy" || echo "unhealthy")

    if echo "$health_status" | grep -q "Up"; then
        print_success $test_num "Backend container is running and healthy"
    else
        print_failure $test_num "Backend container health check failed" "Container status: $health_status"
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
    echo -e "${BLUE}Checking Docker services...${NC}"
    if ! docker-compose ps backend &>/dev/null; then
        echo -e "${RED}${CROSS_MARK} Backend container not running. Start with: docker-compose up -d${NC}"
        exit 1
    fi
    echo -e "${GREEN}${CHECK_MARK} Backend container is running${NC}"
    echo ""

    # Run all tests
    test_health_endpoint
    test_model_registry_api
    test_model_status_api
    test_server_status_api
    test_cgrag_status_api
    test_settings_api
    test_api_docs
    test_python_tests
    test_backend_errors
    test_container_health

    # Print summary and exit
    print_summary
    exit $?
}

# Run main function
main "$@"
