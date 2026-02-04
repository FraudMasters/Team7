#!/bin/bash

# Test Verification Script for Route-Based Code Splitting
# Generated for subtask-5-2: Run unit tests to ensure no regressions
# Usage: cd frontend && ./verify-tests.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Unit Test Verification Script${NC}"
echo -e "${BLUE}Route-Based Code Splitting Implementation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Error: npm is not available in this environment${NC}"
    echo -e "${YELLOW}⚠️  This script requires npm to run tests${NC}"
    echo -e "${YELLOW}⚠️  Please run this in an environment with Node.js and npm installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ npm found: $(npm --version)${NC}"
echo ""

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: package.json not found${NC}"
    echo -e "${YELLOW}⚠️  Please run this script from the frontend directory${NC}"
    echo -e "${YELLOW}   Usage: cd frontend && ./verify-tests.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ In frontend directory${NC}"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found, installing dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Running Unit Tests with Coverage${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Run tests with coverage
if npm run test:coverage -- --run; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Check coverage report
    if [ -f "coverage/coverage-summary.json" ]; then
        echo -e "${BLUE}Coverage Summary:${NC}"
        # Parse and display coverage from JSON (simplified)
        echo -e "${GREEN}✓ Coverage report generated in coverage/ directory${NC}"
        echo -e "${YELLOW}→ Open coverage/index.html in browser for detailed report${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ Test verification successful!${NC}"
    echo -e "${GREEN}✅ No regressions detected${NC}"
    echo -e "${GREEN}✅ Lazy loading implementation is compatible with test suite${NC}"
    echo ""

    # Display test count summary
    echo -e "${BLUE}Test Summary:${NC}"
    npm run test -- --run --reporter=verbose 2>&1 | grep -E "Test Files|Tests|Duration" || true

    echo ""
    echo -e "${BLUE}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""

    echo -e "${YELLOW}Debugging steps:${NC}"
    echo -e "${YELLOW}1. Run individual test files to identify failures:${NC}"
    echo -e "   ${BLUE}npm run test -- <test-file>${NC}"
    echo -e "${YELLOW}2. Check if failure is related to lazy loading:${NC}"
    echo -e "   ${BLUE}   If yes: Review TEST_ANALYSIS.md${NC}"
    echo -e "   ${BLUE}   If no: Likely unrelated test issue${NC}"
    echo -e "${YELLOW}3. Run tests without coverage to see detailed output:${NC}"
    echo -e "   ${BLUE}npm run test -- --run${NC}"
    echo ""

    exit 1
fi
