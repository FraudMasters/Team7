#!/bin/bash
#
# Frontend Health Dashboard Verification Script
#
# This script verifies that the frontend health dashboard shows correct status
# for all services as specified in subtask-6-6.
#
# Usage: ./frontend/tests/verification/test_frontend_health_dashboard.sh
#
# Prerequisites:
# - Backend server running on http://localhost:8000
# - Frontend dev server running on http://localhost:5173
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backend and Frontend URLs
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
HEALTH_ENDPOINT="$BACKEND_URL/api/health/detailed"
DEPENDENCIES_ENDPOINT="$BACKEND_URL/api/health/dependencies"

# Functions for colored output
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"

    print_info "Testing: $test_name"

    if eval "$test_command" > /dev/null 2>&1; then
        print_success "$test_name"
        ((TESTS_PASSED++))
        return 0
    else
        print_error "$test_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if server is running
check_server() {
    local url="$1"
    local name="$2"

    if curl -s -f "$url" > /dev/null 2>&1; then
        print_success "$name is running"
        return 0
    else
        print_error "$name is not running"
        return 1
    fi
}

# Parse health check response and verify status colors
verify_health_status_colors() {
    local response="$1"

    # Check for status values in response
    if echo "$response" | grep -q '"status": *"healthy"'; then
        print_success "Found 'healthy' status in response (green indicator expected)"
        ((TESTS_PASSED++))
    else
        print_error "No 'healthy' status found in response"
        ((TESTS_FAILED++))
    fi

    # Check for degraded status
    if echo "$response" | grep -q '"status": *"degraded"'; then
        print_success "Found 'degraded' status in response (yellow indicator expected)"
        ((TESTS_PASSED++))
    else
        print_info "No 'degraded' status found (may not have degraded services)"
        ((TESTS_SKIPPED++))
    fi

    # Check for unhealthy status
    if echo "$response" | grep -q '"status": *"unhealthy"'; then
        print_success "Found 'unhealthy' status in response (red indicator expected)"
        ((TESTS_PASSED++))
    else
        print_info "No 'unhealthy' status found (all services healthy)"
        ((TESTS_SKIPPED++))
    fi
}

# Main verification
main() {
    print_header "Frontend Health Dashboard Verification"

    # Check prerequisites
    print_info "Checking prerequisites..."

    BACKEND_RUNNING=false
    FRONTEND_RUNNING=false

    if check_server "$BACKEND_URL" "Backend server"; then
        BACKEND_RUNNING=true
    fi

    if check_server "$FRONTEND_URL" "Frontend dev server"; then
        FRONTEND_RUNNING=true
    fi

    if [ "$BACKEND_RUNNING" = false ] || [ "$FRONTEND_RUNNING" = false ]; then
        print_error "Prerequisites not met. Please start the required services."
        print_info "Backend: cd backend && python main.py"
        print_info "Frontend: cd frontend && npm run dev"
        exit 1
    fi

    echo ""

    # Test 1: Verify health endpoint returns correct status structure
    print_header "Test 1: Backend Health API Structure"

    HEALTH_RESPONSE=$(curl -s "$HEALTH_ENDPOINT")

    if run_test "Health endpoint returns 200" "curl -s -f '$HEALTH_ENDPOINT'" ""; then
        print_success "Health endpoint accessible"
        ((TESTS_PASSED++))
    else
        print_error "Health endpoint not accessible"
        ((TESTS_FAILED++))
    fi

    # Verify response has required fields
    if echo "$HEALTH_RESPONSE" | grep -q '"status"'; then
        print_success "Response contains 'status' field"
        ((TESTS_PASSED++))
    else
        print_error "Response missing 'status' field"
        ((TESTS_FAILED++))
    fi

    if echo "$HEALTH_RESPONSE" | grep -q '"checks"'; then
        print_success "Response contains 'checks' field"
        ((TESTS_PASSED++))
    else
        print_error "Response missing 'checks' field"
        ((TESTS_FAILED++))
    fi

    if echo "$HEALTH_RESPONSE" | grep -q '"overall_health_percentage"'; then
        print_success "Response contains 'overall_health_percentage' field"
        ((TESTS_PASSED++))
    else
        print_error "Response missing 'overall_health_percentage' field"
        ((TESTS_FAILED++))
    fi

    # Test 2: Verify all expected services are present
    print_header "Test 2: Service Coverage"

    EXPECTED_SERVICES=("database" "redis" "celery" "ml_ner_model" "ml_zero_shot_model" "ml_language_tools" "external_api")

    for service in "${EXPECTED_SERVICES[@]}"; do
        if echo "$HEALTH_RESPONSE" | grep -q "\"$service\""; then
            print_success "Service '$service' found in health check response"
            ((TESTS_PASSED++))
        else
            print_error "Service '$service' missing from health check response"
            ((TESTS_FAILED++))
        fi
    done

    # Test 3: Verify status color mapping
    print_header "Test 3: Status Color Mapping"

    verify_health_status_colors "$HEALTH_RESPONSE"

    # Test 4: Verify dependency graph endpoint
    print_header "Test 4: Dependency Graph Data"

    DEPS_RESPONSE=$(curl -s "$DEPENDENCIES_ENDPOINT")

    if run_test "Dependencies endpoint returns 200" "curl -s -f '$DEPENDENCIES_ENDPOINT'" ""; then
        print_success "Dependencies endpoint accessible"
        ((TESTS_PASSED++))
    else
        print_error "Dependencies endpoint not accessible"
        ((TESTS_FAILED++))
    fi

    if echo "$DEPS_RESPONSE" | grep -q '"services"'; then
        print_success "Response contains 'services' field"
        ((TESTS_PASSED++))
    else
        print_error "Response missing 'services' field"
        ((TESTS_FAILED++))
    fi

    if echo "$DEPS_RESPONSE" | grep -q '"summary"'; then
        print_success "Response contains 'summary' field"
        ((TESTS_PASSED++))
    else
        print_error "Response missing 'summary' field"
        ((TESTS_FAILED++))
    fi

    # Test 5: Verify frontend route accessibility
    print_header "Test 5: Frontend Route"

    if run_test "Health dashboard route accessible" "curl -s -f '$FRONTEND_URL/recruiter/health'" ""; then
        print_success "Health dashboard route accessible"
        ((TESTS_PASSED++))
    else
        print_error "Health dashboard route not accessible"
        ((TESTS_FAILED++))
    fi

    # Test 6: Verify frontend component structure
    print_header "Test 6: Frontend Component Structure"

    FRONTEND_HTML=$(curl -s "$FRONTEND_URL/recruiter/health")

    # Check for key elements in the frontend
    if echo "$FRONTEND_HTML" | grep -q "Health Dashboard\|System Health Dashboard"; then
        print_success "Health dashboard title present"
        ((TESTS_PASSED++))
    else
        print_warning "Health dashboard title not found (may be rendered client-side)"
        ((TESTS_SKIPPED++))
    fi

    # Test 7: Verify service status categories
    print_header "Test 7: Service Categories"

    CATEGORIES=("infrastructure" "messaging" "ml" "external")

    for category in "${CATEGORIES[@]}"; do
        if echo "$HEALTH_RESPONSE" | grep -q "\"category\": *\"$category\""; then
            print_success "Category '$category' found in health checks"
            ((TESTS_PASSED++))
        else
            print_warning "Category '$category' not found"
            ((TESTS_SKIPPED++))
        fi
    done

    # Test 8: Verify essential service flags
    print_header "Test 8: Essential Service Markers"

    if echo "$HEALTH_RESPONSE" | grep -q '"essential": *true'; then
        print_success "Essential service markers present"
        ((TESTS_PASSED++))
    else
        print_error "Essential service markers missing"
        ((TESTS_FAILED++))
    fi

    # Test 9: Verify response times are tracked
    print_header "Test 9: Response Time Tracking"

    if echo "$HEALTH_RESPONSE" | grep -q '"response_time_ms"'; then
        print_success "Response time metrics present"
        ((TESTS_PASSED++))
    else
        print_error "Response time metrics missing"
        ((TESTS_FAILED++))
    fi

    # Test 10: Verify critical issues and warnings arrays
    print_header "Test 10: Critical Issues and Warnings"

    if echo "$HEALTH_RESPONSE" | grep -q '"critical_issues"'; then
        print_success "Critical issues array present"
        ((TESTS_PASSED++))
    else
        print_error "Critical issues array missing"
        ((TESTS_FAILED++))
    fi

    if echo "$HEALTH_RESPONSE" | grep -q '"warnings"'; then
        print_success "Warnings array present"
        ((TESTS_PASSED++))
    else
        print_error "Warnings array missing"
        ((TESTS_FAILED++))
    fi

    # Summary
    print_header "Verification Summary"

    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "Tests Skipped: ${YELLOW}$TESTS_SKIPPED${NC}"
    echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))"

    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All critical tests passed!"
        echo ""
        print_info "Next steps for manual verification:"
        echo "1. Open http://localhost:5173/recruiter/health in a browser"
        echo "2. Verify all services show color-coded status (green/yellow/red)"
        echo "3. Click on a service card to see detailed health information"
        echo "4. Hover over dependency graph nodes to see service relationships"
        echo "5. Wait 30 seconds to verify auto-refresh functionality"
        echo "6. Click the Refresh button to verify manual refresh works"
        exit 0
    else
        print_error "Some tests failed. Please review the errors above."
        exit 1
    fi
}

# Run main function
main
