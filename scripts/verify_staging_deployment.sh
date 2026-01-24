#!/bin/bash
# Staging Deployment Verification Script
# This script performs end-to-end verification of the staging deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
STAGING_URL="${STAGING_URL:-http://localhost}"
BACKEND_URL="${BACKEND_URL:-${STAGING_URL}:8000}"
FRONTEND_URL="${FRONTEND_URL:-${STAGING_URL}:5173}"
FLOWER_URL="${FLOWER_URL:-${STAGING_URL}:5555}"
TEST_RESUME="${TEST_RESUME:-./backend/tests/accuracy_validation/test_resumes.json}"

# Counter for results
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    log_info "Checking $name at $url"

    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")

    if [ "$status" -eq "$expected_status" ]; then
        log_info "✓ $name is accessible (HTTP $status)"
        ((PASSED++))
        return 0
    else
        log_error "✗ $name returned HTTP $status (expected $expected_status)"
        ((FAILED++))
        return 1
    fi
}

check_json_response() {
    local name=$1
    local url=$2
    local field=$3

    log_info "Checking $name JSON response at $url"

    response=$(curl -s "$url")
    value=$(echo "$response" | jq -r ".$field" 2>/dev/null || echo "")

    if [ -n "$value" ] && [ "$value" != "null" ]; then
        log_info "✓ $name contains valid JSON with field '$field'"
        ((PASSED++))
        return 0
    else
        log_error "✗ $name response is missing field '$field' or invalid JSON"
        ((FAILED++))
        return 1
    fi
}

upload_test_resume() {
    log_info "Testing resume upload endpoint"

    # Create a minimal test PDF
    test_pdf="/tmp/test_resume.pdf"
    echo "%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
210
%%EOF" > "$test_pdf"

    # Upload the test resume
    response=$(curl -s -X POST \
        -F "file=@$test_pdf" \
        "$BACKEND_URL/api/resumes/upload")

    resume_id=$(echo "$response" | jq -r '.resume_id' 2>/dev/null || echo "")

    if [ -n "$resume_id" ] && [ "$resume_id" != "null" ]; then
        log_info "✓ Resume upload successful, ID: $resume_id"
        ((PASSED++))
        echo "$resume_id"
        return 0
    else
        log_error "✗ Resume upload failed: $response"
        ((FAILED++))
        return 1
    fi
}

analyze_resume() {
    local resume_id=$1
    log_info "Testing resume analysis for ID: $resume_id"

    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"resume_id\": \"$resume_id\"}" \
        "$BACKEND_URL/api/resumes/analyze")

    # Check if analysis contains expected fields
    has_keywords=$(echo "$response" | jq -e '.keywords' > /dev/null 2>&1 && echo "true" || echo "false")
    has_entities=$(echo "$response" | jq -e '.entities' > /dev/null 2>&1 && echo "true" || echo "false")
    has_errors=$(echo "$response" | jq -e '.errors' > /dev/null 2>&1 && echo "true" || echo "false")

    if [ "$has_keywords" = "true" ] || [ "$has_entities" = "true" ] || [ "$has_errors" = "true" ]; then
        log_info "✓ Resume analysis completed successfully"
        ((PASSED++))
        return 0
    else
        log_error "✗ Resume analysis failed: $response"
        ((FAILED++))
        return 1
    fi
}

check_celery_worker() {
    local url=$1
    log_info "Checking Celery worker status"

    response=$(curl -s "$url/api/workers" 2>/dev/null || echo "{}")
    worker_count=$(echo "$response" | jq 'length' 2>/dev/null || echo "0")

    if [ "$worker_count" -gt 0 ]; then
        log_info "✓ Celery worker is running ($worker_count worker(s) detected)"
        ((PASSED++))
        return 0
    else
        log_warning "⚠ No active Celery workers detected (may be starting up)"
        ((WARNINGS++))
        return 1
    fi
}

check_console_errors() {
    log_info "Checking for console errors (manual verification required)"
    log_warning "⚠ Open browser DevTools at $FRONTEND_URL and verify no console errors"
    ((WARNINGS++))
}

# Main verification flow
echo "========================================="
echo "  Staging Deployment Verification"
echo "========================================="
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "Flower URL: $FLOWER_URL"
echo ""

# 1. Check service health endpoints
log_info "Step 1: Checking service health endpoints"
echo "-------------------------------------------"
check_endpoint "Backend Health" "$BACKEND_URL/health" 200
check_endpoint "Backend Ready" "$BACKEND_URL/ready" 200
check_endpoint "Frontend" "$FRONTEND_URL/" 200
check_json_response "Backend Info" "$BACKEND_URL/" "title"
echo ""

# 2. Check API documentation
log_info "Step 2: Checking API documentation"
echo "-------------------------------------------"
check_endpoint "API Docs (Swagger)" "$BACKEND_URL/docs" 200
check_endpoint "API Docs (ReDoc)" "$BACKEND_URL/redoc" 200
echo ""

# 3. Check Celery monitoring
log_info "Step 3: Checking Celery monitoring"
echo "-------------------------------------------"
check_endpoint "Flower Monitoring" "$FLOWER_URL/" 200
check_celery_worker "$FLOWER_URL"
echo ""

# 4. Test resume upload
log_info "Step 4: Testing resume upload"
echo "-------------------------------------------"
resume_id=$(upload_test_resume)
echo ""

# 5. Test resume analysis
log_info "Step 5: Testing resume analysis"
echo "-------------------------------------------"
if [ -n "$resume_id" ]; then
    analyze_resume "$resume_id"
else
    log_error "Skipping analysis test (upload failed)"
fi
echo ""

# 6. Test job matching endpoint
log_info "Step 6: Testing job matching endpoint"
echo "-------------------------------------------"
if [ -n "$resume_id" ]; then
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"resume_id\": \"$resume_id\", \"vacancy_data\": {\"required_skills\": [\"Python\", \"Docker\"]}}" \
        "$BACKEND_URL/api/matching/compare")

    has_match=$(echo "$response" | jq -e '.match_percentage' > /dev/null 2>&1 && echo "true" || echo "false")

    if [ "$has_match" = "true" ]; then
        log_info "✓ Job matching endpoint works"
        ((PASSED++))
    else
        log_error "✗ Job matching endpoint failed"
        ((FAILED++))
    fi
else
    log_error "Skipping matching test (upload failed)"
fi
echo ""

# 7. Check async processing
log_info "Step 7: Checking async processing (Celery)"
echo "-------------------------------------------"
# Check if Celery tasks can be queued
check_endpoint "Celery Ping" "$BACKEND_URL/api/celery/ping" 200 2>/dev/null || log_warning "⚠ Celery ping endpoint not available"
echo ""

# 8. Check for console errors (manual step)
log_info "Step 8: Console error check"
echo "-------------------------------------------"
check_console_errors
echo ""

# 9. Check database connectivity
log_info "Step 9: Checking database connectivity"
echo "-------------------------------------------"
check_json_response "Database Check" "$BACKEND_URL/health" "database_status"
echo ""

# Final summary
echo "========================================="
echo "  Verification Summary"
echo "========================================="
echo -e "Passed:  ${GREEN}$PASSED${NC}"
echo -e "Failed:  ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    log_info "✓ All critical checks passed!"
    echo ""
    echo "Next steps:"
    echo "1. Open $FRONTEND_URL in browser"
    echo "2. Upload a test resume (PDF)"
    echo "3. View analysis results"
    echo "4. Compare with a job vacancy"
    echo "5. Check browser console for errors"
    echo "6. Monitor Celery tasks at $FLOWER_URL"
    echo ""
    exit 0
else
    log_error "✗ $FAILED check(s) failed. Please review and fix."
    echo ""
    exit 1
fi
