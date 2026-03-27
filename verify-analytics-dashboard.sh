#!/bin/bash

# Analytics Dashboard End-to-End Verification Script
# This script verifies the analytics dashboard implementation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo -e "Analytics Dashboard Verification"
echo -e "========================================${NC}"
echo ""

# Function to check if service is running
check_service() {
    local port=$1
    local name=$2

    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running on port $port"
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT running on port $port"
        return 1
    fi
}

# Function to test API endpoint
test_endpoint() {
    local url=$1
    local name=$2

    echo -n "Testing $name... "
    response=$(curl -s -w "\n%{http_code}" "$url" || echo "000")
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $status_code)"

        # Check if response contains data (not placeholder)
        if echo "$body" | grep -q "average_days\|stage_name\|source_name\|recruiter_id"; then
            echo -e "  ${GREEN}→${NC} Response contains real database fields"
            return 0
        else
            echo -e "  ${YELLOW}⚠${NC} Response may contain placeholder data"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} (HTTP $status_code)"
        return 1
    fi
}

# Step 1: Check if services are running
echo -e "${BLUE}Step 1: Checking Services${NC}"
echo "----------------------------"

BACKEND_OK=0
FRONTEND_OK=0

if check_service 8000 "Backend API"; then
    BACKEND_OK=1
fi

if check_service 5173 "Frontend"; then
    FRONTEND_OK=1
fi

echo ""

if [ $BACKEND_OK -eq 0 ] || [ $FRONTEND_OK -eq 0 ]; then
    echo -e "${YELLOW}⚠ Services are not running. Starting them...${NC}"
    echo ""
    echo "To start services, run:"
    echo "  cd backend && uvicorn main:app --reload --port 8000 &"
    echo "  cd frontend && npm run dev &"
    echo ""
    echo "Or run the init script:"
    echo "  bash .auto-claude/specs/047-analytics-reporting-dashboard/init.sh"
    echo ""
    exit 1
fi

# Step 2: Test Backend API Endpoints
echo -e "${BLUE}Step 2: Testing Backend Analytics Endpoints${NC}"
echo "-------------------------------------------"

BACKEND_TESTS_PASSED=0
BACKEND_TESTS_TOTAL=4

test_endpoint "http://localhost:8000/api/analytics/key-metrics" "Key Metrics Endpoint" && ((BACKEND_TESTS_PASSED++)) || true
test_endpoint "http://localhost:8000/api/analytics/funnel" "Hiring Funnel Endpoint" && ((BACKEND_TESTS_PASSED++)) || true
test_endpoint "http://localhost:8000/api/analytics/source-effectiveness" "Source Effectiveness Endpoint" && ((BACKEND_TESTS_PASSED++)) || true
test_endpoint "http://localhost:8000/api/analytics/recruiter-performance" "Recruiter Performance Endpoint" && ((BACKEND_TESTS_PASSED++)) || true

echo ""
echo -e "Backend Tests: ${BACKEND_TESTS_PASSED}/${BACKEND_TESTS_TOTAL} passed"
echo ""

# Step 3: Test Backend API with Date Filters
echo -e "${BLUE}Step 3: Testing Date Range Filters${NC}"
echo "-----------------------------------"

# Get dates for last 30 days
START_DATE=$(date -u -v-30d +"%Y-%m-%dT00:00:00Z" 2>/dev/null || date -u -d "30 days ago" +"%Y-%m-%dT00:00:00Z")
END_DATE=$(date -u +"%Y-%m-%dT23:59:59Z")

echo "Testing with date range: $START_DATE to $END_DATE"
test_endpoint "http://localhost:8000/api/analytics/key-metrics?start_date=$START_DATE&end_date=$END_DATE" "Key Metrics with Date Filter"

echo ""

# Step 4: Frontend Verification (Manual)
echo -e "${BLUE}Step 4: Frontend Dashboard Verification${NC}"
echo "---------------------------------------"
echo ""
echo "Please manually verify the following in your browser:"
echo ""
echo -e "${YELLOW}1. Recruiter Dashboard (/recruiter/dashboard):${NC}"
echo "   URL: http://localhost:5173/recruiter/dashboard"
echo "   ✓ Page loads without errors"
echo "   ✓ 'Time to Hire' shows real database value (not placeholder)"
echo "   ✓ 'Active Jobs' shows actual vacancy count"
echo "   ✓ 'Total Candidates' shows actual candidate count"
echo "   ✓ 'Applications/Job' is calculated correctly"
echo "   ✓ No console errors in browser DevTools"
echo ""
echo -e "${YELLOW}2. Advanced Analytics Page (/recruiter/analytics):${NC}"
echo "   URL: http://localhost:5173/recruiter/analytics"
echo ""
echo "   ${YELLOW}a) Hiring Funnel Tab:${NC}"
echo "      ✓ Funnel visualization displays actual hiring stages"
echo "      ✓ Stage names are formatted properly (Applied, Screening, Interview, etc.)"
echo "      ✓ Candidate counts are real numbers from database"
echo "      ✓ Conversion rates are calculated and displayed"
echo ""
echo "   ${YELLOW}b) Source Effectiveness Tab:${NC}"
echo "      ✓ Source table shows real recruiting sources"
echo "      ✓ Candidate counts per source are displayed"
echo "      ✓ Conversion rates are shown"
echo "      ✓ No placeholder/test data visible"
echo ""
echo "   ${YELLOW}c) Recruiter Performance Tab:${NC}"
echo "      ✓ Performance metrics cards are visible"
echo "      ✓ Metrics show appropriate data"
echo "      ✓ Layout is consistent with other tabs"
echo ""
echo "   ${YELLOW}d) Date Range Filters:${NC}"
echo "      ✓ Change time period filter (7d, 30d, 90d, 1y)"
echo "      ✓ Data updates when filter changes"
echo "      ✓ Loading indicators appear during data fetch"
echo "      ✓ Error messages display if API fails"
echo ""

# Step 5: Database Verification
echo -e "${BLUE}Step 5: Database Data Verification${NC}"
echo "-----------------------------------"
echo ""
echo "Checking if database has analytics data..."
echo ""

# You can add psql commands here if needed
echo "To verify database has data, run:"
echo "  psql -d agenthr -c 'SELECT COUNT(*) FROM hiring_stages;'"
echo "  psql -d agenthr -c 'SELECT COUNT(*) FROM analytics_events;'"
echo "  psql -d agenthr -c 'SELECT COUNT(*) FROM recruiters;'"
echo ""

# Summary
echo -e "${BLUE}========================================"
echo -e "Verification Summary"
echo -e "========================================${NC}"
echo ""

if [ $BACKEND_TESTS_PASSED -eq $BACKEND_TESTS_TOTAL ]; then
    echo -e "${GREEN}✓ All backend API tests passed!${NC}"
else
    echo -e "${RED}✗ Some backend tests failed ($BACKEND_TESTS_PASSED/$BACKEND_TESTS_TOTAL passed)${NC}"
fi

echo ""
echo "Next steps:"
echo "1. Complete the manual frontend verification above"
echo "2. Test date range filters in the UI"
echo "3. Check browser console for any errors"
echo "4. Verify no placeholder data is visible"
echo ""
echo -e "${GREEN}If all checks pass, the analytics dashboard is ready!${NC}"
echo ""
