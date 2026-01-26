#!/bin/bash
# API Endpoint Testing Script
# Tests all new API endpoints from the merge
# Usage: ./test_api_endpoints.sh

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "API Endpoint Testing Script"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local expected_code="${4:-200}"

    TOTAL_COUNT=$((TOTAL_COUNT + 1))

    echo -n "Testing: $method $url ... "

    response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} ($response)"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    elif [ "$response" = "404" ]; then
        echo -e "${RED}✗ FAIL${NC} (404 Not Found)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    else
        echo -e "${YELLOW}⚠ WARN${NC} (Unexpected status: $response, expected: $expected_code)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# Function to test endpoint with JSON output
test_endpoint_json() {
    local name="$1"
    local url="$2"

    echo "Testing: $name"
    echo "URL: $url"

    response=$(curl -s -w "\n%{http_code}" "$BASE_URL$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "Response (first 200 chars):"
        echo "$body" | head -c 200
        echo ""
        echo "---"
        PASS_COUNT=$((PASS_COUNT + 1))
    elif [ "$http_code" = "404" ]; then
        echo -e "${RED}✗ FAIL${NC} (404 Not Found)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    else
        echo -e "${YELLOW}⚠ WARN${NC} (Status: $http_code)"
        echo "Response:"
        echo "$body" | head -c 200
        echo ""
        echo "---"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    echo ""
}

echo "=========================================="
echo "Health Check"
echo "=========================================="
test_endpoint "Health" "GET" "/health" "200"
echo ""

echo "=========================================="
echo "Analytics Endpoints (NEW from merge)"
echo "=========================================="
test_endpoint "Key Metrics" "GET" "/api/analytics/key-metrics" "200"
test_endpoint "Funnel" "GET" "/api/analytics/funnel" "200"
test_endpoint "Skill Demand" "GET" "/api/analytics/skill-demand" "200"
test_endpoint "Source Tracking" "GET" "/api/analytics/source-tracking" "200"
test_endpoint "Recruiter Performance" "GET" "/api/analytics/recruiter-performance" "200"
echo ""

echo "=========================================="
echo "Reports Endpoints (NEW from merge)"
echo "=========================================="
test_endpoint "List Reports" "GET" "/api/reports/" "200"
test_endpoint "Create Report" "POST" "/api/reports/" "422"  # 422 = validation error (no body)
test_endpoint "Export PDF" "POST" "/api/reports/export/pdf" "422"
test_endpoint "Export CSV" "POST" "/api/reports/export/csv" "422"
test_endpoint "Schedule Report" "POST" "/api/reports/schedule" "422"
echo ""

echo "=========================================="
echo "Other Key Endpoints"
echo "=========================================="
test_endpoint "Resumes List" "GET" "/api/resumes/" "200"
test_endpoint "Matching" "GET" "/api/matching" "200"
test_endpoint "Feedback" "GET" "/api/feedback" "200"
echo ""

echo "=========================================="
echo "Detailed JSON Response Tests"
echo "=========================================="
test_endpoint_json "Analytics Key Metrics" "/api/analytics/key-metrics"
test_endpoint_json "Reports List" "/api/reports/"
echo ""

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Total Tests: $TOTAL_COUNT"
echo -e "Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
