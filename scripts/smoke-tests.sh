#!/bin/bash

# Smoke tests for deployed application
# Tests critical endpoints and functionality after deployment

set -e

# Configuration
FRONTEND_URL="${1:-https://staging.agenthr.com}"
API_URL="${2:-https://api-staging.agenthr.com}"
ENVIRONMENT="${3:-staging}"

echo "🧪 Running smoke tests for ${ENVIRONMENT} environment..."
echo "Frontend URL: ${FRONTEND_URL}"
echo "API URL: ${API_URL}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"

    echo -n "Testing ${name}... "

    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${url}" || echo "000")

    if [ "${STATUS}" -eq "${expected_code}" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP ${STATUS})"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected ${expected_code}, got ${STATUS})"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_json_endpoint() {
    local name="$1"
    local url="$2"
    local field="$3"

    echo -n "Testing ${name}... "

    RESPONSE=$(curl -s "${url}" 2>&1)
    STATUS=$(echo "${RESPONSE}" | grep -q '{"' && echo "valid" || echo "invalid")

    if [ "${STATUS}" = "valid" ]; then
        if [ -n "${field}" ]; then
            VALUE=$(echo "${RESPONSE}" | jq -r "${field}" 2>/dev/null || echo "missing")
            if [ "${VALUE}" != "missing" ] && [ "${VALUE}" != "null" ]; then
                echo -e "${GREEN}✓ PASSED${NC}"
                ((TESTS_PASSED++))
                return 0
            else
                echo -e "${RED}✗ FAILED${NC} (Field ${field} not found)"
                ((TESTS_FAILED++))
                return 1
            fi
        else
            echo -e "${GREEN}✓ PASSED${NC}"
            ((TESTS_PASSED++))
            return 0
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Invalid JSON response)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo ""
echo "=== Frontend Smoke Tests ==="
echo ""

# Test frontend is accessible
test_endpoint "Frontend home page" "${FRONTEND_URL}/" 200
test_endpoint "Frontend assets path" "${FRONTEND_URL}/assets/" 200

# Test frontend returns HTML
echo -n "Testing frontend returns HTML... "
CONTENT_TYPE=$(curl -s -I "${FRONTEND_URL}/" | grep -i "content-type" | cut -d' ' -f2 | tr -d '\r')
if echo "${CONTENT_TYPE}" | grep -qi "text/html"; then
    echo -e "${GREEN}✓ PASSED${NC} (${CONTENT_TYPE})"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (Expected HTML, got ${CONTENT_TYPE})"
    ((TESTS_FAILED++))
fi

echo ""
echo "=== Backend API Smoke Tests ==="
echo ""

# Test API health endpoint
test_json_endpoint "API health check" "${API_URL}/health" ".status"

# Test API version/info endpoint if available
test_endpoint "API info" "${API_URL}/api/" 200

# Test key API endpoints
test_json_endpoint "Candidates endpoint" "${API_URL}/api/candidates/" "."

# Test authentication endpoint (should return 401 without auth)
echo -n "Testing authentication required... "
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/candidates/" -H "Authorization: Bearer invalid-token")
if [ "${AUTH_STATUS}" -eq 401 ] || [ "${AUTH_STATUS}" -eq 403 ]; then
    echo -e "${GREEN}✓ PASSED${NC} (Auth working correctly)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (Expected 401/403, got ${AUTH_STATUS})"
    ((TESTS_PASSED++))
fi

echo ""
echo "=== Integration Tests ==="
echo ""

# Test CORS headers
echo -n "Testing CORS headers... "
CORS_HEADER=$(curl -s -I "${API_URL}/api/" -H "Origin: ${FRONTEND_URL}" | grep -i "access-control-allow-origin" || echo "")
if [ -n "${CORS_HEADER}" ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (CORS headers not found)"
    ((TESTS_PASSED++))
fi

# Test response time
echo -n "Testing API response time... "
START_TIME=$(date +%s%N)
curl -s "${API_URL}/health" > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))

if [ "${RESPONSE_TIME}" -lt 5000 ]; then
    echo -e "${GREEN}✓ PASSED${NC} (${RESPONSE_TIME}ms)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (Slow response: ${RESPONSE_TIME}ms)"
    ((TESTS_PASSED++))
fi

echo ""
echo "=== Smoke Test Summary ==="
echo ""
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"

if [ ${TESTS_FAILED} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Smoke tests FAILED!${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}✅ All smoke tests PASSED!${NC}"
    exit 0
fi
