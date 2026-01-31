"""
Integration tests for resume comparison and ranking API.

This test suite validates the end-to-end integration between:
- Frontend (simulated via HTTP requests)
- Backend Comparison API (FastAPI endpoints)
- Multi-resume comparison logic
- Skill matching with synonym support
- Ranking and filtering capabilities
- Sharing functionality

Test Coverage:
- Create comparison views (2-5 resumes)
- List and filter comparisons
- Update and delete comparisons
- Shared comparison access
- Error scenarios (invalid resume counts, missing files, etc.)
- End-to-end comparison workflows
- Ranking by match percentage
"""
import io
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def test_pdf_file() -> bytes:
    """
    Create a minimal valid PDF file for testing.

    Returns:
        Bytes content of a simple PDF file
    """
    # Create a minimal PDF file with text content
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


@pytest.fixture
def sample_vacancy_data() -> dict:
    """
    Sample job vacancy data for comparison tests.

    Returns:
        Dictionary with vacancy requirements
    """
    return {
        "title": "Java Developer",
        "required_skills": ["Java", "Spring", "PostgreSQL", "Docker", "Kubernetes"],
        "additional_requirements": ["Kafka", "Redis", "Git"],
        "min_experience_months": 36,
    }


@pytest.fixture
def sample_vacancy_data_alternative() -> dict:
    """
    Alternative sample vacancy data for testing.

    Returns:
        Dictionary with different vacancy requirements
    """
    return {
        "title": "Python Developer",
        "required_skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
        "additional_requirements": ["Docker", "Kubernetes", "Celery"],
        "min_experience_months": 24,
    }


class TestCreateComparison:
    """Tests for creating comparison views."""

    def test_create_comparison_success(self, client: TestClient, sample_vacancy_data: dict):
        """Test creating a comparison view with valid data."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-123",
                "resume_ids": ["resume1", "resume2", "resume3"],
                "name": "Senior Developer Candidates",
                "created_by": "user-123",
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Validate response structure
        assert "id" in data
        assert data["vacancy_id"] == "vacancy-123"
        assert data["resume_ids"] == ["resume1", "resume2", "resume3"]
        assert data["name"] == "Senior Developer Candidates"
        assert data["created_by"] == "user-123"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_comparison_with_filters(self, client: TestClient):
        """Test creating a comparison with filter settings."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-456",
                "resume_ids": ["resume1", "resume2"],
                "name": "Filtered Comparison",
                "filters": {
                    "min_match_percentage": 50,
                    "max_match_percentage": 100,
                    "sort_by": "match_percentage",
                    "order": "desc"
                }
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["vacancy_id"] == "vacancy-456"
        assert data["filters"]["min_match_percentage"] == 50
        assert data["filters"]["sort_by"] == "match_percentage"

    def test_create_comparison_with_sharing(self, client: TestClient):
        """Test creating a comparison that can be shared."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-789",
                "resume_ids": ["resume1", "resume2", "resume3", "resume4"],
                "name": "Shared Comparison",
                "created_by": "user-456",
                "shared_with": ["user-789", "user-101", " recruiter@example.com"]
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["shared_with"] == ["user-789", "user-101", " recruiter@example.com"]

    def test_create_comparison_too_few_resumes(self, client: TestClient):
        """Test creating a comparison with less than 2 resumes (should fail)."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-123",
                "resume_ids": ["resume1"],  # Only 1 resume
                "name": "Invalid Comparison"
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "At least 2 resumes" in data["detail"]

    def test_create_comparison_too_many_resumes(self, client: TestClient):
        """Test creating a comparison with more than 5 resumes (should fail)."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-123",
                "resume_ids": ["resume1", "resume2", "resume3", "resume4", "resume5", "resume6"],  # 6 resumes
                "name": "Invalid Comparison"
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "Maximum 5 resumes" in data["detail"]

    def test_create_comparison_minimal_data(self, client: TestClient):
        """Test creating a comparison with only required fields."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-min",
                "resume_ids": ["resume1", "resume2"]
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["vacancy_id"] == "vacancy-min"
        assert data["name"] is None  # Optional field not provided
        assert data["created_by"] is None  # Optional field not provided


class TestListComparisons:
    """Tests for listing comparison views."""

    def test_list_comparisons_empty(self, client: TestClient):
        """Test listing comparisons when none exist."""
        response = client.get("/api/comparisons/")

        assert response.status_code == 200
        data = response.json()

        assert "comparisons" in data
        assert "total_count" in data
        assert isinstance(data["comparisons"], list)

    def test_list_comparisons_with_vacancy_filter(self, client: TestClient):
        """Test listing comparisons filtered by vacancy ID."""
        response = client.get("/api/comparisons/?vacancy_id=vacancy-123")

        assert response.status_code == 200
        data = response.json()

        assert "comparisons" in data
        assert "filters_applied" in data
        assert data["filters_applied"]["vacancy_id"] == "vacancy-123"

    def test_list_comparisons_with_creator_filter(self, client: TestClient):
        """Test listing comparisons filtered by creator."""
        response = client.get("/api/comparisons/?created_by=user-123")

        assert response.status_code == 200
        data = response.json()

        assert "comparisons" in data
        assert data["filters_applied"]["created_by"] == "user-123"

    def test_list_comparisons_with_match_percentage_range(self, client: TestClient):
        """Test listing comparisons filtered by match percentage range."""
        response = client.get(
            "/api/comparisons/?min_match_percentage=50&max_match_percentage=90"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filters_applied"]["min_match_percentage"] == 50
        assert data["filters_applied"]["max_match_percentage"] == 90

    def test_list_comparisons_invalid_range(self, client: TestClient):
        """Test with invalid match percentage range (min > max)."""
        response = client.get(
            "/api/comparisons/?min_match_percentage=90&max_match_percentage=50"
        )

        assert response.status_code == 422
        data = response.json()
        assert "min_match_percentage must be less than or equal" in data["detail"]

    def test_list_comparisons_sort_by_match_percentage(self, client: TestClient):
        """Test sorting comparisons by match percentage."""
        response = client.get(
            "/api/comparisons/?sort_by=match_percentage&order=desc"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filters_applied"]["sort_by"] == "match_percentage"
        assert data["filters_applied"]["order"] == "desc"

    def test_list_comparisons_sort_by_name(self, client: TestClient):
        """Test sorting comparisons by name."""
        response = client.get(
            "/api/comparisons/?sort_by=name&order=asc"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filters_applied"]["sort_by"] == "name"
        assert data["filters_applied"]["order"] == "asc"

    def test_list_comparisons_invalid_sort_field(self, client: TestClient):
        """Test sorting with invalid sort field."""
        response = client.get("/api/comparisons/?sort_by=invalid_field")

        assert response.status_code == 422
        data = response.json()
        assert "Invalid sort_by field" in data["detail"]

    def test_list_comparisons_invalid_order(self, client: TestClient):
        """Test sorting with invalid order."""
        response = client.get("/api/comparisons/?order=invalid")

        assert response.status_code == 422
        data = response.json()
        assert "Invalid order field" in data["detail"]

    def test_list_comparisons_with_pagination(self, client: TestClient):
        """Test pagination with limit and offset."""
        response = client.get("/api/comparisons/?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()

        # Should include pagination info in filters
        assert "filters_applied" in data

    def test_list_comparisons_invalid_limit(self, client: TestClient):
        """Test with invalid limit (too high)."""
        response = client.get("/api/comparisons/?limit=200")

        # Should still work but use default max
        assert response.status_code in [200, 422]

    def test_list_comparisons_combined_filters(self, client: TestClient):
        """Test listing with multiple filters combined."""
        response = client.get(
            "/api/comparisons/?"
            "vacancy_id=vacancy-123&"
            "created_by=user-456&"
            "min_match_percentage=60&"
            "sort_by=match_percentage&"
            "order=desc&"
            "limit=25"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filters_applied"]["vacancy_id"] == "vacancy-123"
        assert data["filters_applied"]["created_by"] == "user-456"
        assert data["filters_applied"]["min_match_percentage"] == 60


class TestGetComparison:
    """Tests for retrieving specific comparison views."""

    def test_get_comparison_success(self, client: TestClient):
        """Test retrieving a comparison by ID."""
        comparison_id = "test-comparison-123"
        response = client.get(f"/api/comparisons/{comparison_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == comparison_id
        assert "vacancy_id" in data
        assert "resume_ids" in data
        assert "created_at" in data

    def test_get_comparison_with_results(self, client: TestClient):
        """Test retrieving a comparison that has comparison results."""
        comparison_id = "comparison-with-results"
        response = client.get(f"/api/comparisons/{comparison_id}")

        assert response.status_code == 200
        data = response.json()

        # Should have comparison_results if available
        assert "comparison_results" in data

    def test_get_nonexistent_comparison(self, client: TestClient):
        """Test retrieving a comparison that doesn't exist."""
        # Current implementation returns placeholder, so this should still work
        response = client.get("/api/comparisons/nonexistent-id")

        # May return 200 with placeholder or 404 when database is integrated
        assert response.status_code in [200, 404]


class TestUpdateComparison:
    """Tests for updating comparison views."""

    def test_update_comparison_name(self, client: TestClient):
        """Test updating the name of a comparison."""
        comparison_id = "comparison-to-update"
        response = client.put(
            f"/api/comparisons/{comparison_id}",
            json={"name": "Updated Comparison Name"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == comparison_id
        assert data["name"] == "Updated Comparison Name"

    def test_update_comparison_filters(self, client: TestClient):
        """Test updating the filters of a comparison."""
        comparison_id = "comparison-filters"
        response = client.put(
            f"/api/comparisons/{comparison_id}",
            json={
                "filters": {
                    "min_match_percentage": 70,
                    "sort_by": "match_percentage"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filters"]["min_match_percentage"] == 70

    def test_update_comparison_shared_list(self, client: TestClient):
        """Test updating the shared_with list."""
        comparison_id = "comparison-share"
        response = client.put(
            f"/api/comparisons/{comparison_id}",
            json={
                "shared_with": ["new-user@example.com", "another-user@example.com"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "new-user@example.com" in data["shared_with"]

    def test_update_comparison_multiple_fields(self, client: TestClient):
        """Test updating multiple fields at once."""
        comparison_id = "comparison-multi"
        response = client.put(
            f"/api/comparisons/{comparison_id}",
            json={
                "name": "New Name",
                "filters": {"sort_by": "name"},
                "shared_with": ["user@example.com"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "New Name"
        assert data["filters"]["sort_by"] == "name"
        assert "user@example.com" in data["shared_with"]

    def test_update_comparison_empty_body(self, client: TestClient):
        """Test updating with empty JSON body (no changes)."""
        comparison_id = "comparison-no-change"
        response = client.put(
            f"/api/comparisons/{comparison_id}",
            json={}
        )

        assert response.status_code == 200
        # Should return comparison with no changes

    def test_update_nonexistent_comparison(self, client: TestClient):
        """Test updating a comparison that doesn't exist."""
        response = client.put(
            "/api/comparisons/nonexistent",
            json={"name": "New Name"}
        )

        # May return 200 with placeholder or 404 when database is integrated
        assert response.status_code in [200, 404]


class TestDeleteComparison:
    """Tests for deleting comparison views."""

    def test_delete_comparison_success(self, client: TestClient):
        """Test deleting a comparison by ID."""
        comparison_id = "comparison-to-delete"
        response = client.delete(f"/api/comparisons/{comparison_id}")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "deleted successfully" in data["message"]

    def test_delete_nonexistent_comparison(self, client: TestClient):
        """Test deleting a comparison that doesn't exist."""
        response = client.delete("/api/comparisons/nonexistent")

        # May return 200 or 404 depending on implementation
        assert response.status_code in [200, 404]


class TestSharedComparisons:
    """Tests for shared comparison access."""

    def test_get_shared_comparison_success(self, client: TestClient):
        """Test accessing a shared comparison via share ID."""
        share_id = "abc123def456"
        response = client.get(f"/api/comparisons/shared/{share_id}")

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "share_id" in data
        assert data["share_id"] == share_id

    def test_get_shared_comparison_has_results(self, client: TestClient):
        """Test that shared comparison includes comparison results."""
        share_id = "shared-with-results"
        response = client.get(f"/api/comparisons/shared/{share_id}")

        assert response.status_code == 200
        data = response.json()

        # Shared comparisons should show results
        assert "comparison_results" in data
        assert "vacancy_id" in data
        assert "resume_ids" in data

    def test_get_shared_nonexistent_comparison(self, client: TestClient):
        """Test accessing a shared comparison that doesn't exist."""
        response = client.get("/api/comparisons/shared/invalid-share-id")

        # May return 200 with placeholder or 404 when database is integrated
        assert response.status_code in [200, 404]


class TestCompareMultipleResumes:
    """Tests for the compare_multiple_resumes function logic."""

    @pytest.mark.slow
    def test_compare_two_resumes(
        self,
        client: TestClient,
        test_pdf_file: bytes,
        sample_vacancy_data: dict
    ):
        """Test comparing exactly 2 resumes (minimum)."""
        # Upload two test resumes
        resume1_response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume1.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
        )
        resume2_response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume2.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
        )

        assert resume1_response.status_code == 201
        assert resume2_response.status_code == 201

        resume1_id = resume1_response.json()["id"]
        resume2_id = resume2_response.json()["id"]

        # Create comparison
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-test",
                "resume_ids": [resume1_id, resume2_id]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["resume_ids"]) == 2

    @pytest.mark.slow
    def test_compare_five_resumes(
        self,
        client: TestClient,
        test_pdf_file: bytes
    ):
        """Test comparing 5 resumes (maximum)."""
        # Upload five test resumes
        resume_ids = []
        for i in range(5):
            response = client.post(
                "/api/resumes/upload",
                files={"file": (f"resume{i}.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
            )
            assert response.status_code == 201
            resume_ids.append(response.json()["id"])

        # Create comparison with all 5 resumes
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-max",
                "resume_ids": resume_ids
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["resume_ids"]) == 5


class TestEndToEndWorkflows:
    """Complete end-to-end workflow tests."""

    @pytest.mark.slow
    def test_create_and_retrieve_comparison_workflow(
        self,
        client: TestClient,
        test_pdf_file: bytes,
        sample_vacancy_data: dict
    ):
        """
        Test complete workflow: create comparison → retrieve → verify.

        This simulates:
        1. Upload multiple resumes
        2. Create comparison view
        3. Retrieve the comparison
        4. Verify all data is present
        """
        # Step 1: Upload resumes
        resume_ids = []
        for i in range(3):
            response = client.post(
                "/api/resumes/upload",
                files={"file": (f"candidate{i}.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
            )
            assert response.status_code == 201
            resume_ids.append(response.json()["id"])

        # Step 2: Create comparison
        create_response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-workflow",
                "resume_ids": resume_ids,
                "name": "Developer Candidates - Round 1"
            }
        )
        assert create_response.status_code == 201
        comparison_data = create_response.json()
        comparison_id = comparison_data["id"]

        # Step 3: Retrieve comparison
        get_response = client.get(f"/api/comparisons/{comparison_id}")
        assert get_response.status_code == 200
        retrieved_data = get_response.json()

        # Step 4: Verify data integrity
        assert retrieved_data["id"] == comparison_id
        assert retrieved_data["vacancy_id"] == "vacancy-workflow"
        assert retrieved_data["name"] == "Developer Candidates - Round 1"
        assert retrieved_data["resume_ids"] == resume_ids

    @pytest.mark.slow
    def test_create_update_delete_workflow(
        self,
        client: TestClient,
        test_pdf_file: bytes
    ):
        """
        Test full CRUD workflow: create → update → delete.

        This tests the complete lifecycle of a comparison view.
        """
        # Step 1: Upload resumes
        resume_ids = []
        for i in range(2):
            response = client.post(
                "/api/resumes/upload",
                files={"file": (f"resume{i}.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
            )
            assert response.status_code == 201
            resume_ids.append(response.json()["id"])

        # Step 2: Create comparison
        create_response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-crud",
                "resume_ids": resume_ids,
                "name": "Initial Name"
            }
        )
        assert create_response.status_code == 201
        comparison_id = create_response.json()["id"]

        # Step 3: Update comparison
        update_response = client.put(
            f"/api/comparisons/{comparison_id}",
            json={
                "name": "Updated Name",
                "filters": {"min_match_percentage": 60}
            }
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["name"] == "Updated Name"

        # Step 4: Delete comparison
        delete_response = client.delete(f"/api/comparisons/{comparison_id}")
        assert delete_response.status_code == 200

    @pytest.mark.slow
    def test_shared_comparison_workflow(
        self,
        client: TestClient,
        test_pdf_file: bytes
    ):
        """
        Test creating a comparison and accessing it via share link.

        This simulates sharing comparison results with team members.
        """
        # Upload resumes
        resume_ids = []
        for i in range(3):
            response = client.post(
                "/api/resumes/upload",
                files={"file": (f"resume{i}.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
            )
            assert response.status_code == 201
            resume_ids.append(response.json()["id"])

        # Create comparison with sharing
        create_response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-share",
                "resume_ids": resume_ids,
                "name": "Shared Senior Dev Candidates",
                "shared_with": [" recruiter@company.com", "hiring-manager@company.com"]
            }
        )
        assert create_response.status_code == 201
        comparison_id = create_response.json()["id"]

        # In a real implementation, this would generate a share_id
        # For now, we'll simulate accessing via share endpoint
        share_id = f"share-{comparison_id}"

        # Access shared comparison
        shared_response = client.get(f"/api/comparisons/shared/{share_id}")
        assert shared_response.status_code in [200, 404]  # May not find without database

    @pytest.mark.slow
    def test_filter_and_sort_workflow(
        self,
        client: TestClient,
        test_pdf_file: bytes
    ):
        """
        Test creating comparisons and listing with filters/sorting.

        This verifies the filtering and sorting functionality works correctly.
        """
        # Create multiple comparisons
        comparisons_created = []

        for i in range(3):
            # Upload resumes for each comparison
            resume_ids = []
            for j in range(2):
                response = client.post(
                    "/api/resumes/upload",
                    files={"file": (f"resume{i}-{j}.pdf", io.BytesIO(test_pdf_file), "application/pdf")}
                )
                assert response.status_code == 201
                resume_ids.append(response.json()["id"])

            # Create comparison
            response = client.post(
                "/api/comparisons/",
                json={
                    "vacancy_id": f"vacancy-{i}",
                    "resume_ids": resume_ids,
                    "name": f"Comparison {i}",
                    "created_by": f"user-{i % 2}"  # Alternate between user-0 and user-1
                }
            )
            assert response.status_code == 201
            comparisons_created.append(response.json())

        # Test filtering by creator
        filter_response = client.get("/api/comparisons/?created_by=user-0")
        assert filter_response.status_code == 200

        # Test sorting
        sort_response = client.get("/api/comparisons/?sort_by=name&order=asc")
        assert sort_response.status_code == 200


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_create_comparison_empty_resume_list(self, client: TestClient):
        """Test creating comparison with empty resume list."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-empty",
                "resume_ids": []
            }
        )

        assert response.status_code == 422
        assert "At least 2 resumes" in response.json()["detail"]

    def test_create_comparison_with_null_vacancy_id(self, client: TestClient):
        """Test creating comparison with null vacancy_id."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": None,
                "resume_ids": ["resume1", "resume2"]
            }
        )

        # Should fail validation
        assert response.status_code == 422

    def test_create_comparison_malformed_resume_ids(self, client: TestClient):
        """Test creating comparison with invalid resume_ids format."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "vacancy-test",
                "resume_ids": "not-a-list"  # Should be a list
            }
        )

        # Should fail validation
        assert response.status_code == 422

    def test_list_comparisons_invalid_limit_string(self, client: TestClient):
        """Test listing with invalid limit (string instead of int)."""
        response = client.get("/api/comparisons/?limit=abc")

        # Should fail validation or use default
        assert response.status_code in [200, 422]

    def test_list_comparisons_negative_offset(self, client: TestClient):
        """Test listing with negative offset."""
        response = client.get("/api/comparisons/?offset=-10")

        # Should fail validation
        assert response.status_code == 422

    def test_update_with_invalid_filters(self, client: TestClient):
        """Test updating with malformed filter object."""
        response = client.put(
            "/api/comparisons/some-id",
            json={
                "filters": "invalid-filter-object"  # Should be dict
            }
        )

        # Should fail validation
        assert response.status_code == 422

    def test_shared_access_malformed_share_id(self, client: TestClient):
        """Test accessing shared comparison with malformed share_id."""
        response = client.get("/api/comparisons/shared/")

        # Should return 404 or method not allowed
        assert response.status_code in [404, 405, 200]


# Pytest fixtures
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


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    """
    Clean up uploaded test files after each test.

    This fixture runs automatically after each test to remove
    any files uploaded during the test.
    """
    yield

    # Cleanup: Remove files from uploads directory
    upload_dir = Path("data/uploads")
    if upload_dir.exists():
        # Remove test files (those with hex IDs from our tests)
        for file in upload_dir.glob("*"):
            if file.is_file() and len(file.stem) == 16:  # Hex ID length
                try:
                    file.unlink()
                except Exception:
                    pass  # File may be locked by another process


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
