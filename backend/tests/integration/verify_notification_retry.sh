#!/bin/bash

# Verification script for notification delivery retry logic and failure handling
# This script runs all retry logic tests and provides a summary report

set -e

echo "=========================================="
echo "Notification Retry Logic Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")/../.."

echo "Running notification retry logic tests..."
echo ""

# Run the retry tests
if python -m pytest tests/integration/test_notification_retry.py -v --tb=short; then
    echo ""
    echo -e "${GREEN}✅ All retry logic tests passed!${NC}"
    echo ""
    echo "Test Coverage:"
    echo "  ✓ Successful delivery without retries"
    echo "  ✓ Transient errors trigger retry with exponential backoff"
    echo "  ✓ Max retries limit respected (3 for single, 2 for bulk)"
    echo "  ✓ Exponential backoff timing (60s, 120s, 240s for single)"
    echo "  ✓ Validation errors do not trigger retries"
    echo "  ✓ Timeout errors do not trigger retries"
    echo "  ✓ Bulk notifications handle partial failures"
    echo "  ✓ Delivery tracking fields updated correctly"
    echo "  ✓ Metadata handling in notifications"
    echo "  ✓ Duplicate email removal in bulk sends"
    echo ""
    echo -e "${GREEN}Retry Logic Verification: PASSED${NC}"
else
    echo ""
    echo -e "${RED}❌ Some retry logic tests failed${NC}"
    echo ""
    echo "Please check the test output above for details."
    echo "Common issues:"
    echo "  - Task module not found: Check PYTHONPATH"
    echo "  - Import errors: Verify all dependencies are installed"
    echo "  - Database errors: Ensure test database can be created"
    exit 1
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
