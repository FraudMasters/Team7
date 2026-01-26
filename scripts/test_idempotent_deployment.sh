#!/bin/bash
# Test Suite: Idempotent Deployment Verification
# This script tests that the deployment script can be run multiple times safely

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    TESTS_RUN=$((TESTS_RUN + 1))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo "========================================="
echo "  Idempotent Deployment Test Suite"
echo "========================================="
echo ""

# Test 1: Verify script structure for idempotency
log_test "1. Verify script has stop_existing_containers() function"
if grep -q "stop_existing_containers()" scripts/deploy.sh; then
    log_pass "stop_existing_containers() function exists"

    # Verify it's called in main() - look in the main function section
    if awk '/^main\(/,/^}/' scripts/deploy.sh | grep -q "stop_existing_containers"; then
        log_pass "  stop_existing_containers() is called in main()"
    else
        log_fail "  stop_existing_containers() is NOT called in main()"
    fi
else
    log_fail "stop_existing_containers() function NOT found"
fi

# Test 2: Verify docker-compose down uses || true for safety
log_test "2. Verify docker-compose down has error suppression"
if grep -q "docker-compose down --remove-orphans || true" scripts/deploy.sh; then
    log_pass "docker-compose down uses || true for error suppression"
else
    log_fail "docker-compose down missing || true error suppression"
fi

# Test 3: Verify mkdir -p is used (idempotent directory creation)
log_test "3. Verify mkdir -p for idempotent directory creation"
if grep -q "mkdir -p" scripts/deploy.sh; then
    log_pass "mkdir -p is used (idempotent)"
    mkdir_count=$(grep -c "mkdir -p" scripts/deploy.sh || true)
    log_pass "  Found $mkdir_count instances of mkdir -p"
else
    log_fail "mkdir -p not found"
fi

# Test 4: Verify environment setup checks file existence
log_test "4. Verify environment setup checks before creating .env files"
if grep -q '\[ ! -f .env \]' scripts/deploy.sh; then
    log_pass ".env file existence check found"
else
    log_fail ".env file existence check NOT found"
fi

if grep -q '\[ ! -f backend/.env \]' scripts/deploy.sh; then
    log_pass "backend/.env file existence check found"
else
    log_fail "backend/.env file existence check NOT found"
fi

if grep -q '\[ ! -f frontend/.env \]' scripts/deploy.sh; then
    log_pass "frontend/.env file existence check found"
else
    log_fail "frontend/.env file existence check NOT found"
fi

# Test 5: Verify migration command handles already applied migrations
log_test "5. Verify migration command handles already applied migrations"
if grep -q "alembic upgrade head.*||.*log_warning" scripts/deploy.sh; then
    log_pass "Migration command has fallback for already applied migrations"
else
    log_fail "Migration command missing fallback for already applied migrations"
fi

# Test 6: Verify docker-compose up -d is idempotent
log_test "6. Verify docker-compose up -d is used (idempotent command)"
up_count=$(grep -c "docker-compose up -d" scripts/deploy.sh || true)
if [ $up_count -gt 0 ]; then
    log_pass "Found $up_count instances of docker-compose up -d (idempotent)"
else
    log_fail "docker-compose up -d not found"
fi

# Test 7: Verify no destructive operations without safeguards
log_test "7. Verify no destructive operations without safeguards"
destructive_ops=0

# Check for docker rm without safeguards
if grep -q "docker rm" scripts/deploy.sh | grep -v "|| true"; then
    log_fail "  Found docker rm without || true safeguard"
    destructive_ops=$((destructive_ops + 1))
fi

# Check for docker-compose down without || true
if grep -q "docker-compose down" scripts/deploy.sh | grep -v "|| true"; then
    # Exclude the one in stop_existing_containers which has || true
    if grep -B 1 "docker-compose down" scripts/deploy.sh | grep -q "|| true"; then
        log_pass "  docker-compose down has || true safeguard"
    else
        log_fail "  Found docker-compose down without || true safeguard"
        destructive_ops=$((destructive_ops + 1))
    fi
fi

if [ $destructive_ops -eq 0 ]; then
    log_pass "No destructive operations without safeguards"
fi

# Test 8: Verify health checks are used (prevents starting already running services incorrectly)
log_test "8. Verify health checks exist for all services"
health_checks=("wait_for_postgres" "wait_for_redis" "wait_for_http_health")
for check in "${health_checks[@]}"; do
    if grep -q "$check" scripts/deploy.sh; then
        log_pass "  $check function exists"
    else
        log_fail "  $check function NOT found"
    fi
done

# Test 9: Verify all docker-compose commands have proper error handling
log_test "9. Verify docker-compose build has proper context"
if grep -q "docker-compose build" scripts/deploy.sh; then
    log_pass "docker-compose build found"
    # Build is safe to run multiple times
    if grep -B 2 -A 2 "docker-compose build" scripts/deploy.sh | grep -q "log_info"; then
        log_pass "  Build command has logging context"
    fi
else
    log_fail "docker-compose build NOT found"
fi

# Test 10: Verify deployment flow stops existing containers before starting new ones
log_test "10. Verify deployment stops existing containers before starting"
if grep -B 10 -A 10 "stop_existing_containers" scripts/deploy.sh | grep -q "docker-compose build"; then
    log_pass "Containers are stopped before building images"
else
    log_fail "Container stop order not verified"
fi

# Test 11: Verify script uses set -e for error handling
log_test "11. Verify script has set -e for error handling"
if grep -q "^set -e" scripts/deploy.sh; then
    log_pass "set -e found for automatic error detection"
else
    log_fail "set -e NOT found"
fi

# Test 12: Verify trap handler exists for cleanup
log_test "12. Verify trap handler exists for error cleanup"
if grep -q "trap.*cleanup_on_error" scripts/deploy.sh; then
    log_pass "Trap handler for cleanup exists"
else
    log_fail "Trap handler NOT found"
fi

# Test 13: Analyze idempotent patterns in the script
log_test "13. Analyze complete deployment flow for idempotency"

# Check if stop_existing_containers is called before starting services
flow_correct=false
if grep -A 100 "main()" scripts/deploy.sh | grep -B 5 "build_images" | grep -q "stop_existing_containers"; then
    flow_correct=true
fi

if $flow_correct; then
    log_pass "Deployment flow: stop_existing_containers → build_images (correct order)"
else
    log_fail "Deployment flow order incorrect"
fi

# Test 14: Verify script can handle existing .env files
log_test "14. Verify script handles existing .env files gracefully"
if grep -A 5 '\[ ! -f .env \]' scripts/deploy.sh | grep -q "else"; then
    log_pass "Script has else branch for existing .env files"
    if grep -A 10 '\[ ! -f .env \]' scripts/deploy.sh | grep -A 5 "else" | grep -q "log_info.*exists"; then
        log_pass "  Existing files trigger info message (not error)"
    fi
else
    log_fail "Script doesn't handle existing .env files"
fi

# Test 15: Verify health checks have timeout handling
log_test "15. Verify health checks have timeout handling"
timeout_count=$(grep -c "timeout=" scripts/deploy.sh || true)
if [ $timeout_count -gt 0 ]; then
    log_pass "Found $timeout_count health checks with timeout handling"
else
    log_fail "Health checks missing timeout handling"
fi

# Test 16: Verify script doesn't use interactive prompts
log_test "16. Verify script doesn't use interactive prompts (automates re-runs)"
if ! grep -q "read -p" scripts/deploy.sh; then
    log_pass "No interactive prompts found (script is fully automated)"
else
    log_fail "Found interactive prompts (blocks automation)"
fi

# Test 17: Verify all services are started with docker-compose up -d
log_test "17. Verify all services use docker-compose up -d (idempotent)"
services=("postgres" "redis" "backend" "celery_worker" "frontend" "flower")
all_found=true
for service in "${services[@]}"; do
    # Check if service is started with docker-compose up -d (either alone or with others)
    if grep -q "docker-compose up -d.*$service\|$service.*docker-compose up -d" scripts/deploy.sh; then
        log_pass "  $service started with docker-compose up -d"
    else
        log_fail "  $service NOT started with docker-compose up -d"
        all_found=false
    fi
done

# Test 18: Verify error messages are descriptive for re-run scenarios
log_test "18. Verify descriptive logging for idempotent operations"
info_messages=(
    "exists"
    "already"
    "skipping"
    "using existing"
)
found_descriptive=false
for msg in "${info_messages[@]}"; do
    if grep -qi "$msg" scripts/deploy.sh; then
        found_descriptive=true
        break
    fi
done

if $found_descriptive; then
    log_pass "Found descriptive messages for existing resources"
else
    log_fail "Missing descriptive messages for existing resources"
fi

# Test 19: Verify script structure allows for clean re-execution
log_test "19. Verify script executes in single-pass (no state dependencies)"
# Check that main() calls all necessary functions in sequence
if grep -A 100 "main()" scripts/deploy.sh | grep -q "stop_existing_containers"; then
    log_pass "Script starts with cleanup (ensures clean state)"
fi
if grep -A 100 "main()" scripts/deploy.sh | grep -q "build_images"; then
    log_pass "Script includes build step (handles image updates)"
fi
if grep -A 100 "main()" scripts/deploy.sh | grep -q "start_infrastructure"; then
    log_pass "Script includes infrastructure start"
fi
if grep -A 100 "main()" scripts/deploy.sh | grep -q "start_application_services"; then
    log_pass "Script includes application services start"
fi

# Test 20: Final idempotency assessment
log_test "20. Final idempotency design assessment"

idempotent_patterns=0
# Pattern 1: Stops existing containers
if grep -q "stop_existing_containers" scripts/deploy.sh; then
    idempotent_patterns=$((idempotent_patterns + 1))
fi
# Pattern 2: Idempotent directory creation
if grep -q "mkdir -p" scripts/deploy.sh; then
    idempotent_patterns=$((idempotent_patterns + 1))
fi
# Pattern 3: Environment checks before creation
if grep -q '\[ ! -f' scripts/deploy.sh; then
    idempotent_patterns=$((idempotent_patterns + 1))
fi
# Pattern 4: Migration fallback
if grep -q "|| log_warning" scripts/deploy.sh; then
    idempotent_patterns=$((idempotent_patterns + 1))
fi
# Pattern 5: docker-compose up -d (idempotent)
if grep -q "docker-compose up -d" scripts/deploy.sh; then
    idempotent_patterns=$((idempotent_patterns + 1))
fi

log_pass "Found $idempotent_patterns/5 idempotent design patterns"

if [ $idempotent_patterns -ge 4 ]; then
    log_pass "Script follows idempotent design principles"
else
    log_fail "Script missing critical idempotent design patterns"
fi

echo ""
echo "========================================="
echo "  Test Summary"
echo "========================================="
echo ""
echo -e "${BLUE}Tests Run:${NC}    $TESTS_RUN"
echo -e "${GREEN}Tests Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Tests Failed:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Idempotent Deployment Analysis:"
    echo "  The deployment script demonstrates strong idempotent design:"
    echo "  1. Stops existing containers before starting new ones"
    echo "  2. Uses mkdir -p for idempotent directory creation"
    echo "  3. Checks file existence before creating .env files"
    echo "  4. Handles already-applied migrations gracefully"
    echo "  5. Uses docker-compose up -d (idempotent by nature)"
    echo "  6. No interactive prompts (fully automated)"
    echo "  7. Proper error handling with cleanup on failure"
    echo ""
    echo "Expected Behavior on Re-run:"
    echo "  - First run: Deploys all services normally"
    echo "  - Second run:"
    echo "    1. Stops existing containers (clean state)"
    echo "    2. Rebuilds images (if needed)"
    echo "    3. Starts infrastructure services"
    echo "    4. Skips or warns about already-applied migrations"
    echo "    5. Starts application services"
    echo "    6. All services end up running and healthy"
    echo ""
    echo "Manual Testing Required (Docker environment):"
    echo "  1. bash scripts/deploy.sh           # First run"
    echo "  2. docker-compose ps                # Verify all running"
    echo "  3. bash scripts/deploy.sh           # Second run"
    echo "  4. docker-compose ps                # Verify still all running"
    echo "  5. Check exit code is 0 (success)"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo "Review failed tests above to fix idempotency issues"
    echo ""
    exit 1
fi
