#!/bin/bash

# E2E Test Runner for Matching Weights Customization
# This script runs the comprehensive end-to-end test suite

set -e  # Exit on error

echo "=========================================="
echo "E2E Test Suite: Matching Weights Feature"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")/../"
echo "Working directory: $(pwd)"
echo ""

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not active${NC}"
    echo "Activating virtual environment..."
    if [[ -f "../.venv/bin/activate" ]]; then
        source "../.venv/bin/activate"
    else
        echo -e "${RED}Error: Virtual environment not found${NC}"
        echo "Please run: source .venv/bin/activate"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Virtual environment active${NC}"
echo ""

# Check if database is accessible
echo "Checking database connection..."
python -c "
import asyncio
from backend.core.database import async_session_maker
from sqlalchemy import text

async def check_db():
    async with async_session_maker() as session:
        result = await session.execute(text('SELECT 1'))
        print('Database connection: OK')

asyncio.run(check_db())
" 2>/dev/null || {
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "Please ensure PostgreSQL is running and migrations are applied"
    exit 1
}

echo -e "${GREEN}✓ Database connection OK${NC}"
echo ""

# Check if migrations are applied
echo "Checking database migrations..."
python -c "
import asyncio
from backend.core.database import async_session_maker
from sqlalchemy import text

async def check_migrations():
    async with async_session_maker() as session:
        result = await session.execute(text(
            \"SELECT table_name FROM information_schema.tables \"
            \"WHERE table_schema='public' AND table_name='matching_weights_profiles'\"
        ))
        if result.fetchone():
            print('Migration status: OK (matching_weights_profiles table exists)')
        else:
            print('Migration status: MISSING')
            exit(1)

asyncio.run(check_migrations())
" || {
    echo -e "${YELLOW}⚠ Migrations not applied${NC}"
    echo "Running migrations..."
    alembic upgrade head
    echo -e "${GREEN}✓ Migrations applied${NC}"
}

echo ""

# Seed preset profiles if needed
echo "Checking preset profiles..."
python scripts/seed_weight_profiles.py
echo -e "${GREEN}✓ Preset profiles ready${NC}"
echo ""

# Run the E2E tests
echo "=========================================="
echo "Running E2E Test Suite"
echo "=========================================="
echo ""

# Run pytest with E2E tests
pytest tests/integration/test_matching_weights_e2e.py \
    -v \
    --tb=short \
    --disable-warnings \
    -k "test_e2e" \
    --color=yes

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All E2E tests passed!${NC}"
    echo ""
    echo "Test Coverage:"
    echo "  • Preset profiles creation and verification"
    echo "  • Custom profile CRUD operations"
    echo "  • Weight normalization"
    echo "  • Profile selection and vacancy re-matching"
    echo "  • A/B testing comparison"
    echo "  • Complete end-to-end workflow"
    echo ""
    echo "Next Steps:"
    echo "  1. Run manual browser tests (see E2E_TESTING_GUIDE.md)"
    echo "  2. Verify UI components in development environment"
    echo "  3. Check performance under load"
else
    echo -e "${RED}✗ Some E2E tests failed${NC}"
    echo ""
    echo "Please review the errors above and:"
    echo "  1. Check database state"
    echo "  2. Verify API endpoints are accessible"
    echo "  3. Ensure all migrations applied"
    echo "  4. Review test logs for details"
fi
echo "=========================================="

exit $TEST_EXIT_CODE
