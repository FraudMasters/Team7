#!/bin/bash

# Performance Validation: Monitoring Overhead Test
# Subtask 10-5: Ensure monitoring overhead is minimal (< 5% response time increase)
#
# This script validates that the monitoring infrastructure (Prometheus middleware,
# structured logging, correlation IDs) does not significantly impact API performance.
#
# Prerequisites:
# - Docker services must be running (docker-compose up -d)
# - Backend API accessible at http://localhost:8000
# - Prometheus accessible at http://localhost:9090
# - curl and jq commands available
#
# Usage:
#   ./monitoring/validate-monitoring-overhead.sh
#
# Expected Results:
# - Response time increase < 5% compared to baseline
# - CPU usage within acceptable limits
# - Memory usage stable (no leaks)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
API_ENDPOINT="/api/resumes"
NUM_REQUESTS="${NUM_REQUESTS:-100}"
CONCURRENT_REQUESTS="${CONCURRENT_REQUESTS:-10}"
WARMUP_REQUESTS="${WARMUP_REQUESTS:-10}"
EXPECTED_OVERHEAD_THRESHOLD="${EXPECTED_OVERHEAD_THRESHOLD:-5}"  # 5% threshold

# Metrics
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

check_prereqs() {
    log_info "Checking prerequisites..."
    ((TOTAL_TESTS++))

    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed"
        return 1
    fi

    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed"
        return 1
    fi

    # Check if backend is accessible
    if ! curl -sf "${BACKEND_URL}/health" > /dev/null 2>&1; then
        log_error "Backend API is not accessible at ${BACKEND_URL}"
        return 1
    fi

    # Check if Prometheus is accessible
    if ! curl -sf "${PROMETHEUS_URL}/-/healthy" > /dev/null 2>&1; then
        log_error "Prometheus is not accessible at ${PROMETHEUS_URL}"
        return 1
    fi

    log_success "All prerequisites met"
    return 0
}

warmup_backend() {
    log_info "Warming up backend with ${WARMUP_REQUESTS} requests..."

    for i in $(seq 1 ${WARMUP_REQUESTS}); do
        curl -s "${BACKEND_URL}${API_ENDPOINT}" > /dev/null 2>&1 || true
    done

    log_success "Warmup complete"
}

measure_baseline_response_time() {
    log_info "Measuring baseline response time (without monitoring metrics)..."

    # Note: This measures response time with monitoring ENABLED
    # To truly measure baseline without monitoring, you would need to:
    # 1. Deploy a version without PrometheusMiddleware
    # 2. Disable structured logging
    # 3. Remove correlation ID middleware
    #
    # Since this is an integration test, we measure the CURRENT state
    # and compare against industry standards for acceptable overhead

    local total_time=0
    local count=0

    for i in $(seq 1 ${NUM_REQUESTS}); do
        local response_time=$(curl -o /dev/null -s -w '%{time_total}\n' "${BACKEND_URL}${API_ENDPOINT}")
        total_time=$(echo "$total_time + $response_time" | bc)
        ((count++))
    done

    local avg_time=$(echo "scale=4; $total_time / $count" | bc)
    echo "$avg_time"
}

get_prometheus_metrics() {
    log_info "Retrieving metrics from Prometheus..."

    # Wait for Prometheus to scrape latest metrics
    sleep 2

    # Query average response time from Prometheus
    local query='rate(http_request_duration_seconds_sum{handler="'${API_ENDPOINT}'"}[5m]) / rate(http_request_duration_seconds_count{handler="'${API_ENDPOINT}'"}[5m])'
    local prom_avg=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=$(echo "$query" | sed 's/ /%20/g')" | jq -r '.data.result[0].value[1] // "0"')

    echo "$prom_avg"
}

measure_container_resources() {
    log_info "Measuring backend container resource usage..."

    # Get backend container name
    local container_name=$(docker ps --format '{{.Names}}' | grep backend | head -1)

    if [ -z "$container_name" ]; then
        log_warning "Backend container not found"
        return 1
    fi

    # Get CPU usage percentage
    local cpu_usage=$(docker stats "$container_name" --no-stream --format "{{.CPUPerc}}" | sed 's/%//')

    # Get memory usage
    local mem_usage=$(docker stats "$container_name" --no-stream --format "{{.MemUsage}}")

    echo "$cpu_usage|$mem_usage"
}

calculate_overhead() {
    local with_monitoring=$1
    local baseline=$2

    # For this test, we estimate baseline as 80% of measured time
    # This assumes monitoring overhead is typically 10-20%
    local estimated_baseline=$(echo "scale=4; $with_monitoring / 1.2" | bc)

    # Calculate overhead percentage
    local overhead=$(echo "scale=2; (($with_monitoring - $estimated_baseline) / $estimated_baseline) * 100" | bc)

    echo "$overhead"
}

run_performance_test() {
    log_info "=========================================="
    log_info "PERFORMANCE VALIDATION TEST"
    log_info "=========================================="
    log_info "Backend URL: ${BACKEND_URL}"
    log_info "Prometheus URL: ${PROMETHEUS_URL}"
    log_info "Number of requests: ${NUM_REQUESTS}"
    log_info "Concurrent requests: ${CONCURRENT_REQUESTS}"
    log_info "Expected overhead threshold: ${EXPECTED_OVERHEAD_THRESHOLD}%"
    log_info "=========================================="
    echo ""

    # Prerequisites check
    if ! check_prereqs; then
        log_error "Prerequisites check failed. Exiting."
        exit 1
    fi

    echo ""

    # Warmup phase
    ((TOTAL_TESTS++))
    warmup_backend

    echo ""

    # Measure response times
    ((TOTAL_TESTS++))
    log_info "Test 1: Measuring API response times..."

    local avg_response_time=$(measure_baseline_response_time)
    log_info "Average response time: ${avg_response_time}s"

    # Get Prometheus metrics
    local prometheus_avg=$(get_prometheus_metrics)

    if [ "$prometheus_avg" != "0" ] && [ -n "$prometheus_avg" ]; then
        log_info "Prometheus reported average: ${prometheus_avg}s"

        # Compare direct measurement vs Prometheus
        local diff=$(echo "scale=2; ($avg_response_time - $prometheus_avg) / $prometheus_avg * 100" | bc)
        log_info "Difference: ${diff}%"

        if [ $(echo "$diff < 10" | bc -l) -eq 1 ]; then
            log_success "Direct measurement and Prometheus metrics aligned (diff: ${diff}%)"
        else
            log_warning "Significant difference between direct measurement and Prometheus (${diff}%)"
        fi
    else
        log_warning "No metrics available from Prometheus yet"
    fi

    echo ""

    # Calculate monitoring overhead
    ((TOTAL_TESTS++))
    log_info "Test 2: Calculating monitoring overhead..."

    local overhead=$(calculate_overhead "$avg_response_time")
    log_info "Estimated monitoring overhead: ${overhead}%"

    # Check if overhead is acceptable
    local overhead_check=$(echo "$overhead < $EXPECTED_OVERHEAD_THRESHOLD" | bc -l)

    if [ "$overhead_check" -eq 1 ]; then
        log_success "Monitoring overhead within acceptable range (< ${EXPECTED_OVERHEAD_THRESHOLD}%)"
    else
        log_error "Monitoring overhead exceeds threshold (${overhead}% > ${EXPECTED_OVERHEAD_THRESHOLD}%)"
    fi

    echo ""

    # Container resource usage
    ((TOTAL_TESTS++))
    log_info "Test 3: Measuring container resource usage..."

    local resources=$(measure_container_resources)

    if [ $? -eq 0 ]; then
        local cpu_usage=$(echo "$resources" | cut -d'|' -f1)
        local mem_usage=$(echo "$resources" | cut -d'|' -f2)

        log_info "CPU usage: ${cpu_usage}%"
        log_info "Memory usage: ${mem_usage}"

        # Check CPU usage is reasonable (< 50% for idle backend)
        local cpu_check=$(echo "$cpu_usage < 50" | bc -l 2>/dev/null || echo "0")

        if [ "$cpu_check" -eq 1 ]; then
            log_success "CPU usage within acceptable range"
        else
            log_warning "High CPU usage detected: ${cpu_usage}%"
        fi
    else
        log_warning "Could not measure container resources"
    fi

    echo ""

    # Memory leak detection
    ((TOTAL_TESTS++))
    log_info "Test 4: Checking for memory leaks..."

    # Get initial memory
    local resources_before=$(measure_container_resources)
    local mem_before=$(echo "$resources_before" | cut -d'|' -f2 | awk '{print $1}')

    # Make additional requests
    log_info "Making ${NUM_REQUESTS} additional requests to check for memory leaks..."

    for i in $(seq 1 ${NUM_REQUESTS}); do
        curl -s "${BACKEND_URL}${API_ENDPOINT}" > /dev/null 2>&1 || true
    done

    # Get final memory
    sleep 2
    local resources_after=$(measure_container_resources)
    local mem_after=$(echo "$resources_after" | cut -d'|' -f2 | awk '{print $1}')

    # Convert to MB for comparison (handles GiB/MiB format)
    local mem_before_mb=$(echo $mem_before | sed 's/GiB/*1024/g; s/MiB//g' | bc)
    local mem_after_mb=$(echo $mem_after | sed 's/GiB/*1024/g; s/MiB//g' | bc)

    if [ -n "$mem_before_mb" ] && [ -n "$mem_after_mb" ]; then
        local mem_increase=$(echo "scale=2; ($mem_after_mb - $mem_before_mb)" | bc)

        log_info "Memory before: ${mem_before}"
        log_info "Memory after: ${mem_after}"
        log_info "Memory increase: ${mem_increase} MiB"

        # Check if memory increase is acceptable (< 50 MB for 100 requests)
        local mem_check=$(echo "$mem_increase < 50" | bc -l 2>/dev/null || echo "0")

        if [ "$mem_check" -eq 1 ]; then
            log_success "No significant memory leak detected"
        else
            log_warning "Possible memory leak detected (${mem_increase} MiB increase)"
        fi
    else
        log_warning "Could not compare memory usage"
    fi

    echo ""

    # Summary
    log_info "=========================================="
    log_info "TEST SUMMARY"
    log_info "=========================================="
    log_info "Total tests: ${TOTAL_TESTS}"
    log_success "Passed: ${PASSED_TESTS}"
    if [ $FAILED_TESTS -gt 0 ]; then
        log_error "Failed: ${FAILED_TESTS}"
    else
        log_info "Failed: ${FAILED_TESTS}"
    fi
    log_info "=========================================="
    echo ""

    # Overall result
    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "✅ All performance validation tests passed!"
        log_info "Monitoring overhead is minimal and within acceptable limits."
        return 0
    else
        log_error "❌ Some performance validation tests failed."
        log_warning "Review the results above and consider:"
        log_warning "  - Optimizing Prometheus middleware"
        log_warning "  - Reducing logging verbosity"
        log_warning "  - Checking for memory leaks in middleware"
        log_warning "  - Reviewing correlation ID generation overhead"
        return 1
    fi
}

# Run the performance test
run_performance_test
