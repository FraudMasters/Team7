#!/bin/bash
# Validate A/B testing migration file

echo "=========================================="
echo "A/B Testing Migration Validation"
echo "=========================================="
echo

MIGRATION_FILE="backend/alembic/versions/20260321_add_ab_testing_tables.py"

# Check file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Migration file not found: $MIGRATION_FILE"
    exit 1
fi

echo "✓ Migration file exists: $MIGRATION_FILE"
echo

# Check for required elements
echo "--- Checking migration structure ---"

check_element() {
    if grep -q "$2" "$1"; then
        echo "✓ $3: present"
        return 0
    else
        echo "❌ $3: MISSING"
        return 1
    fi
}

PASSED=0
FAILED=0

# Check migration metadata
check_element "$MIGRATION_FILE" "revision: str = '20260321_add_ab_testing_tables'" "Revision identifier" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "down_revision: Union\[str, None\] = '20260321_add_ranking_features_weights'" "Down revision" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "def upgrade()" "Upgrade function" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "def downgrade()" "Downgrade function" && ((PASSED++)) || ((FAILED++))

# Check ab_tests table
check_element "$MIGRATION_FILE" "'ab_tests'" "AB tests table" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'organization_id'" "Organization ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'name'" "Name column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'description'" "Description column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'variant_a_profile_id'" "Variant A profile ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'variant_b_profile_id'" "Variant B profile ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'status'" "Status column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'start_date'" "Start date column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'end_date'" "End date column" && ((PASSED++)) || ((FAILED++))

# Check ab_test_results table
check_element "$MIGRATION_FILE" "'ab_test_results'" "AB test results table" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'ab_test_id'" "AB test ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'vacancy_id'" "Vacancy ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'resume_id'" "Resume ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'match_result_id'" "Match result ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'variant_assigned'" "Variant assigned column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'outcome'" "Outcome column" && ((PASSED++)) || ((FAILED++))

# Check indexes
check_element "$MIGRATION_FILE" "ix_ab_tests_organization_id" "AB tests organization index" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "ix_ab_tests_status" "AB tests status index" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "ix_ab_test_results_ab_test_id" "AB test results test ID index" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "ix_ab_test_results_variant_assigned" "AB test results variant index" && ((PASSED++)) || ((FAILED++))

# Check foreign keys
check_element "$MIGRATION_FILE" "sa.ForeignKey('matching_weights_profiles.id'" "Foreign key to matching_weights_profiles" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "sa.ForeignKey('ab_tests.id'" "Foreign key to ab_tests" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "sa.ForeignKey('job_vacancies.id'" "Foreign key to job_vacancies" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "sa.ForeignKey('resumes.id'" "Foreign key to resumes" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "sa.ForeignKey('match_results.id'" "Foreign key to match_results" && ((PASSED++)) || ((FAILED++))

echo
echo "=========================================="
echo "Checks: $PASSED passed, $FAILED failed"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo
    echo "✅ ALL VALIDATION CHECKS PASSED"
    echo
    echo "Migration is ready to execute with:"
    echo "  cd backend && alembic upgrade head"
    echo
    echo "Expected behavior:"
    echo "  - Creates 'ab_tests' table with 2 variants"
    echo "  - Creates 'ab_test_results' table to track outcomes"
    echo "  - All foreign keys properly configured"
    echo "  - All indexes created for performance"
    echo
    exit 0
else
    echo
    echo "❌ VALIDATION FAILED - $FAILED check(s) failed"
    exit 1
fi
