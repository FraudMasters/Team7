#!/bin/bash

# Password Reset Flow End-to-End Test Script
# Tests the complete password reset flow from request to confirmation to login verification

set -e

API_URL="http://localhost:8000"
TEST_EMAIL="resettest$(date +%s)@example.com"  # Unique email each run
TEST_PASSWORD="OldPass123!"
TEST_NEW_PASSWORD="NewPass456!"
TEST_FULL_NAME="Password Reset Test User"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Password Reset Flow E2E Test${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Test 1: Register a test user first
echo -e "${YELLOW}Test 0: Registering test user...${NC}"
echo "Email: $TEST_EMAIL"
echo ""

REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\",
    \"full_name\": \"${TEST_FULL_NAME}\"
  }")

REGISTER_CODE=$(echo "$REGISTER_RESPONSE" | tail -n1)

if [ "$REGISTER_CODE" != "201" ]; then
  echo -e "${RED}❌ FAILED: Could not register test user (got $REGISTER_CODE)${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Test user registered successfully${NC}"
echo ""

# Test 1: Request password reset with valid email
echo -e "${YELLOW}Test 1: Requesting password reset with valid email...${NC}"
echo ""

RESET_REQUEST_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/password-reset-request" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\"
  }")

RESET_REQUEST_CODE=$(echo "$RESET_REQUEST_RESPONSE" | tail -n1)
RESET_REQUEST_BODY=$(echo "$RESET_REQUEST_RESPONSE" | head -n-1)

echo "HTTP Status: $RESET_REQUEST_CODE"
echo "Response: $RESET_REQUEST_BODY"
echo ""

if [ "$RESET_REQUEST_CODE" != "200" ]; then
  echo -e "${RED}❌ FAILED: Expected 200, got $RESET_REQUEST_CODE${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Password reset request successful${NC}"
echo ""

# Test 2: Request password reset with non-existent email (should return same message)
echo -e "${YELLOW}Test 2: Requesting password reset with non-existent email...${NC}"
echo ""

RESET_REQUEST_FAKE_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/password-reset-request" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"nonexistent$(date +%s)@example.com\"
  }")

RESET_REQUEST_FAKE_CODE=$(echo "$RESET_REQUEST_FAKE_RESPONSE" | tail -n1)
RESET_REQUEST_FAKE_BODY=$(echo "$RESET_REQUEST_FAKE_RESPONSE" | head -n-1)

echo "HTTP Status: $RESET_REQUEST_FAKE_CODE"
echo "Response: $RESET_REQUEST_FAKE_BODY"
echo ""

if [ "$RESET_REQUEST_FAKE_CODE" != "200" ]; then
  echo -e "${RED}❌ FAILED: Expected 200, got $RESET_REQUEST_FAKE_CODE${NC}"
  exit 1
fi

# Verify the response is the same (to prevent email enumeration)
if [ "$RESET_REQUEST_BODY" != "$RESET_REQUEST_FAKE_BODY" ]; then
  echo -e "${RED}❌ FAILED: Responses differ for valid vs invalid email (email enumeration risk)${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Password reset request with non-existent email returns same message (prevents email enumeration)${NC}"
echo ""

# Test 3: Extract reset token from backend logs
echo -e "${YELLOW}Test 3: Extracting reset token from backend...${NC}"
echo ""
echo "Note: In production, the reset token would be sent via email."
echo "For development, we need to extract it from the database."
echo ""

# Query database for the reset token
RESET_TOKEN=$(PGPASSWORD=password psql -h localhost -U agenthr_user -d agenthr_db -t -c \
  "SELECT token FROM refresh_tokens WHERE user_id = (SELECT id FROM users WHERE email = '${TEST_EMAIL}') AND is_revoked = false ORDER BY created_at DESC LIMIT 1;" 2>/dev/null | tr -d ' ')

if [ -z "$RESET_TOKEN" ]; then
  echo -e "${RED}❌ FAILED: Could not extract reset token from database${NC}"
  echo ""
  echo "Debug query:"
  PGPASSWORD=password psql -h localhost -U agenthr_user -d agenthr_db -c \
    "SELECT id, token, expires_at, is_revoked FROM refresh_tokens WHERE user_id = (SELECT id FROM users WHERE email = '${TEST_EMAIL}');"
  exit 1
fi

echo -e "${GREEN}✅ Reset token extracted from database${NC}"
echo "Token: ${RESET_TOKEN:0:50}..."
echo ""

# Test 4: Verify reset token structure (JWT format)
echo -e "${YELLOW}Test 4: Verifying reset token structure (JWT format)...${NC}"

# JWT should have 3 parts separated by dots
TOKEN_PARTS=$(echo "$RESET_TOKEN" | tr '.' '\n' | wc -l)

if [ "$TOKEN_PARTS" != "3" ]; then
  echo -e "${RED}❌ FAILED: Reset token is not valid JWT (has $TOKEN_PARTS parts, expected 3)${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Reset token has valid JWT structure (header.payload.signature)${NC}"
echo ""

# Test 5: Decode token and verify payload
echo -e "${YELLOW}Test 5: Verifying token payload...${NC}"

# Decode JWT payload (base64url decode)
PAYLOAD=$(echo "$RESET_TOKEN" | cut -d'.' -f2 | base64 -d 2>/dev/null || echo "$RESET_TOKEN" | cut -d'.' -f2 | base64 -D 2>/dev/null)

echo "Token Payload (decoded):"
echo "$PAYLOAD" | python3 -m json.tool 2>/dev/null || echo "$PAYLOAD"
echo ""

# Verify required fields
TOKEN_TYPE=$(echo "$PAYLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin).get('type', 'NOT_FOUND'))" 2>/dev/null)
TOKEN_EXPIRATION=$(echo "$PAYLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin).get('exp', 'NOT_FOUND'))" 2>/dev/null)
TOKEN_USER_ID=$(echo "$PAYLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin).get('user_id', 'NOT_FOUND'))" 2>/dev/null)

if [ "$TOKEN_TYPE" != "refresh" ]; then
  echo -e "${RED}❌ FAILED: Token type is '$TOKEN_TYPE', expected 'refresh'${NC}"
  exit 1
fi

if [ "$TOKEN_EXPIRATION" == "NOT_FOUND" ]; then
  echo -e "${RED}❌ FAILED: Token missing expiration claim${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Token payload is valid${NC}"
echo "  - Type: $TOKEN_TYPE"
echo "  - User ID: $TOKEN_USER_ID"
echo "  - Expiration: $TOKEN_EXPIRATION"
echo ""

# Test 6: Confirm password reset with valid token
echo -e "${YELLOW}Test 6: Confirming password reset with valid token...${NC}"
echo ""

RESET_CONFIRM_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/password-reset-confirm" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"${RESET_TOKEN}\",
    \"new_password\": \"${TEST_NEW_PASSWORD}\"
  }")

RESET_CONFIRM_CODE=$(echo "$RESET_CONFIRM_RESPONSE" | tail -n1)
RESET_CONFIRM_BODY=$(echo "$RESET_CONFIRM_RESPONSE" | head -n-1)

echo "HTTP Status: $RESET_CONFIRM_CODE"
echo "Response: $RESET_CONFIRM_BODY"
echo ""

if [ "$RESET_CONFIRM_CODE" != "200" ]; then
  echo -e "${RED}❌ FAILED: Expected 200, got $RESET_CONFIRM_CODE${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Password reset confirmed successfully${NC}"
echo ""

# Test 7: Verify reset token was revoked after use
echo -e "${YELLOW}Test 7: Verifying reset token was revoked after use...${NC}"
echo ""

TOKEN_REVOKED=$(PGPASSWORD=password psql -h localhost -U agenthr_user -d agenthr_db -t -c \
  "SELECT is_revoked FROM refresh_tokens WHERE token = '${RESET_TOKEN}';" 2>/dev/null | tr -d ' ')

if [ "$TOKEN_REVOKED" != "t" ]; then
  echo -e "${RED}❌ FAILED: Reset token was not revoked after use${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Reset token was revoked after use${NC}"
echo ""

# Test 8: Try to use the same token again (should fail)
echo -e "${YELLOW}Test 8: Attempting to reuse reset token (should fail)...${NC}"
echo ""

RESET_CONFIRM_REUSE_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/password-reset-confirm" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"${RESET_TOKEN}\",
    \"new_password\": \"AnotherPass789!\"
  }")

RESET_CONFIRM_REUSE_CODE=$(echo "$RESET_CONFIRM_REUSE_RESPONSE" | tail -n1)

echo "HTTP Status: $RESET_CONFIRM_REUSE_CODE"
echo ""

if [ "$RESET_CONFIRM_REUSE_CODE" != "400" ]; then
  echo -e "${RED}❌ FAILED: Expected 400, got $RESET_CONFIRM_REUSE_CODE (token reuse should be prevented)${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Token reuse correctly prevented (400 Bad Request)${NC}"
echo ""

# Test 9: Verify all refresh tokens were revoked (security best practice)
echo -e "${YELLOW}Test 9: Verifying all refresh tokens were revoked after password reset...${NC}"
echo ""

ALL_TOKENS_COUNT=$(PGPASSWORD=password psql -h localhost -U agenthr_user -d agenthr_db -t -c \
  "SELECT COUNT(*) FROM refresh_tokens WHERE user_id = (SELECT id FROM users WHERE email = '${TEST_EMAIL}');" 2>/dev/null | tr -d ' ')

REVOKED_TOKENS_COUNT=$(PGPASSWORD=password psql -h localhost -U agenthr_user -d agenthr_db -t -c \
  "SELECT COUNT(*) FROM refresh_tokens WHERE user_id = (SELECT id FROM users WHERE email = '${TEST_EMAIL}') AND is_revoked = true;" 2>/dev/null | tr -d ' ')

echo "Total tokens: $ALL_TOKENS_COUNT"
echo "Revoked tokens: $REVOKED_TOKENS_COUNT"
echo ""

if [ "$ALL_TOKENS_COUNT" != "$REVOKED_TOKENS_COUNT" ]; then
  echo -e "${RED}❌ FAILED: Not all tokens were revoked after password reset${NC}"
  echo "This is a security risk - old sessions should be invalidated"
  exit 1
fi

echo -e "${GREEN}✅ All refresh tokens were revoked (security best practice)${NC}"
echo ""

# Test 10: Login with new password
echo -e "${YELLOW}Test 10: Logging in with new password...${NC}"
echo ""

LOGIN_NEW_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_NEW_PASSWORD}\"
  }")

LOGIN_NEW_CODE=$(echo "$LOGIN_NEW_RESPONSE" | tail -n1)
LOGIN_NEW_BODY=$(echo "$LOGIN_NEW_RESPONSE" | head -n-1)

echo "HTTP Status: $LOGIN_NEW_CODE"
echo ""

if [ "$LOGIN_NEW_CODE" != "200" ]; then
  echo -e "${RED}❌ FAILED: Could not login with new password (got $LOGIN_NEW_CODE)${NC}"
  exit 1
fi

# Extract tokens from response
NEW_ACCESS_TOKEN=$(echo "$LOGIN_NEW_BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$NEW_ACCESS_TOKEN" ]; then
  echo -e "${RED}❌ FAILED: access_token not found in response${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Login with new password successful${NC}"
echo "New Access Token: ${NEW_ACCESS_TOKEN:0:50}..."
echo ""

# Test 11: Verify old password no longer works
echo -e "${YELLOW}Test 11: Attempting to login with old password (should fail)...${NC}"
echo ""

LOGIN_OLD_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\"
  }")

LOGIN_OLD_CODE=$(echo "$LOGIN_OLD_RESPONSE" | tail -n1)

echo "HTTP Status: $LOGIN_OLD_CODE"
echo ""

if [ "$LOGIN_OLD_CODE" != "401" ]; then
  echo -e "${RED}❌ FAILED: Expected 401, got $LOGIN_OLD_CODE (old password should not work)${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Old password correctly rejected (401 Unauthorized)${NC}"
echo ""

# Test 12: Confirm password reset with invalid token
echo -e "${YELLOW}Test 12: Attempting password reset with invalid token (should fail)...${NC}"
echo ""

RESET_CONFIRM_INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/password-reset-confirm" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"invalid.token.here\",
    \"new_password\": \"InvalidPass123!\"
  }")

RESET_CONFIRM_INVALID_CODE=$(echo "$RESET_CONFIRM_INVALID_RESPONSE" | tail -n1)

echo "HTTP Status: $RESET_CONFIRM_INVALID_CODE"
echo ""

if [ "$RESET_CONFIRM_INVALID_CODE" != "400" ]; then
  echo -e "${RED}❌ FAILED: Expected 400, got $RESET_CONFIRM_INVALID_CODE${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Invalid token correctly rejected (400 Bad Request)${NC}"
echo ""

# Test 13: Confirm password reset with weak password
echo -e "${YELLOW}Test 13: Attempting password reset with weak password (should fail)...${NC}"
echo ""

# Generate a new reset token for this test
curl -s -X POST "${API_URL}/api/auth/password-reset-request" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${TEST_EMAIL}\"}" > /dev/null

sleep 1

NEW_RESET_TOKEN=$(PGPASSWORD=password psql -h localhost -U agenthr_user -d agenthr_db -t -c \
  "SELECT token FROM refresh_tokens WHERE user_id = (SELECT id FROM users WHERE email = '${TEST_EMAIL}') AND is_revoked = false ORDER BY created_at DESC LIMIT 1;" 2>/dev/null | tr -d ' ')

RESET_WEAK_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/password-reset-confirm" \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"${NEW_RESET_TOKEN}\",
    \"new_password\": \"weak\"
  }")

RESET_WEAK_CODE=$(echo "$RESET_WEAK_RESPONSE" | tail -n1)

echo "HTTP Status: $RESET_WEAK_CODE"
echo ""

if [ "$RESET_WEAK_CODE" != "400" ]; then
  echo -e "${RED}❌ FAILED: Expected 400, got $RESET_WEAK_CODE (weak password should be rejected)${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Weak password correctly rejected (400 Bad Request)${NC}"
echo ""

# Summary
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}All Password Reset Flow Tests Passed!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "Summary:"
echo "  ✅ Password reset request with valid email"
echo "  ✅ Password reset request with non-existent email (prevents enumeration)"
echo "  ✅ Reset token has valid JWT structure"
echo "  ✅ Token payload contains required claims"
echo "  ✅ Password reset confirmed with valid token"
echo "  ✅ Reset token revoked after use"
echo "  ✅ Token reuse correctly prevented"
echo "  ✅ All refresh tokens revoked after password reset"
echo "  ✅ Login successful with new password"
echo "  ✅ Old password no longer works"
echo "  ✅ Invalid token rejected"
echo "  ✅ Weak password rejected"
echo ""
echo -e "${YELLOW}Cleanup SQL:${NC}"
echo "DELETE FROM roles WHERE user_id = (SELECT id FROM users WHERE email = '${TEST_EMAIL}');"
echo "DELETE FROM refresh_tokens WHERE user_id = (SELECT id FROM users WHERE email = '${TEST_EMAIL}');"
echo "DELETE FROM users WHERE email = '${TEST_EMAIL}';"
echo ""
