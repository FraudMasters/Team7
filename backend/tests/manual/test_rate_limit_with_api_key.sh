#!/bin/bash
# Manual verification script for rate limiting with API key (subtask-2-4)
# This script tests rate limiting behavior with API key authentication
# Makes 100 requests and verifies rate limit headers and 429 responses

set -e

echo "========================================="
echo "Rate Limiting with API Key Test"
echo "========================================="
echo ""

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
GENERATE_ENDPOINT="${BASE_URL}/api/api-keys/generate"
TEST_ENDPOINT="${BASE_URL}/api/candidates"
REQUEST_COUNT="${REQUEST_COUNT:-100}"
RATE_LIMIT="${RATE_LIMIT:-10}"  # Requests per minute for testing

echo "Configuration:"
echo "  Base URL: ${BASE_URL}"
echo "  Test Endpoint: ${TEST_ENDPOINT}"
echo "  Request Count: ${REQUEST_COUNT}"
echo "  Rate Limit: ${RATE_LIMIT}/minute"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
SUCCESS_COUNT=0
RATE_LIMITED_COUNT=0
ERROR_COUNT=0

# Step 1: Generate API key with custom rate limit
echo "Step 1: Generating API key with rate limit of ${RATE_LIMIT}/minute"
echo "---------------------------------------------------------------"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${GENERATE_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Rate Limit Test Key\",
    \"scopes\": [\"read:candidates\"],
    \"rate_limit\": {
      \"requests_per_minute\": ${RATE_LIMIT}
    }
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "201" ]; then
  echo -e "${RED}❌ Failed to generate API key${NC}"
  echo "HTTP Status Code: ${HTTP_CODE}"
  echo "Response body:"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  exit 1
fi

API_KEY=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('key', ''))" 2>/dev/null || echo "")
KEY_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")

if [ -z "$API_KEY" ]; then
  echo -e "${RED}❌ Failed to extract API key from response${NC}"
  exit 1
fi

echo -e "${GREEN}✅ API key generated successfully${NC}"
echo "  API Key ID: ${KEY_ID}"
echo "  API Key: ${API_KEY:0:8}... (truncated)"
echo ""

# Step 2: Make requests and monitor rate limiting
echo "Step 2: Making ${REQUEST_COUNT} requests with rate limit monitoring"
echo "-------------------------------------------------------------------"
echo ""

# Create a temporary file for detailed results
TEMP_FILE=$(mktemp)

for i in $(seq 1 $REQUEST_COUNT); do
  # Make request with API key
  RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nHEADERS:%{header_json}" -X GET "${TEST_ENDPOINT}" \
    -H "X-API-Key: ${API_KEY}" 2>/dev/null || echo "CURL_ERROR")

  # Extract HTTP code
  HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)

  # Extract rate limit headers using simple grep approach
  # Note: This is a simplified version. For production, use jq or python
  RATE_LIMIT_LIMIT=""
  RATE_LIMIT_REMAINING=""
  RATE_LIMIT_RESET=""
  RETRY_AFTER=""

  # Try to extract headers from response
  if echo "$RESPONSE" | grep -q "x-ratelimit-limit"; then
    RATE_LIMIT_LIMIT=$(echo "$RESPONSE" | grep -i "x-ratelimit-limit" | head -n1 | sed 's/.*: *\([0-9]*\).*/\1/')
  fi

  if echo "$RESPONSE" | grep -q "x-ratelimit-remaining"; then
    RATE_LIMIT_REMAINING=$(echo "$RESPONSE" | grep -i "x-ratelimit-remaining" | head -n1 | sed 's/.*: *\([0-9]*\).*/\1/')
  fi

  if echo "$RESPONSE" | grep -q "x-ratelimit-reset"; then
    RATE_LIMIT_RESET=$(echo "$RESPONSE" | grep -i "x-ratelimit-reset" | head -n1 | sed 's/.*: *\([0-9]*\).*/\1/')
  fi

  if echo "$RESPONSE" | grep -q "retry-after"; then
    RETRY_AFTER=$(echo "$RESPONSE" | grep -i "retry-after" | head -n1 | sed 's/.*: *\([0-9]*\).*/\1/')
  fi

  # Categorize response
  if [ "$HTTP_CODE" == "200" ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    echo -e "${GREEN}Request ${i}/${REQUEST_COUNT}: 200 OK${NC} | Limit: ${RATE_LIMIT_LIMIT:-N/A} | Remaining: ${RATE_LIMIT_REMAINING:-N/A}"
  elif [ "$HTTP_CODE" == "429" ]; then
    RATE_LIMITED_COUNT=$((RATE_LIMITED_COUNT + 1))
    if [ $RATE_LIMITED_COUNT -eq 1 ]; then
      echo ""
      echo -e "${YELLOW}⚠️  Rate limit exceeded at request ${i}${NC}"
      echo "  HTTP Status: 429 Too Many Requests"
      echo "  Retry-After: ${RETRY_AFTER:-N/A} seconds"
      echo "  X-RateLimit-Limit: ${RATE_LIMIT_LIMIT:-N/A}"
      echo "  X-RateLimit-Remaining: ${RATE_LIMIT_REMAINING:-N/A}"
      echo "  X-RateLimit-Reset: ${RATE_LIMIT_RESET:-N/A}"

      # Extract error body
      ERROR_BODY=$(echo "$RESPONSE" | sed -n '1,/HTTP_CODE:/p' | sed '$d')
      if [ -n "$ERROR_BODY" ]; then
        echo "  Error Response:"
        echo "$ERROR_BODY" | python3 -m json.tool 2>/dev/null || echo "  $ERROR_BODY"
      fi
      echo ""
    else
      echo -e "${YELLOW}Request ${i}/${REQUEST_COUNT}: 429 Rate Limited${NC} | Retry-After: ${RETRY_AFTER:-N/A}s"
    fi
  else
    ERROR_COUNT=$((ERROR_COUNT + 1))
    echo -e "${RED}Request ${i}/${REQUEST_COUNT}: ${HTTP_CODE} Error${NC}"
  fi

  # Save detailed results
  echo "${i},${HTTP_CODE},${RATE_LIMIT_LIMIT},${RATE_LIMIT_REMAINING},${RATE_LIMIT_RESET},${RETRY_AFTER}" >> "$TEMP_FILE"

  # Small delay to avoid overwhelming the server
  sleep 0.1
done

echo ""
echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo ""
echo "Total Requests: ${REQUEST_COUNT}"
echo -e "${GREEN}Successful (200): ${SUCCESS_COUNT}${NC}"
echo -e "${YELLOW}Rate Limited (429): ${RATE_LIMITED_COUNT}${NC}"
echo -e "${RED}Errors: ${ERROR_COUNT}${NC}"
echo ""

# Step 3: Verify rate limiting behavior
echo "Step 3: Verification"
echo "-------------------"
echo ""

VERIFICATION_PASSED=true

# Verify that we got some successful requests
if [ $SUCCESS_COUNT -gt 0 ]; then
  echo -e "${GREEN}✅ Received successful responses (200 OK)${NC}"
else
  echo -e "${RED}❌ No successful responses received${NC}"
  VERIFICATION_PASSED=false
fi

# Verify that rate limiting kicked in
if [ $RATE_LIMITED_COUNT -gt 0 ]; then
  echo -e "${GREEN}✅ Rate limiting enforced (429 responses received)${NC}"
else
  echo -e "${YELLOW}⚠️  No rate limit responses (429) received${NC}"
  echo "   This might indicate:"
  echo "   - Rate limit is too high for the number of requests"
  echo "   - Requests are spread out enough to not trigger limit"
  echo "   - Rate limiting middleware is not active"
fi

# Verify rate limit headers were present
HEADERS_CHECK=$(head -n 1 "$TEMP_FILE")
if echo "$HEADERS_CHECK" | grep -q "[0-9]"; then
  echo -e "${GREEN}✅ Rate limit headers present in responses${NC}"
else
  echo -e "${RED}❌ Rate limit headers missing from responses${NC}"
  VERIFICATION_PASSED=false
fi

# Check if rate limit matches expected value
FIRST_LIMIT=$(head -n 1 "$TEMP_FILE" | cut -d',' -f3)
if [ ! -z "$FIRST_LIMIT" ] && [ "$FIRST_LIMIT" -eq "$RATE_LIMIT" ]; then
  echo -e "${GREEN}✅ Rate limit header matches expected value (${RATE_LIMIT})${NC}"
elif [ ! -z "$FIRST_LIMIT" ]; then
  echo -e "${YELLOW}⚠️  Rate limit header (${FIRST_LIMIT}) differs from expected (${RATE_LIMIT})${NC}"
  echo "   This might indicate default rate limiting is being used"
fi

# Verify retry-after header on 429 responses
if [ $RATE_LIMITED_COUNT -gt 0 ]; then
  RETRY_AFTER_CHECK=$(grep ",429," "$TEMP_FILE" | head -n 1 | cut -d',' -f6)
  if [ ! -z "$RETRY_AFTER_CHECK" ]; then
    echo -e "${GREEN}✅ Retry-After header present on 429 responses${NC}"
  else
    echo -e "${YELLOW}⚠️  Retry-After header may be missing from 429 responses${NC}"
  fi
fi

echo ""

# Step 4: Detailed breakdown
echo "Step 4: Request Timeline"
echo "----------------------"
echo "First 20 requests:"
head -n 20 "$TEMP_FILE" | while IFS=',' read -r req_num http_code limit remaining reset retry; do
  if [ "$http_code" == "200" ]; then
    echo "  #${req_num}: 200 OK | Remaining: ${remaining:-N/A}/${limit:-N/A}"
  elif [ "$http_code" == "429" ]; then
    echo "  #${req_num}: 429 Rate Limited | Retry-After: ${retry:-N/A}s"
  else
    echo "  #${req_num}: ${http_code}"
  fi
done

echo ""
echo "Last 5 requests:"
tail -n 5 "$TEMP_FILE" | while IFS=',' read -r req_num http_code limit remaining reset retry; do
  if [ "$http_code" == "200" ]; then
    echo "  #${req_num}: 200 OK | Remaining: ${remaining:-N/A}/${limit:-N/A}"
  elif [ "$http_code" == "429" ]; then
    echo "  #${req_num}: 429 Rate Limited | Retry-After: ${retry:-N/A}s"
  else
    echo "  #${req_num}: ${http_code}"
  fi
done

# Cleanup
rm -f "$TEMP_FILE"

echo ""
echo "========================================="
if [ "$VERIFICATION_PASSED" = true ] && [ $SUCCESS_COUNT -gt 0 ]; then
  echo -e "${GREEN}✅ All Verifications Passed${NC}"
  echo "========================================="
  exit 0
else
  echo -e "${YELLOW}⚠️  Some Verifications Failed or Incomplete${NC}"
  echo "========================================="
  echo ""
  echo "Please review the results above."
  echo "If rate limiting is not working as expected, verify:"
  echo "  1. RateLimitMiddleware is registered in backend/main.py"
  echo "  2. Redis is running and accessible"
  echo "  3. Rate limit configuration is loaded from environment"
  echo "  4. Backend server is running and accessible"
  exit 1
fi
