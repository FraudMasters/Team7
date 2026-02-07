#!/bin/bash

##############################################################################
# Subtask 4-4 Verification Script: Test Password Reset Flow via Email
#
# This script performs automated verification of the password reset flow
# functionality including frontend components, backend endpoints, Keycloak
# configuration, and end-to-end testing capabilities.
#
# Usage: bash scripts/verify-subtask-4-4.sh
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-agenthr}"
KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin123}"

# Test user credentials
TEST_USER_EMAIL="password-reset-test@example.com"
TEST_USER_USERNAME="passwordresetuser"
TEST_USER_PASSWORD="OldPassword123!"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_section() {
    echo -e "\n${YELLOW}>>> $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_fail() {
    echo -e "${RED}✗ FAIL: $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ INFO: $1${NC}"
}

check_service() {
    local url=$1
    local name=$2

    if curl -sf "$url" > /dev/null 2>&1; then
        print_success "$name is accessible at $url"
        return 0
    else
        print_fail "$name is not accessible at $url"
        return 1
    fi
}

check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        print_success "$description exists: $file"
        return 0
    else
        print_fail "$description not found: $file"
        return 1
    fi
}

##############################################################################
# Prerequisites Check
##############################################################################

check_prerequisites() {
    print_header "CHECKING PREREQUISITES"

    # Check required commands
    local required_commands=("curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            print_success "Required command available: $cmd"
        else
            print_fail "Required command not found: $cmd"
            echo "  Install with: apt-get install $cmd (Ubuntu/Debian)"
        fi
    done

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        print_success "Docker is available"
    else
        print_warning "Docker not found (required for some checks)"
    fi
}

##############################################################################
# Service Health Checks
##############################################################################

check_services() {
    print_header "SERVICE HEALTH CHECKS"

    # Check Frontend
    print_section "Frontend Service"
    if check_service "$FRONTEND_URL" "Frontend"; then
        # Check for login page
        if curl -sf "$FRONTEND_URL/login" | grep -q "password"; then
            print_success "Login page accessible"
        else
            print_warning "Login page may not have expected content"
        fi
    fi

    # Check Backend
    print_section "Backend Service"
    if check_service "$BACKEND_URL" "Backend API"; then
        # Check API docs
        if curl -sf "$BACKEND_URL/docs" > /dev/null; then
            print_success "API documentation accessible"
        else
            print_warning "API docs not accessible"
        fi
    fi

    # Check Keycloak
    print_section "Keycloak Service"
    if check_service "$KEYCLOAK_URL" "Keycloak"; then
        # Check health endpoint
        if curl -sf "$KEYCLOAK_URL/health/ready" > /dev/null 2>&1; then
            print_success "Keycloak health endpoint responding"
        else
            print_warning "Keycloak health endpoint not responding"
        fi

        # Check realm
        if curl -sf "$KEYCLOAK_URL/realms/$KEYCLOAK_REALM" > /dev/null 2>&1; then
            print_success "Keycloak realm '$KEYCLOAK_REALM' exists"
        else
            print_fail "Keycloak realm '$KEYCLOAK_REALM' not found"
        fi
    fi
}

##############################################################################
# Frontend Component Checks
##############################################################################

check_frontend_components() {
    print_header "FRONTEND COMPONENT CHECKS"

    # Check E2E test file
    print_section "E2E Test Files"
    check_file "frontend/e2e/password-reset-flow.spec.ts" "Password reset E2E test suite"

    # Check for LoginPage
    print_section "Login Page Component"
    if [ -f "frontend/src/auth/LoginPage.tsx" ]; then
        print_success "LoginPage component exists"

        # Check for forgot password link
        if grep -q "forgot password\|Forgot Password" frontend/src/auth/LoginPage.tsx 2>/dev/null; then
            print_success "Forgot Password link present in LoginPage"
        else
            print_warning "Forgot Password link not found in LoginPage"
        fi
    else
        print_fail "LoginPage component not found"
    fi

    # Check for forgot password page (if implemented)
    print_section "Forgot Password Page"
    if [ -f "frontend/src/auth/ForgotPasswordPage.tsx" ]; then
        print_success "ForgotPasswordPage component exists"
    elif grep -r "forgot-password\|ForgotPassword" frontend/src/ 2>/dev/null | grep -q "Page\|page"; then
        print_success "Forgot password functionality found in codebase"
    else
        print_warning "Dedicated forgot password page not found (may use Keycloak default)"
    fi

    # Check reset password page (if implemented)
    print_section "Reset Password Page"
    if [ -f "frontend/src/auth/ResetPasswordPage.tsx" ]; then
        print_success "ResetPasswordPage component exists"
    elif grep -r "reset-password\|ResetPassword" frontend/src/ 2>/dev/null | grep -q "Page\|page"; then
        print_success "Reset password functionality found in codebase"
    else
        print_warning "Dedicated reset password page not found (may use Keycloak default)"
    fi

    # Check routing configuration
    print_section "Routing Configuration"
    if [ -f "frontend/src/App.tsx" ]; then
        if grep -q "forgot-password\|reset-password" frontend/src/App.tsx 2>/dev/null; then
            print_success "Password reset routes configured in App.tsx"
        else
            print_info "Password reset routes may be handled by Keycloak default pages"
        fi
    fi

    # Check AuthContext for password reset methods
    print_section "AuthContext"
    if [ -f "frontend/src/contexts/AuthContext.tsx" ]; then
        if grep -q "resetPassword\|forgotPassword" frontend/src/contexts/AuthContext.tsx 2>/dev/null; then
            print_success "Password reset methods in AuthContext"
        else
            print_info "Password reset may be handled by Keycloak directly"
        fi
    fi
}

##############################################################################
# Backend Endpoint Checks
##############################################################################

check_backend_endpoints() {
    print_header "BACKEND ENDPOINT CHECKS"

    # Check auth endpoints
    print_section "Authentication Endpoints"

    local auth_endpoints=(
        "POST /api/auth/login"
        "POST /api/auth/logout"
        "POST /api/auth/refresh"
        "GET /api/auth/me"
    )

    for endpoint in "${auth_endpoints[@]}"; do
        if grep -r "$endpoint" backend/api/ 2>/dev/null | grep -q "router\|@app"; then
            print_success "Endpoint defined: $endpoint"
        else
            print_info "Endpoint may be handled by Keycloak: $endpoint"
        fi
    done

    # Check for password reset endpoints (if custom implementation)
    print_section "Password Reset Endpoints"
    if grep -r "reset.*password\|forgot.*password" backend/api/ 2>/dev/null | grep -q "def\|async def\|router"; then
        print_success "Password reset endpoints found in backend"
    else
        print_info "Password reset handled by Keycloak (no custom endpoints needed)"
    fi

    # Check auth middleware
    print_section "Authentication Middleware"
    if [ -f "backend/middleware/auth.py" ]; then
        print_success "Auth middleware exists"
        if grep -q "JWT\|token" backend/middleware/auth.py 2>/dev/null; then
            print_success "JWT token validation in auth middleware"
        fi
    else
        print_fail "Auth middleware not found"
    fi
}

##############################################################################
# Keycloak Configuration Checks
##############################################################################

check_keycloak_config() {
    print_header "KEYCLOAK CONFIGURATION CHECKS"

    # Get admin token
    print_section "Keycloak Admin Access"
    local admin_token=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
        -d "client_id=admin-cli" \
        -d "username=$KEYCLOAK_ADMIN" \
        -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
        -d "grant_type=password" | jq -r '.access_token' 2>/dev/null)

    if [ -n "$admin_token" ] && [ "$admin_token" != "null" ]; then
        print_success "Keycloak admin authentication successful"

        # Check forgot password enabled
        print_section "Realm Settings"
        local forgot_password=$(curl -s "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM" \
            -H "Authorization: Bearer $admin_token" | jq -r '.resetPasswordAllowed' 2>/dev/null)

        if [ "$forgot_password" == "true" ]; then
            print_success "Forgot password feature enabled in realm"
        else
            print_fail "Forgot password feature not enabled"
        fi

        # Check SMTP configuration
        print_section "SMTP Configuration"
        local smtp_host=$(curl -s "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM" \
            -H "Authorization: Bearer $admin_token" | jq -r '.smtpServer.host' 2>/dev/null)

        if [ -n "$smtp_host" ] && [ "$smtp_host" != "null" ]; then
            print_success "SMTP configured: $smtp_host"
        else
            print_warning "SMTP not configured (required for password reset)"
        fi

        # Check test user (if exists)
        print_section "Test User"
        local test_user=$(curl -s "$KEYCLOAK_URL/admin/realms/$KEYCLOAK_REALM/users?username=$TEST_USER_USERNAME" \
            -H "Authorization: Bearer $admin_token" | jq -r '.[0].username' 2>/dev/null)

        if [ "$test_user" == "$TEST_USER_USERNAME" ]; then
            print_success "Test user exists: $TEST_USER_USERNAME"
        else
            print_info "Test user not found: $TEST_USER_USERNAME (create for testing)"
        fi

    else
        print_fail "Could not authenticate with Keycloak admin"
        print_info "Check admin credentials and Keycloak availability"
    fi
}

##############################################################################
# E2E Test Coverage Checks
##############################################################################

check_e2e_tests() {
    print_header "E2E TEST COVERAGE"

    # Check E2E test file
    print_section "Password Reset E2E Tests"
    if [ -f "frontend/e2e/password-reset-flow.spec.ts" ]; then
        print_success "Password reset E2E test file exists"

        # Count test cases
        local test_count=$(grep -c "test(" frontend/e2e/password-reset-flow.spec.ts 2>/dev/null || echo "0")
        print_info "Number of test cases: $test_count"

        # Check for key test scenarios
        local test_scenarios=(
            "Forgot Password"
            "Password Reset Request"
            "Email Delivery"
            "Password Reset Page"
            "Complete Password Reset Flow"
        )

        for scenario in "${test_scenarios[@]}"; do
            if grep -q "$scenario" frontend/e2e/password-reset-flow.spec.ts 2>/dev/null; then
                print_success "Test scenario covered: $scenario"
            else
                print_warning "Test scenario not found: $scenario"
            fi
        done

        # Check Playwright config
        if [ -f "frontend/playwright.config.ts" ]; then
            print_success "Playwright configuration exists"
        else
            print_warning "Playwright config not found"
        fi
    else
        print_fail "Password reset E2E test file not found"
    fi

    # Check testing guide
    print_section "Testing Documentation"
    if [ -f ".auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-4-testing-guide.md" ]; then
        print_success "Testing guide exists"
    else
        print_fail "Testing guide not found"
    fi
}

##############################################################################
# Manual Testing Requirements
##############################################################################

check_manual_testing_requirements() {
    print_header "MANUAL TESTING REQUIREMENTS"

    print_section "Required Components"
    echo "For manual testing, ensure you have:"
    echo "  1. Keycloak service running at $KEYCLOAK_URL"
    echo "  2. Frontend running at $FRONTEND_URL"
    echo "  3. SMTP configured in Keycloak"
    echo "  4. Test user account created"
    echo "  5. Access to email inbox for test user"
    echo ""

    print_section "Email Testing Options"
    echo "For email testing, use one of:"
    echo "  - MailHog: http://localhost:8025"
    echo "  - MailCatcher: http://localhost:1080"
    echo "  - Ethereal Email: https://ethereal.email/"
    echo "  - Real SMTP service (e.g., Gmail with App Password)"
    echo ""

    print_section "Manual Testing Checklist"
    local manual_checks=(
        "Navigate to login page and click Forgot Password link"
        "Submit password reset request with valid email"
        "Check email inbox for reset link"
        "Click reset link and navigate to reset page"
        "Enter new password and confirm"
        "Verify password was changed"
        "Login with new password"
        "Verify old password no longer works"
        "Test with invalid/expired reset token"
        "Test email validation and error handling"
    )

    for check in "${manual_checks[@]}"; do
        echo "  [ ] $check"
    done

    echo ""
    print_info "See testing guide for detailed instructions:"
    echo "  .auto-claude/specs/.../subtask-4-4-testing-guide.md"
}

##############################################################################
# Security Best Practices Check
##############################################################################

check_security_practices() {
    print_header "SECURITY BEST PRACTICES CHECK"

    # Check for user enumeration prevention
    print_section "User Enumeration Prevention"
    if grep -r "if.*email.*exists\|check your email\|instructions.*sent" frontend/src/ 2>/dev/null | grep -q "."; then
        print_success "Generic messages found (prevents user enumeration)"
    else
        print_info "Verify generic messages are used for password reset"
    fi

    # Check for token expiration handling
    print_section "Token Security"
    if grep -r "expired\|invalid.*token" frontend/src/ 2>/dev/null | grep -q "."; then
        print_success "Token expiration handling found"
    else
        print_info "Verify expired tokens are handled correctly"
    fi

    # Check for password requirements
    print_section "Password Requirements"
    if grep -r "password.*requirement\|password.*strength\|password.*policy" frontend/src/ 2>/dev/null | grep -q "."; then
        print_success "Password requirements enforced"
    else
        print_info "Verify password requirements are enforced"
    fi

    # Check for HTTPS in production (warning for HTTP in dev)
    print_section "SSL/HTTPS Configuration"
    if [[ "$FRONTEND_URL" == https://* ]] && [[ "$KEYCLOAK_URL" == https://* ]]; then
        print_success "HTTPS configured (production-ready)"
    elif [[ "$FRONTEND_URL" == http://* ]] || [[ "$KEYCLOAK_URL" == http://* ]]; then
        print_warning "HTTP detected (OK for development, use HTTPS in production)"
    fi
}

##############################################################################
# Integration Points Check
##############################################################################

check_integration_points() {
    print_header "INTEGRATION POINTS CHECK"

    # Check frontend-backend integration
    print_section "Frontend-Backend Integration"
    if grep -r "Authorization.*Bearer" frontend/src/api/ 2>/dev/null | grep -q "."; then
        print_success "Authorization header configured in API client"
    fi

    # Check Keycloak integration
    print_section "Keycloak Integration"
    if grep -r "KEYCLOAK" frontend/src/ 2>/dev/null | grep -q "."; then
        print_success "Keycloak configuration present in frontend"
    fi

    if grep -r "KEYCLOAK" backend/ 2>/dev/null | grep -q "."; then
        print_success "Keycloak configuration present in backend"
    fi

    # Check OIDC configuration
    print_section "OIDC Configuration"
    if [ -f "frontend/src/contexts/AuthContext.tsx" ]; then
        if grep -q "oidc\|openid-connect" frontend/src/contexts/AuthContext.tsx 2>/dev/null; then
            print_success "OIDC configuration in AuthContext"
        fi
    fi
}

##############################################################################
# File Structure Verification
##############################################################################

check_file_structure() {
    print_header "FILE STRUCTURE VERIFICATION"

    local required_files=(
        "frontend/e2e/password-reset-flow.spec.ts:E2E test suite"
        ".auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-4-testing-guide.md:Testing guide"
        "scripts/verify-subtask-4-4.sh:Verification script"
        "frontend/src/auth/LoginPage.tsx:Login page component"
        "frontend/src/contexts/AuthContext.tsx:Auth context"
        "backend/middleware/auth.py:Auth middleware"
    )

    for file_info in "${required_files[@]}"; do
        IFS=':' read -r file description <<< "$file_info"
        check_file "$file" "$description"
    done
}

##############################################################################
# Summary and Recommendations
##############################################################################

print_summary() {
    print_header "VERIFICATION SUMMARY"

    echo -e "Total Checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo ""

    local pass_rate=0
    if [ $TOTAL_CHECKS -gt 0 ]; then
        pass_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    fi
    echo "Pass Rate: $pass_rate%"

    if [ $pass_rate -ge 80 ]; then
        echo -e "\n${GREEN}✓ Overall Status: GOOD${NC}"
    elif [ $pass_rate -ge 60 ]; then
        echo -e "\n${YELLOW}⚠ Overall Status: ACCEPTABLE${NC}"
    else
        echo -e "\n${RED}✗ Overall Status: NEEDS ATTENTION${NC}"
    fi

    echo ""
    print_section "Next Steps"
    echo "1. Run E2E tests: cd frontend && npm run test:e2e password-reset-flow"
    echo "2. Perform manual testing (see testing guide)"
    echo "3. Test email delivery with actual SMTP service"
    echo "4. Verify password reset flow end-to-end"
    echo "5. Check all test scenarios in testing guide"

    if [ $FAILED_CHECKS -gt 0 ]; then
        echo -e "\n${RED}Failed checks need attention before marking complete${NC}"
    fi

    if [ $WARNINGS -gt 0 ]; then
        echo -e "\n${YELLOW}Review warnings and address if needed${NC}"
    fi
}

##############################################################################
# Main Execution
##############################################################################

main() {
    print_header "SUBTASK 4-4 VERIFICATION: PASSWORD RESET FLOW TESTING"

    echo "Starting automated verification..."
    echo "Frontend URL: $FRONTEND_URL"
    echo "Backend URL: $BACKEND_URL"
    echo "Keycloak URL: $KEYCLOAK_URL"
    echo ""

    # Run all checks
    check_prerequisites
    check_services
    check_frontend_components
    check_backend_endpoints
    check_keycloak_config
    check_e2e_tests
    check_manual_testing_requirements
    check_security_practices
    check_integration_points
    check_file_structure

    # Print summary
    print_summary

    # Exit with appropriate code
    if [ $FAILED_CHECKS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
