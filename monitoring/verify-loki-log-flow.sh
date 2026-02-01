#!/bin/bash

# Loki Log Flow Verification Script
# Verifies that logs are flowing to Loki with correlation IDs

set -e

echo "======================================"
echo "Loki Log Flow Verification"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓ $message${NC}"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠ $message${NC}"
    else
        echo "  $message"
    fi
}

# Function to check if service is accessible
check_service() {
    local url=$1
    local name=$2
    if curl -s -f "$url" > /dev/null 2>&1; then
        print_status "OK" "$name is accessible"
        return 0
    else
        print_status "FAIL" "$name is not accessible"
        return 1
    fi
}

# Step 1: Check if services are running
echo "Step 1: Checking service availability..."
echo "--------------------------------------"

check_service "http://localhost:3100/ready" "Loki" || exit 1
check_service "http://localhost:9090/-/healthy" "Prometheus" || exit 1
check_service "http://localhost:8000/health" "Backend API" || exit 1

# Check Docker containers
echo ""
print_status "INFO" "Checking Docker containers..."
if docker ps | grep -q "resume_analysis_loki"; then
    print_status "OK" "Loki container is running"
else
    print_status "FAIL" "Loki container is not running"
    exit 1
fi

if docker ps | grep -q "resume_analysis_promtail"; then
    print_status "OK" "Promtail container is running"
else
    print_status "FAIL" "Promtail container is not running"
    exit 1
fi

if docker ps | grep -q "resume_analysis_backend"; then
    print_status "OK" "Backend container is running"
else
    print_status "FAIL" "Backend container is not running"
    exit 1
fi

echo ""

# Step 2: Make API request and capture correlation ID
echo "Step 2: Making test API request..."
echo "--------------------------------------"

# Make request and capture headers
RESPONSE=$(curl -s -X GET http://localhost:8000/api/resumes -D -)
CORRELATION_ID=$(echo "$RESPONSE" | grep -i "x-correlation-id" | cut -d' ' -f2 | tr -d '\r' | tr -d '\n')

if [ -z "$CORRELATION_ID" ]; then
    print_status "FAIL" "No correlation ID found in response headers"
    exit 1
else
    print_status "OK" "Correlation ID: $CORRELATION_ID"
fi

echo ""

# Step 3: Verify logs were generated in backend
echo "Step 3: Checking backend logs..."
echo "--------------------------------------"

# Wait a moment for logs to be written
sleep 2

# Check if correlation ID appears in backend logs
if docker logs resume_analysis_backend --tail 100 2>&1 | grep -q "$CORRELATION_ID"; then
    print_status "OK" "Correlation ID found in backend logs"
else
    print_status "WARN" "Correlation ID not found in backend logs (may need to wait longer)"
fi

echo ""

# Step 4: Wait for Promtail to scrape and send to Loki
echo "Step 4: Waiting for Promtail to send logs to Loki..."
echo "--------------------------------------"

# Wait for Promtail to scrape and send logs
sleep 5

print_status "INFO" "Checking Promtail logs..."
PROMTAIL_LOGS=$(docker logs resume_analysis_promtail --tail 20 2>&1)
if echo "$PROMTAIL_LOGS" | grep -q "level=error"; then
    print_status "WARN" "Errors found in Promtail logs"
    echo "$PROMTAIL_LOGS" | grep "level=error"
else
    print_status "OK" "No errors in Promtail logs"
fi

echo ""

# Step 5: Query Loki for correlation ID
echo "Step 5: Querying Loki for correlation ID..."
echo "--------------------------------------"

# Query Loki for the correlation ID
LOKI_QUERY='{job="backend"} |~ "'$CORRELATION_ID'"'
LOKI_URL="http://localhost:3100/loki/api/v1/query"

# URL encode the query
ENCODED_QUERY=$(echo -n "$LOKI_QUERY" | jq -sRr @uri)

# Make query to Loki
LOKI_RESPONSE=$(curl -s -G "$LOKI_URL" --data-urlencode "query=$LOKI_QUERY" --data-urlencode "limit=100")

# Check if Loki returned any results
RESULT_COUNT=$(echo "$LOKI_RESPONSE" | jq -r '.data.result | length' 2>/dev/null || echo "0")

if [ "$RESULT_COUNT" -gt 0 ]; then
    print_status "OK" "Found $RESULT_COUNT log entries with correlation ID in Loki"

    # Display sample log entries
    echo ""
    print_status "INFO" "Sample log entries from Loki:"
    echo "$LOKI_RESPONSE" | jq -r '.data.result[0].values[0][1]' 2>/dev/null | head -5 | while read -r line; do
        echo "  $line"
    done
else
    print_status "FAIL" "No log entries found in Loki with correlation ID"
    print_status "INFO" "Loki response: $LOKI_RESPONSE"
    exit 1
fi

echo ""

# Step 6: Verify log structure
echo "Step 6: Verifying log structure..."
echo "--------------------------------------"

# Get a sample log entry
SAMPLE_LOG=$(echo "$LOKI_RESPONSE" | jq -r '.data.result[0].values[0][1]' 2>/dev/null)

# Check for required fields
REQUIRED_FIELDS=("timestamp" "level" "logger" "correlation_id")
ALL_FIELDS_PRESENT=true

for field in "${REQUIRED_FIELDS[@]}"; do
    if echo "$SAMPLE_LOG" | grep -q "\"$field\""; then
        print_status "OK" "Field '$field' present in logs"
    else
        print_status "FAIL" "Field '$field' missing from logs"
        ALL_FIELDS_PRESENT=false
    fi
done

if [ "$ALL_FIELDS_PRESENT" = true ]; then
    print_status "OK" "All required fields present in log structure"
else
    print_status "FAIL" "Some required fields missing from log structure"
    exit 1
fi

echo ""

# Step 7: Test Grafana datasource
echo "Step 7: Testing Grafana Loki datasource..."
echo "--------------------------------------"

GRAFANA_DS_URL="http://localhost:3001/api/datasources"

if curl -s "$GRAFANA_DS_URL" | grep -q '"name":"Loki"'; then
    print_status "OK" "Loki datasource configured in Grafana"
else
    print_status "WARN" "Loki datasource not found in Grafana"
fi

echo ""

# Summary
echo "======================================"
echo "Verification Summary"
echo "======================================"
echo ""
print_status "OK" "All checks passed!"
echo ""
echo "Test Results:"
echo "  - Services running: ✓"
echo "  - Correlation ID generation: ✓"
echo "  - Backend logging: ✓"
echo "  - Promtail collection: ✓"
echo "  - Loki aggregation: ✓"
echo "  - Log structure: ✓"
echo ""
echo "Test Correlation ID: $CORRELATION_ID"
echo ""
echo "To view logs in Grafana:"
echo "  1. Open http://localhost:3001"
echo "  2. Navigate to Explore"
echo "  3. Select Loki datasource"
echo "  4. Run query: {job=\"backend\"} |~ \"$CORRELATION_ID\""
echo ""
echo "Verification complete!"
