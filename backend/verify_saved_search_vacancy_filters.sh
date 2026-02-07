#!/bin/bash
#
# Shell wrapper for verify_saved_search_vacancy_filters.py
# Checks prerequisites and runs the verification script
#

set -e

echo "======================================================================"
echo "Subtask 5-1: Verify Saved Search with Vacancy Filters"
echo "======================================================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "✗ Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python version: $PYTHON_VERSION"

# Check if requests library is installed
if ! python3 -c "import requests" 2>/dev/null; then
    echo "✗ Error: requests library is not installed"
    echo "  Install with: pip install requests"
    exit 1
fi

echo "✓ requests library is installed"

# Check if backend server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✗ Error: Backend server is not running on http://localhost:8000"
    echo ""
    echo "Start the server with:"
    echo "  cd backend && python -m uvicorn main:app --reload --port 8000"
    echo ""
    exit 1
fi

echo "✓ Backend server is running on http://localhost:8000"
echo ""
echo "Running verification..."
echo ""

# Run the Python verification script
python3 backend/verify_saved_search_vacancy_filters.py
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✓ Verification completed successfully"
else
    echo "✗ Verification failed"
fi

exit $exit_code
