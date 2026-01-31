#!/bin/bash
# Quick Performance Test Runner
# This script runs the performance verification for 10k+ candidates

echo "================================"
echo "Performance Verification Test"
echo "Sub-2 second search with 10k+ candidates"
echo "================================"
echo ""

cd backend

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

echo "Running performance verification..."
echo ""

python3 verify_performance.py

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Performance verification PASSED"
else
    echo "❌ Performance verification FAILED"
fi

exit $exit_code
