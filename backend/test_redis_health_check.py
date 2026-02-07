#!/usr/bin/env python
"""
Simple verification test for RedisHealthChecker.

This test verifies that the RedisHealthChecker class is properly implemented
and can be imported and instantiated.
"""
import sys


def test_redis_health_checker_import():
    """Test that RedisHealthChecker can be imported."""
    try:
        from services.health_check import RedisHealthChecker
        print("✓ RedisHealthChecker imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import RedisHealthChecker: {e}")
        return False


def test_redis_health_checker_instantiation():
    """Test that RedisHealthChecker can be instantiated."""
    try:
        from services.health_check import RedisHealthChecker
        checker = RedisHealthChecker()
        print(f"✓ RedisHealthChecker instantiated (timeout={checker.timeout_seconds}s)")
        return True
    except Exception as e:
        print(f"✗ Failed to instantiate RedisHealthChecker: {e}")
        return False


def test_redis_health_checker_has_cache_service():
    """Test that RedisHealthChecker has a CacheService instance."""
    try:
        from services.health_check import RedisHealthChecker
        checker = RedisHealthChecker()
        if hasattr(checker, 'cache_service'):
            print("✓ RedisHealthChecker has cache_service attribute")
            return True
        else:
            print("✗ RedisHealthChecker missing cache_service attribute")
            return False
    except Exception as e:
        print(f"✗ Failed to check cache_service: {e}")
        return False


def test_redis_health_checker_check_method():
    """Test that RedisHealthChecker has async check method."""
    try:
        from services.health_check import RedisHealthChecker
        checker = RedisHealthChecker()
        if hasattr(checker, 'check'):
            import asyncio
            if asyncio.iscoroutinefunction(checker.check):
                print("✓ RedisHealthChecker has async check() method")
                return True
            else:
                print("✗ RedisHealthChecker.check() is not async")
                return False
        else:
            print("✗ RedisHealthChecker missing check() method")
            return False
    except Exception as e:
        print(f"✗ Failed to check check() method: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("RedisHealthChecker Verification Tests")
    print("=" * 60)

    tests = [
        test_redis_health_checker_import,
        test_redis_health_checker_instantiation,
        test_redis_health_checker_has_cache_service,
        test_redis_health_checker_check_method,
    ]

    results = []
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        results.append(test())

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    sys.exit(0 if all(results) else 1)
