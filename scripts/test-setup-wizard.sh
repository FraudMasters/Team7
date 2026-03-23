#!/bin/bash
# TEAM7 Resume Analysis Platform - Setup Wizard Automated Test Script
# Tests setup wizard functionality that doesn't require Docker daemon

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
    rm -f .env.test .env.backup .env.invalid .env.test_backup .env.flag_test_backup

    # Restore original .env if backed up
    if [ -f .env.original_test ]; then
        mv .env.original_test .env
        log_info "Restored original .env file"
    fi
}

# Trap cleanup on script exit
trap cleanup EXIT

# Setup function - ensure we have a valid .env for testing
setup_test_environment() {
    # Backup existing .env
    if [ -f .env ]; then
        cp .env .env.original_test
    fi

    # Ensure .env.example exists
    if [ ! -f .env.example ]; then
        log_error ".env.example not found - cannot run tests"
        exit 1
    fi

    # Create .env from example for testing
    cp .env.example .env
}

# Test 1: Help command
test_help_command() {
    log_test_start "Help Command"

    if bash scripts/setup-wizard.sh --help 2>&1 | grep -q "USAGE"; then
        record_test "Help displays usage information" "pass"
    else
        record_test "Help displays usage information" "fail"
    fi

    if bash scripts/setup-wizard.sh --help 2>&1 | grep -q "profile"; then
        record_test "Help documents profile option" "pass"
    else
        record_test "Help documents profile option" "fail"
    fi
}

# Test 2: Dry-run mode
test_dry_run_mode() {
    log_test_start "Dry-Run Mode"

    if bash scripts/setup-wizard.sh --dry-run --profile core 2>&1 | grep -q "DRY RUN"; then
        record_test "Dry-run mode indicates no changes" "pass"
    else
        record_test "Dry-run mode indicates no changes" "fail"
    fi

    if bash scripts/setup-wizard.sh --dry-run --profile core > /dev/null 2>&1; then
        record_test "Dry-run completes successfully" "pass"
    else
        record_test "Dry-run completes successfully" "fail"
    fi
}

# Test 3: Profile validation
test_profile_validation() {
    log_test_start "Profile Validation"

    # Test valid profiles
    for profile in minimal core monitoring-only; do
        if bash scripts/setup-wizard.sh --dry-run --profile "$profile" > /dev/null 2>&1; then
            record_test "Accepts valid profile: $profile" "pass"
        else
            record_test "Accepts valid profile: $profile" "fail"
        fi
    done

    # Test invalid profile
    if bash scripts/setup-wizard.sh --dry-run --profile invalid-profile > /dev/null 2>&1; then
        record_test "Rejects invalid profile" "fail"
    else
        record_test "Rejects invalid profile" "pass"
    fi
}

# Test 4: Environment file creation
test_env_creation() {
    log_test_start "Environment File Creation"

    # Remove .env temporarily
    rm -f .env

    # Run dry-run which should note .env would be created
    local output=$(bash scripts/setup-wizard.sh --dry-run --non-interactive --profile core 2>&1)

    if echo "$output" | grep -q "Would copy .env.example to .env\|Using default configuration"; then
        record_test ".env creation is handled" "pass"
    else
        record_test ".env creation is handled" "fail"
    fi

    # Restore .env
    cp .env.example .env
}

# Test 5: Required variables validation
test_required_variables() {
    log_test_start "Required Variables Validation"

    # Ensure complete .env
    cp .env.example .env

    # Run validation
    if bash scripts/setup-wizard.sh --dry-run --profile core 2>&1 | grep -q "is configured"; then
        record_test "Validates required variables" "pass"
    else
        record_test "Validates required variables" "fail"
    fi
}

# Test 6: Invalid configuration detection
test_invalid_config() {
    log_test_start "Invalid Configuration Detection"

    # Create invalid .env
    cat > .env << 'EOF'
POSTGRES_USER=testuser
# Missing critical variables
EOF

    # Should fail validation
    if bash scripts/setup-wizard.sh --dry-run --non-interactive 2>&1 | grep -q "not set\|validation failed"; then
        record_test "Detects missing variables" "pass"
    else
        record_test "Detects missing variables" "fail"
    fi

    # Restore valid .env
    cp .env.example .env
}

# Test 7: DATABASE_URL validation
test_database_url_validation() {
    log_test_start "DATABASE_URL Validation"

    # Ensure valid .env
    cp .env.example .env

    # Should validate DATABASE_URL format
    if bash scripts/setup-wizard.sh --dry-run --profile core 2>&1 | grep -q "DATABASE_URL.*valid"; then
        record_test "Validates DATABASE_URL format" "pass"
    else
        record_test "Validates DATABASE_URL format" "fail"
    fi
}

# Test 8: Health check integration
test_health_check_integration() {
    log_test_start "Health Check Integration"

    if [ ! -f scripts/health-check.sh ]; then
        record_test "Health check script exists" "fail"
        return
    fi

    record_test "Health check script exists" "pass"

    # Check if wizard mentions health check
    if bash scripts/setup-wizard.sh --dry-run --profile core 2>&1 | grep -q -i "health"; then
        record_test "Wizard integrates health checks" "pass"
    else
        record_test "Wizard integrates health checks" "fail"
    fi
}

# Test 9: Command-line flags
test_command_flags() {
    log_test_start "Command-Line Flags"

    # Test --validate-only (as dry-run)
    if bash scripts/setup-wizard.sh --dry-run --validate-only 2>&1 | grep -q "Validation"; then
        record_test "--validate-only flag works" "pass"
    else
        record_test "--validate-only flag works" "fail"
    fi

    # Test --non-interactive
    if bash scripts/setup-wizard.sh --dry-run --non-interactive --profile core > /dev/null 2>&1; then
        record_test "--non-interactive flag works" "pass"
    else
        record_test "--non-interactive flag works" "fail"
    fi

    # Test --skip-health-check
    if bash scripts/setup-wizard.sh --dry-run --skip-health-check --profile core > /dev/null 2>&1; then
        record_test "--skip-health-check flag works" "pass"
    else
        record_test "--skip-health-check flag works" "fail"
    fi
}

# Test 10: Error handling
test_error_handling() {
    log_test_start "Error Handling"

    # Test unknown flag
    if bash scripts/setup-wizard.sh --unknown-flag 2>&1 | grep -q "Unknown option"; then
        record_test "Rejects unknown flags" "pass"
    else
        record_test "Rejects unknown flags" "fail"
    fi
}

# Test 11: Profile-specific configurations
test_profile_configs() {
    log_test_start "Profile-Specific Configurations"

    # Each profile should complete in dry-run
    local profiles=("minimal" "core" "monitoring-only")

    for profile in "${profiles[@]}"; do
        if bash scripts/setup-wizard.sh --dry-run --profile "$profile" 2>&1 | grep -q "$profile"; then
            record_test "Profile $profile has configuration" "pass"
        else
            record_test "Profile $profile has configuration" "fail"
        fi
    done
}

# Test 12: Prerequisites check
test_prerequisites() {
    log_test_start "Prerequisites Check"

    if bash scripts/setup-wizard.sh --dry-run --profile core 2>&1 | grep -q "Prerequisites"; then
        record_test "Prerequisites check runs" "pass"
    else
        record_test "Prerequisites check runs" "fail"
    fi

    # Dry-run should be lenient
    if bash scripts/setup-wizard.sh --dry-run --profile core 2>&1 | grep -q "continuing in dry-run mode\|All prerequisites satisfied"; then
        record_test "Dry-run is lenient with prerequisites" "pass"
    else
        record_test "Dry-run is lenient with prerequisites" "fail"
    fi
}

# Main test execution
main() {
    log_step "TEAM7 Resume Analysis Platform"
    log_step "Setup Wizard Automated Test Suite"

    echo ""
    log_info "This test suite validates wizard functionality without requiring Docker."
    log_info "For full end-to-end tests, see scripts/SETUP_WIZARD_TESTING.md"
    echo ""

    # Setup
    setup_test_environment

    # Run all tests
    test_help_command
    test_dry_run_mode
    test_profile_validation
    test_env_creation
    test_required_variables
    test_invalid_config
    test_database_url_validation
    test_health_check_integration
    test_command_flags
    test_error_handling
    test_profile_configs
    test_prerequisites

    # Display summary
    log_step "Test Summary"
    echo ""
    echo -e "${CYAN}Total Tests:${NC} $((TESTS_PASSED + TESTS_FAILED))"
    echo -e "${GREEN}Passed:${NC}      $TESTS_PASSED"
    echo -e "${RED}Failed:${NC}      $TESTS_FAILED"
    echo ""

    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Failed tests:"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $test"
        done
        echo ""
        log_info "Review test output above for details"
        exit 1
    else
        log_success "All automated tests passed!"
        echo ""
        log_step "Next Steps"
        echo ""
        echo -e "${YELLOW}Manual Testing Required:${NC}"
        echo ""
        echo "The following tests require Docker to be running:"
        echo ""
        echo "1. Full deployment test:"
        echo "   bash scripts/setup-wizard.sh --non-interactive --profile core"
        echo ""
        echo "2. Service health validation:"
        echo "   bash scripts/health-check.sh"
        echo ""
        echo "3. Interactive mode testing:"
        echo "   bash scripts/setup-wizard.sh"
        echo ""
        echo "See scripts/SETUP_WIZARD_TESTING.md for complete test procedures"
        echo ""
        exit 0
    fi
}

# Run main function
main "$@"
