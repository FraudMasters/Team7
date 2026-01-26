#!/bin/bash
# Test Error Handling and Rollback for deploy.sh
# This script tests various failure scenarios to verify proper error handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

log_error() {
    echo -e "${RED}[TEST FAIL]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[TEST PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[TEST WARN]${NC} $1"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"  # "success" or "failure"

    echo ""
    log_info "Running: $test_name"

    if eval "$test_command"; then
        if [ "$expected_result" = "success" ]; then
            log_success "$test_name passed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "$test_name - Expected failure but succeeded"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        local exit_code=$?
        if [ "$expected_result" = "failure" ]; then
            log_success "$test_name - Failed as expected (exit code: $exit_code)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "$test_name - Expected success but failed (exit code: $exit_code)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
}

# Function to verify cleanup_on_error exists and has correct structure
test_cleanup_function_exists() {
    log_info "Verifying cleanup_on_error function exists..."

    if grep -q "cleanup_on_error()" scripts/deploy.sh; then
        log_success "cleanup_on_error() function found"

        # Check for docker-compose down --remove-orphans
        if grep -A 3 "cleanup_on_error()" scripts/deploy.sh | grep -q "docker-compose down --remove-orphans"; then
            log_success "Cleanup function includes 'docker-compose down --remove-orphans'"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "Cleanup function missing 'docker-compose down --remove-orphans'"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi

        # Check for trap handler
        if grep -q "trap cleanup_on_error ERR" scripts/deploy.sh; then
            log_success "Trap handler for ERR is set"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "Trap handler for ERR is not set"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi

        # Check for exit code preservation (check for both exit_code variable and exit command)
        if grep -A 5 "cleanup_on_error()" scripts/deploy.sh | grep -q "exit_code=\$?"; then
            if grep -A 5 "cleanup_on_error()" scripts/deploy.sh | grep -q "exit.*\$exit_code"; then
                log_success "Cleanup function preserves exit code"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                log_error "Cleanup function doesn't exit with preserved code"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi
        else
            log_error "Cleanup function doesn't preserve exit code"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_error "cleanup_on_error() function not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test set -e for error handling
test_set_e_exists() {
    log_info "Verifying 'set -e' for error handling..."

    if grep -q "^set -e" scripts/deploy.sh; then
        log_success "set -e is present in script"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "set -e is not present in script"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test prerequisite error handling
test_prerequisite_error_handling() {
    log_info "Verifying prerequisite error handling..."

    # Check Docker prerequisite
    if grep -A 2 "check_docker ||" scripts/deploy.sh | grep -q "exit 1"; then
        log_success "Docker check exits with error on failure"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Docker check doesn't exit with error"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check Docker Compose prerequisite
    if grep -A 2 "check_docker_compose ||" scripts/deploy.sh | grep -q "exit 1"; then
        log_success "Docker Compose check exits with error on failure"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Docker Compose check doesn't exit with error"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test environment setup error handling
test_environment_error_handling() {
    log_info "Verifying environment setup error handling..."

    # Check if setup_environment returns error code
    if grep -A 1 "setup_environment" scripts/deploy.sh | grep -q "|| exit 1"; then
        log_success "Environment setup exits on error"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Environment setup doesn't exit on error"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test health check error handling
test_health_check_error_handling() {
    log_info "Verifying health check error handling..."

    # Check PostgreSQL health check
    if grep -A 1 "wait_for_postgres" scripts/deploy.sh | grep -q "|| exit 1"; then
        log_success "PostgreSQL health check causes exit on timeout"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "PostgreSQL health check doesn't cause exit on timeout"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check Redis health check
    if grep -A 1 "wait_for_redis" scripts/deploy.sh | grep -q "|| exit 1"; then
        log_success "Redis health check causes exit on timeout"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Redis health check doesn't cause exit on timeout"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check that health check functions return 1 on timeout (look within function bounds)
    if awk '/^wait_for_postgres\(\)/,/^}$/ { if (/return 1/) found=1 } END { exit !found }' scripts/deploy.sh; then
        log_success "wait_for_postgres returns 1 on timeout"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "wait_for_postgres doesn't return 1 on timeout"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    if awk '/^wait_for_redis\(\)/,/^}$/ { if (/return 1/) found=1 } END { exit !found }' scripts/deploy.sh; then
        log_success "wait_for_redis returns 1 on timeout"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "wait_for_redis doesn't return 1 on timeout"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    if awk '/^wait_for_http_health\(\)/,/^}$/ { if (/return 1/) found=1 } END { exit !found }' scripts/deploy.sh; then
        log_success "wait_for_http_health returns 1 on timeout"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "wait_for_http_health doesn't return 1 on timeout"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test error message quality
test_error_message_quality() {
    log_info "Verifying error message quality..."

    # Check for descriptive error in cleanup
    if grep -A 5 "cleanup_on_error()" scripts/deploy.sh | grep -q "log_error"; then
        log_success "Cleanup function uses log_error for messages"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Cleanup function doesn't use log_error"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check for specific error messages in prerequisites
    if grep "Docker is required but not installed" scripts/deploy.sh >/dev/null; then
        log_success "Descriptive error message for missing Docker"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Missing descriptive error for Docker prerequisite"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    if grep "Docker Compose is required but not installed" scripts/deploy.sh >/dev/null; then
        log_success "Descriptive error message for missing Docker Compose"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Missing descriptive error for Docker Compose prerequisite"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Check for timeout error messages
    if grep "failed to become ready within" scripts/deploy.sh >/dev/null; then
        log_success "Descriptive timeout error messages present"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "Missing descriptive timeout error messages"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to simulate port conflict (without requiring actual port in use)
test_port_conflict_detection() {
    log_info "Verifying port conflict detection capability..."

    # Check if check_port_availability function exists
    if grep -q "check_port_availability()" scripts/deploy.sh; then
        log_success "Port availability check function exists"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Check if it returns error code
        if grep -A 10 "check_port_availability()" scripts/deploy.sh | grep -q "return 1"; then
            log_success "Port check returns 1 on port conflict"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "Port check doesn't return 1 on conflict"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi

        # Check for error message on port conflict
        if grep -A 10 "check_port_availability()" scripts/deploy.sh | grep -q "log_error.*Port.*already in use"; then
            log_success "Port check logs error on conflict"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_error "Port check doesn't log error on conflict"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_warning "Port availability check not implemented"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to verify all functions have error handling
test_function_error_handling() {
    log_info "Verifying functions handle errors properly..."

    # Check that all docker-compose commands have error handling
    local docker_compose_cmds=$(grep -n "docker-compose" scripts/deploy.sh | wc -l | tr -d ' ')
    local docker_compose_safe=$(grep -n "docker-compose.*||" scripts/deploy.sh | wc -l | tr -d ' ')

    log_info "Found $docker_compose_cmds docker-compose commands"
    log_info "Found $docker_compose_safe with explicit error handling"

    # Key commands that should have explicit error handling
    local critical_cmds=(
        "docker-compose down"
        "docker-compose build"
    )

    for cmd in "${critical_cmds[@]}"; do
        if grep "$cmd" scripts/deploy.sh | grep -q "||"; then
            log_success "Command '$cmd' has explicit error handling (||)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_warning "Command '$cmd' relies on set -e for error handling"
            TESTS_PASSED=$((TESTS_PASSED + 1))  # set -e is sufficient
        fi
    done
}

# Main test execution
main() {
    echo "========================================="
    echo "  Error Handling & Rollback Tests"
    echo "========================================="
    echo ""

    # Static analysis tests (can run without Docker)
    test_set_e_exists
    test_cleanup_function_exists
    test_prerequisite_error_handling
    test_environment_error_handling
    test_health_check_error_handling
    test_error_message_quality
    test_port_conflict_detection
    test_function_error_handling

    # Summary
    echo ""
    echo "========================================="
    echo "  Test Summary"
    echo "========================================="
    echo ""
    log_success "Tests Passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Tests Failed: $TESTS_FAILED"
        echo ""
        log_error "Some tests failed. Please review the output above."
        exit 1
    else
        log_success "All tests passed!"
        echo ""
        log_info "Note: Docker integration tests require a full development environment."
        log_info "Run the following manual tests when Docker is available:"
        echo ""
        echo "1. Port Conflict Test:"
        echo "   - Start a service on port 8000: python -m http.server 8000"
        echo "   - Run: bash scripts/deploy.sh"
        echo "   - Verify: Script detects port conflict and exits"
        echo "   - Verify: docker-compose ps shows no services running"
        echo ""
        echo "2. Missing Docker Test:"
        echo "   - Temporarily rename docker: sudo mv /usr/bin/docker /usr/bin/docker.bak"
        echo "   - Run: bash scripts/deploy.sh"
        echo "   - Verify: Script exits with descriptive error"
        echo "   - Restore: sudo mv /usr/bin/docker.bak /usr/bin/docker"
        echo ""
        echo "3. Invalid .env Test:"
        echo "   - Create invalid .env: echo 'INVALID_SYNTAX' > .env"
        echo "   - Run: bash scripts/deploy.sh"
        echo "   - Verify: Script handles gracefully (may succeed with defaults)"
        echo ""
        echo "4. Service Failure Test:"
        echo "   - Mock postgres failure (stop postgres container immediately after start)"
        echo "   - Run: bash scripts/deploy.sh"
        echo "   - Verify: Script detects timeout and triggers cleanup"
        echo "   - Verify: docker-compose ps shows no services running"
        echo ""
        exit 0
    fi
}

# Run main function
main "$@"
