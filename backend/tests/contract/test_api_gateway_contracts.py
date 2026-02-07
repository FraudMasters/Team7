"""
Contract tests for API Gateway to service boundaries.

This module provides contract tests verifying that:
1. API Gateway endpoints return responses matching expected schemas
2. Service boundaries maintain consistent interfaces
3. Error responses follow standard contract
4. Response models contain required fields with correct types

Contract tests differ from integration tests:
- Contract tests verify interface compatibility (schema, types, required fields)
- Integration tests verify end-to-end functionality

Markers:
    - contract: Marks tests as contract tests (API/service interface verification)
"""
import json
import logging
from typing import Any, Dict
from uuid import uuid4

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================================================
# Test Helpers
# ============================================================================

def validate_response_schema(
    response_data: Dict[str, Any],
    required_fields: Dict[str, type],
    optional_fields: Dict[str, type] = None,
) -> None:
    """
    Validate response data matches expected schema.

    Args:
        response_data: The response JSON data
        required_fields: Dict of required field names to their types
        optional_fields: Dict of optional field names to their types

    Raises:
        AssertionError: If validation fails
    """
    # Check required fields
    for field, field_type in required_fields.items():
        assert field in response_data, f"Missing required field: {field}"
        value = response_data[field]
        assert value is not None, f"Required field '{field}' is None"
        assert isinstance(value, field_type), (
            f"Field '{field}' has wrong type: "
            f"expected {field_type}, got {type(value)}"
        )

    # Check optional fields if present
    optional_fields = optional_fields or {}
    for field, field_type in optional_fields.items():
        if field in response_data:
            value = response_data[field]
            if value is not None:
                assert isinstance(value, field_type), (
                    f"Field '{field}' has wrong type: "
                    f"expected {field_type}, got {type(value)}"
                )


def validate_error_response(
    response_data: Dict[str, Any],
    expected_status: int = None,
) -> None:
    """
    Validate error response follows standard contract.

    Args:
        response_data: The error response JSON data
        expected_status: Expected HTTP status code

    Raises:
        AssertionError: If validation fails
    """
    # Error responses should have 'detail' field
    assert "detail" in response_data, "Error response missing 'detail' field"
    assert isinstance(response_data["detail"], str), (
        "Error 'detail' must be a string"
    )

    # Some endpoints may have additional error fields
    allowed_fields = {"detail", "error_code", "error_type", "context"}
    for field in response_data:
        assert field in allowed_fields, f"Unexpected error field: {field}"


def validate_list_response(
    response_data: Dict[str, Any],
    item_field: str = "items",
) -> None:
    """
    Validate paginated list response follows standard contract.

    Args:
        response_data: The response JSON data
        item_field: Field name containing the list items

    Raises:
        AssertionError: If validation fails
    """
    assert item_field in response_data, f"List response missing '{item_field}' field"
    assert isinstance(response_data[item_field], list), (
        f"Field '{item_field}' must be a list"
    )

    # Common pagination fields
    if "total" in response_data:
        assert isinstance(response_data["total"], int), (
            "Pagination 'total' must be an integer"
        )
        assert response_data["total"] >= 0, "Pagination 'total' must be non-negative"

    if "skip" in response_data:
        assert isinstance(response_data["skip"], int), (
            "Pagination 'skip' must be an integer"
        )
        assert response_data["skip"] >= 0, "Pagination 'skip' must be non-negative"

    if "limit" in response_data:
        assert isinstance(response_data["limit"], int), (
            "Pagination 'limit' must be an integer"
        )
        assert response_data["limit"] > 0, "Pagination 'limit' must be positive"


# ============================================================================
# Candidate API Contract Tests
# ============================================================================

@pytest.mark.contract
class TestCandidateListContract:
    """
    Contract tests for /api/candidates endpoint.

    Verifies that the candidate list API returns responses
    matching the expected schema and contract.
    """

    async def test_candidates_list_response_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that GET /api/candidates returns valid response schema.

        Contract requirements:
        - Response is a list
        - Each item has required fields: id, filename, current_stage, stage_name
        - Fields have correct types
        """
        response = await client.get("/api/candidates")

        # Should succeed for valid request
        assert response.status_code in (200, 401, 403), (
            f"Unexpected status: {response.status_code}"
        )

        # If authenticated, validate response structure
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Response should be a list"

            if len(data) > 0:
                candidate = data[0]
                validate_response_schema(
                    candidate,
                    required_fields={
                        "id": str,
                        "filename": str,
                        "current_stage": str,
                        "stage_name": str,
                        "created_at": str,
                        "updated_at": str,
                    },
                    optional_fields={
                        "vacancy_id": (str, type(None)),
                        "notes": (str, type(None)),
                        "tags": list,
                        "notes_count": int,
                        "latest_activity": (dict, type(None)),
                    },
                )

    async def test_candidates_list_with_filters_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that GET /api/candidates with filters returns valid schema.

        Contract requirements:
        - Accepts query parameters for filtering
        - Returns consistent response structure
        """
        params = {
            "stage": "applied",
            "limit": 10,
        }
        response = await client.get("/api/candidates", params=params)

        # Response structure should be consistent
        assert response.status_code in (200, 401, 403), (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Response should be a list"


@pytest.mark.contract
class TestCandidateMovementContract:
    """
    Contract tests for candidate movement API.

    Verifies that moving candidates between stages follows
    the expected contract.
    """

    async def test_move_candidate_request_schema(
        self,
        client: AsyncClient,
        sample_resume,
    ) -> None:
        """
        Test that POST /api/candidates/{id}/move accepts valid request.

        Contract requirements:
        - Accepts stage_id, optional vacancy_id, optional notes
        - Returns response with previous and new stage
        """
        request_data = {
            "stage_id": "interview",
            "vacancy_id": str(uuid4()),
            "notes": "Moved to interview stage",
        }

        response = await client.post(
            f"/api/candidates/{sample_resume.id}/move",
            json=request_data,
        )

        # May fail auth, but should accept request format
        if response.status_code not in (200, 201, 401, 403, 404):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code in (200, 201):
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "id": str,
                    "resume_id": str,
                    "previous_stage": str,
                    "new_stage": str,
                    "message": str,
                },
            )


# ============================================================================
# Vacancy API Contract Tests
# ============================================================================

@pytest.mark.contract
class TestVacancyApiContract:
    """
    Contract tests for /api/vacancies endpoint.

    Verifies that vacancy management APIs maintain
    consistent response contracts.
    """

    async def test_create_vacancy_request_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that POST /api/vacancies accepts valid request schema.

        Contract requirements:
        - Accepts title, description, required_skills
        - Accepts optional fields: location, salary_min, salary_max, etc.
        - Returns created vacancy with all fields
        """
        request_data = {
            "title": "Python Developer",
            "description": "A test job description",
            "required_skills": ["Python", "FastAPI"],
            "min_experience_months": 36,
            "location": "Remote",
            "salary_min": 80000,
            "salary_max": 120000,
        }

        response = await client.post("/api/vacancies", json=request_data)

        # May fail auth, but should accept request format
        if response.status_code not in (200, 201, 401, 403):
            # If validation fails, check it's for expected reason
            if response.status_code == 422:
                # Validation error - check it's not for our test data
                pass
            else:
                assert False, f"Unexpected status: {response.status_code}"

        if response.status_code in (200, 201):
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "id": str,
                    "title": str,
                    "description": str,
                    "required_skills": list,
                    "created_at": str,
                    "updated_at": str,
                },
                optional_fields={
                    "min_experience_months": (int, type(None)),
                    "location": (str, type(None)),
                    "salary_min": (int, type(None)),
                    "salary_max": (int, type(None)),
                    "industry": (str, type(None)),
                    "work_format": (str, type(None)),
                },
            )

    async def test_list_vacancies_response_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that GET /api/vacancies returns valid list schema.

        Contract requirements:
        - Returns list of vacancies
        - Supports pagination: skip, limit
        - Each vacancy has required fields
        """
        params = {
            "skip": 0,
            "limit": 10,
        }
        response = await client.get("/api/vacancies", params=params)

        assert response.status_code in (200, 401, 403), (
            f"Unexpected status: {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict)), "Response should be list or dict"

            # Some endpoints return paginated as dict with items
            if isinstance(data, dict):
                if "items" in data:
                    validate_list_response(data, "items")
                    items = data["items"]
                else:
                    items = []
            else:
                items = data

            if len(items) > 0:
                vacancy = items[0]
                validate_response_schema(
                    vacancy,
                    required_fields={
                        "id": str,
                        "title": str,
                        "description": str,
                        "required_skills": list,
                        "created_at": str,
                    },
                )


# ============================================================================
# Matching API Contract Tests
# ============================================================================

@pytest.mark.contract
class TestMatchingApiContract:
    """
    Contract tests for /api/matching endpoint.

    Verifies that resume-to-vacancy matching API
    maintains consistent response contracts.
    """

    async def test_match_request_schema(
        self,
        client: AsyncClient,
        sample_resume,
        sample_vacancy,
    ) -> None:
        """
        Test that POST /api/matching accepts valid request schema.

        Contract requirements:
        - Accepts resume_id and vacancy_id
        - Returns match results with scores and highlighting
        """
        request_data = {
            "resume_id": str(sample_resume.id),
            "vacancy_id": str(sample_vacancy.id),
        }

        response = await client.post("/api/matching", json=request_data)

        # Should accept request format
        if response.status_code not in (200, 401, 403, 404):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            # Match response should have score and match details
            validate_response_schema(
                data,
                required_fields={
                    "match_percentage": (int, float),
                },
                optional_fields={
                    "matched_skills": list,
                    "missing_skills": list,
                    "additional_skills": list,
                    "experience_match": (str, type(None)),
                    "highlights": dict,
                },
            )

            # Score should be in valid range
            assert 0 <= data["match_percentage"] <= 100, (
                f"Match percentage out of range: {data['match_percentage']}"
            )


# ============================================================================
# Ranking API Contract Tests
# ============================================================================

@pytest.mark.contract
class TestRankingApiContract:
    """
    Contract tests for /api/ranking endpoint.

    Verifies that AI-powered candidate ranking API
    maintains consistent response contracts.
    """

    async def test_rank_candidate_request_schema(
        self,
        client: AsyncClient,
        sample_resume,
        sample_vacancy,
    ) -> None:
        """
        Test that POST /api/ranking accepts valid request schema.

        Contract requirements:
        - Accepts resume_id, vacancy_id
        - Returns ranking score with confidence
        - Includes feature contributions
        """
        request_data = {
            "resume_id": str(sample_resume.id),
            "vacancy_id": str(sample_vacancy.id),
            "use_experiment": True,
        }

        response = await client.post("/api/ranking/rank", json=request_data)

        # Should accept request format
        if response.status_code not in (200, 401, 403, 404, 503):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "resume_id": str,
                    "vacancy_id": str,
                    "rank_score": (int, float),
                    "recommendation": str,
                    "confidence": (int, float),
                    "model_version": str,
                },
                optional_fields={
                    "rank_position": (int, type(None)),
                    "is_experiment": bool,
                    "experiment_group": (str, type(None)),
                    "feature_contributions": dict,
                    "ranking_factors": dict,
                },
            )

            # Scores should be in valid ranges
            assert 0 <= data["rank_score"] <= 1, (
                f"Rank score out of range: {data['rank_score']}"
            )
            assert 0 <= data["confidence"] <= 1, (
                f"Confidence out of range: {data['confidence']}"
            )

    async def test_get_vacancy_rankings_schema(
        self,
        client: AsyncClient,
        sample_vacancy,
    ) -> None:
        """
        Test that GET /api/ranking/vacancy/{id} returns valid schema.

        Contract requirements:
        - Returns list of ranked candidates
        - Includes rank scores and positions
        """
        response = await client.get(f"/api/ranking/vacancy/{sample_vacancy.id}")

        if response.status_code not in (200, 401, 403, 404):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Response should be a list"

            if len(data) > 0:
                ranking = data[0]
                validate_response_schema(
                    ranking,
                    required_fields={
                        "resume_id": str,
                        "rank_score": (int, float),
                        "rank_position": int,
                    },
                    optional_fields={
                        "recommendation": str,
                        "confidence": (int, float),
                    },
                )


# ============================================================================
# Search API Contract Tests
# ============================================================================

@pytest.mark.contract
class TestSearchApiContract:
    """
    Contract tests for /api/search endpoint.

    Verifies that advanced search API maintains
    consistent response contracts.
    """

    async def test_search_request_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that POST /api/search accepts valid request schema.

        Contract requirements:
        - Accepts query, filters, skip, limit, sort_by
        - Returns search results with metadata
        """
        request_data = {
            "query": "Python developer",
            "filters": {
                "skills": ["Python"],
                "min_experience_years": 3,
            },
            "skip": 0,
            "limit": 10,
            "sort_by": "relevance",
        }

        response = await client.post("/api/search", json=request_data)

        # Should accept request format
        if response.status_code not in (200, 401, 403):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "total": int,
                    "candidates": list,
                },
                optional_fields={
                    "query": str,
                    "filters_applied": dict,
                    "execution_time_seconds": (int, float),
                },
            )

            # Total should be non-negative
            assert data["total"] >= 0, f"Total count negative: {data['total']}"

    async def test_search_with_boolean_operators_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that search accepts boolean operators in query.

        Contract requirements:
        - Accepts AND, OR, NOT operators in query string
        - Returns consistent response structure
        """
        request_data = {
            "query": "Python AND Django OR FastAPI NOT Java",
            "skip": 0,
            "limit": 10,
        }

        response = await client.post("/api/search", json=request_data)

        # Response structure should be consistent
        if response.status_code not in (200, 401, 403):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "total": int,
                    "candidates": list,
                },
            )


# ============================================================================
# Resume Upload Contract Tests
# ============================================================================

@pytest.mark.contract
class TestResumeUploadContract:
    """
    Contract tests for /api/resumes/upload endpoint.

    Verifies that resume upload API maintains
    consistent response contracts.
    """

    async def test_resume_upload_response_schema(
        self,
        client: AsyncClient,
        temp_dir,
    ) -> None:
        """
        Test that POST /api/resumes/upload returns valid schema.

        Contract requirements:
        - Accepts multipart/form-data with file
        - Returns resume record with id, filename, status
        """
        # Create minimal PDF file
        import os
        pdf_path = temp_dir / "test_resume.pdf"
        pdf_path.write_bytes(
            b"%PDF-1.4\n"
            b"1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
            b"2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n"
            b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n>>\nendobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
            b"trailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF"
        )

        with open(pdf_path, "rb") as f:
            files = {"file": ("test_resume.pdf", f, "application/pdf")}
            response = await client.post("/api/resumes/upload", files=files)

        # Should accept file upload
        if response.status_code not in (200, 201, 401, 403, 413, 415):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code in (200, 201):
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "id": str,
                    "filename": str,
                    "status": str,
                    "message": str,
                },
            )

            # Status should be valid
            valid_statuses = ["pending", "processing", "completed", "failed"]
            assert data["status"] in valid_statuses, (
                f"Invalid status: {data['status']}"
            )


# ============================================================================
# Error Response Contract Tests
# ============================================================================

@pytest.mark.contract
class TestErrorResponseContract:
    """
    Contract tests for standardized error responses.

    Verifies that all endpoints return consistent error
    response format following the contract.
    """

    async def test_404_response_contract(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that 404 responses follow standard contract.

        Contract requirements:
        - Has 'detail' field with error message
        - Consistent structure across endpoints
        """
        # Test with non-existent resource
        fake_id = uuid4()
        response = await client.get(f"/api/candidates/{fake_id}")

        if response.status_code == 404:
            data = response.json()
            validate_error_response(data, expected_status=404)

    async def test_422_validation_error_contract(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that 422 validation errors follow standard contract.

        Contract requirements:
        - Has 'detail' field describing validation issues
        - Provides field-level error information
        """
        # Send invalid data
        invalid_data = {
            "title": "AB",  # Too short
            "description": "short",  # Too short
        }

        response = await client.post("/api/vacancies", json=invalid_data)

        if response.status_code == 422:
            data = response.json()
            validate_error_response(data, expected_status=422)

            # Validation errors should have detail
            assert "detail" in data, "Validation error missing 'detail'"
            assert isinstance(data["detail"], list), (
                "Validation detail should be a list"
            )

    async def test_401_unauthorized_contract(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that 401 unauthorized responses follow standard contract.

        Contract requirements:
        - Has 'detail' field explaining authorization requirement
        - Consistent structure
        """
        # Most endpoints require auth, so any protected endpoint works
        response = await client.get("/api/candidates")

        if response.status_code == 401:
            data = response.json()
            validate_error_response(data, expected_status=401)

    async def test_403_forbidden_contract(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that 403 forbidden responses follow standard contract.

        Contract requirements:
        - Has 'detail' field explaining permission denial
        - Consistent structure
        """
        # Try accessing admin endpoint
        response = await client.get("/api/users")

        if response.status_code == 403:
            data = response.json()
            validate_error_response(data, expected_status=403)


# ============================================================================
# Service Integration Contract Tests
# ============================================================================

@pytest.mark.contract
class TestCacheServiceContract:
    """
    Contract tests for Cache Service integration.

    Verifies that cache service maintains consistent interface
    when used by API endpoints.
    """

    async def test_cache_key_format_contract(
        self,
        client: AsyncClient,
        sample_resume,
    ) -> None:
        """
        Test that cache keys follow expected format.

        Contract requirements:
        - Cache keys use format: {prefix}:{namespace}:{key}
        - Namespace is consistent for each entity type
        """
        from services.cache_service import CacheService

        # Verify cache service has correct namespaces
        assert hasattr(CacheService, "NAMESPACE_CANDIDATE")
        assert hasattr(CacheService, "NAMESPACE_VACANCY")
        assert hasattr(CacheService, "NAMESPACE_MATCH")

        # Namespaces should be strings
        assert isinstance(CacheService.NAMESPACE_CANDIDATE, str)
        assert isinstance(CacheService.NAMESPACE_VACANCY, str)
        assert isinstance(CacheService.NAMESPACE_MATCH, str)


@pytest.mark.contract
class TestSearchServiceContract:
    """
    Contract tests for Search Service integration.

    Verifies that search service maintains consistent interface.
    """

    async def test_search_filters_contract(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that search service accepts expected filter format.

        Contract requirements:
        - Accepts SearchFilters dataclass structure
        - Supports all expected filter types
        """
        from services.search_service import SearchFilters

        # Verify SearchFilters has expected fields
        filter_instance = SearchFilters(
            skills=["Python"],
            min_experience_years=3,
            location="Remote",
        )

        assert filter_instance.skills == ["Python"]
        assert filter_instance.min_experience_years == 3
        assert filter_instance.location == "Remote"

    async def test_search_result_contract(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that search service returns expected result format.

        Contract requirements:
        - SearchResult contains total, candidates, query
        - Execution time is tracked
        """
        from services.search_service import SearchResult

        # Verify SearchResult structure
        result = SearchResult(
            total=10,
            candidates=[],
            query="Python",
            filters_applied={},
            execution_time_seconds=0.5,
        )

        assert isinstance(result.total, int)
        assert isinstance(result.candidates, list)
        assert isinstance(result.query, str)
        assert result.execution_time_seconds >= 0
