#!/usr/bin/env python3
"""
Validate interview_prep migration file structure and dependencies.
This script verifies the migration is ready to execute without database connection.
"""

import sys
from pathlib import Path

def validate_migration_exists():
    """Check that the migration file exists."""
    versions_dir = Path(__file__).parent / "alembic" / "versions"
    migration_file = versions_dir / "20260201_add_interview_prep.py"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print(f"✓ Migration file exists: {migration_file}")
    return True

def validate_migration_structure():
    """Validate the migration has correct structure."""
    versions_dir = Path(__file__).parent / "alembic" / "versions"
    migration_file = versions_dir / "20260201_add_interview_prep.py"

    # Read the migration file
    content = migration_file.read_text()

    # Check for required elements
    checks = [
        ("revision identifier", 'revision: str = '),
        ("down_revision", 'down_revision: Union[str, None] = '),
        ("upgrade function", 'def upgrade()'),
        ("downgrade function", 'def downgrade()'),
        ("interview_preps table", "'interview_preps'"),
        ("resume_id foreign key", "'resume_id'"),
        ("vacancy_id foreign key", "'vacancy_id'"),
        ("technical_questions column", "'technical_questions'"),
        ("behavioral_questions column", "'behavioral_questions'"),
        ("situational_questions column", "'situational_questions'"),
        ("skill_verification_topics column", "'skill_verification_topics'"),
        ("areas_to_probe column", "'areas_to_probe'"),
        ("custom_questions column", "'custom_questions'"),
        ("question_feedback column", "'question_feedback'"),
    ]

    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✓ {check_name}: present")
        else:
            print(f"❌ {check_name}: MISSING")
            all_passed = False

    return all_passed

def validate_migration_chain():
    """Validate that the migration fits correctly in the chain."""
    versions_dir = Path(__file__).parent / "alembic" / "versions"

    # Find the migration file
    migration_files = list(versions_dir.glob("20260201_add_interview_prep.py"))
    if not migration_files:
        print("❌ Migration file not found")
        return False

    # Read revision info
    content = migration_files[0].read_text()

    # Extract revision and down_revision
    import re
    revision_match = re.search(r"revision: str = '([^']+)'", content)
    down_revision_match = re.search(r"down_revision: Union\[str, None\] = '([^']+)'", content)

    if not revision_match:
        print("❌ Revision identifier not found")
        return False

    if not down_revision_match:
        print("❌ Down revision not found")
        return False

    revision = revision_match.group(1)
    down_revision = down_revision_match.group(1)

    print(f"✓ Migration revision: {revision}")
    print(f"✓ Down revision: {down_revision}")

    # Verify down_revision exists
    # Check if the down_revision file exists
    for mig_file in versions_dir.glob("*.py"):
        mig_content = mig_file.read_text()
        if f"revision: str = '{down_revision}'" in mig_content:
            print(f"✓ Down revision {down_revision} exists in {mig_file.name}")
            return True

    print(f"❌ Down revision {down_revision} not found in any migration file")
    return False

def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Interview Prep Migration Validation")
    print("=" * 60)
    print()

    checks = [
        ("Migration file exists", validate_migration_exists),
        ("Migration structure", validate_migration_structure),
        ("Migration chain", validate_migration_chain),
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        if not check_func():
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("✅ ALL VALIDATION CHECKS PASSED")
        print()
        print("Migration is ready to execute with:")
        print("  cd backend && alembic upgrade head")
        print()
        print("Expected behavior:")
        print("  - Alembic will detect current version")
        print("  - Apply interview_prep table migration")
        print("  - Complete with no errors")
        return 0
    else:
        print("❌ VALIDATION FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
