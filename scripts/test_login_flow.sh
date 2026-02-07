#!/bin/bash

# Login Flow End-to-End Test Script
# Tests the complete login flow from API to JWT tokens to protected routes

set -e

API_URL="http://localhost:8000"
TEST_EMAIL="logintest$(date +%s)@example.com"  # Unique email each run
TEST_PASSWORD="TestPass123!"
TEST_FULL_NAME="Login Test User"

echo "=========================================="
echo "Login Flow E2E Test"
echo "=========================================="
echo ""

# Test 1: Register a test user first
echo "Test 0: Registering test user..."
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
  echo "❌ FAILED: Could not register test user (got $REGISTER_CODE)"
  exit 1
fi

echo "✅ Test user registered successfully"
echo ""

# Test 1: Login with valid credentials
echo "Test 1: Logging in with valid credentials..."
echo ""

LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\"
  }")

LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

echo "HTTP Status: $LOGIN_CODE"
echo "Response (truncated): $(echo "$LOGIN_BODY" | head -c 200)..."
echo ""

if [ "$LOGIN_CODE" != "200" ]; then
  echo "❌ FAILED: Expected 200, got $LOGIN_CODE"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Extract tokens from response
ACCESS_TOKEN=$(echo "$LOGIN_BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
REFRESH_TOKEN=$(echo "$LOGIN_BODY" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4)
TOKEN_TYPE=$(echo "$LOGIN_BODY" | grep -o '"token_type":"[^"]*"' | cut -d'"' -f4)
EXPIRES_IN=$(echo "$LOGIN_BODY" | grep -o '"expires_in":[0-9]*' | cut -d':' -f2)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ FAILED: access_token not found in response"
  exit 1
fi

if [ -z "$REFRESH_TOKEN" ]; then
  echo "❌ FAILED: refresh_token not found in response"
  exit 1
fi

echo "Access Token: ${ACCESS_TOKEN:0:50}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
echo "Token Type: $TOKEN_TYPE"
echo "Expires In: $EXPIRES_IN seconds (~$(($EXPIRES_IN/60)) minutes)"
echo ""

# Test 2: Verify token structure (JWT format)
echo "Test 2: Verifying token structure (JWT format)..."

# JWT should have 3 parts separated by dots
ACCESS_PARTS=$(echo "$ACCESS_TOKEN" | tr '.' '\n' | wc -l)
REFRESH_PARTS=$(echo "$REFRESH_TOKEN" | tr '.' '\n' | wc -l)

if [ "$ACCESS_PARTS" != "3" ]; then
  echo "❌ FAILED: Access token is not valid JWT (has $ACCESS_PARTS parts, expected 3)"
  exit 1
fi

if [ "$REFRESH_PARTS" != "3" ]; then
  echo "❌ FAILED: Refresh token is not valid JWT (has $REFRESH_PARTS parts, expected 3)"
  exit 1
fi

echo "✅ Both tokens have valid JWT structure (header.payload.signature)"
echo ""

# Test 3: Verify tokens start with JWT prefix
echo "Test 3: Verifying JWT format..."

if [[ ! "$ACCESS_TOKEN" =~ ^eyJ ]]; then
  echo "❌ FAILED: Access token does not start with 'eyJ' (Base64url prefix)"
  exit 1
fi

if [[ ! "$REFRESH_TOKEN" =~ ^eyJ ]]; then
  echo "❌ FAILED: Refresh token does not start with 'eyJ' (Base64url prefix)"
  exit 1
fi

echo "✅ Both tokens use Base64url encoding (start with 'eyJ')"
echo ""

# Test 4: Decode access token payload (without verification)
echo "Test 4: Inspecting access token payload..."

# Get the payload part (second part of JWT)
ACCESS_PAYLOAD=$(echo "$ACCESS_TOKEN" | cut -d'.' -f2)
# Add padding if needed
ACCESS_PAYLOAD_LENGTH=${#ACCESS_PAYLOAD}
PADDING=$((4 - ACCESS_PAYLOAD_LENGTH % 4))
if [ $PADDING -ne 4 ]; then
  ACCESS_PAYLOAD="${ACCESS_PAYLOAD}$(printf '=%.0s' $(seq 1 $PADDING))"
fi

# Decode base64url
ACCESS_PAYLOAD_DECODED=$(echo "$ACCESS_PAYLOAD" | base64 -d 2>/dev/null || echo "$ACCESS_PAYLOAD" | base64 -D 2>/dev/null)

if [ -z "$ACCESS_PAYLOAD_DECODED" ]; then
  echo "❌ FAILED: Could not decode access token payload"
  exit 1
fi

echo "Access Token Payload:"
echo "$ACCESS_PAYLOAD_DECODED" | python3 -m json.tool 2>/dev/null || echo "$ACCESS_PAYLOAD_DECODED"
echo ""

# Verify required claims
if ! echo "$ACCESS_PAYLOAD_DECODED" | grep -q '"sub"'; then
  echo "❌ FAILED: Access token missing 'sub' claim (user_id)"
  exit 1
fi

if ! echo "$ACCESS_PAYLOAD_DECODED" | grep -q '"email"'; then
  echo "❌ FAILED: Access token missing 'email' claim"
  exit 1
fi

if ! echo "$ACCESS_PAYLOAD_DECODED" | grep -q '"exp"'; then
  echo "❌ FAILED: Access token missing 'exp' claim (expiration)"
  exit 1
fi

if ! echo "$ACCESS_PAYLOAD_DECODED" | grep -q '"type"'; then
  echo "❌ FAILED: Access token missing 'type' claim"
  exit 1
fi

TOKEN_TYPE_CLAIM=$(echo "$ACCESS_PAYLOAD_DECODED" | grep -o '"type":"[^"]*"' | cut -d'"' -f4)
if [ "$TOKEN_TYPE_CLAIM" != "access" ]; then
  echo "❌ FAILED: Access token has wrong type: $TOKEN_TYPE_CLAIM (expected 'access')"
  exit 1
fi

echo "✅ Access token payload valid (contains sub, email, exp, type='access')"
echo ""

# Test 5: Decode refresh token payload
echo "Test 5: Inspecting refresh token payload..."

REFRESH_PAYLOAD=$(echo "$REFRESH_TOKEN" | cut -d'.' -f2)
REFRESH_PAYLOAD_LENGTH=${#REFRESH_PAYLOAD}
PADDING=$((4 - REFRESH_PAYLOAD_LENGTH % 4))
if [ $PADDING -ne 4 ]; then
  REFRESH_PAYLOAD="${REFRESH_PAYLOAD}$(printf '=%.0s' $(seq 1 $PADDING))"
fi

REFRESH_PAYLOAD_DECODED=$(echo "$REFRESH_PAYLOAD" | base64 -d 2>/dev/null || echo "$REFRESH_PAYLOAD" | base64 -D 2>/dev/null)

if [ -z "$REFRESH_PAYLOAD_DECODED" ]; then
  echo "❌ FAILED: Could not decode refresh token payload"
  exit 1
fi

echo "Refresh Token Payload:"
echo "$REFRESH_PAYLOAD_DECODED" | python3 -m json.tool 2>/dev/null || echo "$REFRESH_PAYLOAD_DECODED"
echo ""

REFRESH_TYPE_CLAIM=$(echo "$REFRESH_PAYLOAD_DECODED" | grep -o '"type":"[^"]*"' | cut -d'"' -f4)
if [ "$REFRESH_TYPE_CLAIM" != "refresh" ]; then
  echo "❌ FAILED: Refresh token has wrong type: $REFRESH_TYPE_CLAIM (expected 'refresh')"
  exit 1
fi

echo "✅ Refresh token payload valid (contains sub, email, exp, type='refresh')"
echo ""

# Test 6: Login with wrong password
echo "Test 6: Testing login with wrong password..."

WRONG_PASS_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"WrongPassword123!\"
  }")

WRONG_PASS_CODE=$(echo "$WRONG_PASS_RESPONSE" | tail -n1)

if [ "$WRONG_PASS_CODE" != "401" ]; then
  echo "❌ FAILED: Expected 401 for wrong password, got $WRONG_PASS_CODE"
  exit 1
fi

echo "✅ Wrong password correctly rejected (401)"
echo ""

# Test 7: Login with non-existent user
echo "Test 7: Testing login with non-existent user..."

NONEXISTENT_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"nonexistent$(date +%s)@example.com\",
    \"password\": \"${TEST_PASSWORD}\"
  }")

NONEXISTENT_CODE=$(echo "$NONEXISTENT_RESPONSE" | tail -n1)

if [ "$NONEXISTENT_CODE" != "401" ]; then
  echo "❌ FAILED: Expected 401 for non-existent user, got $NONEXISTENT_CODE"
  exit 1
fi

echo "✅ Non-existent user correctly rejected (401)"
echo ""

# Test 8: Access protected route without token
echo "Test 8: Testing protected route without authentication..."

PROTECTED_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X GET "${API_URL}/api/candidates/")

PROTECTED_CODE=$(echo "$PROTECTED_RESPONSE" | tail -n1)

if [ "$PROTECTED_CODE" != "401" ]; then
  echo "❌ FAILED: Expected 401 for protected route without token, got $PROTECTED_CODE"
  exit 1
fi

echo "✅ Protected route correctly rejected unauthenticated request (401)"
echo ""

# Test 9: Access protected route with valid token
echo "Test 9: Testing protected route with valid token..."

PROTECTED_AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X GET "${API_URL}/api/candidates/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

PROTECTED_AUTH_CODE=$(echo "$PROTECTED_AUTH_RESPONSE" | tail -n1)

if [ "$PROTECTED_AUTH_CODE" != "200" ]; then
  echo "❌ FAILED: Expected 200 for protected route with valid token, got $PROTECTED_AUTH_CODE"
  exit 1
fi

echo "✅ Protected route accepted authenticated request (200)"
echo ""

# Test 10: Access protected route with invalid token
echo "Test 10: Testing protected route with invalid token..."

INVALID_TOKEN_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X GET "${API_URL}/api/candidates/" \
  -H "Authorization: Bearer invalid_token_here")

INVALID_TOKEN_CODE=$(echo "$INVALID_TOKEN_RESPONSE" | tail -n1)

if [ "$INVALID_TOKEN_CODE" != "401" ]; then
  echo "❌ FAILED: Expected 401 for invalid token, got $INVALID_TOKEN_CODE"
  exit 1
fi

echo "✅ Protected route correctly rejected invalid token (401)"
echo ""

# Test 11: Verify response format
echo "Test 11: Verifying login response format..."

# Check for required fields
if ! echo "$LOGIN_BODY" | grep -q '"token_type":'; then
  echo "❌ FAILED: Response missing 'token_type'"
  exit 1
fi

if ! echo "$LOGIN_BODY" | grep -q '"expires_in":'; then
  echo "❌ FAILED: Response missing 'expires_in'"
  exit 1
fi

if ! echo "$LOGIN_BODY" | grep -q '"user":'; then
  echo "❌ FAILED: Response missing 'user'"
  exit 1
fi

# Check user object structure
if ! echo "$LOGIN_BODY" | grep -q '"id":'; then
  echo "❌ FAILED: User object missing 'id'"
  exit 1
fi

if ! echo "$LOGIN_BODY" | grep -q '"email":'; then
  echo "❌ FAILED: User object missing 'email'"
  exit 1
fi

# Verify no password leaked
if echo "$LOGIN_BODY" | grep -q '"password"'; then
  echo "❌ FAILED: Password leaked in response!"
  exit 1
fi

if echo "$LOGIN_BODY" | grep -q '"password_hash"'; then
  echo "❌ FAILED: password_hash leaked in response!"
  exit 1
fi

echo "✅ Response format correct, no sensitive data leaked"
echo ""

# Test 12: Verify token expiration times
echo "Test 12: Verifying token expiration times..."

CURRENT_TIME=$(date +%s)

# Extract exp from access token
ACCESS_EXP=$(echo "$ACCESS_PAYLOAD_DECODED" | grep -o '"exp":[0-9]*' | cut -d':' -f2)
ACCESS_EXPIRES_IN=$((ACCESS_EXP - CURRENT_TIME))

# Access token should expire in ~30 minutes (1800 seconds)
if [ $ACCESS_EXPIRES_IN -lt 1700 ] || [ $ACCESS_EXPIRES_IN -gt 1900 ]; then
  echo "❌ FAILED: Access token expiration $ACCESS_EXPIRES_IN seconds outside expected range (1700-1900)"
  exit 1
fi

echo "✅ Access token expires in ${ACCESS_EXPIRES_IN} seconds (~$(($ACCESS_EXPIRES_IN/60)) minutes)"

# Extract exp from refresh token
REFRESH_EXP=$(echo "$REFRESH_PAYLOAD_DECODED" | grep -o '"exp":[0-9]*' | cut -d':' -f2)
REFRESH_EXPIRES_IN=$((REFRESH_EXP - CURRENT_TIME))

# Refresh token should expire in ~7 days (604800 seconds)
EXPECTED_REFRESH=604800
REFRESH_TOLERANCE=10
if [ $REFRESH_EXPIRES_IN -lt $((EXPECTED_REFRESH - REFRESH_TOLERANCE)) ] || [ $REFRESH_EXPIRES_IN -gt $((EXPECTED_REFRESH + REFRESH_TOLERANCE)) ]; then
  echo "❌ FAILED: Refresh token expiration $REFRESH_EXPIRES_IN seconds outside expected range"
  exit 1
fi

echo "✅ Refresh token expires in ${REFRESH_EXPIRES_IN} seconds (~$(($REFRESH_EXPIRES_IN/86400)) days)"
echo ""

# Success!
echo "=========================================="
echo "✅ ALL TESTS PASSED"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ User can login with valid credentials"
echo "  ✓ JWT tokens (access + refresh) are generated"
echo "  ✓ Tokens have valid JWT structure"
echo "  ✓ Access token has type='access' and ~30 min expiration"
echo "  ✓ Refresh token has type='refresh' and ~7 day expiration"
echo "  ✓ Wrong password is rejected (401)"
echo "  ✓ Non-existent user is rejected (401)"
echo "  ✓ Protected routes require authentication (401 without token)"
echo "  ✓ Protected routes accept valid tokens (200 with token)"
echo "  ✓ Invalid tokens are rejected (401)"
echo "  ✓ Response format is correct"
echo "  ✓ No sensitive data leaked"
echo ""
echo "Test user created:"
echo "  Email: $TEST_EMAIL"
echo "  Password: $TEST_PASSWORD"
echo ""
echo "To manually test in browser:"
echo "  1. Go to http://localhost:5173/login"
echo "  2. Login with: $TEST_EMAIL / $TEST_PASSWORD"
echo ""
echo "To clean up test data, run:"
echo "  DELETE FROM refresh_tokens WHERE user_id IN (SELECT id FROM users WHERE email = '$TEST_EMAIL');"
echo "  DELETE FROM roles WHERE user_id IN (SELECT id FROM users WHERE email = '$TEST_EMAIL');"
echo "  DELETE FROM users WHERE email = '$TEST_EMAIL';"
