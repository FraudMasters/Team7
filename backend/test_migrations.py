#!/usr/bin/env python3
"""
Test script to validate migration chain integrity without database connection.
This verifies that all migrations can be imported and their dependencies are correct.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_migration_chain():
    """Test that all migrations form a valid linear chain."""
    versions_dir = Path(__file__).parent / "alembic" / "versions"

    # Find all migration files
    migration_files = sorted(versions_dir.glob("00*.py"))
    print(f"Found {len(migration_files)} migration files")

    migrations = {}
    for mig_file in migration_files:
        # Import the migration module
        module_name = f"alembic.versions.{mig_file.stem}"
        try:
            module = __import__(module_name, fromlist=['revision', 'down_revision'])
            revision = module.revision
            down_revision = module.down_revision
            migrations[revision] = {
                'file': mig_file.name,
                'down_revision': down_revision,
                'module': module
            }
            print(f"✓ {mig_file.name}: revision={revision}, down_revision={down_revision}")
        except Exception as e:
            print(f"✗ {mig_file.name}: Failed to import - {e}")
            return False

    # Verify chain integrity
    print("\n--- Verifying Migration Chain ---")

    # Find head (migration with no dependent)
    head_candidates = [rev for rev, data in migrations.items()
                      if rev not in [data['down_revision'] for data in migrations.values()]]

    if len(head_candidates) != 1:
        print(f"✗ Chain error: Expected 1 head, found {len(head_candidates)}: {head_candidates}")
        return False

    head = head_candidates[0]
    print(f"✓ Head migration: {head} ({migrations[head]['file']})")

    # Find base (migration with down_revision = None)
    base_candidates = [rev for rev, data in migrations.items()
                      if data['down_revision'] is None]

    if len(base_candidates) != 1:
        print(f"✗ Chain error: Expected 1 base, found {len(base_candidates)}: {base_candidates}")
        return False

    base = base_candidates[0]
    print(f"✓ Base migration: {base} ({migrations[base]['file']})")

    # Walk the chain from base to head
    print("\n--- Migration Chain Order ---")
    current = base
    chain = []
    while current is not None:
        data = migrations[current]
        chain.append(current)
        print(f"  {current} -> {data['file']}")
        current = data['down_revision'] if data['down_revision'] in migrations else None

    # Verify we reached the head
    if current != head and chain[-1] != head:
        print(f"✗ Chain broken: Expected to reach {head}, but stopped at {chain[-1]}")
        return False

    # Verify expected chain order
    expected_chain = [
        "001_init",
        "002_add_advanced_matching",
        "003_add_resume_comparisons",
        "004_add_analytics_tables",
        "005_add_batch_jobs",
        "006_add_candidate_feedback",
        "007_add_resume_search",
        "008_add_score_appeals",
        "009_add_performance_indexes"
    ]

    if chain != expected_chain:
        print(f"\n✗ Chain order mismatch!")
        print(f"Expected: {expected_chain}")
        print(f"Got:      {chain}")
        return False

    print(f"\n✓ Migration chain is correct: {len(chain)} migrations in sequence")
    print(f"✓ All migrations are properly linked")
    print(f"✓ Ready for: alembic upgrade head")

    return True

def test_migration_syntax():
    """Test that all migrations have valid upgrade/downgrade functions."""
    print("\n--- Testing Migration Syntax ---")

    versions_dir = Path(__file__).parent / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("00*.py"))

    for mig_file in migration_files:
        module_name = f"alembic.versions.{mig_file.stem}"
        try:
            module = __import__(module_name, fromlist=['upgrade', 'downgrade'])

            # Check upgrade function exists and is callable
            if not hasattr(module, 'upgrade') or not callable(module.upgrade):
                print(f"✗ {mig_file.name}: Missing or non-callable upgrade() function")
                return False

            # Check downgrade function exists and is callable
            if not hasattr(module, 'downgrade') or not callable(module.downgrade):
                print(f"✗ {mig_file.name}: Missing or non-callable downgrade() function")
                return False

            print(f"✓ {mig_file.name}: Has valid upgrade() and downgrade() functions")

        except Exception as e:
            print(f"✗ {mig_file.name}: Syntax error - {e}")
            return False

    print(f"\n✓ All {len(migration_files)} migrations have valid structure")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Migration Validation Test")
    print("=" * 60)

    success = True

    # Test 1: Migration chain integrity
    if not test_migration_chain():
        success = False

    # Test 2: Migration syntax
    if not test_migration_syntax():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED")
        print("Migrations are ready to run: alembic upgrade head")
        sys.exit(0)
    else:
        print("✗ TESTS FAILED")
        sys.exit(1)
