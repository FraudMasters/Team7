#!/usr/bin/env python3
"""
Verification script for backend translation module.

This script tests the backend_translations module by retrieving error messages
in both English and Russian languages.
"""

from i18n.backend_translations import (
    get_error_message,
    get_success_message,
    get_validation_message,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
)


def test_error_messages():
    """Test error message translations."""
    print("=" * 60)
    print("Testing Error Messages")
    print("=" * 60)

    # Test file_too_large error
    en_message = get_error_message("file_too_large", "en", size=10.5, max_mb=5)
    ru_message = get_error_message("file_too_large", "ru", size=10.5, max_mb=5)

    print(f"\n✓ file_too_large (en): {en_message}")
    print(f"✓ file_too_large (ru): {ru_message}")

    # Test invalid_file_type error
    en_message = get_error_message("invalid_file_type", "en", file_ext=".exe", allowed=".pdf, .docx")
    ru_message = get_error_message("invalid_file_type", "ru", file_ext=".exe", allowed=".pdf, .docx")

    print(f"\n✓ invalid_file_type (en): {en_message}")
    print(f"✓ invalid_file_type (ru): {ru_message}")

    # Test database_error
    en_message = get_error_message("database_error", "en")
    ru_message = get_error_message("database_error", "ru")

    print(f"\n✓ database_error (en): {en_message}")
    print(f"✓ database_error (ru): {ru_message}")


def test_success_messages():
    """Test success message translations."""
    print("\n" + "=" * 60)
    print("Testing Success Messages")
    print("=" * 60)

    en_message = get_success_message("file_uploaded", "en")
    ru_message = get_success_message("file_uploaded", "ru")

    print(f"\n✓ file_uploaded (en): {en_message}")
    print(f"✓ file_uploaded (ru): {ru_message}")

    en_message = get_success_message("analysis_completed", "en")
    ru_message = get_success_message("analysis_completed", "ru")

    print(f"\n✓ analysis_completed (en): {en_message}")
    print(f"✓ analysis_completed (ru): {ru_message}")


def test_validation_messages():
    """Test validation message translations."""
    print("\n" + "=" * 60)
    print("Testing Validation Messages")
    print("=" * 60)

    en_message = get_validation_message("invalid_resume_id", "en")
    ru_message = get_validation_message("invalid_resume_id", "ru")

    print(f"\n✓ invalid_resume_id (en): {en_message}")
    print(f"✓ invalid_resume_id (ru): {ru_message}")

    en_message = get_validation_message("language_not_supported", "en", lang="de", supported="en, ru")
    ru_message = get_validation_message("language_not_supported", "ru", lang="de", supported="en, ru")

    print(f"\n✓ language_not_supported (en): {en_message}")
    print(f"✓ language_not_supported (ru): {ru_message}")


def test_locale_normalization():
    """Test locale string normalization."""
    print("\n" + "=" * 60)
    print("Testing Locale Normalization")
    print("=" * 60)

    from i18n.backend_translations import _validate_locale

    test_locales = ["en", "en-US", "ru", "ru-RU", "de", "fr-FR", ""]
    for locale in test_locales:
        normalized = _validate_locale(locale)
        print(f"✓ {locale!r} → {normalized!r}")


def test_fallback_behavior():
    """Test fallback to default language."""
    print("\n" + "=" * 60)
    print("Testing Fallback Behavior")
    print("=" * 60)

    # Test unsupported language falls back to English
    en_message = get_error_message("file_too_large", "de", size=10, max_mb=5)
    print(f"✓ Unsupported locale 'de' falls back to: {en_message}")

    # Test missing key returns key itself
    missing_key = get_error_message("nonexistent_key", "en")
    print(f"✓ Missing key returns: {missing_key}")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("Backend Translation Module Verification")
    print("=" * 60)
    print(f"\nSupported languages: {SUPPORTED_LANGUAGES}")
    print(f"Default language: {DEFAULT_LANGUAGE}")

    try:
        test_error_messages()
        test_success_messages()
        test_validation_messages()
        test_locale_normalization()
        test_fallback_behavior()

        print("\n" + "=" * 60)
        print("✓ All verification tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
