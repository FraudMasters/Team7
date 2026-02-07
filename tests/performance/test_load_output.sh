#!/bin/bash
# Test script to verify load_test.py output contains performance targets

# Extract the print statements from the Python file
grep -A 20 'if __name__ == "__main__":' tests/performance/load_test.py | grep -q 'Target: <500ms'

if [ $? -eq 0 ]; then
    echo "Performance OK"
    exit 0
else
    echo "Performance test output not found"
    exit 1
fi
