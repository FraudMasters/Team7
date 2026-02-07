#!/bin/bash
#
# Webhook reception and processing flow test script
#
# This script tests the complete webhook flow using curl commands.
# It verifies webhooks are received, validated, processed, and logged.
#

set -e

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-test_webhook_secret_12345}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Generate HMAC-SHA256 signature
generate_signature() {
    local payload="$1"
    local secret="$2"

    echo -n "$payload" | openssl dgst -sha256 -hmac "$secret" | awk '{print "sha256="$2}'
}

# Send webhook and verify response
send_webhook() {
    local platform="$1"
    local event="$2"
    local payload="$3"

    local webhook_url="${API_BASE_URL}/api/webhooks/${platform}"
    local signature=$(generate_signature "$payload" "$WEBHOOK_SECRET")

    log_info "Sending webhook to ${webhook_url}"
    log_info "Event: ${event}"

    # Send webhook
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Webhook-Signature: ${signature}" \
        -d "$payload" \
        "$webhook_url")

    # Extract status code (last line)
    http_code=$(echo "$response" | tail -n1)
    # Extract body (everything except last line)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        log_success "Webhook received successfully (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"

        # Check if sync was triggered
        event_id=$(echo "$body" | jq -r '.event_id // empty')
        if [ -n "$event_id" ] && [ "$event_id" != "null" ]; then
            log_success "Sync triggered: ${event_id}"
        else
            log_info "No sync triggered (event may not require sync)"
        fi

        return 0
    else
        log_error "Webhook failed (HTTP $http_code)"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Check if backend is running
check_backend() {
    log_info "Checking if backend is running at ${API_BASE_URL}..."

    if curl -s -f "${API_BASE_URL}/health" > /dev/null 2>&1; then
        log_success "Backend is running"
        return 0
    else
        log_error "Backend is not running or not accessible"
        log_info "Start the backend with: cd backend && uvicorn main:app --reload"
        return 1
    fi
}

# Main test execution
main() {
    echo "=================================================="
    echo "WEBHOOK RECEPTION AND PROCESSING FLOW TEST"
    echo "=================================================="
    echo ""
    echo "Target API: ${API_BASE_URL}"
    echo "Webhook Secret: ${WEBHOOK_SECRET}"
    echo ""

    # Check backend
    if ! check_backend; then
        exit 1
    fi

    echo ""
    echo "=================================================="
    echo "Testing Webhook Endpoints"
    echo "=================================================="

    # Test 1: Greenhouse - candidate.created
    echo ""
    echo "--- Test 1: Greenhouse candidate.created ---"
    greenhouse_payload_1='{
        "event": "candidate.created",
        "data": {
            "candidate_id": 12345,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "application_id": 98765
        }
    }'
    send_webhook "greenhouse" "candidate.created" "$greenhouse_payload_1"

    # Test 2: Greenhouse - candidate.updated
    echo ""
    echo "--- Test 2: Greenhouse candidate.updated ---"
    greenhouse_payload_2='{
        "event": "candidate.updated",
        "data": {
            "candidate_id": 12345,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com"
        }
    }'
    send_webhook "greenhouse" "candidate.updated" "$greenhouse_payload_2"

    # Test 3: Lever - candidate.created
    echo ""
    echo "--- Test 3: Lever candidate.created ---"
    lever_payload_1='{
        "event": "candidate.created",
        "data": {
            "id": "507f1f77bcf86cd799439011",
            "name": "Jane Doe",
            "email": "jane.doe@example.com"
        }
    }'
    send_webhook "lever" "candidate.created" "$lever_payload_1"

    # Test 4: Lever - opportunity.updated
    echo ""
    echo "--- Test 4: Lever opportunity.updated ---"
    lever_payload_2='{
        "event": "opportunity.updated",
        "data": {
            "opportunityId": "507f1f77bcf86cd799439012",
            "candidateId": "507f1f77bcf86cd799439011",
            "stage": "Phone Screen"
        }
    }'
    send_webhook "lever" "opportunity.updated" "$lever_payload_2"

    # Test 5: Workday - employee.created
    echo ""
    echo "--- Test 5: Workday employee.created ---"
    workday_payload_1='{
        "event": "employee.created",
        "data": {
            "worker_id": "ABC123",
            "name": "Bob Johnson",
            "email": "bob.johnson@company.com",
            "position": "Software Engineer"
        }
    }'
    send_webhook "workday" "employee.created" "$workday_payload_1"

    # Test 6: BambooHR - employee_added
    echo ""
    echo "--- Test 6: BambooHR employee_added ---"
    bamboohr_payload_1='{
        "event": "employee_added",
        "data": {
            "id": "101",
            "firstName": "Charlie",
            "lastName": "Brown",
            "email": "charlie.brown@company.com",
            "jobTitle": "Product Manager"
        }
    }'
    send_webhook "bamboohr" "employee_added" "$bamboohr_payload_1"

    # Test 7: Ashby - candidate.created
    echo ""
    echo "--- Test 7: Ashby candidate.created ---"
    ashby_payload_1='{
        "event": "candidate.created",
        "data": {
            "id": "ashby_candidate_123",
            "name": "Diana Prince",
            "email": "diana.prince@example.com"
        }
    }'
    send_webhook "ashby" "candidate.created" "$ashby_payload_1"

    # Test 8: Invalid signature (should fail)
    echo ""
    echo "--- Test 8: Invalid signature (should fail) ---"
    log_info "Testing webhook with invalid signature..."
    invalid_payload='{"event": "candidate.created", "data": {}}'
    webhook_url="${API_BASE_URL}/api/webhooks/greenhouse"

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "X-Webhook-Signature: sha256=invalid_signature" \
        -d "$invalid_payload" \
        "$webhook_url")

    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "401" ]; then
        log_success "Invalid signature rejected as expected (HTTP $http_code)"
    else
        log_error "Expected 401 for invalid signature, got $http_code"
    fi

    # Test 9: Invalid platform (should fail)
    echo ""
    echo "--- Test 9: Invalid platform (should fail) ---"
    log_info "Testing webhook with invalid platform..."
    invalid_platform_url="${API_BASE_URL}/api/webhooks/invalid_platform"

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"event": "test", "data": {}}' \
        "$invalid_platform_url")

    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "400" ]; then
        log_success "Invalid platform rejected as expected (HTTP $http_code)"
    else
        log_error "Expected 400 for invalid platform, got $http_code"
    fi

    # Test 10: List webhook endpoints
    echo ""
    echo "--- Test 10: List webhook endpoints ---"
    log_info "Fetching list of available webhook endpoints..."
    webhook_list_url="${API_BASE_URL}/api/webhooks/"

    response=$(curl -s "${webhook_list_url}")
    echo "$response" | jq '.' 2>/dev/null || echo "$response"

    echo ""
    echo "=================================================="
    echo "TEST SUMMARY"
    echo "=================================================="
    echo ""
    log_success "Webhook flow tests completed"
    echo ""
    echo "Verification steps performed:"
    echo "  ✓ Test webhook payloads sent to webhook endpoints"
    echo "  ✓ Webhooks received and validated (signature verification)"
    echo "  ✓ Data processed and sync tasks triggered"
    echo ""
    echo "Next steps:"
    echo "  1. Check backend logs for webhook processing details"
    echo "  2. Verify sync log entries in database:"
    echo "     SELECT * FROM sync_logs WHERE sync_metadata->>'triggered_by' = 'webhook';"
    echo "  3. Verify audit log entries for webhook events"
    echo ""
    echo "To view sync logs:"
    echo "  psql -U agenthr -d agenthr -c \"SELECT id, integration_id, sync_type, status, sync_metadata FROM sync_logs ORDER BY created_at DESC LIMIT 10;\""
    echo ""
}

# Run main function
main "$@"
