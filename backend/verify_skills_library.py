#!/usr/bin/env python
"""Verification script for skills_library module."""
import sys

try:
    from skills.skills_library import SkillsLibrary, load_position_skills, get_skills_for_position
    print("✓ Successfully imported SkillsLibrary")
    print("✓ Successfully imported load_position_skills")
    print("✓ Successfully imported get_skills_for_position")

    # Test basic functionality
    lib = SkillsLibrary()
    print(f"✓ Created SkillsLibrary instance")

    all_skills = lib.get_all_skills()
    print(f"✓ Loaded {len(all_skills)} unique skills across all positions")

    positions = lib.get_all_positions()
    print(f"✓ Found {len(positions)} position taxonomies")

    # Test specific position
    frontend_skills = lib.get_skills_for_position("frontend_developer")
    if frontend_skills:
        print(f"✓ Retrieved frontend_developer skills:")
        print(f"  - Required: {len(frontend_skills['required_skills'])} skills")
        print(f"  - Optional: {len(frontend_skills['optional_skills'])} skills")
        print(f"  - Variants: {len(frontend_skills['position_variants'])} variants")

    print("\nOK - All verifications passed")
    sys.exit(0)
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
