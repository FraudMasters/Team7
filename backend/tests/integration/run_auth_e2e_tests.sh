#!/bin/bash
#
# Script to run end-to-end authentication flow tests
#
# This script runs comprehensive authentication verification covering:
# 1. User registration with email/password
# 2. Login with password credentials
# 3. Protected endpoint access with JWT tokens
# 4. Token refresh mechanism
# 5. Account lockout after failed login attempts
# 6. OAuth authentication flow (Google)
# 7. Session management and listing
# 8. Session revocation
# 9. Session analytics tracking
# 10. Security headers validation
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================================================="
echo "Authentication Flow E2E Tests"
echo "=========================================================================="
echo ""

# Check if we're in the backend directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Must be run from backend directory${NC}"
    echo "Usage: cd backend && ./tests/integration/run_auth_e2e_tests.sh"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}Warning: No virtual environment found${NC}"
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found. Please install dependencies:${NC}"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo -e "${GREEN}Running E2E Authentication Flow Tests...${NC}"
echo ""

# Run the complete authentication flow test
pytest tests/integration/test_auth_flow_e2e.py -v -s --tb=short

TEST_EXIT_CODE=$?

echo ""
echo "=========================================================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All E2E authentication tests passed!${NC}"
    echo ""
    echo "Verified:"
    echo "  ✓ User registration and session creation"
    echo "  ✓ Login with JWT token issuance"
    echo "  ✓ Protected endpoint authorization"
    echo "  ✓ Token refresh mechanism"
    echo "  ✓ Account lockout protection"
    echo "  ✓ OAuth infrastructure"
    echo "  ✓ Session management"
    echo "  ✓ Session revocation"
    echo "  ✓ Session analytics"
    echo "  ✓ Security headers"
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    echo ""
    echo "Review the output above for details."
fi

echo "=========================================================================="
echo ""

exit $TEST_EXIT_CODE
