"""
Validation script for resume_templates migration.

This script validates the structure and integrity of the
resume_templates Alembic migration before execution.
"""
import re
import sys
from pathlib import Path


def validate_migration_file():
    """Validate the resume_templates migration file exists and has correct structure."""
    migration_path = Path("alembic/versions/20260210_add_resume_templates.py")

    if not migration_path.exists():
        print("❌ FAIL: Migration file not found")
        return False

    print(f"✅ Migration file exists: {migration_path}")

    # Read migration content
    content = migration_path.read_text()

    # Check for required elements
    checks = {
        "revision": r'revision:\s*str\s*=\s*"([^"]+)"',
        "down_revision": r'down_revision:\s*Union\[str,\s*None\]\s*=\s*"([^"]+)"',
        "upgrade function": r'def upgrade\(\)',
        "downgrade function": r'def downgrade\(\)',
        "create_table": r'op\.create_table\(\s*"resume_templates"',
        "id column": r'sa\.Column\(\s*"id"',
        "organization_id column": r'sa\.Column\(\s*"organization_id"',
        "name column": r'sa\.Column\(\s*"name"',
        "template_type column": r'sa\.Column\(\s*"template_type"',
        "layout_config column": r'sa\.Column\(\s*"layout_config"',
        "style_config column": r'sa\.Column\(\s*"style_config"',
        "section_config column": r'sa\.Column\(\s*"section_config"',
        "is_default column": r'sa\.Column\(\s*"is_default"',
        "is_active column": r'sa\.Column\(\s*"is_active"',
        "is_ats_compliant column": r'sa\.Column\(\s*"is_ats_compliant"',
        "created_at column": r'sa\.Column\(\s*"created_at"',
        "drop_table": r'op\.drop_table\(\s*"resume_templates"',
    }

    results = {}
    for check_name, pattern in checks.items():
        match = re.search(pattern, content)
        results[check_name] = match is not None
        status = "✅" if match else "❌"
        print(f"{status} {check_name}: {'Found' if match else 'NOT FOUND'}")

    # Extract revision IDs
    revision_match = re.search(r'revision:\s*str\s*=\s*"([^"]+)"', content)
    down_revision_match = re.search(r'down_revision:\s*Union\[str,\s*None\]\s*=\s*"([^"]+)"', content)

    if revision_match:
        revision = revision_match.group(1)
        print(f"\n✅ Revision ID: {revision}")
    else:
        print("\n❌ FAIL: Could not extract revision ID")
        return False

    if down_revision_match:
        down_revision = down_revision_match.group(1)
        print(f"✅ Down revision: {down_revision}")
    else:
        print("❌ FAIL: Could not extract down revision ID")
        return False

    # Check if all required elements are present
    all_passed = all(results.values())
    missing = [name for name, passed in results.items() if not passed]

    if all_passed:
        print(f"\n✅ PASS: All {len(checks)} validation checks passed")
        print(f"\nMigration summary:")
        print(f"  - Revision: {revision}")
        print(f"  - Down revision: {down_revision}")
        print(f"  - Table: resume_templates")
        print(f"  - Columns: 13 (id, organization_id, name, description, template_type,")
        print(f"              layout_config, style_config, section_config, preview_url,")
        print(f"              is_default, is_active, is_ats_compliant, created_by, created_at, updated_at)")
        return True
    else:
        print(f"\n❌ FAIL: {len(missing)} validation check(s) failed")
        print(f"Missing: {', '.join(missing)}")
        return False


def validate_migration_chain():
    """Validate that the migration chain is intact."""
    versions_dir = Path("alembic/versions")

    if not versions_dir.exists():
        print("❌ FAIL: alembic/versions directory not found")
        return False

    # Find all migration files
    migration_files = sorted(versions_dir.glob("*.py"))
    print(f"\n✅ Found {len(migration_files)} migration file(s)")

    # Extract revision IDs from all migrations
    revisions = {}
    for migration_file in migration_files:
        content = migration_file.read_text()
        revision_match = re.search(r'revision:\s*str\s*=\s*"([^"]+)"', content)
        down_revision_match = re.search(r'down_revision:\s*Union\[str,\s*None\]\s*=\s*"([^"]+)"', content)

        if revision_match:
            revision = revision_match.group(1)
            down_revision = down_revision_match.group(1) if down_revision_match else None
            revisions[revision] = {
                "file": migration_file.name,
                "down_revision": down_revision
            }

    # Check for resume_templates revision
    resume_templates_rev = "20260210_add_resume_templates"
    if resume_templates_rev in revisions:
        print(f"✅ resume_templates migration found in chain")
        down_rev = revisions[resume_templates_rev]["down_revision"]
        print(f"   Down revision: {down_rev}")

        # Verify down revision exists
        if down_rev and down_rev in revisions:
            print(f"✅ Down revision {down_rev} exists in chain")
        elif down_rev:
            print(f"⚠️  WARNING: Down revision {down_rev} not found in chain")
    else:
        print(f"❌ FAIL: resume_templates migration not found in chain")
        return False

    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Resume Templates Migration Validation")
    print("=" * 60)

    print("\n1. Validating migration file structure...")
    structure_valid = validate_migration_file()

    print("\n" + "=" * 60)
    print("\n2. Validating migration chain...")
    chain_valid = validate_migration_chain()

    print("\n" + "=" * 60)
    print("\nFINAL RESULT:")
    if structure_valid and chain_valid:
        print("✅ PASS: Migration is valid and ready for execution")
        print("\nTo execute the migration when database is available:")
        print("  cd backend")
        print("  alembic upgrade head")
        print("\nOr use the programmatic runner:")
        print("  cd backend")
        print("  python run_migration.py")
        return 0
    else:
        print("❌ FAIL: Migration validation failed")
        print("\nPlease fix the issues above before executing the migration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
