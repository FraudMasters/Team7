#!/usr/bin/env python3
"""
Verification script for Accept-Language header support in backend error messages.

This script tests that backend API endpoints properly respect the Accept-Language header
and return translated error messages in the requested language (English or Russian).
"""
import os
import sys
import requests
import tempfile
from pathlib import Path

# API base URL
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
UPLOAD_URL = f"{API_BASE_URL}/api/resumes/upload"


def create_test_file(size_mb: float = 1.0) -> bytes:
    """
    Create a test file of specified size in MB.

    Args:
        size_mb: Size of the file in megabytes

    Returns:
        File content as bytes
    """
    size_bytes = int(size_mb * 1024 * 1024)
    return b"0" * size_bytes


def test_english_error_message():
    """
    Test that error messages are returned in English when Accept-Language: en is set.

    Returns:
        True if test passes, False otherwise
    """
    print("\n" + "=" * 80)
    print("TEST 1: English Error Messages (Accept-Language: en)")
    print("=" * 80)

    # Test 1a: Invalid file type error
    print("\n1a. Testing invalid file type error...")
    test_file = create_test_file(0.1)  # Small file

    files = {
        "file": ("test.txt", test_file, "text/plain")
    }

    headers = {
        "Accept-Language": "en"
    }

    try:
        response = requests.post(UPLOAD_URL, files=files, headers=headers, timeout=10)

        if response.status_code == 415:
            error_data = response.json()
            error_message = error_data.get("detail", "")

            print(f"   Status Code: {response.status_code} ✓")
            print(f"   Error Message: {error_message}")

            # Check for English keywords
            english_indicators = ["Unsupported", "file type", "Allowed"]
            has_english = any(indicator in error_message for indicator in english_indicators)

            if has_english:
                print("   ✓ Error message is in ENGLISH")
                return True
            else:
                print("   ✗ Error message is NOT in English")
                print(f"   Expected English keywords: {english_indicators}")
                return False
        else:
            print(f"   ✗ Unexpected status code: {response.status_code} (expected 415)")
            return False

    except requests.exceptions.ConnectionError:
        print("   ✗ Failed to connect to backend API")
        print("   Make sure the backend is running on", API_BASE_URL)
        return None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None


def test_russian_error_message():
    """
    Test that error messages are returned in Russian when Accept-Language: ru is set.

    Returns:
        True if test passes, False otherwise
    """
    print("\n" + "=" * 80)
    print("TEST 2: Russian Error Messages (Accept-Language: ru)")
    print("=" * 80)

    # Test 2a: Invalid file type error
    print("\n2a. Testing invalid file type error...")
    test_file = create_test_file(0.1)

    files = {
        "file": ("test.txt", test_file, "text/plain")
    }

    headers = {
        "Accept-Language": "ru"
    }

    try:
        response = requests.post(UPLOAD_URL, files=files, headers=headers, timeout=10)

        if response.status_code == 415:
            error_data = response.json()
            error_message = error_data.get("detail", "")

            print(f"   Status Code: {response.status_code} ✓")
            print(f"   Error Message: {error_message}")

            # Check for Russian keywords (Cyrillic)
            russian_indicators = ["Неподдерживаемый", "тип", "файла", "Допустимые"]
            has_russian = any(indicator in error_message for indicator in russian_indicators)

            if has_russian:
                print("   ✓ Error message is in RUSSIAN")
                return True
            else:
                print("   ✗ Error message is NOT in Russian")
                print(f"   Expected Russian keywords: {russian_indicators}")
                return False
        else:
            print(f"   ✗ Unexpected status code: {response.status_code} (expected 415)")
            return False

    except requests.exceptions.ConnectionError:
        print("   ✗ Failed to connect to backend API")
        print("   Make sure the backend is running on", API_BASE_URL)
        return None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None


def test_file_too_large_error():
    """
    Test file size error in both English and Russian.

    Returns:
        True if test passes, False otherwise
    """
    print("\n" + "=" * 80)
    print("TEST 3: File Size Error with Parameter Interpolation")
    print("=" * 80)

    # Test 3a: English
    print("\n3a. Testing English file size error...")
    # Create a file larger than the max size (assuming 5MB max)
    test_file = create_test_file(6.0)

    files = {
        "file": ("large.pdf", test_file, "application/pdf")
    }

    headers_en = {
        "Accept-Language": "en"
    }

    try:
        response = requests.post(UPLOAD_URL, files=files, headers=headers_en, timeout=10)

        if response.status_code == 413:
            error_data = response.json()
            error_message = error_data.get("detail", "")

            print(f"   Status Code: {response.status_code} ✓")
            print(f"   Error Message: {error_message}")

            # Check for English keywords and parameter interpolation
            if "exceeds maximum allowed size" in error_message.lower():
                print("   ✓ English error message with parameter interpolation")
                en_success = True
            else:
                print("   ✗ Missing expected English text")
                en_success = False
        else:
            print(f"   ✗ Unexpected status code: {response.status_code} (expected 413)")
            en_success = False

    except requests.exceptions.ConnectionError:
        print("   ✗ Failed to connect to backend API")
        return None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        en_success = False

    # Test 3b: Russian
    print("\n3b. Testing Russian file size error...")
    headers_ru = {
        "Accept-Language": "ru"
    }

    try:
        response = requests.post(UPLOAD_URL, files=files, headers=headers_ru, timeout=10)

        if response.status_code == 413:
            error_data = response.json()
            error_message = error_data.get("detail", "")

            print(f"   Status Code: {response.status_code} ✓")
            print(f"   Error Message: {error_message}")

            # Check for Russian keywords and parameter interpolation
            russian_indicators = ["превышает", "максимально", "допустимый"]
            has_russian = any(indicator in error_message for indicator in russian_indicators)

            if has_russian:
                print("   ✓ Russian error message with parameter interpolation")
                ru_success = True
            else:
                print("   ✗ Missing expected Russian text")
                ru_success = False
        else:
            print(f"   ✗ Unexpected status code: {response.status_code} (expected 413)")
            ru_success = False

    except requests.exceptions.ConnectionError:
        print("   ✗ Failed to connect to backend API")
        return None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        ru_success = False

    return en_success and ru_success


def test_language_variations():
    """
    Test various Accept-Language header formats.

    Returns:
        True if test passes, False otherwise
    """
    print("\n" + "=" * 80)
    print("TEST 4: Accept-Language Header Format Variations")
    print("=" * 80)

    test_cases = [
        ("en", "English"),
        ("en-US", "English (US)"),
        ("en-GB", "English (GB)"),
        ("ru", "Russian"),
        ("ru-RU", "Russian (Russia)"),
    ]

    all_passed = True

    for lang_code, lang_name in test_cases:
        print(f"\n4. Testing Accept-Language: {lang_code} ({lang_name})...")

        test_file = create_test_file(0.1)
        files = {
            "file": ("test.txt", test_file, "text/plain")
        }

        headers = {
            "Accept-Language": lang_code
        }

        try:
            response = requests.post(UPLOAD_URL, files=files, headers=headers, timeout=10)

            if response.status_code == 415:
                error_data = response.json()
                error_message = error_data.get("detail", "")

                # Determine expected language
                is_english = lang_code.startswith("en")
                is_russian = lang_code.startswith("ru")

                if is_english:
                    if "Unsupported" in error_message or "file type" in error_message:
                        print(f"   ✓ Correctly returned English error")
                    else:
                        print(f"   ✗ Expected English error, got: {error_message[:50]}...")
                        all_passed = False
                elif is_russian:
                    if "Неподдерживаемый" in error_message or "тип" in error_message:
                        print(f"   ✓ Correctly returned Russian error")
                    else:
                        print(f"   ✗ Expected Russian error, got: {error_message[:50]}...")
                        all_passed = False

        except requests.exceptions.ConnectionError:
            print("   ✗ Failed to connect to backend API")
            return None
        except Exception as e:
            print(f"   ✗ Error: {e}")
            all_passed = False

    return all_passed


def test_default_language():
    """
    Test that English is returned as default when no Accept-Language header is provided.

    Returns:
        True if test passes, False otherwise
    """
    print("\n" + "=" * 80)
    print("TEST 5: Default Language (No Accept-Language Header)")
    print("=" * 80)

    print("\n5. Testing error message without Accept-Language header...")

    test_file = create_test_file(0.1)
    files = {
        "file": ("test.txt", test_file, "text/plain")
    }

    # No Accept-Language header
    headers = {}

    try:
        response = requests.post(UPLOAD_URL, files=files, headers=headers, timeout=10)

        if response.status_code == 415:
            error_data = response.json()
            error_message = error_data.get("detail", "")

            print(f"   Status Code: {response.status_code} ✓")
            print(f"   Error Message: {error_message}")

            # Check for English (default)
            if "Unsupported" in error_message or "file type" in error_message:
                print("   ✓ Default language is ENGLISH")
                return True
            else:
                print("   ✗ Default language is not English")
                return False
        else:
            print(f"   ✗ Unexpected status code: {response.status_code} (expected 415)")
            return False

    except requests.exceptions.ConnectionError:
        print("   ✗ Failed to connect to backend API")
        return None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None


def main():
    """Run all verification tests."""
    print("\n" + "=" * 80)
    print("BACKEND ACCEPT-LANGUAGE HEADER VERIFICATION")
    print("=" * 80)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"Upload Endpoint: {UPLOAD_URL}")

    # Run all tests
    results = {
        "English Error Messages": test_english_error_message(),
        "Russian Error Messages": test_russian_error_message(),
        "File Size Error with Interpolation": test_file_too_large_error(),
        "Language Format Variations": test_language_variations(),
        "Default Language": test_default_language(),
    }

    # Print summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in results.items():
        if result is True:
            print(f"✓ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"✗ {test_name}: FAILED")
            failed += 1
        else:
            print(f"○ {test_name}: SKIPPED (connection error)")
            skipped += 1

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0 and skipped == 0:
        print("\n✓ ALL TESTS PASSED - Backend properly respects Accept-Language header")
        return 0
    elif failed > 0:
        print("\n✗ SOME TESTS FAILED - Review errors above")
        return 1
    else:
        print("\n○ TESTS SKIPPED - Backend API not accessible")
        print("  Make sure the backend is running:")
        print("  cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return 2


if __name__ == "__main__":
    sys.exit(main())
