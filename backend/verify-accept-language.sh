#!/bin/bash
# Verification script for Accept-Language header support in backend error messages
# This script tests that backend API endpoints properly respect the Accept-Language header

set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
UPLOAD_URL="${API_BASE_URL}/api/resumes/upload"

echo "=========================================="
echo "Backend Accept-Language Header Verification"
echo "=========================================="
echo "API Base URL: $API_BASE_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if backend is running
check_backend() {
    echo "Checking if backend is running..."
    if curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/health" | grep -q "200\|404"; then
        echo -e "${GREEN}✓ Backend is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Backend is not accessible${NC}"
        echo "Please start the backend first:"
        echo "  cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        return 1
    fi
}

# Function to test error message in specific language
test_error_message() {
    local lang_code="$1"
    local lang_name="$2"
    local expected_keyword="$3"

    echo ""
    echo "Testing $lang_name error message (Accept-Language: $lang_code)..."

    # Create a temporary test file with invalid extension
    local tmpfile=$(mktemp)
    echo "test content" > "$tmpfile.txt"

    # Make request with Accept-Language header
    response=$(curl -s -X POST "$UPLOAD_URL" \
        -F "file=@$tmpfile.txt" \
        -H "Accept-Language: $lang_code" \
        -w "\n%{http_code}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    rm -f "$tmpfile" "$tmpfile.txt"

    # Check response
    if [ "$http_code" = "415" ]; then
        echo -e "  Status Code: $http_code ${GREEN}✓${NC}"
        echo "  Response: $body"

        if echo "$body" | grep -q "$expected_keyword"; then
            echo -e "  ${GREEN}✓ Error message is in $lang_name${NC}"
            return 0
        else
            echo -e "  ${RED}✗ Error message is NOT in $lang_name${NC}"
            echo "  Expected keyword: $expected_keyword"
            return 1
        fi
    else
        echo -e "  ${RED}✗ Unexpected status code: $http_code (expected 415)${NC}"
        echo "  Response: $body"
        return 1
    fi
}

# Function to test file size error with parameter interpolation
test_file_size_error() {
    local lang_code="$1"
    local lang_name="$2"
    local expected_keyword="$3"

    echo ""
    echo "Testing $lang_name file size error (Accept-Language: $lang_code)..."

    # Create a large test file (6MB)
    local tmpfile=$(mktemp)
    dd if=/dev/zero of="$tmpfile" bs=1M count=6 2>/dev/null

    # Make request with Accept-Language header
    response=$(curl -s -X POST "$UPLOAD_URL" \
        -F "file=@$tmpfile" \
        -H "Accept-Language: $lang_code" \
        -w "\n%{http_code}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    rm -f "$tmpfile"

    # Check response
    if [ "$http_code" = "413" ]; then
        echo -e "  Status Code: $http_code ${GREEN}✓${NC}"
        echo "  Response: $body"

        if echo "$body" | grep -q "$expected_keyword"; then
            echo -e "  ${GREEN}✓ Error message in $lang_name with parameter interpolation${NC}"
            return 0
        else
            echo -e "  ${RED}✗ Error message missing expected text${NC}"
            echo "  Expected keyword: $expected_keyword"
            return 1
        fi
    else
        echo -e "  ${RED}✗ Unexpected status code: $http_code (expected 413)${NC}"
        echo "  Response: $body"
        return 1
    fi
}

# Main verification
main() {
    # Check backend availability
    if ! check_backend; then
        exit 2
    fi

    echo ""
    echo "=========================================="
    echo "Running Verification Tests"
    echo "=========================================="

    local passed=0
    local failed=0

    # Test 1: English error message
    echo ""
    echo "--- Test 1: English Error Message ---"
    if test_error_message "en" "English" "Unsupported"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Test 2: Russian error message
    echo ""
    echo "--- Test 2: Russian Error Message ---"
    if test_error_message "ru" "Russian" "Неподдерживаемый"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Test 3: English file size error
    echo ""
    echo "--- Test 3: English File Size Error ---"
    if test_file_size_error "en" "English" "exceeds maximum"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Test 4: Russian file size error
    echo ""
    echo "--- Test 4: Russian File Size Error ---"
    if test_file_size_error "ru" "Russian" "превышает"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Test 5: Default language (no Accept-Language header)
    echo ""
    echo "--- Test 5: Default Language (No Header) ---"
    echo "Testing default error message (no Accept-Language header)..."

    tmpfile=$(mktemp)
    echo "test content" > "$tmpfile.txt"

    response=$(curl -s -X POST "$UPLOAD_URL" \
        -F "file=@$tmpfile.txt" \
        -w "\n%{http_code}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    rm -f "$tmpfile" "$tmpfile.txt"

    if [ "$http_code" = "415" ]; then
        echo -e "  Status Code: $http_code ${GREEN}✓${NC}"
        echo "  Response: $body"

        if echo "$body" | grep -q "Unsupported"; then
            echo -e "  ${GREEN}✓ Default language is English${NC}"
            ((passed++))
        else
            echo -e "  ${RED}✗ Default language is not English${NC}"
            ((failed++))
        fi
    else
        echo -e "  ${RED}✗ Unexpected status code: $http_code (expected 415)${NC}"
        ((failed++))
    fi

    # Print summary
    echo ""
    echo "=========================================="
    echo "Verification Summary"
    echo "=========================================="
    echo "Tests Passed: $passed"
    echo "Tests Failed: $failed"
    echo ""

    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
        echo "Backend properly respects Accept-Language header"
        exit 0
    else
        echo -e "${RED}✗ SOME TESTS FAILED${NC}"
        exit 1
    fi
}

# Run main function
main
