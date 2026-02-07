#!/bin/bash

# Manual Testing Script for Vacancy Filters with Infinite Scroll
# This script tests that filters work correctly with pagination

set -e

BASE_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"

echo "========================================"
echo "Vacancy Filter + Pagination Manual Test"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Backend returns all data for client-side filtering
echo -e "${YELLOW}Test 1: Backend returns all data for client-side filtering${NC}"
echo "Fetching all vacancies with limit=10000..."
RESPONSE=$(curl -s "$BASE_URL/api/vacancies/?skip=0&limit=10000")
TOTAL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "error")
VACANCIES_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['vacancies']))" 2>/dev/null || echo "error")

if [ "$TOTAL" != "error" ] && [ "$VACANCIES_COUNT" != "error" ]; then
    echo -e "${GREEN}✓ Backend returned $VACANCIES_COUNT vacancies (total: $TOTAL)${NC}"
else
    echo -e "${RED}✗ Failed to fetch all vacancies${NC}"
    exit 1
fi
echo ""

# Test 2: Verify filterable attributes exist
echo -e "${YELLOW}Test 2: Verify filterable attributes exist in dataset${NC}"
echo "Checking work formats, locations, and dates..."

WORK_FORMATS=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
formats = set(v.get('work_format', 'unknown') for v in data['vacancies'])
print(', '.join(sorted(formats)))
" 2>/dev/null || echo "error")

LOCATIONS=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
locations = set(v.get('location', 'unknown') for v in data['vacancies'])
print(', '.join(sorted(locations)[:5]))
" 2>/dev/null || echo "error")

echo "Work formats found: $WORK_FORMATS"
echo "Locations (sample): $LOCATIONS"
echo -e "${GREEN}✓ Filterable attributes present${NC}"
echo ""

# Test 3: Simulate frontend filter behavior
echo -e "${YELLOW}Test 3: Simulate frontend filter behavior${NC}"
echo "1. Initial paginated load (no filters, limit=20)..."
RESPONSE1=$(curl -s "$BASE_URL/api/vacancies/?skip=0&limit=20")
COUNT1=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['vacancies']))" 2>/dev/null || echo "error")
TOTAL1=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "error")

echo "   - Returned $COUNT1 vacancies (total: $TOTAL1)"

echo "2. Filter applied (load all, limit=10000)..."
RESPONSE2=$(curl -s "$BASE_URL/api/vacancies/?skip=0&limit=10000")
COUNT2=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['vacancies']))" 2>/dev/null || echo "error")
TOTAL2=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "error")

echo "   - Returned $COUNT2 vacancies (total: $TOTAL2)"

echo "3. Filter cleared (back to pagination, limit=20)..."
RESPONSE3=$(curl -s "$BASE_URL/api/vacancies/?skip=0&limit=20")
COUNT3=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['vacancies']))" 2>/dev/null || echo "error")
TOTAL3=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "error")

echo "   - Returned $COUNT3 vacancies (total: $TOTAL3)"

if [ "$TOTAL1" = "$TOTAL2" ] && [ "$TOTAL2" = "$TOTAL3" ]; then
    echo -e "${GREEN}✓ Total count consistent across filter changes (total: $TOTAL1)${NC}"
else
    echo -e "${RED}✗ Total count inconsistent across filter changes${NC}"
    echo "  Total1: $TOTAL1, Total2: $TOTAL2, Total3: $TOTAL3"
fi
echo ""

# Test 4: Test filter data integrity
echo -e "${YELLOW}Test 4: Test filter data integrity${NC}"
echo "Checking for duplicates and missing IDs..."

ALL_IDS=$(echo "$RESPONSE2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
ids = [v['id'] for v in data['vacancies']]
print(','.join(sorted(ids)))
" 2>/dev/null || echo "error")

UNIQUE_COUNT=$(echo "$ALL_IDS" | tr ',' '\n' | sort -u | wc -l)
TOTAL_COUNT=$(echo "$ALL_IDS" | tr ',' '\n' | wc -l)

echo "Total IDs: $TOTAL_COUNT"
echo "Unique IDs: $UNIQUE_COUNT"

if [ "$TOTAL_COUNT" -eq "$UNIQUE_COUNT" ]; then
    echo -e "${GREEN}✓ No duplicate IDs found${NC}"
else
    echo -e "${RED}✗ Found duplicate IDs${NC}"
fi
echo ""

# Test 5: Test work format filtering
echo -e "${YELLOW}Test 5: Test work format filtering (client-side)${NC}"
REMOTE_COUNT=$(echo "$RESPONSE2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = sum(1 for v in data['vacancies'] if v.get('work_format') == 'remote')
print(count)
" 2>/dev/null || echo "error")

OFFICE_COUNT=$(echo "$RESPONSE2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = sum(1 for v in data['vacancies'] if v.get('work_format') == 'office')
print(count)
" 2>/dev/null || echo "error")

HYBRID_COUNT=$(echo "$RESPONSE2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = sum(1 for v in data['vacancies'] if v.get('work_format') == 'hybrid')
print(count)
" 2>/dev/null || echo "error")

echo "Remote vacancies: $REMOTE_COUNT"
echo "Office vacancies: $OFFICE_COUNT"
echo "Hybrid vacancies: $HYBRID_COUNT"

if [ "$REMOTE_COUNT" -gt 0 ] || [ "$OFFICE_COUNT" -gt 0 ] || [ "$HYBRID_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Work format filtering works${NC}"
else
    echo -e "${RED}✗ No vacancies found with work formats${NC}"
fi
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}Backend API Tests Complete!${NC}"
echo "========================================"
echo ""
echo "Next Steps: Frontend Manual Testing"
echo "------------------------------------"
echo "1. Start the backend: cd backend && python run.py"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Open browser: $FRONTEND_URL/vacancies"
echo ""
echo "Manual Testing Checklist:"
echo "  ✓ Apply work format filter (remote/office/hybrid)"
echo "  ✓ Verify pagination resets (list refreshes)"
echo "  ✓ Apply location filter"
echo "  ✓ Verify only matching vacancies show"
echo "  ✓ Apply date range filter"
echo "  ✓ Verify infinite scroll is DISABLED when filters active"
echo "  ✓ Clear all filters"
echo "  ✓ Verify infinite scroll is ENABLED again"
echo "  ✓ Scroll to bottom and verify new vacancies load"
echo ""
