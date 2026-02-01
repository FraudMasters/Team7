#!/usr/bin/env python3
"""
Test script to verify cache invalidation implementation.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_cache_service_imports():
    """Test that cache service imports correctly."""
    try:
        from backend.services.cache_service import (
            get_cache_service,
            CacheService,
            invalidate_candidate_cache,
            invalidate_vacancy_cache,
            invalidate_match_cache
        )
        print("✓ Cache service imports successful")
        print(f"  - invalidate_candidate_cache: {invalidate_candidate_cache}")
        print(f"  - invalidate_vacancy_cache: {invalidate_vacancy_cache}")
        print(f"  - invalidate_match_cache: {invalidate_match_cache}")
        return True
    except ImportError as e:
        print(f"✗ Cache service import failed: {e}")
        return False

def test_candidates_api_imports():
    """Test that candidates API imports correctly."""
    try:
        from backend.api.candidates import invalidate_candidate_cache
        print("✓ Candidates API imports invalidate_candidate_cache")
        return True
    except ImportError as e:
        print(f"✗ Candidates API import failed: {e}")
        return False

def test_matching_api_imports():
    """Test that matching API imports correctly."""
    try:
        from backend.api.matching import invalidate_match_cache
        print("✓ Matching API imports invalidate_match_cache")
        return True
    except ImportError as e:
        print(f"✗ Matching API import failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Cache Invalidation Verification Tests")
    print("=" * 60)
    print()

    results = []

    # Test 1: Cache service imports
    print("Test 1: Cache service imports")
    print("-" * 60)
    results.append(test_cache_service_imports())
    print()

    # Test 2: Candidates API imports
    print("Test 2: Candidates API imports")
    print("-" * 60)
    results.append(test_candidates_api_imports())
    print()

    # Test 3: Matching API imports
    print("Test 3: Matching API imports")
    print("-" * 60)
    results.append(test_matching_api_imports())
    print()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
