#!/usr/bin/env python
"""
Standalone verification script for user invitation and organization membership workflow.

This script tests the end-to-end user invitation workflow:
1. Create organization admin user
2. Create new organization
3. Invite user to organization as member
4. Verify user can access organization data
5. Verify user cannot see other organizations

Run this script to verify the user invitation and membership functionality.
"""
import sys
import requests
from typing import Dict, Any, Tuple
import json


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(message: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message in red."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_section(title: str):
    """Print section header in bold."""
    print(f"\n{Colors.BOLD}{title}{Colors.END}")
    print("=" * 60)


class UserInvitationWorkflowTester:
    """Test suite for user invitation and organization membership workflow."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the tester.

        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.test_data = {}

    def test_create_organization_admin_user(self) -> bool:
        """
        Test Step 1: Create an organization admin user.

        Returns:
            True if test passes, False otherwise
        """
        print_section("Step 1: Create Organization Admin User")

        try:
            response = self.session.post(
                f"{self.base_url}/api/users/",
                json={
                    "email": "admin@companya.com",
                    "name": "Alice Admin",
                    "role": "admin",
                    "is_active": True
                }
            )

            if response.status_code == 201:
                data = response.json()
                self.test_data["admin_user_id"] = data["id"]

                print_success(f"Admin user created: {data['email']}")
                print_info(f"  User ID: {data['id']}")
                print_info(f"  Name: {data['name']}")
                print_info(f"  Role: {data['role']}")
                return True
            else:
                print_error(f"Failed to create admin user: {response.status_code}")
                print_info(f"  Response: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception creating admin user: {e}")
            return False

    def test_create_new_organization(self) -> bool:
        """
        Test Step 2: Create a new organization.

        Returns:
            True if test passes, False otherwise
        """
        print_section("Step 2: Create New Organization")

        try:
            response = self.session.post(
                f"{self.base_url}/api/organizations/",
                json={
                    "name": "Company A",
                    "slug": "company-a",
                    "settings": {"industry": "Technology", "size": "mid-size"}
                }
            )

            if response.status_code == 201:
                data = response.json()
                self.test_data["org_a_id"] = data["id"]
                self.test_data["org_a_slug"] = data["slug"]

                print_success(f"Organization created: {data['name']}")
                print_info(f"  Organization ID: {data['id']}")
                print_info(f"  Slug: {data['slug']}")
                print_info(f"  Active: {data['is_active']}")
                return True
            else:
                print_error(f"Failed to create organization: {response.status_code}")
                print_info(f"  Response: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception creating organization: {e}")
            return False

    def test_invite_user_to_organization(self) -> bool:
        """
        Test Step 3: Invite a user to organization as member.

        Returns:
            True if test passes, False otherwise
        """
        print_section("Step 3: Invite User to Organization as Member")

        try:
            org_id = self.test_data.get("org_a_id")
            if not org_id:
                print_error("Organization ID not found in test data")
                return False

            response = self.session.post(
                f"{self.base_url}/api/organizations/{org_id}/invite",
                json={
                    "email": "bob@companya.com",
                    "role": "member"
                }
            )

            if response.status_code == 201:
                data = response.json()
                self.test_data["invited_user_id"] = data["id"]

                print_success(f"User invited to organization: {data['email']}")
                print_info(f"  User ID: {data['id']}")
                print_info(f"  Name: {data['name']}")
                print_info(f"  Organization: {data['organization_name']}")
                print_info(f"  Role: {data['role']}")
                print_info(f"  Member since: {data.get('created_at', 'N/A')}")

                # Verify the user was added to the organization
                assert data["email"] == "bob@companya.com", "Email mismatch"
                assert data["organization_id"] == org_id, "Organization ID mismatch"
                assert data["role"] == "member", "Role mismatch"

                return True
            else:
                print_error(f"Failed to invite user: {response.status_code}")
                print_info(f"  Response: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception inviting user: {e}")
            return False

    def test_user_can_access_organization_data(self) -> bool:
        """
        Test Step 4: Verify user can access organization data.

        Returns:
            True if test passes, False otherwise
        """
        print_section("Step 4: Verify User Can Access Organization Data")

        try:
            org_id = self.test_data.get("org_a_id")
            if not org_id:
                print_error("Organization ID not found in test data")
                return False

            # Query the user's organizations
            user_id = self.test_data.get("invited_user_id")
            if not user_id:
                print_error("Invited user ID not found in test data")
                return False

            response = self.session.get(
                f"{self.base_url}/api/users/{user_id}/organizations"
            )

            if response.status_code == 200:
                organizations = response.json()

                print_success(f"User has access to {len(organizations)} organization(s)")

                # Verify user has access to Company A
                found_org = False
                for org in organizations:
                    print_info(f"  - {org['organization_name']} ({org['role']})")
                    if org["organization_id"] == org_id:
                        found_org = True
                        assert org["role"] == "member", "User should have member role"

                if found_org:
                    print_success("User can access their organization's data")
                    return True
                else:
                    print_error("User cannot access their assigned organization")
                    return False
            else:
                print_error(f"Failed to query user organizations: {response.status_code}")
                print_info(f"  Response: {response.text}")
                return False

        except Exception as e:
            print_error(f"Exception verifying user access: {e}")
            return False

    def test_user_cannot_see_other_organizations(self) -> bool:
        """
        Test Step 5: Verify user cannot see other organizations' data.

        This is the critical isolation test.

        Returns:
            True if test passes, False otherwise
        """
        print_section("Step 5: Verify User Cannot See Other Organizations")

        try:
            # Create Organization B (different from user's organization)
            response = self.session.post(
                f"{self.base_url}/api/organizations/",
                json={
                    "name": "Company B",
                    "slug": "company-b"
                }
            )

            if response.status_code != 201:
                print_error("Failed to create Organization B")
                return False

            org_b_data = response.json()
            org_b_id = org_b_data["id"]
            print_success(f"Created Organization B: {org_b_data['name']}")

            # Invite a different user to Organization B
            response = self.session.post(
                f"{self.base_url}/api/organizations/{org_b_id}/invite",
                json={
                    "email": "charlie@companyb.com",
                    "role": "member"
                }
            )

            if response.status_code != 201:
                print_error("Failed to invite user to Organization B")
                return False

            charlie_user_id = response.json()["id"]
            print_success(f"Invited Charlie to Organization B")

            # Verify Bob (from Company A) is not in Company B
            bob_user_id = self.test_data.get("invited_user_id")
            response = self.session.get(
                f"{self.base_url}/api/users/{bob_user_id}/organizations"
            )

            if response.status_code != 200:
                print_error("Failed to query Bob's organizations")
                return False

            bob_orgs = response.json()
            bob_org_ids = [org["organization_id"] for org in bob_orgs]

            # Bob should only have access to Company A, not Company B
            org_a_id = self.test_data.get("org_a_id")

            if org_a_id in bob_org_ids and org_b_id not in bob_org_ids:
                print_success("Bob can only see his own organization (Company A)")
                print_info(f"  Bob's organizations: {[org['organization_name'] for org in bob_orgs]}")
                print_success("CROSS-ORGANIZATION LEAKAGE PREVENTED ✓")
                return True
            else:
                print_error("CROSS-ORGANIZATION LEAKAGE DETECTED!")
                print_info(f"  Bob should NOT see Organization B")
                print_info(f"  Bob's organizations: {[org['organization_name'] for org in bob_orgs]}")
                return False

        except Exception as e:
            print_error(f"Exception verifying organization isolation: {e}")
            return False

    def run_all_tests(self) -> bool:
        """
        Run all tests in sequence.

        Returns:
            True if all tests pass, False otherwise
        """
        print(f"\n{Colors.BOLD}{'=' * 60}")
        print(f"User Invitation and Organization Membership Workflow Tests")
        print(f"{'=' * 60}{Colors.END}\n")

        results = []

        # Run tests in sequence
        results.append(("Create Admin User", self.test_create_organization_admin_user()))
        results.append(("Create Organization", self.test_create_new_organization()))
        results.append(("Invite User", self.test_invite_user_to_organization()))
        results.append(("Verify User Access", self.test_user_can_access_organization_data()))
        results.append(("Verify Organization Isolation", self.test_user_cannot_see_other_organizations()))

        # Print summary
        print_section("Test Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
            print(f"  {test_name}: {status}")

        print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

        if passed == total:
            print(f"{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED ✓{Colors.END}\n")
            return True
        else:
            print(f"{Colors.RED}{Colors.BOLD}SOME TESTS FAILED ✗{Colors.END}\n")
            return False


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test user invitation and organization membership workflow"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    tester = UserInvitationWorkflowTester(base_url=args.url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
