#!/bin/bash
# Manual pagination test script
# Run this after starting the backend to verify pagination works correctly

BASE_URL="http://localhost:8000/api/vacancies"

echo "========================================="
echo "Pagination Manual Verification Test"
echo "========================================="
echo ""

# Test 1: Check total count
echo "Test 1: Checking total count and first page..."
echo "GET $BASE_URL?skip=0&limit=10"
response=$(curl -s "$BASE_URL?skip=0&limit=10")
echo "$response" | grep -q '"total"'
if [ $? -eq 0 ]; then
    echo "✓ Response contains 'total' field"
else
    echo "✗ Response missing 'total' field"
    exit 1
fi

echo "$response" | grep -q '"vacancies"'
if [ $? -eq 0 ]; then
    echo "✓ Response contains 'vacancies' field"
else
    echo "✗ Response missing 'vacancies' field"
    exit 1
fi

# Extract total count
total=$(echo "$response" | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo "✓ Total vacancies: $total"
echo ""

# Test 2: Test page size
echo "Test 2: Testing page size limit..."
echo "GET $BASE_URL?skip=0&limit=20"
response=$(curl -s "$BASE_URL?skip=0&limit=20")
count=$(echo "$response" | grep -o '"id"' | wc -l)
echo "✓ Vacancies returned: $count"
if [ $count -le 20 ]; then
    echo "✓ Page size limit respected (≤20)"
else
    echo "✗ Page size limit violated (got $count, expected ≤20)"
    exit 1
fi
echo ""

# Test 3: Test skip offset
echo "Test 3: Testing skip offset (no overlap)..."
echo "GET $BASE_URL?skip=0&limit=5"
page1=$(curl -s "$BASE_URL?skip=0&limit=5")
id1=$(echo "$page1" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

echo "GET $BASE_URL?skip=5&limit=5"
page2=$(curl -s "$BASE_URL?skip=5&limit=5")
id2=$(echo "$page2" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ "$id1" != "$id2" ]; then
    echo "✓ No overlap between pages (different IDs)"
else
    echo "✗ Overlap detected between pages"
    exit 1
fi
echo ""

# Test 4: Test parameter validation
echo "Test 4: Testing parameter validation..."

echo "GET $BASE_URL?limit=1000 (should fail with 422)"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL?limit=1000")
status_code=$(echo "$response" | tail -1)
if [ "$status_code" = "422" ]; then
    echo "✓ Rejects limit > 500 (422)"
else
    echo "✗ Should reject limit > 500, got status $status_code"
fi

echo "GET $BASE_URL?skip=-10 (should fail with 422)"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL?skip=-10")
status_code=$(echo "$response" | tail -1)
if [ "$status_code" = "422" ]; then
    echo "✓ Rejects negative skip (422)"
else
    echo "✗ Should reject negative skip, got status $status_code"
fi

echo "GET $BASE_URL?limit=0 (should fail with 422)"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL?limit=0")
status_code=$(echo "$response" | tail -1)
if [ "$status_code" = "422" ]; then
    echo "✓ Rejects limit = 0 (422)"
else
    echo "✗ Should reject limit = 0, got status $status_code"
fi
echo ""

# Test 5: Scroll through all vacancies (simulate infinite scroll)
echo "Test 5: Simulating infinite scroll through all vacancies..."
skip=0
limit=20
total_fetched=0
page=0

while true; do
    response=$(curl -s "$BASE_URL?skip=$skip&limit=$limit")

    # Check if we got results
    vacancy_count=$(echo "$response" | grep -o '"id"' | wc -l)

    if [ $vacancy_count -eq 0 ]; then
        echo "Page $((page+1)): No more vacancies"
        break
    fi

    total_fetched=$((total_fetched + vacancy_count))
    page=$((page + 1))

    echo "Page $page: Fetched $vacancy_count vacancies (total: $total_fetched, skip: $skip)"

    if [ $vacancy_count -lt $limit ]; then
        echo "✓ Reached end (last page had < $limit items)"
        break
    fi

    skip=$((skip + limit))

    # Safety limit to prevent infinite loops
    if [ $page -gt 10 ]; then
        echo "Stopping at page 10 (safety limit)"
        break
    fi
done

echo ""
echo "✓ Successfully scrolled through $total_fetched vacancies across $page pages"
echo ""

# Test 6: Edge case - request beyond total
echo "Test 6: Testing edge case (skip beyond total)..."
if [ ! -z "$total" ]; then
    skip_beyond=$((total + 100))
    echo "GET $BASE_URL?skip=$skip_beyond&limit=10"
    response=$(curl -s "$BASE_URL?skip=$skip_beyond&limit=10")
    vacancy_count=$(echo "$response" | grep -o '"id"' | wc -l)

    if [ $vacancy_count -eq 0 ]; then
        echo "✓ Returns empty list when skip > total"
    else
        echo "✗ Should return empty list when skip > total"
    fi
fi
echo ""

echo "========================================="
echo "All Manual Tests Completed!"
echo "========================================="
echo ""
echo "For browser testing, open:"
echo "  - Frontend: http://localhost:5173/vacancies"
echo "  - API: $BASE_URL?skip=0&limit=20"
echo ""
echo "Verify in browser:"
echo "  1. Scroll to bottom of vacancy list"
echo "  2. Check that new vacancies load automatically"
echo "  3. Verify no errors in browser console"
echo "  4. Check that all vacancies are accessible"
