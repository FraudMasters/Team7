#!/bin/bash
#
# Search Alert Workflow - End-to-End Verification Script
#
# This script runs the complete verification of the search alert workflow.
# It tests the entire flow from creating saved searches to sending notifications.
#
# Usage:
#   cd backend
#   bash run_search_alert_verification.sh
#

set -e  # Exit on error

echo "========================================================================"
echo "Search Alert Workflow - End-to-End Verification"
echo "========================================================================"
echo ""

# Change to backend directory
cd "$(dirname "$0")"

echo "Step 1: Running verification script..."
echo "------------------------------------------------------------------------"

# Run the Python verification script
python verify_search_alert_workflow.py

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✓ VERIFICATION SUCCESSFUL"
    echo "========================================================================"
    echo ""
    echo "All steps of the search alert workflow have been verified:"
    echo "  1. ✓ Create saved search with filters"
    echo "  2. ✓ Upload new resume that matches criteria"
    echo "  3. ✓ Celery task processes and matches resume"
    echo "  4. ✓ SearchAlert record created"
    echo "  5. ✓ Email notification sent (simulated)"
    echo "  6. ✓ Alert marked as sent"
    echo ""
    exit 0
else
    echo ""
    echo "========================================================================"
    echo "✗ VERIFICATION FAILED"
    echo "========================================================================"
    echo ""
    echo "Please check the error messages above for details."
    echo ""
    exit 1
fi
