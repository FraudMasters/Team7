#!/usr/bin/env python
"""
Verification script for Alembic database migration configuration

This script validates:
1. Alembic configuration file is valid
2. Database models can be imported
3. Migration files are discoverable
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def verify_alembic_config():
    """Verify Alembic configuration"""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    print("✓ Alembic configuration is valid")

    # List revisions
    revisions = list(script.get_revisions())
    print(f"✓ Found {len(revisions)} revision(s)")

    for rev in revisions:
        print(f"  - {rev.revision}: {rev.doc or 'No description'}")

    return True


def verify_models():
    """Verify database models can be imported"""
    try:
        from models import Base, Resume, AnalysisResult, JobVacancy, MatchResult

        print("✓ Database models imported successfully")

        # Check tables are defined
        tables = Base.metadata.tables.keys()
        print(f"✓ Found {len(tables)} table(s): {', '.join(tables)}")

        return True
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Alembic Migration Verification")
    print("=" * 60)

    checks = [
        ("Alembic Configuration", verify_alembic_config),
        ("Database Models", verify_models),
    ]

    results = {}
    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"✗ Error: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = all(results.values())
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    if all_passed:
        print("\n✓ All verification checks passed!")
        return 0
    else:
        print("\n✗ Some verification checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
