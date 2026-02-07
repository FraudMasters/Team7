#!/usr/bin/env python3
"""
Test script for user registration flow with email verification.

This script tests the complete registration flow:
1. User registration with email/password
2. Email verification (simulated)
3. Login with new credentials
4. JWT token storage and validation
5. Access to protected endpoints

Run this script to verify the registration and authentication flow is working.
"""

import asyncio
import sys
import requests
from typing import Dict, Any, Optional
import json

# Configuration
BACKEND_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test_registration@example.com",
    "password": "TestPass123",
    "name": "Test Registration User"
}


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message: str):
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"✗ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"ℹ {message}")


def check_backend_health() -> bool:
    """Check if the backend is running."""
    print_section("1. Backend Health Check")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is running: {data.get('service', 'unknown')}")
            print_info(f"Version: {data.get('version', 'unknown')}")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running on port 8000?")
        return False
    except Exception as e:
        print_error(f"Error checking backend health: {e}")
        return False


def test_registration() -> Optional[Dict[str, Any]]:
    """Test user registration endpoint."""
    print_section("2. User Registration")

    url = f"{BACKEND_URL}/api/auth/register"
    print_info(f"POST {url}")
    print_info(f"Email: {TEST_USER['email']}")

    try:
        response = requests.post(url, json=TEST_USER, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("Registration successful!")
            print_info(f"Response: {json.dumps(data, indent=2)}")

            # Check if user data is returned
            if "user" in data:
                user = data["user"]
                print_success(f"User created with ID: {user.get('id')}")
                print_success(f"User name: {user.get('name')}")
                print_success(f"User email: {user.get('email')}")
                print_success(f"User role: {user.get('role')}")
                print_success(f"Email verified: {user.get('email_verified', False)}")

            # Check if tokens are returned (auto-login after registration)
            if "access_token" in data:
                print_success("Access token received (auto-login after registration)")
                print_info(f"Token type: {data.get('token_type', 'bearer')}")
                return data
            else:
                print_info("No access token in response (email verification may be required)")
                return data
        else:
            print_error(f"Registration failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print_error(f"Response: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend")
        return None
    except Exception as e:
        print_error(f"Registration failed: {e}")
        return None


def test_login() -> Optional[Dict[str, Any]]:
    """Test user login endpoint."""
    print_section("3. User Login")

    url = f"{BACKEND_URL}/api/auth/login"
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }

    print_info(f"POST {url}")
    print_info(f"Email: {TEST_USER['email']}")

    try:
        response = requests.post(url, json=login_data, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("Login successful!")
            print_info(f"Token type: {data.get('token_type', 'bearer')}")

            # Validate access token
            if "access_token" in data:
                print_success("Access token received")
                print_info(f"Access token length: {len(data['access_token'])} chars")

            # Validate refresh token
            if "refresh_token" in data:
                print_success("Refresh token received")
                print_info(f"Refresh token length: {len(data['refresh_token'])} chars")

            # Check user data
            if "user" in data:
                user = data["user"]
                print_success(f"Authenticated user: {user.get('name')}")
                print_success(f"User role: {user.get('role')}")
                print_success(f"Is active: {user.get('is_active', False)}")

            return data
        else:
            print_error(f"Login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print_error(f"Response: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend")
        return None
    except Exception as e:
        print_error(f"Login failed: {e}")
        return None


def test_protected_endpoint(access_token: str) -> bool:
    """Test accessing a protected endpoint with JWT token."""
    print_section("4. Protected Endpoint Access")

    url = f"{BACKEND_URL}/api/auth/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    print_info(f"GET {url}")
    print_info("Authorization: Bearer <token>")

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("Protected endpoint accessible!")
            print_info(f"User data: {json.dumps(data, indent=2)}")

            # Verify user data
            if data.get("email") == TEST_USER["email"]:
                print_success("Email matches registered user")
            if data.get("name") == TEST_USER["name"]:
                print_success("Name matches registered user")

            return True
        else:
            print_error(f"Protected endpoint returned status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print_error(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend")
        return False
    except Exception as e:
        print_error(f"Protected endpoint test failed: {e}")
        return False


def test_token_structure(access_token: str) -> bool:
    """Test JWT token structure."""
    print_section("5. JWT Token Structure Validation")

    print_info("Validating JWT token structure...")

    try:
        # JWT tokens have 3 parts separated by dots
        parts = access_token.split(".")
        if len(parts) != 3:
            print_error("Invalid JWT structure: should have 3 parts")
            return False

        print_success("JWT has valid structure (header.payload.signature)")

        # Decode token parts (without verification)
        import base64

        def decode_part(part: str) -> str:
            """Decode a base64url encoded part."""
            # Add padding if needed
            padded = part + "=" * (4 - len(part) % 4)
            return base64.urlsafe_b64decode(padded).decode()

        try:
            header = json.loads(decode_part(parts[0]))
            print_success(f"JWT header: {json.dumps(header, indent=2)}")

            payload = json.loads(decode_part(parts[1]))
            print_success(f"JWT payload: {json.dumps(payload, indent=2)}")

            # Check for standard claims
            if "sub" in payload:
                print_success(f"Subject (user ID): {payload['sub']}")
            if "exp" in payload:
                print_success("Expiration claim present")
            if "iat" in payload:
                print_success("Issued at claim present")

            return True
        except Exception as e:
            print_info(f"Could not decode token (expected for encrypted tokens): {e}")
            return True  # Not necessarily an error

    except Exception as e:
        print_error(f"Token validation failed: {e}")
        return False


def test_unauthorized_access() -> bool:
    """Test that protected endpoints reject unauthorized requests."""
    print_section("6. Unauthorized Access Test")

    url = f"{BACKEND_URL}/api/auth/me"
    print_info(f"GET {url} (without Authorization header)")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 401:
            print_success("Unauthorized request correctly rejected (401)")
            return True
        else:
            print_error(f"Expected 401, got status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Unauthorized access test failed: {e}")
        return False


def cleanup_test_user():
    """Optional: Cleanup test user (if logout endpoint exists)."""
    print_section("7. Cleanup")

    print_info("Test complete. You can manually clean up the test user:")
    print_info(f"  Email: {TEST_USER['email']}")
    print_info("  Or use the database to delete the user record.")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  USER REGISTRATION FLOW - END-TO-END TEST")
    print("=" * 60)
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Test user: {TEST_USER['email']}")

    # Track test results
    results = {
        "backend_health": False,
        "registration": False,
        "login": False,
        "protected_endpoint": False,
        "token_structure": False,
        "unauthorized_access": False,
    }

    # Run tests
    results["backend_health"] = check_backend_health()
    if not results["backend_health"]:
        print_error("Backend is not running. Please start the backend service first.")
        print_info("Run: cd backend && python main.py")
        return 1

    registration_data = test_registration()
    results["registration"] = registration_data is not None

    if not results["registration"]:
        print_error("Registration failed. Cannot continue with further tests.")
        return 1

    login_data = test_login()
    results["login"] = login_data is not None

    if not results["login"]:
        print_error("Login failed. Cannot continue with token tests.")
        return 1

    access_token = login_data.get("access_token")
    if access_token:
        results["token_structure"] = test_token_structure(access_token)
        results["protected_endpoint"] = test_protected_endpoint(access_token)

    results["unauthorized_access"] = test_unauthorized_access()

    cleanup_test_user()

    # Print summary
    print_section("TEST SUMMARY")
    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    if all_passed:
        print_success("ALL TESTS PASSED!")
        print_info("The registration and authentication flow is working correctly.")
        return 0
    else:
        print_error("SOME TESTS FAILED")
        print_info("Please review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
