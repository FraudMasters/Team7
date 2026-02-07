#!/bin/bash
# LinkedIn OAuth Flow End-to-End Test Runner
# This script runs the OAuth flow tests

set -e

echo "======================================================================"
echo "LinkedIn OAuth Flow End-to-End Test"
echo "======================================================================"
echo ""
echo "This test validates the complete OAuth 2.0 integration:"
echo "1. Backend auth URL generation"
echo "2. Frontend redirect handling"
echo "3. Backend callback processing"
echo "4. Token exchange logic"
echo "5. Error handling"
echo "6. CSRF protection"
echo ""

# Change to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✓ Virtual environment found"
    source .venv/bin/activate
else
    echo "⚠ No virtual environment found, using system Python"
fi

# Check Python version
echo "Python version: $(python --version 2>&1 || echo 'Not found')"

# Run the test
echo ""
echo "Running OAuth flow tests..."
echo "----------------------------------------------------------------------"
python test_linkedin_oauth_flow.py "$@"

exit $?
