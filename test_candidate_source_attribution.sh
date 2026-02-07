#!/bin/bash

# Test Script for Candidate Source Attribution Analytics Endpoint
# This script tests the /api/analytics/candidate-source-attribution endpoint
# with various scenarios and validates the response metrics.

set -e

BASE_URL="http://localhost:8000"
ENDPOINT="/api/analytics/candidate-source-attribution"
FULL_URL="${BASE_URL}${ENDPOINT}"

echo "=========================================="
echo "Candidate Source Attribution Endpoint Test"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Function to test endpoint
test_endpoint() {
    local test_name="$1"
    local url="$2"
    local expected_status="$3"
    local description="$4"

    echo ""
    echo "Test: ${test_name}"
    echo "Description: ${description}"
    echo "URL: ${url}"

    response=$(curl -s -w "\n%{http_code}" "${url}")
    http_code=$(echo "${response}" | tail -n1)
    body=$(echo "${response}" | sed '$d')

    if [ "${http_code}" -eq "${expected_status}" ]; then
        print_result 0 "${test_name} - HTTP ${http_code}"

        # If successful, validate response structure
        if [ "${http_code}" == "200" ]; then
            validate_response_structure "${body}" "${test_name}"
        fi
    else
        print_result 1 "${test_name} - Expected ${expected_status}, got ${http_code}"
        echo "Response: ${body}"
    fi
}

# Function to validate response structure
validate_response_structure() {
    local body="$1"
    local test_name="$2"

    # Check if response is valid JSON
    if ! echo "${body}" | jq empty 2>/dev/null; then
        print_result 1 "${test_name} - Invalid JSON response"
        echo "Response: ${body}"
        return
    fi

    # Validate required fields
    has_sources=$(echo "${body}" | jq -r '.sources != null')
    has_total=$(echo "${body}" | jq -r '.total_candidates != null')
    has_date_range=$(echo "${body}" | jq -r '.date_range != null')

    if [ "${has_sources}" == "true" ] && [ "${has_total}" == "true" ] && [ "${has_date_range}" == "true" ]; then
        print_result 0 "${test_name} - Response structure valid"

        # Validate sources array
        validate_sources "${body}" "${test_name}"
    else
        print_result 1 "${test_name} - Missing required fields"
        echo "Sources: ${has_sources}, Total: ${has_total}, DateRange: ${has_date_range}"
    fi
}

# Function to validate sources array
validate_sources() {
    local body="$1"
    local test_name="$2"

    local sources_count=$(echo "${body}" | jq -r '.sources | length')
    local total_candidates=$(echo "${body}" | jq -r '.total_candidates')

    echo "  Sources found: ${sources_count}"
    echo "  Total candidates: ${total_candidates}"

    # Validate each source has required fields
    echo "${body}" | jq -r '.sources[] | @json' | while IFS= read -r source; do
        source_name=$(echo "${source}" | jq -r '.source')
        candidate_count=$(echo "${source}" | jq -r '.candidate_count')
        hired_count=$(echo "${source}" | jq -r '.hired_count')
        conversion_rate=$(echo "${source}" | jq -r '.conversion_rate')
        avg_time_to_hire=$(echo "${source}" | jq -r '.average_time_to_hire_days')
        stage_dist_count=$(echo "${source}" | jq -r '.stage_distribution | length')

        echo "  - Source: ${source_name}"
        echo "    Candidates: ${candidate_count}, Hired: ${hired_count}"
        echo "    Conversion Rate: ${conversion_rate}"
        echo "    Avg Time-to-Hire: ${avg_time_to_hire} days"
        echo "    Stage Distribution entries: ${stage_dist_count}"

        # Validate conversion rate calculation
        if [ "${candidate_count}" -gt 0 ]; then
            expected_rate=$(awk "BEGIN {print ${hired_count} / ${candidate_count}}")
            actual_rate=$(echo "${conversion_rate}" | awk '{printf "%.3f", $1}')

            # Use approximate comparison for floating point
            rate_diff=$(awk "BEGIN {print (${expected_rate} > ${actual_rate} ? ${expected_rate} - ${actual_rate} : ${actual_rate} - ${expected_rate})}")
            rate_diff=$(awk "BEGIN {print (${rate_diff} < 0.001 ? 0 : 1)}")

            if [ "${rate_diff}" -eq 0 ]; then
                print_result 0 "${test_name} - ${source_name} conversion rate correct (${hired_count}/${candidate_count} = ${conversion_rate})"
            else
                print_result 1 "${test_name} - ${source_name} conversion rate incorrect (expected ~${expected_rate}, got ${conversion_rate})"
            fi
        fi

        # Validate stage distribution percentages sum to approximately 1.0
        if [ "${stage_dist_count}" -gt 0 ]; then
            total_percentage=$(echo "${source}" | jq -r '[.stage_distribution[].percentage] | add')

            # Allow small rounding error
            sum_valid=$(awk "BEGIN {print (${total_percentage} >= 0.99 && ${total_percentage} <= 1.01) ? 1 : 0}")

            if [ "${sum_valid}" -eq 1 ]; then
                print_result 0 "${test_name} - ${source_name} stage distribution percentages sum to ${total_percentage} (valid)"
            else
                print_result 1 "${test_name} - ${source_name} stage distribution percentages sum to ${total_percentage} (should be ~1.0)"
            fi
        fi
    done
}

# ============================================
# TEST 1: Basic endpoint call (no filters)
# ============================================
echo -e "${YELLOW}===========================================${NC}"
echo -e "${YELLOW}TEST SUITE 1: Basic Endpoint Test${NC}"
echo -e "${YELLOW}===========================================${NC}"

test_endpoint \
    "Basic Request" \
    "${FULL_URL}" \
    200 \
    "Test basic endpoint without any filters"

# ============================================
# TEST 2: Date range filtering
# ============================================
echo ""
echo -e "${YELLOW}===========================================${NC}"
echo -e "${YELLOW}TEST SUITE 2: Date Range Filtering${NC}"
echo -e "${YELLOW}===========================================${NC}"

test_endpoint \
    "Start Date Only" \
    "${FULL_URL}?start_date=2024-01-01" \
    200 \
    "Test with start_date filter only"

test_endpoint \
    "End Date Only" \
    "${FULL_URL}?end_date=2024-12-31" \
    200 \
    "Test with end_date filter only"

test_endpoint \
    "Date Range" \
    "${FULL_URL}?start_date=2024-01-01&end_date=2024-12-31" \
    200 \
    "Test with both start_date and end_date filters"

test_endpoint \
    "ISO 8601 Date Format" \
    "${FULL_URL}?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z" \
    200 \
    "Test with ISO 8601 datetime format"

# ============================================
# TEST 3: Invalid date formats
# ============================================
echo ""
echo -e "${YELLOW}===========================================${NC}"
echo -e "${YELLOW}TEST SUITE 3: Error Handling${NC}"
echo -e "${YELLOW}===========================================${NC}"

test_endpoint \
    "Invalid Start Date" \
    "${FULL_URL}?start_date=invalid-date" \
    400 \
    "Test with invalid start_date format (should return 400)"

test_endpoint \
    "Invalid End Date" \
    "${FULL_URL}?end_date=2024-13-45" \
    400 \
    "Test with invalid end_date format (should return 400)"

test_endpoint \
    "Invalid Date Format" \
    "${FULL_URL}?start_date=not-a-date" \
    400 \
    "Test with malformed date (should return 400)"

# ============================================
# TEST 4: Edge cases
# ============================================
echo ""
echo -e "${YELLOW}===========================================${NC}"
echo -e "${YELLOW}TEST SUITE 4: Edge Cases${NC}"
echo -e "${YELLOW}===========================================${NC}"

test_endpoint \
    "Same Start and End Date" \
    "${FULL_URL}?start_date=2024-06-15&end_date=2024-06-15" \
    200 \
    "Test with same start and end date"

test_endpoint \
    "Future Date Range" \
    "${FULL_URL}?start_date=2025-01-01&end_date=2025-12-31" \
    200 \
    "Test with future date range (may return empty data)"

test_endpoint \
    "Past Date Range" \
    "${FULL_URL}?start_date=2020-01-01&end_date=2020-12-31" \
    200 \
    "Test with past date range (may return empty data)"

# ============================================
# TEST 5: Data validation
# ============================================
echo ""
echo -e "${YELLOW}===========================================${NC}"
echo -e "${YELLOW}TEST SUITE 5: Data Validation${NC}"
echo -e "${YELLOW}===========================================${NC}"

echo ""
echo "Running detailed data validation..."
response=$(curl -s "${FULL_URL}")

# Check if response is valid JSON
if echo "${response}" | jq empty 2>/dev/null; then
    print_result 0 "Response is valid JSON"

    # Check for sources array
    sources_count=$(echo "${response}" | jq -r '.sources | length')
    echo "Total sources: ${sources_count}"

    if [ "${sources_count}" -gt 0 ]; then
        print_result 0 "Data available - ${sources_count} source(s) found"

        # Display summary
        echo ""
        echo "Source Summary:"
        echo "${response}" | jq -r '.sources[] | "  - \(.source): \(.candidate_count) candidates, \(.hired_count) hired (\(.conversion_rate * 100)% conversion)"'

        # Validate total candidates
        calculated_total=$(echo "${response}" | jq '[.sources[].candidate_count] | add')
        reported_total=$(echo "${response}" | jq -r '.total_candidates')

        if [ "${calculated_total}" == "${reported_total}" ]; then
            print_result 0 "Total candidates matches sum of source counts (${reported_total})"
        else
            print_result 1 "Total candidates mismatch - calculated: ${calculated_total}, reported: ${reported_total}"
        fi
    else
        print_result 1 "No data available - endpoint returned empty sources array"
        echo "Note: This may be expected if no resume_uploaded events exist in database"
    fi
else
    print_result 1 "Response is not valid JSON"
    echo "Response: ${response}"
fi

# ============================================
# TEST SUMMARY
# ============================================
echo ""
echo -e "${YELLOW}===========================================${NC}"
echo -e "${YELLOW}TEST SUMMARY${NC}"
echo -e "${YELLOW}===========================================${NC}"
echo ""
echo -e "${GREEN}Tests Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Tests Failed: ${TESTS_FAILED}${NC}"
echo ""

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi
