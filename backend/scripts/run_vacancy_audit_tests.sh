#!/bin/bash
# Verification script for subtask-3-1: Run all vacancy audit tests together
# This script runs all 5 vacancy audit logging tests to verify they pass together

set -e

echo "========================================="
echo "Running Vacancy Audit Tests"
echo "========================================="
echo ""

cd backend

echo "Test file: tests/api/test_vacancies_audit.py"
echo ""
echo "Expected tests (5):"
echo "  1. test_create_vacancy_creates_audit_log - VACANCY_CREATED with after_value"
echo "  2. test_view_vacancy_creates_audit_log - VACANCY_VIEWED entry"
echo "  3. test_update_vacancy_creates_audit_log - VACANCY_UPDATED with before/after values"
echo "  4. test_delete_vacancy_creates_audit_log - VACANCY_DELETED with before_value"
echo "  5. test_multiple_vacancy_operations_create_distinct_audit_logs - Multiple operations"
echo ""

# Run the tests
pytest tests/api/test_vacancies_audit.py -v

echo ""
echo "========================================="
echo "✓ All vacancy audit tests passed!"
echo "========================================="
