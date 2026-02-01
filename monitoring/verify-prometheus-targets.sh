#!/bin/bash
# Verification script for Prometheus targets
# Subtask 10-1: Verify Prometheus is scraping all targets successfully

set -e

PROMETHEUS_URL="http://localhost:9090"
EXPECTED_TARGETS=(
  "backend:8000"
  "celery_exporter:9540"
  "postgres_exporter:9187"
  "redis:6379"
  "cadvisor:8080"
  "loki:9090"
  "prometheus:9090"
)

echo "========================================"
echo "Prometheus Targets Verification"
echo "========================================"
echo ""

# Check if Prometheus is accessible
echo "1. Checking Prometheus API connectivity..."
if curl -s "${PROMETHEUS_URL}/api/v1/status/config" > /dev/null 2>&1; then
    echo "✓ Prometheus API is accessible at ${PROMETHEUS_URL}"
else
    echo "✗ Prometheus API is NOT accessible at ${PROMETHEUS_URL}"
    echo "  Please ensure Prometheus is running"
    exit 1
fi

echo ""
echo "2. Fetching targets status from Prometheus..."
TARGETS_JSON=$(curl -s "${PROMETHEUS_URL}/api/v1/targets")

# Extract target information
echo ""
echo "3. Analyzing target health..."
echo ""

# Parse and display each target
echo "Target Status Summary:"
echo "----------------------"

# Count total and up targets
TOTAL_TARGETS=0
UP_TARGETS=0
DOWN_TARGETS=0

# Get target health for each job
for job in backend celery-exporter postgres redis cadvisor loki prometheus docker; do
    HEALTH=$(echo "$TARGETS_JSON" | jq -r ".data.activeTargets[] | select(.labels.job==\"$job\") | .health" 2>/dev/null || echo "unknown")

    if [ "$HEALTH" = "up" ]; then
        echo "✓ $job: UP"
        UP_TARGETS=$((UP_TARGETS + 1))
        TOTAL_TARGETS=$((TOTAL_TARGETS + 1))
    elif [ "$HEALTH" = "down" ]; then
        # Get the error message
        ERROR=$(echo "$TARGETS_JSON" | jq -r ".data.activeTargets[] | select(.labels.job==\"$job\") | .lastError" 2>/dev/null || echo "Unknown error")
        echo "✗ $job: DOWN"
        echo "  Error: $ERROR"
        DOWN_TARGETS=$((DOWN_TARGETS + 1))
        TOTAL_TARGETS=$((TOTAL_TARGETS + 1))
    else
        echo "? $job: NOT FOUND"
        TOTAL_TARGETS=$((TOTAL_TARGETS + 1))
    fi
done

echo ""
echo "Summary: $UP_TARGETS/$TOTAL_TARGETS targets are UP"
echo ""

# Check if metrics are being collected
echo "4. Verifying metrics collection..."
echo ""

# Test querying the 'up' metric
UP_METRIC=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=up" | jq -r '.data.result[] | "\(.metric.job): \(.value[1])"' 2>/dev/null || echo "")

if [ -n "$UP_METRIC" ]; then
    echo "✓ Metrics are being collected from:"
    echo "$UP_METRIC" | while read -r line; do
        if [[ "$line" == *"1"* ]]; then
            echo "  ✓ $line"
        else
            echo "  ✗ $line"
        fi
    done
else
    echo "✗ No metrics found"
fi

echo ""
echo "5. Detailed Target Information:"
echo "-------------------------------"

# Show detailed information for each target
echo "$TARGETS_JSON" | jq -r '.data.activeTargets[] | "
Job: \(.labels.job // "unknown")
Target: \(.labels.instance // "unknown")
Health: \(.health)
Last Scrape: \(.lastScrape // "N/A")
Scrape Duration: \(.lastScrapeDuration // "N/A")s
Error: \(.lastError // "None")
---"' 2>/dev/null || echo "Unable to parse detailed target information"

echo ""
echo "========================================"
echo "Verification Complete"
echo "========================================"

# Exit with appropriate status
if [ $UP_TARGETS -eq $TOTAL_TARGETS ]; then
    echo "✓ All targets are UP!"
    exit 0
elif [ $UP_TARGETS -gt 0 ]; then
    echo "⚠ Some targets are UP, but $DOWN_TARGETS are DOWN"
    exit 1
else
    echo "✗ All targets are DOWN or unreachable"
    exit 1
fi
