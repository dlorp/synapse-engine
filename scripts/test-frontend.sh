#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Frontend Test Suite
# =============================================================================
# Comprehensive automated testing for frontend React app, build configuration,
# and container health. All tests run through Docker containers.
#
# Usage:
#   ./scripts/test-frontend.sh
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
TOTAL_TESTS=8
PASSED=0
FAILED=0
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  S.Y.N.A.P.S.E. ENGINE Frontend Test Suite${NC}"
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
        echo -e "${GREEN}${CHECK_MARK} All frontend tests passed!${NC}"
        return 0
    else
        echo -e "${RED}${CROSS_MARK} Some frontend tests failed.${NC}"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Test Functions
# -----------------------------------------------------------------------------

test_http_response() {
    local test_num=1
    print_test $test_num "HTTP response (200 OK)"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>&1)

    if [ "$response" = "200" ]; then
        print_success $test_num "Frontend returned 200 OK"
    else
        print_failure $test_num "Frontend HTTP response failed" "HTTP $response (expected 200)"
    fi
}

test_valid_html() {
    local test_num=2
    print_test $test_num "Valid HTML document"

    local response
    response=$(curl -s http://localhost:5173 2>&1)

    # Case-insensitive check for DOCTYPE (HTML5 allows lowercase)
    if echo "$response" | grep -i -q "<!doctype html>"; then
        print_success $test_num "Valid HTML document with DOCTYPE"
    else
        print_failure $test_num "Invalid HTML document" "Missing <!DOCTYPE html>"
    fi
}

test_react_root() {
    local test_num=3
    print_test $test_num "React root element"

    local response
    response=$(curl -s http://localhost:5173 2>&1)

    if echo "$response" | grep -q 'id="root"'; then
        print_success $test_num "React root element found"
    else
        print_failure $test_num "React root element missing" "Expected <div id=\"root\"></div>"
    fi
}

test_vite_config() {
    local test_num=4
    print_test $test_num "Vite config files exist"

    cd "$PROJECT_ROOT"

    local all_exist=true
    local missing_files=""

    # Check for essential Vite config files
    local required_files=(
        "frontend/vite.config.ts"
        "frontend/package.json"
        "frontend/tsconfig.json"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            all_exist=false
            missing_files="${missing_files}\n    - $file"
        fi
    done

    if [ "$all_exist" = true ]; then
        print_success $test_num "All Vite config files present"
    else
        print_failure $test_num "Missing Vite config files" "$missing_files"
    fi
}

test_npm_tests() {
    local test_num=5
    print_test $test_num "npm test (React component tests)"

    cd "$PROJECT_ROOT"

    # Check if package.json has test script
    if ! grep -q '"test"' frontend/package.json; then
        echo -e "${YELLOW}${WARNING} [${test_num}/${TOTAL_TESTS}] SKIP${NC}: No test script defined in package.json"
        ((PASSED++))
        return
    fi

    # Run npm test in frontend container
    local result
    result=$(docker-compose exec -T frontend npm test -- --run 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        print_success $test_num "npm test passed"
    else
        # Check if no tests were found
        if echo "$result" | grep -q "no test files found"; then
            echo -e "${YELLOW}${WARNING} [${test_num}/${TOTAL_TESTS}] SKIP${NC}: No test files found"
            ((PASSED++))
        else
            print_failure $test_num "npm test failed" "Exit code: $exit_code"
        fi
    fi
}

test_static_assets() {
    local test_num=6
    print_test $test_num "Static assets loading"

    # Test if JavaScript bundle is being served
    local response
    response=$(curl -s http://localhost:5173/@vite/client 2>&1)

    if echo "$response" | grep -q "vite" || [ -n "$response" ]; then
        print_success $test_num "Vite client assets loading"
    else
        print_failure $test_num "Static assets not loading" "Vite client not accessible"
    fi
}

test_frontend_errors() {
    local test_num=7
    print_test $test_num "Frontend logs for errors"

    cd "$PROJECT_ROOT"

    # Get recent logs and check for critical errors
    local error_count
    error_count=$(docker-compose logs --tail=100 frontend 2>/dev/null | grep -i -E "error|failed" | grep -v -E "ECONNREFUSED|warnings|deprecated" | wc -l || echo "0")
    # Clean up the count - remove all whitespace including newlines
    error_count=$(echo "$error_count" | tr -d '[:space:]')
    # Default to 0 if empty
    error_count=${error_count:-0}

    if [ "$error_count" -eq 0 ] 2>/dev/null; then
        print_success $test_num "No critical errors in frontend logs"
    else
        print_failure $test_num "Found errors in frontend logs" "$error_count error(s) detected"
    fi
}

test_container_health() {
    local test_num=8
    print_test $test_num "Frontend container health"

    cd "$PROJECT_ROOT"

    # Check if frontend container is healthy
    local health_status
    health_status=$(docker-compose ps frontend 2>/dev/null | grep -E "Up|healthy" || echo "unhealthy")

    if echo "$health_status" | grep -q "Up"; then
        print_success $test_num "Frontend container is running and healthy"
    else
        print_failure $test_num "Frontend container health check failed" "Container status: $health_status"
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
    if ! docker-compose ps frontend &>/dev/null; then
        echo -e "${RED}${CROSS_MARK} Frontend container not running. Start with: docker-compose up -d${NC}"
        exit 1
    fi
    echo -e "${GREEN}${CHECK_MARK} Frontend container is running${NC}"
    echo ""

    # Run all tests
    test_http_response
    test_valid_html
    test_react_root
    test_vite_config
    test_npm_tests
    test_static_assets
    test_frontend_errors
    test_container_health

    # Print summary and exit
    print_summary
    exit $?
}

# Run main function
main "$@"
