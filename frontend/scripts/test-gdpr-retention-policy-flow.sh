#!/bin/bash

# GDPR Data Retention Policy End-to-End Test Runner
#
# This script runs the complete GDPR retention policy tests and generates a report.
#
# Usage:
#   ./scripts/test-gdpr-retention-policy-flow.sh [options]
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
      echo "GDPR Data Retention Policy End-to-End Test Runner"
      echo ""
      echo "Usage:"
      echo "  ./scripts/test-gdpr-retention-policy-flow.sh [options]"
      echo ""
      echo "Options:"
      echo "  --ui          Run tests in UI mode (interactive)"
      echo "  --headed      Run tests with visible browser"
      echo "  --debug       Run tests in debug mode"
      echo "  --grep PATTERN Filter tests by pattern"
      echo "  --help        Show this help message"
      echo ""
      echo "Examples:"
      echo "  ./scripts/test-gdpr-retention-policy-flow.sh"
      echo "  ./scripts/test-gdpr-retention-policy-flow.sh --ui"
      echo "  ./scripts/test-gdpr-retention-policy-flow.sh --headed"
      echo "  ./scripts/test-gdpr-retention-policy-flow.sh --grep \"API Management\""
      echo "  ./scripts/test-gdpr-retention-policy-flow.sh --grep \"Data Verification\""
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
echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}GDPR Retention Policy E2E Test Runner${NC}"
echo -e "${BLUE}===========================================${NC}"
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
echo "   Test File: e2e/gdpr-retention-policy-flow.spec.ts"
echo "   Total Tests: 19"
echo "   Test Suites:"
echo "     • Retention Policy Management API (5 tests)"
echo "     • Data Creation with Different Ages (3 tests)"
echo "     • Cleanup Execution Tests (3 tests)"
echo "     • Data Verification Tests (3 tests)"
echo "     • Audit Trail Verification Tests (2 tests)"
echo "     • Mobile Responsive Tests (2 tests)"
echo "     • Complete End-to-End Workflow Test (1 test)"
echo ""

if [ -n "$GREP_PATTERN" ]; then
  echo -e "${GREEN}🔍 Filter Pattern: ${GREP_PATTERN}${NC}"
  echo ""
fi

# Build Playwright command
PLAYWRIGHT_CMD="npx playwright test e2e/gdpr-retention-policy-flow.spec.ts"

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
  echo -e "${GREEN}✅ GDPR Retention Policy Automation Verified:${NC}"
  echo "   ✓ Retention policies create and manage correctly"
  echo "   ✓ Old data deleted per retention period"
  echo "   ✓ Recent data preserved correctly"
  echo "   ✓ Cleanup logged to audit trail"
  echo "   ✓ Dry-run mode works properly"
  echo "   ✓ Mobile responsive verified"
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
  echo "   4. Ensure Celery worker is available (for manual task execution)"
  echo "   5. Check retention policy API endpoints are working"
  echo "   6. Verify audit log API is accessible"
  echo "   7. Check browser console for errors"
  echo "   8. Check backend logs for errors"
  echo ""
  echo -e "${RED}❌ GDPR Retention Policy Automation Test: FAILED${NC}"
fi

echo -e "${BLUE}─────────────────────────────────${NC}"
echo ""

# Show next steps
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}🎉 Congratulations! Retention policy automation is working correctly.${NC}"
  echo ""
  echo "GDPR Requirements Verified:"
  echo "  • Storage Limitation: Automatic data deletion after retention period"
  echo "  • Data Minimization: Only necessary data retained"
  echo "  • Right to Erasure: Automated cleanup supports GDPR compliance"
  echo "  • Accountability: Complete audit trail of cleanup operations"
  echo "  • Transparency: Retention policies tracked and logged"
  echo ""
  echo "Next steps:"
  echo "  • Run other GDPR e2e tests if not yet completed"
  echo "  • Review test report: playwright-report/index.html"
  echo "  • Update implementation plan to mark subtask-7-4 as completed"
  echo "  • Proceed to subtask-7-5: Privacy by design verification"
else
  echo -e "${YELLOW}📝 To see test details, run:${NC}"
  echo "  npx playwright show-report"
  echo ""
  echo -e "${YELLOW}📝 To re-run failed tests only:${NC}"
  echo "  npx playwright test e2e/gdpr-retention-policy-flow.spec.ts --retries=0"
  echo ""
  echo -e "${YELLOW}📝 To run specific test suites:${NC}"
  echo "  npx playwright test e2e/gdpr-retention-policy-flow.spec.ts -g \"API Management\""
  echo "  npx playwright test e2e/gdpr-retention-policy-flow.spec.ts -g \"Data Verification\""
  echo "  npx playwright test e2e/gdpr-retention-policy-flow.spec.ts -g \"Audit Trail\""
fi

echo ""

exit $TEST_EXIT_CODE
