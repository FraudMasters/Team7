#!/bin/bash
# Verification script for audit log anonymization endpoint

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Testing Audit Log Anonymization Endpoint"
echo "=========================================="

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}Backend server is not running on http://localhost:8000${NC}"
    echo "Please start the backend server first:"
    echo "  cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo -e "${GREEN}Backend server is running${NC}"

# Test 1: Test with invalid UUID format
echo ""
echo "Test 1: Invalid UUID format (should return 400)"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  http://localhost:8000/api/audit-logs/anonymize/invalid-uuid \
  -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid UUID (HTTP 400)${NC}"
else
    echo -e "${RED}✗ Expected HTTP 400, got HTTP $HTTP_CODE${NC}"
    echo "Response: $BODY"
fi

# Test 2: Test with valid UUID (no logs case)
echo ""
echo "Test 2: Valid UUID with no logs (should return 200 with count 0)"
TEST_UUID="00000000-0000-0000-0000-000000000000"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  http://localhost:8000/api/audit-logs/anonymize/$TEST_UUID \
  -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Request successful (HTTP 200)${NC}"
    echo "Response: $BODY"
else
    echo -e "${RED}✗ Expected HTTP 200, got HTTP $HTTP_CODE${NC}"
    echo "Response: $BODY"
fi

# Test 3: Check response structure
echo ""
echo "Test 3: Validating response structure"
if echo "$BODY" | grep -q "anonymized_count" && echo "$BODY" | grep -q "message"; then
    echo -e "${GREEN}✓ Response contains required fields (anonymized_count, message)${NC}"
else
    echo -e "${RED}✗ Response missing required fields${NC}"
    echo "Response: $BODY"
fi

echo ""
echo "=========================================="
echo "Verification complete"
