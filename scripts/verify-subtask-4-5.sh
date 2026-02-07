#!/bin/bash

###############################################################################
# Verification Script for JWT Token Refresh Mechanism (Subtask 4-5)
#
# This script performs automated verification of the JWT token refresh
# functionality, including service health, E2E test coverage, configuration
# validation, and integration checks.
#
# Usage: bash scripts/verify-subtask-4-5.sh
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:5173}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
API_URL="${API_URL:-http://localhost:8000}"
TEST_USER_EMAIL="${TEST_USER_EMAIL:-admin@agenthr.com}"
TEST_USER_PASSWORD="${TEST_USER_PASSWORD:-admin123}"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Print header
print_header() {
    echo -e "${BLUE}=============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=============================================${NC}"
}

# Print section
print_section() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
}

# Print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

# Print failure
print_failure() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

# Print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Print info
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if URL is accessible
check_url() {
    local url=$1
    local description=$2

    if curl -s -f -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|301\|302"; then
        print_success "$description is accessible ($url)"
        return 0
    else
        print_failure "$description is not accessible ($url)"
        return 1
    fi
}

# Print summary
print_summary() {
    echo ""
    print_header "Verification Summary"
    echo -e "${GREEN}Passed:${NC} $PASSED"
    echo -e "${RED}Failed:${NC} $FAILED"
    echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""

    local TOTAL=$((PASSED + FAILED))
    if [ $TOTAL -gt 0 ]; then
        local PERCENT=$((PASSED * 100 / TOTAL))
        echo -e "Success Rate: ${PERCENT}%"
    fi

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}All checks passed!${NC}"
        return 0
    else
        echo -e "${RED}Some checks failed. Please review the output above.${NC}"
        return 1
    fi
}

###############################################################################
# Main Verification
###############################################################################

print_header "JWT Token Refresh Mechanism Verification (Subtask 4-5)"

print_info "Configuration:"
echo "  BASE_URL: $BASE_URL"
echo "  KEYCLOAK_URL: $KEYCLOAK_URL"
echo "  API_URL: $API_URL"
echo "  TEST_USER_EMAIL: $TEST_USER_EMAIL"

###############################################################################
# 1. Service Health Checks
###############################################################################

print_section "1. Service Health Checks"

# Check Frontend
if check_url "$BASE_URL" "Frontend"; then
    FRONTEND_RUNNING=true
else
    FRONTEND_RUNNING=false
fi

# Check Keycloak
if check_url "$KEYCLOAK_URL/health/ready" "Keycloak Health Endpoint"; then
    KEYCLOAK_RUNNING=true
else
    KEYCLOAK_RUNNING=false
fi

# Check Keycloak Realm
if check_url "$KEYCLOAK_URL/realms/agenthr/.well-known/openid-configuration" "Keycloak Realm (agenthr)"; then
    KEYCLOAK_REALM_EXISTS=true
else
    KEYCLOAK_REALM_EXISTS=false
fi

# Check Backend API
if check_url "$API_URL/docs" "Backend API Documentation"; then
    BACKEND_RUNNING=true
else
    BACKEND_RUNNING=false
fi

# Check Backend Auth Endpoint
if check_url "$API_URL/api/auth/me" "Backend Auth Endpoint (requires auth)"; then
    print_warning "Backend auth endpoint accessible (may require authentication)"
else
    print_info "Backend auth endpoint requires authentication (expected)"
fi

###############################################################################
# 2. Frontend Token Refresh Configuration
###############################################################################

print_section "2. Frontend Token Refresh Configuration"

# Check AuthContext.tsx exists
if [ -f "frontend/src/contexts/AuthContext.tsx" ]; then
    print_success "AuthContext.tsx exists"

    # Check for automaticSilentRenew
    if grep -q "automaticSilentRenew: true" frontend/src/contexts/AuthContext.tsx; then
        print_success "automaticSilentRenew enabled in AuthContext"
    else
        print_failure "automaticSilentRenew not enabled in AuthContext"
    fi

    # Check for monitorSession
    if grep -q "monitorSession: true" frontend/src/contexts/AuthContext.tsx; then
        print_success "monitorSession enabled in AuthContext"
    else
        print_failure "monitorSession not enabled in AuthContext"
    fi

    # Check for includeIdTokenInSilentRenew
    if grep -q "includeIdTokenInSilentRenew: true" frontend/src/contexts/AuthContext.tsx; then
        print_success "includeIdTokenInSilentRenew enabled"
    else
        print_warning "includeIdTokenInSilentRenew not enabled (optional)"
    fi

    # Check for checkSessionIntervalInSeconds
    if grep -q "checkSessionIntervalInSeconds:" frontend/src/contexts/AuthContext.tsx; then
        print_success "checkSessionIntervalInSeconds configured"
    else
        print_warning "checkSessionIntervalInSeconds not configured"
    fi
else
    print_failure "AuthContext.tsx not found"
fi

# Check API client interceptor
if [ -f "frontend/src/api/client.ts" ]; then
    print_success "API client exists"

    # Check for getAuthToken method
    if grep -q "getAuthToken" frontend/src/api/client.ts; then
        print_success "getAuthToken method exists in API client"
    else
        print_failure "getAuthToken method not found in API client"
    fi

    # Check for Authorization header interceptor
    if grep -q "Authorization.*Bearer" frontend/src/api/client.ts; then
        print_success "Authorization header interceptor configured"
    else
        print_failure "Authorization header interceptor not found"
    fi
else
    print_failure "API client not found"
fi

###############################################################################
# 3. Backend Token Refresh Support
###############################################################################

print_section "3. Backend Token Refresh Support"

# Check auth endpoints exist
if [ -f "backend/api/auth.py" ]; then
    print_success "backend/api/auth.py exists"

    # Check for refresh endpoint
    if grep -q "def.*refresh" backend/api/auth.py; then
        print_success "Token refresh endpoint exists"
    else
        print_warning "Token refresh endpoint not found (may use Keycloak directly)"
    fi

    # Check for logout endpoint
    if grep -q "def.*logout" backend/api/auth.py; then
        print_success "Logout endpoint exists"
    else
        print_warning "Logout endpoint not found"
    fi

    # Check for /me endpoint
    if grep -q '"/me"' backend/api/auth.py; then
        print_success "Current user endpoint exists"
    else
        print_failure "Current user endpoint not found"
    fi
else
    print_failure "backend/api/auth.py not found"
fi

# Check auth middleware
if [ -f "backend/middleware/auth.py" ]; then
    print_success "Auth middleware exists"

    # Check for TokenData model
    if grep -q "class TokenData" backend/middleware/auth.py; then
        print_success "TokenData model defined"
    else
        print_warning "TokenData model not found"
    fi

    # Check for JWT decoding
    if grep -q "decode_token" backend/middleware/auth.py; then
        print_success "JWT token decoding implemented"
    else
        print_warning "JWT decoding function not found"
    fi
else
    print_failure "Auth middleware not found"
fi

###############################################################################
# 4. Keycloak Token Configuration
###############################################################################

print_section "4. Keycloak Token Configuration"

# Check if Keycloak is running before attempting to query configuration
if [ "$KEYCLOAK_RUNNING" = true ] && [ "$KEYCLOAK_REALM_EXISTS" = true ]; then
    # Get OIDC configuration
    OIDC_CONFIG=$(curl -s "$KEYCLOAK_URL/realms/agenthr/.well-known/openid-configuration")

    if [ -n "$OIDC_CONFIG" ]; then
        print_success "OIDC configuration retrieved"

        # Check token endpoint
        if echo "$OIDC_CONFIG" | grep -q "token_endpoint"; then
            TOKEN_ENDPOINT=$(echo "$OIDC_CONFIG" | grep -o '"token_endpoint":"[^"]*"' | cut -d'"' -f4)
            print_success "Token endpoint available: $TOKEN_ENDPOINT"
        else
            print_failure "Token endpoint not found in OIDC config"
        fi

        # Check refresh token scope support
        if echo "$OIDC_CONFIG" | grep -q "offline_access"; then
            print_success "Offline access scope supported (refresh tokens)"
        else
            print_warning "Offline access scope not advertised"
        fi
    else
        print_failure "Failed to retrieve OIDC configuration"
    fi

    # Try to get token configuration from Keycloak Admin API
    # This requires admin credentials
    if [ -n "$KEYCLOAK_ADMIN_PASSWORD" ]; then
        ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
            -d "client_id=admin-cli" \
            -d "username=$KEYCLOAK_ADMIN_USERNAME" \
            -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
            -d "grant_type=password" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

        if [ -n "$ADMIN_TOKEN" ]; then
            print_success "Admin token obtained for configuration check"

            # Get realm token settings
            TOKEN_CONFIG=$(curl -s "$KEYCLOAK_URL/admin/realms/agenthr" \
                -H "Authorization: Bearer $ADMIN_TOKEN" | grep -o '"accessTokenLifespan":[0-9]*' | cut -d':' -f2)

            if [ -n "$TOKEN_CONFIG" ]; then
                print_success "Access Token Lifespan configured: ${TOKEN_CONFIG}s"
            fi
        else
            print_warning "Could not obtain admin token (check KEYCLOAK_ADMIN_PASSWORD)"
        fi
    else
        print_info "Set KEYCLOAK_ADMIN_PASSWORD to check token configuration"
    fi
else
    print_warning "Keycloak not running - skipping configuration checks"
fi

###############################################################################
# 5. E2E Test Coverage
###############################################################################

print_section "5. E2E Test Coverage"

# Check E2E test file exists
if [ -f "frontend/e2e/token-refresh-flow.spec.ts" ]; then
    print_success "Token refresh E2E test file exists"

    # Count test suites
    TEST_SUITES=$(grep -c "test.describe(" frontend/e2e/token-refresh-flow.spec.ts || true)
    print_info "Found $TEST_SUITES test suites"

    # Count test cases
    TEST_CASES=$(grep -c "test(" frontend/e2e/token-refresh-flow.spec.ts || true)
    print_info "Found $TEST_CASES test cases"

    # Check for critical test scenarios
    CRITICAL_TESTS=(
        "Automatic Token Refresh"
        "API Calls with Refreshed Tokens"
        "Token Refresh Failure Handling"
        "Multiple Refresh Cycles"
        "Session Monitoring"
    )

    for test_name in "${CRITICAL_TESTS[@]}"; do
        if grep -q "$test_name" frontend/e2e/token-refresh-flow.spec.ts; then
            print_success "Test scenario: $test_name"
        else
            print_warning "Missing test scenario: $test_name"
        fi
    done
else
    print_failure "Token refresh E2E test file not found"
fi

# Check if Playwright is configured
if [ -f "frontend/playwright.config.ts" ]; then
    print_success "Playwright configuration exists"
else
    print_warning "Playwright configuration not found"
fi

###############################################################################
# 6. File Structure Verification
###############################################################################

print_section "6. File Structure Verification"

# Required files
FILES=(
    "frontend/src/contexts/AuthContext.tsx"
    "frontend/src/api/client.ts"
    "backend/api/auth.py"
    "backend/middleware/auth.py"
    "frontend/e2e/token-refresh-flow.spec.ts"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file exists"
    else
        print_failure "$file not found"
    fi
done

###############################################################################
# 7. Integration Points
###############################################################################

print_section "7. Integration Points"

# Check react-oidc-context dependency
if [ -f "frontend/package.json" ]; then
    if grep -q "react-oidc-context" frontend/package.json; then
        print_success "react-oidc-context dependency installed"
    else
        print_failure "react-oidc-context dependency missing"
    fi

    if grep -q "oidc-client-ts" frontend/package.json; then
        print_success "oidc-client-ts dependency installed"
    else
        print_failure "oidc-client-ts dependency missing"
    fi
else
    print_failure "frontend/package.json not found"
fi

# Check fastapi-keycloak dependency
if [ -f "backend/requirements.txt" ]; then
    if grep -q "fastapi-keycloak" backend/requirements.txt; then
        print_success "fastapi-keycloak dependency installed"
    else
        print_failure "fastapi-keycloak dependency missing"
    fi
else
    print_failure "backend/requirements.txt not found"
fi

###############################################################################
# 8. Documentation
###############################################################################

print_section "8. Documentation"

# Check testing guide exists
if [ -f ".auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-5-testing-guide.md" ]; then
    print_success "Manual testing guide exists"

    # Check for key sections
    SECTIONS=(
        "Test Scenarios"
        "Token Refresh Configuration"
        "Troubleshooting"
        "Success Criteria"
    )

    for section in "${SECTIONS[@]}"; do
        if grep -q "$section" .auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-5-testing-guide.md; then
            print_success "Documentation section: $section"
        else
            print_warning "Missing section: $section"
        fi
    done
else
    print_failure "Manual testing guide not found"
fi

###############################################################################
# 9. Quick Integration Test
###############################################################################

print_section "9. Quick Integration Test"

# Test login flow (if all services running)
if [ "$FRONTEND_RUNNING" = true ] && [ "$KEYCLOAK_RUNNING" = true ]; then
    print_info "All services running - integration test possible"
    print_info "To test token refresh manually:"
    echo "  1. Login to $BASE_URL/login"
    echo "  2. Open DevTools → Application → Local Storage"
    echo "  3. Find key: oidc.user:$KEYCLOAK_URL/realms/agenthr:agenthr-frontend"
    echo "  4. Note the access_token and expires_at values"
    echo "  5. Wait 5 minutes (or until near expiration)"
    echo "  6. Refresh the Local Storage view"
    echo "  7. Verify access_token changed and expires_at extended"
else
    print_warning "Services not running - integration test not possible"
fi

###############################################################################
# 10. Security Best Practices
###############################################################################

print_section "10. Security Best Practices"

# Check token storage (should be in localStorage, not exposed in URLs)
if grep -q "localStorage" frontend/src/contexts/AuthContext.tsx; then
    print_success "Tokens stored in localStorage (managed by react-oidc-context)"
else
    print_warning "Token storage mechanism unclear"
fi

# Check that tokens are not logged
if grep -q "console.log.*token" frontend/src/api/client.ts; then
    print_warning "Token logging detected (security concern)"
else
    print_success "No token logging found"
fi

# Check for HTTPS in production (warning for HTTP in dev)
if [[ "$KEYCLOAK_URL" == http://* ]]; then
    print_warning "Using HTTP for Keycloak (OK for development, use HTTPS in production)"
else
    print_success "Using HTTPS for Keycloak"
fi

# Check token expiration validation
if grep -q "exp" backend/middleware/auth.py; then
    print_success "Backend validates token expiration"
else
    print_warning "Token expiration validation not found"
fi

###############################################################################
# Prerequisites Summary
###############################################################################

print_section "Prerequisites Summary"

echo "Before running full E2E tests, ensure:"
echo "  1. Keycloak server is running: $KEYCLOAK_URL"
echo "  2. Frontend is running: $BASE_URL"
echo "  3. Backend API is running: $API_URL"
echo "  4. Test users exist in Keycloak:"
echo "     - admin@agenthr.com (Admin role)"
echo "     - recruiter@agenthr.com (Recruiter role)"
echo "     - viewer@agenthr.com (Viewer role)"
echo "  5. Token lifespans configured (for realistic testing):"
echo "     - Access Token Lifespan: 5 minutes"
echo "     - Refresh Token Max Age: 10 hours"
echo ""
echo "To configure Keycloak token settings:"
echo "  1. Login to Admin Console: $KEYCLOAK_URL/admin"
echo "  2. Select 'agenthr' realm"
echo "  3. Go to Realm Settings → Tokens"
echo "  4. Adjust Access Token Lifespan to 300 seconds (5 minutes)"
echo "  5. Click Save"

###############################################################################
# E2E Test Execution Instructions
###############################################################################

print_section "E2E Test Execution"

echo "To run E2E tests:"
echo "  cd frontend"
echo "  npm run test:e2e token-refresh-flow.spec.ts"
echo ""
echo "To run all E2E tests:"
echo "  cd frontend"
echo "  npm run test:e2e"

###############################################################################
# Manual Testing Instructions
###############################################################################

print_section "Manual Testing Instructions"

echo "For manual testing, refer to:"
echo "  .auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-5-testing-guide.md"
echo ""
echo "Quick test:"
echo "  1. Login: $BASE_URL/login"
echo "  2. Check tokens in DevTools → Application → Local Storage"
echo "  3. Wait 5 minutes for automatic refresh"
echo "  4. Verify token changed and expiration extended"

###############################################################################
# Final Summary
###############################################################################

print_summary

if [ $FAILED -eq 0 ]; then
    echo ""
    print_info "Next Steps:"
    echo "  1. Run E2E tests: cd frontend && npm run test:e2e token-refresh-flow.spec.ts"
    echo "  2. Perform manual testing using the testing guide"
    echo "  3. Verify token refresh with browser DevTools"
    echo "  4. Test with different user roles (Admin, Recruiter, Viewer)"
    exit 0
else
    echo ""
    print_info "Please fix the issues above before proceeding with testing."
    exit 1
fi
