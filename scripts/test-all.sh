#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE Master Test Runner
# =============================================================================
# Comprehensive test suite runner that executes all test scripts:
# - Backend API tests
# - Frontend React tests
# - Integration tests
# - Pre-flight checks
# - Final summary report
#
# Usage:
#   ./scripts/test-all.sh
#
# Exit Codes:
#   0 - All tests passed
#   1 - One or more tests failed
# =============================================================================

# Note: NOT using 'set -e' here because we want to run all test suites
# even if one fails. We track pass/fail explicitly for each suite.
set -o pipefail  # Catch errors in pipes

# -----------------------------------------------------------------------------
# Color Codes & Symbols
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

CHECK_MARK="✓"
CROSS_MARK="✗"
WARNING="⚠"
ROCKET="🚀"

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Test suite results
BACKEND_RESULT=0
FRONTEND_RESULT=0
INTEGRATION_RESULT=0

TOTAL_SUITES=3
PASSED_SUITES=0
FAILED_SUITES=0

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                          ║"
    echo "║               S.Y.N.A.P.S.E. ENGINE COMPREHENSIVE TEST SUITE             ║"
    echo "║                                                                          ║"
    echo "║              Multi-Model Orchestration WebUI - Test Runner              ║"
    echo "║                                                                          ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

print_section() {
    local title=$1
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $title${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_info() {
    local message=$1
    echo -e "${BLUE}ℹ${NC}  $message"
}

print_success() {
    local message=$1
    echo -e "${GREEN}${CHECK_MARK}${NC}  $message"
}

print_failure() {
    local message=$1
    echo -e "${RED}${CROSS_MARK}${NC}  $message"
}

print_warning() {
    local message=$1
    echo -e "${YELLOW}${WARNING}${NC}  $message"
}

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

run_preflight_checks() {
    print_section "Pre-Flight Checks"

    local all_checks_passed=true

    # Check 1: Docker is running
    print_info "Checking Docker daemon..."
    if docker info &>/dev/null; then
        print_success "Docker daemon is running"
    else
        print_failure "Docker daemon is not running"
        echo -e "${RED}  Please start Docker and try again${NC}"
        exit 1
    fi

    # Check 2: Docker Compose is available
    print_info "Checking Docker Compose..."
    if docker-compose version &>/dev/null; then
        local compose_version
        compose_version=$(docker-compose version --short 2>/dev/null || echo "unknown")
        print_success "Docker Compose is available (version: $compose_version)"
    else
        print_failure "Docker Compose is not available"
        exit 1
    fi

    # Check 3: Project structure
    print_info "Checking project structure..."
    local required_dirs=("backend" "frontend" "scripts" "config")
    local missing_dirs=""
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$PROJECT_ROOT/$dir" ]; then
            missing_dirs="${missing_dirs} $dir"
        fi
    done

    if [ -z "$missing_dirs" ]; then
        print_success "Project structure is valid"
    else
        print_failure "Missing directories:$missing_dirs"
        all_checks_passed=false
    fi

    # Check 4: Docker Compose services
    print_info "Checking Docker Compose services..."
    cd "$PROJECT_ROOT"
    if docker-compose ps &>/dev/null; then
        print_success "Docker Compose configuration is valid"
    else
        print_failure "Docker Compose configuration error"
        exit 1
    fi

    # Check 5: Required services are running
    print_info "Checking required services status..."
    local required_services=("redis" "backend" "frontend")
    local down_services=""

    for service in "${required_services[@]}"; do
        if ! docker-compose ps "$service" 2>/dev/null | grep -q "Up"; then
            down_services="${down_services} $service"
        fi
    done

    if [ -z "$down_services" ]; then
        print_success "All required services are running"
    else
        print_failure "Services not running:$down_services"
        echo -e "${YELLOW}  Starting services with: docker-compose up -d${NC}"
        docker-compose up -d
        echo -e "${YELLOW}  Waiting 10 seconds for services to initialize...${NC}"
        sleep 10
    fi

    # Check 6: Test scripts are executable
    print_info "Checking test scripts..."
    local test_scripts=(
        "$SCRIPT_DIR/test-backend.sh"
        "$SCRIPT_DIR/test-frontend.sh"
        "$SCRIPT_DIR/test-integration.sh"
    )
    local non_executable=""

    for script in "${test_scripts[@]}"; do
        if [ ! -f "$script" ]; then
            print_failure "Test script not found: $(basename "$script")"
            exit 1
        fi
        if [ ! -x "$script" ]; then
            non_executable="${non_executable} $(basename "$script")"
        fi
    done

    if [ -z "$non_executable" ]; then
        print_success "All test scripts are executable"
    else
        print_warning "Making scripts executable:$non_executable"
        chmod +x "${test_scripts[@]}"
        print_success "Scripts are now executable"
    fi

    echo ""
    if [ "$all_checks_passed" = true ]; then
        print_success "All pre-flight checks passed!"
    else
        print_failure "Some pre-flight checks failed"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Test Suite Runners
# -----------------------------------------------------------------------------

run_backend_tests() {
    print_section "Backend Test Suite"

    if [ -x "$SCRIPT_DIR/test-backend.sh" ]; then
        if "$SCRIPT_DIR/test-backend.sh"; then
            BACKEND_RESULT=0
            ((PASSED_SUITES++))
            echo ""
            print_success "Backend test suite completed successfully"
        else
            BACKEND_RESULT=1
            ((FAILED_SUITES++))
            echo ""
            print_failure "Backend test suite failed"
        fi
    else
        print_failure "Backend test script not found or not executable"
        BACKEND_RESULT=1
        ((FAILED_SUITES++))
    fi
}

run_frontend_tests() {
    print_section "Frontend Test Suite"

    if [ -x "$SCRIPT_DIR/test-frontend.sh" ]; then
        if "$SCRIPT_DIR/test-frontend.sh"; then
            FRONTEND_RESULT=0
            ((PASSED_SUITES++))
            echo ""
            print_success "Frontend test suite completed successfully"
        else
            FRONTEND_RESULT=1
            ((FAILED_SUITES++))
            echo ""
            print_failure "Frontend test suite failed"
        fi
    else
        print_failure "Frontend test script not found or not executable"
        FRONTEND_RESULT=1
        ((FAILED_SUITES++))
    fi
}

run_integration_tests() {
    print_section "Integration Test Suite"

    if [ -x "$SCRIPT_DIR/test-integration.sh" ]; then
        if "$SCRIPT_DIR/test-integration.sh"; then
            INTEGRATION_RESULT=0
            ((PASSED_SUITES++))
            echo ""
            print_success "Integration test suite completed successfully"
        else
            INTEGRATION_RESULT=1
            ((FAILED_SUITES++))
            echo ""
            print_failure "Integration test suite failed"
        fi
    else
        print_failure "Integration test script not found or not executable"
        INTEGRATION_RESULT=1
        ((FAILED_SUITES++))
    fi
}

# -----------------------------------------------------------------------------
# Final Summary
# -----------------------------------------------------------------------------

print_final_summary() {
    print_section "Final Summary"

    echo -e "${CYAN}Test Suite Results:${NC}"
    echo ""

    # Backend results
    if [ $BACKEND_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}${CHECK_MARK} Backend Tests${NC}      - PASSED"
    else
        echo -e "  ${RED}${CROSS_MARK} Backend Tests${NC}      - FAILED"
    fi

    # Frontend results
    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}${CHECK_MARK} Frontend Tests${NC}     - PASSED"
    else
        echo -e "  ${RED}${CROSS_MARK} Frontend Tests${NC}     - FAILED"
    fi

    # Integration results
    if [ $INTEGRATION_RESULT -eq 0 ]; then
        echo -e "  ${GREEN}${CHECK_MARK} Integration Tests${NC}  - PASSED"
    else
        echo -e "  ${RED}${CROSS_MARK} Integration Tests${NC}  - FAILED"
    fi

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  Total Test Suites: ${TOTAL_SUITES}"
    echo -e "  ${GREEN}Passed: ${PASSED_SUITES}${NC}"
    echo -e "  ${RED}Failed: ${FAILED_SUITES}${NC}"
    echo ""

    if [ $FAILED_SUITES -eq 0 ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                                      ║${NC}"
        echo -e "${GREEN}║                  ${CHECK_MARK} ALL TESTS PASSED! ${CHECK_MARK}                               ║${NC}"
        echo -e "${GREEN}║                                                                      ║${NC}"
        echo -e "${GREEN}║         File reorganization did not break anything! ${ROCKET}              ║${NC}"
        echo -e "${GREEN}║                                                                      ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}╔══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                                      ║${NC}"
        echo -e "${RED}║                   ${CROSS_MARK} SOME TESTS FAILED ${CROSS_MARK}                              ║${NC}"
        echo -e "${RED}║                                                                      ║${NC}"
        echo -e "${RED}║              Please review the test output above                    ║${NC}"
        echo -e "${RED}║                                                                      ║${NC}"
        echo -e "${RED}╚══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}Troubleshooting Tips:${NC}"
        echo -e "  1. Check Docker logs: ${CYAN}docker-compose logs -f${NC}"
        echo -e "  2. Verify services: ${CYAN}docker-compose ps${NC}"
        echo -e "  3. Rebuild containers: ${CYAN}docker-compose build --no-cache${NC}"
        echo -e "  4. Restart services: ${CYAN}docker-compose restart${NC}"
        echo ""
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

main() {
    # Change to project root
    cd "$PROJECT_ROOT"

    # Print banner
    print_banner

    # Get start time
    local start_time
    start_time=$(date +%s)

    # Run pre-flight checks
    run_preflight_checks

    # Run all test suites
    # Even if one fails, continue with others (set +e temporarily)
    set +e

    run_backend_tests
    run_frontend_tests
    run_integration_tests

    set -e

    # Get end time and calculate duration
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    echo -e "${BLUE}Total execution time: ${duration} seconds${NC}"

    # Print final summary
    print_final_summary
    local exit_code=$?

    exit $exit_code
}

# Run main function
main "$@"
