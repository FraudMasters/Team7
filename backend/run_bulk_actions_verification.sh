#!/bin/bash
# Bulk Actions Verification Script
#
# This script runs the comprehensive bulk actions verification
# to ensure all bulk operations work correctly on search results.
#
# Usage:
#   ./run_bulk_actions_verification.sh          # Run verification
#   ./run_bulk_actions_verification.sh --cleanup  # Run and cleanup
#   ./run_bulk_actions_verification.sh --verbose  # Verbose output

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Bulk Actions Verification${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Change to backend directory
cd "$(dirname "$0")"

# Run verification script
echo -e "${YELLOW}Running bulk actions verification...${NC}"
echo ""

if python3 verify_bulk_actions.py "$@"; then
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  ✓ All Verifications Passed!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${GREEN}Bulk actions are working correctly!${NC}"
    echo ""
    echo "Verified functionality:"
    echo "  ✓ Search returns 20+ candidates"
    echo "  ✓ Bulk tag action works correctly"
    echo "  ✓ Bulk export (JSON) works correctly"
    echo "  ✓ Bulk export (CSV) works correctly"
    echo "  ✓ Bulk add_to_pipeline action works correctly"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}  ✗ Verification Failed${NC}"
    echo -e "${RED}============================================${NC}"
    echo ""
    echo -e "${RED}Please review the errors above and fix the issues.${NC}"
    echo ""
    echo "To run with verbose output:"
    echo "  ./run_bulk_actions_verification.sh --verbose"
    echo ""
    exit 1
fi
