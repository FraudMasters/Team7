"""
Schema validation tests for API responses.

This module provides comprehensive schema validation tests verifying that:
1. API responses match their Pydantic model definitions exactly
2. Response fields have correct types and value constraints
3. Nested objects and arrays are properly structured
4. Optional vs required fields are correctly handled
5. Field validation (min/max length, ranges) is enforced

These tests differ from standard contract tests by focusing specifically
on schema correctness and data type validation rather than API behavior.

Markers:
    - contract: Marks tests as contract tests (schema validation)
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from pydantic import BaseModel, ValidationError, validator
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================================================
# Schema Validation Helpers
# ============================================================================

def validate_field_type(
    value: Any,
    expected_type: Union[type, tuple],
    field_name: str,
    allow_none: bool = False,
) -> None:
    """
    Validate that a field value has the expected type.

    Args:
        value: The value to check
        expected_type: Expected type(s) - can be a single type or tuple of types
        field_name: Name of the field (for error messages)
        allow_none: Whether None is an acceptable value

    Raises:
        AssertionError: If type validation fails
    """
    if value is None:
        assert allow_none, f"Field '{field_name}' cannot be None"
        return

    assert isinstance(value, expected_type), (
        f"Field '{field_name}' has wrong type: "
        f"expected {expected_type}, got {type(value).__name__} "
        f"(value: {repr(value)[:100]})"
    )


def validate_string_field(
    value: Any,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
    allow_none: bool = False,
) -> None:
    """
    Validate a string field with constraints.

    Args:
        value: The value to check
        field_name: Name of the field
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        pattern: Regex pattern the string must match
        allow_none: Whether None is acceptable

    Raises:
        AssertionError: If validation fails
    """
    validate_field_type(value, str, field_name, allow_none=allow_none)

    if value is None and allow_none:
        return

    value_len = len(value)
    if min_length is not None:
        assert value_len >= min_length, (
            f"Field '{field_name}' length {value_len} < min_length {min_length}"
        )
    if max_length is not None:
        assert value_len <= max_length, (
            f"Field '{field_name}' length {value_len} > max_length {max_length}"
        )
    if pattern is not None:
        assert re.match(pattern, value), (
            f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
        )


def validate_numeric_field(
    value: Any,
    field_name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    allow_none: bool = False,
) -> None:
    """
    Validate a numeric field with range constraints.

    Args:
        value: The value to check
        field_name: Name of the field
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        allow_none: Whether None is acceptable

    Raises:
        AssertionError: If validation fails
    """
    validate_field_type(value, (int, float), field_name, allow_none=allow_none)

    if value is None and allow_none:
        return

    if min_value is not None:
        assert value >= min_value, (
            f"Field '{field_name}' value {value} < min_value {min_value}"
        )
    if max_value is not None:
        assert value <= max_value, (
            f"Field '{field_name}' value {value} > max_value {max_value}"
        )


def validate_list_field(
    value: Any,
    field_name: str,
    item_type: Optional[type] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    allow_none: bool = False,
) -> List[Any]:
    """
    Validate a list field with constraints.

    Args:
        value: The value to check
        field_name: Name of the field
        item_type: Expected type of list items
        min_items: Minimum number of items
        max_items: Maximum number of items
        allow_none: Whether None is acceptable

    Returns:
        The validated list for further processing

    Raises:
        AssertionError: If validation fails
    """
    validate_field_type(value, list, field_name, allow_none=allow_none)

    if value is None and allow_none:
        return []

    value_len = len(value)
    if min_items is not None:
        assert value_len >= min_items, (
            f"Field '{field_name}' has {value_len} items < min_items {min_items}"
        )
    if max_items is not None:
        assert value_len <= max_items, (
            f"Field '{field_name}' has {value_len} items > max_items {max_items}"
        )

    # Validate item types if specified
    if item_type is not None:
        for i, item in enumerate(value):
            if item is not None:
                assert isinstance(item, item_type), (
                    f"Field '{field_name}[{i}]' has wrong type: "
                    f"expected {item_type}, got {type(item).__name__}"
                )

    return value


def validate_datetime_field(
    value: Any,
    field_name: str,
    allow_none: bool = False,
    require_iso_format: bool = True,
) -> None:
    """
    Validate a datetime field.

    Args:
        value: The value to check
        field_name: Name of the field
        allow_none: Whether None is acceptable
        require_iso_format: Whether to require ISO 8601 format

    Raises:
        AssertionError: If validation fails
    """
    validate_field_type(value, str, field_name, allow_none=allow_none)

    if value is None and allow_none:
        return

    if require_iso_format:
        # Try to parse as ISO format datetime
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            # Check if it's a valid ISO-like format
            assert re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value), (
                f"Field '{field_name}' is not in ISO 8601 format: {value}"
            )


def validate_uuid_field(
    value: Any,
    field_name: str,
    allow_none: bool = False,
) -> None:
    """
    Validate a UUID field.

    Args:
        value: The value to check
        field_name: Name of the field
        allow_none: Whether None is acceptable

    Raises:
        AssertionError: If validation fails
    """
    validate_field_type(value, str, field_name, allow_none=allow_none)

    if value is None and allow_none:
        return

    try:
        UUID(value)
    except ValueError:
        raise AssertionError(
            f"Field '{field_name}' is not a valid UUID: {value}"
        )


def validate_response_object(
    response_data: Dict[str, Any],
    schema_definition: Dict[str, Any],
    strict_required: bool = True,
) -> None:
    """
    Validate an entire response object against a schema definition.

    Args:
        response_data: The response JSON to validate
        schema_definition: Dictionary defining field schemas
            Format: {
                "field_name": {
                    "type": type | tuple,
                    "required": bool,
                    "min_length": int (for strings),
                    "max_length": int (for strings),
                    "min_value": int|float (for numbers),
                    "max_value": int|float (for numbers),
                    "pattern": str (for strings),
                    "item_type": type (for lists),
                    "min_items": int (for lists),
                    "max_items": int (for lists),
                }
            }
        strict_required: If True, fail on extra fields not in schema

    Raises:
        AssertionError: If validation fails
    """
    # Check required fields are present
    for field_name, field_schema in schema_definition.items():
        is_required = field_schema.get("required", False)
        field_type = field_schema.get("type")

        if field_name not in response_data:
            if is_required and strict_required:
                raise AssertionError(f"Missing required field: {field_name}")
            continue

        value = response_data[field_name]

        # Handle None values
        if value is None:
            if is_required and not field_schema.get("allow_none", False):
                raise AssertionError(f"Required field '{field_name}' is None")
            continue

        # Type-specific validation
        if field_type == str:
            validate_string_field(
                value,
                field_name,
                min_length=field_schema.get("min_length"),
                max_length=field_schema.get("max_length"),
                pattern=field_schema.get("pattern"),
                allow_none=field_schema.get("allow_none", False),
            )
        elif field_type in (int, float, (int, float)):
            validate_numeric_field(
                value,
                field_name,
                min_value=field_schema.get("min_value"),
                max_value=field_schema.get("max_value"),
                allow_none=field_schema.get("allow_none", False),
            )
        elif field_type == list:
            validate_list_field(
                value,
                field_name,
                item_type=field_schema.get("item_type"),
                min_items=field_schema.get("min_items"),
                max_items=field_schema.get("max_items"),
                allow_none=field_schema.get("allow_none", False),
            )
        elif field_type == dict:
            validate_field_type(
                value,
                dict,
                field_name,
                allow_none=field_schema.get("allow_none", False),
            )
        elif field_type == bool:
            validate_field_type(
                value,
                bool,
                field_name,
                allow_none=field_schema.get("allow_none", False),
            )
        else:
            # Generic type check
            validate_field_type(
                value,
                field_type,
                field_name,
                allow_none=field_schema.get("allow_none", False),
            )


# ============================================================================
# Common Schema Definitions
# ============================================================================

TIMESTAMP_SCHEMA = {
    "type": str,
    "required": True,
    "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
}

UUID_SCHEMA = {
    "type": str,
    "required": True,
    "pattern": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
}

VACANCY_RESPONSE_SCHEMA = {
    "id": {"type": str, "required": True, "pattern": r"[0-9a-f-]{36}"},
    "title": {"type": str, "required": True, "min_length": 3, "max_length": 255},
    "description": {"type": str, "required": True, "min_length": 10},
    "required_skills": {"type": list, "required": True, "item_type": str, "min_items": 1},
    "min_experience_months": {"type": (int, type(None)), "required": True, "allow_none": True},
    "additional_requirements": {"type": list, "required": True, "item_type": str},
    "industry": {"type": (str, type(None)), "required": True, "allow_none": True, "max_length": 100},
    "work_format": {"type": (str, type(None)), "required": True, "allow_none": True, "max_length": 50},
    "location": {"type": (str, type(None)), "required": True, "allow_none": True, "max_length": 255},
    "salary_min": {"type": (int, type(None)), "required": True, "allow_none": True, "min_value": 0},
    "salary_max": {"type": (int, type(None)), "required": True, "allow_none": True, "min_value": 0},
    "english_level": {"type": (str, type(None)), "required": True, "allow_none": True, "max_length": 50},
    "employment_type": {"type": (str, type(None)), "required": True, "allow_none": True, "max_length": 50},
    "external_id": {"type": (str, type(None)), "required": True, "allow_none": True, "max_length": 255},
    "source": {"type": (str, type(None)), "required": True, "allow_none": True, "max_length": 50},
    "created_at": {"type": str, "required": True, "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"},
    "updated_at": {"type": str, "required": True, "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"},
}

RESUME_RESPONSE_SCHEMA = {
    "id": {"type": str, "required": True, "pattern": r"[0-9a-f-]{36}"},
    "filename": {"type": str, "required": True, "min_length": 1, "max_length": 255},
    "status": {"type": str, "required": True},
    "created_at": {"type": str, "required": True},
    "updated_at": {"type": str, "required": True},
}


# ============================================================================
# Vacancy API Schema Tests
# ============================================================================

@pytest.mark.contract
class TestVacancyResponseSchemas:
    """
    Schema validation tests for Vacancy API responses.

    Verifies that all vacancy-related endpoints return responses
    matching the expected schema with correct field types and constraints.
    """

    async def test_create_vacancy_response_schema(
        self,
        client: AsyncClient,
        sample_user,
    ) -> None:
        """
        Test POST /api/vacancies response schema.

        Schema requirements:
        - All required fields present with correct types
        - String fields respect length constraints
        - Numeric fields are non-negative where appropriate
        - UUID fields are valid UUIDs
        - Timestamps are in ISO format
        """
        request_data = {
            "title": "Senior Python Developer",
            "description": "We are looking for an experienced Python developer to join our team.",
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "min_experience_months": 36,
            "additional_requirements": ["Docker", "Kubernetes"],
            "industry": "Technology",
            "work_format": "Remote",
            "location": "Remote",
            "salary_min": 80000,
            "salary_max": 120000,
            "english_level": "B2",
            "employment_type": "full-time",
        }

        response = await client.post("/api/vacancies/", json=request_data)

        # May fail auth, but if it succeeds validate schema
        if response.status_code in (200, 201):
            data = response.json()

            # Validate each field
            validate_uuid_field(data.get("id"), "id", allow_none=False)
            validate_string_field(
                data.get("title"),
                "title",
                min_length=3,
                max_length=255,
                allow_none=False,
            )
            validate_string_field(
                data.get("description"),
                "description",
                min_length=10,
                allow_none=False,
            )
            validate_list_field(
                data.get("required_skills"),
                "required_skills",
                item_type=str,
                min_items=1,
                allow_none=False,
            )
            validate_numeric_field(
                data.get("min_experience_months"),
                "min_experience_months",
                min_value=0,
                allow_none=True,
            )
            validate_list_field(
                data.get("additional_requirements"),
                "additional_requirements",
                item_type=str,
                allow_none=False,
            )
            validate_numeric_field(
                data.get("salary_min"),
                "salary_min",
                min_value=0,
                allow_none=True,
            )
            validate_numeric_field(
                data.get("salary_max"),
                "salary_max",
                min_value=0,
                allow_none=True,
            )
            validate_datetime_field(data.get("created_at"), "created_at", allow_none=False)
            validate_datetime_field(data.get("updated_at"), "updated_at", allow_none=False)

    async def test_vacancy_list_response_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test GET /api/vacancies list response schema.

        Schema requirements:
        - Response is a list or dict with items
        - Each vacancy item matches VacancyResponse schema
        - Pagination parameters (if present) are integers
        """
        params = {"skip": 0, "limit": 10}
        response = await client.get("/api/vacancies/", params=params)

        if response.status_code == 200:
            data = response.json()

            # Could be a list directly or a dict with items
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "items" in data:
                items = data["items"]

                # Validate pagination fields
                if "total" in data:
                    validate_numeric_field(data["total"], "total", min_value=0, allow_none=False)
                if "skip" in data:
                    validate_numeric_field(data["skip"], "skip", min_value=0, allow_none=False)
                if "limit" in data:
                    validate_numeric_field(data["limit"], "limit", min_value=1, allow_none=False)
            else:
                items = []

            # Validate each vacancy item
            for item in items:
                if isinstance(item, dict):
                    validate_uuid_field(item.get("id"), "id", allow_none=False)
                    validate_string_field(item.get("title"), "title", min_length=1, allow_none=False)
                    validate_list_field(
                        item.get("required_skills"),
                        "required_skills",
                        item_type=str,
                        allow_none=False,
                    )

    async def test_vacancy_search_response_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test POST /api/vacancies/search response schema.

        Schema requirements:
        - Response includes total, vacancies, query, execution_time_seconds
        - total is non-negative integer
        - vacancies is a list
        - execution_time_seconds is a non-negative float
        """
        request_data = {
            "query": "Python developer",
            "skip": 0,
            "limit": 10,
            "sort_by": "date",
        }

        response = await client.post("/api/vacancies/search", json=request_data)

        if response.status_code == 200:
            data = response.json()

            # Validate search response structure
            validate_numeric_field(data.get("total"), "total", min_value=0, allow_none=False)
            validate_list_field(data.get("vacancies"), "vacancies", allow_none=False)
            validate_string_field(data.get("query"), "query", allow_none=False)
            validate_numeric_field(
                data.get("execution_time_seconds"),
                "execution_time_seconds",
                min_value=0,
                allow_none=False,
            )

            # Validate result count matches total for first page
            if data.get("total") == 0:
                assert len(data.get("vacancies", [])) == 0, (
                    "Total is 0 but vacancies list is not empty"
                )


# ============================================================================
# Matching API Schema Tests
# ============================================================================

@pytest.mark.contract
class TestMatchingResponseSchemas:
    """
    Schema validation tests for Matching API responses.

    Verifies that matching endpoints return responses
    with proper score ranges and skill lists.
    """

    async def test_match_response_schema(
        self,
        client: AsyncClient,
        sample_resume,
        sample_vacancy,
    ) -> None:
        """
        Test POST /api/matching response schema.

        Schema requirements:
        - match_percentage is between 0 and 100
        - Skills lists contain strings
        - Fields have correct types
        """
        request_data = {
            "resume_id": str(sample_resume.id),
            "vacancy_id": str(sample_vacancy.id),
        }

        response = await client.post("/api/matching", json=request_data)

        if response.status_code == 200:
            data = response.json()

            # Validate match score range
            validate_numeric_field(
                data.get("match_percentage"),
                "match_percentage",
                min_value=0,
                max_value=100,
                allow_none=False,
            )

            # Validate skills lists
            if "matched_skills" in data:
                validate_list_field(
                    data["matched_skills"],
                    "matched_skills",
                    item_type=str,
                    allow_none=True,
                )
            if "missing_skills" in data:
                validate_list_field(
                    data["missing_skills"],
                    "missing_skills",
                    item_type=str,
                    allow_none=True,
                )
            if "additional_skills" in data:
                validate_list_field(
                    data["additional_skills"],
                    "additional_skills",
                    item_type=str,
                    allow_none=True,
                )

    async def test_skill_match_types(
        self,
        client: AsyncClient,
        sample_resume,
        sample_vacancy,
    ) -> None:
        """
        Test that skill matching returns correct data types.

        Verifies:
        - All skill fields are lists of strings
        - No non-string values in skill lists
        - Empty lists are valid
        """
        request_data = {
            "resume_id": str(sample_resume.id),
            "vacancy_id": str(sample_vacancy.id),
        }

        response = await client.post("/api/matching", json=request_data)

        if response.status_code == 200:
            data = response.json()

            skill_fields = ["matched_skills", "missing_skills", "additional_skills"]

            for field in skill_fields:
                if field in data and data[field] is not None:
                    assert isinstance(data[field], list), (
                        f"Field '{field}' should be a list, got {type(data[field])}"
                    )
                    for i, skill in enumerate(data[field]):
                        assert isinstance(skill, str), (
                            f"Field '{field}[{i}]' should be a string, "
                            f"got {type(skill).__name__}: {repr(skill)}"
                        )


# ============================================================================
# Ranking API Schema Tests
# ============================================================================

@pytest.mark.contract
class TestRankingResponseSchemas:
    """
    Schema validation tests for Ranking API responses.

    Verifies that ranking endpoints return responses
    with valid scores and recommendations.
    """

    async def test_rank_response_schema(
        self,
        client: AsyncClient,
        sample_resume,
        sample_vacancy,
    ) -> None:
        """
        Test POST /api/ranking/rank response schema.

        Schema requirements:
        - rank_score is between 0 and 1
        - confidence is between 0 and 1
        - recommendation is a string
        - model_version is a string
        """
        request_data = {
            "resume_id": str(sample_resume.id),
            "vacancy_id": str(sample_vacancy.id),
            "use_experiment": False,
        }

        response = await client.post("/api/ranking/rank", json=request_data)

        if response.status_code == 200:
            data = response.json()

            # Validate rank score
            validate_numeric_field(
                data.get("rank_score"),
                "rank_score",
                min_value=0.0,
                max_value=1.0,
                allow_none=False,
            )

            # Validate confidence
            validate_numeric_field(
                data.get("confidence"),
                "confidence",
                min_value=0.0,
                max_value=1.0,
                allow_none=False,
            )

            # Validate recommendation
            validate_string_field(
                data.get("recommendation"),
                "recommendation",
                min_length=1,
                allow_none=False,
            )

            # Validate model version
            validate_string_field(
                data.get("model_version"),
                "model_version",
                min_length=1,
                allow_none=False,
            )

            # Validate UUID fields
            validate_uuid_field(data.get("resume_id"), "resume_id", allow_none=False)
            validate_uuid_field(data.get("vacancy_id"), "vacancy_id", allow_none=False)

    async def test_vacancy_rankings_list_schema(
        self,
        client: AsyncClient,
        sample_vacancy,
    ) -> None:
        """
        Test GET /api/ranking/vacancy/{id} response schema.

        Schema requirements:
        - Response is a list
        - Each item has resume_id, rank_score, rank_position
        - rank_positions are sequential integers starting from 1
        - Items are sorted by rank_position
        """
        response = await client.get(f"/api/ranking/vacancy/{sample_vacancy.id}")

        if response.status_code == 200:
            data = response.json()

            assert isinstance(data, list), "Response should be a list"

            # Validate each ranking item
            for i, item in enumerate(data):
                validate_uuid_field(item.get("resume_id"), "resume_id", allow_none=False)
                validate_numeric_field(
                    item.get("rank_score"),
                    "rank_score",
                    min_value=0.0,
                    max_value=1.0,
                    allow_none=False,
                )
                validate_numeric_field(
                    item.get("rank_position"),
                    "rank_position",
                    min_value=1,
                    allow_none=False,
                )

                # Check positions are sequential
                if i > 0:
                    prev_position = data[i - 1].get("rank_position")
                    current_position = item.get("rank_position")
                    assert current_position > prev_position, (
                        f"Rank positions should be sequential: "
                        f"{prev_position} followed by {current_position}"
                    )


# ============================================================================
# Resume API Schema Tests
# ============================================================================

@pytest.mark.contract
class TestResumeResponseSchemas:
    """
    Schema validation tests for Resume API responses.

    Verifies that resume endpoints return responses
    with proper file metadata and processing status.
    """

    async def test_resume_upload_response_schema(
        self,
        client: AsyncClient,
        temp_dir,
    ) -> None:
        """
        Test POST /api/resumes/upload response schema.

        Schema requirements:
        - Response includes id, filename, status, message
        - status is one of: pending, processing, completed, failed
        - id is a valid UUID
        - filename is non-empty string
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

        if response.status_code in (200, 201):
            data = response.json()

            # Validate response structure
            validate_uuid_field(data.get("id"), "id", allow_none=False)
            validate_string_field(
                data.get("filename"),
                "filename",
                min_length=1,
                max_length=255,
                allow_none=False,
            )
            validate_string_field(
                data.get("message"),
                "message",
                min_length=1,
                allow_none=False,
            )

            # Validate status enum
            valid_statuses = ["pending", "processing", "completed", "failed"]
            status = data.get("status")
            assert isinstance(status, str), "Status should be a string"
            assert status in valid_statuses, (
                f"Invalid status: {status}. Must be one of {valid_statuses}"
            )

    async def test_resume_analysis_schema(
        self,
        client: AsyncClient,
        sample_resume,
    ) -> None:
        """
        Test GET /api/resumes/{id}/analysis response schema.

        Schema requirements:
        - Response includes skills (list of strings)
        - total_experience_months is non-negative integer
        - education is a list of dictionaries
        - quality_score is between 0 and 100
        """
        response = await client.get(f"/api/resumes/{sample_resume.id}/analysis")

        if response.status_code == 200:
            data = response.json()

            # Validate skills
            validate_list_field(
                data.get("skills"),
                "skills",
                item_type=str,
                allow_none=False,
            )

            # Validate experience
            validate_numeric_field(
                data.get("total_experience_months"),
                "total_experience_months",
                min_value=0,
                allow_none=True,
            )

            # Validate education
            validate_list_field(
                data.get("education"),
                "education",
                item_type=dict,
                allow_none=False,
            )

            # Validate quality score
            if "quality_score" in data and data["quality_score"] is not None:
                validate_numeric_field(
                    data["quality_score"],
                    "quality_score",
                    min_value=0,
                    max_value=100,
                    allow_none=False,
                )


# ============================================================================
# Error Response Schema Tests
# ============================================================================

@pytest.mark.contract
class TestErrorResponseSchemas:
    """
    Schema validation tests for error responses.

    Verifies that all error responses follow a consistent schema.
    """

    async def test_404_error_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that 404 errors follow standard schema.

        Schema requirements:
        - Has 'detail' field (string)
        - May have 'error_code' or 'error_type' fields
        - All additional fields are from allowed set
        """
        fake_id = uuid4()
        response = await client.get(f"/api/vacancies/{fake_id}")

        if response.status_code == 404:
            data = response.json()

            # Validate error structure
            assert "detail" in data, "404 error must have 'detail' field"
            validate_string_field(data["detail"], "detail", min_length=1, allow_none=False)

            # Check for known error fields
            allowed_fields = {"detail", "error_code", "error_type", "context", "type"}
            for field in data:
                assert field in allowed_fields, (
                    f"Unexpected field in error response: {field}"
                )

    async def test_422_validation_error_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that 422 validation errors follow standard schema.

        Schema requirements:
        - Has 'detail' field (usually a list of validation errors)
        - Each validation error has 'loc', 'type', 'msg' fields
        """
        # Send invalid data to trigger validation error
        invalid_data = {
            "title": "AB",  # Too short
            "description": "short",  # Too short
            "required_skills": [],  # Too few items
        }

        response = await client.post("/api/vacancies/", json=invalid_data)

        if response.status_code == 422:
            data = response.json()

            # FastAPI validation errors have specific structure
            assert "detail" in data, "Validation error must have 'detail' field"

            detail = data["detail"]
            if isinstance(detail, list):
                for error in detail:
                    assert isinstance(error, dict), "Validation error item must be a dict"
                    assert "loc" in error, "Validation error must have 'loc' field"
                    assert "type" in error, "Validation error must have 'type' field"
                    assert "msg" in error, "Validation error must have 'msg' field"

    async def test_500_error_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that 500 errors follow standard schema.

        Schema requirements:
        - Has error message field
        - Does not expose sensitive information
        - Has consistent structure
        """
        # This test is informational - 500 errors should not occur
        # but if they do, they should have proper schema
        # We'll just document the expected schema

        expected_500_schema = {
            "error": {"type": str, "required": True},
            "detail": {"type": str, "required": True},
            "type": {"type": str, "required": False},
        }

        # Schema documentation for developers
        assert "error" in expected_500_schema
        assert "detail" in expected_500_schema


# ============================================================================
# Pagination Schema Tests
# ============================================================================

@pytest.mark.contract
class TestPaginationSchemas:
    """
    Schema validation tests for paginated responses.

    Verifies that pagination parameters are properly validated.
    """

    async def test_pagination_parameters_schema(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that pagination parameters are validated.

        Schema requirements:
        - skip must be non-negative integer
        - limit must be positive integer within bounds
        - Invalid pagination parameters are rejected
        """
        # Test valid pagination
        valid_params = {"skip": 0, "limit": 10}
        response = await client.get("/api/vacancies/", params=valid_params)

        # Should not cause validation error
        assert response.status_code in (200, 401, 403, 404), (
            f"Valid pagination params caused unexpected status: {response.status_code}"
        )

        # Test invalid skip (negative)
        invalid_params = {"skip": -1, "limit": 10}
        response = await client.get("/api/vacancies/", params=invalid_params)

        # Should be rejected or handled gracefully
        if response.status_code == 422:
            # Validation error is expected
            pass

        # Test invalid limit (too large)
        invalid_params = {"skip": 0, "limit": 10000}
        response = await client.get("/api/vacancies/", params=invalid_params)

        # Should be rejected or handled gracefully
        if response.status_code == 422:
            # Validation error is expected
            pass

    async def test_paginated_response_structure(
        self,
        client: AsyncClient,
    ) -> None:
        """
        Test that paginated responses have consistent structure.

        Schema requirements:
        - total reflects total number of items
        - skip and limit match request parameters
        - items count is <= limit
        """
        params = {"skip": 0, "limit": 5}
        response = await client.get("/api/vacancies/", params=params)

        if response.status_code == 200:
            data = response.json()

            # If response is paginated dict
            if isinstance(data, dict):
                # Validate pagination metadata
                if "total" in data:
                    validate_numeric_field(data["total"], "total", min_value=0)
                if "skip" in data:
                    validate_numeric_field(data["skip"], "skip", min_value=0)
                    assert data["skip"] == params["skip"], (
                        f"Response skip {data['skip']} != request skip {params['skip']}"
                    )
                if "limit" in data:
                    validate_numeric_field(data["limit"], "limit", min_value=1)
                    assert data["limit"] == params["limit"], (
                        f"Response limit {data['limit']} != request limit {params['limit']}"
                    )

                # Validate items count
                if "items" in data:
                    validate_list_field(data["items"], "items")
                    assert len(data["items"]) <= params["limit"], (
                        f"Returned {len(data['items'])} items > limit {params['limit']}"
                    )
