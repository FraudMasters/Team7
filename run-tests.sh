#!/bin/bash
# Test Execution Script for Subtask 4-1
# This script runs all tests to verify no regressions from database optimizations
#
# Usage:
#   cd backend && source .venv/bin/activate
#   bash ../run-tests.sh

set -e  # Exit on error

echo "=================================="
echo "Subtask 4-1: Test Execution Script"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL client not found in PATH${NC}"
    echo "   Ensure PostgreSQL is running"
fi

if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found${NC}"
    echo "   Activate virtual environment: source .venv/bin/activate"
    exit 1
fi

echo -e "${GREEN}✅ pytest found${NC}"
echo ""

# Verify imports
echo "📦 Verifying imports..."
python -c "from config import get_settings; print('  ✅ config module OK')"
python -c "from database import engine; print('  ✅ database module OK')"
python -c "from utils.eager_loading import bulk_fetch_by_ids; print('  ✅ eager_loading module OK')"
echo ""

# Verify configuration
echo "⚙️  Verifying database configuration..."
python -c "
from config import get_settings
s = get_settings()
print(f'  Pool size: {s.db_pool_size}')
print(f'  Max overflow: {s.db_max_overflow}')
print(f'  Pool timeout: {s.db_pool_timeout}s')
print(f'  Pool recycle: {s.db_pool_recycle}s')
"
echo ""

# Run tests
echo "🧪 Running test suite..."
echo ""

# Run high-priority tests first (directly affected by changes)
echo "--- High Priority Tests (Directly Affected) ---"
echo "Running analytics tests..."
pytest tests/api/test_analytics.py -v --tb=short || echo -e "${RED}❌ Analytics tests failed${NC}"

echo ""
echo "Running workflow integration tests..."
pytest tests/integration/test_workflow_e2e.py -v --tb=short || echo -e "${RED}❌ Workflow tests failed${NC}"

echo ""
echo "--- Medium Priority Tests (Indirectly Affected) ---"
echo "Running performance tests..."
pytest tests/performance/test_api_performance.py -v --tb=short || echo -e "${RED}❌ Performance tests failed${NC}"

echo ""
echo "--- Full Test Suite ---"
echo "Running all tests..."
pytest tests/ -v --tb=short --maxfail=5 || {
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Check the output above for details"
    exit 1
}

echo ""
echo "=================================="
echo -e "${GREEN}✅ All tests passed!${NC}"
echo "=================================="
echo ""
echo "Summary:"
echo "  • Database configuration: ✅ Verified"
echo "  • Eager loading utilities: ✅ Imported"
echo "  • Analytics endpoints: ✅ No regressions"
echo "  • Workflow integration: ✅ No regressions"
echo "  • Performance tests: ✅ Passed"
echo "  • All test suites: ✅ Passed"
echo ""
echo "No regressions detected from database optimization changes."
echo ""
