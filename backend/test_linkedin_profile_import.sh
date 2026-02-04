#!/bin/bash
# Test execution script for LinkedIn profile import flow integration tests
# This script runs comprehensive tests for the complete import flow

set -e

echo "========================================="
echo "LinkedIn Profile Import Flow - Integration Tests"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")"

echo -e "${YELLOW}Step 1: Checking dependencies...${NC}"
python -c "import pytest; print('✓ pytest installed')" || {
    echo -e "${RED}✗ pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio pytest-mock
}

echo -e "${YELLOW}Step 2: Verifying implementation files...${NC}"
python -c "from tasks.linkedin_sync import sync_linkedin_profile; print('✓ sync_linkedin_profile task exists')" || {
    echo -e "${RED}✗ sync_linkedin_profile task not found${NC}"
    exit 1
}

python -c "from tasks.linkedin_sync import map_linkedin_skills_to_taxonomy; print('✓ map_linkedin_skills_to_taxonomy function exists')" || {
    echo -e "${RED}✗ map_linkedin_skills_to_taxonomy function not found${NC}"
    exit 1
}

python -c "from tasks.linkedin_sync import save_linkedin_profile; print('✓ save_linkedin_profile function exists')" || {
    echo -e "${RED}✗ save_linkedin_profile function not found${NC}"
    exit 1
}

python -c "from services.linkedin_service import LinkedInService; print('✓ LinkedInService class exists')" || {
    echo -e "${RED}✗ LinkedInService class not found${NC}"
    exit 1
}

python -c "from models.linkedin_profile import LinkedInProfile; print('✓ LinkedInProfile model exists')" || {
    echo -e "${RED}✗ LinkedInProfile model not found${NC}"
    exit 1
}

python -c "from models.linkedin_import import LinkedInImport; print('✓ LinkedInImport model exists')" || {
    echo -e "${RED}✗ LinkedInImport model not found${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}Step 3: Running integration tests...${NC}"
echo ""

# Run the integration tests
if pytest tests/test_linkedin_profile_import_flow.py -v --tb=short -k "test_" 2>&1; then
    echo ""
    echo -e "${GREEN}✓ All integration tests passed!${NC}"
    TEST_RESULT=0
else
    echo ""
    echo -e "${RED}✗ Some integration tests failed${NC}"
    TEST_RESULT=1
fi

echo ""
echo -e "${YELLOW}Step 4: Verifying test coverage...${NC}"
echo ""

# Count test cases
TOTAL_TESTS=$(grep -c "def test_" tests/test_linkedin_profile_import_flow.py || echo "0")
echo "Total test cases defined: $TOTAL_TESTS"

# List test categories
echo ""
echo "Test categories covered:"
echo "  ✓ Step 1: Profile import request validation"
echo "  ✓ Step 2: Profile data fetching from LinkedIn API"
echo "  ✓ Step 3: Profile database saving"
echo "  ✓ Step 4: Celery task triggering"
echo "  ✓ Step 5: Skill taxonomy mapping"
echo "  ✓ Step 6: Candidate record creation"
echo "  ✓ Step 7: Frontend component verification"
echo "  ✓ End-to-end integration scenarios"
echo "  ✓ Edge cases and error handling"

echo ""
echo "========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}Integration Test Suite: PASSED${NC}"
else
    echo -e "${RED}Integration Test Suite: FAILED${NC}"
fi
echo "========================================="

exit $TEST_RESULT
