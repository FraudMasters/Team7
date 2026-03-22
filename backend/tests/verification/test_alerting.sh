#!/bin/bash
# Verification script for Audit Alerting System
# This script verifies the complete audit alerting workflow

set -e  # Exit on error

echo "=========================================="
echo "Audit Alerting System Verification"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track overall status
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo "Step 1: Running Integration Tests"
echo "----------------------------------"
echo ""

# Run pytest integration tests
if command -v pytest &> /dev/null; then
    echo "Running pytest integration tests for audit alerting..."
    cd "$(dirname "$0")/../.." || exit 1

    if pytest tests/integration/test_audit_alerting_e2e.py -v; then
        print_result 0 "Integration tests passed"
    else
        print_result 1 "Integration tests failed"
    fi
else
    echo -e "${YELLOW}⚠ WARNING${NC}: pytest not found. Skipping integration tests."
    echo "Install pytest: pip install pytest pytest-asyncio httpx"
fi

echo ""
echo "Step 2: Verifying Alert Configuration API"
echo "------------------------------------------"
echo ""

# Check if backend is running
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "Backend server is running. Testing API endpoints..."

    # Test GET /api/audit/alerts/types
    echo "Testing GET /api/audit/alerts/types..."
    if curl -s -f http://localhost:8000/api/audit/alerts/types > /dev/null; then
        print_result 0 "GET /api/audit/alerts/types endpoint works"
    else
        print_result 1 "GET /api/audit/alerts/types endpoint failed"
    fi

    # Test GET /api/audit/alerts/severities
    echo "Testing GET /api/audit/alerts/severities..."
    if curl -s -f http://localhost:8000/api/audit/alerts/severities > /dev/null; then
        print_result 0 "GET /api/audit/alerts/severities endpoint works"
    else
        print_result 1 "GET /api/audit/alerts/severities endpoint failed"
    fi

    # Test GET /api/audit/alerts/
    echo "Testing GET /api/audit/alerts/..."
    if curl -s -f http://localhost:8000/api/audit/alerts/ > /dev/null; then
        print_result 0 "GET /api/audit/alerts/ endpoint works"
    else
        print_result 1 "GET /api/audit/alerts/ endpoint failed"
    fi
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Backend server not running on http://localhost:8000"
    echo "Start the backend server to verify API endpoints:"
    echo "  cd backend && uvicorn main:app --reload"
fi

echo ""
echo "Step 3: Verifying Celery Task Registration"
echo "-------------------------------------------"
echo ""

# Check if the audit alerting task is registered
if command -v python &> /dev/null; then
    cd "$(dirname "$0")/../.." || exit 1

    echo "Checking if audit alerting task is importable..."
    if python -c "from tasks.audit_alerting import check_and_alert_suspicious_activity; print('OK')" 2>/dev/null; then
        print_result 0 "Audit alerting task is importable"
    else
        print_result 1 "Audit alerting task import failed"
    fi

    echo "Checking if audit alerting service is importable..."
    if python -c "from services.audit_alerting import detect_suspicious_activity; print('OK')" 2>/dev/null; then
        print_result 0 "Audit alerting service is importable"
    else
        print_result 1 "Audit alerting service import failed"
    fi
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Python not found in PATH"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Failed: $TESTS_FAILED${NC}"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All automated tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
fi

echo ""
echo "=========================================="
echo "Manual Verification Steps"
echo "=========================================="
echo ""
echo "To complete end-to-end verification, follow these manual steps:"
echo ""
echo "1. Create Alert Rule for Failed Logins"
echo "   - Open the database and insert an alert config:"
echo "     INSERT INTO audit_alert_configs ("
echo "       id, name, alert_type, description, enabled, severity,"
echo "       threshold, time_window_minutes, cooldown_minutes,"
echo "       recipients, alert_config, trigger_count"
echo "     ) VALUES ("
echo "       gen_random_uuid(), 'Failed Login Alert', 'failed_logins',"
echo "       'Alert when too many failed logins occur', true, 'warning',"
echo "       5, 10, 60,"
echo "       '{\"emails\": [\"security@example.com\"]}'::jsonb,"
echo "       '{}'::jsonb, 0"
echo "     );"
echo ""
echo "2. Simulate 6 Failed Login Attempts"
echo "   - Use the authentication API to simulate failed logins:"
echo "     for i in {1..6}; do"
echo "       curl -X POST http://localhost:8000/api/auth/login \\"
echo "         -H 'Content-Type: application/json' \\"
echo "         -d '{\"email\":\"test@example.com\",\"password\":\"wrong\"}'"
echo "       sleep 10"
echo "     done"
echo ""
echo "3. Run Suspicious Activity Detection"
echo "   - Manually trigger the Celery task:"
echo "     python -c \\"
echo "       from tasks.audit_alerting import check_and_alert_suspicious_activity; \\"
echo "       result = check_and_alert_suspicious_activity.delay(); \\"
echo "       print(result.get())\""
echo ""
echo "4. Check Audit Logs for Alert Detection"
echo "   - Query the audit logs to verify alert detection:"
echo "     SELECT * FROM audit_logs"
echo "     WHERE action = 'ALERT_TRIGGERED'"
echo "     ORDER BY created_at DESC"
echo "     LIMIT 5;"
echo ""
echo "5. Verify Alert Details"
echo "   - Check that the alert contains:"
echo "     * alert_type = 'FAILED_LOGIN'"
echo "     * count >= 5 (threshold exceeded)"
echo "     * entities array with user_id or ip_address"
echo "     * time_window_minutes = 10"
echo "     * severity = 'warning'"
echo ""
echo "6. Test Different Alert Types"
echo "   - Create alert configs for:"
echo "     * bulk_data_export (threshold: 100 in 10 min)"
echo "     * permission_changes (threshold: 3 in 10 min)"
echo "   - Simulate events for each type"
echo "   - Verify alerts are triggered correctly"
echo ""
echo "7. Test Frontend UI (Optional)"
echo "   - Navigate to http://localhost:5173/admin/audit-alerts"
echo "   - Verify alert rules are displayed"
echo "   - Test enabling/disabling alert rules"
echo "   - Verify trigger count is updated"
echo ""

echo "=========================================="
echo "Additional Resources"
echo "=========================================="
echo ""
echo "Documentation:"
echo "  - See .auto-claude/specs/010-audit-logging/subtask-6-2-verification.md"
echo "  - See backend/services/audit_alerting.py for service implementation"
echo "  - See backend/tasks/audit_alerting.py for Celery task"
echo ""
echo "Database Schema:"
echo "  - audit_alert_configs: Alert rule configuration"
echo "  - audit_logs: Audit log entries (includes alert detection events)"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
