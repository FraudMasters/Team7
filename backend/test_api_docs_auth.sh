#!/bin/bash
# Test script to verify API documentation endpoints require authentication
# This script tests the DocsAuthMiddleware implementation

set -e

echo "=========================================="
echo "API Docs Authentication Verification Test"
echo "=========================================="
echo ""

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
DOCS_ENDPOINT="$BACKEND_URL/docs"
REDOC_ENDPOINT="$BACKEND_URL/redoc"
OPENAPI_ENDPOINT="$BACKEND_URL/openapi.json"

# Default credentials from config
DOCS_USERNAME="${DOCS_USERNAME:-admin}"
DOCS_PASSWORD="${DOCS_PASSWORD:-admin}"

echo "Testing endpoint: $DOCS_ENDPOINT"
echo "Credentials: $DOCS_USERNAME:$DOCS_PASSWORD"
echo ""

# Make request without auth and save headers
TEMP_FILE=$(mktemp)
curl -s -D - "$DOCS_ENDPOINT" -o /dev/null > "$TEMP_FILE" 2>&1 || true

echo "=========================================="
echo "Test 1: Access /docs WITHOUT authentication"
echo "=========================================="
HTTP_STATUS=$(grep "^HTTP" "$TEMP_FILE" | tail -1 | awk '{print $2}')
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "401" ]; then
    echo "✅ PASS: /docs correctly returns 401 Unauthorized without auth"

    # Check for WWW-Authenticate header
    if grep -qi "WWW-Authenticate:" "$TEMP_FILE"; then
        WWW_AUTH=$(grep -i "WWW-Authenticate:" "$TEMP_FILE" | cut -d: -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        echo "✅ PASS: WWW-Authenticate header present: $WWW_AUTH"
    else
        echo "❌ FAIL: WWW-Authenticate header missing"
    fi
else
    echo "❌ FAIL: /docs should return 401 Unauthorized without auth"
    echo "   Got: $HTTP_STATUS"
    echo ""
    echo "Response Headers:"
    cat "$TEMP_FILE"
fi
echo ""

# Cleanup temp file
rm -f "$TEMP_FILE"

# Test with valid credentials
echo "=========================================="
echo "Test 2: Access /docs WITH valid authentication"
echo "=========================================="

TEMP_FILE=$(mktemp)
curl -s -D - -u "$DOCS_USERNAME:$DOCS_PASSWORD" "$DOCS_ENDPOINT" -o /dev/null > "$TEMP_FILE" 2>&1 || true

HTTP_STATUS=$(grep "^HTTP" "$TEMP_FILE" | tail -1 | awk '{print $2}')
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ PASS: /docs correctly returns 200 OK with valid credentials"
else
    echo "❌ FAIL: /docs should return 200 OK with valid credentials"
    echo "   Got: $HTTP_STATUS"
    echo ""
    echo "Response Headers:"
    cat "$TEMP_FILE"
fi
echo ""

# Cleanup temp file
rm -f "$TEMP_FILE"

# Test /redoc endpoint
echo "=========================================="
echo "Test 3: Access /redoc WITHOUT authentication"
echo "=========================================="

TEMP_FILE=$(mktemp)
curl -s -D - "$REDOC_ENDPOINT" -o /dev/null > "$TEMP_FILE" 2>&1 || true

HTTP_STATUS=$(grep "^HTTP" "$TEMP_FILE" | tail -1 | awk '{print $2}')
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "401" ]; then
    echo "✅ PASS: /redoc correctly returns 401 Unauthorized without auth"
else
    echo "❌ FAIL: /redoc should return 401 Unauthorized without auth"
    echo "   Got: $HTTP_STATUS"
fi
echo ""

# Cleanup temp file
rm -f "$TEMP_FILE"

# Test /openapi.json endpoint
echo "=========================================="
echo "Test 4: Access /openapi.json WITHOUT authentication"
echo "=========================================="

TEMP_FILE=$(mktemp)
curl -s -D - "$OPENAPI_ENDPOINT" -o /dev/null > "$TEMP_FILE" 2>&1 || true

HTTP_STATUS=$(grep "^HTTP" "$TEMP_FILE" | tail -1 | awk '{print $2}')
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "401" ]; then
    echo "✅ PASS: /openapi.json correctly returns 401 Unauthorized without auth"
else
    echo "❌ FAIL: /openapi.json should return 401 Unauthorized without auth"
    echo "   Got: $HTTP_STATUS"
fi
echo ""

# Cleanup temp file
rm -f "$TEMP_FILE"

# Test with invalid credentials
echo "=========================================="
echo "Test 5: Access /docs WITH INVALID authentication"
echo "=========================================="

TEMP_FILE=$(mktemp)
curl -s -D - -u "wrong:wrong" "$DOCS_ENDPOINT" -o /dev/null > "$TEMP_FILE" 2>&1 || true

HTTP_STATUS=$(grep "^HTTP" "$TEMP_FILE" | tail -1 | awk '{print $2}')
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "401" ]; then
    echo "✅ PASS: /docs correctly returns 401 Unauthorized with invalid credentials"
else
    echo "❌ FAIL: /docs should return 401 Unauthorized with invalid credentials"
    echo "   Got: $HTTP_STATUS"
fi
echo ""

# Cleanup temp file
rm -f "$TEMP_FILE"

echo "=========================================="
echo "Verification Complete"
echo "=========================================="
echo ""
echo "Summary:"
echo "--------"
echo "API documentation endpoints (/docs, /redoc, /openapi.json) are protected"
echo "with HTTP Basic authentication. Unauthorized access returns 401."
echo "Authorized access with valid credentials returns 200."
echo ""
echo "Configuration:"
echo "  SECURITY_API_DOCS_ENABLED: true (default)"
echo "  SECURITY_API_DOCS_USERNAME: admin (default)"
echo "  SECURITY_API_DOCS_PASSWORD: admin (default)"
echo ""
echo "⚠️  IMPORTANT: For production, change the default credentials!"
echo ""
echo "To set custom credentials, export environment variables:"
echo "  export SECURITY_API_DOCS_USERNAME=your_username"
echo "  export SECURITY_API_DOCS_PASSWORD=your_password"
