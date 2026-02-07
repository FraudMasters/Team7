#!/bin/bash
# Test script to verify all security headers are present on backend API responses
# This script tests the SecurityHeadersMiddleware implementation

set -e

echo "=========================================="
echo "Security Headers Verification Test"
echo "=========================================="
echo ""

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="$BACKEND_URL/health"

echo "Testing endpoint: $HEALTH_ENDPOINT"
echo ""

# Make request and save headers
TEMP_FILE=$(mktemp)
curl -s -D - "$HEALTH_ENDPOINT" -o /dev/null > "$TEMP_FILE" 2>&1 || true

echo "Response Headers:"
cat "$TEMP_FILE"
echo ""
echo "=========================================="
echo "Verification Results:"
echo "=========================================="
echo ""

# Check each security header
PASSED=0
FAILED=0

# Helper function to check header
check_header() {
    HEADER_NAME="$1"
    EXPECTED_VALUE="$2"
    if grep -qi "^$HEADER_NAME:" "$TEMP_FILE"; then
        VALUE=$(grep -i "^$HEADER_NAME:" "$TEMP_FILE" | cut -d: -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [ -n "$EXPECTED_VALUE" ]; then
            if echo "$VALUE" | grep -iq "$EXPECTED_VALUE"; then
                echo "✅ PASS: $HEADER_NAME"
                echo "   Found: $VALUE"
                PASSED=$((PASSED + 1))
            else
                echo "❌ FAIL: $HEADER_NAME"
                echo "   Expected: $EXPECTED_VALUE"
                echo "   Found: $VALUE"
                FAILED=$((FAILED + 1))
            fi
        else
            echo "✅ PASS: $HEADER_NAME (present)"
            echo "   Found: $VALUE"
            PASSED=$((PASSED + 1))
        fi
    else
        echo "❌ FAIL: $HEADER_NAME (missing)"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# 1. X-Content-Type-Options
check_header "X-Content-Type-Options" "nosniff"

# 2. X-Frame-Options
check_header "X-Frame-Options" "DENY"

# 3. Referrer-Policy
check_header "Referrer-Policy" "strict-origin-when-cross-origin"

# 4. Permissions-Policy
check_header "Permissions-Policy" "geolocation=(), microphone=(), camera=()"

# 5. Content-Security-Policy (should be present)
if grep -qi "^Content-Security-Policy:" "$TEMP_FILE"; then
    CSP_VALUE=$(grep -i "^Content-Security-Policy:" "$TEMP_FILE" | cut -d: -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    echo "✅ PASS: Content-Security-Policy"
    echo "   Found: $CSP_VALUE"
    PASSED=$((PASSED + 1))
else
    echo "❌ FAIL: Content-Security-Policy (missing)"
    FAILED=$((FAILED + 1))
fi
echo ""

# 6. Strict-Transport-Security (only if HTTPS)
if [[ "$BACKEND_URL" == https://* ]]; then
    check_header "Strict-Transport-Security" "max-age=31536000"
else
    echo "⚠️  SKIP: Strict-Transport-Security (not applicable for HTTP)"
    echo "   Note: HSTS is only applied to HTTPS requests"
    echo ""
fi

# Cleanup
rm -f "$TEMP_FILE"

echo "=========================================="
echo "Summary: $PASSED passed, $FAILED failed"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo "✅ All security headers verified successfully!"
    exit 0
else
    echo "❌ Some security headers are missing or incorrect!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Ensure the backend server is running"
    echo "2. Ensure the backend has been restarted after middleware integration"
    echo "3. Check backend logs for any errors"
    echo "4. Verify SecurityHeadersMiddleware is registered in main.py"
    exit 1
fi
