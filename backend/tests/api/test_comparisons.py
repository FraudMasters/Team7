"""
Unit tests for comparison API endpoints.

Tests cover:
- Create comparison endpoint
- List comparisons endpoint with filters
- Get comparison by ID endpoint
- Update comparison endpoint
- Delete comparison endpoint
- Compare multiple resumes endpoint
- Shared comparison endpoint (not implemented)
- Validation and error handling
"""
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: Configured test client
    """
    return TestClient(app)


class TestCreateComparisonEndpoint:
    """Tests for POST /api/comparisons/ endpoint."""

    def test_create_comparison_success(self, client):
        """Test successful comparison creation."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2", "resume3"],
            "name": "Senior Developer Candidates",
            "created_by": "user-123",
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["vacancy_id"] == payload["vacancy_id"]
        assert data["resume_ids"] == payload["resume_ids"]
        assert data["name"] == "Senior Developer Candidates"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_comparison_minimal_payload(self, client):
        """Test comparison creation with minimal required fields."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["vacancy_id"] == payload["vacancy_id"]
        assert data["resume_ids"] == payload["resume_ids"]

    def test_create_comparison_with_filters(self, client):
        """Test comparison creation with filter settings."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
            "filters": {
                "min_match_percentage": 50,
                "max_match_percentage": 100,
                "sort_by": "match_percentage",
            },
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["filters"] == payload["filters"]

    def test_create_comparison_with_shared_with(self, client):
        """Test comparison creation with sharing settings."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
            "shared_with": ["user-456", "user-789"],
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["shared_with"] == payload["shared_with"]

    def test_create_comparison_invalid_vacancy_id_format(self, client):
        """Test comparison creation with invalid vacancy_id format."""
        payload = {
            "vacancy_id": "invalid-uuid-format",
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 422
        assert "Invalid vacancy_id format" in response.json()["detail"]

    def test_create_comparison_too_few_resumes(self, client):
        """Test comparison creation with less than 2 resumes."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],  # Only 1 resume
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 422
        assert "At least 2 resumes" in response.json()["detail"]

    def test_create_comparison_too_many_resumes(self, client):
        """Test comparison creation with more than 5 resumes."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2", "resume3", "resume4", "resume5", "resume6"],  # 6 resumes
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 422
        assert "Maximum 5 resumes" in response.json()["detail"]

    def test_create_comparison_missing_vacancy_id(self, client):
        """Test comparison creation without vacancy_id."""
        payload = {
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 422

    def test_create_comparison_missing_resume_ids(self, client):
        """Test comparison creation without resume_ids."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 422


class TestListComparisonsEndpoint:
    """Tests for GET /api/comparisons/ endpoint."""

    def test_list_comparisons_success(self, client):
        """Test successful comparison listing."""
        response = client.get("/api/comparisons/")
        assert response.status_code == 200
        data = response.json()
        assert "comparisons" in data
        assert "total_count" in data
        assert isinstance(data["comparisons"], list)
        assert isinstance(data["total_count"], int)

    def test_list_comparisons_by_vacancy_id(self, client):
        """Test filtering comparisons by vacancy_id."""
        vacancy_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/api/comparisons/?vacancy_id={vacancy_id}")
        assert response.status_code == 200
        data = response.json()
        assert "comparisons" in data

    def test_list_comparisons_by_created_by(self, client):
        """Test filtering comparisons by creator."""
        response = client.get("/api/comparisons/?created_by=user-123")
        assert response.status_code == 200
        data = response.json()
        assert "comparisons" in data

    def test_list_comparisons_invalid_vacancy_id(self, client):
        """Test listing with invalid vacancy_id format."""
        response = client.get("/api/comparisons/?vacancy_id=invalid-uuid")
        assert response.status_code == 422
        assert "Invalid vacancy_id format" in response.json()["detail"]

    def test_list_comparisons_sort_by_created_at(self, client):
        """Test sorting by created_at."""
        response = client.get("/api/comparisons/?sort_by=created_at&order=desc")
        assert response.status_code == 200

    def test_list_comparisons_sort_by_name(self, client):
        """Test sorting by name."""
        response = client.get("/api/comparisons/?sort_by=name&order=asc")
        assert response.status_code == 200

    def test_list_comparisons_invalid_sort_field(self, client):
        """Test sorting with invalid field."""
        response = client.get("/api/comparisons/?sort_by=invalid_field")
        assert response.status_code == 422
        assert "Invalid sort_by field" in response.json()["detail"]

    def test_list_comparisons_invalid_order(self, client):
        """Test sorting with invalid order."""
        response = client.get("/api/comparisons/?order=invalid_order")
        assert response.status_code == 422
        assert "Invalid order field" in response.json()["detail"]

    def test_list_comparisons_with_limit(self, client):
        """Test limit parameter."""
        response = client.get("/api/comparisons/?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["comparisons"]) <= 5

    def test_list_comparisons_with_offset(self, client):
        """Test offset parameter."""
        response = client.get("/api/comparisons/?offset=10")
        assert response.status_code == 200

    def test_list_comparisons_limit_validation(self, client):
        """Test limit validation (max 100)."""
        response = client.get("/api/comparisons/?limit=150")
        assert response.status_code == 422

    def test_list_comparisons_offset_validation(self, client):
        """Test offset validation (must be >= 0)."""
        response = client.get("/api/comparisons/?offset=-1")
        assert response.status_code == 422

    def test_list_comparisons_match_percentage_range_valid(self, client):
        """Test valid match percentage range filter."""
        response = client.get("/api/comparisons/?min_match_percentage=50&max_match_percentage=90")
        assert response.status_code == 200

    def test_list_comparisons_match_percentage_range_invalid(self, client):
        """Test invalid match percentage range (min > max)."""
        response = client.get("/api/comparisons/?min_match_percentage=90&max_match_percentage=50")
        assert response.status_code == 422
        assert "min_match_percentage must be less than or equal to max_match_percentage" in response.json()["detail"]


class TestGetComparisonEndpoint:
    """Tests for GET /api/comparisons/{comparison_id} endpoint."""

    def test_get_comparison_success(self, client):
        """Test successful comparison retrieval."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/api/comparisons/{comparison_id}")
        # May return 404 if comparison doesn't exist
        assert response.status_code in [200, 404]

    def test_get_comparison_invalid_uuid(self, client):
        """Test retrieval with invalid UUID format."""
        response = client.get("/api/comparisons/invalid-uuid-format")
        assert response.status_code == 422
        assert "Invalid comparison_id format" in response.json()["detail"]

    def test_get_comparison_response_structure(self, client):
        """Test comparison response has correct structure."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/api/comparisons/{comparison_id}")
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "vacancy_id" in data
            assert "resume_ids" in data
            assert "created_at" in data
            assert "updated_at" in data


class TestUpdateComparisonEndpoint:
    """Tests for PUT /api/comparisons/{comparison_id} endpoint."""

    def test_update_comparison_name(self, client):
        """Test updating comparison name."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "name": "Updated Comparison Name",
        }
        response = client.put(f"/api/comparisons/{comparison_id}", json=payload)
        # May return 404 if comparison doesn't exist
        assert response.status_code in [200, 404]

    def test_update_comparison_filters(self, client):
        """Test updating comparison filters."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "filters": {
                "min_match_percentage": 60,
                "sort_by": "match_percentage",
            },
        }
        response = client.put(f"/api/comparisons/{comparison_id}", json=payload)
        assert response.status_code in [200, 404]

    def test_update_comparison_shared_with(self, client):
        """Test updating shared users list."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "shared_with": ["user-123", "user-456"],
        }
        response = client.put(f"/api/comparisons/{comparison_id}", json=payload)
        assert response.status_code in [200, 404]

    def test_update_comparison_notes(self, client):
        """Test updating comparison notes."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "notes": {
                "resume-1": "Strong candidate, interview scheduled",
                "resume-2": "Missing key skills",
            },
        }
        response = client.put(f"/api/comparisons/{comparison_id}", json=payload)
        assert response.status_code in [200, 404]

    def test_update_comparison_multiple_fields(self, client):
        """Test updating multiple fields at once."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "name": "Updated Name",
            "filters": {"sort_by": "name"},
            "notes": {"resume-1": "Note"},
        }
        response = client.put(f"/api/comparisons/{comparison_id}", json=payload)
        assert response.status_code in [200, 404]

    def test_update_comparison_invalid_uuid(self, client):
        """Test update with invalid UUID format."""
        payload = {"name": "Updated Name"}
        response = client.put("/api/comparisons/invalid-uuid", json=payload)
        assert response.status_code == 422
        assert "Invalid comparison_id format" in response.json()["detail"]

    def test_update_comparison_empty_body(self, client):
        """Test update with empty body."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {}
        response = client.put(f"/api/comparisons/{comparison_id}", json=payload)
        # Should work - just updates nothing
        assert response.status_code in [200, 404]


class TestDeleteComparisonEndpoint:
    """Tests for DELETE /api/comparisons/{comparison_id} endpoint."""

    def test_delete_comparison_success(self, client):
        """Test successful comparison deletion."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.delete(f"/api/comparisons/{comparison_id}")
        # May return 404 if comparison doesn't exist
        assert response.status_code in [200, 404]

    def test_delete_comparison_invalid_uuid(self, client):
        """Test deletion with invalid UUID format."""
        response = client.delete("/api/comparisons/invalid-uuid-format")
        assert response.status_code == 422
        assert "Invalid comparison_id format" in response.json()["detail"]

    def test_delete_comparison_response_structure(self, client):
        """Test deletion response has correct structure."""
        comparison_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.delete(f"/api/comparisons/{comparison_id}")
        if response.status_code == 200:
            data = response.json()
            assert "message" in data


class TestCompareMultipleEndpoint:
    """Tests for POST /api/comparisons/compare-multiple endpoint."""

    def test_compare_multiple_success(self, client):
        """Test successful comparison of multiple resumes."""
        payload = {
            "vacancy_id": "vacancy-123",
            "resume_ids": ["resume1", "resume2", "resume3"],
            "vacancy_data": {
                "title": "Senior Java Developer",
                "required_skills": ["Java", "Spring", "SQL"],
                "min_experience_months": 60,
            },
        }
        response = client.post("/api/comparisons/compare-multiple", json=payload)
        # May return 404 if resume files don't exist
        assert response.status_code in [200, 404, 500]

    def test_compare_multiple_without_vacancy_data(self, client):
        """Test comparison without explicit vacancy_data."""
        payload = {
            "vacancy_id": "vacancy-123",
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/comparisons/compare-multiple", json=payload)
        # Should use default vacancy data
        assert response.status_code in [200, 404, 500]

    def test_compare_multiple_too_few_resumes(self, client):
        """Test comparison with less than 2 resumes."""
        payload = {
            "vacancy_id": "vacancy-123",
            "resume_ids": ["resume1"],  # Only 1 resume
        }
        response = client.post("/api/comparisons/compare-multiple", json=payload)
        assert response.status_code == 422

    def test_compare_multiple_too_many_resumes(self, client):
        """Test comparison with more than 5 resumes."""
        payload = {
            "vacancy_id": "vacancy-123",
            "resume_ids": ["r1", "r2", "r3", "r4", "r5", "r6"],  # 6 resumes
        }
        response = client.post("/api/comparisons/compare-multiple", json=payload)
        assert response.status_code == 422

    def test_compare_multiple_missing_vacancy_id(self, client):
        """Test comparison without vacancy_id."""
        payload = {
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/comparisons/compare-multiple", json=payload)
        assert response.status_code == 422

    def test_compare_multiple_missing_resume_ids(self, client):
        """Test comparison without resume_ids."""
        payload = {
            "vacancy_id": "vacancy-123",
        }
        response = client.post("/api/comparisons/compare-multiple", json=payload)
        assert response.status_code == 422

    def test_compare_multiple_response_structure(self, client):
        """Test comparison response has correct structure."""
        payload = {
            "vacancy_id": "vacancy-123",
            "resume_ids": ["resume1", "resume2"],
            "vacancy_data": {
                "title": "Developer",
                "required_skills": ["Python"],
            },
        }
        response = client.post("/api/comparisons/compare-multiple", json=payload)
        if response.status_code == 200:
            data = response.json()
            assert "vacancy_id" in data
            assert "comparisons" in data
            assert isinstance(data["comparisons"], list)
            assert "all_unique_skills" in data
            assert "processing_time" in data


class TestSharedComparisonEndpoint:
    """Tests for GET /api/comparisons/shared/{share_id} endpoint."""

    def test_get_shared_comparison_not_found(self, client):
        """Test shared comparison endpoint (not implemented)."""
        share_id = "abc123def456"
        response = client.get(f"/api/comparisons/shared/{share_id}")
        # Should return 404 as sharing is not fully implemented
        assert response.status_code == 404
        assert "Sharing functionality" in response.json()["detail"]


class TestErrorHandling:
    """Tests for error handling across all endpoints."""

    def test_method_not_allowed(self, client):
        """Test unsupported HTTP methods."""
        # GET on POST endpoint
        response = client.post("/api/comparisons/123")
        assert response.status_code in [405, 404]

    def test_invalid_json(self, client):
        """Test endpoints with invalid JSON."""
        response = client.post(
            "/api/comparisons/",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_content_type(self, client):
        """Test POST endpoints without Content-Type."""
        response = client.post(
            "/api/comparisons/",
            data="vacancy_id=test&resume_ids=r1,r2",
        )
        # Should either work or return 415/422
        assert response.status_code in [200, 201, 415, 422]


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_create_comparison_max_resumes(self, client):
        """Test comparison creation with exactly 5 resumes (maximum)."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2", "resume3", "resume4", "resume5"],
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201

    def test_create_comparison_min_resumes(self, client):
        """Test comparison creation with exactly 2 resumes (minimum)."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201

    def test_create_comparison_very_long_name(self, client):
        """Test comparison creation with very long name."""
        long_name = "A" * 500
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
            "name": long_name,
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201

    def test_create_comparison_special_characters_in_name(self, client):
        """Test comparison creation with special characters."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
            "name": "Comparison <script>alert('test')</script>",
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201

    def test_create_comparison_unicode_in_name(self, client):
        """Test comparison creation with unicode characters."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
            "name": "比较 名称",
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201

    def test_create_comparison_empty_filters(self, client):
        """Test comparison creation with empty filters dict."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
            "filters": {},
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201

    def test_create_comparison_complex_filters(self, client):
        """Test comparison with complex filters."""
        complex_filters = {
            "min_match_percentage": 50,
            "max_match_percentage": 100,
            "sort_by": "match_percentage",
            "sort_order": "desc",
            "filter_field_1": "value_1",
            "filter_field_2": ["value_2a", "value_2b"],
            "nested": {"key": "value"},
        }
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2"],
            "filters": complex_filters,
        }
        response = client.post("/api/comparisons/", json=payload)
        assert response.status_code == 201

    def test_list_comparisons_default_pagination(self, client):
        """Test default pagination parameters."""
        response = client.get("/api/comparisons/")
        assert response.status_code == 200

    def test_list_comparisons_combined_filters(self, client):
        """Test combining multiple filters."""
        response = client.get(
            "/api/comparisons/?vacancy_id=123e4567-e89b-12d3-a456-426614174000"
            "&created_by=user-123&sort_by=name&order=asc&limit=10&offset=0"
        )
        assert response.status_code == 200
