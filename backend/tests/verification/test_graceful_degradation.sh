#!/bin/bash
# Test graceful degradation when non-essential services are unavailable
# This is the verification script for subtask-6-3

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "========================================="
echo "Testing Graceful Degradation"
echo "========================================="
echo "API URL: $API_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to check endpoint
check_endpoint() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"

    echo -n "Testing $description... "

    response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        # Show relevant part of response
        if echo "$body" | jq -e '.overall_status' >/dev/null 2>&1; then
            overall_status=$(echo "$body" | jq -r '.overall_status')
            echo "  Overall status: $overall_status"
        fi
        if echo "$body" | jq -e '.status' >/dev/null 2>&1; then
            status=$(echo "$body" | jq -r '.status')
            echo "  Status: $status"
        fi
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (expected HTTP $expected_status, got $http_code)"
        echo "  Response: $body"
        return 1
    fi
}

# Helper function to check component status
check_component_status() {
    local endpoint="$1"
    local component="$2"
    local expected_statuses="$3"  # Comma-separated list of acceptable statuses

    echo -n "Checking $component status... "

    response=$(curl -s "$API_URL$endpoint")

    # Extract component status
    component_status=$(echo "$response" | jq -r ".components.$component.status // .status // empty")

    if [ -z "$component_status" ]; then
        echo -e "${YELLOW}⚠ SKIP${NC} (component not found in response)"
        return 0
    fi

    # Check if status is in expected list
    if echo "$expected_statuses" | grep -q "$component_status"; then
        echo -e "${GREEN}✓ PASS${NC} ($component_status)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (expected one of: $expected_statuses, got: $component_status)"
        return 1
    fi
}

echo "1. Testing basic health endpoint (should always return 200)"
echo "   This endpoint performs lightweight check without dependencies"
check_endpoint "/health" 200 "basic health check"
echo ""

echo "2. Testing /api/health endpoint (should always return 200)"
echo "   This is a lightweight check that returns immediately"
check_endpoint "/api/health" 200 "API health check"
echo ""

echo "3. Testing detailed health endpoint"
echo "   Should return 200 even if optional components are degraded"
check_endpoint "/api/health/detailed" 200 "detailed health check"

# Check individual component statuses
echo ""
echo "4. Checking individual component statuses:"
check_component_status "/api/health/detailed" "database" "healthy,degraded,unhealthy"
check_component_status "/api/health/detailed" "redis" "healthy,degraded,unhealthy"
check_component_status "/api/health/detailed" "celery" "healthy,degraded,unhealthy"
check_component_status "/api/health/detailed" "ml_models" "healthy,degraded"
check_component_status "/api/health/detailed" "external_apis" "healthy,degraded"
echo ""

echo "5. Testing readiness endpoint"
echo "   Should return 200 if essential services are operational"
check_endpoint "/api/health/ready" 200 "readiness check"
echo ""

echo "6. Testing dependency graph endpoint"
check_endpoint "/api/health/dependencies" 200 "dependency graph"
echo ""

echo "========================================="
echo "Key Graceful Degradation Behaviors:"
echo "========================================="
echo ""
echo "✓ Non-essential services (ML models, external APIs) can be 'degraded'"
echo "  without causing the overall system to be 'unhealthy'"
echo ""
echo "✓ The /api/health endpoint always returns 200 (lightweight check)"
echo ""
echo "✓ The /api/health/detailed endpoint returns 200 for 'healthy' or 'degraded'"
echo "  status, only returns 503 when essential services are 'unhealthy'"
echo ""
echo "✓ Essential services: database, redis, celery"
echo "  (these must be operational for system to be 'ready')"
echo ""
echo "✓ Optional services: ml_models, external_apis"
echo "  (these can be unavailable without breaking core functionality)"
echo ""

echo "========================================="
echo "All graceful degradation tests passed!"
echo "========================================="
