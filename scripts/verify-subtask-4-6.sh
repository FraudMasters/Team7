#!/bin/bash

###############################################################################
# Verification Script for Subtask 4-6: Logout Flow and Token Cleanup
#
# This script performs automated checks to verify that the logout flow
# and token cleanup functionality has been properly implemented and tested.
#
# Usage: ./scripts/verify-subtask-4-6.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:5173}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Test counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_section() {
    echo -e "\n${YELLOW}>>> $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_file_exists() {
    local file="$1"
    local description="$2"

    if [ -f "$file" ]; then
        print_success "$description exists: $file"
        return 0
    else
        print_failure "$description missing: $file"
        return 1
    fi
}

check_service_health() {
    local url="$1"
    local service_name="$2"

    if curl -s -f "$url" > /dev/null 2>&1; then
        print_success "$service_name is healthy"
        return 0
    else
        print_failure "$service_name is not healthy"
        return 1
    fi
}

###############################################################################
# Verification Checks
###############################################################################

print_header "VERIFICATION: Subtask 4-6 - Logout Flow and Token Cleanup"

###############################################################################
# 1. File Structure Verification
###############################################################################

print_section "1. File Structure Verification"

# Check E2E test file
check_file_exists \
    "$PROJECT_ROOT/frontend/e2e/logout-flow.spec.ts" \
    "E2E test file for logout flow"

# Check testing guide
check_file_exists \
    "$PROJECT_ROOT/.auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-6-testing-guide.md" \
    "Testing guide for logout flow"

# Check verification script itself
check_file_exists \
    "$PROJECT_ROOT/scripts/verify-subtask-4-6.sh" \
    "Verification script"

###############################################################################
# 2. Service Health Checks
###############################################################################

print_section "2. Service Health Checks"

# Check frontend
if check_service_health "$BASE_URL" "Frontend"; then
    FRONTEND_RUNNING=true
else
    FRONTEND_RUNNING=false
    print_info "Frontend is not running. Start with: cd frontend && npm run dev"
fi

# Check backend
if check_service_health "$BACKEND_URL/docs" "Backend"; then
    BACKEND_RUNNING=true
else
    BACKEND_RUNNING=false
    print_info "Backend is not running. Start with: cd backend && uvicorn main:app --reload"
fi

# Check Keycloak
if check_service_health "$KEYCLOAK_URL/health/ready" "Keycloak"; then
    KEYCLOAK_RUNNING=true
else
    KEYCLOAK_RUNNING=false
    print_info "Keycloak is not running. Start with: docker-compose up -d keycloak"
fi

###############################################################################
# 3. AuthContext Implementation Verification
###############################################################################

print_section "3. AuthContext Implementation Verification"

# Check if AuthContext has logout function
if grep -q "logout.*signoutRedirect" "$PROJECT_ROOT/frontend/src/contexts/AuthContext.tsx" 2>/dev/null; then
    print_success "AuthContext has logout function calling signoutRedirect"
else
    print_failure "AuthContext missing logout function or signoutRedirect call"
fi

# Check if post_logout_redirect_uri is configured
if grep -q "post_logout_redirect_uri" "$PROJECT_ROOT/frontend/src/contexts/AuthContext.tsx" 2>/dev/null; then
    print_success "AuthContext has post_logout_redirect_uri configured"
else
    print_failure "AuthContext missing post_logout_redirect_uri configuration"
fi

# Check if oidcConfig is exported
if grep -q "export.*oidcConfig" "$PROJECT_ROOT/frontend/src/contexts/AuthContext.tsx" 2>/dev/null; then
    print_success "AuthContext exports oidcConfig for external configuration"
else
    print_failure "AuthContext does not export oidcConfig"
fi

# Check useAuthContext hook
if grep -q "export.*useAuthContext" "$PROJECT_ROOT/frontend/src/contexts/AuthContext.tsx" 2>/dev/null; then
    print_success "AuthContext exports useAuthContext hook"
else
    print_failure "AuthContext missing useAuthContext export"
fi

###############################################################################
# 4. Backend Logout Endpoint Verification
###############################################################################

print_section "4. Backend Logout Endpoint Verification"

# Check if backend has logout endpoint
if [ -f "$PROJECT_ROOT/backend/api/auth.py" ]; then
    if grep -q "def logout" "$PROJECT_ROOT/backend/api/auth.py" 2>/dev/null; then
        print_success "Backend has logout endpoint"
    else
        print_failure "Backend missing logout endpoint"
    fi

    # Check if logout endpoint is properly registered in router
    if grep -q '"/logout"' "$PROJECT_ROOT/backend/api/auth.py" 2>/dev/null; then
        print_success "Backend logout endpoint is registered"
    else
        print_failure "Backend logout endpoint not registered in router"
    fi
else
    print_failure "Backend auth.py file not found"
fi

# Check if main.py includes auth router
if [ -f "$PROJECT_ROOT/backend/main.py" ]; then
    if grep -q "auth.*router" "$PROJECT_ROOT/backend/main.py" 2>/dev/null; then
        print_success "Backend main.py includes auth router"
    else
        print_failure "Backend main.py missing auth router"
    fi
fi

###############################################################################
# 5. ProtectedRoute Implementation Verification
###############################################################################

print_section "5. ProtectedRoute Implementation Verification"

# Check if ProtectedRoute component exists
if [ -f "$PROJECT_ROOT/frontend/src/auth/ProtectedRoute.tsx" ]; then
    print_success "ProtectedRoute component exists"

    # Check if ProtectedRoute checks authentication
    if grep -q "isAuthenticated" "$PROJECT_ROOT/frontend/src/auth/ProtectedRoute.tsx" 2>/dev/null; then
        print_success "ProtectedRoute checks authentication state"
    else
        print_failure "ProtectedRoute missing authentication check"
    fi

    # Check if ProtectedRoute redirects to login
    if grep -q "/login" "$PROJECT_ROOT/frontend/src/auth/ProtectedRoute.tsx" 2>/dev/null; then
        print_success "ProtectedRoute redirects to login for unauthenticated users"
    else
        print_failure "ProtectedRoute missing login redirect"
    fi
else
    print_failure "ProtectedRoute component not found"
fi

###############################################################################
# 6. E2E Test Coverage Verification
###############################################################################

print_section "6. E2E Test Coverage Verification"

# Check if E2E test file exists and has test suites
if [ -f "$PROJECT_ROOT/frontend/e2e/logout-flow.spec.ts" ]; then
    print_success "E2E test file exists"

    # Count test suites
    TEST_SUITES=$(grep -c "test.describe" "$PROJECT_ROOT/frontend/e2e/logout-flow.spec.ts" 2>/dev/null || echo "0")
    print_info "Found $TEST_SUITES test suites in logout-flow.spec.ts"

    if [ "$TEST_SUITES" -ge 10 ]; then
        print_success "E2E test has adequate test suite coverage (>= 10)"
    else
        print_failure "E2E test has insufficient test suite coverage (< 10)"
    fi

    # Check for specific test scenarios
    REQUIRED_TESTS=(
        "Logout Button Accessibility"
        "Complete Logout Flow"
        "Protected Route Access After Logout"
        "API Authorization After Logout"
        "Logout State Persistence"
    )

    for test_name in "${REQUIRED_TESTS[@]}"; do
        if grep -q "$test_name" "$PROJECT_ROOT/frontend/e2e/logout-flow.spec.ts" 2>/dev/null; then
            print_success "E2E test includes: $test_name"
        else
            print_failure "E2E test missing: $test_name"
        fi
    done
else
    print_failure "E2E test file not found"
fi

###############################################################################
# 7. Integration Points Verification
###############################################################################

print_section "7. Integration Points Verification"

# Check if react-oidc-context is installed
if [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
    if grep -q "react-oidc-context" "$PROJECT_ROOT/frontend/package.json" 2>/dev/null; then
        print_success "react-oidc-context is installed"
    else
        print_failure "react-oidc-context not found in package.json"
    fi

    if grep -q "oidc-client-ts" "$PROJECT_ROOT/frontend/package.json" 2>/dev/null; then
        print_success "oidc-client-ts is installed"
    else
        print_failure "oidc-client-ts not found in package.json"
    fi
else
    print_failure "Frontend package.json not found"
fi

# Check if fastapi-keycloak is installed in backend
if [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
    if grep -q "fastapi-keycloak" "$PROJECT_ROOT/backend/requirements.txt" 2>/dev/null; then
        print_success "fastapi-keycloak is installed"
    else
        print_failure "fastapi-keycloak not found in requirements.txt"
    fi
else
    print_failure "Backend requirements.txt not found"
fi

###############################################################################
# 8. Testing Guide Completeness Verification
###############################################################################

print_section "8. Testing Guide Completeness Verification"

TESTING_GUIDE="$PROJECT_ROOT/.auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-6-testing-guide.md"

if [ -f "$TESTING_GUIDE" ]; then
    print_success "Testing guide exists"

    # Check for required sections
    REQUIRED_SECTIONS=(
        "Overview"
        "Prerequisites"
        "Test Scenarios"
        "Troubleshooting"
        "Success Criteria"
    )

    for section in "${REQUIRED_SECTIONS[@]}"; do
        if grep -q "$section" "$TESTING_GUIDE" 2>/dev/null; then
            print_success "Testing guide includes section: $section"
        else
            print_failure "Testing guide missing section: $section"
        fi
    done

    # Count test scenarios
    SCENARIOS=$(grep -c "### Scenario" "$TESTING_GUIDE" 2>/dev/null || echo "0")
    print_info "Found $SCENARIOS test scenarios in testing guide"

    if [ "$SCENARIOS" -ge 10 ]; then
        print_success "Testing guide has adequate test scenarios (>= 10)"
    else
        print_failure "Testing guide has insufficient test scenarios (< 10)"
    fi
else
    print_failure "Testing guide not found"
fi

###############################################################################
# 9. Security Best Practices Verification
###############################################################################

print_section "9. Security Best Practices Verification"

# Check if tokens are cleared from localStorage on logout
if grep -q "removeItem\|clear" "$PROJECT_ROOT/frontend/src/contexts/AuthContext.tsx" 2>/dev/null; then
    print_success "AuthContext includes token cleanup logic"
else
    print_failure "AuthContext missing token cleanup logic"
fi

# Check if backend validates tokens
if [ -f "$PROJECT_ROOT/backend/middleware/auth.py" ]; then
    if grep -q "decode\|validate" "$PROJECT_ROOT/backend/middleware/auth.py" 2>/dev/null; then
        print_success "Backend has token validation logic"
    else
        print_failure "Backend missing token validation logic"
    fi
else
    print_failure "Backend auth middleware not found"
fi

# Check for no console.log with token data
if grep -r "console.log.*token" "$PROJECT_ROOT/frontend/src/" 2>/dev/null | grep -v "node_modules" | grep -v ".spec.ts" > /dev/null; then
    print_failure "Found console.log statements with token data (security risk)"
else
    print_success "No console.log statements exposing tokens"
fi

###############################################################################
# 10. Documentation and Prerequisites Verification
###############################################################################

print_section "10. Documentation and Prerequisites Verification"

# Check if README mentions logout
if [ -f "$PROJECT_ROOT/README.md" ]; then
    if grep -qi "logout\|sign out" "$PROJECT_ROOT/README.md" 2>/dev/null; then
        print_success "README mentions logout functionality"
    else
        print_info "README does not mention logout (optional)"
    fi
fi

# Check if .env.example has Keycloak variables
if [ -f "$PROJECT_ROOT/.env.example" ]; then
    KEYCLOAK_VARS=$(grep -c "KEYCLOAK\|VITE_KEYCLOAK" "$PROJECT_ROOT/.env.example" 2>/dev/null || echo "0")
    print_info "Found $KEYCLOAK_VARS Keycloak-related variables in .env.example"

    if [ "$KEYCLOAK_VARS" -ge 5 ]; then
        print_success ".env.example has adequate Keycloak configuration"
    else
        print_failure ".env.example missing Keycloak configuration"
    fi
fi

###############################################################################
# Final Summary
###############################################################################

print_header "VERIFICATION SUMMARY"

echo -e "Total Checks:  $TOTAL_CHECKS"
echo -e "${GREEN}Passed:       $PASSED_CHECKS${NC}"
echo -e "${RED}Failed:       $FAILED_CHECKS${NC}"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "\n${GREEN}✓ All verification checks passed!${NC}\n"
    echo -e "Next Steps:"
    echo -e "1. Start all services: docker-compose up -d"
    echo -e "2. Run E2E tests: cd frontend && npm run test:e2e -- logout-flow.spec.ts"
    echo -e "3. Follow manual testing guide: .auto-claude/specs/.../subtask-4-6-testing-guide.md"
    echo -e "4. Update implementation plan to mark subtask-4-6 as completed"
    exit 0
else
    echo -e "\n${RED}✗ Some verification checks failed${NC}\n"
    echo -e "Actions Required:"
    echo -e "1. Review failed checks above"
    echo -e "2. Implement missing functionality"
    echo -e "3. Re-run this verification script"
    exit 1
fi
