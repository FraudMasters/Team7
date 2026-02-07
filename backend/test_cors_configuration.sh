#!/bin/bash

# CORS Configuration Verification Script
# Tests that CORS middleware rejects unauthorized origins and doesn't use credentials

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend URL
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "========================================="
echo "CORS Configuration Verification Tests"
echo "========================================="
echo "Backend URL: $BACKEND_URL"
echo ""

# Test 1: Verify unauthorized origin is rejected
echo -e "${YELLOW}[Test 1]${NC} Testing unauthorized origin (http://malicious-site.com)"
echo "Expected: No Access-Control-Allow-Origin header"

RESPONSE=$(curl -s -i -H "Origin: http://malicious-site.com" \
  "$BACKEND_URL/api/resumes" 2>&1 || true)

if echo "$RESPONSE" | grep -qi "access-control-allow-origin: http://malicious-site.com"; then
  echo -e "${RED}✗ FAILED${NC}: Unauthorized origin was allowed!"
  echo "Response headers:"
  echo "$RESPONSE" | grep -i "access-control"
  exit 1
else
  echo -e "${GREEN}✓ PASSED${NC}: Unauthorized origin was rejected"
fi
echo ""

# Test 2: Verify Access-Control-Allow-Credentials is NOT present
echo -e "${YELLOW}[Test 2]${NC} Testing that allow_credentials is NOT enabled"
echo "Expected: No Access-Control-Allow-Credentials header"

if echo "$RESPONSE" | grep -qi "access-control-allow-credentials:"; then
  echo -e "${RED}✗ FAILED${NC}: Access-Control-Allow-Credentials header is present!"
  echo "Response headers:"
  echo "$RESPONSE" | grep -i "access-control"
  exit 1
else
  echo -e "${GREEN}✓ PASSED${NC}: Access-Control-Allow-Credentials is not set"
fi
echo ""

# Test 3: Test with authorized origin (should work)
echo -e "${YELLOW}[Test 3]${NC} Testing authorized origin (http://localhost:5173)"
echo "Expected: Request succeeds (may or may not have CORS headers for simple GET)"

AUTH_RESPONSE=$(curl -s -i -H "Origin: http://localhost:5173" \
  "$BACKEND_URL/health" 2>&1 || true)

HTTP_STATUS=$(echo "$AUTH_RESPONSE" | grep -i "^HTTP/" | awk '{print $2}')

if [ "$HTTP_STATUS" = "200" ]; then
  echo -e "${GREEN}✓ PASSED${NC}: Authorized origin request succeeded (HTTP $HTTP_STATUS)"
else
  echo -e "${RED}✗ FAILED${NC}: Authorized origin request failed (HTTP $HTTP_STATUS)"
  exit 1
fi
echo ""

# Test 4: Test OPTIONS preflight request for unauthorized origin
echo -e "${YELLOW}[Test 4]${NC} Testing OPTIONS preflight for unauthorized origin"
echo "Expected: No CORS headers for unauthorized origin"

PREFLIGHT_RESPONSE=$(curl -s -i -X OPTIONS \
  -H "Origin: http://evil-hacker.com" \
  -H "Access-Control-Request-Method: POST" \
  "$BACKEND_URL/api/resumes" 2>&1 || true)

if echo "$PREFLIGHT_RESPONSE" | grep -qi "access-control-allow-origin: http://evil-hacker.com"; then
  echo -e "${RED}✗ FAILED${NC}: Unauthorized origin received CORS headers in preflight!"
  echo "Response headers:"
  echo "$PREFLIGHT_RESPONSE" | grep -i "access-control"
  exit 1
else
  echo -e "${GREEN}✓ PASSED${NC}: Unauthorized origin preflight rejected"
fi
echo ""

# Test 5: Verify allow_credentials is not in preflight response
echo -e "${YELLOW}[Test 5]${NC} Testing that allow_credentials is NOT in preflight"
echo "Expected: No Access-Control-Allow-Credentials in preflight response"

if echo "$PREFLIGHT_RESPONSE" | grep -qi "access-control-allow-credentials:.*true"; then
  echo -e "${RED}✗ FAILED${NC}: Access-Control-Allow-Credentials: true found in preflight!"
  echo "Response headers:"
  echo "$PREFLIGHT_RESPONSE" | grep -i "access-control"
  exit 1
else
  echo -e "${GREEN}✓ PASSED${NC}: Access-Control-Allow-Credentials not set to true"
fi
echo ""

echo "========================================="
echo -e "${GREEN}All CORS tests passed!${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "✓ Unauthorized origins are rejected"
echo "✓ Access-Control-Allow-Credentials is not enabled"
echo "✓ Authorized origins can make requests"
echo "✓ Preflight requests are properly validated"
