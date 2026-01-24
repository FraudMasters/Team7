#!/bin/bash

# E2E Test Setup Verification Script
# Checks if all prerequisites are met for running Playwright E2E tests

set -e

echo "======================================"
echo "E2E Test Setup Verification"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

check_port() {
    PORT=$1
    SERVICE=$2

    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $SERVICE is running on port $PORT"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $SERVICE is not running on port $PORT"
        return 1
    fi
}

check_file() {
    FILE=$1

    if [ -f "$FILE" ]; then
        echo -e "${GREEN}✓${NC} $FILE exists"
        return 0
    else
        echo -e "${RED}✗${NC} $FILE does not exist"
        return 1
    fi
}

# Track overall status
ALL_GOOD=true

echo "1. Checking required commands..."
echo "-------------------------------"
check_command node || ALL_GOOD=false
check_command npm || ALL_GOOD=false
check_command npx || ALL_GOOD=false
echo ""

echo "2. Checking Playwright installation..."
echo "-------------------------------"
if [ -d "node_modules/@playwright/test" ]; then
    echo -e "${GREEN}✓${NC} Playwright is installed in node_modules"
else
    echo -e "${RED}✗${NC} Playwright is not installed. Run: npm install"
    ALL_GOOD=false
fi

if [ -d "$HOME/.cache/ms-playwright" ] || [ -d "node_modules/.cache/ms-playwright" ]; then
    echo -e "${GREEN}✓${NC} Playwright browsers are installed"
else
    echo -e "${YELLOW}⚠${NC} Playwright browsers may not be installed. Run: npm run test:e2e:install"
fi
echo ""

echo "3. Checking E2E test files..."
echo "-------------------------------"
check_file "e2e/resume-analysis.spec.ts" || ALL_GOOD=false
check_file "e2e/fixtures/example-resume.json" || ALL_GOOD=false
check_file "e2e/fixtures/example-vacancy.json" || ALL_GOOD=false
check_file "e2e/fixtures/example-analysis-response.json" || ALL_GOOD=false
check_file "playwright.config.ts" || ALL_GOOD=false
echo ""

echo "4. Checking service availability..."
echo "-------------------------------"
BACKEND_RUNNING=false
FRONTEND_RUNNING=false

if check_port 8000 "Backend API"; then
    BACKEND_RUNNING=true
fi

if check_port 5173 "Frontend dev server"; then
    FRONTEND_RUNNING=true
fi
echo ""

echo "5. Checking API health..."
echo "-------------------------------"
if [ "$BACKEND_RUNNING" = true ]; then
    if curl -s http://localhost:8000/health | grep -q "status"; then
        echo -e "${GREEN}✓${NC} Backend API is healthy"
    else
        echo -e "${RED}✗${NC} Backend API is not responding correctly"
        ALL_GOOD=false
    fi
else
    echo -e "${YELLOW}⚠${NC} Skipping API health check (backend not running)"
fi
echo ""

# Summary
echo "======================================"
echo "Summary"
echo "======================================"

if [ "$ALL_GOOD" = true ] && [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo ""
    echo "You can run E2E tests:"
    echo "  npm run test:e2e          # Run all tests"
    echo "  npm run test:e2e:ui       # Run in UI mode"
    echo "  npm run test:e2e:debug    # Debug tests"
    echo ""
    exit 0
else
    echo -e "${YELLOW}Setup incomplete. Please fix the issues above.${NC}"
    echo ""

    if [ "$BACKEND_RUNNING" = false ]; then
        echo "To start backend:"
        echo "  cd backend"
        echo "  uvicorn main:app --reload --port 8000"
        echo ""
    fi

    if [ "$FRONTEND_RUNNING" = false ]; then
        echo "To start frontend:"
        echo "  npm run dev"
        echo ""
    fi

    exit 1
fi
