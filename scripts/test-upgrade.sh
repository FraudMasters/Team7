#!/bin/bash
# TEAM7 Resume Analysis Platform - Upgrade Script Automated Test
# Tests upgrade.sh functionality without requiring full Docker deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_test_start() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}TEST: $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

log_step() {
    echo ""
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=====================================${NC}"
}

# Record test result
record_test() {
    local test_name="$1"
    local result="$2"

    if [ "$result" = "pass" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_success "✓ PASSED: $test_name"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name")
        log_error "✗ FAILED: $test_name"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test artifacts..."

    # Remove test files
    rm -f .env.test .env.backup .env.test_upgrade
    rm -rf backups_test

    # Restore original .env if backed up
    if [ -f .env.original_test_upgrade ]; then
        mv .env.original_test_upgrade .env
        log_info "Restored original .env file"
    fi
}

# Trap cleanup on script exit
trap cleanup EXIT

# Setup function
setup_test_environment() {
    log_step "Setting Up Test Environment"

    # Backup existing .env
    if [ -f .env ]; then
        cp .env .env.original_test_upgrade
    fi

    # Ensure .env.example exists
    if [ ! -f .env.example ]; then
        log_error ".env.example not found - cannot run tests"
        exit 1
    fi

    # Create .env from example for testing
    cp .env.example .env

    # Create test backup directory
    mkdir -p backups_test

    log_success "Test environment set up successfully"
}

# Test 1: Help command
test_help_command() {
    log_test_start "Help Command"

    if bash scripts/upgrade.sh --help > /dev/null 2>&1; then
        record_test "Help command executes" "pass"
    else
        record_test "Help command executes" "fail"
        return
    fi

    local help_output=$(bash scripts/upgrade.sh --help 2>&1)

    # Check for required sections
    if echo "$help_output" | grep -q "OPTIONS:"; then
        record_test "Help shows OPTIONS section" "pass"
    else
        record_test "Help shows OPTIONS section" "fail"
    fi

    if echo "$help_output" | grep -q "EXAMPLES:"; then
        record_test "Help shows EXAMPLES section" "pass"
    else
        record_test "Help shows EXAMPLES section" "fail"
    fi

    if echo "$help_output" | grep -q "UPGRADE PROCESS:"; then
        record_test "Help shows UPGRADE PROCESS section" "pass"
    else
        record_test "Help shows UPGRADE PROCESS section" "fail"
    fi

    if echo "$help_output" | grep -q "ROLLBACK PROCESS:"; then
        record_test "Help shows ROLLBACK PROCESS section" "pass"
    else
        record_test "Help shows ROLLBACK PROCESS section" "fail"
    fi
}

# Test 2: Flag validation
test_flag_validation() {
    log_test_start "Command-Line Flags"

    # Test --skip-backup flag
    if bash scripts/upgrade.sh --help | grep -q "\-\-skip-backup"; then
        record_test "--skip-backup flag documented" "pass"
    else
        record_test "--skip-backup flag documented" "fail"
    fi

    # Test --rollback flag
    if bash scripts/upgrade.sh --help | grep -q "\-\-rollback"; then
        record_test "--rollback flag documented" "pass"
    else
        record_test "--rollback flag documented" "fail"
    fi

    # Test --no-downtime flag
    if bash scripts/upgrade.sh --help | grep -q "\-\-no-downtime"; then
        record_test "--no-downtime flag documented" "pass"
    else
        record_test "--no-downtime flag documented" "fail"
    fi

    # Test --check-migrations flag
    if bash scripts/upgrade.sh --help | grep -q "\-\-check-migrations"; then
        record_test "--check-migrations flag documented" "pass"
    else
        record_test "--check-migrations flag documented" "fail"
    fi

    # Test unknown flag handling
    if bash scripts/upgrade.sh --unknown-flag 2>&1 | grep -q "Unknown option"; then
        record_test "Unknown flag rejected with error" "pass"
    else
        record_test "Unknown flag rejected with error" "fail"
    fi
}

# Test 3: Script structure validation
test_script_structure() {
    log_test_start "Script Structure"

    # Test bash syntax
    if bash -n scripts/upgrade.sh 2>/dev/null; then
        record_test "Script has valid bash syntax" "pass"
    else
        record_test "Script has valid bash syntax" "fail"
        return
    fi

    # Check for required functions
    local script_content=$(cat scripts/upgrade.sh)

    if echo "$script_content" | grep -q "^backup_database()"; then
        record_test "backup_database() function exists" "pass"
    else
        record_test "backup_database() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "^rollback_database()"; then
        record_test "rollback_database() function exists" "pass"
    else
        record_test "rollback_database() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "^perform_standard_upgrade()"; then
        record_test "perform_standard_upgrade() function exists" "pass"
    else
        record_test "perform_standard_upgrade() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "^perform_zero_downtime_upgrade()"; then
        record_test "perform_zero_downtime_upgrade() function exists" "pass"
    else
        record_test "perform_zero_downtime_upgrade() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "^check_pending_migrations()"; then
        record_test "check_pending_migrations() function exists" "pass"
    else
        record_test "check_pending_migrations() function exists" "fail"
    fi
}

# Test 4: Backup directory structure
test_backup_structure() {
    log_test_start "Backup Management"

    # Verify backup directory references
    local script_content=$(cat scripts/upgrade.sh)

    if echo "$script_content" | grep -q 'BACKUP_DIR='; then
        record_test "BACKUP_DIR variable defined" "pass"
    else
        record_test "BACKUP_DIR variable defined" "fail"
    fi

    if echo "$script_content" | grep -q 'db_backup_.*\.sql'; then
        record_test "Database backup naming convention used" "pass"
    else
        record_test "Database backup naming convention used" "fail"
    fi

    if echo "$script_content" | grep -q 'latest_backup\.sql'; then
        record_test "Latest backup symlink used" "pass"
    else
        record_test "Latest backup symlink used" "fail"
    fi

    if echo "$script_content" | grep -q 'config_.*TIMESTAMP'; then
        record_test "Config backup with timestamp used" "pass"
    else
        record_test "Config backup with timestamp used" "fail"
    fi
}

# Test 5: Health check functions
test_health_checks() {
    log_test_start "Health Check Functions"

    local script_content=$(cat scripts/upgrade.sh)

    if echo "$script_content" | grep -q "^wait_for_postgres()"; then
        record_test "wait_for_postgres() function exists" "pass"
    else
        record_test "wait_for_postgres() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "^wait_for_redis()"; then
        record_test "wait_for_redis() function exists" "pass"
    else
        record_test "wait_for_redis() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "^wait_for_http_health()"; then
        record_test "wait_for_http_health() function exists" "pass"
    else
        record_test "wait_for_http_health() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "^wait_for_services()"; then
        record_test "wait_for_services() function exists" "pass"
    else
        record_test "wait_for_services() function exists" "fail"
    fi
}

# Test 6: Upgrade workflow validation
test_upgrade_workflow() {
    log_test_start "Upgrade Workflow"

    local script_content=$(cat scripts/upgrade.sh)

    # Check standard upgrade steps
    if echo "$script_content" | grep -q "create_backup_directory"; then
        record_test "Backup directory creation in workflow" "pass"
    else
        record_test "Backup directory creation in workflow" "fail"
    fi

    if echo "$script_content" | grep -q "backup_database"; then
        record_test "Database backup in workflow" "pass"
    else
        record_test "Database backup in workflow" "fail"
    fi

    if echo "$script_content" | grep -q "docker-compose pull"; then
        record_test "Image pull in workflow" "pass"
    else
        record_test "Image pull in workflow" "fail"
    fi

    if echo "$script_content" | grep -q "docker-compose build"; then
        record_test "Image build in workflow" "pass"
    else
        record_test "Image build in workflow" "fail"
    fi

    if echo "$script_content" | grep -q "alembic upgrade head"; then
        record_test "Database migration in workflow" "pass"
    else
        record_test "Database migration in workflow" "fail"
    fi
}

# Test 7: Error handling
test_error_handling() {
    log_test_start "Error Handling"

    local script_content=$(cat scripts/upgrade.sh)

    if echo "$script_content" | grep -q "set -e"; then
        record_test "Script uses 'set -e' for error handling" "pass"
    else
        record_test "Script uses 'set -e' for error handling" "fail"
    fi

    if echo "$script_content" | grep -q "trap.*cleanup_on_error"; then
        record_test "Error trap configured" "pass"
    else
        record_test "Error trap configured" "fail"
    fi

    if echo "$script_content" | grep -q "cleanup_on_error()"; then
        record_test "cleanup_on_error() function exists" "pass"
    else
        record_test "cleanup_on_error() function exists" "fail"
    fi
}

# Test 8: Rollback workflow
test_rollback_workflow() {
    log_test_start "Rollback Workflow"

    local script_content=$(cat scripts/upgrade.sh)

    if echo "$script_content" | grep -q "perform_rollback()"; then
        record_test "perform_rollback() function exists" "pass"
    else
        record_test "perform_rollback() function exists" "fail"
    fi

    # Check rollback steps
    if echo "$script_content" | grep -q "docker-compose down"; then
        record_test "Service stop in rollback workflow" "pass"
    else
        record_test "Service stop in rollback workflow" "fail"
    fi

    if echo "$script_content" | grep -A 20 "rollback_database()" | grep -q "DROP DATABASE"; then
        record_test "Database drop in rollback" "pass"
    else
        record_test "Database drop in rollback" "fail"
    fi

    if echo "$script_content" | grep -A 20 "rollback_database()" | grep -q "CREATE DATABASE"; then
        record_test "Database recreate in rollback" "pass"
    else
        record_test "Database recreate in rollback" "fail"
    fi
}

# Test 9: Migration check functionality
test_migration_check() {
    log_test_start "Migration Check"

    local script_content=$(cat scripts/upgrade.sh)

    if echo "$script_content" | grep -q "check_pending_migrations()"; then
        record_test "check_pending_migrations() function exists" "pass"
    else
        record_test "check_pending_migrations() function exists" "fail"
    fi

    if echo "$script_content" | grep -q "alembic current"; then
        record_test "Gets current revision with alembic current" "pass"
    else
        record_test "Gets current revision with alembic current" "fail"
    fi

    if echo "$script_content" | grep -q "alembic heads"; then
        record_test "Gets target revision with alembic heads" "pass"
    else
        record_test "Gets target revision with alembic heads" "fail"
    fi
}

# Test 10: Zero-downtime upgrade
test_zero_downtime() {
    log_test_start "Zero-Downtime Upgrade"

    local script_content=$(cat scripts/upgrade.sh)

    if echo "$script_content" | grep -q "perform_zero_downtime_upgrade()"; then
        record_test "Zero-downtime function exists" "pass"
    else
        record_test "Zero-downtime function exists" "fail"
    fi

    if echo "$script_content" | grep -A 50 "perform_zero_downtime_upgrade()" | grep -q "\-\-no-deps"; then
        record_test "Uses --no-deps for rolling updates" "pass"
    else
        record_test "Uses --no-deps for rolling updates" "fail"
    fi

    if echo "$script_content" | grep -A 50 "perform_zero_downtime_upgrade()" | grep -q "Restarting backend"; then
        record_test "Restarts backend service" "pass"
    else
        record_test "Restarts backend service" "fail"
    fi
}

# Test summary
print_test_summary() {
    log_step "Test Summary"

    local total_tests=$((TESTS_PASSED + TESTS_FAILED))

    echo ""
    echo "========================================="
    echo "  Test Results"
    echo "========================================="
    echo ""
    echo "Total Tests:  $total_tests"
    echo -e "${GREEN}Passed:${NC}       $TESTS_PASSED"
    echo -e "${RED}Failed:${NC}       $TESTS_FAILED"
    echo ""

    if [ $TESTS_FAILED -gt 0 ]; then
        echo "Failed Tests:"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "${RED}  ✗ $test${NC}"
        done
        echo ""
        exit 1
    else
        log_success "All tests passed!"
        echo ""
        exit 0
    fi
}

# Main test execution
main() {
    echo "========================================="
    echo "  Upgrade Script Test Suite"
    echo "========================================="
    echo ""
    log_info "Starting automated tests for scripts/upgrade.sh"
    echo ""

    # Setup
    setup_test_environment

    # Run all tests
    test_help_command
    test_flag_validation
    test_script_structure
    test_backup_structure
    test_health_checks
    test_upgrade_workflow
    test_error_handling
    test_rollback_workflow
    test_migration_check
    test_zero_downtime

    # Print summary
    print_test_summary
}

# Run main function
main "$@"
