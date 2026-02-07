#!/bin/bash

##############################################################################
# Verification Script for Subtask 4-3: Role-Based Access Control Testing
#
# This script performs automated health checks for RBAC testing infrastructure
# and provides guidance for manual testing execution.
#
# Prerequisites:
# - Keycloak server running on http://localhost:8080
# - Frontend running on http://localhost:5173
# - Backend running on http://localhost:8000
# - Test users created in Keycloak (admin, recruiter, viewer)
##############################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counter for results
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASS_COUNT++))
}

print_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAIL_COUNT++))
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
    ((WARN_COUNT++))
}

print_info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

check_service() {
    local url=$1
    local name=$2
    local timeout=${3:-5}

    if curl -sf --max-time "$timeout" "$url" > /dev/null 2>&1; then
        print_success "$name is accessible at $url"
        return 0
    else
        print_fail "$name is NOT accessible at $url"
        return 1
    fi
}

##############################################################################
# Main Execution
##############################################################################

main() {
    print_header "RBAC Testing Verification - Subtask 4-3"

    echo -e "This script will verify the testing infrastructure for role-based access control."
    echo -e "It checks service health, test user availability, and provides testing guidance.\n"

    ##############################################################################
    # Check 1: Service Health
    ##############################################################################
    print_header "1. Service Health Checks"

    # Check Frontend
    if check_service "http://localhost:5173" "Frontend"; then
        FRONTEND_RUNNING=true
    else
        FRONTEND_RUNNING=false
    fi

    # Check Backend
    if check_service "http://localhost:8000/docs" "Backend API Docs"; then
        BACKEND_RUNNING=true
    else
        BACKEND_RUNNING=false
    fi

    # Check Keycloak
    if check_service "http://localhost:8080/health/ready" "Keycloak"; then
        KEYCLOAK_RUNNING=true
    else
        KEYCLOAK_RUNNING=false
    fi

    ##############################################################################
    # Check 2: Test User Existence
    ##############################################################################
    print_header "2. Test User Verification"

    if [ "$KEYCLOAK_RUNNING" = true ]; then
        # Try to get admin token to verify user exists
        print_info "Verifying admin user exists..."
        ADMIN_TOKEN=$(curl -s -X POST \
            "http://localhost:8080/realms/agenthr/protocol/openid-connect/token" \
            -d "client_id=agenthr-backend" \
            -d "username=admin@agenthr.com" \
            -d "password=admin123" \
            -d "grant_type=password" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")

        if [ "$ADMIN_TOKEN" = "200" ]; then
            print_success "Admin user (admin@agenthr.com) exists and can authenticate"
        else
            print_fail "Admin user (admin@agenthr.com) does not exist or wrong password"
        fi

        # Check if recruiter and viewer users exist (will fail if not created)
        print_info "Checking for test users (recruiter, viewer)..."

        RECRUITER_TOKEN=$(curl -s -X POST \
            "http://localhost:8080/realms/agenthr/protocol/openid-connect/token" \
            -d "client_id=agenthr-backend" \
            -d "username=recruiter@agenthr.com" \
            -d "password=recruiter123" \
            -d "grant_type=password" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")

        if [ "$RECRUITER_TOKEN" = "200" ]; then
            print_success "Recruiter user (recruiter@agenthr.com) exists"
            RECRUITER_EXISTS=true
        else
            print_warning "Recruiter user (recruiter@agenthr.com) does not exist - needs to be created"
            RECRUITER_EXISTS=false
        fi

        VIEWER_TOKEN=$(curl -s -X POST \
            "http://localhost:8080/realms/agenthr/protocol/openid-connect/token" \
            -d "client_id=agenthr-backend" \
            -d "username=viewer@agenthr.com" \
            -d "password=viewer123" \
            -d "grant_type=password" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")

        if [ "$VIEWER_TOKEN" = "200" ]; then
            print_success "Viewer user (viewer@agenthr.com) exists"
            VIEWER_EXISTS=true
        else
            print_warning "Viewer user (viewer@agenthr.com) does not exist - needs to be created"
            VIEWER_EXISTS=false
        fi
    else
        print_warning "Skipping user checks - Keycloak not running"
    fi

    ##############################################################################
    # Check 3: E2E Test File
    ##############################################################################
    print_header "3. E2E Test Suite"

    if [ -f "frontend/e2e/rbac-access-control.spec.ts" ]; then
        print_success "E2E test file exists: frontend/e2e/rbac-access-control.spec.ts"

        # Count test cases
        TEST_COUNT=$(grep -c "test('" "frontend/e2e/rbac-access-control.spec.ts" 2>/dev/null || echo "0")
        print_info "Found $TEST_COUNT test cases in RBAC test suite"

        if [ "$TEST_COUNT" -ge 20 ]; then
            print_success "E2E test suite has comprehensive coverage ($TEST_COUNT tests)"
        else
            print_warning "E2E test suite may need more tests (currently: $TEST_COUNT)"
        fi
    else
        print_fail "E2E test file not found: frontend/e2e/rbac-access-control.spec.ts"
    fi

    ##############################################################################
    # Check 4: Testing Documentation
    ##############################################################################
    print_header "4. Testing Documentation"

    if [ -f ".auto-claude/specs/055-1-user-authentication-authorization-system/subtask-4-3-testing-guide.md" ]; then
        print_success "Manual testing guide exists"
        print_info "Location: .auto-claude/specs/.../subtask-4-3-testing-guide.md"
    else
        print_fail "Manual testing guide not found"
    fi

    ##############################################################################
    # Check 5: Backend Role Protection
    ##############################################################################
    print_header "5. Backend Role Protection Verification"

    if [ "$BACKEND_RUNNING" = true ]; then
        # Check if backend has role-protected endpoints
        print_info "Checking for role-protected endpoints..."

        # Try to access admin endpoint without auth (should return 401)
        UNAUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/users/" 2>/dev/null || echo "000")

        if [ "$UNAUTH_STATUS" = "401" ]; then
            print_success "Admin endpoint requires authentication (401 Unauthorized without token)"
        else
            print_warning "Admin endpoint returned $UNAUTH_STATUS (expected 401)"
        fi

        # Try with admin token (should return 200 or 404)
        if [ "$ADMIN_TOKEN" = "200" ]; then
            ADMIN_ENDPOINT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: Bearer $ADMIN_TOKEN" \
                "http://localhost:8000/api/users/" 2>/dev/null || echo "000")

            if [ "$ADMIN_ENDPOINT_STATUS" = "200" ] || [ "$ADMIN_ENDPOINT_STATUS" = "404" ]; then
                print_success "Admin endpoint accessible with Admin role (status: $ADMIN_ENDPOINT_STATUS)"
            else
                print_warning "Admin endpoint returned unexpected status: $ADMIN_ENDPOINT_STATUS"
            fi
        fi
    else
        print_warning "Skipping backend checks - Backend not running"
    fi

    ##############################################################################
    # Check 6: Frontend Protected Routes
    ##############################################################################
    print_header "6. Frontend Protected Routes"

    if [ -f "frontend/src/App.tsx" ]; then
        print_info "Checking frontend route protection..."

        # Check if ProtectedRoute is imported
        if grep -q "ProtectedRoute" "frontend/src/App.tsx" 2>/dev/null; then
            print_success "ProtectedRoute component is used in App.tsx"

            # Count protected routes
            PROTECTED_COUNT=$(grep -c "ProtectedRoute" "frontend/src/App.tsx" 2>/dev/null || echo "0")
            print_info "Found $PROTECTED_COUNT protected route definitions"

            if [ "$PROTECTED_COUNT" -ge 5 ]; then
                print_success "Multiple routes are protected with role-based access"
            fi
        else
            print_warning "ProtectedRoute not found in App.tsx"
        fi
    else
        print_fail "frontend/src/App.tsx not found"
    fi

    ##############################################################################
    # Check 7: Test Environment Setup
    ##############################################################################
    print_header "7. Test Environment"

    # Check if Playwright is configured
    if [ -f "frontend/playwright.config.ts" ]; then
        print_success "Playwright configuration exists"
    else
        print_warning "Playwright configuration not found"
    fi

    # Check if .env files have test credentials
    if [ -f ".env" ]; then
        if grep -q "KEYCLOAK" ".env" 2>/dev/null; then
            print_success ".env file contains Keycloak configuration"
        else
            print_warning ".env file missing Keycloak configuration"
        fi
    else
        print_warning ".env file not found"
    fi

    ##############################################################################
    # Summary and Recommendations
    ##############################################################################
    print_header "Verification Summary"

    echo -e "Total Checks: $((PASS_COUNT + FAIL_COUNT + WARN_COUNT))"
    echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
    echo -e "${RED}Failed: $FAIL_COUNT${NC}"
    echo -e "${YELLOW}Warnings: $WARN_COUNT${NC}"

    echo -e "\n"

    if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -eq 0 ]; then
        echo -e "${GREEN}All checks passed! Testing infrastructure is ready.${NC}\n"
    elif [ "$FAIL_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}Some warnings detected. Review output above for details.${NC}\n"
    else
        echo -e "${RED}Some checks failed. Address issues before proceeding with tests.${NC}\n"
    fi

    ##############################################################################
    # Next Steps Guidance
    ##############################################################################
    print_header "Next Steps"

    if [ "$RECRUITER_EXISTS" = false ] || [ "$VIEWER_EXISTS" = false ]; then
        echo -e "${YELLOW}1. Create Test Users in Keycloak:${NC}"
        echo -e "   - Log in to http://localhost:8080/admin"
        echo -e "   - Navigate to Users → Add user"
        echo -e "   - Create recruiter@agenthr.com with Recruiter role"
        echo -e "   - Create viewer@agenthr.com with Viewer role"
        echo -e "   - See testing guide for detailed instructions\n"
    fi

    if [ "$FRONTEND_RUNNING" = true ] && [ "$BACKEND_RUNNING" = true ] && [ "$KEYCLOAK_RUNNING" = true ]; then
        echo -e "${GREEN}All services are running! You can proceed with testing:${NC}\n"

        echo -e "Option 1: Run E2E Tests (Automated)"
        echo -e "  cd frontend"
        echo -e "  npm run test:e2e rbac-access-control.spec.ts\n"

        echo -e "Option 2: Manual Testing (Guided)"
        echo -e "  Follow the scenarios in:"
        echo -e "  .auto-claude/specs/.../subtask-4-3-testing-guide.md\n"

        echo -e "Option 3: Quick API Tests"
        echo -e "  bash scripts/quick-rbac-test.sh\n"
    else
        echo -e "${YELLOW}Start required services:${NC}"
        echo -e "  docker-compose up -d keycloak postgres"
        echo -e "  cd backend && python main.py  # Terminal 1"
        echo -e "  cd frontend && npm run dev    # Terminal 2\n"
    fi

    ##############################################################################
    # Quick Test Commands (if services are running)
    ##############################################################################
    if [ "$BACKEND_RUNNING" = true ] && [ "$KEYCLOAK_RUNNING" = true ] && [ "$ADMIN_TOKEN" = "200" ]; then
        print_header "Quick API Test (Admin Access)"

        print_info "Testing Admin access to /api/users/ endpoint..."
        RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
            "http://localhost:8000/api/users/" 2>/dev/null || echo '{"error":"request failed"}')

        if echo "$RESPONSE" | grep -q "users"; then
            print_success "Admin can access user management endpoint"
        else
            print_warning "Admin endpoint response unexpected"
        fi
    fi

    if [ "$BACKEND_RUNNING" = true ] && [ "$KEYCLOAK_RUNNING" = true ] && [ "$RECRUITER_EXISTS" = true ]; then
        print_header "Quick API Test (Recruiter Blocked)"

        print_info "Testing Recruiter blocked from /api/users/ endpoint..."
        RECRUITER_TOKEN=$(curl -s -X POST \
            "http://localhost:8080/realms/agenthr/protocol/openid-connect/token" \
            -d "client_id=agenthr-backend" \
            -d "username=recruiter@agenthr.com" \
            -d "password=recruiter123" \
            -d "grant_type=password" \
            -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")

        if [ "$RECRUITER_TOKEN" = "200" ]; then
            # Get actual token
            RECRUITER_ACCESS=$(curl -s -X POST \
                "http://localhost:8080/realms/agenthr/protocol/openid-connect/token" \
                -d "client_id=agenthr-backend" \
                -d "username=recruiter@agenthr.com" \
                -d "password=recruiter123" \
                -d "grant_type=password" | jq -r '.access_token' 2>/dev/null || echo "")

            if [ -n "$RECRUITER_ACCESS" ]; then
                RESPONSE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                    -H "Authorization: Bearer $RECRUITER_ACCESS" \
                    "http://localhost:8000/api/users/" 2>/dev/null || echo "000")

                if [ "$RESPONSE_STATUS" = "403" ]; then
                    print_success "Recruiter correctly blocked from admin endpoint (403 Forbidden)"
                else
                    print_warning "Recruiter endpoint returned $RESPONSE_STATUS (expected 403)"
                fi
            fi
        fi
    fi

    ##############################################################################
    # Documentation Reference
    ##############################################################################
    print_header "Documentation Reference"

    echo -e "E2E Test Suite: frontend/e2e/rbac-access-control.spec.ts"
    echo -e "Manual Testing Guide: .auto-claude/specs/.../subtask-4-3-testing-guide.md"
    echo -e "This Script: scripts/verify-subtask-4-3.sh"
    echo -e ""

    echo -e "For detailed testing scenarios and troubleshooting,"
    echo -e "refer to the manual testing guide."

    ##############################################################################
    # Exit with appropriate code
    ##############################################################################
    if [ "$FAIL_COUNT" -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
