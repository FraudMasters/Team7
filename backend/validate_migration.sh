#!/bin/bash
# Validate interview_prep migration file

echo "=========================================="
echo "Interview Prep Migration Validation"
echo "=========================================="
echo

MIGRATION_FILE="backend/alembic/versions/20260201_add_interview_prep.py"

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

check_element "$MIGRATION_FILE" "revision: str = " "Revision identifier" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "down_revision: Union\[str, None\] = " "Down revision" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "def upgrade()" "Upgrade function" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "def downgrade()" "Downgrade function" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'interview_preps'" "Interview preps table" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'resume_id'" "Resume ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'vacancy_id'" "Vacancy ID column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'technical_questions'" "Technical questions column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'behavioral_questions'" "Behavioral questions column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'situational_questions'" "Situational questions column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'skill_verification_topics'" "Skill verification topics column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'areas_to_probe'" "Areas to probe column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'custom_questions'" "Custom questions column" && ((PASSED++)) || ((FAILED++))
check_element "$MIGRATION_FILE" "'question_feedback'" "Question feedback column" && ((PASSED++)) || ((FAILED++))

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
    echo "  - Alembic will detect current version"
    echo "  - Apply interview_prep table migration"
    echo "  - Complete with no errors"
    echo
    echo "See INTERVIEW_PREP_MIGRATION_STATUS.md for details"
    exit 0
else
    echo
    echo "❌ VALIDATION FAILED - $FAILED check(s) failed"
    exit 1
fi
