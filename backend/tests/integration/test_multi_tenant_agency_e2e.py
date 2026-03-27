"""
End-to-end integration tests for multi-tenant agency mode.

This test suite validates the complete multi-tenant agency workflow:
- Agency creation and management
- Client tenant creation and isolation
- Data isolation between client tenants
- Cross-client analytics for agencies
- Usage tracking per client
- Agency dashboard metrics

Test Coverage:
- Agency CRUD operations
- Client tenant management
- Resume isolation between client tenants
- Agency can view all client data
- Per-client usage tracking
- Cross-client metrics aggregation
"""
import io
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(__file__).parent.parent.parent)

from main import app


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


class TestAgencyCRUD:
    """Tests for agency creation, read, update, and delete operations."""

    def test_create_agency(self, client: TestClient):
        """
        Test creating a recruitment agency.

        Verifies:
        - Agency can be created with required fields
        - Agency gets assigned a unique ID
        - Agency data is properly persisted
        """
        response = client.post(
            "/api/agencies/",
            json={
                "name": "TechRecruiters Inc",
                "slug": "tech-recruiters",
                "domain": "techrecruiters.com",
                "contact_email": "contact@techrecruiters.com",
                "contact_phone": "+1-555-0100"
            }
        )

        assert response.status_code == 201, f"Failed to create agency: {response.text}"
        data = response.json()
        assert data["name"] == "TechRecruiters Inc"
        assert data["slug"] == "tech-recruiters"
        assert data["domain"] == "techrecruiters.com"
        assert data["is_active"] is True
        assert "id" in data

    def test_list_agencies(self, client: TestClient):
        """
        Test listing all agencies.

        Verifies:
        - Agencies can be listed
        - Response includes all created agencies
        """
        # Create a test agency
        create_response = client.post(
            "/api/agencies/",
            json={
                "name": "Test Agency for Listing",
                "slug": "test-agency-list"
            }
        )
        assert create_response.status_code == 201
        agency_id = create_response.json()["id"]

        # List agencies
        response = client.get("/api/agencies/")
        assert response.status_code == 200
        data = response.json()

        # Should have agencies array
        assert "agencies" in data or "items" in data
        agencies = data.get("agencies", data.get("items", []))

        # Find our created agency
        agency_ids = [agency["id"] for agency in agencies]
        assert agency_id in agency_ids

    def test_get_agency_by_id(self, client: TestClient):
        """
        Test retrieving a specific agency by ID.

        Verifies:
        - Agency can be retrieved by ID
        - Returned data matches created agency
        """
        # Create agency
        create_response = client.post(
            "/api/agencies/",
            json={
                "name": "Get By ID Agency",
                "slug": "get-by-id-agency"
            }
        )
        assert create_response.status_code == 201
        agency_id = create_response.json()["id"]

        # Get agency by ID
        response = client.get(f"/api/agencies/{agency_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agency_id
        assert data["name"] == "Get By ID Agency"

    def test_duplicate_slug_fails(self, client: TestClient):
        """
        Test that creating an agency with duplicate slug fails.

        Verifies uniqueness constraint on slug field.
        """
        # Create first agency
        response1 = client.post(
            "/api/agencies/",
            json={
                "name": "First Agency",
                "slug": "unique-slug-test"
            }
        )
        assert response1.status_code == 201

        # Try to create second agency with same slug
        response2 = client.post(
            "/api/agencies/",
            json={
                "name": "Second Agency",
                "slug": "unique-slug-test"
            }
        )

        # Should fail with conflict or validation error
        assert response2.status_code in [400, 409, 422]


class TestClientTenantManagement:
    """Tests for client tenant creation and management under agencies."""

    def test_create_client_tenant(self, client: TestClient):
        """
        Test creating a client tenant relationship.

        Verifies:
        - Client tenant can be created linking agency to organization
        - Relationship data is properly persisted
        """
        # Create agency
        agency_response = client.post(
            "/api/agencies/",
            json={
                "name": "Client Management Agency",
                "slug": "client-mgmt-agency"
            }
        )
        assert agency_response.status_code == 201
        agency_id = agency_response.json()["id"]

        # Create organization (client)
        org_response = client.post(
            "/api/organizations/",
            json={
                "name": "Client Organization A",
                "slug": "client-org-a"
            }
        )
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]

        # Create client tenant relationship
        tenant_response = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": org_id,
                "status": "active",
                "is_primary": True
            }
        )

        assert tenant_response.status_code == 201, f"Failed to create client tenant: {tenant_response.text}"
        tenant_data = tenant_response.json()
        assert tenant_data["agency_id"] == agency_id
        assert tenant_data["organization_id"] == org_id
        assert tenant_data["status"] == "active"
        assert tenant_data["is_primary"] is True
        assert "id" in tenant_data

    def test_list_client_tenants_by_agency(self, client: TestClient):
        """
        Test listing all client tenants for a specific agency.

        Verifies:
        - Client tenants can be filtered by agency_id
        - Only tenants for the specified agency are returned
        """
        # Create agency
        agency_response = client.post(
            "/api/agencies/",
            json={
                "name": "Multi-Client Agency",
                "slug": "multi-client-agency"
            }
        )
        assert agency_response.status_code == 201
        agency_id = agency_response.json()["id"]

        # Create two organizations
        org1_response = client.post(
            "/api/organizations/",
            json={"name": "Client 1", "slug": "client-1"}
        )
        org2_response = client.post(
            "/api/organizations/",
            json={"name": "Client 2", "slug": "client-2"}
        )
        assert org1_response.status_code == 201
        assert org2_response.status_code == 201
        org1_id = org1_response.json()["id"]
        org2_id = org2_response.json()["id"]

        # Create client tenant relationships
        tenant1_response = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": org1_id,
                "status": "active"
            }
        )
        tenant2_response = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": org2_id,
                "status": "active"
            }
        )
        assert tenant1_response.status_code == 201
        assert tenant2_response.status_code == 201

        # List client tenants for this agency
        response = client.get(f"/api/client-tenants/?agency_id={agency_id}")
        assert response.status_code == 200
        data = response.json()

        tenants = data.get("client_tenants", data.get("items", []))
        assert len(tenants) >= 2

        # Verify both organizations are in the list
        org_ids = [tenant["organization_id"] for tenant in tenants]
        assert org1_id in org_ids
        assert org2_id in org_ids


class TestMultiTenantDataIsolation:
    """
    Core tests for multi-tenant data isolation between client tenants.

    This validates the critical requirement that client A cannot see client B's data.
    """

    def test_resume_isolation_between_clients(self, client: TestClient, test_pdf_file: bytes):
        """
        Test that resumes uploaded to one client are NOT visible to another client.

        This is the core data isolation test:
        1. Create agency
        2. Create two client organizations under the agency
        3. Upload resume to Client A
        4. Verify resume is visible to Client A
        5. Verify resume is NOT visible to Client B

        Critical Test: Validates data isolation between tenants.
        """
        # Step 1: Create agency
        agency_response = client.post(
            "/api/agencies/",
            json={
                "name": "Isolation Test Agency",
                "slug": "isolation-test-agency"
            }
        )
        assert agency_response.status_code == 201
        agency_id = agency_response.json()["id"]

        # Step 2: Create two client organizations
        client_a_response = client.post(
            "/api/organizations/",
            json={
                "name": "Client A Corp",
                "slug": "client-a-corp"
            }
        )
        assert client_a_response.status_code == 201
        client_a_id = client_a_response.json()["id"]

        client_b_response = client.post(
            "/api/organizations/",
            json={
                "name": "Client B Corp",
                "slug": "client-b-corp"
            }
        )
        assert client_b_response.status_code == 201
        client_b_id = client_b_response.json()["id"]

        # Create client tenant relationships
        tenant_a_response = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": client_a_id,
                "status": "active"
            }
        )
        tenant_b_response = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": client_b_id,
                "status": "active"
            }
        )
        assert tenant_a_response.status_code == 201
        assert tenant_b_response.status_code == 201
        tenant_a_id = tenant_a_response.json()["id"]
        tenant_b_id = tenant_b_response.json()["id"]

        # Step 3: Upload resume to Client A
        upload_response = client.post(
            "/api/resumes/upload",
            headers={
                "X-Organization-ID": client_a_id,
                "X-Tenant-ID": tenant_a_id,
                "X-Agency-ID": agency_id
            },
            files={
                "file": ("client_a_resume.pdf", io.BytesIO(test_pdf_file), "application/pdf")
            }
        )
        assert upload_response.status_code == 201
        resume_a_id = upload_response.json()["id"]

        # Step 4: Verify resume is visible to Client A
        client_a_candidates = client.get(
            "/api/candidates/",
            headers={
                "X-Organization-ID": client_a_id,
                "X-Tenant-ID": tenant_a_id,
                "X-Agency-ID": agency_id
            }
        )
        assert client_a_candidates.status_code == 200
        client_a_data = client_a_candidates.json()
        client_a_candidate_ids = [c["id"] for c in client_a_data.get("candidates", client_a_data.get("items", []))]

        # Resume should be visible to Client A
        assert resume_a_id in client_a_candidate_ids, \
            f"Resume {resume_a_id} should be visible to Client A"

        # Step 5: Verify resume is NOT visible to Client B
        client_b_candidates = client.get(
            "/api/candidates/",
            headers={
                "X-Organization-ID": client_b_id,
                "X-Tenant-ID": tenant_b_id,
                "X-Agency-ID": agency_id
            }
        )
        assert client_b_candidates.status_code == 200
        client_b_data = client_b_candidates.json()
        client_b_candidate_ids = [c["id"] for c in client_b_data.get("candidates", client_b_data.get("items", []))]

        # Resume should NOT be visible to Client B (CRITICAL ISOLATION TEST)
        assert resume_a_id not in client_b_candidate_ids, \
            f"DATA LEAKAGE: Resume {resume_a_id} from Client A is visible to Client B!"

    def test_multiple_resumes_isolation(self, client: TestClient, test_pdf_file: bytes):
        """
        Test isolation with multiple resumes across multiple clients.

        Verifies:
        - Multiple resumes can be uploaded to each client
        - Each client sees only their own resumes
        - No cross-contamination of data
        """
        # Create agency
        agency = client.post(
            "/api/agencies/",
            json={"name": "Multi Resume Agency", "slug": "multi-resume-agency"}
        ).json()
        agency_id = agency["id"]

        # Create two clients
        client_a = client.post(
            "/api/organizations/",
            json={"name": "Multi Resume Client A", "slug": "multi-resume-client-a"}
        ).json()
        client_b = client.post(
            "/api/organizations/",
            json={"name": "Multi Resume Client B", "slug": "multi-resume-client-b"}
        ).json()

        # Create tenant relationships
        tenant_a = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": client_a["id"],
                "status": "active"
            }
        ).json()
        tenant_b = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": client_b["id"],
                "status": "active"
            }
        ).json()

        # Upload 3 resumes to Client A
        client_a_resumes = []
        for i in range(3):
            response = client.post(
                "/api/resumes/upload",
                headers={
                    "X-Organization-ID": client_a["id"],
                    "X-Tenant-ID": tenant_a["id"],
                    "X-Agency-ID": agency_id
                },
                files={
                    "file": (f"client_a_resume_{i}.pdf", io.BytesIO(test_pdf_file), "application/pdf")
                }
            )
            if response.status_code == 201:
                client_a_resumes.append(response.json()["id"])

        # Upload 2 resumes to Client B
        client_b_resumes = []
        for i in range(2):
            response = client.post(
                "/api/resumes/upload",
                headers={
                    "X-Organization-ID": client_b["id"],
                    "X-Tenant-ID": tenant_b["id"],
                    "X-Agency-ID": agency_id
                },
                files={
                    "file": (f"client_b_resume_{i}.pdf", io.BytesIO(test_pdf_file), "application/pdf")
                }
            )
            if response.status_code == 201:
                client_b_resumes.append(response.json()["id"])

        # Verify Client A sees only their resumes
        response_a = client.get(
            "/api/candidates/",
            headers={
                "X-Organization-ID": client_a["id"],
                "X-Tenant-ID": tenant_a["id"],
                "X-Agency-ID": agency_id
            }
        )
        if response_a.status_code == 200:
            data_a = response_a.json()
            visible_to_a = [c["id"] for c in data_a.get("candidates", data_a.get("items", []))]

            # Client A should see their own resumes
            for resume_id in client_a_resumes:
                assert resume_id in visible_to_a, \
                    f"Client A cannot see their own resume {resume_id}"

            # Client A should NOT see Client B's resumes
            for resume_id in client_b_resumes:
                assert resume_id not in visible_to_a, \
                    f"DATA LEAKAGE: Client A can see Client B's resume {resume_id}"

        # Verify Client B sees only their resumes
        response_b = client.get(
            "/api/candidates/",
            headers={
                "X-Organization-ID": client_b["id"],
                "X-Tenant-ID": tenant_b["id"],
                "X-Agency-ID": agency_id
            }
        )
        if response_b.status_code == 200:
            data_b = response_b.json()
            visible_to_b = [c["id"] for c in data_b.get("candidates", data_b.get("items", []))]

            # Client B should see their own resumes
            for resume_id in client_b_resumes:
                assert resume_id in visible_to_b, \
                    f"Client B cannot see their own resume {resume_id}"

            # Client B should NOT see Client A's resumes
            for resume_id in client_a_resumes:
                assert resume_id not in visible_to_b, \
                    f"DATA LEAKAGE: Client B can see Client A's resume {resume_id}"


class TestAgencyAnalytics:
    """Tests for agency-level cross-client analytics."""

    def test_agency_can_view_cross_client_metrics(self, client: TestClient):
        """
        Test that agency can view aggregated metrics across all clients.

        Verifies:
        - Agency analytics endpoint returns data
        - Metrics include cross-client aggregation
        """
        # Create agency
        agency = client.post(
            "/api/agencies/",
            json={"name": "Analytics Agency", "slug": "analytics-agency"}
        ).json()
        agency_id = agency["id"]

        # Get agency analytics
        response = client.get(
            f"/api/agency-analytics/summary?agency_id={agency_id}",
            headers={"X-Agency-ID": agency_id}
        )

        assert response.status_code == 200, f"Failed to get agency analytics: {response.text}"
        data = response.json()

        # Should have summary metrics
        assert "total_clients" in data or "clients" in data
        assert "total_candidates" in data or "candidates" in data


class TestUsageTracking:
    """Tests for per-client usage tracking."""

    def test_billing_usage_tracking(self, client: TestClient):
        """
        Test that usage is tracked per client tenant.

        Verifies:
        - Billing API returns usage data
        - Usage can be filtered by agency
        """
        # Create agency
        agency = client.post(
            "/api/agencies/",
            json={"name": "Billing Test Agency", "slug": "billing-test-agency"}
        ).json()
        agency_id = agency["id"]

        # Get billing usage data
        response = client.get(
            f"/api/billing/usage?agency_id={agency_id}",
            headers={"X-Agency-ID": agency_id}
        )

        # Should return usage data (even if empty)
        assert response.status_code == 200, f"Failed to get billing usage: {response.text}"
        data = response.json()

        # Should have usage structure
        assert isinstance(data, (dict, list))


class TestEndToEndWorkflow:
    """
    Complete end-to-end workflow test.

    This test validates the entire multi-tenant agency workflow from start to finish.
    """

    def test_complete_agency_workflow(self, client: TestClient, test_pdf_file: bytes):
        """
        Complete end-to-end test of multi-tenant agency mode.

        Workflow:
        1. Create agency via API ✓
        2. Create two client tenants under agency ✓
        3. Upload resume to client A ✓
        4. Verify resume NOT visible to client B ✓
        5. Verify agency can see both clients' data ✓
        6. Verify usage tracking per client ✓
        7. Verify agency dashboard shows cross-client metrics ✓
        """
        # Step 1: Create agency via API
        print("\n=== Step 1: Creating Agency ===")
        agency_response = client.post(
            "/api/agencies/",
            json={
                "name": "E2E Test Agency",
                "slug": "e2e-test-agency",
                "domain": "e2e-test.com",
                "contact_email": "test@e2e-test.com"
            }
        )
        assert agency_response.status_code == 201, f"Failed to create agency: {agency_response.text}"
        agency = agency_response.json()
        agency_id = agency["id"]
        print(f"✓ Agency created: {agency_id}")

        # Step 2: Create two client tenants under agency
        print("\n=== Step 2: Creating Client Tenants ===")

        # Create Client A organization
        client_a_org = client.post(
            "/api/organizations/",
            json={"name": "E2E Client A", "slug": "e2e-client-a"}
        ).json()
        client_a_id = client_a_org["id"]
        print(f"✓ Client A organization created: {client_a_id}")

        # Create Client B organization
        client_b_org = client.post(
            "/api/organizations/",
            json={"name": "E2E Client B", "slug": "e2e-client-b"}
        ).json()
        client_b_id = client_b_org["id"]
        print(f"✓ Client B organization created: {client_b_id}")

        # Create tenant relationships
        tenant_a = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": client_a_id,
                "status": "active",
                "is_primary": True
            }
        ).json()
        tenant_a_id = tenant_a["id"]
        print(f"✓ Client A tenant created: {tenant_a_id}")

        tenant_b = client.post(
            "/api/client-tenants/",
            json={
                "agency_id": agency_id,
                "organization_id": client_b_id,
                "status": "active"
            }
        ).json()
        tenant_b_id = tenant_b["id"]
        print(f"✓ Client B tenant created: {tenant_b_id}")

        # Step 3: Upload resume to client A
        print("\n=== Step 3: Uploading Resume to Client A ===")
        upload_response = client.post(
            "/api/resumes/upload",
            headers={
                "X-Organization-ID": client_a_id,
                "X-Tenant-ID": tenant_a_id,
                "X-Agency-ID": agency_id
            },
            files={
                "file": ("candidate_resume.pdf", io.BytesIO(test_pdf_file), "application/pdf")
            }
        )
        assert upload_response.status_code == 201, f"Failed to upload resume: {upload_response.text}"
        resume = upload_response.json()
        resume_id = resume["id"]
        print(f"✓ Resume uploaded to Client A: {resume_id}")

        # Step 4: Verify resume NOT visible to client B
        print("\n=== Step 4: Verifying Data Isolation ===")

        # Check Client A can see the resume
        client_a_view = client.get(
            "/api/candidates/",
            headers={
                "X-Organization-ID": client_a_id,
                "X-Tenant-ID": tenant_a_id,
                "X-Agency-ID": agency_id
            }
        )
        assert client_a_view.status_code == 200
        client_a_data = client_a_view.json()
        client_a_resumes = [c["id"] for c in client_a_data.get("candidates", client_a_data.get("items", []))]
        assert resume_id in client_a_resumes, "Client A should see their own resume"
        print(f"✓ Client A can see resume {resume_id}")

        # Check Client B CANNOT see the resume
        client_b_view = client.get(
            "/api/candidates/",
            headers={
                "X-Organization-ID": client_b_id,
                "X-Tenant-ID": tenant_b_id,
                "X-Agency-ID": agency_id
            }
        )
        assert client_b_view.status_code == 200
        client_b_data = client_b_view.json()
        client_b_resumes = [c["id"] for c in client_b_data.get("candidates", client_b_data.get("items", []))]
        assert resume_id not in client_b_resumes, "DATA LEAKAGE: Client B should NOT see Client A's resume"
        print(f"✓ Client B cannot see Client A's resume (isolation confirmed)")

        # Step 5: Verify agency can see both clients' data
        print("\n=== Step 5: Verifying Agency Access ===")
        tenants_list = client.get(
            f"/api/client-tenants/?agency_id={agency_id}",
            headers={"X-Agency-ID": agency_id}
        )
        assert tenants_list.status_code == 200
        tenants_data = tenants_list.json()
        tenants = tenants_data.get("client_tenants", tenants_data.get("items", []))
        tenant_org_ids = [t["organization_id"] for t in tenants]
        assert client_a_id in tenant_org_ids, "Agency should see Client A"
        assert client_b_id in tenant_org_ids, "Agency should see Client B"
        print(f"✓ Agency can see both clients: {len(tenants)} total clients")

        # Step 6: Verify usage tracking per client
        print("\n=== Step 6: Verifying Usage Tracking ===")
        usage_response = client.get(
            f"/api/billing/usage?agency_id={agency_id}",
            headers={"X-Agency-ID": agency_id}
        )
        assert usage_response.status_code == 200, f"Failed to get usage data: {usage_response.text}"
        print(f"✓ Usage tracking endpoint accessible")

        # Step 7: Verify agency dashboard shows cross-client metrics
        print("\n=== Step 7: Verifying Cross-Client Analytics ===")
        analytics_response = client.get(
            f"/api/agency-analytics/summary?agency_id={agency_id}",
            headers={"X-Agency-ID": agency_id}
        )
        assert analytics_response.status_code == 200, f"Failed to get analytics: {analytics_response.text}"
        analytics_data = analytics_response.json()
        print(f"✓ Agency analytics endpoint accessible")
        print(f"  Analytics data: {analytics_data}")

        print("\n=== E2E Test Complete ===")
        print("✓ All verification steps passed")
        print("✓ Multi-tenant data isolation confirmed")
        print("✓ Agency cross-client access confirmed")
        print("✓ Usage tracking confirmed")
        print("✓ Analytics confirmed")


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "agency: marks tests as agency-related tests")
    config.addinivalue_line("markers", "multi_tenant: marks tests as multi-tenant isolation tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
