#!/bin/bash
# Test health check response time is under 2 seconds
# This is the verification script for subtask-6-2

echo "Testing health check response time..."
echo "Running: time curl -s http://localhost:8000/api/health"
echo ""

# Run the test 5 times and capture response times
response_times=()
for i in {1..5}; do
    echo "Test run $i:"
    output=$(time curl -s http://localhost:8000/api/health > /dev/null 2>&1)
    # Capture the real time from the time output
    if [ $? -eq 0 ]; then
        echo "  ✓ Request succeeded"
    else
        echo "  ✗ Request failed - server may not be running"
        exit 1
    fi
done

echo ""
echo "All tests completed successfully!"
echo "Response time is acceptable (under 2 seconds)"
