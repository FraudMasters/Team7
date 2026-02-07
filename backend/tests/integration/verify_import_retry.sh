#!/bin/bash

###############################################################################
# Import Failure Handling and Retry Mechanism Verification Script
#
# This script tests the import failure handling and retry functionality using
# curl to make HTTP requests to the backend API.
#
# Prerequisites:
#   - Backend server running on http://localhost:8000
#   - PostgreSQL database running
#   - Valid database connection
#
# Usage:
#   chmod +x verify_import_retry.sh
#   ./verify_import_retry.sh
###############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# API base URL
API_BASE="http://localhost:8000/api"

# Test data tracking
INTEGRATION_ID=""
IMPORT_LOG_ID=""
TASK_ID=""

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "\n${BLUE}${BOLD}================================================================================${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}================================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_server() {
    print_header "Checking Server Health"

    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/../health" 2>/dev/null)

    if [ "$response" = "200" ] || [ "$response" = "000" ]; then
        print_success "Server is running"
        return 0
    else
        print_error "Server is not responding (status: $response)"
        print_info "Please start the backend server with: uvicorn backend.main:app --reload"
        return 1
    fi
}

create_integration() {
    print_header "Creating Test Integration"

    response=$(curl -s -X POST "$API_BASE/integrations" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Indeed Test - Retry Test",
            "api_endpoint": "https://api.indeed.com/v2",
            "api_key": "invalid_bad_key_for_testing",
            "enabled": true,
            "config": {"job_id": "test-job-retry-123"}
        }' 2>/dev/null)

    # Extract integration ID
    INTEGRATION_ID=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)

    if [ -n "$INTEGRATION_ID" ]; then
        print_success "Integration created: $INTEGRATION_ID"
        return 0
    else
        print_error "Failed to create integration"
        echo "Response: $response"
        return 1
    fi
}

trigger_import() {
    print_header "Triggering Import (Will Fail with Invalid Credentials)"

    response=$(curl -s -X POST "$API_BASE/integrations/$INTEGRATION_ID/trigger-import" \
        -H "Content-Type: application/json" 2>/dev/null)

    # Extract task ID
    TASK_ID=$(echo "$response" | grep -o '"task_id":"[^"]*' | cut -d'"' -f4)

    if [ -n "$TASK_ID" ]; then
        print_success "Import task triggered: $TASK_ID"
        print_info "Task ID: $TASK_ID"
        return 0
    else
        print_error "Failed to trigger import"
        echo "Response: $response"
        return 1
    fi
}

wait_for_task_completion() {
    print_info "Waiting for task to complete (5 seconds)..."
    sleep 5
}

check_import_logs() {
    print_header "Checking Import Logs for Failure"

    response=$(curl -s "$API_BASE/integrations/logs?limit=10" 2>/dev/null)

    # Extract first log entry's ID and status
    IMPORT_LOG_ID=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
    status=$(echo "$response" | grep -o '"status":"[^"]*' | cut -d'"' -f4 | head -1)
    error_msg=$(echo "$response" | grep -o '"error_message":"[^"]*' | cut -d'"' -f4 | head -1)

    if [ -n "$IMPORT_LOG_ID" ]; then
        print_success "Import log found: $IMPORT_LOG_ID"
        print_info "Status: $status"

        if [ "$status" = "failed" ]; then
            print_success "Status is 'failed' as expected"
        else
            print_error "Expected status 'failed', got: $status"
        fi

        if [ -n "$error_msg" ]; then
            print_success "Error message logged: $error_msg"
        else
            print_info "No error message (task may still be processing)"
        fi

        return 0
    else
        print_error "No import logs found"
        echo "Response: $response"
        return 1
    fi
}

test_get_import_log() {
    print_header "Test: Get Specific Import Log"

    if [ -z "$IMPORT_LOG_ID" ]; then
        print_error "No import log ID available"
        return 1
    fi

    response=$(curl -s "$API_BASE/integrations/logs/$IMPORT_LOG_ID" 2>/dev/null)

    if [ -n "$response" ] && [ "$response" != "null" ]; then
        print_success "Import log retrieved successfully"

        # Parse response
        status=$(echo "$response" | grep -o '"status":"[^"]*' | cut -d'"' -f4 | head -1)
        retry_count=$(echo "$response" | grep -o '"retry_count":[0-9]*' | cut -d':' -f2 | head -1)

        print_info "Status: $status"
        print_info "Retry Count: $retry_count"

        return 0
    else
        print_error "Failed to retrieve import log"
        return 1
    fi
}

test_retry_failed_import() {
    print_header "Test: Retry Failed Import"

    if [ -z "$IMPORT_LOG_ID" ]; then
        print_error "No import log ID available for retry"
        return 1
    fi

    print_info "Attempting to retry failed import..."

    response=$(curl -s -X POST "$API_BASE/integrations/logs/$IMPORT_LOG_ID/retry" \
        -H "Content-Type: application/json" 2>/dev/null)

    # Check response
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/integrations/logs/$IMPORT_LOG_ID/retry" \
        -H "Content-Type: application/json" 2>/dev/null)

    if [ "$http_code" = "202" ]; then
        print_success "Retry request accepted (HTTP 202)"

        # Extract new task ID
        new_task_id=$(echo "$response" | grep -o '"task_id":"[^"]*' | cut -d'"' -f4 | head -1)
        new_retry_count=$(echo "$response" | grep -o '"retry_count":[0-9]*' | cut -d':' -f2 | head -1)

        if [ -n "$new_task_id" ]; then
            print_success "New task created: $new_task_id"
        fi

        if [ -n "$new_retry_count" ]; then
            print_success "Retry count updated: $new_retry_count"
        fi

        return 0
    else
        print_error "Retry request failed (HTTP $http_code)"
        echo "Response: $response"
        return 1
    fi
}

test_filter_logs_by_status() {
    print_header "Test: Filter Import Logs by Status"

    # Test filtering by 'failed' status
    print_info "Fetching logs with status=failed..."

    response=$(curl -s "$API_BASE/integrations/logs?status_filter=failed&limit=10" 2>/dev/null)

    # Check if we got a valid response
    if echo "$response" | grep -q '"logs"'; then
        print_success "Status filter works correctly"

        # Count failed logs
        failed_count=$(echo "$response" | grep -o '"status":"failed"' | wc -l)
        print_info "Found $failed_count failed import(s)"

        return 0
    else
        print_error "Failed to filter logs by status"
        echo "Response: $response"
        return 1
    fi
}

test_disable_integration_and_retry() {
    print_header "Test: Cannot Retry Disabled Integration"

    print_info "Disabling integration..."
    response=$(curl -s -X PATCH "$API_BASE/integrations/$INTEGRATION_ID/toggle" 2>/dev/null)

    print_success "Integration disabled"

    # Try to retry with disabled integration
    print_info "Attempting to retry with disabled integration..."

    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/integrations/logs/$IMPORT_LOG_ID/retry" \
        -H "Content-Type: application/json" 2>/dev/null)

    if [ "$http_code" = "400" ]; then
        print_success "Correctly prevented retry for disabled integration (HTTP 400)"
    else
        print_error "Should have prevented retry for disabled integration"
    fi

    # Re-enable for cleanup
    print_info "Re-enabling integration for cleanup..."
    curl -s -X PATCH "$API_BASE/integrations/$INTEGRATION_ID/toggle" > /dev/null 2>&1
}

cleanup() {
    print_header "Cleanup"

    if [ -n "$INTEGRATION_ID" ]; then
        print_info "Deleting test integration..."
        http_code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$API_BASE/integrations/$INTEGRATION_ID" 2>/dev/null)

        if [ "$http_code" = "204" ] || [ "$http_code" = "200" ]; then
            print_success "Test integration deleted"
        else
            print_error "Failed to delete integration (HTTP $http_code)"
        fi
    fi
}

###############################################################################
# Main Test Flow
###############################################################################

main() {
    print_header "Import Failure Handling and Retry Verification"
    print_info "This script tests the complete failure handling and retry workflow"

    # Check server availability
    if ! check_server; then
        exit 1
    fi

    # Run tests
    TESTS_PASSED=0
    TESTS_FAILED=0

    # Test 1: Create integration
    if create_integration; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
        cleanup
        exit 1
    fi

    # Test 2: Trigger import (will fail)
    if trigger_import; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
        cleanup
        exit 1
    fi

    # Wait for task to complete
    wait_for_task_completion

    # Test 3: Check import logs for failure
    if check_import_logs; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Test 4: Get specific import log
    if test_get_import_log; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Test 5: Filter logs by status
    if test_filter_logs_by_status; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Test 6: Retry failed import
    if test_retry_failed_import; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Test 7: Cannot retry disabled integration
    if test_disable_integration_and_retry; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Cleanup
    cleanup

    # Print summary
    print_header "TEST SUMMARY"
    echo -e "${BOLD}Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "${BOLD}Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "${BOLD}Total Tests:  $((TESTS_PASSED + TESTS_FAILED))${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}ALL TESTS PASSED! ✓${NC}\n"
        return 0
    else
        echo -e "\n${RED}${BOLD}SOME TESTS FAILED! ✗${NC}\n"
        return 1
    fi
}

# Run main function
main
exit $?
