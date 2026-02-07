#!/bin/bash

###############################################################################
# Token Refresh Flow End-to-End Test Script
#
# This script tests the complete token refresh flow using curl commands.
# It verifies that:
# 1. User can login and receive JWT tokens (access + refresh)
# 2. Access token works for protected API calls
# 3. Access token can be refreshed using refresh token
# 4. New access token is different from original
# 5. New access token works for protected API calls
# 6. Invalid refresh tokens are rejected
# 7. Revoked refresh tokens are rejected
# 8. Token type claims are enforced (access vs refresh)
#
# Prerequisites:
# - Backend server running on http://localhost:8000
# - PostgreSQL database with auth tables created
# - curl command available
# - jq command available (for JSON parsing)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API base URL
API_BASE="http://localhost:8000"

# Test user credentials
TEST_EMAIL="token_refresh_test@example.com"
TEST_PASSWORD="RefreshTest123!"
TEST_FULL_NAME="Token Refresh Test User"

# Output functions
print_header() {
    echo ""
    echo "=============================================================================="
    echo -e "${BLUE}$1${NC}"
    echo "=============================================================================="
    echo ""
}

print_step() {
    echo -e "${YELLOW}Step $1:${NC} $2"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Cleanup function
cleanup() {
    print_header "Cleanup"
    print_info "Removing test user if exists..."

    # Try to login to get tokens (user may not exist)
    LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}") || true

    # Extract tokens if login succeeded
    REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token // empty')

    # Logout to revoke refresh token
    if [ -n "$REFRESH_TOKEN" ] && [ "$REFRESH_TOKEN" != "null" ]; then
        curl -s -X POST "${API_BASE}/api/auth/logout" \
            -H "Content-Type: application/json" \
            -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}" > /dev/null
        print_success "Logged out and revoked refresh token"
    fi

    print_success "Cleanup completed"
}

# Main test flow
main() {
    print_header "Token Refresh Flow End-to-End Test"

    # Check if server is running
    print_info "Checking if backend server is running..."
    if ! curl -s "${API_BASE}/health" > /dev/null 2>&1; then
        print_error "Backend server is not running on ${API_BASE}"
        print_info "Please start the backend server first:"
        echo "  cd backend"
        echo "  uvicorn main:app --reload"
        exit 1
    fi
    print_success "Backend server is running"

    # Cleanup from previous test runs
    cleanup

    #==========================================================================
    # Test 1: User Registration
    #==========================================================================
    print_header "Test 1: User Registration"

    print_step "1" "Registering test user..."
    REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\",\"full_name\":\"${TEST_FULL_NAME}\"}")

    REGISTER_STATUS=$(echo "$REGISTER_RESPONSE" | tail -n1)
    REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | sed '$d')

    if [ "$REGISTER_STATUS" -eq 201 ]; then
        print_success "User registered successfully (HTTP $REGISTER_STATUS)"
        echo "Response: $REGISTER_BODY"
    elif [ "$REGISTER_STATUS" -eq 400 ] && echo "$REGISTER_BODY" | grep -q "already registered"; then
        print_info "User already registered, continuing with test..."
    else
        print_error "Registration failed (HTTP $REGISTER_STATUS)"
        echo "Response: $REGISTER_BODY"
        exit 1
    fi

    #==========================================================================
    # Test 2: User Login
    #==========================================================================
    print_header "Test 2: User Login"

    print_step "1" "Logging in with test credentials..."
    LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")

    LOGIN_STATUS=$(echo "$LOGIN_RESPONSE" | tail -n1)
    LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

    if [ "$LOGIN_STATUS" -ne 200 ]; then
        print_error "Login failed (HTTP $LOGIN_STATUS)"
        echo "Response: $LOGIN_BODY"
        exit 1
    fi

    print_success "Login successful (HTTP $LOGIN_STATUS)"

    # Extract tokens
    ACCESS_TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access_token')
    REFRESH_TOKEN=$(echo "$LOGIN_BODY" | jq -r '.refresh_token')
    TOKEN_TYPE=$(echo "$LOGIN_BODY" | jq -r '.token_type')
    EXPIRES_IN=$(echo "$LOGIN_BODY" | jq -r '.expires_in')

    print_info "Access Token: ${ACCESS_TOKEN:0:50}..."
    print_info "Refresh Token: ${REFRESH_TOKEN:0:50}..."
    print_info "Token Type: $TOKEN_TYPE"
    print_info "Expires In: $EXPIRES_IN seconds"

    if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
        print_error "Access token not found in response"
        exit 1
    fi

    if [ -z "$REFRESH_TOKEN" ] || [ "$REFRESH_TOKEN" = "null" ]; then
        print_error "Refresh token not found in response"
        exit 1
    fi

    #==========================================================================
    # Test 3: Access Token Works for Protected Requests
    #==========================================================================
    print_header "Test 3: Access Token Works for Protected Requests"

    print_step "1" "Accessing protected /api/candidates/ endpoint with access token..."
    PROTECTED_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_BASE}/api/candidates/" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")

    PROTECTED_STATUS=$(echo "$PROTECTED_RESPONSE" | tail -n1)
    PROTECTED_BODY=$(echo "$PROTECTED_RESPONSE" | sed '$d')

    if [ "$PROTECTED_STATUS" -eq 200 ]; then
        print_success "Protected request successful (HTTP $PROTECTED_STATUS)"
    else
        print_error "Protected request failed (HTTP $PROTECTED_STATUS)"
        echo "Response: $PROTECTED_BODY"
        exit 1
    fi

    #==========================================================================
    # Test 4: Token Refresh
    #==========================================================================
    print_header "Test 4: Token Refresh"

    print_step "1" "Refreshing access token using refresh token..."
    REFRESH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}")

    REFRESH_STATUS=$(echo "$REFRESH_RESPONSE" | tail -n1)
    REFRESH_BODY=$(echo "$REFRESH_RESPONSE" | sed '$d')

    if [ "$REFRESH_STATUS" -ne 200 ]; then
        print_error "Token refresh failed (HTTP $REFRESH_STATUS)"
        echo "Response: $REFRESH_BODY"
        exit 1
    fi

    print_success "Token refresh successful (HTTP $REFRESH_STATUS)"

    # Extract new access token
    NEW_ACCESS_TOKEN=$(echo "$REFRESH_BODY" | jq -r '.access_token')
    NEW_TOKEN_TYPE=$(echo "$REFRESH_BODY" | jq -r '.token_type')
    NEW_EXPIRES_IN=$(echo "$REFRESH_BODY" | jq -r '.expires_in')

    print_info "New Access Token: ${NEW_ACCESS_TOKEN:0:50}..."
    print_info "Token Type: $NEW_TOKEN_TYPE"
    print_info "Expires In: $NEW_EXPIRES_IN seconds"

    # Verify refresh token is NOT in response (no rotation)
    REFRESH_TOKEN_IN_RESPONSE=$(echo "$REFRESH_BODY" | jq -r '.refresh_token // empty')
    if [ -n "$REFRESH_TOKEN_IN_RESPONSE" ]; then
        print_error "Refresh token should not be in refresh response (token rotation not implemented)"
    else
        print_success "No refresh token in response (as expected)"
    fi

    #==========================================================================
    # Test 5: New Access Token is Different
    #==========================================================================
    print_header "Test 5: New Access Token is Different"

    if [ "$ACCESS_TOKEN" != "$NEW_ACCESS_TOKEN" ]; then
        print_success "New access token is different from original"
    else
        print_error "New access token is the same as original (should be different)"
        exit 1
    fi

    #==========================================================================
    # Test 6: New Access Token Works
    #==========================================================================
    print_header "Test 6: New Access Token Works for Protected Requests"

    print_step "1" "Accessing protected endpoint with new access token..."
    NEW_PROTECTED_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_BASE}/api/candidates/" \
        -H "Authorization: Bearer ${NEW_ACCESS_TOKEN}")

    NEW_PROTECTED_STATUS=$(echo "$NEW_PROTECTED_RESPONSE" | tail -n1)
    NEW_PROTECTED_BODY=$(echo "$NEW_PROTECTED_RESPONSE" | sed '$d')

    if [ "$NEW_PROTECTED_STATUS" -eq 200 ]; then
        print_success "Protected request with new token successful (HTTP $NEW_PROTECTED_STATUS)"
    else
        print_error "Protected request with new token failed (HTTP $NEW_PROTECTED_STATUS)"
        echo "Response: $NEW_PROTECTED_BODY"
        exit 1
    fi

    #==========================================================================
    # Test 7: Multiple Token Refreshes
    #==========================================================================
    print_header "Test 7: Multiple Token Refreshes"

    print_step "1" "Refreshing token 3 times..."
    for i in 1 2 3; do
        print_step "1.${i}" "Refresh attempt $i..."
        MULTI_REFRESH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/refresh" \
            -H "Content-Type: application/json" \
            -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}")

        MULTI_REFRESH_STATUS=$(echo "$MULTI_REFRESH_RESPONSE" | tail -n1)

        if [ "$MULTI_REFRESH_STATUS" -eq 200 ]; then
            print_success "Refresh $i successful"
        else
            print_error "Refresh $i failed (HTTP $MULTI_REFRESH_STATUS)"
            exit 1
        fi
    done

    #==========================================================================
    # Test 8: Invalid Refresh Token
    #==========================================================================
    print_header "Test 8: Invalid Refresh Token Rejected"

    print_step "1" "Attempting to refresh with invalid token..."
    INVALID_REFRESH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\":\"invalid.refresh.token\"}")

    INVALID_REFRESH_STATUS=$(echo "$INVALID_REFRESH_RESPONSE" | tail -n1)
    INVALID_REFRESH_BODY=$(echo "$INVALID_REFRESH_RESPONSE" | sed '$d')

    if [ "$INVALID_REFRESH_STATUS" -eq 401 ]; then
        print_success "Invalid refresh token rejected (HTTP $INVALID_REFRESH_STATUS)"
        echo "Error: $(echo "$INVALID_REFRESH_BODY" | jq -r '.detail')"
    else
        print_error "Expected 401, got HTTP $INVALID_REFRESH_STATUS"
        exit 1
    fi

    #==========================================================================
    # Test 9: Access Token Cannot Be Used for Refresh
    #==========================================================================
    print_header "Test 9: Access Token Cannot Be Used for Refresh"

    print_step "1" "Attempting to use access token for refresh..."
    WRONG_TYPE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\":\"${NEW_ACCESS_TOKEN}\"}")

    WRONG_TYPE_STATUS=$(echo "$WRONG_TYPE_RESPONSE" | tail -n1)
    WRONG_TYPE_BODY=$(echo "$WRONG_TYPE_RESPONSE" | sed '$d')

    if [ "$WRONG_TYPE_STATUS" -eq 401 ]; then
        print_success "Access token rejected for refresh (HTTP $WRONG_TYPE_STATUS)"
        echo "Error: $(echo "$WRONG_TYPE_BODY" | jq -r '.detail')"
    else
        print_error "Expected 401, got HTTP $WRONG_TYPE_STATUS"
        exit 1
    fi

    #==========================================================================
    # Test 10: Refresh Token Cannot Access Protected Endpoints
    #==========================================================================
    print_header "Test 10: Refresh Token Cannot Access Protected Endpoints"

    print_step "1" "Attempting to access protected endpoint with refresh token..."
    REFRESH_PROTECTED_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_BASE}/api/candidates/" \
        -H "Authorization: Bearer ${REFRESH_TOKEN}")

    REFRESH_PROTECTED_STATUS=$(echo "$REFRESH_PROTECTED_RESPONSE" | tail -n1)

    if [ "$REFRESH_PROTECTED_STATUS" -eq 401 ]; then
        print_success "Refresh token rejected for protected endpoint (HTTP $REFRESH_PROTECTED_STATUS)"
    else
        print_error "Expected 401, got HTTP $REFRESH_PROTECTED_STATUS"
        exit 1
    fi

    #==========================================================================
    # Test 11: Logout Revokes Refresh Token
    #==========================================================================
    print_header "Test 11: Logout Revokes Refresh Token"

    print_step "1" "Logging out to revoke refresh token..."
    LOGOUT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}")

    LOGOUT_STATUS=$(echo "$LOGOUT_RESPONSE" | tail -n1)

    if [ "$LOGOUT_STATUS" -eq 200 ]; then
        print_success "Logout successful (HTTP $LOGOUT_STATUS)"
    else
        print_error "Logout failed (HTTP $LOGOUT_STATUS)"
        exit 1
    fi

    print_step "2" "Attempting to refresh with revoked token..."
    REVOKED_REFRESH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/api/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{\"refresh_token\":\"${REFRESH_TOKEN}\"}")

    REVOKED_REFRESH_STATUS=$(echo "$REVOKED_REFRESH_RESPONSE" | tail -n1)
    REVOKED_REFRESH_BODY=$(echo "$REVOKED_REFRESH_RESPONSE" | sed '$d')

    if [ "$REVOKED_REFRESH_STATUS" -eq 401 ]; then
        print_success "Revoked refresh token rejected (HTTP $REVOKED_REFRESH_STATUS)"
        echo "Error: $(echo "$REVOKED_REFRESH_BODY" | jq -r '.detail')"
    else
        print_error "Expected 401 for revoked token, got HTTP $REVOKED_REFRESH_STATUS"
        exit 1
    fi

    #==========================================================================
    # Summary
    #==========================================================================
    print_header "Test Summary"

    echo -e "${GREEN}All tests passed!${NC}"
    echo ""
    echo "Verified:"
    echo "  ✓ User can register and login"
    echo "  ✓ User receives access and refresh tokens"
    echo "  ✓ Access token works for protected API calls"
    echo "  ✓ Access token can be refreshed using refresh token"
    echo "  ✓ New access token is different from original"
    echo "  ✓ New access token works for protected API calls"
    echo "  ✓ Multiple refreshes work correctly"
    echo "  ✓ Invalid refresh tokens are rejected"
    echo "  ✓ Revoked refresh tokens are rejected"
    echo "  ✓ Token type claims are enforced (access vs refresh)"
    echo "  ✓ Refresh token cannot access protected endpoints"
    echo ""

    # Cleanup
    cleanup
}

# Run main function
main
