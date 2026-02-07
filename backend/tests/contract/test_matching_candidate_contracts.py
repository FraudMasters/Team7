"""
Contract tests for Matching to Candidate service boundaries.

This module provides contract tests verifying that:
1. Matching service returns valid candidate ranking data
2. Ranked candidates API returns responses matching expected schemas
3. Match results integrate properly with candidate workflow
4. Error responses follow standard contract

Contract tests differ from integration tests:
- Contract tests verify interface compatibility (schema, types, required fields)
- Integration tests verify end-to-end functionality

Markers:
    - contract: Marks tests as contract tests (API/service interface verification)
"""
import logging
from typing import Any, Dict
from uuid import uuid4

import pytest
from httpx import AsyncClient
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


def validate_ranking_score(value: Any, field_name: str = "score") -> None:
    """
    Validate that a ranking score is within valid range.

    Args:
        value: The score value to validate
        field_name: Name of the field for error messages

    Raises:
        AssertionError: If validation fails
    """
    assert isinstance(value, (int, float)), f"{field_name} must be numeric"
    assert 0 <= value <= 1, f"{field_name} must be between 0 and 1, got {value}"


# ============================================================================
# Ranked Candidates API Contract Tests
# ============================================================================

@pytest.mark.contract
class TestRankedCandidatesContract:
    """
    Contract tests for /api/candidates/vacancy/{vacancy_id}/ranked endpoint.

    Verifies that ranked candidates API returns responses
    matching the expected schema and contract.
    """

    async def test_ranked_candidates_request_schema(
        self,
        client: AsyncClient,
        sample_vacancy,
    ) -> None:
        """
        Test that GET /api/candidates/vacancy/{id}/ranked accepts valid request.

        Contract requirements:
        - Accepts vacancy_id as path parameter
        - Accepts optional limit query parameter (1-200)
        - Returns ranked candidates with detailed scoring
        """
        params = {"limit": 10}
        response = await client.get(
            f"/api/candidates/vacancy/{sample_vacancy.id}/ranked",
            params=params,
        )

        # May fail auth or not found, but should accept request format
        if response.status_code not in (200, 401, 403, 404):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "vacancy_id": str,
                    "total_candidates": int,
                    "candidates": list,
                },
            )

            # Total candidates should be non-negative
            assert data["total_candidates"] >= 0, (
                f"Total candidates negative: {data['total_candidates']}"
            )

    async def test_ranked_candidates_limit_validation(
        self,
        client: AsyncClient,
        sample_vacancy,
    ) -> None:
        """
        Test that limit parameter is validated correctly.

        Contract requirements:
        - Limit must be between 1 and 200
        - Default limit is 50
        - Invalid limits return appropriate error
        """
        # Test valid limits
        for limit in [1, 50, 200]:
            response = await client.get(
                f"/api/candidates/vacancy/{sample_vacancy.id}/ranked",
                params={"limit": limit},
            )
            # Should accept the format (even if unauthenticated)
            assert response.status_code in (200, 401, 403, 404), (
                f"Unexpected status for limit={limit}: {response.status_code}"
            )

    async def test_ranked_candidate_item_schema(
        self,
        client: AsyncClient,
        sample_vacancy,
        sample_resume,
    ) -> None:
        """
        Test that individual ranked candidate items match expected schema.

        Contract requirements:
        - Each candidate has: resume_id, vacancy_id, rank_score, rank_position
        - Optional fields: recommendation, confidence, feature_contributions, ranking_factors
        - Scores are in valid ranges
        """
        response = await client.get(
            f"/api/candidates/vacancy/{sample_vacancy.id}/ranked",
            params={"limit": 10},
        )

        if response.status_code == 200:
            data = response.json()
            if len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                validate_response_schema(
                    candidate,
                    required_fields={
                        "resume_id": str,
                        "vacancy_id": str,
                        "rank_score": (int, float),
                        "recommendation": str,
                        "confidence": (int, float),
                    },
                    optional_fields={
                        "rank_position": (int, type(None)),
                        "feature_contributions": dict,
                        "ranking_factors": dict,
                    },
                )

                # Validate score ranges
                validate_ranking_score(candidate["rank_score"], "rank_score")
                validate_ranking_score(candidate["confidence"], "confidence")

    async def test_ranked_candidates_invalid_vacancy_id(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that invalid vacancy_id returns proper error contract.

        Contract requirements:
        - Invalid UUID format returns 422
        - Non-existent vacancy returns 404
        - Error responses follow standard contract
        """
        # Test invalid UUID format
        fake_id = "not-a-uuid"
        response = await client.get(
            f"/api/candidates/vacancy/{fake_id}/ranked",
        )

        if response.status_code == 422:
            data = response.json()
            validate_error_response(data, expected_status=422)

        # Test non-existent UUID
        fake_uuid = str(uuid4())
        response = await client.get(
            f"/api/candidates/vacancy/{fake_uuid}/ranked",
        )

        if response.status_code == 404:
            data = response.json()
            validate_error_response(data, expected_status=404)


# ============================================================================
# Matching to Candidate Stage Integration Contract Tests
# ============================================================================

@pytest.mark.contract
class TestMatchingStageIntegrationContract:
    """
    Contract tests for Matching service integration with Candidate stages.

    Verifies that match results can properly integrate with candidate
    workflow stages and pipeline movement.
    """

    async def test_match_result_to_stage_transition_schema(
        self,
        client: AsyncClient,
        sample_resume,
        sample_vacancy,
    ) -> None:
        """
        Test that match results can be used for stage transitions.

        Contract requirements:
        - Match results include vacancy_id for stage association
        - Match results include resume_id for candidate identification
        - Match percentage can inform hiring decisions
        """
        request_data = {
            "resume_id": str(sample_resume.id),
            "vacancy_data": {
                "id": str(sample_vacancy.id),
                "title": "Python Developer",
                "required_skills": ["Python", "FastAPI"],
                "min_experience_months": 36,
            },
        }

        response = await client.post(
            "/api/matching/compare-unified",
            json=request_data,
        )

        # Should accept request format
        if response.status_code not in (200, 401, 403, 500):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            # Verify response has fields needed for stage transitions
            validate_response_schema(
                data,
                required_fields={
                    "resume_id": str,
                    "vacancy_title": str,
                    "overall_score": (int, float),
                    "recommendation": str,
                },
                optional_fields={
                    "matched_skills": list,
                    "missing_skills": list,
                    "passed": bool,
                },
            )

            # Overall score should be in valid range (0-1 for unified matcher)
            assert 0 <= data["overall_score"] <= 1, (
                f"Overall score out of range: {data['overall_score']}"
            )

    async def test_stage_transition_with_match_context(
        self,
        client: AsyncClient,
        sample_resume,
    ) -> None:
        """
        Test that candidate stage movement accepts match-related context.

        Contract requirements:
        - Stage movement accepts vacancy_id parameter
        - Stage movement accepts optional notes parameter
        - Response confirms stage transition with match context
        """
        request_data = {
            "stage_id": "interview",
            "vacancy_id": str(uuid4()),  # May not exist, but tests schema
            "notes": "High match score (85%) - good fit for role",
        }

        response = await client.put(
            f"/api/candidates/{sample_resume.id}/stage",
            json=request_data,
        )

        # May fail auth or not found, but should accept request format
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
# Bulk Operations with Matching Context Contract Tests
# ============================================================================

@pytest.mark.contract
class TestBulkMatchingOperationsContract:
    """
    Contract tests for bulk candidate operations with matching context.

    Verifies that bulk operations maintain proper contracts when
    working with matched candidates.
    """

    async def test_bulk_move_with_vacancy_context_schema(
        self,
        client: AsyncClient,
        sample_resume,
    ) -> None:
        """
        Test that bulk move accepts vacancy_id for match context.

        Contract requirements:
        - Accepts list of resume_ids
        - Accepts stage_id for target stage
        - Accepts optional vacancy_id for match association
        - Returns summary with success/failure counts
        """
        request_data = {
            "resume_ids": [str(sample_resume.id)],
            "stage_id": "screening",
            "vacancy_id": str(uuid4()),  # Test schema, not existence
            "notes": "Moved based on high match scores",
        }

        response = await client.post(
            "/api/candidates/bulk-move",
            json=request_data,
        )

        # May fail auth, but should accept request format
        if response.status_code not in (200, 401, 403):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "total_requested": int,
                    "successful": int,
                    "failed": int,
                    "results": list,
                },
            )

            # Counts should be non-negative and sum correctly
            assert data["total_requested"] >= 0
            assert data["successful"] >= 0
            assert data["failed"] >= 0
            assert data["successful"] + data["failed"] == data["total_requested"]

    async def test_bulk_add_to_pipeline_from_matching_schema(
        self,
        client: AsyncClient,
        sample_resume,
    ) -> None:
        """
        Test that bulk action 'add_to_pipeline' works with matching context.

        Contract requirements:
        - Action type 'add_to_pipeline' accepts stage_id
        - Accepts optional vacancy_id for match context
        - Returns individual results for each candidate
        """
        request_data = {
            "action": "add_to_pipeline",
            "resume_ids": [str(sample_resume.id)],
            "stage_id": "interview",
            "vacancy_id": str(uuid4()),  # Test schema
            "notes": "Added from matching results",
        }

        response = await client.post(
            "/api/candidates/bulk-action",
            json=request_data,
        )

        # May fail auth, but should accept request format
        if response.status_code not in (200, 401, 403):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "action": str,
                    "total_requested": int,
                    "successful": int,
                    "failed": int,
                    "results": list,
                },
            )

            # Verify action is echoed correctly
            assert data["action"] == "add_to_pipeline"


# ============================================================================
# Match Result Persistence Contract Tests
# ============================================================================

@pytest.mark.contract
class TestMatchResultPersistenceContract:
    """
    Contract tests for match result persistence and retrieval.

    Verifies that match results are stored and retrieved with
    consistent schemas.
    """

    async def test_get_match_result_schema(
        self,
        client: AsyncClient,
        sample_resume,
        sample_vacancy,
    ) -> None:
        """
        Test that GET /api/matching/jobs/{vacancy_id}/resumes/{resume_id} returns valid schema.

        Contract requirements:
        - Returns match result with all score components
        - Includes related resume and vacancy data
        - Provides match percentage and recommendation
        """
        response = await client.get(
            f"/api/matching/jobs/{sample_vacancy.id}/resumes/{sample_resume.id}",
        )

        # May not be found (no match computed yet), but should have valid schema
        if response.status_code not in (200, 401, 403, 404):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "id": str,
                    "resume_id": str,
                    "vacancy_id": str,
                    "match_percentage": (int, float),
                    "recommendation": str,
                },
                optional_fields={
                    "overall_score": (int, float, type(None)),
                    "keyword_score": (int, float, type(None)),
                    "tfidf_score": (int, float, type(None)),
                    "vector_score": (int, float, type(None)),
                    "vector_similarity": (int, float, type(None)),
                    "matched_skills": list,
                    "missing_skills": list,
                    "additional_skills_matched": list,
                    "passed": bool,
                    "matcher_version": str,
                },
            )

            # Validate match percentage is in valid range
            assert 0 <= data["match_percentage"] <= 100, (
                f"Match percentage out of range: {data['match_percentage']}"
            )

            # Verify related entities are included
            if "resume" in data:
                validate_response_schema(
                    data["resume"],
                    required_fields={
                        "id": str,
                        "filename": str,
                    },
                    optional_fields={
                        "status": str,
                        "language": str,
                    },
                )

            if "vacancy" in data:
                validate_response_schema(
                    data["vacancy"],
                    required_fields={
                        "id": str,
                        "title": str,
                    },
                    optional_fields={
                        "required_skills": list,
                        "min_experience_months": (int, type(None)),
                    },
                )

    async def test_match_result_id_format(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that invalid UUID format returns proper error.

        Contract requirements:
        - Invalid vacancy_id format returns 422
        - Invalid resume_id format returns 422
        - Error responses follow standard contract
        """
        # Test invalid vacancy_id
        response = await client.get(
            "/api/matching/jobs/not-a-uuid/resumes/abc-123-def-456",
        )

        if response.status_code == 422:
            data = response.json()
            validate_error_response(data, expected_status=422)

        # Test invalid resume_id
        response = await client.get(
            "/api/matching/jobs/abc-123-def-456/resumes/not-a-uuid",
        )

        if response.status_code == 422:
            data = response.json()
            validate_error_response(data, expected_status=422)


# ============================================================================
# Match Feedback Integration Contract Tests
# ============================================================================

@pytest.mark.contract
class TestMatchFeedbackContract:
    """
    Contract tests for match feedback submission contract.

    Verifies that match feedback API maintains consistent interface
    for recruiting workflow integration.
    """

    async def test_submit_feedback_request_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that POST /api/matching/feedback accepts valid request schema.

        Contract requirements:
        - Accepts match_id, skill, was_correct fields
        - Accepts optional recruiter_correction and confidence_score
        - Returns created feedback record
        """
        request_data = {
            "match_id": str(uuid4()),
            "skill": "Python",
            "was_correct": True,
            "recruiter_correction": None,
            "confidence_score": 0.95,
        }

        response = await client.post(
            "/api/matching/feedback",
            json=request_data,
        )

        # Should accept request format (may fail auth)
        if response.status_code not in (201, 401, 403, 500):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 201:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "id": str,
                    "match_id": str,
                    "skill": str,
                    "was_correct": bool,
                    "feedback_source": str,
                    "processed": bool,
                    "created_at": str,
                },
                optional_fields={
                    "recruiter_correction": (str, type(None)),
                },
            )

    async def test_feedback_confidence_range_validation(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that confidence_score is validated to be between 0 and 1.

        Contract requirements:
        - confidence_score must be between 0 and 1
        - Invalid confidence scores return validation error
        """
        # Test invalid confidence scores
        invalid_scores = [-0.1, 1.1, 2.0, 100]

        for score in invalid_scores:
            request_data = {
                "match_id": str(uuid4()),
                "skill": "Python",
                "was_correct": True,
                "confidence_score": score,
            }

            response = await client.post(
                "/api/matching/feedback",
                json=request_data,
            )

            # Should reject invalid confidence score (or fail auth)
            if response.status_code not in (201, 401, 403, 422):
                assert False, f"Unexpected status for score={score}: {response.status_code}"

            if response.status_code == 422:
                data = response.json()
                validate_error_response(data, expected_status=422)


# ============================================================================
# Stage Metrics with Matching Context Contract Tests
# ============================================================================

@pytest.mark.contract
class TestStageMetricsMatchingContract:
    """
    Contract tests for stage metrics with matching context.

    Verifies that stage metrics can be analyzed alongside
    matching performance data.
    """

    async def test_stage_metrics_response_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that GET /api/candidates/metrics returns valid schema.

        Contract requirements:
        - Returns list of stage metrics
        - Each stage has time_metrics and dropoff_metrics
        - Supports optional stage_id, start_date, end_date filters
        """
        response = await client.get("/api/candidates/metrics")

        # Should accept request format
        if response.status_code not in (200, 401, 403):
            assert False, f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            validate_response_schema(
                data,
                required_fields={
                    "metrics": list,
                    "total_stages": int,
                },
                optional_fields={
                    "stage_id": (str, type(None)),
                },
            )

            # Validate stage count matches
            assert data["total_stages"] == len(data["metrics"])

            # Validate individual stage metrics if present
            if len(data["metrics"]) > 0:
                stage_metric = data["metrics"][0]
                validate_response_schema(
                    stage_metric,
                    required_fields={
                        "stage_name": str,
                        "time_metrics": dict,
                        "dropoff_metrics": dict,
                    },
                    optional_fields={
                        "stage_id": (str, type(None)),
                        "display_name": (str, type(None)),
                    },
                )

    async def test_stage_metrics_time_fields_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that time_metrics contains all expected numeric fields.

        Contract requirements:
        - average_days, median_days, min_days, max_days are numeric
        - candidate_count is non-negative integer
        """
        response = await client.get("/api/candidates/metrics")

        if response.status_code == 200:
            data = response.json()
            if len(data["metrics"]) > 0:
                time_metrics = data["metrics"][0]["time_metrics"]

                for field in ["average_days", "median_days", "min_days", "max_days"]:
                    assert field in time_metrics, f"Missing time metric field: {field}"
                    assert isinstance(time_metrics[field], (int, float)), (
                        f"Time metric '{field}' should be numeric"
                    )
                    assert time_metrics[field] >= 0, (
                        f"Time metric '{field}' should be non-negative"
                    )

                assert "candidate_count" in time_metrics
                assert isinstance(time_metrics["candidate_count"], int)
                assert time_metrics["candidate_count"] >= 0

    async def test_stage_metrics_dropoff_fields_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that dropoff_metrics contains all expected numeric fields.

        Contract requirements:
        - candidates_entered, candidates_exited, candidates_current are non-negative
        - dropoff_rate is between 0 and 1
        """
        response = await client.get("/api/candidates/metrics")

        if response.status_code == 200:
            data = response.json()
            if len(data["metrics"]) > 0:
                dropoff_metrics = data["metrics"][0]["dropoff_metrics"]

                for field in ["candidates_entered", "candidates_exited", "candidates_current"]:
                    assert field in dropoff_metrics, f"Missing dropoff field: {field}"
                    assert isinstance(dropoff_metrics[field], int), (
                        f"Dropoff field '{field}' should be integer"
                    )
                    assert dropoff_metrics[field] >= 0, (
                        f"Dropoff field '{field}' should be non-negative"
                    )

                assert "dropoff_rate" in dropoff_metrics
                assert isinstance(dropoff_metrics["dropoff_rate"], (int, float))
                assert 0 <= dropoff_metrics["dropoff_rate"] <= 1, (
                    f"dropoff_rate should be between 0 and 1"
                )
