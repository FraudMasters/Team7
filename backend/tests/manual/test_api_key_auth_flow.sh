#!/bin/bash
# Manual verification script for API key authentication flow (subtask-2-3)
# This script tests the complete API key authentication flow

set -e

echo "========================================="
echo "API Key Authentication Flow Test"
echo "========================================="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_ENDPOINT="${BASE_URL}/api/api-keys/generate"

echo "Testing endpoint: ${API_ENDPOINT}"
echo ""

# Test 1: Generate API key without authentication (should work - this is the generation endpoint)
echo "Test 1: Generate API key"
echo "------------------------"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Key",
    "scopes": ["read:candidates"]
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status Code: ${HTTP_CODE}"

if [ "$HTTP_CODE" == "201" ]; then
  echo "✅ Test 1 PASSED: API key created successfully"
  echo "Response body:"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

  # Extract the API key for further tests
  API_KEY=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('key', ''))" 2>/dev/null || echo "")

  if [ -n "$API_KEY" ]; then
    echo ""
    echo "Generated API Key: ${API_KEY}"

    # Test 2: Use the API key to authenticate
    echo ""
    echo "Test 2: Authenticate with generated API key"
    echo "-------------------------------------------"

    # Test with a protected endpoint (e.g., listing API keys)
    LIST_ENDPOINT="${BASE_URL}/api/api-keys"
    LIST_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${LIST_ENDPOINT}" \
      -H "X-API-Key: ${API_KEY}")

    LIST_HTTP_CODE=$(echo "$LIST_RESPONSE" | tail -n1)
    LIST_BODY=$(echo "$LIST_RESPONSE" | sed '$d')

    echo "HTTP Status Code: ${LIST_HTTP_CODE}"

    if [ "$LIST_HTTP_CODE" == "200" ]; then
      echo "✅ Test 2 PASSED: Authentication with API key successful"
      echo "Response body:"
      echo "$LIST_BODY" | python3 -m json.tool 2>/dev/null || echo "$LIST_BODY"
    else
      echo "❌ Test 2 FAILED: Expected 200, got ${LIST_HTTP_CODE}"
      echo "Response body:"
      echo "$LIST_BODY"
      exit 1
    fi

    # Test 3: Test with invalid API key
    echo ""
    echo "Test 3: Authenticate with invalid API key"
    echo "-----------------------------------------"

    INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${LIST_ENDPOINT}" \
      -H "X-API-Key: invalid_key_12345")

    INVALID_HTTP_CODE=$(echo "$INVALID_RESPONSE" | tail -n1)
    INVALID_BODY=$(echo "$INVALID_RESPONSE" | sed '$d')

    echo "HTTP Status Code: ${INVALID_HTTP_CODE}"

    if [ "$INVALID_HTTP_CODE" == "401" ] || [ "$INVALID_HTTP_CODE" == "403" ]; then
      echo "✅ Test 3 PASSED: Invalid API key rejected with ${INVALID_HTTP_CODE}"
      echo "Response body:"
      echo "$INVALID_BODY" | python3 -m json.tool 2>/dev/null || echo "$INVALID_BODY"
    else
      echo "❌ Test 3 FAILED: Expected 401 or 403, got ${INVALID_HTTP_CODE}"
      echo "Response body:"
      echo "$INVALID_BODY"
      exit 1
    fi

    # Test 4: Test without API key header
    echo ""
    echo "Test 4: Request without API key header"
    echo "--------------------------------------"

    NO_KEY_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${LIST_ENDPOINT}")

    NO_KEY_HTTP_CODE=$(echo "$NO_KEY_RESPONSE" | tail -n1)
    NO_KEY_BODY=$(echo "$NO_KEY_RESPONSE" | sed '$d')

    echo "HTTP Status Code: ${NO_KEY_HTTP_CODE}"

    # This might return 401 (if auth is required) or 200 (if endpoint allows both)
    echo "Response body:"
    echo "$NO_KEY_BODY" | python3 -m json.tool 2>/dev/null || echo "$NO_KEY_BODY"
    echo "ℹ️  Test 4 INFO: Status ${NO_KEY_HTTP_CODE} (may vary based on endpoint configuration)"
  fi
else
  echo "❌ Test 1 FAILED: Expected 201, got ${HTTP_CODE}"
  echo "Response body:"
  echo "$BODY"
  exit 1
fi

echo ""
echo "========================================="
echo "All API Key Authentication Tests Complete"
echo "========================================="
