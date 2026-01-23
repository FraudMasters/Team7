#!/usr/bin/env python3
"""
Verification script for job matching endpoint (subtask-4-4).

This script tests the matching API endpoint with sample data.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Job Matching Endpoint Verification")
print("=" * 60)

# Test 1: Import matching module
print("\n[1/4] Testing import of matching module...")
try:
    from api.matching import (
        load_skill_synonyms,
        normalize_skill_name,
        check_skill_match,
        find_matching_synonym,
        router,
    )
    print("✓ Successfully imported matching module")
except Exception as e:
    print(f"✗ Failed to import matching module: {e}")
    sys.exit(1)

# Test 2: Load skill synonyms
print("\n[2/4] Testing skill synonyms loading...")
try:
    synonyms = load_skill_synonyms()
    print(f"✓ Loaded {len(synonyms)} skill synonym mappings")

    # Show some examples
    print("\n  Example synonym mappings:")
    count = 0
    for skill, variants in list(synonyms.items())[:5]:
        print(f"    - {skill}: {', '.join(variants[:3])}{'...' if len(variants) > 3 else ''}")
        count += 1
        if count >= 3:
            break
except Exception as e:
    print(f"✗ Failed to load skill synonyms: {e}")
    sys.exit(1)

# Test 3: Test skill matching functions
print("\n[3/4] Testing skill matching functions...")
try:
    # Test normalize_skill_name
    assert normalize_skill_name("  React JS  ") == "react js"
    print("✓ normalize_skill_name() works correctly")

    # Test check_skill_match
    resume_skills = ["Java", "PostgreSQL", "Spring Boot", "Docker"]
    assert check_skill_match(resume_skills, "Java", synonyms) == True
    assert check_skill_match(resume_skills, "SQL", synonyms) == True  # PostgreSQL matches SQL
    assert check_skill_match(resume_skills, "Python", synonyms) == False
    print("✓ check_skill_match() works correctly")

    # Test find_matching_synonym
    match = find_matching_synonym(resume_skills, "SQL", synonyms)
    assert match == "PostgreSQL"
    print(f"✓ find_matching_synonym() works correctly: SQL -> {match}")

except AssertionError as e:
    print(f"✗ Skill matching test failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error testing skill matching: {e}")
    sys.exit(1)

# Test 4: Check router is configured
print("\n[4/4] Testing API router configuration...")
try:
    routes = [route for route in router.routes]
    print(f"✓ Matching router has {len(routes)} route(s)")

    # Show routes
    for route in routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = ", ".join(route.methods)
            print(f"    - {methods} {route.path}")
        elif hasattr(route, "path"):
            print(f"    - {route.path}")

except Exception as e:
    print(f"✗ Failed to check router configuration: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All verification tests passed! ✓")
print("=" * 60)

print("\nTo test the API endpoint manually:")
print("1. Start the server:")
print("   cd backend && uvicorn main:app --reload --port 8000")
print("\n2. Upload a resume first:")
print("   curl -X POST http://localhost:8000/api/resumes/upload \\")
print("     -F 'file=@test_resume.pdf'")
print("\n3. Test matching endpoint:")
print("   curl -X POST http://localhost:8000/api/matching/compare \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{")
print('       "resume_id": "YOUR_RESUME_ID",')
print('       "vacancy_data": {')
print('         "title": "Java Developer",')
print('         "required_skills": ["Java", "Spring", "SQL"],')
print('         "min_experience_months": 36')
print("       }")
print("     }'")
print("\n" + "=" * 60)
