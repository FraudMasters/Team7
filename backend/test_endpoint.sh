#!/bin/bash
# Bash script to test candidate source attribution endpoint
# This script validates the endpoint using curl and basic text processing

set -e

# Configuration
BASE_URL="http://localhost:8000"
ENDPOINT="/api/analytics/candidate-source-attribution"
FULL_URL="${BASE_URL}${ENDPOINT}"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Functions
print_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if server is running
check_server() {
    print_section "Checking Server Status"

    if curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
        print_success "Backend server is running"
        return 0
    else
        print_error "Backend server is not running!"
        print_info "Start server with: cd backend && python -m uvicorn main:app --reload"
        return 1
    fi
}

# Test 1: Endpoint Availability
test_endpoint_exists() {
    print_section "TEST 1: Endpoint Availability"

    STATUS=$(curl -s -w "%{http_code}" -o /tmp/test_response.json "${FULL_URL}")

    if [ "$STATUS" = "200" ]; then
        print_success "Endpoint is accessible (HTTP 200)"
        return 0
    else
        print_error "Endpoint returned HTTP $STATUS"
        cat /tmp/test_response.json
        return 1
    fi
}

# Test 2: Response Structure
test_response_structure() {
    print_section "TEST 2: Response Structure Validation"

    curl -s "${FULL_URL}" > /tmp/test_response.json

    # Check if response is valid JSON
    if ! jq empty /tmp/test_response.json 2>/dev/null; then
        print_error "Response is not valid JSON"
        return 1
    fi

    print_success "Response is valid JSON"

    # Check for required fields
    if jq -e '.sources' /tmp/test_response.json > /dev/null; then
        print_success "Field 'sources' exists"
    else
        print_error "Field 'sources' missing"
        return 1
    fi

    if jq -e '.total_candidates' /tmp/test_response.json > /dev/null; then
        print_success "Field 'total_candidates' exists"
    else
        print_error "Field 'total_candidates' missing"
        return 1
    fi

    if jq -e '.date_range' /tmp/test_response.json > /dev/null; then
        print_success "Field 'date_range' exists"
    else
        print_error "Field 'date_range' missing"
        return 1
    fi

    # Check data types
    SOURCES_TYPE=$(jq -r '.sources | type' /tmp/test_response.json)
    if [ "$SOURCES_TYPE" = "array" ]; then
        print_success "Field 'sources' is an array"
    else
        print_error "Field 'sources' is not an array (type: $SOURCES_TYPE)"
        return 1
    fi

    TOTAL_TYPE=$(jq -r '.total_candidates | type' /tmp/test_response.json)
    if [ "$TOTAL_TYPE" = "number" ]; then
        print_success "Field 'total_candidates' is a number"
    else
        print_error "Field 'total_candidates' is not a number (type: $TOTAL_TYPE)"
        return 1
    fi

    return 0
}

# Test 3: Source Entry Structure
test_source_structure() {
    print_section "TEST 3: Source Entry Structure"

    curl -s "${FULL_URL}" > /tmp/test_response.json

    SOURCE_COUNT=$(jq '.sources | length' /tmp/test_response.json)

    if [ "$SOURCE_COUNT" -eq 0 ]; then
        print_info "No sources in response (empty dataset)"
        return 0
    fi

    print_success "Found $SOURCE_COUNT source(s)"

    # Check first source structure
    FIRST_SOURCE=$(jq '.sources[0]' /tmp/test_response.json)

    REQUIRED_FIELDS=("source" "candidate_count" "hired_count" "conversion_rate" "average_time_to_hire_days" "stage_distribution")

    for field in "${REQUIRED_FIELDS[@]}"; do
        if echo "$FIRST_SOURCE" | jq -e ".$field" > /dev/null; then
            print_success "Source has field '$field'"
        else
            print_error "Source missing field '$field'"
            return 1
        fi
    done

    # Validate field types
    SOURCE_TYPE=$(echo "$FIRST_SOURCE" | jq -r '.source | type')
    if [ "$SOURCE_TYPE" = "string" ]; then
        print_success "Field 'source' is a string"
    else
        print_error "Field 'source' is not a string"
        return 1
    fi

    CANDIDATE_COUNT=$(echo "$FIRST_SOURCE" | jq '.candidate_count')
    if [ "$CANDIDATE_COUNT" -ge 0 ] 2>/dev/null; then
        print_success "Field 'candidate_count' is non-negative"
    else
        print_error "Field 'candidate_count' is invalid: $CANDIDATE_COUNT"
        return 1
    fi

    HIRED_COUNT=$(echo "$FIRST_SOURCE" | jq '.hired_count')
    if [ "$HIRED_COUNT" -ge 0 ] 2>/dev/null; then
        print_success "Field 'hired_count' is non-negative"
    else
        print_error "Field 'hired_count' is invalid: $HIRED_COUNT"
        return 1
    fi

    if [ "$HIRED_COUNT" -le "$CANDIDATE_COUNT" ]; then
        print_success "hired_count <= candidate_count"
    else
        print_error "hired_count ($HIRED_COUNT) > candidate_count ($CANDIDATE_COUNT)"
        return 1
    fi

    CONVERSION_RATE=$(echo "$FIRST_SOURCE" | jq '.conversion_rate')
    if (( $(echo "$CONVERSION_RATE >= 0" | bc -l) )) && (( $(echo "$CONVERSION_RATE <= 1" | bc -l) )); then
        print_success "conversion_rate is between 0 and 1"
    else
        print_error "conversion_rate is out of range: $CONVERSION_RATE"
        return 1
    fi

    return 0
}

# Test 4: Date Filtering
test_date_filtering() {
    print_section "TEST 4: Date Filtering"

    # Test valid date range
    STATUS=$(curl -s -w "%{http_code}" -o /tmp/test_response.json \
        "${FULL_URL}?start_date=2024-01-01&end_date=2024-12-31")

    if [ "$STATUS" = "200" ]; then
        print_success "Date filtering works with valid date range"
    else
        print_error "Date filtering failed with HTTP $STATUS"
        return 1
    fi

    # Test ISO 8601 format
    STATUS=$(curl -s -w "%{http_code}" -o /tmp/test_response.json \
        "${FULL_URL}?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z")

    if [ "$STATUS" = "200" ]; then
        print_success "Date filtering works with ISO 8601 format"
    else
        print_error "ISO 8601 format failed with HTTP $STATUS"
        return 1
    fi

    # Test invalid date format
    STATUS=$(curl -s -w "%{http_code}" -o /tmp/test_response.json \
        "${FULL_URL}?start_date=invalid-date")

    if [ "$STATUS" = "400" ] || [ "$STATUS" = "422" ]; then
        print_success "Invalid date format returns HTTP $STATUS (error)"
    else
        print_error "Invalid date format should return 400/422, got $STATUS"
        return 1
    fi

    return 0
}

# Test 5: Total Candidates Calculation
test_total_calculation() {
    print_section "TEST 5: Total Candidates Calculation"

    curl -s "${FULL_URL}" > /tmp/test_response.json

    REPORTED_TOTAL=$(jq '.total_candidates' /tmp/test_response.json)
    CALCULATED_TOTAL=$(jq '[.sources[].candidate_count] | add' /tmp/test_response.json)

    if [ "$REPORTED_TOTAL" -eq "$CALCULATED_TOTAL" ]; then
        print_success "total_candidates matches sum of source counts ($REPORTED_TOTAL)"
        return 0
    else
        print_error "total_candidates mismatch: reported=$REPORTED_TOTAL, calculated=$CALCULATED_TOTAL"
        return 1
    fi
}

# Test 6: Display Sample Data
display_sample_data() {
    print_section "SAMPLE DATA"

    curl -s "${FULL_URL}" > /tmp/test_response.json

    echo "Response:"
    jq '.' /tmp/test_response.json

    TOTAL=$(jq '.total_candidates' /tmp/test_response.json)
    SOURCE_COUNT=$(jq '.sources | length' /tmp/test_response.json)

    echo -e "\n${BLUE}Summary:${NC}"
    echo "Total Candidates: $TOTAL"
    echo "Number of Sources: $SOURCE_COUNT"

    if [ "$SOURCE_COUNT" -gt 0 ]; then
        echo -e "\n${BLUE}Top 3 Sources:${NC}"
        jq -r '.sources[:3] | .[] | "  - \(.source | ascii_upcase): \(.candidate_count) candidates, \(.hired_count) hired (\(.conversion_rate * 100)% conversion)"' /tmp/test_response.json
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}CANDIDATE SOURCE ATTRIBUTION TEST SUITE${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "\nTesting: $FULL_URL\n"

    # Check dependencies
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is required but not installed."
        echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
        exit 1
    fi

    if ! command -v bc &> /dev/null; then
        echo "Error: bc is required but not installed."
        echo "Install with: brew install bc (macOS) or apt-get install bc (Linux)"
        exit 1
    fi

    # Run tests
    check_server || exit 1
    test_endpoint_exists
    test_response_structure
    test_source_structure
    test_date_filtering
    test_total_calculation
    display_sample_data

    # Print summary
    print_section "TEST SUMMARY"
    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo "Total: $TOTAL_TESTS"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ ALL TESTS PASSED!${NC}\n"
        exit 0
    else
        echo -e "\n${RED}✗ SOME TESTS FAILED${NC}\n"
        exit 1
    fi
}

# Run main function
main "$@"
