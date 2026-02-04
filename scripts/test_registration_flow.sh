#!/bin/bash

# Registration Flow End-to-End Test Script
# Tests the complete registration flow from API to database

set -e

API_URL="http://localhost:8000"
TEST_EMAIL="testuser$(date +%s)@example.com"  # Unique email each run
TEST_PASSWORD="TestPass123!"
TEST_FULL_NAME="Test User"

echo "=========================================="
echo "Registration Flow E2E Test"
echo "=========================================="
echo ""

# Test 1: Register new user
echo "Test 1: Registering new user..."
echo "Email: $TEST_EMAIL"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\",
    \"full_name\": \"${TEST_FULL_NAME}\"
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY"
echo ""

if [ "$HTTP_CODE" != "201" ]; then
  echo "❌ FAILED: Expected 201, got $HTTP_CODE"
  exit 1
fi

echo "✅ Registration successful"
echo ""

# Extract user ID from response
USER_ID=$(echo "$BODY" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "User ID: $USER_ID"
echo ""

# Test 2: Verify password is not returned in response
echo "Test 2: Verifying password not in response..."
if echo "$BODY" | grep -q "password"; then
  echo "❌ FAILED: Password found in response"
  exit 1
fi
echo "✅ Password not exposed in response"
echo ""

# Test 3: Attempt duplicate registration
echo "Test 3: Attempting duplicate registration..."
DUPLICATE_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"${TEST_PASSWORD}\",
    \"full_name\": \"${TEST_FULL_NAME}\"
  }")

DUPLICATE_CODE=$(echo "$DUPLICATE_RESPONSE" | tail -n1)
DUPLICATE_BODY=$(echo "$DUPLICATE_RESPONSE" | head -n-1)

echo "HTTP Status: $DUPLICATE_CODE"
echo "Response: $DUPLICATE_BODY"
echo ""

if [ "$DUPLICATE_CODE" != "400" ]; then
  echo "❌ FAILED: Expected 400 for duplicate, got $DUPLICATE_CODE"
  exit 1
fi

echo "✅ Duplicate registration correctly rejected"
echo ""

# Test 4: Password validation - weak password
echo "Test 4: Testing password validation (weak password)..."
WEAK_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"weakpass$(date +%s)@example.com\",
    \"password\": \"weak\",
    \"full_name\": \"Test User\"
  }")

WEAK_CODE=$(echo "$WEAK_RESPONSE" | tail -n1)

if [ "$WEAK_CODE" != "422" ]; then
  echo "❌ FAILED: Expected 422 for weak password, got $WEAK_CODE"
  exit 1
fi

echo "✅ Weak password correctly rejected"
echo ""

# Test 5: Email validation - invalid email
echo "Test 5: Testing email validation (invalid email)..."
INVALID_EMAIL_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"notanemail\",
    \"password\": \"${TEST_PASSWORD}\",
    \"full_name\": \"Test User\"
  }")

INVALID_EMAIL_CODE=$(echo "$INVALID_EMAIL_RESPONSE" | tail -n1)

if [ "$INVALID_EMAIL_CODE" != "422" ]; then
  echo "❌ FAILED: Expected 422 for invalid email, got $INVALID_EMAIL_CODE"
  exit 1
fi

echo "✅ Invalid email correctly rejected"
echo ""

# Test 6: Login with the registered user
echo "Test 6: Testing login with registered user..."
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
  echo "❌ FAILED: Expected 200 for login, got $LOGIN_CODE"
  exit 1
fi

# Check for access_token and refresh_token in response
if ! echo "$LOGIN_BODY" | grep -q "access_token"; then
  echo "❌ FAILED: access_token not found in login response"
  exit 1
fi

if ! echo "$LOGIN_BODY" | grep -q "refresh_token"; then
  echo "❌ FAILED: refresh_token not found in login response"
  exit 1
fi

echo "✅ Login successful, tokens received"
echo ""

echo "=========================================="
echo "✅ ALL TESTS PASSED"
echo "=========================================="
echo ""
echo "Test user created:"
echo "  Email: $TEST_EMAIL"
echo "  ID: $USER_ID"
echo ""
echo "To clean up test data, run:"
echo "  DELETE FROM roles WHERE user_id = '$USER_ID';"
echo "  DELETE FROM users WHERE id = '$USER_ID';"
