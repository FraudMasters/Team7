#!/bin/bash

###############################################################################
# Role-Based Access Control (RBAC) Flow Test Script
#
# This script tests the complete RBAC enforcement:
# - Creates users with different roles (Admin, Recruiter, Hiring Manager, Viewer)
# - Tests access to protected endpoints for each role
# - Verifies 403 Forbidden for unauthorized roles
# - Verifies 200 OK for authorized roles
# - Tests role hierarchy
#
# Prerequisites:
# - Backend server running on http://localhost:8000
# - PostgreSQL database with auth tables created
#
# Usage:
#   chmod +x test_rbac_flow.sh
#   ./test_rbac_flow.sh
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API base URL
BASE_URL="http://localhost:8000"

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Cleanup function
cleanup() {
    print_header "Cleaning Up Test Users"

    # Get admin token first (we'll create one if needed)
    ADMIN_EMAIL="rbac_admin_test@example.com"

    # Try to login as admin
    ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"AdminTestPass123!\"}" || echo "")

    # If login failed, create admin user
    if [[ $ADMIN_LOGIN_RESPONSE == *"access_token"* ]]; then
        ADMIN_TOKEN=$(echo $ADMIN_LOGIN_RESPONSE | jq -r '.access_token')
        print_success "Admin user already exists, using existing account"
    else
        print_info "Creating admin user for cleanup..."
        curl -s -X POST "$BASE_URL/api/auth/register" \
            -H "Content-Type: application/json" \
            -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"AdminTestPass123!\", \"full_name\": \"RBAC Test Admin\"}" > /dev/null

        # Login to get token
        ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"AdminTestPass123!\"}")

        ADMIN_TOKEN=$(echo $ADMIN_LOGIN_RESPONSE | jq -r '.access_token')
        print_success "Admin user created for cleanup"
    fi

    # List of test users to cleanup
    TEST_USERS=(
        "rbac_viewer_test@example.com"
        "rbac_recruiter_test@example.com"
        "rbac_hiring_manager_test@example.com"
        "rbac_admin_test@example.com"
        "rbac_admin_cleanup@example.com"
    )

    # Note: We can't delete users directly without a delete endpoint
    # Just log that cleanup would happen here
    print_info "Test users created during testing (manual cleanup may be needed):"
    for email in "${TEST_USERS[@]}"; do
        echo "  - $email"
    done

    print_success "Cleanup complete"
}

# Check if backend is running
check_backend() {
    print_header "Checking Backend Server"

    if curl -s -f "$BASE_URL/docs" > /dev/null; then
        print_success "Backend server is running on $BASE_URL"
        return 0
    else
        print_failure "Backend server is not running on $BASE_URL"
        print_info "Please start the backend server first:"
        echo "  cd backend"
        echo "  uvicorn main:app --reload"
        exit 1
    fi
}

# Create a user and assign role (requires database access, so we'll use registration + manual role assignment)
create_user_with_role() {
    local email=$1
    local password=$2
    local full_name=$3
    local role=$4

    print_test "Creating user: $email with role: $role"

    # Register user
    REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$email\", \"password\": \"$password\", \"full_name\": \"$full_name\"}")

    REGISTER_STATUS=$(echo "$REGISTER_RESPONSE" | tail -n1)
    REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | sed '$d')

    if [[ $REGISTER_STATUS == "201" ]]; then
        print_success "User registered: $email"

        # Note: Role assignment requires direct database access or admin API
        # For this test, we'll use the default viewer role and note that
        # in production, role assignment would be done via:
        # 1. Admin API endpoint
        # 2. Direct database INSERT into roles table
        # 3. User registration with role parameter (if allowed)

        print_info "Note: Role '$role' assignment requires database access or admin API"
        print_info "User created with default 'viewer' role"

        # Login to get tokens
        LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"email\": \"$email\", \"password\": \"$password\"}")

        ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
        REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.refresh_token')

        echo "$ACCESS_TOKEN"

    else
        print_failure "Failed to register user: $email (status: $REGISTER_STATUS)"
        echo "$REGISTER_BODY"
        return 1
    fi
}

# Test endpoint access
test_endpoint_access() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local token=$4
    local expected_status=$5
    local data=$6

    print_test "$test_name"

    if [[ $method == "GET" ]]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token")
    elif [[ $method == "POST" ]]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [[ $method == "PUT" ]]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    STATUS=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [[ $STATUS == "$expected_status" ]]; then
        print_success "$test_name (status: $STATUS)"
        return 0
    else
        print_failure "$test_name (expected: $expected_status, got: $STATUS)"
        echo "Response: $BODY"
        return 1
    fi
}

# Main test execution
main() {
    print_header "RBAC Flow Test Suite"
    echo "This test suite verifies role-based access control enforcement"
    echo "across different user roles and protected endpoints."
    echo ""
    echo "Test Coverage:"
    echo "  - User creation with different roles"
    echo "  - Viewer access restrictions"
    echo "  - Recruiter access permissions"
    echo "  - Hiring Manager access permissions"
    echo "  - Admin access permissions"
    echo "  - Unauthenticated access denial"
    echo "  - Error message validation"
    echo ""

    # Check backend
    check_backend

    # Create test users
    print_header "Creating Test Users"

    # Note: In a real test environment, we would directly insert roles into database
    # For this script, we'll create users and note their default role

    print_info "Creating Viewer user..."
    VIEWER_TOKEN=$(create_user_with_role \
        "rbac_viewer_test@example.com" \
        "ViewerTestPass123!" \
        "RBAC Test Viewer" \
        "viewer")

    echo ""
    print_info "Creating Recruiter user..."
    RECRUITER_TOKEN=$(create_user_with_role \
        "rbac_recruiter_test@example.com" \
        "RecruiterTestPass123!" \
        "RBAC Test Recruiter" \
        "recruiter")

    echo ""
    print_info "Creating Hiring Manager user..."
    HM_TOKEN=$(create_user_with_role \
        "rbac_hiring_manager_test@example.com" \
        "HiringManagerTestPass123!" \
        "RBAC Test Hiring Manager" \
        "hiring_manager")

    echo ""
    print_info "Creating Admin user..."
    ADMIN_TOKEN=$(create_user_with_role \
        "rbac_admin_test@example.com" \
        "AdminTestPass123!" \
        "RBAC Test Admin" \
        "admin")

    echo ""
    read -p "Users created. Please manually assign roles in database before continuing. Press Enter to continue..."

    # Test unauthenticated access
    print_header "Test 1: Unauthenticated Access Denial"

    test_endpoint_access \
        "Unauthenticated: List candidates" \
        "GET" \
        "/api/candidates/" \
        "invalid_token" \
        "401"

    test_endpoint_access \
        "Unauthenticated: Move candidate stage" \
        "PUT" \
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage" \
        "invalid_token" \
        "401" \
        '{"stage_id": "interview"}'

    # Test viewer access
    print_header "Test 2: Viewer Role Access (Should Fail for Recruiter Endpoints)"

    test_endpoint_access \
        "Viewer: List candidates (read-only)" \
        "GET" \
        "/api/candidates/" \
        "$VIEWER_TOKEN" \
        "200"

    test_endpoint_access \
        "Viewer: Move candidate stage" \
        "PUT" \
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage" \
        "$VIEWER_TOKEN" \
        "403" \
        '{"stage_id": "interview"}'

    test_endpoint_access \
        "Viewer: Bulk move candidates" \
        "POST" \
        "/api/candidates/bulk-move" \
        "$VIEWER_TOKEN" \
        "403" \
        '{"resume_ids": ["00000000-0000-0000-0000-000000000001"], "stage_id": "interview"}'

    test_endpoint_access \
        "Viewer: Bulk action (export)" \
        "POST" \
        "/api/candidates/bulk-action" \
        "$VIEWER_TOKEN" \
        "403" \
        '{"action": "export", "resume_ids": ["00000000-0000-0000-0000-000000000001"]}'

    # Test recruiter access
    print_header "Test 3: Recruiter Role Access (Should Succeed)"

    test_endpoint_access \
        "Recruiter: List candidates (read-only)" \
        "GET" \
        "/api/candidates/" \
        "$RECRUITER_TOKEN" \
        "200"

    test_endpoint_access \
        "Recruiter: Move candidate stage" \
        "PUT" \
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage" \
        "$RECRUITER_TOKEN" \
        "404" \
        '{"stage_id": "interview"}'

    print_info "Note: 404 is expected (candidate doesn't exist), 403 would indicate authorization failure"

    test_endpoint_access \
        "Recruiter: Bulk move candidates" \
        "POST" \
        "/api/candidates/bulk-move" \
        "$RECRUITER_TOKEN" \
        "404" \
        '{"resume_ids": ["00000000-0000-0000-0000-000000000001"], "stage_id": "interview"}'

    # Test hiring manager access
    print_header "Test 4: Hiring Manager Role Access (Should Succeed)"

    test_endpoint_access \
        "Hiring Manager: List candidates (read-only)" \
        "GET" \
        "/api/candidates/" \
        "$HM_TOKEN" \
        "200"

    test_endpoint_access \
        "Hiring Manager: Move candidate stage" \
        "PUT" \
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage" \
        "$HM_TOKEN" \
        "404" \
        '{"stage_id": "interview"}"

    # Test admin access
    print_header "Test 5: Admin Role Access (Should Succeed for All)"

    test_endpoint_access \
        "Admin: List candidates (read-only)" \
        "GET" \
        "/api/candidates/" \
        "$ADMIN_TOKEN" \
        "200"

    test_endpoint_access \
        "Admin: Move candidate stage" \
        "PUT" \
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage" \
        "$ADMIN_TOKEN" \
        "404" \
        '{"stage_id": "interview"}"

    test_endpoint_access \
        "Admin: Bulk move candidates" \
        "POST" \
        "/api/candidates/bulk-move" \
        "$ADMIN_TOKEN" \
        "404" \
        '{"resume_ids": ["00000000-0000-0000-0000-000000000001"], "stage_id": "interview"}'

    # Test error messages
    print_header "Test 6: RBAC Error Message Validation"

    print_test "Checking 403 error message content..."
    RESPONSE=$(curl -s -X PUT "$BASE_URL/api/candidates/00000000-0000-0000-0000-000000000001/stage" \
        -H "Authorization: Bearer $VIEWER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"stage_id": "interview"}')

    if echo "$RESPONSE" | jq -e '.detail' > /dev/null; then
        ERROR_DETAIL=$(echo "$RESPONSE" | jq -r '.detail')
        print_success "Error response has 'detail' field: $ERROR_DETAIL"

        if echo "$ERROR_DETAIL" | grep -iq "role\|recruiter\|permission"; then
            print_success "Error message mentions role/permission requirement"
        else
            print_failure "Error message should mention role/permission requirement"
        fi
    else
        print_failure "Error response should have 'detail' field"
    fi

    # Final results
    print_header "Test Results Summary"

    echo -e "${BLUE}Total Tests:${NC} $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
    echo -e "${RED}Failed:${NC} $FAILED_TESTS"

    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "\n${GREEN}✓ All RBAC tests passed!${NC}\n"
        exit 0
    else
        echo -e "\n${RED}✗ Some RBAC tests failed${NC}\n"
        exit 1
    fi
}

# Trap to ensure cleanup runs
trap cleanup EXIT

# Run main tests
main "$@"
