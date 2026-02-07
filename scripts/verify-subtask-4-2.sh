#!/bin/bash

###############################################################################
# Verification Script for Subtask 4-2: Test Login Flow with Valid Credentials
#
# This script performs automated verification of the login flow implementation.
# It checks services, configuration, file structure, and provides guidance
# for manual E2E testing.
#
# Usage:
#   bash scripts/verify-subtask-4-2.sh
#
# Prerequisites:
#   - Keycloak service running on http://localhost:8080
#   - Frontend running on http://localhost:5173
#   - Backend running on http://localhost:8000
#   - curl, grep, jq commands available
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
REALM="${REALM:-agenthr}"
FRONTEND_CLIENT="${FRONTEND_CLIENT:-agenthr-frontend}"
BACKEND_CLIENT="${BACKEND_CLIENT:-agenthr-backend}"

# Test user credentials (default admin user)
TEST_USER_EMAIL="${TEST_USER_EMAIL:-admin@agenthr.com}"
TEST_USER_PASSWORD="${TEST_USER_PASSWORD:-admin123}"

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_section() {
    echo -e "\n${BLUE}▶ $1${NC}\n"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASS_COUNT++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

print_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARN_COUNT++))
}

print_info() {
    echo -e "  $1"
}

check_http() {
    local url="$1"
    local description="$2"

    if curl -s -f -o /dev/null -w "%{http_code}" "$url" > /dev/null 2>&1; then
        print_pass "$description"
        return 0
    else
        print_fail "$description"
        return 1
    fi
}

###############################################################################
# Main Verification
###############################################################################

main() {
    print_header "Subtask 4-2 Verification: Login Flow Testing"

    # 1. Service Health Checks
    print_section "1. Service Health Checks"

    echo "Checking if required services are running..."

    # Check Frontend
    if check_http "$FRONTEND_URL" "Frontend is accessible at $FRONTEND_URL"; then
        FRONTEND_VERSION=$(curl -s "$FRONTEND_URL" | grep -oP '(?<=<meta name="version" content=")[^"]*' || echo "unknown")
        print_info "Frontend version: $FRONTEND_VERSION"
    fi

    # Check Keycloak
    if check_http "$KEYCLOAK_URL/health/ready" "Keycloak is healthy at $KEYCLOAK_URL"; then
        KEYCLOAK_VERSION=$(curl -s "$KEYCLOAK_URL/realms/$REALM/.well-known/openid-configuration" | jq -r '.issuer' || echo "unknown")
        print_info "Keycloak realm: $KEYCLOAK_VERSION"
    fi

    # Check Backend
    if check_http "$BACKEND_URL/docs" "Backend API docs accessible at $BACKEND_URL"; then
        print_info "Backend API documentation available"
    fi

    # 2. Frontend Login Page Accessibility
    print_section "2. Frontend Login Page Accessibility"

    echo "Checking login page components..."

    # Check login page loads
    LOGIN_PAGE=$(curl -s "$FRONTEND_URL/login")
    if [ $? -eq 0 ] && [ -n "$LOGIN_PAGE" ]; then
        print_pass "Login page loads successfully"

        # Check for key elements
        if echo "$LOGIN_PAGE" | grep -q 'input.*type="email"'; then
            print_pass "Email input field present"
        else
            print_fail "Email input field not found"
        fi

        if echo "$LOGIN_PAGE" | grep -q 'input.*type="password"'; then
            print_pass "Password input field present"
        else
            print_fail "Password input field not found"
        fi

        if echo "$LOGIN_PAGE" | grep -q 'button.*type="submit"'; then
            print_pass "Login button present"
        else
            print_fail "Login button not found"
        fi

        if echo "$LOGIN_PAGE" | grep -iq 'forgot password'; then
            print_pass "Forgot Password link present"
        else
            print_warn "Forgot Password link not found"
        fi

        if echo "$LOGIN_PAGE" | grep -iq 'register\|sign up'; then
            print_pass "Registration link present"
        else
            print_warn "Registration link not found"
        fi
    else
        print_fail "Failed to load login page"
    fi

    # 3. Keycloak Configuration Verification
    print_section "3. Keycloak Configuration"

    echo "Checking Keycloak realm and client configuration..."

    # Check if realm exists
    REALM_INFO=$(curl -s "$KEYCLOAK_URL/realms/$REALM/.well-known/openid-configuration" 2>/dev/null)
    if [ -n "$REALM_INFO" ]; then
        print_pass "Realm '$REALM' exists and is accessible"

        # Check issuer
        ISSUER=$(echo "$REALM_INFO" | jq -r '.issuer')
        print_info "Issuer: $ISSUER"

        # Check authorization endpoint
        AUTH_ENDPOINT=$(echo "$REALM_INFO" | jq -r '.authorization_endpoint')
        print_info "Auth endpoint: $AUTH_ENDPOINT"

        # Check token endpoint
        TOKEN_ENDPOINT=$(echo "$REALM_INFO" | jq -r '.token_endpoint')
        print_info "Token endpoint: $TOKEN_ENDPOINT"
    else
        print_fail "Realm '$REALM' not found or not accessible"
    fi

    # Check frontend client
    if command -v jq &> /dev/null; then
        # Try to get client info from Keycloak (requires admin token)
        print_info "Note: Detailed client verification requires Keycloak admin token"
        print_info "Run 'bash scripts/setup-keycloak-realm.sh' to verify client configuration"
    fi

    # 4. Backend Auth Endpoints
    print_section "4. Backend Authentication Endpoints"

    echo "Checking backend auth endpoints..."

    # Check auth endpoints exist (by trying OPTIONS)
    AUTH_ENDPOINTS=("/api/auth/login" "/api/auth/logout" "/api/auth/refresh" "/api/auth/me" "/api/auth/validate")

    for endpoint in "${AUTH_ENDPOINTS[@]}"; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "$BACKEND_URL$endpoint" 2>/dev/null || echo "000")
        if [ "$STATUS" = "200" ] || [ "$STATUS" = "204" ] || [ "$STATUS" = "405" ]; then
            print_pass "Endpoint $endpoint exists (HTTP $STATUS)"
        else
            print_warn "Endpoint $endpoint not accessible (HTTP $STATUS)"
        fi
    done

    # 5. File Structure Verification
    print_section "5. File Structure Verification"

    echo "Checking required files exist..."

    # Frontend files
    FRONTEND_FILES=(
        "frontend/src/auth/LoginPage.tsx"
        "frontend/src/auth/RegisterPage.tsx"
        "frontend/src/auth/CallbackPage.tsx"
        "frontend/src/auth/ProtectedRoute.tsx"
        "frontend/src/contexts/AuthContext.tsx"
        "frontend/src/api/client.ts"
    )

    for file in "${FRONTEND_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_pass "File exists: $file"
        else
            print_fail "File missing: $file"
        fi
    done

    # Backend files
    BACKEND_FILES=(
        "backend/middleware/auth.py"
        "backend/api/auth.py"
        "backend/config.py"
    )

    for file in "${BACKEND_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_pass "File exists: $file"
        else
            print_fail "File missing: $file"
        fi
    done

    # E2E test files
    E2E_FILES=(
        "frontend/e2e/login-flow.spec.ts"
        "frontend/e2e/registration-flow.spec.ts"
    )

    for file in "${E2E_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_pass "E2E test file exists: $file"
        else
            print_warn "E2E test file missing: $file"
        fi
    done

    # 6. Playwright Configuration
    print_section "6. Playwright E2E Test Configuration"

    echo "Checking Playwright setup..."

    if [ -f "frontend/playwright.config.ts" ]; then
        print_pass "Playwright config file exists"

        # Check if Playwright is installed
        if [ -d "frontend/node_modules/@playwright" ]; then
            print_pass "Playwright is installed"
        else
            print_warn "Playwright may not be installed (run 'cd frontend && npm install')"
        fi

        # Check browsers are installed
        if command -v npx &> /dev/null; then
            if npx playwright --version &> /dev/null; then
                PLAYWRIGHT_VERSION=$(npx playwright --version 2>/dev/null || echo "unknown")
                print_pass "Playwright CLI available: $PLAYWRIGHT_VERSION"
            else
                print_warn "Playwright CLI not available"
            fi
        else
            print_warn "npx not found (Node.js/npm may not be installed)"
        fi
    else
        print_fail "Playwright config file missing"
    fi

    # 7. Integration Points Verification
    print_section "7. Integration Points Verification"

    echo "Checking integration between components..."

    # Check AuthContext exports
    if [ -f "frontend/src/contexts/AuthContext.tsx" ]; then
        if grep -q "export.*oidcConfig" frontend/src/contexts/AuthContext.tsx; then
            print_pass "AuthContext exports oidcConfig"
        else
            print_warn "AuthContext may not export oidcConfig"
        fi

        if grep -q "useAuthContext" frontend/src/contexts/AuthContext.tsx; then
            print_pass "AuthContext provides useAuthContext hook"
        else
            print_fail "AuthContext missing useAuthContext hook"
        fi
    fi

    # Check API client has auth interceptor
    if [ -f "frontend/src/api/client.ts" ]; then
        if grep -q "Authorization" frontend/src/api/client.ts; then
            print_pass "API client includes Authorization header"
        else
            print_warn "API client may not include Authorization header"
        fi
    fi

    # Check ProtectedRoute component
    if [ -f "frontend/src/auth/ProtectedRoute.tsx" ]; then
        if grep -q "useAuthContext" frontend/src/auth/ProtectedRoute.tsx; then
            print_pass "ProtectedRoute uses AuthContext"
        else
            print_warn "ProtectedRoute may not integrate with AuthContext"
        fi
    fi

    # 8. Environment Variables Check
    print_section "8. Environment Variables Check"

    echo "Checking environment configuration..."

    # Frontend env vars
    FRONTEND_ENV_VARS=(
        "VITE_KEYCLOAK_URL"
        "VITE_KEYCLOAK_REALM"
        "VITE_KEYCLOAK_CLIENT_ID"
    )

    print_info "Frontend environment variables (defaults):"
    print_info "  VITE_KEYCLOAK_URL=${VITE_KEYCLOAK_URL:-http://localhost:8080}"
    print_info "  VITE_KEYCLOAK_REALM=${VITE_KEYCLOAK_REALM:-agenthr}"
    print_info "  VITE_KEYCLOAK_CLIENT_ID=${VITE_KEYCLOAK_CLIENT_ID:-agenthr-frontend}"

    # Backend env vars
    BACKEND_ENV_VARS=(
        "KEYCLOAK_SERVER_URL"
        "KEYCLOAK_REALM"
        "KEYCLOAK_CLIENT_ID"
        "KEYCLOAK_CLIENT_SECRET"
    )

    print_info "Backend environment variables:"
    if [ -f ".env" ]; then
        if grep -q "KEYCLOAK_SERVER_URL" .env; then
            print_pass "KEYCLOAK_SERVER_URL configured in .env"
        else
            print_warn "KEYCLOAK_SERVER_URL not found in .env"
        fi

        if grep -q "KEYCLOAK_REALM" .env; then
            print_pass "KEYCLOAK_REALM configured in .env"
        else
            print_warn "KEYCLOAK_REALM not found in .env"
        fi

        if grep -q "KEYCLOAK_CLIENT_ID" .env; then
            print_pass "KEYCLOAK_CLIENT_ID configured in .env"
        else
            print_warn "KEYCLOAK_CLIENT_ID not found in .env"
        fi

        if grep -q "KEYCLOAK_CLIENT_SECRET" .env; then
            print_pass "KEYCLOAK_CLIENT_SECRET configured in .env"
        else
            print_warn "KEYCLOAK_CLIENT_SECRET not found in .env"
        fi
    else
        print_warn ".env file not found (create from .env.example)"
    fi

    # 9. Manual Testing Guidance
    print_section "9. Manual Testing Guidance"

    echo "E2E automated testing requires running Playwright tests:"
    echo ""
    print_info "To run E2E tests:"
    echo "  cd frontend"
    echo "  npm run test:e2e"
    echo ""
    print_info "To run specific login flow tests:"
    echo "  cd frontend"
    echo "  npx playwright test login-flow.spec.ts"
    echo ""
    print_info "For manual testing, follow the guide at:"
    echo "  .auto-claude/specs/.../subtask-4-2-testing-guide.md"
    echo ""

    # Provide test credentials
    echo "Test credentials for manual testing:"
    print_info "  Email: $TEST_USER_EMAIL"
    print_info "  Password: $TEST_USER_PASSWORD"
    print_info "  Keycloak Admin: http://localhost:8080/admin"
    echo ""

    # 10. Summary and Next Steps
    print_section "10. Verification Summary"

    TOTAL_CHECKS=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))
    PASS_PERCENTAGE=$((PASS_COUNT * 100 / TOTAL_CHECKS))

    echo "Total checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
    echo -e "${YELLOW}Warnings: $WARN_COUNT${NC}"
    echo -e "${RED}Failed: $FAIL_COUNT${NC}"
    echo ""
    echo "Pass rate: $PASS_PERCENTAGE%"

    if [ $FAIL_COUNT -eq 0 ]; then
        echo -e "\n${GREEN}✓ All critical checks passed!${NC}\n"
        echo "Next steps:"
        echo "  1. Run E2E tests: cd frontend && npm run test:e2e"
        echo "  2. Perform manual testing using the guide"
        echo "  3. Update implementation_plan.json with status: 'completed'"
        echo "  4. Commit changes with: git add . && git commit -m 'auto-claude: subtask-4-2 - Test login flow with valid credentials'"
    else
        echo -e "\n${RED}✗ Some checks failed. Please fix the issues above.${NC}\n"
        echo "Common issues:"
        echo "  - Services not running: Start Keycloak, frontend, backend"
        echo "  - Missing files: Check implementation is complete"
        echo "  - Configuration errors: Verify .env and Keycloak settings"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check service logs: docker-compose logs [service]"
        echo "  2. Verify Keycloak setup: bash scripts/verify-subtask-1-4.sh"
        echo "  3. Review testing guide for detailed scenarios"
    fi

    echo ""
    print_info "Verification complete!"
    echo ""

    # Return exit code based on failures
    if [ $FAIL_COUNT -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
