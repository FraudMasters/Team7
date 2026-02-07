#!/bin/bash

###############################################################################
# GDPR Data Export Flow - End-to-End Test Runner
#
# This script runs the full suite of GDPR data export flow tests, including:
# - Frontend UI tests (dialog, format selection, export initiation)
# - API integration tests (export requests, error handling)
# - File download tests (JSON/CSV files, content verification)
# - Mobile responsive tests (375x667 viewport)
# - Complete end-to-end tests (full export flows)
#
# Usage:
#   ./test-gdpr-data-export-flow.sh [options]
#
# Options:
#   --ui        Run tests in Playwright UI mode (headed, interactive)
#   --headed    Run tests in headed mode (visible browser)
#   --debug     Run tests in debug mode (pause execution)
#   --grep      Run only tests matching pattern (e.g., --grep "JSON")
#   --project   Run tests for specific project (chromium, firefox, webkit)
#
# Examples:
#   ./test-gdpr-data-export-flow.sh                 # Run all tests headless
#   ./test-gdpr-data-export-flow.sh --ui            # Run with UI
#   ./test-gdpr-data-export-flow.sh --grep "JSON"   # Run JSON export tests only
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT="chromium"
MODE=""
GREP_PATTERN=""
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --ui)
      MODE="--ui"
      shift
      ;;
    --headed)
      MODE="--headed"
      shift
      ;;
    --debug)
      MODE="--debug"
      shift
      ;;
    --grep)
      GREP_PATTERN="$2"
      shift 2
      ;;
    --project)
      PROJECT="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --ui        Run tests in Playwright UI mode (headed, interactive)"
      echo "  --headed    Run tests in headed mode (visible browser)"
      echo "  --debug     Run tests in debug mode (pause execution)"
      echo "  --grep      Run only tests matching pattern (e.g., --grep 'JSON')"
      echo "  --project   Run tests for specific project (chromium, firefox, webkit)"
      echo "  -h, --help  Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GDPR Data Export Flow - E2E Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Change to frontend directory
cd "$BASE_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo -e "${YELLOW}node_modules not found. Installing dependencies...${NC}"
  npm install
fi

# Check if Playwright is installed
if ! npx playwright --version > /dev/null 2>&1; then
  echo -e "${YELLOW}Playwright not found. Installing...${NC}"
  npx playwright install
fi

# Build command
COMMAND="npx playwright test e2e/gdpr-data-export-flow.spec.ts --project=$PROJECT"

if [ -n "$MODE" ]; then
  COMMAND="$COMMAND $MODE"
fi

if [ -n "$GREP_PATTERN" ]; then
  COMMAND="$COMMAND --grep \"$GREP_PATTERN\""
fi

# Print test configuration
echo -e "${BLUE}Test Configuration:${NC}"
echo "  Project: $PROJECT"
echo "  Test File: e2e/gdpr-data-export-flow.spec.ts"
echo "  Mode: ${MODE:-headless (default)}"
if [ -n "$GREP_PATTERN" ]; then
  echo "  Filter: $GREP_PATTERN"
fi
echo ""

# Print test suites
echo -e "${BLUE}Test Suites:${NC}"
echo "  ✓ Frontend UI (7 tests)"
echo "  ✓ API Integration (3 tests, 1 skipped)"
echo "  ✓ File Download (6 tests)"
echo "  ✓ Mobile Responsive (2 tests)"
echo "  ✓ Complete End-to-End (2 tests)"
echo ""

# Prompt for confirmation unless in UI/debug mode
if [ "$MODE" != "--ui" ] && [ "$MODE" != "--debug" ]; then
  echo -e "${YELLOW}Running tests in headless mode...${NC}"
  echo -e "${YELLOW}Use --ui flag for interactive mode${NC}"
  echo ""
fi

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo ""

eval $COMMAND

# Capture exit code
EXIT_CODE=$?

echo ""

# Check results
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}✓ All tests passed!${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""
  echo -e "${GREEN}GDPR Data Export Flow verified:${NC}"
  echo "  ✓ Frontend UI renders correctly"
  echo "  ✓ API integration works"
  echo "  ✓ File downloads successful"
  echo "  ✓ JSON format valid and complete"
  echo "  ✓ CSV format valid and complete"
  echo "  ✓ Mobile responsive working"
  echo "  ✓ End-to-end flows functional"
  echo ""
else
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}✗ Some tests failed!${NC}"
  echo -e "${RED}========================================${NC}"
  echo ""
  echo -e "${YELLOW}Troubleshooting:${NC}"
  echo "  1. Ensure backend API is running at http://localhost:8000"
  echo "  2. Ensure frontend dev server is running at http://localhost:5173"
  echo "  3. Check browser console for errors"
  echo "  4. Verify TEST_RESUME_ID environment variable is set"
  echo "  5. Review test output above for specific failures"
  echo ""
  echo -e "${YELLOW}For debugging, try:${NC}"
  echo "  $0 --ui"
  echo "  $0 --debug"
  echo "  $0 --grep 'test name'"
  echo ""
fi

exit $EXIT_CODE
