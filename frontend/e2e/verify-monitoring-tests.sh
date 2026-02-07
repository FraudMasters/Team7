#!/bin/bash

# Integration Monitoring Dashboard Verification Script
#
# This script verifies that the integration monitoring test infrastructure is properly set up
# and provides guidance for running the tests.

set -e

echo "================================"
echo "Integration Monitoring Tests Verification"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} File missing: $1"
        ((FAILED++))
        return 1
    fi
}

check_file_content() {
    local file="$1"
    local pattern="$2"
    local description="$3"

    if [ ! -f "$file" ]; then
        echo -e "${RED}✗${NC} File not found: $file"
        ((FAILED++))
        return 1
    fi

    if grep -q "$pattern" "$file"; then
        echo -e "${GREEN}✓${NC} $description"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Missing: $description"
        ((WARNINGS++))
        return 1
    fi
}

# Start verification
echo "1. Checking Test File Structure..."
echo "-----------------------------------"

check_file "frontend/e2e/integrations-monitoring.spec.ts"
check_file "frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md"

echo ""
echo "2. Verifying Test Implementation..."
echo "-----------------------------------"

# Check test file structure
if check_file "frontend/e2e/integrations-monitoring.spec.ts"; then
    check_file_content "frontend/e2e/integrations-monitoring.spec.ts" "test.describe" "Test suites defined"
    check_file_content "frontend/e2e/integrations-monitoring.spec.ts" "should display integration health status" "Integration health status tests"
    check_file_content "frontend/e2e/integrations-monitoring.spec.ts" "should display sync metrics" "Sync metrics tests"
    check_file_content "frontend/e2e/integrations-monitoring.spec.ts" "should display recent sync errors" "Error display tests"
    check_file_content "frontend/e2e/integrations-monitoring.spec.ts" "should allow viewing detailed sync history" "Sync history tests"
    check_file_content "frontend/e2e/integrations-monitoring.spec.ts" "should auto-refresh" "Real-time updates tests"
    check_file_content "frontend/e2e/integrations-monitoring.spec.ts" "should display helpful message when no integrations" "Empty state tests"
fi

echo ""
echo "3. Checking Documentation..."
echo "----------------------------"

if check_file "frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md"; then
    check_file_content "frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md" "## Test Coverage" "Test coverage section"
    check_file_content "frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md" "## Running the Tests" "Test execution instructions"
    check_file_content "frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md" "## Verification Checklist" "Manual verification checklist"
    check_file_content "frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md" "## CI/CD Integration" "CI/CD integration examples"
fi

echo ""
echo "4. Checking Frontend Components..."
echo "----------------------------------"

check_file "frontend/src/pages/IntegrationsPage.tsx"
check_file "frontend/src/components/SyncHistory.tsx"

if [ -f "frontend/src/pages/IntegrationsPage.tsx" ]; then
    check_file_content "frontend/src/pages/IntegrationsPage.tsx" "integration.*status|status.*badge" "Integration status display"
    check_file_content "frontend/src/pages/IntegrationsPage.tsx" "sync.*history|SyncHistory" "Sync history component"
fi

if [ -f "frontend/src/components/SyncHistory.tsx" ]; then
    check_file_content "frontend/src/components/SyncHistory.tsx" "sync.*status|records.*processed|duration" "Sync metrics display"
fi

echo ""
echo "5. Checking Backend API Endpoints..."
echo "------------------------------------"

check_file "backend/api/integrations.py"

if [ -f "backend/api/integrations.py" ]; then
    check_file_content "backend/api/integrations.py" "GET.*integrations" "List integrations endpoint"
    check_file_content "backend/api/integrations.py" "syncs|sync.*history" "Sync history endpoint"
fi

echo ""
echo "6. Verification Summary..."
echo "-------------------------"

echo "Passed: $PASSED"
echo "Warnings: $WARNINGS"
echo "Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Ensure backend server is running: cd backend && python -m uvicorn main:app --reload"
    echo "2. Ensure frontend server is running: cd frontend && npm run dev"
    echo "3. Run the monitoring tests: cd frontend && npm run test:e2e integrations-monitoring"
    echo ""
    echo "For detailed instructions, see: frontend/e2e/INTEGRATIONS_MONITORING_TESTS.md"

    # Check if services are running
    echo ""
    echo "Checking service availability..."

    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend API is running on http://localhost:8000"
    else
        echo -e "${YELLOW}⚠${NC} Backend API is not running on http://localhost:8000"
        echo "  Start it with: cd backend && python -m uvicorn main:app --reload"
    fi

    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend is running on http://localhost:5173"
    else
        echo -e "${YELLOW}⚠${NC} Frontend is not running on http://localhost:5173"
        echo "  Start it with: cd frontend && npm run dev"
    fi

    echo ""
    echo "To run tests now:"
    echo "  cd frontend && npx playwright test integrations-monitoring.spec.ts"
    echo ""
    echo "To run tests with UI:"
    echo "  cd frontend && npx playwright test integrations-monitoring.spec.ts --ui"

    exit 0
else
    echo ""
    echo -e "${RED}✗ Some checks failed. Please review the output above.${NC}"
    exit 1
fi
