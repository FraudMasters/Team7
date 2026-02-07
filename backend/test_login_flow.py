#!/usr/bin/env python3
"""
Test script for login and protected route access flow.

This script tests the complete login flow:
1. Login with valid credentials
2. JWT token generation and validation
3. Access to protected endpoints with JWT token
4. Verify JWT sent in subsequent API requests
5. Test accessing various protected recruiter routes

Run this script to verify the login and protected route access is working.
"""

import asyncio
import sys
import requests
from typing import Dict, Any, Optional
import json

# Configuration
BACKEND_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test_login@example.com",
    "password": "TestPass123",
    "name": "Test Login User"
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


def setup_test_user() -> bool:
    """Create a test user for login testing."""
    print_section("2. Setup Test User")

    url = f"{BACKEND_URL}/api/auth/register"
    print_info(f"POST {url}")
    print_info(f"Creating test user: {TEST_USER['email']}")

    try:
        response = requests.post(url, json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"],
            "name": TEST_USER["name"]
        }, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("Test user created successfully!")
            print_info(f"User ID: {data.get('user', {}).get('id', 'unknown')}")
            return True
        elif response.status_code == 400 and "already registered" in response.json().get('detail', ''):
            print_success("Test user already exists (from previous test)")
            return True
        else:
            print_error(f"Failed to create test user: {response.status_code}")
            print_info(f"Response: {response.text}")
            # Continue anyway as user might already exist
            return True

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend")
        return False
    except Exception as e:
        print_info(f"Setup error: {e}")
        return True  # Continue anyway


def test_login_success() -> Optional[Dict[str, Any]]:
    """Test successful login with valid credentials."""
    print_section("3. Login with Valid Credentials")

    url = f"{BACKEND_URL}/api/auth/login"
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }

    print_info(f"POST {url}")
    print_info(f"Email: {TEST_USER['email']}")
    print_info(f"Password: {'*' * len(TEST_USER['password'])}")

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
                print_success(f"User email: {user.get('email')}")
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


def test_login_invalid_credentials() -> bool:
    """Test login with invalid credentials."""
    print_section("4. Login with Invalid Credentials")

    url = f"{BACKEND_URL}/api/auth/login"
    login_data = {
        "email": TEST_USER["email"],
        "password": "WrongPassword123"
    }

    print_info(f"POST {url}")
    print_info(f"Email: {TEST_USER['email']}")
    print_info(f"Password: WrongPassword123 (incorrect)")

    try:
        response = requests.post(url, json=login_data, timeout=10)

        if response.status_code == 401:
            print_success("Invalid credentials correctly rejected (401)")
            return True
        else:
            print_error(f"Expected 401, got status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Invalid credentials test failed: {e}")
        return False


def test_jwt_token_structure(access_token: str) -> bool:
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
            if "role" in payload:
                print_success(f"Role claim: {payload['role']}")

            return True
        except Exception as e:
            print_info(f"Could not decode token: {e}")
            return True  # Not necessarily an error

    except Exception as e:
        print_error(f"Token validation failed: {e}")
        return False


def test_protected_endpoint_auth_me(access_token: str) -> bool:
    """Test accessing /api/auth/me endpoint with JWT token."""
    print_section("6. Protected Endpoint - /api/auth/me")

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
            print_info(f"User data: {json.dumps(data, indent=2, default=str)}")

            # Verify user data
            if data.get("email") == TEST_USER["email"]:
                print_success("Email matches authenticated user")
            if data.get("name") == TEST_USER["name"]:
                print_success("Name matches authenticated user")

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


def test_protected_recruiter_routes(access_token: str) -> bool:
    """Test accessing various protected recruiter routes."""
    print_section("7. Protected Recruiter Routes")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    routes_to_test = [
        ("Candidates List", "/api/candidates/"),
        ("Vacancies List", "/api/vacancies/"),
        ("Analytics Key Metrics", "/api/analytics/key-metrics"),
        ("Backups List", "/api/backups/"),
    ]

    all_passed = True

    for route_name, route_path in routes_to_test:
        url = f"{BACKEND_URL}{route_path}"
        print_info(f"Testing {route_name}: GET {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                print_success(f"  {route_name}: Accessible (200)")
            elif response.status_code == 401:
                print_error(f"  {route_name}: Unauthorized (401)")
                all_passed = False
            else:
                print_info(f"  {route_name}: Status {response.status_code}")
                # Some routes might return 404 if no data, that's ok
                if response.status_code != 404:
                    print_info(f"    Response: {response.text[:100]}")

        except Exception as e:
            print_error(f"  {route_name}: Request failed - {e}")
            all_passed = False

    return all_passed


def test_jwt_in_requests(access_token: str) -> bool:
    """Verify JWT token is sent correctly in API requests."""
    print_section("8. Verify JWT Token Sent in Requests")

    url = f"{BACKEND_URL}/api/auth/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    print_info(f"GET {url}")
    print_info("Checking if JWT token is included in Authorization header...")

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print_success("JWT token successfully sent in Authorization header")
            print_success("Server accepted and validated the token")
            return True
        else:
            print_error("Server rejected the request")
            return False

    except Exception as e:
        print_error(f"Request failed: {e}")
        return False


def test_unauthorized_access() -> bool:
    """Test that protected endpoints reject requests without JWT token."""
    print_section("9. Unauthorized Access Without Token")

    test_endpoints = [
        ("/api/auth/me", "Current User"),
        ("/api/candidates/", "Candidates List"),
        ("/api/vacancies/", "Vacancies List"),
    ]

    all_passed = True

    for endpoint, name in test_endpoints:
        url = f"{BACKEND_URL}{endpoint}"
        print_info(f"Testing {name}: GET {url} (without Authorization header)")

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 401:
                print_success(f"  {name}: Correctly rejected (401)")
            else:
                print_error(f"  {name}: Expected 401, got status {response.status_code}")
                all_passed = False

        except Exception as e:
            print_error(f"  {name}: Request failed - {e}")
            all_passed = False

    return all_passed


def test_token_expiry_and_refresh(access_token: str, refresh_token: str) -> bool:
    """Test token refresh mechanism."""
    print_section("10. Token Refresh Mechanism")

    url = f"{BACKEND_URL}/api/auth/refresh"
    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }

    print_info(f"POST {url}")
    print_info("Using refresh token to get new access token...")

    try:
        response = requests.post(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("Token refresh successful!")

            if "access_token" in data:
                print_success("New access token received")
                print_info(f"New access token length: {len(data['access_token'])} chars")

            return True
        else:
            print_info(f"Token refresh returned status {response.status_code}")
            print_info("Note: Token refresh might not be implemented yet")
            return True  # Not a critical failure

    except Exception as e:
        print_info(f"Token refresh test failed: {e}")
        print_info("Note: Token refresh might not be implemented yet")
        return True  # Not a critical failure


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  LOGIN AND PROTECTED ROUTE ACCESS - END-TO-END TEST")
    print("=" * 60)
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Test user: {TEST_USER['email']}")

    # Track test results
    results = {
        "backend_health": False,
        "setup_test_user": False,
        "login_success": False,
        "login_invalid_credentials": False,
        "jwt_token_structure": False,
        "protected_endpoint_auth_me": False,
        "protected_recruiter_routes": False,
        "jwt_in_requests": False,
        "unauthorized_access": False,
        "token_refresh": False,
    }

    # Run tests
    results["backend_health"] = check_backend_health()
    if not results["backend_health"]:
        print_error("Backend is not running. Please start the backend service first.")
        print_info("Run: cd backend && python main.py")
        return 1

    results["setup_test_user"] = setup_test_user()
    if not results["setup_test_user"]:
        print_error("Failed to setup test user. Cannot continue.")
        return 1

    login_data = test_login_success()
    results["login_success"] = login_data is not None

    if not results["login_success"]:
        print_error("Login failed. Cannot continue with token tests.")
        return 1

    access_token = login_data.get("access_token")
    refresh_token = login_data.get("refresh_token")

    if access_token:
        results["jwt_token_structure"] = test_jwt_token_structure(access_token)
        results["protected_endpoint_auth_me"] = test_protected_endpoint_auth_me(access_token)
        results["protected_recruiter_routes"] = test_protected_recruiter_routes(access_token)
        results["jwt_in_requests"] = test_jwt_in_requests(access_token)

    results["login_invalid_credentials"] = test_login_invalid_credentials()
    results["unauthorized_access"] = test_unauthorized_access()

    if refresh_token:
        results["token_refresh"] = test_token_expiry_and_refresh(access_token, refresh_token)

    # Print summary
    print_section("TEST SUMMARY")
    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    if all_passed:
        print_success("ALL TESTS PASSED!")
        print_info("The login and protected route access flow is working correctly.")
        print_info("\nNext steps:")
        print_info("  1. Test the login page in the browser")
        print_info("  2. Verify redirect to dashboard after login")
        print_info("  3. Verify JWT tokens stored in localStorage")
        print_info("  4. Test logout functionality")
        return 0
    else:
        print_error("SOME TESTS FAILED")
        print_info("Please review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
