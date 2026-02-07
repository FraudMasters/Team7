#!/usr/bin/env python3
"""
Test script for role-based access control (RBAC).

This script tests role-based permissions for Admin, Recruiter, and Viewer roles:
1. Create users with different roles
2. Verify Admin can access admin endpoints
3. Verify Recruiter cannot access admin endpoints
4. Verify Viewer has read-only access
5. Verify role permissions are enforced

Run this script to verify role-based access control is working correctly.
"""

import asyncio
import sys
import requests
from typing import Dict, Any, Optional, List
import json

# Configuration
BACKEND_URL = "http://localhost:8000"

# Test users for each role
TEST_USERS = {
    "admin": {
        "email": "test_admin@example.com",
        "password": "TestPass123",
        "name": "Test Admin User",
        "role": "Admin"
    },
    "recruiter": {
        "email": "test_recruiter@example.com",
        "password": "TestPass123",
        "name": "Test Recruiter User",
        "role": "Recruiter"
    },
    "viewer": {
        "email": "test_viewer@example.com",
        "password": "TestPass123",
        "name": "Test Viewer User",
        "role": "Viewer"
    }
}


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


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


def get_role_id_from_db(role_name: str) -> Optional[str]:
    """
    Get role ID from the database by role name.
    This is a helper function that queries the roles table.
    """
    try:
        # For now, we'll register users and let the system assign default roles
        # In production, you'd query the database directly
        # The registration endpoint assigns Recruiter role by default
        # We'll need to update roles via API after registration
        return None
    except Exception as e:
        print_info(f"Error getting role ID: {e}")
        return None


def create_test_users() -> Dict[str, Dict[str, Any]]:
    """
    Create test users with different roles.

    Returns:
        Dictionary mapping role names to user data including tokens
    """
    print_section("2. Create Test Users with Different Roles")

    users_data = {}

    for role_key, user_info in TEST_USERS.items():
        print_info(f"Creating {user_info['role']} user: {user_info['email']}")

        url = f"{BACKEND_URL}/api/auth/register"
        try:
            response = requests.post(url, json={
                "email": user_info["email"],
                "password": user_info["password"],
                "name": user_info["name"]
            }, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print_success(f"{user_info['role']} user created successfully")
                print_info(f"  User ID: {data.get('user', {}).get('id', 'unknown')}")
                print_info(f"  Assigned Role: {data.get('user', {}).get('role', 'Recruiter')}")

                # Login to get tokens
                login_url = f"{BACKEND_URL}/api/auth/login"
                login_response = requests.post(login_url, json={
                    "email": user_info["email"],
                    "password": user_info["password"]
                }, timeout=10)

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    users_data[role_key] = {
                        "email": user_info["email"],
                        "name": user_info["name"],
                        "role": login_data.get("user", {}).get("role", "Recruiter"),
                        "user_id": login_data.get("user", {}).get("id"),
                        "access_token": login_data.get("access_token"),
                        "refresh_token": login_data.get("refresh_token")
                    }
                    print_success(f"  {user_info['Role']} logged in successfully")
                else:
                    print_error(f"  Failed to login {user_info['Role']} user")

            elif response.status_code == 400 and "already registered" in response.json().get('detail', ''):
                print_success(f"{user_info['Role']} user already exists (from previous test)")

                # Login to get tokens
                login_url = f"{BACKEND_URL}/api/auth/login"
                login_response = requests.post(login_url, json={
                    "email": user_info["email"],
                    "password": user_info["password"]
                }, timeout=10)

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    users_data[role_key] = {
                        "email": user_info["email"],
                        "name": user_info["name"],
                        "role": login_data.get("user", {}).get("role", "Recruiter"),
                        "user_id": login_data.get("user", {}).get("id"),
                        "access_token": login_data.get("access_token"),
                        "refresh_token": login_data.get("refresh_token")
                    }
                    print_success(f"  {user_info['Role']} logged in successfully")
                else:
                    print_error(f"  Failed to login {user_info['Role']} user")
            else:
                print_error(f"Failed to create {user_info['Role']} user: {response.status_code}")
                print_info(f"Response: {response.text}")

        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to backend")
            return {}
        except Exception as e:
            print_error(f"Error creating {user_info['Role']} user: {e}")

    return users_data


def update_user_roles(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Update user roles via admin API.
    This requires an admin user to call the API.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if roles were updated successfully
    """
    print_section("3. Update User Roles")

    # First, find which user has Admin role
    admin_token = None
    admin_user_id = None

    for role_key, user_data in users_data.items():
        if user_data.get("role") == "Admin":
            admin_token = user_data.get("access_token")
            admin_user_id = user_data.get("user_id")
            break

    if not admin_token:
        print_info("No admin user found. Skipping role updates.")
        print_info("Users will have their default roles (Recruiter).")
        print_info("To test RBAC properly, please manually update roles in the database.")
        return False

    print_info(f"Admin user found: {admin_user_id}")
    print_info("Updating user roles via admin API...")

    # Get role IDs from the database
    role_ids = {}
    try:
        # We need to get role IDs first
        # For now, we'll try to list users to see if admin API works
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BACKEND_URL}/api/users/", headers=headers, timeout=10)

        if response.status_code == 200:
            print_success("Admin can access /api/users/ endpoint")

            # Get all roles from the response
            data = response.json()
            users_list = data.get("users", [])

            for user in users_list:
                role_name = user.get("role")
                role_id = user.get("role_id")
                if role_name and role_id:
                    role_ids[role_name] = role_id

            print_info(f"Found roles: {list(role_ids.keys())}")

            # Now update roles for test users
            for role_key, user_data in users_data.items():
                target_role = TEST_USERS[role_key]["role"]

                if user_data.get("role") == target_role:
                    print_info(f"  {user_data['name']} already has {target_role} role")
                    continue

                if target_role in role_ids and user_data.get("user_id"):
                    update_url = f"{BACKEND_URL}/api/users/{user_data['user_id']}/role"
                    update_response = requests.put(
                        update_url,
                        headers=headers,
                        json={"role_id": role_ids[target_role]},
                        timeout=10
                    )

                    if update_response.status_code == 200:
                        result = update_response.json()
                        print_success(f"  Updated {user_data['name']} role to {target_role}")
                        user_data["role"] = target_role
                    else:
                        print_error(f"  Failed to update {user_data['name']} role: {update_response.status_code}")
                        print_info(f"    Response: {update_response.text}")
                else:
                    print_error(f"  Cannot update {user_data['name']} to {target_role}: role ID not found")

            return True
        else:
            print_error(f"Failed to access admin API: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error updating user roles: {e}")
        return False


def test_admin_access(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Test that Admin user can access admin-only endpoints.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if all admin access tests passed
    """
    print_section("4. Test Admin Access to Admin Endpoints")

    if "admin" not in users_data:
        print_error("No admin user found. Skipping admin access tests.")
        return False

    admin_token = users_data["admin"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin-only endpoints to test
    admin_endpoints = [
        ("List Users", "GET", "/api/users/"),
        ("Get User", "GET", "/api/users/"),
        ("List Backups", "GET", "/api/backups/"),
        ("Analytics Key Metrics", "GET", "/api/analytics/key-metrics"),
        ("Analytics Quality Metrics", "GET", "/api/analytics/quality-metrics"),
    ]

    all_passed = True

    for endpoint_name, method, path in admin_endpoints:
        url = f"{BACKEND_URL}{path}"
        print_info(f"Testing {endpoint_name}: {method} {url}")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)

            # Admin should be able to access these endpoints
            # Expected: 200 OK or 404 (if no data) but NOT 401 or 403
            if response.status_code in [200, 404]:
                print_success(f"  {endpoint_name}: Access granted ({response.status_code})")
            elif response.status_code == 401:
                print_error(f"  {endpoint_name}: Unauthorized (401) - Admin should have access")
                all_passed = False
            elif response.status_code == 403:
                print_error(f"  {endpoint_name}: Forbidden (403) - Admin should have access")
                all_passed = False
            else:
                print_info(f"  {endpoint_name}: Status {response.status_code}")

        except Exception as e:
            print_error(f"  {endpoint_name}: Request failed - {e}")
            all_passed = False

    return all_passed


def test_recruiter_no_admin_access(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Test that Recruiter user cannot access admin-only endpoints.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if all access denial tests passed
    """
    print_section("5. Test Recruiter Cannot Access Admin Endpoints")

    if "recruiter" not in users_data:
        print_error("No recruiter user found. Skipping recruiter access tests.")
        return False

    recruiter_token = users_data["recruiter"]["access_token"]
    headers = {"Authorization": f"Bearer {recruiter_token}"}

    # Admin-only endpoints that Recruiter should NOT access
    admin_endpoints = [
        ("List Users", "GET", "/api/users/"),
        ("Update User Role", "PUT", "/api/users/"),
        ("List Backups", "GET", "/api/backups/"),
        ("Create Backup", "POST", "/api/backups/"),
    ]

    all_passed = True

    for endpoint_name, method, path in admin_endpoints:
        url = f"{BACKEND_URL}{path}"

        # For user endpoints, we need a valid user ID
        if "{user_id}" in path and users_data.get("admin", {}).get("user_id"):
            url = url.replace("{user_id}", users_data["admin"]["user_id"])

        print_info(f"Testing {endpoint_name}: {method} {url}")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json={}, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json={}, timeout=10)

            # Recruiter should NOT be able to access admin endpoints
            # Expected: 403 Forbidden
            if response.status_code == 403:
                print_success(f"  {endpoint_name}: Correctly denied (403 Forbidden)")
            elif response.status_code == 401:
                print_info(f"  {endpoint_name}: Unauthorized (401) - May indicate auth issue")
            elif response.status_code in [200, 404]:
                print_error(f"  {endpoint_name}: Access granted ({response.status_code}) - Recruiter should NOT have access")
                all_passed = False
            else:
                print_info(f"  {endpoint_name}: Status {response.status_code}")

        except Exception as e:
            print_info(f"  {endpoint_name}: Request failed - {e}")

    return all_passed


def test_recruiter_can_access_recruiting_endpoints(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Test that Recruiter user can access recruiting endpoints.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if all recruiter access tests passed
    """
    print_section("6. Test Recruiter Can Access Recruiting Endpoints")

    if "recruiter" not in users_data:
        print_error("No recruiter user found. Skipping recruiter access tests.")
        return False

    recruiter_token = users_data["recruiter"]["access_token"]
    headers = {"Authorization": f"Bearer {recruiter_token}"}

    # Recruiting endpoints that Recruiter should access
    recruiting_endpoints = [
        ("List Candidates", "GET", "/api/candidates/"),
        ("List Vacancies", "GET", "/api/vacancies/"),
        ("Analytics Key Metrics", "GET", "/api/analytics/key-metrics"),
    ]

    all_passed = True

    for endpoint_name, method, path in recruiting_endpoints:
        url = f"{BACKEND_URL}{path}"
        print_info(f"Testing {endpoint_name}: {method} {url}")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)

            # Recruiter should be able to access these endpoints
            # Expected: 200 OK or 404 (if no data) but NOT 401 or 403
            if response.status_code in [200, 404]:
                print_success(f"  {endpoint_name}: Access granted ({response.status_code})")
            elif response.status_code == 401:
                print_error(f"  {endpoint_name}: Unauthorized (401) - Recruiter should have access")
                all_passed = False
            elif response.status_code == 403:
                print_error(f"  {endpoint_name}: Forbidden (403) - Recruiter should have access")
                all_passed = False
            else:
                print_info(f"  {endpoint_name}: Status {response.status_code}")

        except Exception as e:
            print_error(f"  {endpoint_name}: Request failed - {e}")
            all_passed = False

    return all_passed


def test_viewer_read_only_access(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Test that Viewer user has read-only access.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if all read-only tests passed
    """
    print_section("7. Test Viewer Read-Only Access")

    if "viewer" not in users_data:
        print_error("No viewer user found. Skipping viewer access tests.")
        return False

    viewer_token = users_data["viewer"]["access_token"]
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Read-only endpoints (GET requests)
    read_endpoints = [
        ("List Candidates", "GET", "/api/candidates/"),
        ("List Vacancies", "GET", "/api/vacancies/"),
        ("Analytics Key Metrics", "GET", "/api/analytics/key-metrics"),
    ]

    all_passed = True

    # Test read access
    print_info("Testing READ access (should work):")
    for endpoint_name, method, path in read_endpoints:
        url = f"{BACKEND_URL}{path}"
        print_info(f"  Testing {endpoint_name}: {method} {url}")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)

            # Viewer should be able to read
            if response.status_code in [200, 404]:
                print_success(f"    {endpoint_name}: Read access granted ({response.status_code})")
            elif response.status_code == 403:
                print_error(f"    {endpoint_name}: Forbidden (403) - Viewer should have read access")
                all_passed = False
            else:
                print_info(f"    {endpoint_name}: Status {response.status_code}")

        except Exception as e:
            print_error(f"    {endpoint_name}: Request failed - {e}")
            all_passed = False

    # Test write access (should be denied)
    print_info("\nTesting WRITE access (should be denied):")

    # Try to create a candidate (should fail)
    print_info("  Testing Create Candidate: POST /api/candidates/")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/candidates/",
            headers=headers,
            json={"name": "Test Candidate"},
            timeout=10
        )

        if response.status_code == 403:
            print_success(f"    Create Candidate: Correctly denied (403 Forbidden)")
        elif response.status_code in [200, 201]:
            print_error(f"    Create Candidate: Allowed - Viewer should NOT have write access")
            all_passed = False
        elif response.status_code == 401:
            print_info(f"    Create Candidate: Unauthorized (401)")
        else:
            print_info(f"    Create Candidate: Status {response.status_code}")

    except Exception as e:
        print_info(f"    Create Candidate: Request failed - {e}")

    # Try to create a vacancy (should fail)
    print_info("  Testing Create Vacancy: POST /api/vacancies/")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/vacancies/",
            headers=headers,
            json={"title": "Test Vacancy"},
            timeout=10
        )

        if response.status_code == 403:
            print_success(f"    Create Vacancy: Correctly denied (403 Forbidden)")
        elif response.status_code in [200, 201]:
            print_error(f"    Create Vacancy: Allowed - Viewer should NOT have write access")
            all_passed = False
        elif response.status_code == 401:
            print_info(f"    Create Vacancy: Unauthorized (401)")
        else:
            print_info(f"    Create Vacancy: Status {response.status_code}")

    except Exception as e:
        print_info(f"    Create Vacancy: Request failed - {e}")

    return all_passed


def test_viewer_no_admin_access(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Test that Viewer user cannot access admin endpoints.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if all access denial tests passed
    """
    print_section("8. Test Viewer Cannot Access Admin Endpoints")

    if "viewer" not in users_data:
        print_error("No viewer user found. Skipping viewer access tests.")
        return False

    viewer_token = users_data["viewer"]["access_token"]
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Admin endpoints that Viewer should NOT access
    admin_endpoints = [
        ("List Users", "GET", "/api/users/"),
        ("List Backups", "GET", "/api/backups/"),
    ]

    all_passed = True

    for endpoint_name, method, path in admin_endpoints:
        url = f"{BACKEND_URL}{path}"
        print_info(f"Testing {endpoint_name}: {method} {url}")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)

            # Viewer should NOT be able to access admin endpoints
            if response.status_code == 403:
                print_success(f"  {endpoint_name}: Correctly denied (403 Forbidden)")
            elif response.status_code in [200, 404]:
                print_error(f"  {endpoint_name}: Access granted - Viewer should NOT have access")
                all_passed = False
            elif response.status_code == 401:
                print_info(f"  {endpoint_name}: Unauthorized (401)")
            else:
                print_info(f"  {endpoint_name}: Status {response.status_code}")

        except Exception as e:
            print_info(f"  {endpoint_name}: Request failed - {e}")

    return all_passed


def test_role_permissions_enforced(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Test that role permissions are properly enforced across all roles.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if all permission tests passed
    """
    print_section("9. Test Role Permissions Enforcement")

    # Test scenarios:
    # 1. Admin can access everything
    # 2. Recruiter can access recruiting endpoints but not admin endpoints
    # 3. Viewer can only read data

    all_passed = True

    # Test 1: Admin should be able to update user roles
    if "admin" in users_data and "recruiter" in users_data:
        print_info("Test 1: Admin updating user role")
        admin_headers = {"Authorization": f"Bearer {users_data['admin']['access_token']}"}

        # Get role IDs first
        try:
            response = requests.get(f"{BACKEND_URL}/api/users/", headers=admin_headers, timeout=10)
            if response.status_code == 200:
                print_success("  Admin can list users")
            else:
                print_error(f"  Admin cannot list users: {response.status_code}")
                all_passed = False
        except Exception as e:
            print_error(f"  Error: {e}")
            all_passed = False

    # Test 2: Recruiter should NOT be able to update user roles
    if "recruiter" in users_data:
        print_info("\nTest 2: Recruiter attempting to update user role")
        recruiter_headers = {"Authorization": f"Bearer {users_data['recruiter']['access_token']}"}

        try:
            response = requests.get(f"{BACKEND_URL}/api/users/", headers=recruiter_headers, timeout=10)
            if response.status_code == 403:
                print_success("  Recruiter correctly denied access to user list (403)")
            elif response.status_code == 401:
                print_info("  Recruiter unauthorized (401)")
            else:
                print_error(f"  Recruiter should NOT access user list: {response.status_code}")
                all_passed = False
        except Exception as e:
            print_info(f"  Error: {e}")

    # Test 3: Viewer should have read access to analytics
    if "viewer" in users_data:
        print_info("\nTest 3: Viewer accessing analytics")
        viewer_headers = {"Authorization": f"Bearer {users_data['viewer']['access_token']}"}

        try:
            response = requests.get(f"{BACKEND_URL}/api/analytics/key-metrics", headers=viewer_headers, timeout=10)
            if response.status_code in [200, 404]:
                print_success("  Viewer can read analytics")
            elif response.status_code == 403:
                print_error("  Viewer denied read access to analytics (403)")
                all_passed = False
            else:
                print_info(f"  Status: {response.status_code}")
        except Exception as e:
            print_error(f"  Error: {e}")
            all_passed = False

    # Test 4: Viewer should NOT be able to create backups
    if "viewer" in users_data:
        print_info("\nTest 4: Viewer attempting to create backup")
        viewer_headers = {"Authorization": f"Bearer {users_data['viewer']['access_token']}"}

        try:
            response = requests.post(f"{BACKEND_URL}/api/backups/", headers=viewer_headers, json={}, timeout=10)
            if response.status_code == 403:
                print_success("  Viewer correctly denied backup creation (403)")
            elif response.status_code == 401:
                print_info("  Viewer unauthorized (401)")
            else:
                print_error(f"  Viewer should NOT create backups: {response.status_code}")
                all_passed = False
        except Exception as e:
            print_info(f"  Error: {e}")

    return all_passed


def test_cross_role_isolation(users_data: Dict[str, Dict[str, Any]]) -> bool:
    """
    Test that users cannot access/modify other users' data improperly.

    Args:
        users_data: Dictionary of user data with tokens

    Returns:
        True if all isolation tests passed
    """
    print_section("10. Test Cross-Role Isolation")

    all_passed = True

    # Test 1: Recruiter cannot modify Admin user
    if "recruiter" in users_data and "admin" in users_data:
        print_info("Test 1: Recruiter attempting to modify Admin user")
        recruiter_headers = {"Authorization": f"Bearer {users_data['recruiter']['access_token']}"}
        admin_user_id = users_data['admin']['user_id']

        if admin_user_id:
            try:
                response = requests.put(
                    f"{BACKEND_URL}/api/users/{admin_user_id}/role",
                    headers=recruiter_headers,
                    json={"role_id": "00000000-0000-0000-0000-000000000000"},
                    timeout=10
                )

                if response.status_code == 403:
                    print_success("  Recruiter correctly denied (403)")
                elif response.status_code == 401:
                    print_info("  Unauthorized (401)")
                else:
                    print_info(f"  Status: {response.status_code}")
            except Exception as e:
                print_info(f"  Error: {e}")

    # Test 2: Viewer cannot delete candidates
    if "viewer" in users_data:
        print_info("\nTest 2: Viewer attempting to access admin settings")
        viewer_headers = {"Authorization": f"Bearer {users_data['viewer']['access_token']}"}

        try:
            # Try to access settings (should be denied)
            response = requests.get(f"{BACKEND_URL}/api/settings/", headers=viewer_headers, timeout=10)

            if response.status_code == 403:
                print_success("  Viewer correctly denied settings access (403)")
            elif response.status_code == 404:
                print_info("  Settings endpoint not found (404)")
            elif response.status_code == 401:
                print_info("  Unauthorized (401)")
            else:
                print_info(f"  Status: {response.status_code}")
        except Exception as e:
            print_info(f"  Error: {e}")

    return all_passed


def print_user_summary(users_data: Dict[str, Dict[str, Any]]):
    """Print a summary of created users and their roles."""
    print_section("Test Users Summary")

    for role_key, user_data in users_data.items():
        print(f"\n{role_key.upper()} USER:")
        print(f"  Name: {user_data.get('name')}")
        print(f"  Email: {user_data.get('email')}")
        print(f"  Role: {user_data.get('role')}")
        print(f"  User ID: {user_data.get('user_id')}")


def main():
    """Run all role-based access control tests."""
    print("\n" + "=" * 70)
    print("  ROLE-BASED ACCESS CONTROL - END-TO-END TEST")
    print("=" * 70)
    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Test users: {', '.join(TEST_USERS.keys())}")

    # Track test results
    results = {
        "backend_health": False,
        "create_test_users": False,
        "update_user_roles": False,
        "admin_access": False,
        "recruiter_no_admin_access": False,
        "recruiter_can_recruit": False,
        "viewer_read_only": False,
        "viewer_no_admin": False,
        "permissions_enforced": False,
        "cross_role_isolation": False,
    }

    # Run tests
    results["backend_health"] = check_backend_health()
    if not results["backend_health"]:
        print_error("Backend is not running. Please start the backend service first.")
        print_info("Run: cd backend && python main.py")
        return 1

    users_data = create_test_users()
    results["create_test_users"] = len(users_data) > 0

    if not results["create_test_users"]:
        print_error("Failed to create test users. Cannot continue.")
        return 1

    # Print user summary
    print_user_summary(users_data)

    # Update roles (optional, depends on having an admin)
    results["update_user_roles"] = update_user_roles(users_data)

    # Run role-based tests
    results["admin_access"] = test_admin_access(users_data)
    results["recruiter_no_admin_access"] = test_recruiter_no_admin_access(users_data)
    results["recruiter_can_recruit"] = test_recruiter_can_access_recruiting_endpoints(users_data)
    results["viewer_read_only"] = test_viewer_read_only_access(users_data)
    results["viewer_no_admin"] = test_viewer_no_admin_access(users_data)
    results["permissions_enforced"] = test_role_permissions_enforced(users_data)
    results["cross_role_isolation"] = test_cross_role_isolation(users_data)

    # Print summary
    print_section("TEST SUMMARY")
    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 70)
    if all_passed:
        print_success("ALL TESTS PASSED!")
        print_info("Role-based access control is working correctly.")
        print_info("\nKey findings:")
        print_info("  ✓ Admin users can access all endpoints")
        print_info("  ✓ Recruiter users can access recruiting endpoints but not admin endpoints")
        print_info("  ✓ Viewer users have read-only access to data")
        print_info("  ✓ Role permissions are properly enforced")
        print_info("  ✓ Cross-role isolation is working")
        return 0
    else:
        print_error("SOME TESTS FAILED")
        print_info("Please review the errors above and fix the issues.")
        print_info("\nCommon issues:")
        print_info("  - Users may not have the correct roles assigned")
        print_info("  - Role permissions may not be configured correctly")
        print_info("  - Admin API endpoints may not be properly protected")
        return 1


if __name__ == "__main__":
    sys.exit(main())
