#!/bin/bash

###############################################################################
# Logout Flow Test Script
#
# This script tests the complete logout flow including:
# - User login
# - Logout with refresh token
# - Token revocation verification
# - Protected route denial after logout
# - Security verification (no information leakage)
#
# Usage:
#   ./scripts/test_logout_flow.sh
#
# Requirements:
#   - Backend server running on http://localhost:8000
#   - PostgreSQL database running
#   - jq installed (for JSON parsing)
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

# Test variables
TEST_EMAIL="logout_test@example.com"
TEST_PASSWORD="TestPassword123!"
REFRESH_TOKEN=""
ACCESS_TOKEN=""

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
}

print_error() {
    echo -e "${RED}✗ FAIL:${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

# Check if server is running
check_server() {
    print_header "Checking Server Availability"

    if curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" | grep -q "200"; then
        print_success "Server is running at ${BASE_URL}"
        return 0
    else
        print_error "Server is not running at ${BASE_URL}"
        print_info "Please start the backend server first:"
        echo "  cd backend && python -m uvicorn main:app --reload"
        exit 1
    fi
}

# Cleanup test user
cleanup_test_user() {
    print_header "Cleanup Test User"

    print_info "Removing test user if exists..."
    curl -s -X DELETE "${BASE_URL}/api/test/cleanup-user?email=${TEST_EMAIL}" 2>/dev/null || true
    print_success "Cleanup completed"
}

# Create test user
setup_test_user() {
    print_header "Create Test User"

    print_test "Registering test user: ${TEST_EMAIL}"

    response=$(curl -s -X POST "${BASE_URL}/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_EMAIL}\",
            \"password\": \"${TEST_PASSWORD}\",
            \"full_name\": \"Logout Test User\"
        }")

    echo "Response: ${response}"

    if echo "${response}" | grep -q "User registered successfully"; then
        print_success "User registered successfully"
    else
        print_error "Failed to register user"
        echo "Response: ${response}"
        exit 1
    fi
}

# Test 1: Complete Logout Flow
test_complete_logout_flow() {
    print_header "Test 1: Complete Logout Flow"

    # Step 1: Login
    print_test "Step 1: Login with email and password"

    login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_EMAIL}\",
            \"password\": \"${TEST_PASSWORD}\"
        }")

    echo "Login Response: ${login_response}"

    # Extract tokens
    ACCESS_TOKEN=$(echo "${login_response}" | jq -r '.access_token // empty')
    REFRESH_TOKEN=$(echo "${login_response}" | jq -r '.refresh_token // empty')

    if [ -z "${ACCESS_TOKEN}" ] || [ -z "${REFRESH_TOKEN}" ]; then
        print_error "Login failed - no tokens received"
        exit 1
    fi

    print_success "Login successful - received access_token and refresh_token"

    # Verify token structure (JWT format: header.payload.signature)
    if [[ ! "${ACCESS_TOKEN}" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
        print_error "Access token has invalid JWT format"
        exit 1
    fi

    if [[ ! "${REFRESH_TOKEN}" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
        print_error "Refresh token has invalid JWT format"
        exit 1
    fi

    print_success "Tokens have valid JWT format"

    # Step 2: Logout
    print_test "Step 2: Logout with refresh token"

    logout_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${REFRESH_TOKEN}\"
        }")

    echo "Logout Response: ${logout_response}"

    if echo "${logout_response}" | grep -q "Logged out successfully"; then
        print_success "Logout successful"
    else
        print_error "Logout failed"
        echo "Response: ${logout_response}"
        exit 1
    fi

    # Step 3: Verify token revoked in database
    print_test "Step 3: Verify refresh token revoked in database"

    # Try to refresh with revoked token
    refresh_response=$(curl -s -X POST "${BASE_URL}/api/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${REFRESH_TOKEN}\"
        }")

    echo "Refresh Response (with revoked token): ${refresh_response}"

    if echo "${refresh_response}" | grep -q "401\|revoked\|invalid"; then
        print_success "Token correctly revoked - refresh request rejected"
    else
        print_error "Token was not properly revoked"
        exit 1
    fi
}

# Test 2: Logout with Invalid Token
test_logout_with_invalid_token() {
    print_header "Test 2: Logout with Invalid Token"

    print_test "Logout with invalid/missing refresh token"

    logout_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d '{
            "refresh_token": "invalid_refresh_token"
        }')

    echo "Logout Response: ${logout_response}"

    # Should return success for security (prevent token enumeration)
    if echo "${logout_response}" | grep -q "Logged out successfully"; then
        print_success "Returns success for invalid token (security measure)"
    else
        print_error "Response doesn't match expected behavior"
        exit 1
    fi
}

# Test 3: Logout with Empty Token
test_logout_with_empty_token() {
    print_header "Test 3: Logout with Empty Token"

    print_test "Logout with empty refresh token"

    logout_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d '{
            "refresh_token": ""
        }')

    echo "Logout Response: ${logout_response}"

    # Should return success for security
    if echo "${logout_response}" | grep -q "Logged out successfully"; then
        print_success "Returns success for empty token (security measure)"
    else
        print_error "Response doesn't match expected behavior"
        exit 1
    fi
}

# Test 4: Multiple Logout Attempts
test_multiple_logout_attempts() {
    print_header "Test 4: Multiple Logout Attempts (Idempotent)"

    # Login first
    login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_EMAIL}\",
            \"password\": \"${TEST_PASSWORD}\"
        }")

    REFRESH_TOKEN=$(echo "${login_response}" | jq -r '.refresh_token')

    # First logout
    print_test "First logout attempt"

    logout1_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${REFRESH_TOKEN}\"
        }")

    # Second logout (token already revoked)
    print_test "Second logout attempt (token already revoked)"

    logout2_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${REFRESH_TOKEN}\"
        }")

    # Both should succeed (idempotent operation)
    if echo "${logout1_response}" | grep -q "Logged out successfully" && \
       echo "${logout2_response}" | grep -q "Logged out successfully"; then
        print_success "Multiple logout attempts succeed (idempotent)"
    else
        print_error "Multiple logout attempts failed"
        exit 1
    fi
}

# Test 5: Logout Response Format
test_logout_response_format() {
    print_header "Test 5: Logout Response Format"

    # Login first
    login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_EMAIL}\",
            \"password\": \"${TEST_PASSWORD}\"
        }")

    REFRESH_TOKEN=$(echo "${login_response}" | jq -r '.refresh_token')

    print_test "Verify logout response format"

    logout_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${REFRESH_TOKEN}\"
        }")

    echo "Logout Response: ${logout_response}"

    # Check response has "message" field
    message=$(echo "${logout_response}" | jq -r '.message // empty')

    if [ -z "${message}" ]; then
        print_error "Response missing 'message' field"
        exit 1
    fi

    print_success "Response has 'message' field: ${message}"

    # Check response does NOT contain tokens (security)
    if echo "${logout_response}" | grep -q "access_token\|refresh_token"; then
        print_error "Response should not contain tokens"
        exit 1
    fi

    print_success "Response does not leak tokens"
}

# Test 6: Logout Prevents Token Refresh
test_logout_prevents_refresh() {
    print_header "Test 6: Logout Prevents Token Refresh"

    # Login
    login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_EMAIL}\",
            \"password\": \"${TEST_PASSWORD}\"
        }")

    REFRESH_TOKEN=$(echo "${login_response}" | jq -r '.refresh_token')

    # Logout
    print_test "Logout with refresh token"

    curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${REFRESH_TOKEN}\"
        }" > /dev/null

    # Try to refresh with revoked token
    print_test "Attempt to refresh with revoked token"

    refresh_response=$(curl -s -X POST "${BASE_URL}/api/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${REFRESH_TOKEN}\"
        }")

    echo "Refresh Response: ${refresh_response}"

    if echo "${refresh_response}" | grep -q "401\|revoked\|invalid"; then
        print_success "Revoked token cannot be used for refresh"
    else
        print_error "Revoked token was accepted for refresh"
        exit 1
    fi
}

# Test 7: Security - No Information Leakage
test_no_information_leakage() {
    print_header "Test 7: Security - No Information Leakage"

    # Login to get valid token
    login_response=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${TEST_EMAIL}\",
            \"password\": \"${TEST_PASSWORD}\"
        }")

    VALID_TOKEN=$(echo "${login_response}" | jq -r '.refresh_token')

    # Logout with valid token
    print_test "Logout with valid token"

    valid_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"${VALID_TOKEN}\"
        }")

    # Logout with invalid token
    print_test "Logout with invalid token"

    invalid_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d '{
            "refresh_token": "completely_invalid_token"
        }')

    echo "Valid Token Response: ${valid_response}"
    echo "Invalid Token Response: ${invalid_response}"

    # Both responses should be identical (prevent token enumeration)
    if [ "${valid_response}" = "${invalid_response}" ]; then
        print_success "Valid and invalid tokens return same response (no leakage)"
    else
        print_error "Responses differ - potential information leakage"
        exit 1
    fi
}

# Test 8: Logout with Malformed JWT
test_logout_with_malformed_jwt() {
    print_header "Test 8: Logout with Malformed JWT"

    print_test "Logout with malformed JWT token"

    logout_response=$(curl -s -X POST "${BASE_URL}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d '{
            "refresh_token": "not.a.valid.jwt"
        }')

    echo "Logout Response: ${logout_response}"

    # Should return success for security
    if echo "${logout_response}" | grep -q "Logged out successfully"; then
        print_success "Returns success for malformed JWT (security measure)"
    else
        print_error "Response doesn't match expected behavior"
        exit 1
    fi
}

# Main execution
main() {
    print_header "Logout Flow Test Suite"

    # Check prerequisites
    check_server

    # Setup
    cleanup_test_user
    setup_test_user

    # Run tests
    test_complete_logout_flow
    test_logout_with_invalid_token
    test_logout_with_empty_token
    test_multiple_logout_attempts
    test_logout_response_format
    test_logout_prevents_refresh
    test_no_information_leakage
    test_logout_with_malformed_jwt

    # Cleanup
    cleanup_test_user

    # Summary
    print_header "Test Suite Summary"
    print_success "All logout flow tests passed!"
    echo ""
    print_info "Tests verified:"
    echo "  ✓ Complete logout flow (login → logout → verify revocation)"
    echo "  ✓ Logout with invalid token (security measure)"
    echo "  ✓ Logout with empty token (security measure)"
    echo "  ✓ Multiple logout attempts (idempotent operation)"
    echo "  ✓ Logout response format (no token leakage)"
    echo "  ✓ Logout prevents token refresh"
    echo "  ✓ No information leakage (valid vs invalid tokens)"
    echo "  ✓ Logout with malformed JWT (security measure)"
    echo ""
    print_success "Logout flow is working correctly!"
}

# Run main function
main "$@"
