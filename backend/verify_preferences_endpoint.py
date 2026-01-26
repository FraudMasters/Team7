#!/usr/bin/env python3
"""
Verification script for preferences API endpoints.

This script tests the preferences endpoints to ensure:
1. GET /api/preferences/language returns current language (default: en)
2. PUT /api/preferences/language updates language preference
3. Invalid language codes are rejected with 422 status
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests

    API_URL = "http://localhost:8000/api/preferences/language"

    def test_get_default_language():
        """Test getting the default language preference."""
        print("Test 1: GET default language preference")

        try:
            response = requests.get(API_URL, timeout=5)

            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.json()}")

            if response.status_code == 200:
                data = response.json()
                if "language" in data and data["language"] in ["en", "ru"]:
                    print(f"  ✓ PASS: Returns valid language preference: {data['language']}")
                    return True
                else:
                    print("  ✗ FAIL: Invalid response format")
                    return False
            else:
                print(f"  ✗ FAIL: Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ FAIL: Request failed: {e}")
            return False

    def test_update_language_to_russian():
        """Test updating language preference to Russian."""
        print("\nTest 2: PUT language preference to Russian")

        try:
            response = requests.put(
                API_URL,
                json={"language": "ru"},
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.json()}")

            if response.status_code == 200:
                data = response.json()
                if data.get("language") == "ru":
                    print("  ✓ PASS: Language updated to Russian")
                    return True
                else:
                    print(f"  ✗ FAIL: Language not updated correctly: {data}")
                    return False
            else:
                print(f"  ✗ FAIL: Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ FAIL: Request failed: {e}")
            return False

    def test_update_language_to_english():
        """Test updating language preference back to English."""
        print("\nTest 3: PUT language preference to English")

        try:
            response = requests.put(
                API_URL,
                json={"language": "en"},
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.json()}")

            if response.status_code == 200:
                data = response.json()
                if data.get("language") == "en":
                    print("  ✓ PASS: Language updated to English")
                    return True
                else:
                    print(f"  ✗ FAIL: Language not updated correctly: {data}")
                    return False
            else:
                print(f"  ✗ FAIL: Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ FAIL: Request failed: {e}")
            return False

    def test_invalid_language():
        """Test rejection of invalid language code."""
        print("\nTest 4: PUT invalid language code")

        try:
            response = requests.put(
                API_URL,
                json={"language": "fr"},
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.json()}")

            if response.status_code == 422:
                print("  ✓ PASS: Returns 422 for unsupported language")
                return True
            else:
                print(f"  ✗ FAIL: Expected 422, got {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ FAIL: Request failed: {e}")
            return False

    def main():
        """Run all tests."""
        print("=" * 60)
        print("Preferences API Endpoint Verification")
        print("=" * 60)

        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code != 200:
                print("\n✗ ERROR: Server health check failed")
                sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"\n✗ ERROR: Cannot connect to server: {e}")
            print("\nPlease start the server first:")
            print("  cd backend")
            print("  python -m uvicorn main:app --reload --port 8000")
            sys.exit(1)

        # Run tests
        results = []
        results.append(test_get_default_language())
        results.append(test_update_language_to_russian())
        results.append(test_update_language_to_english())
        results.append(test_invalid_language())

        # Summary
        print("\n" + "=" * 60)
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        print("=" * 60)

        if all(results):
            print("\n✓ All tests PASSED")
            sys.exit(0)
        else:
            print("\n✗ Some tests FAILED")
            sys.exit(1)

    if __name__ == "__main__":
        main()

except ImportError:
    print("Note: requests library not installed. Install with:")
    print("  pip install requests")
    print("\nOr test manually with curl:")
    print("  # Get current language")
    print("  curl -X GET http://localhost:8000/api/preferences/language")
    print("  # Set language to Russian")
    print('  curl -X PUT http://localhost:8000/api/preferences/language -H "Content-Type: application/json" -d \'{"language": "ru"}\'')
    print("  # Set language to English")
    print('  curl -X PUT http://localhost:8000/api/preferences/language -H "Content-Type: application/json" -d \'{"language": "en"}\'')
    sys.exit(1)
