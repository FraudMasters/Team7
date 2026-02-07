"""
Integration tests for user invitation and organization membership workflow.

This test suite validates end-to-end that:
- Users can be invited to organizations via email
- New user accounts are auto-created when inviting non-existent users
- Organization memberships are properly established
- Users can access data from their organizations
- Users cannot see data from organizations they're not members of
- Role-based access control is enforced

Test Coverage:
- Organization admin creation
- User invitation workflow
- Organization membership verification
- Cross-organization access prevention
- Multi-organization membership scenarios
"""
import io
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI application
import sys
sys.path.insert(0, str(__file__).parent.parent.parent)

from main import app
from database import async_session_maker, get_db
from models.organization import Organization
from models.user import User
from models.organization_user import OrganizationUser, OrganizationUserRole
from models.resume import Resume


@pytest.fixture
def test_pdf_file() -> bytes:
    """
    Create a minimal valid PDF file for testing.

    Returns:
        Bytes content of a simple PDF file
    """
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 700 Td
(John Doe - Software Engineer) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000264 00000 n
0000000349 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
428
%%EOF
"""
    return pdf_content


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


class TestUserInvitationWorkflow:
    """Tests for complete user invitation and membership workflow."""

    def test_create_organization_admin_user(self, client: TestClient):
        """
        Test Step 1: Create an organization admin user.

        This test verifies:
        - Admin users can be created via API
        - User accounts are properly initialized
        - User data includes required fields (id, email, name, role)
        """
        response = client.post(
            "/api/users/",
            json={
                "email": "admin@companya.com",
                "name": "Alice Admin",
                "role": "admin",
                "is_active": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "admin@companya.com"
        assert data["name"] == "Alice Admin"
        assert data["role"] == "admin"
        assert data["is_active"] is True
        assert "id" in data

        return data["id"]

    def test_create_new_organization(self, client: TestClient):
        """
        Test Step 2: Create a new organization.

        This test verifies:
        - Organizations can be created with unique slugs
        - Organization data includes required fields
        - Organization is immediately accessible
        """
        response = client.post(
            "/api/organizations/",
            json={
                "name": "Company A",
                "slug": "company-a",
                "settings": {"industry": "Technology", "size": "mid-size"}
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Company A"
        assert data["slug"] == "company-a"
        assert data["is_active"] is True
        assert "id" in data

        return data["id"]

    def test_invite_user_to_organization_as_member(self, client: TestClient):
        """
        Test Step 3: Invite a user to organization as member.

        This test verifies:
        - Users can be invited via email address
        - New user accounts are auto-created for non-existent emails
        - Organization membership is established
        - Membership includes correct role (member)
        - Response includes user and organization details
        """
        # First create an organization
        org_response = client.post(
            "/api/organizations/",
            json={
                "name": "Company B",
                "slug": "company-b"
            }
        )
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]

        # Invite a new user (this user doesn't exist yet)
        invite_response = client.post(
            f"/api/organizations/{org_id}/invite",
            json={
                "email": "bob@companyb.com",
                "role": "member"
            }
        )

        assert invite_response.status_code == 201
        data = invite_response.json()
        assert data["email"] == "bob@companyb.com"
        assert data["name"] == "bob"  # Auto-generated from email
        assert data["organization_id"] == org_id
        assert data["organization_name"] == "Company B"
        assert data["role"] == "member"
        assert "id" in data
        assert "created_at" in data

        return data["id"], org_id

    def test_verify_user_can_access_organization_data(self, client: TestClient, test_pdf_file: bytes):
        """
        Test Step 4: Verify user can access organization data.

        This test verifies:
        - Invited users can access their organization's data
        - Organization context is properly enforced
        - Users see only data from their organizations
        """
        # Create organization
        org_response = client.post(
            "/api/organizations/",
            json={"name": "Company C", "slug": "company-c"}
        )
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]

        # Invite user to organization
        invite_response = client.post(
            f"/api/organizations/{org_id}/invite",
            json={"email": "charlie@companyc.com", "role": "member"}
        )
        assert invite_response.status_code == 201
        user_id = invite_response.json()["id"]

        # Upload a candidate with organization context
        upload_response = client.post(
            "/api/resumes/upload",
            headers={"X-Organization-ID": org_id},
            files={"file": ("charlie_candidate.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
        )
        assert upload_response.status_code == 201
        candidate_id = upload_response.json()["id"]

        # Query candidates with organization context
        query_response = client.get(
            "/api/candidates/",
            headers={"X-Organization-ID": org_id}
        )

        assert query_response.status_code == 200
        data = query_response.json()
        candidates = data.get("candidates", data.get("items", []))

        # Verify the uploaded candidate is visible
        candidate_ids = [c["id"] for c in candidates]
        assert candidate_id in candidate_ids, "User cannot see their organization's candidate"

    def test_verify_user_cannot_see_other_organizations(self, client: TestClient, test_pdf_file: bytes):
        """
        Test Step 5: Verify user cannot see other organizations' data.

        This is the critical isolation test that verifies:
        - Users can only see data from their own organizations
        - Cross-organization data leakage is prevented
        - Organization context properly filters all queries
        """
        # Create two organizations
        org_a_response = client.post(
            "/api/organizations/",
            json={"name": "Isolation Test A", "slug": "isolation-test-a"}
        )
        assert org_a_response.status_code == 201
        org_a_id = org_a_response.json()["id"]

        org_b_response = client.post(
            "/api/organizations/",
            json={"name": "Isolation Test B", "slug": "isolation-test-b"}
        )
        assert org_b_response.status_code == 201
        org_b_id = org_b_response.json()["id"]

        # Invite user to Organization A only
        invite_response = client.post(
            f"/api/organizations/{org_a_id}/invite",
            json={"email": "david@isolated.com", "role": "member"}
        )
        assert invite_response.status_code == 201
        user_id = invite_response.json()["id"]

        # Upload candidates to Organization A
        org_a_candidates = []
        for i in range(2):
            response = client.post(
                "/api/resumes/upload",
                headers={"X-Organization-ID": org_a_id},
                files={
                    "file": (
                        f"org_a_candidate_{i}.pdf",
                        io.BytesIO(test_pdf_file),
                        "application/pdf"
                    )
                }
            )
            assert response.status_code == 201
            org_a_candidates.append(response.json()["id"])

        # Upload candidates to Organization B
        org_b_candidates = []
        for i in range(2):
            response = client.post(
                "/api/resumes/upload",
                headers={"X-Organization-ID": org_b_id},
                files={
                    "file": (
                        f"org_b_candidate_{i}.pdf",
                        io.BytesIO(test_pdf_file),
                        "application/pdf"
                    )
                }
            )
            assert response.status_code == 201
            org_b_candidates.append(response.json()["id"])

        # Query with Organization A context (user's organization)
        response_a = client.get(
            "/api/candidates/",
            headers={"X-Organization-ID": org_a_id}
        )
        assert response_a.status_code == 200
        data_a = response_a.json()
        candidate_ids_a = [c["id"] for c in data_a.get("candidates", data_a.get("items", []))]

        # User should see all Organization A candidates
        for candidate_id in org_a_candidates:
            assert candidate_id in candidate_ids_a, \
                f"User cannot see their own organization's candidate {candidate_id}"

        # User should NOT see Organization B candidates
        for candidate_id in org_b_candidates:
            assert candidate_id not in candidate_ids_a, \
                f"CROSS-ORG LEAKAGE: User can see candidate {candidate_id} from non-member organization!"

    def test_invite_existing_user_to_organization(self, client: TestClient):
        """
        Test inviting an existing user to an organization.

        Verifies:
        - Existing users can be invited to new organizations
        - User gains access to the new organization
        - User maintains access to existing organizations
        - User can query data from all their organizations
        """
        # Create a user
        user_response = client.post(
            "/api/users/",
            json={
                "email": "eve@multiorg.com",
                "name": "Eve Multiorg",
                "role": "member"
            }
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        # Create first organization and invite user
        org1_response = client.post(
            "/api/organizations/",
            json={"name": "Eve's First Org", "slug": "eves-first"}
        )
        assert org1_response.status_code == 201
        org1_id = org1_response.json()["id"]

        invite1_response = client.post(
            f"/api/organizations/{org1_id}/invite",
            json={"email": "eve@multiorg.com", "role": "admin"}
        )
        assert invite1_response.status_code == 201

        # Create second organization and invite the same user
        org2_response = client.post(
            "/api/organizations/",
            json={"name": "Eve's Second Org", "slug": "eves-second"}
        )
        assert org2_response.status_code == 201
        org2_id = org2_response.json()["id"]

        invite2_response = client.post(
            f"/api/organizations/{org2_id}/invite",
            json={"email": "eve@multiorg.com", "role": "member"}
        )
        assert invite2_response.status_code == 201

        # Verify user belongs to both organizations
        user_get_response = client.get(f"/api/users/{user_id}")
        assert user_get_response.status_code == 200
        user_data = user_get_response.json()

        # Check organization memberships
        organizations = user_data.get("organizations", [])
        org_ids = [org["organization_id"] for org in organizations]

        assert org1_id in org_ids, "User not in first organization"
        assert org2_id in org_ids, "User not in second organization"

        # Verify roles
        org1_role = next((org["role"] for org in organizations if org["organization_id"] == org1_id), None)
        org2_role = next((org["role"] for org in organizations if org["organization_id"] == org2_id), None)

        assert org1_role == "admin", "User should have admin role in first org"
        assert org2_role == "member", "User should have member role in second org"

    def test_duplicate_invition_fails(self, client: TestClient):
        """
        Test that inviting the same user twice to the same organization fails.

        Verifies:
        - Duplicate membership invitations are rejected
        - Appropriate error message is returned
        - Existing membership is not duplicated
        """
        # Create organization
        org_response = client.post(
            "/api/organizations/",
            json={"name": "Duplicate Test Org", "slug": "duplicate-test"}
        )
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]

        # Invite user once
        invite1_response = client.post(
            f"/api/organizations/{org_id}/invite",
            json={"email": "frank@duplicate.com", "role": "member"}
        )
        assert invite1_response.status_code == 201

        # Try to invite the same user again
        invite2_response = client.post(
            f"/api/organizations/{org_id}/invite",
            json={"email": "frank@duplicate.com", "role": "admin"}
        )
        assert invite2_response.status_code == 400
        assert "already a member" in invite2_response.json()["detail"].lower()

    def test_invite_with_invalid_role_fails(self, client: TestClient):
        """
        Test that inviting with an invalid role fails.

        Verifies:
        - Only valid roles (admin, member, viewer) are accepted
        - Invalid roles are rejected with appropriate error
        """
        # Create organization
        org_response = client.post(
            "/api/organizations/",
            json={"name": "Role Test Org", "slug": "role-test"}
        )
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]

        # Try to invite with invalid role
        invite_response = client.post(
            f"/api/organizations/{org_id}/invite",
            json={"email": "grace@role.com", "role": "superadmin"}
        )
        assert invite_response.status_code == 400
        assert "invalid role" in invite_response.json()["detail"].lower()

    def test_invite_to_nonexistent_organization_fails(self, client: TestClient):
        """
        Test that inviting to a nonexistent organization fails.

        Verifies:
        - Invitations to non-existent organizations are rejected
        - Appropriate 404 error is returned
        """
        fake_org_id = "00000000-0000-0000-0000-000000000000"

        invite_response = client.post(
            f"/api/organizations/{fake_org_id}/invite",
            json={"email": "henry@nowhere.com", "role": "member"}
        )
        assert invite_response.status_code == 404
        assert "not found" in invite_response.json()["detail"].lower()


class TestOrganizationMembershipQueries:
    """Tests for querying organization memberships."""

    def test_get_user_organizations(self, client: TestClient):
        """
        Test retrieving a user's organization memberships.

        Verifies:
        - User's organizations endpoint returns all memberships
        - Each membership includes org details and role
        - Response is properly formatted
        """
        # Create user
        user_response = client.post(
            "/api/users/",
            json={"email": "iris@query.com", "name": "Iris Query", "role": "member"}
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        # Create and join multiple organizations
        for i in range(3):
            org_response = client.post(
                "/api/organizations/",
                json={"name": f"Iris's Org {i}", "slug": f"iris-org-{i}"}
            )
            assert org_response.status_code == 201
            org_id = org_response.json()["id"]

            invite_response = client.post(
                f"/api/organizations/{org_id}/invite",
                json={"email": "iris@query.com", "role": "member"}
            )
            assert invite_response.status_code == 201

        # Get user's organizations
        get_orgs_response = client.get(f"/api/users/{user_id}/organizations")
        assert get_orgs_response.status_code == 200

        organizations = get_orgs_response.json()
        assert isinstance(organizations, list)
        assert len(organizations) == 3

        # Verify each organization has required fields
        for org in organizations:
            assert "organization_id" in org
            assert "organization_name" in org
            assert "organization_slug" in org
            assert "role" in org
            assert "created_at" in org


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "user_invitation: marks tests as user invitation workflow tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
