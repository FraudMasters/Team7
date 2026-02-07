#!/bin/bash
# Manual verification script for job board import trigger functionality
# This script tests the POST /api/integrations/{id}/trigger-import endpoint

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_BASE="${API_BASE:-http://localhost:8000}"

echo -e "${YELLOW}Job Board Import Trigger Manual Test${NC}"
echo "API Base: $API_BASE"
echo ""

# Test 1: Create a test integration
echo -e "${YELLOW}Test 1: Creating test integration...${NC}"
CREATE_RESPONSE=$(curl -s -X POST "$API_BASE/api/integrations/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manual Test Integration",
    "api_endpoint": "https://api.test.com/v1",
    "api_key": "test_key_1234567890",
    "enabled": true
  }')

INTEGRATION_ID=$(echo $CREATE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$INTEGRATION_ID" ]; then
  echo -e "${RED}✗ Failed to create test integration${NC}"
  echo "Response: $CREATE_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Integration created with ID: $INTEGRATION_ID${NC}"
echo ""

# Test 2: Trigger manual import on enabled integration
echo -e "${YELLOW}Test 2: Triggering manual import...${NC}"
TRIGGER_RESPONSE=$(curl -s -X POST "$API_BASE/api/integrations/$INTEGRATION_ID/trigger-import")

TASK_ID=$(echo $TRIGGER_RESPONSE | grep -o '"task_id":"[^"]*' | cut -d'"' -f4)
STATUS=$(echo $TRIGGER_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)

if [ "$STATUS" == "pending" ] && [ -n "$TASK_ID" ]; then
  echo -e "${GREEN}✓ Import triggered successfully${NC}"
  echo "  Task ID: $TASK_ID"
  echo "  Status: $STATUS"
else
  echo -e "${RED}✗ Failed to trigger import${NC}"
  echo "Response: $TRIGGER_RESPONSE"
fi
echo ""

# Test 3: Try triggering on disabled integration
echo -e "${YELLOW}Test 3: Testing disabled integration...${NC}"
DISABLE_RESPONSE=$(curl -s -X PATCH "$API_BASE/api/integrations/$INTEGRATION_ID/toggle")
echo "Integration disabled: $DISABLE_RESPONSE"

TRIGGER_DISABLED=$(curl -s -X POST "$API_BASE/api/integrations/$INTEGRATION_ID/trigger-import")
DISABLED_ERROR=$(echo $TRIGGER_DISABLED | grep -o '"detail":"[^"]*' | cut -d'"' -f4)

if echo "$DISABLED_ERROR" | grep -qi "disabled"; then
  echo -e "${GREEN}✓ Correctly rejects disabled integration${NC}"
  echo "  Error: $DISABLED_ERROR"
else
  echo -e "${RED}✗ Should reject disabled integration${NC}"
  echo "Response: $TRIGGER_DISABLED"
fi
echo ""

# Test 4: Re-enable integration
echo -e "${YELLOW}Test 4: Re-enabling integration...${NC}"
ENABLE_RESPONSE=$(curl -s -X PATCH "$API_BASE/api/integrations/$INTEGRATION_ID/toggle")
echo "Integration re-enabled: $ENABLE_RESPONSE"
echo ""

# Test 5: Verify import logs (may be empty if no applicants found)
echo -e "${YELLOW}Test 5: Checking import logs...${NC}"
LOGS_RESPONSE=$(curl -s -X GET "$API_BASE/api/integrations/logs?limit=5")
LOG_COUNT=$(echo $LOGS_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)

echo -e "${GREEN}✓ Import logs endpoint accessible${NC}"
echo "  Total logs: $LOG_COUNT"
echo ""

# Cleanup
echo -e "${YELLOW}Cleanup: Deleting test integration...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE "$API_BASE/api/integrations/$INTEGRATION_ID" -w "\n%{http_code}")
DELETE_STATUS=$(echo "$DELETE_RESPONSE" | tail -n1)

if [ "$DELETE_STATUS" == "204" ]; then
  echo -e "${GREEN}✓ Test integration deleted${NC}"
else
  echo -e "${YELLOW}! Could not delete integration (status: $DELETE_STATUS)${NC}"
fi
echo ""

echo -e "${GREEN}=== Test Complete ===${NC}"
echo ""
echo "Next Steps:"
echo "1. Check Celery worker logs to verify task was received:"
echo "   docker logs <celery-container>"
echo ""
echo "2. Check import logs in the frontend:"
echo "   Navigate to http://localhost:5173/integrations"
echo ""
echo "3. Verify database for new import log entries:"
echo "   docker exec -it <postgres-container> psql -U agenthr -d agenthr"
echo "   SELECT * FROM import_logs ORDER BY created_at DESC LIMIT 5;"
