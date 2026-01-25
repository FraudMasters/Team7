#!/usr/bin/env python
"""Verification script for locale_helpers module."""
import sys

try:
    from utils.locale_helpers import (
        format_date,
        format_number,
        format_currency,
        get_supported_locales,
        _validate_locale,
        _parse_date_string,
        _format_integer_part,
    )
    print("✓ Successfully imported format_date")
    print("✓ Successfully imported format_number")
    print("✓ Successfully imported format_currency")
    print("✓ Successfully imported get_supported_locales")
    print("✓ Successfully imported _validate_locale")
    print("✓ Successfully imported _parse_date_string")
    print("✓ Successfully imported _format_integer_part")

    # Test basic functionality
    print("\n--- Testing format_date ---")
    en_date = format_date('2024-01-15', 'en')
    ru_date = format_date('2024-01-15', 'ru')
    print(f"English date: {en_date}")
    print(f"Russian date: {ru_date}")

    # Test format_number
    print("\n--- Testing format_number ---")
    en_number = format_number(1234.56, 'en')
    ru_number = format_number(1234.56, 'ru')
    print(f"English number: {en_number}")
    print(f"Russian number: {ru_number}")

    # Test format_currency
    print("\n--- Testing format_currency ---")
    en_currency = format_currency(1234.56, 'en', currency='USD')
    ru_currency = format_currency(1234.56, 'ru', currency='RUB')
    print(f"English currency: {en_currency}")
    print(f"Russian currency: {ru_currency}")

    # Test get_supported_locales
    print("\n--- Testing get_supported_locales ---")
    locales = get_supported_locales()
    print(f"Supported locales: {locales}")

    # Verify expected outputs
    assert en_date == "January 15, 2024", f"Expected 'January 15, 2024', got '{en_date}'"
    assert ru_date == "15 января 2024", f"Expected '15 января 2024', got '{ru_date}'"
    assert en_number == "1,234.56", f"Expected '1,234.56', got '{en_number}'"
    assert ru_number == "1 234,56", f"Expected '1 234,56', got '{ru_number}'"
    assert en_currency == "1,234.56 USD", f"Expected '1,234.56 USD', got '{en_currency}'"
    assert ru_currency == "1 234,56 RUB", f"Expected '1 234,56 RUB', got '{ru_currency}'"
    assert locales == ["en", "ru"], f"Expected ['en', 'ru'], got {locales}"

    print("\n✓ All assertions passed")
    print("\nOK - All imports and tests successful")
    sys.exit(0)

except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except AssertionError as e:
    print(f"✗ Assertion failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
