#!/bin/bash

# GDPR Consent Flow End-to-End Test Runner
#
# This script runs the complete GDPR consent flow tests and generates a report.
#
# Usage:
#   ./scripts/test-gdpr-consent-flow.sh [options]
#
# Options:
#   --ui          Run tests in UI mode (interactive)
#   --headed      Run tests with visible browser
#   --debug       Run tests in debug mode
#   --grep        Filter tests by pattern
#   --help        Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
UI_MODE=false
HEADED=false
DEBUG=false
GREP_PATTERN=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --ui)
      UI_MODE=true
      shift
      ;;
    --headed)
      HEADED=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --grep)
      GREP_PATTERN="$2"
      shift 2
      ;;
    --help)
      echo "GDPR Consent Flow End-to-End Test Runner"
      echo ""
      echo "Usage:"
      echo "  ./scripts/test-gdpr-consent-flow.sh [options]"
      echo ""
      echo "Options:"
      echo "  --ui          Run tests in UI mode (interactive)"
      echo "  --headed      Run tests with visible browser"
      echo "  --debug       Run tests in debug mode"
      echo "  --grep PATTERN Filter tests by pattern"
      echo "  --help        Show this help message"
      echo ""
      echo "Examples:"
      echo "  ./scripts/test-gdpr-consent-flow.sh"
      echo "  ./scripts/test-gdpr-consent-flow.sh --ui"
      echo "  ./scripts/test-gdpr-consent-flow.sh --headed"
      echo "  ./scripts/test-gdpr-consent-flow.sh --grep \"Cookie Banner\""
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
done

# Print banner
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}GDPR Consent Flow E2E Test Runner${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Change to frontend directory
cd "$(dirname "$0")/.."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
  npm install
fi

# Check if Playwright is installed
if ! npx playwright --version > /dev/null 2>&1; then
  echo -e "${YELLOW}⚠️  Playwright not found. Installing Playwright browsers...${NC}"
  npx playwright install chromium
fi

# Print test info
echo -e "${GREEN}📋 Test Configuration:${NC}"
echo "   Test File: e2e/gdpr-consent-flow.spec.ts"
echo "   Total Tests: 18"
echo "   Test Suites:"
echo "     • Cookie Banner (6 tests)"
echo "     • Privacy Settings (6 tests)"
echo "     • API Integration (2 tests)"
echo "     • Mobile Responsive (3 tests)"
echo "     • Complete End-to-End (1 test)"
echo ""

if [ -n "$GREP_PATTERN" ]; then
  echo -e "${GREEN}🔍 Filter Pattern: ${GREP_PATTERN}${NC}"
  echo ""
fi

# Build Playwright command
PLAYWRIGHT_CMD="npx playwright test e2e/gdpr-consent-flow.spec.ts"

if [ "$UI_MODE" = true ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --ui"
  echo -e "${GREEN}🎨 Mode: UI (Interactive)${NC}"
elif [ "$HEADED" = true ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --headed"
  echo -e "${GREEN}👁️  Mode: Headed (Visible Browser)${NC}"
else
  echo -e "${GREEN}🤖 Mode: Headless${NC}"
fi

if [ "$DEBUG" = true ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --debug"
  echo -e "${GREEN}🐛 Debug: Enabled${NC}"
fi

if [ -n "$GREP_PATTERN" ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD -g \"$GREP_PATTERN\""
fi

echo ""
echo -e "${BLUE}─────────────────────────────────${NC}"
echo -e "${BLUE}Running Tests...${NC}"
echo -e "${BLUE}─────────────────────────────────${NC}"
echo ""

# Run tests
eval $PLAYWRIGHT_CMD
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}─────────────────────────────────${NC}"

# Check results
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ All tests passed!${NC}"
  echo ""
  echo -e "${GREEN}📊 Test Results:${NC}"
  echo "   Status: PASSED"
  echo "   Details: See test-report.html for full report"
  echo ""
  echo -e "${GREEN}✅ GDPR Consent Flow End-to-End Test: PASSED${NC}"
else
  echo -e "${RED}❌ Some tests failed!${NC}"
  echo ""
  echo -e "${RED}📊 Test Results:${NC}"
  echo "   Status: FAILED"
  echo "   Details: Check the output above for error details"
  echo ""
  echo -e "${YELLOW}💡 Troubleshooting:${NC}"
  echo "   1. Ensure backend API is running on http://localhost:8000"
  echo "   2. Ensure frontend is running on http://localhost:5173"
  echo "   3. Ensure database is running and migrations are applied"
  echo "   4. Check browser console for errors"
  echo "   5. Check backend logs for errors"
  echo ""
  echo -e "${RED}❌ GDPR Consent Flow End-to-End Test: FAILED${NC}"
fi

echo -e "${BLUE}─────────────────────────────────${NC}"
echo ""

# Show next steps
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}🎉 Congratulations! The consent flow is working correctly.${NC}"
  echo ""
  echo "Next steps:"
  echo "  • Run other GDPR e2e tests (data export, data deletion, etc.)"
  echo "  • Review test report: playwright-report/index.html"
  echo "  • Update implementation plan to mark subtask-7-1 as completed"
else
  echo -e "${YELLOW}📝 To see test details, run:${NC}"
  echo "  npx playwright show-report"
  echo ""
  echo -e "${YELLOW}📝 To re-run failed tests only:${NC}"
  echo "  npx playwright test e2e/gdpr-consent-flow.spec.ts --retries=0"
fi

echo ""

exit $TEST_EXIT_CODE
