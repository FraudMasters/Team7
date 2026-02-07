#!/bin/bash

###############################################################################
# Verification Script for Subtask 4-1
# Test user registration flow with email verification
#
# This script performs automated checks and provides guidance for manual
# testing of the user registration flow with email verification.
#
# Usage: bash scripts/verify-subtask-4-1.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:5173}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

print_failure() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN_COUNT++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_service() {
    local name="$1"
    local url="$2"

    if curl -sf -o /dev/null -w "%{http_code}" "$url" > /dev/null 2>&1; then
        print_success "$name is running and accessible"
        return 0
    else
        print_failure "$name is not accessible at $url"
        return 1
    fi
}

print_header "VERIFICATION: User Registration Flow with Email Verification"
print_info "Subtask: subtask-4-1"
print_info "This script verifies the registration flow components"
echo ""

###############################################################################
# 1. Service Health Checks
###############################################################################

print_header "1. Service Health Checks"

check_service "Frontend" "$BASE_URL" || true
check_service "Keycloak" "$KEYCLOAK_URL/health/ready" || true
check_service "Backend API" "$BACKEND_URL/docs" || true

# Check Keycloak realm exists
REALM_CHECK=$(curl -sf "$KEYCLOAK_URL/realms/agenthr/.well-known/openid-configuration" > /dev/null 2>&1 && echo "yes" || echo "no")
if [ "$REALM_CHECK" = "yes" ]; then
    print_success "Keycloak realm 'agenthr' exists"
else
    print_failure "Keycloak realm 'agenthr' not found"
fi

###############################################################################
# 2. Frontend Registration Page
###############################################################################

print_header "2. Frontend Registration Page"

# Check if registration page loads
REGISTRATION_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/register" 2>/dev/null || echo "000")
if [ "$REGISTRATION_HTTP" = "200" ]; then
    print_success "Registration page is accessible (HTTP $REGISTRATION_HTTP)"
else
    print_failure "Registration page returned HTTP $REGISTRATION_HTTP"
fi

# Check if login page exists (for navigation test)
LOGIN_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/login" 2>/dev/null || echo "000")
if [ "$LOGIN_HTTP" = "200" ]; then
    print_success "Login page is accessible (HTTP $LOGIN_HTTP)"
else
    print_failure "Login page returned HTTP $LOGIN_HTTP"
fi

###############################################################################
# 3. Keycloak Registration Configuration
###############################################################################

print_header "3. Keycloak Registration Configuration"

# Check if registration is enabled in realm
# We can't directly check this without admin credentials, but we can check
# if the registration endpoint is accessible
REG_ENDPOINT=$(curl -sf "$KEYCLOAK_URL/realms/agenthr/protocol/openid-connect/registrations" > /dev/null 2>&1 && echo "yes" || echo "no")
if [ "$REG_ENDPOINT" = "yes" ]; then
    print_success "Keycloak registration endpoint is accessible"
else
    print_warning "Keycloak registration endpoint check failed (may require authentication)"
fi

###############################################################################
# 4. Backend Auth Endpoints
###############################################################################

print_header "4. Backend Authentication Endpoints"

# Check if auth endpoints exist (should return 401 or 422 without proper auth)
LOGIN_ENDPOINT=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/api/auth/login" -H "Content-Type: application/json" -d '{}' 2>/dev/null || echo "000")
if [ "$LOGIN_ENDPOINT" = "422" ] || [ "$LOGIN_ENDPOINT" = "401" ]; then
    print_success "Login endpoint exists (HTTP $LOGIN_ENDPOINT - validation error expected)"
elif [ "$LOGIN_ENDPOINT" = "000" ]; then
    print_failure "Login endpoint not accessible"
else
    print_warning "Login endpoint returned unexpected HTTP $LOGIN_ENDPOINT"
fi

ME_ENDPOINT=$(curl -sf -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/auth/me" 2>/dev/null || echo "000")
if [ "$ME_ENDPOINT" = "401" ]; then
    print_success "User info endpoint exists and requires auth (HTTP 401)"
elif [ "$ME_ENDPOINT" = "000" ]; then
    print_failure "User info endpoint not accessible"
else
    print_warning "User info endpoint returned unexpected HTTP $ME_ENDPOINT"
fi

###############################################################################
# 5. File Structure Verification
###############################################################################

print_header "5. File Structure Verification"

# Check E2E test file
if [ -f "frontend/e2e/registration-flow.spec.ts" ]; then
    print_success "E2E registration test file exists"
else
    print_failure "E2E registration test file not found"
fi

# Check testing guide
if [ -f ".auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-1-testing-guide.md" ]; then
    print_success "Testing guide document exists"
else
    print_failure "Testing guide document not found"
fi

# Check AuthContext
if [ -f "frontend/src/contexts/AuthContext.tsx" ]; then
    print_success "AuthContext component exists"
else
    print_failure "AuthContext component not found"
fi

# Check RegisterPage
if [ -f "frontend/src/auth/RegisterPage.tsx" ]; then
    print_success "RegisterPage component exists"
else
    print_failure "RegisterPage component not found"
fi

# Check LoginPage
if [ -f "frontend/src/auth/LoginPage.tsx" ]; then
    print_success "LoginPage component exists"
else
    print_failure "LoginPage component not found"
fi

# Check ProtectedRoute
if [ -f "frontend/src/auth/ProtectedRoute.tsx" ]; then
    print_success "ProtectedRoute component exists"
else
    print_failure "ProtectedRoute component not found"
fi

# Check backend auth endpoints
if [ -f "backend/api/auth.py" ]; then
    print_success "Backend auth API module exists"
else
    print_failure "Backend auth API module not found"
fi

###############################################################################
# 6. Playwright Test Configuration
###############################################################################

print_header "6. Playwright Test Configuration"

# Check if Playwright is installed
if [ -f "frontend/package.json" ]; then
    if grep -q "@playwright/test" frontend/package.json; then
        print_success "Playwright is in dependencies"

        # Check if playwright config exists
        if [ -f "frontend/playwright.config.ts" ]; then
            print_success "Playwright config file exists"
        else
            print_failure "Playwright config file not found"
        fi
    else
        print_failure "Playwright not found in dependencies"
    fi
else
    print_failure "package.json not found"
fi

###############################################################################
# 7. Manual Testing Guidance
###############################################################################

print_header "7. Manual Testing Requirements"

print_info "The following checks require manual testing:"
echo ""

print_warning "Manual Test 1: Registration Form Validation"
echo "  1. Open $BASE_URL/register in browser"
echo "  2. Try entering invalid email format"
echo "  3. Verify validation error appears"
echo ""

print_warning "Manual Test 2: Registration with Email Verification"
echo "  1. Open $BASE_URL/register in browser"
echo "  2. Fill form with valid data (use test email account)"
echo "  3. Submit form"
echo "  4. Check email for verification link"
echo "  5. Click verification link"
echo "  6. Verify account is activated"
echo "  7. Login with new credentials"
echo ""

print_warning "Manual Test 3: Login Before Email Verification"
echo "  1. Complete registration but DO NOT verify email"
echo "  2. Try to login"
echo "  3. Verify error: 'Email not verified'"
echo ""

print_warning "Manual Test 4: Password Strength Indicator"
echo "  1. Open registration page"
echo "  2. Enter various passwords (weak, strong)"
echo "  3. Verify strength indicator updates correctly"
echo ""

###############################################################################
# 8. Running Automated Tests
###############################################################################

print_header "8. Running Automated Tests"

print_info "To run E2E tests, execute:"
echo ""
echo "  cd frontend"
echo "  npm run test:e2e:install    # First time only"
echo "  npm run test:e2e            # Run all E2E tests"
echo "  npm run test:e2e:ui         # Run with UI mode"
echo "  npx playwright test registration-flow.spec.ts  # Run specific test"
echo ""

# Check if we can run tests (in a restricted environment, we probably can't)
if command -v npm &> /dev/null; then
    print_info "npm is available - you can run tests"
else
    print_warning "npm not available - tests cannot be run in this environment"
fi

###############################################################################
# 9. Prerequisites Summary
###############################################################################

print_header "9. Prerequisites Summary"

print_info "Before testing, ensure:"
echo "  ✓ Keycloak is running: docker-compose up -d keycloak"
echo "  ✓ Frontend is running: cd frontend && npm run dev"
echo "  ✓ Backend is running: cd backend && uvicorn main:app --reload"
echo "  ✓ SMTP is configured in Keycloak Admin Console"
echo "  ✓ Test email account is accessible"
echo ""

###############################################################################
# 10. Final Summary
###############################################################################

print_header "VERIFICATION SUMMARY"

echo -e "${GREEN}Passed:${NC} $PASS_COUNT"
echo -e "${RED}Failed:${NC} $FAIL_COUNT"
echo -e "${YELLOW}Warnings:${NC} $WARN_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    print_success "All automated checks passed!"
    echo ""
    print_info "Next steps:"
    echo "  1. Review manual testing requirements above"
    echo "  2. Follow testing guide: subtask-4-1-testing-guide.md"
    echo "  3. Run automated E2E tests if environment allows"
    echo "  4. Document any issues found"
    echo ""

    if [ $WARN_COUNT -gt 0 ]; then
        print_warning "Some checks produced warnings - review them above"
    fi

    echo -e "${GREEN}✓ Subtask 4-1 automated verification: COMPLETE${NC}"
    exit 0
else
    print_failure "Some automated checks failed"
    echo ""
    print_info "Troubleshooting:"
    echo "  1. Ensure all services are running (Keycloak, Frontend, Backend)"
    echo "  2. Check service URLs are correct"
    echo "  3. Review error messages above"
    echo "  4. Check service logs: docker-compose logs [service]"
    echo ""

    echo -e "${RED}✗ Subtask 4-1 automated verification: FAILED${NC}"
    exit 1
fi
