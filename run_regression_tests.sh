#!/bin/bash
# Full Regression Test Suite
# Runs both backend and frontend tests to ensure no regressions
# For Candidate Source Attribution Analytics Feature

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "Full Regression Test Suite"
echo "Candidate Source Attribution Analytics"
echo "========================================"
echo ""

# Backend tests
echo -e "${BLUE}[1/2] Running Backend Tests...${NC}"
echo ""
cd backend

if [ ! -f "run_backend_tests.sh" ]; then
    echo -e "${RED}Error: run_backend_tests.sh not found${NC}"
    exit 1
fi

chmod +x run_backend_tests.sh
./run_backend_tests.sh -v

BACKEND_EXIT_CODE=$?
cd ..

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Backend tests PASSED${NC}"
else
    echo -e "${RED}❌ Backend tests FAILED${NC}"
    exit 1
fi

echo ""
echo "========================================"
echo ""

# Frontend tests
echo -e "${BLUE}[2/2] Running Frontend Tests...${NC}"
echo ""
cd frontend

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm not found${NC}"
    echo "Please install Node.js and npm"
    exit 1
fi

# Run frontend tests
npm test -- --watchAll=false

FRONTEND_EXIT_CODE=$?
cd ..

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend tests PASSED${NC}"
else
    echo -e "${RED}❌ Frontend tests FAILED${NC}"
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
echo "========================================"
echo ""
echo "Summary:"
echo "  Backend:  PASSED"
echo "  Frontend: PASSED"
echo ""
echo "No regressions detected!"
echo ""
