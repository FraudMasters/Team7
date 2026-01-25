#!/usr/bin/env python3
"""
Verification script for exception handler translations.

This script tests that exception handlers return translated error messages
based on the Accept-Language header.
"""
import sys
import json


def test_import():
    """Test that the translation module imports correctly."""
    print("Testing imports...")
    try:
        from main import app, _extract_accept_language
        from i18n.backend_translations import get_error_message
        print("✓ Imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_extract_language():
    """Test the _extract_accept_language function."""
    print("\nTesting _extract_accept_language...")

    from main import _extract_accept_language
    from fastapi import Request

    # Create mock request class
    class MockRequest:
        def __init__(self, headers):
            self.headers = headers

    # Test cases
    test_cases = [
        ({"Accept-Language": "en"}, "en"),
        ({"Accept-Language": "ru"}, "ru"),
        ({"Accept-Language": "en-US"}, "en"),
        ({"Accept-Language": "ru-RU"}, "ru"),
        ({"Accept-Language": "en-US,ru;q=0.9"}, "en"),
        ({}, "en"),  # No header
    ]

    for headers, expected in test_cases:
        request = MockRequest(headers)
        result = _extract_accept_language(request)
        if result == expected:
            print(f"  ✓ {headers.get('Accept-Language', 'None')} -> {result}")
        else:
            print(f"  ✗ {headers.get('Accept-Language', 'None')} -> {result} (expected {expected})")
            return False

    return True


def test_translations():
    """Test that translation keys work correctly."""
    print("\nTesting error message translations...")

    from i18n.backend_translations import get_error_message

    test_cases = [
        ("database_error", "en", "Database error occurred"),
        ("database_error", "ru", "Произошла ошибка базы данных"),
        ("invalid_input", "en", "Invalid input provided"),
        ("invalid_input", "ru", "Неверные входные данные"),
        ("internal_server_error", "en", "An internal server error occurred"),
        ("internal_server_error", "ru", "Произошла внутренняя ошибка сервера"),
    ]

    for key, locale, expected_prefix in test_cases:
        result = get_error_message(key, locale)
        if result.startswith(expected_prefix) or result == expected_prefix:
            print(f"  ✓ {key} ({locale}): {result[:50]}...")
        else:
            print(f"  ✗ {key} ({locale}): {result} (expected prefix: {expected_prefix})")
            return False

    return True


def test_exception_handlers_structure():
    """Test that exception handlers are properly structured."""
    print("\nTesting exception handler structure...")

    from main import app

    # Check that exception handlers are registered
    if not app.exception_handlers:
        print("  ✗ No exception handlers registered")
        return False

    # Check for specific exception handlers
    handler_types = [
        SQLAlchemyError,
        ValueError,
        Exception,
    ]

    from sqlalchemy.exc import SQLAlchemyError

    for exc_type in handler_types:
        if exc_type in app.exception_handlers or exc_type.__name__ in [
            h.__name__ if hasattr(h, "__name__") else str(h) for h in app.exception_handlers.keys()
        ]:
            print(f"  ✓ Exception handler for {exc_type.__name__} registered")
        else:
            print(f"  ✗ Exception handler for {exc_type.__name__} not found")
            return False

    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Exception Handler Translation Verification")
    print("=" * 60)

    tests = [
        test_import,
        test_extract_language,
        test_translations,
        test_exception_handlers_structure,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    if all(results):
        print("\n✓ All verification tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
