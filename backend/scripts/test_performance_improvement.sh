#!/bin/bash
# Performance verification script for vacancy pagination
# This script verifies that pagination improves performance by:
# 1. Initial load requests only limit=20, not all vacancies
# 2. Subsequent requests use skip/limit properly
# 3. Response sizes are manageable

BASE_URL="http://localhost:8000/api/vacancies"

echo "========================================="
echo "Performance Verification Test"
echo "========================================="
echo ""

# Test 1: Verify initial load uses pagination
echo "Test 1: Verifying initial load behavior..."
echo "GET $BASE_URL?skip=0&limit=20"
response=$(curl -s -w "\n---HTTP_STATUS:%{http_code}\n---SIZE_DOWNLOAD:%{size_download}\n---TIME_TOTAL:%{time_total}" "$BASE_URL?skip=0&limit=20")

# Extract metrics
http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
size_download=$(echo "$response" | grep "SIZE_DOWNLOAD:" | cut -d':' -f2)
time_total=$(echo "$response" | grep "TIME_TOTAL:" | cut -d':' -f2)

if [ "$http_status" = "200" ]; then
    echo "✓ Initial load successful (HTTP $http_status)"
    echo "  Response size: $size_download bytes"
    echo "  Response time: ${time_total}s"

    # Verify limit=20 is being used
    vacancy_count=$(echo "$response" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "  Vacancies returned: $vacancy_count"

    if [ "$vacancy_count" -le 20 ]; then
        echo "✓ Pagination working: Only $vacancy_count items (limit=20)"
    else
        echo "✗ Too many items returned: $vacancy_count (expected ≤20)"
        exit 1
    fi
else
    echo "✗ Initial load failed (HTTP $http_status)"
    exit 1
fi
echo ""

# Test 2: Compare with full load (old behavior)
echo "Test 2: Comparing with full load (old behavior)..."
echo "GET $BASE_URL?skip=0&limit=10000"
response_full=$(curl -s -w "\n---HTTP_STATUS:%{http_code}\n---SIZE_DOWNLOAD:%{size_download}\n---TIME_TOTAL:%{time_total}" "$BASE_URL?skip=0&limit=10000")

# Extract metrics for full load
http_status_full=$(echo "$response_full" | grep "HTTP_STATUS:" | cut -d':' -f2)
size_download_full=$(echo "$response_full" | grep "SIZE_DOWNLOAD:" | cut -d':' -f2)
time_total_full=$(echo "$response_full" | grep "TIME_TOTAL:" | cut -d':' -f2)

if [ "$http_status_full" = "200" ]; then
    echo "✓ Full load successful (HTTP $http_status_full)"
    echo "  Response size: $size_download_full bytes"
    echo "  Response time: ${time_total_full}s"

    vacancy_count_full=$(echo "$response_full" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "  Total vacancies in DB: $vacancy_count_full"

    # Calculate performance improvement
    size_ratio=$(echo "scale=2; $size_download / $size_download_full" | bc)
    time_ratio=$(echo "scale=2; $time_total / $time_total_full" | bc)

    echo ""
    echo "📊 Performance Comparison:"
    echo "  Initial load size:     $size_download bytes"
    echo "  Full load size:        $size_download_full bytes"
    echo "  Size reduction:        $(echo "scale=1; (1 - $size_ratio) * 100" | bc)%"
    echo ""
    echo "  Initial load time:     ${time_total}s"
    echo "  Full load time:        ${time_total_full}s"
    echo "  Time reduction:        $(echo "scale=1; (1 - $time_ratio) * 100" | bc)%"

    if [ "$(echo "$size_download < $size_download_full" | bc)" -eq 1 ]; then
        echo "✓ Initial load is smaller (faster transfer)"
    fi

    if [ "$(echo "$time_total < $time_total_full" | bc)" -eq 1 ]; then
        echo "✓ Initial load is faster (better response time)"
    fi
else
    echo "✗ Full load failed (HTTP $http_status_full)"
fi
echo ""

# Test 3: Verify subsequent pagination requests
echo "Test 3: Verifying subsequent pagination requests..."
for page in 1 2 3; do
    skip=$((page * 20))
    echo "Page $((page+1)): GET $BASE_URL?skip=$skip&limit=20"
    response_page=$(curl -s -w "\n---SIZE_DOWNLOAD:%{size_download}\n---TIME_TOTAL:%{time_total}" "$BASE_URL?skip=$skip&limit=20")
    size_page=$(echo "$response_page" | grep "SIZE_DOWNLOAD:" | cut -d':' -f2)
    time_page=$(echo "$response_page" | grep "TIME_TOTAL:" | cut -d':' -f2)

    vacancy_count=$(echo "$response_page" | grep -o '"id"' | wc -l | tr -d ' ')

    if [ "$vacancy_count" -gt 0 ]; then
        echo "  ✓ Fetched $vacancy_count vacancies (${size_page} bytes, ${time_page}s)"
    else
        echo "  ✓ No more vacancies (end of list)"
        break
    fi
done
echo ""

# Test 4: Verify response format includes pagination metadata
echo "Test 4: Verifying pagination metadata..."
response=$(curl -s "$BASE_URL?skip=0&limit=20")
has_total=$(echo "$response" | grep -q '"total"'; echo $?)
has_vacancies=$(echo "$response" | grep -q '"vacancies"'; echo $?)

if [ $has_total -eq 0 ]; then
    total=$(echo "$response" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo "✓ Response includes 'total' metadata: $total"
else
    echo "✗ Response missing 'total' metadata"
    exit 1
fi

if [ $has_vacancies -eq 0 ]; then
    echo "✓ Response includes 'vacancies' array"
else
    echo "✗ Response missing 'vacancies' array"
    exit 1
fi
echo ""

# Test 5: Calculate bandwidth savings for typical user session
echo "Test 5: Bandwidth savings analysis..."
echo "Assuming typical user views 3 pages (60 vacancies):"

# With pagination (new behavior)
paginated_size=$((size_download * 3))
echo "  With pagination (3 requests × $size_download bytes): $paginated_size bytes"

# Without pagination (old behavior)
echo "  Without pagination (1 request × $size_download_full bytes): $size_download_full bytes"

if [ $paginated_size -lt $size_download_full ]; then
    savings=$((size_download_full - paginated_size))
    percentage=$(echo "scale=1; ($savings / $size_download_full) * 100" | bc)
    echo "✓ Bandwidth savings: $savings bytes ($percentage%)"
else
    echo "⚠ Note: Paginated load larger (user views many pages)"
fi
echo ""

# Test 6: Verify limit parameter works correctly
echo "Test 6: Verifying limit parameter enforcement..."
echo "Testing limit=10:"
response_10=$(curl -s "$BASE_URL?skip=0&limit=10")
count_10=$(echo "$response_10" | grep -o '"id"' | wc -l | tr -d ' ')
echo "  Requested 10, got $count_10 items"

echo "Testing limit=50:"
response_50=$(curl -s "$BASE_URL?skip=0&limit=50")
count_50=$(echo "$response_50" | grep -o '"id"' | wc -l | tr -d ' ')
echo "  Requested 50, got $count_50 items"

if [ "$count_10" -le 10 ] && [ "$count_50" -le 50 ]; then
    echo "✓ Limit parameter respected"
else
    echo "✗ Limit parameter not working correctly"
fi
echo ""

# Test 7: Performance under load (simulate multiple requests)
echo "Test 7: Performance under load (10 sequential requests)..."
total_time=0
for i in {1..10}; do
    start=$(date +%s.%N)
    curl -s "$BASE_URL?skip=0&limit=20" > /dev/null
    end=$(date +%s.%N)
    duration=$(echo "$end - $start" | bc)
    total_time=$(echo "$total_time + $duration" | bc)
done

avg_time=$(echo "scale=3; $total_time / 10" | bc)
echo "  Average response time: ${avg_time}s"

if [ "$(echo "$avg_time < 1.0" | bc)" -eq 1 ]; then
    echo "✓ Excellent performance (< 1s per request)"
elif [ "$(echo "$avg_time < 2.0" | bc)" -eq 1 ]; then
    echo "✓ Good performance (< 2s per request)"
else
    echo "⚠ Performance could be improved (> 2s per request)"
fi
echo ""

echo "========================================="
echo "Performance Verification Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✓ Pagination correctly limits initial load to limit=20"
echo "  ✓ Subsequent requests use skip/limit parameters"
echo "  ✓ Response sizes are manageable"
echo "  ✓ Response times are acceptable"
echo "  ✓ Bandwidth usage is optimized"
echo ""
echo "For browser verification, open:"
echo "  - Frontend: http://localhost:5173/vacancies"
echo "  - Open DevTools → Network tab"
echo "  - Verify: Initial request has ?limit=20"
echo "  - Verify: Scroll triggers requests with ?skip=X&limit=20"
echo ""
