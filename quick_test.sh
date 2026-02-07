#!/bin/bash

# Quick endpoint verification script

echo "Checking backend server status..."
echo ""

# Test if server is running
SERVER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null)

if [ "$SERVER_STATUS" == "200" ]; then
    echo "✓ Backend server is running on port 8000"
else
    echo "✗ Backend server is not responding"
    echo "  Please start the server with:"
    echo "  cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

echo ""
echo "Testing candidate-source-attribution endpoint..."
echo ""

# Test basic endpoint call
echo "1. Basic endpoint test (no filters):"
RESPONSE=$(curl -s http://localhost:8000/api/analytics/candidate-source-attribution)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/analytics/candidate-source-attribution)

if [ "$HTTP_CODE" == "200" ]; then
    echo "   ✓ HTTP 200 - Endpoint accessible"

    # Check if response is valid JSON
    if echo "$RESPONSE" | jq empty 2>/dev/null; then
        echo "   ✓ Valid JSON response"

        # Extract key metrics
        TOTAL_CANDIDATES=$(echo "$RESPONSE" | jq -r '.total_candidates')
        SOURCES_COUNT=$(echo "$RESPONSE" | jq -r '.sources | length')

        echo "   Total candidates: $TOTAL_CANDIDATES"
        echo "   Sources found: $SOURCES_COUNT"

        if [ "$SOURCES_COUNT" -gt 0 ]; then
            echo ""
            echo "   Source breakdown:"
            echo "$RESPONSE" | jq -r '.sources[] | "   - \(.source): \(.candidate_count) candidates, \(.hired_count) hired (\(.conversion_rate * 100)% conversion)"'
        else
            echo "   ⚠ No sources found - this may be expected if no resume_uploaded events exist"
        fi
    else
        echo "   ✗ Invalid JSON response"
        echo "   Response: $RESPONSE"
    fi
elif [ "$HTTP_CODE" == "404" ]; then
    echo "   ✗ HTTP 404 - Endpoint not found"
    echo "   This usually means:"
    echo "   1. Server hasn't reloaded the changes yet"
    echo "   2. There's a syntax error preventing endpoint registration"
    echo ""
    echo "   To fix:"
    echo "   - Restart the backend server"
    echo "   - Check for Python syntax errors: python3 -m py_compile backend/api/analytics.py"
    echo "   - Verify models are defined before the endpoint"
else
    echo "   ✗ HTTP $HTTP_CODE - Unexpected error"
    echo "   Response: $RESPONSE"
fi

echo ""
echo "2. Date filter test:"
RESPONSE=$(curl -s "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=2024-01-01&end_date=2024-12-31")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=2024-01-01&end_date=2024-12-31")

if [ "$HTTP_CODE" == "200" ]; then
    echo "   ✓ Date filtering works (HTTP 200)"
    DATE_RANGE=$(echo "$RESPONSE" | jq -r '.date_range')
    echo "   Date range: $DATE_RANGE"
else
    echo "   ✗ Date filter failed with HTTP $HTTP_CODE"
fi

echo ""
echo "3. Invalid date test (should return 400):"
RESPONSE=$(curl -s "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=invalid-date")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=invalid-date")

if [ "$HTTP_CODE" == "400" ]; then
    echo "   ✓ Error handling works (HTTP 400)"
    ERROR_DETAIL=$(echo "$RESPONSE" | jq -r '.detail')
    echo "   Error message: $ERROR_DETAIL"
else
    echo "   ✗ Expected HTTP 400, got HTTP $HTTP_CODE"
    echo "   Response: $RESPONSE"
fi

echo ""
echo "=========================================="
echo "Quick test completed!"
echo ""
echo "For comprehensive testing, run:"
echo "  ./test_candidate_source_attribution.sh"
echo "=========================================="
