"""
Tests for Vacancy Service.

Tests cover model validation, API endpoints, configuration,
database operations, and edge cases.
"""
import json
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from api.vacancies import (
    VacancyCreateRequest,
    VacancyUpdateRequest,
    _vacancy_to_response,
    create_vacancy,
    delete_vacancy,
    get_vacancy,
    list_vacancies,
    update_vacancy,
)
from config import Settings, get_settings
from database import _extract_table_and_operation, get_db, init_db
from main import app, lifespan
from models.base import Base, TimestampMixin, UUIDMixin
from models.vacancy import Vacancy


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_vacancy_data() -> dict:
    """Sample vacancy data for testing."""
    return {
        "title": "Senior Python Developer",
        "description": "We are looking for a senior Python developer with experience in FastAPI.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "min_experience_months": 36,
        "additional_requirements": ["Kubernetes", "Redis"],
        "industry": "Technology",
        "work_format": "remote",
        "location": "Remote",
        "salary_min": 100000,
        "salary_max": 150000,
        "english_level": "Upper Intermediate",
        "employment_type": "full-time",
    }


@pytest.fixture
def sample_vacancy() -> Vacancy:
    """Sample Vacancy model instance."""
    vacancy = Vacancy(
        title="Senior Python Developer",
        description="We are looking for a senior Python developer.",
        required_skills=["Python", "FastAPI"],
        min_experience_months=36,
        additional_requirements=["Docker"],
        industry="Technology",
        work_format="remote",
        location="Remote",
        salary_min=100000,
        salary_max=150000,
        english_level="Upper Intermediate",
        employment_type="full-time",
        external_id="ext-123",
        source="manual",
    )
    vacancy.id = uuid4()
    vacancy.created_at = datetime.now()
    vacancy.updated_at = datetime.now()
    return vacancy


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    session.scalars = Mock()
    session.scalars.all = Mock()
    session.delete = AsyncMock()
    return session


# ============================================================================
# Tests for Vacancy Model
# ============================================================================

class TestVacancyModel:
    """Tests for Vacancy model."""

    def test_vacancy_creation(self):
        """Test creating a Vacancy instance."""
        vacancy = Vacancy(
            title="Software Engineer",
            description="Job description here",
            required_skills=["Python", "SQL"],
        )
        assert vacancy.title == "Software Engineer"
        assert vacancy.description == "Job description here"
        assert vacancy.required_skills == ["Python", "SQL"]
        assert vacancy.min_experience_months is None
        assert vacancy.additional_requirements == []

    def test_vacancy_with_all_fields(self, sample_vacancy):
        """Test Vacancy with all fields populated."""
        assert sample_vacancy.title == "Senior Python Developer"
        assert sample_vacancy.min_experience_months == 36
        assert sample_vacancy.salary_min == 100000
        assert sample_vacancy.salary_max == 150000
        assert sample_vacancy.external_id == "ext-123"
        assert sample_vacancy.source == "manual"

    def test_vacancy_repr(self, sample_vacancy):
        """Test Vacancy __repr__ method."""
        repr_str = repr(sample_vacancy)
        assert "Vacancy" in repr_str
        assert str(sample_vacancy.id) in repr_str
        assert sample_vacancy.title in repr_str

    def test_vacancy_required_skills_default(self):
        """Test required_skills defaults to empty list."""
        vacancy = Vacancy(
            title="Developer",
            description="Job description",
            required_skills=[],
        )
        assert vacancy.required_skills == []

    def test_vacancy_additional_requirements_default(self):
        """Test additional_requirements defaults to empty list."""
        vacancy = Vacancy(
            title="Developer",
            description="Job description",
            required_skills=["Python"],
        )
        assert vacancy.additional_requirements == []

    def test_vacancey_nullable_fields(self):
        """Test nullable fields can be None."""
        vacancy = Vacancy(
            title="Developer",
            description="Job description",
            required_skills=["Python"],
            min_experience_months=None,
            industry=None,
            work_format=None,
            location=None,
            salary_min=None,
            salary_max=None,
            english_level=None,
            employment_type=None,
            external_id=None,
            source=None,
        )
        assert vacancy.min_experience_months is None
        assert vacancy.industry is None
        assert vacancy.work_format is None


# ============================================================================
# Tests for VacancyCreateRequest
# ============================================================================

class TestVacancyCreateRequest:
    """Tests for VacancyCreateRequest model."""

    def test_valid_create_request(self, sample_vacancy_data):
        """Test valid VacancyCreateRequest."""
        request = VacancyCreateRequest(**sample_vacancy_data)
        assert request.title == "Senior Python Developer"
        assert request.required_skills == ["Python", "FastAPI", "PostgreSQL", "Docker"]
        assert request.min_experience_months == 36

    def test_minimal_valid_request(self):
        """Test minimal valid VacancyCreateRequest."""
        request = VacancyCreateRequest(
            title="Developer",
            description="Job description",
            required_skills=["Python"],
        )
        assert request.title == "Developer"
        assert request.description == "Job description"
        assert request.required_skills == ["Python"]
        assert request.additional_requirements == []
        assert request.source == "manual"

    def test_title_too_short(self):
        """Test title less than 3 characters raises error."""
        with pytest.raises(Exception):
            VacancyCreateRequest(
                title="Dev",
                description="Job description",
                required_skills=["Python"],
            )

    def test_description_too_short(self):
        """Test description less than 10 characters raises error."""
        with pytest.raises(Exception):
            VacancyCreateRequest(
                title="Developer",
                description="Short",
                required_skills=["Python"],
            )

    def test_required_skills_cannot_be_empty(self):
        """Test required_skills must have at least one item."""
        with pytest.raises(Exception):
            VacancyCreateRequest(
                title="Developer",
                description="Job description",
                required_skills=[],
            )

    def test_negative_experience_rejected(self):
        """Test negative min_experience_months is rejected."""
        with pytest.raises(Exception):
            VacancyCreateRequest(
                title="Developer",
                description="Job description",
                required_skills=["Python"],
                min_experience_months=-1,
            )

    def test_zero_experience_accepted(self):
        """Test zero min_experience_months is accepted."""
        request = VacancyCreateRequest(
            title="Developer",
            description="Job description",
            required_skills=["Python"],
            min_experience_months=0,
        )
        assert request.min_experience_months == 0

    def test_negative_salary_rejected(self):
        """Test negative salary is rejected."""
        with pytest.raises(Exception):
            VacancyCreateRequest(
                title="Developer",
                description="Job description",
                required_skills=["Python"],
                salary_min=-1000,
            )


# ============================================================================
# Tests for VacancyUpdateRequest
# ============================================================================

class TestVacancyUpdateRequest:
    """Tests for VacancyUpdateRequest model."""

    def test_valid_update_request(self):
        """Test valid VacancyUpdateRequest."""
        request = VacancyUpdateRequest(
            title="Updated Title",
            min_experience_months=48,
        )
        assert request.title == "Updated Title"
        assert request.min_experience_months == 48

    def test_all_fields_optional(self):
        """Test all fields are optional."""
        request = VacancyUpdateRequest()
        assert request.title is None
        assert request.description is None

    def test_partial_update(self):
        """Test partial update with only some fields."""
        request = VacancyUpdateRequest(
            salary_min=120000,
            salary_max=180000,
        )
        assert request.salary_min == 120000
        assert request.salary_max == 180000
        assert request.title is None


# ============================================================================
# Tests for _vacancy_to_response Helper
# ============================================================================

class TestVacancyToResponse:
    """Tests for _vacancy_to_response helper function."""

    def test_vacancy_to_response(self, sample_vacancy):
        """Test converting Vacancy to response dict."""
        response = _vacancy_to_response(sample_vacancy)
        assert isinstance(response, dict)
        assert response["id"] == str(sample_vacancy.id)
        assert response["title"] == sample_vacancy.title
        assert response["description"] == sample_vacancy.description
        assert response["required_skills"] == sample_vacancy.required_skills
        assert response["min_experience_months"] == sample_vacancy.min_experience_months

    def test_response_includes_timestamps(self, sample_vacancy):
        """Test response includes ISO formatted timestamps."""
        response = _vacancy_to_response(sample_vacancy)
        assert "created_at" in response
        assert "updated_at" in response
        assert response["created_at"] == sample_vacancy.created_at.isoformat()
        assert response["updated_at"] == sample_vacancy.updated_at.isoformat()

    def test_response_with_null_timestamps(self):
        """Test response handles null timestamps."""
        vacancy = Vacancy(
            title="Developer",
            description="Description",
            required_skills=["Python"],
        )
        vacancy.created_at = None
        vacancy.updated_at = None
        response = _vacancy_to_response(vacancy)
        assert response["created_at"] is None
        assert response["updated_at"] is None

    def test_response_with_all_fields(self, sample_vacancy):
        """Test response includes all expected fields."""
        response = _vacancy_to_response(sample_vacancy)
        expected_fields = [
            "id", "title", "description", "required_skills",
            "min_experience_months", "additional_requirements",
            "industry", "work_format", "location",
            "salary_min", "salary_max", "english_level",
            "employment_type", "external_id", "source",
            "created_at", "updated_at",
        ]
        for field in expected_fields:
            assert field in response


# ============================================================================
# Tests for create_vacancy Endpoint
# ============================================================================

class TestCreateVacancy:
    """Tests for create_vacancy endpoint."""

    @pytest.mark.asyncio
    async def test_create_vacancy_success(self, sample_vacancy_data, mock_db_session):
        """Test successful vacancy creation."""
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Mock the refresh to set id and timestamps
        new_vacancy = Vacancy(**sample_vacancy_data)
        new_vacancy.id = uuid4()
        new_vacancy.created_at = datetime.now()
        new_vacancy.updated_at = datetime.now()
        mock_db_session.refresh.side_effect = lambda v: setattr(v, 'id', new_vacancy.id) or setattr(v, 'created_at', datetime.now()) or setattr(v, 'updated_at', datetime.now())

        request = Mock(spec=VacancyCreateRequest)
        request.title = sample_vacancy_data["title"]
        request.description = sample_vacancy_data["description"]
        request.required_skills = sample_vacancy_data["required_skills"]
        request.min_experience_months = sample_vacancy_data["min_experience_months"]
        request.additional_requirements = sample_vacancy_data.get("additional_requirements", [])
        request.industry = sample_vacancy_data.get("industry")
        request.work_format = sample_vacancy_data.get("work_format")
        request.location = sample_vacancy_data.get("location")
        request.salary_min = sample_vacancy_data.get("salary_min")
        request.salary_max = sample_vacancy_data.get("salary_max")
        request.english_level = sample_vacancy_data.get("english_level")
        request.employment_type = sample_vacancy_data.get("employment_type")
        request.external_id = sample_vacancy_data.get("external_id")
        request.source = sample_vacancy_data.get("source", "manual")

        with patch("api.vacancies.Vacancy") as mock_vacancy_class:
            mock_vacancy_class.return_value = new_vacancy
            response = await create_vacancy(Mock(), request, mock_db_session)

        assert response.status_code == status.HTTP_201_CREATED
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_vacancy_rollback_on_error(self, mock_db_session):
        """Test rollback on database error."""
        mock_db_session.commit.side_effect = Exception("Database error")

        request = Mock(spec=VacancyCreateRequest)
        request.title = "Developer"
        request.description = "Job description"
        request.required_skills = ["Python"]
        request.min_experience_months = None
        request.additional_requirements = []
        request.industry = None
        request.work_format = None
        request.location = None
        request.salary_min = None
        request.salary_max = None
        request.english_level = None
        request.employment_type = None
        request.external_id = None
        request.source = "manual"

        with pytest.raises(HTTPException) as exc_info:
            await create_vacancy(Mock(), request, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_db_session.rollback.assert_called_once()


# ============================================================================
# Tests for list_vacancies Endpoint
# ============================================================================

class TestListVacancies:
    """Tests for list_vacancies endpoint."""

    @pytest.mark.asyncio
    async def test_list_vacancies_success(self, sample_vacancy, mock_db_session):
        """Test successful listing of vacancies."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_vacancy]
        mock_db_session.execute.return_value = mock_result

        response = await list_vacancies(Mock(), skip=0, limit=100, db=mock_db_session)

        assert response.status_code == status.HTTP_200_OK
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_vacancies_empty(self, mock_db_session):
        """Test listing when no vacancies exist."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        response = await list_vacancies(Mock(), skip=0, limit=100, db=mock_db_session)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_list_vacancies_with_pagination(self, mock_db_session):
        """Test pagination parameters."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        await list_vacancies(Mock(), skip=10, limit=50, db=mock_db_session)

        # Verify execute was called
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_list_vacancies_database_error(self, mock_db_session):
        """Test error handling when database fails."""
        mock_db_session.execute.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await list_vacancies(Mock(), db=mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Tests for get_vacancy Endpoint
# ============================================================================

class TestGetVacancy:
    """Tests for get_vacancy endpoint."""

    @pytest.mark.asyncio
    async def test_get_vacancy_success(self, sample_vacancy, mock_db_session):
        """Test successful retrieval of a vacancy."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_vacancy
        mock_db_session.execute.return_value = mock_result

        response = await get_vacancy(str(sample_vacancy.id), mock_db_session)

        assert response.status_code == status.HTTP_200_OK
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_vacancy_invalid_uuid(self, mock_db_session):
        """Test get_vacancy with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await get_vacancy("invalid-uuid", mock_db_session)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_vacancy_not_found(self, mock_db_session):
        """Test get_vacancy when vacancy doesn't exist."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        test_uuid = str(uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await get_vacancy(test_uuid, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_vacancy_database_error(self, mock_db_session):
        """Test error handling when database fails."""
        mock_db_session.execute.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await get_vacancy(str(uuid4()), mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# Tests for update_vacancy Endpoint
# ============================================================================

class TestUpdateVacancy:
    """Tests for update_vacancy endpoint."""

    @pytest.mark.asyncio
    async def test_update_vacancy_success(self, sample_vacancy, mock_db_session):
        """Test successful vacancy update."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_vacancy
        mock_db_session.execute.return_value = mock_result

        update_request = Mock(spec=VacancyUpdateRequest)
        update_request.model_dump.return_value = {"title": "Updated Title"}

        response = await update_vacancy(
            str(sample_vacancy.id), update_request, mock_db_session
        )

        assert response.status_code == status.HTTP_200_OK
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vacancy_invalid_uuid(self, mock_db_session):
        """Test update_vacancy with invalid UUID."""
        update_request = Mock(spec=VacancyUpdateRequest)

        with pytest.raises(HTTPException) as exc_info:
            await update_vacancy("invalid-uuid", update_request, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_vacancy_not_found(self, mock_db_session):
        """Test update_vacancy when vacancy doesn't exist."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        update_request = Mock(spec=VacancyUpdateRequest)

        with pytest.raises(HTTPException) as exc_info:
            await update_vacancy(str(uuid4()), update_request, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_vacancy_rollback_on_error(self, mock_db_session):
        """Test rollback on database error during update."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_vacancy
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit.side_effect = Exception("Database error")

        update_request = Mock(spec=VacancyUpdateRequest)
        update_request.model_dump.return_value = {"title": "Updated"}

        with pytest.raises(HTTPException) as exc_info:
            await update_vacancy(str(uuid4()), update_request, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_db_session.rollback.assert_called_once()


# ============================================================================
# Tests for delete_vacancy Endpoint
# ============================================================================

class TestDeleteVacancy:
    """Tests for delete_vacancy endpoint."""

    @pytest.mark.asyncio
    async def test_delete_vacancy_success(self, sample_vacancy, mock_db_session):
        """Test successful vacancy deletion."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_vacancy
        mock_db_session.execute.return_value = mock_result

        response = await delete_vacancy(str(sample_vacancy.id), mock_db_session)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_db_session.delete.assert_called_once_with(sample_vacancy)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_vacancy_invalid_uuid(self, mock_db_session):
        """Test delete_vacancy with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await delete_vacancy("invalid-uuid", mock_db_session)

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_delete_vacancy_not_found(self, mock_db_session):
        """Test delete_vacancy when vacancy doesn't exist."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await delete_vacancy(str(uuid4()), mock_db_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_vacancy_rollback_on_error(self, mock_db_session):
        """Test rollback on database error during deletion."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_vacancy
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await delete_vacancy(str(uuid4()), mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_db_session.rollback.assert_called_once()


# ============================================================================
# Tests for Settings (config.py)
# ============================================================================

class TestSettings:
    """Tests for Settings configuration."""

    def test_default_settings(self):
        """Test default Settings values."""
        settings = Settings()
        assert settings.service_host == "0.0.0.0"
        assert settings.service_port == 8004
        assert settings.log_level == "INFO"

    def test_database_url_default(self):
        """Test default database URL."""
        settings = Settings()
        assert "postgresql" in settings.database_url

    def test_redis_url_default(self):
        """Test default Redis URL."""
        settings = Settings()
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_validate_database_url_valid(self):
        """Test database URL validation with valid URL."""
        settings = Settings(database_url="postgresql://localhost/test")
        assert settings.database_url == "postgresql://localhost/test"

    def test_validate_database_url_invalid_scheme(self):
        """Test database URL validation with invalid scheme."""
        settings = Settings(database_url="mysql://localhost/test")
        # Should warn but still return the value
        assert settings.database_url == "mysql://localhost/test"

    def test_validate_log_level_valid(self):
        """Test log level validation with valid levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level.lower())
            assert settings.log_level == level

    def test_validate_log_level_invalid(self):
        """Test log level validation with invalid level."""
        settings = Settings(log_level="INVALID")
        assert settings.log_level == "INFO"  # Default fallback

    def test_cors_origins_property(self):
        """Test cors_origins property returns list."""
        settings = Settings()
        origins = settings.cors_origins
        assert isinstance(origins, list)
        assert len(origins) > 0
        assert "http://localhost:3000" in origins

    def test_get_db_url_async_postgresql(self):
        """Test get_db_url_async converts postgresql URL."""
        settings = Settings(database_url="postgresql://localhost/test")
        async_url = settings.get_db_url_async()
        assert async_url == "postgresql+asyncpg://localhost/test"

    def test_get_db_url_async_already_async(self):
        """Test get_db_url_async keeps async URL."""
        settings = Settings(database_url="postgresql+asyncpg://localhost/test")
        async_url = settings.get_db_url_async()
        assert async_url == "postgresql+asyncpg://localhost/test"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_initialization(self, monkeypatch):
        """Test get_settings initializes on first call."""
        # Reset the global settings
        import config
        monkeypatch.setattr(config, "_settings", None)

        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# ============================================================================
# Tests for Database Functions (database.py)
# ============================================================================

class TestExtractTableAndOperation:
    """Tests for _extract_table_and_operation function."""

    def test_extract_select_operation(self):
        """Test extracting SELECT operation."""
        query = "SELECT * FROM vacancies WHERE id = 1"
        operation, table = _extract_table_and_operation(query)
        assert operation == "SELECT"
        assert table == "vacancies"

    def test_extract_insert_operation(self):
        """Test extracting INSERT operation."""
        query = "INSERT INTO vacancies (title) VALUES ('Developer')"
        operation, table = _extract_table_and_operation(query)
        assert operation == "INSERT"
        assert table == "vacancies"

    def test_extract_update_operation(self):
        """Test extracting UPDATE operation."""
        query = "UPDATE vacancies SET title = 'Dev' WHERE id = 1"
        operation, table = _extract_table_and_operation(query)
        assert operation == "UPDATE"
        assert table == "vacancies"

    def test_extract_delete_operation(self):
        """Test extracting DELETE operation."""
        query = "DELETE FROM vacancies WHERE id = 1"
        operation, table = _extract_table_and_operation(query)
        assert operation == "DELETE"
        assert table == "vacancies"

    def test_extract_unknown_query(self):
        """Test extracting from unknown query format."""
        query = "SOME RANDOM SQL QUERY"
        operation, table = _extract_table_and_operation(query)
        assert table == "unknown"

    def test_extract_with_whitespace(self):
        """Test extraction with leading/trailing whitespace."""
        query = "  SELECT * FROM vacancies  "
        operation, table = _extract_table_and_operation(query)
        assert operation == "SELECT"
        assert table == "vacancies"

    def test_extract_case_insensitive(self):
        """Test extraction is case insensitive."""
        query = "select * from vacancies"
        operation, table = _extract_table_and_operation(query)
        assert operation == "SELECT"
        assert table == "vacancies"


# ============================================================================
# Tests for Main App (main.py)
# ============================================================================

class TestMainApp:
    """Tests for main FastAPI application."""

    def test_app_creation(self):
        """Test FastAPI app is created."""
        assert app is not None
        assert app.title == "Vacancy Service"
        assert app.version == "1.0.0"

    def test_app_docs_urls(self):
        """Test documentation URLs are configured."""
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_app_includes_router(self):
        """Test vacancies router is included."""
        routes = [route.path for route in app.routes]
        assert "/api/vacancies/" in routes

    def test_cors_middleware_configured(self):
        """Test CORS middleware is configured."""
        middleware_types = [type(m) for m in app.user_middleware]
        from fastapi.middleware.cors import CORSMiddleware
        assert CORSMiddleware in middleware_types


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check_endpoint(self):
        """Test /health endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "vacancy-service"
        assert data["version"] == "1.0.0"

    def test_ready_check_endpoint(self):
        """Test /ready endpoint."""
        client = TestClient(app)
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_root_endpoint(self):
        """Test / root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Vacancy Service"
        assert data["version"] == "1.0.0"
        assert "/docs" in data["docs"]
        assert "/health" in data["health"]


# ============================================================================
# Tests for Exception Handlers
# ============================================================================

class TestExceptionHandlers:
    """Tests for exception handlers in main app."""

    def test_sqlalchemy_exception_handler(self):
        """Test SQLAlchemy exception handler."""
        client = TestClient(app)
        from sqlalchemy.exc import SQLAlchemyError

        # Mock an endpoint that raises SQLAlchemyError
        @app.get("/test-sql-error")
        async def test_sql_error():
            raise SQLAlchemyError("Test DB error")

        response = client.get("/test-sql-error")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    def test_value_error_handler(self):
        """Test ValueError exception handler."""
        client = TestClient(app)

        @app.get("/test-value-error")
        async def test_value_error():
            raise ValueError("Test validation error")

        response = client.get("/test-value-error")
        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_general_exception_handler(self):
        """Test general exception handler."""
        client = TestClient(app)

        @app.get("/test-general-error")
        async def test_general_error():
            raise Exception("Test unexpected error")

        response = client.get("/test-general-error")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


# ============================================================================
# Tests for Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_vacancy_with_long_title(self):
        """Test vacancy with maximum length title."""
        title = "A" * 255
        vacancy = Vacancy(
            title=title,
            description="Job description",
            required_skills=["Python"],
        )
        assert len(vacancy.title) == 255

    def test_vacancy_with_long_industry(self):
        """Test vacancy with maximum length industry."""
        industry = "A" * 100
        vacancy = Vacancy(
            title="Developer",
            description="Job description",
            required_skills=["Python"],
            industry=industry,
        )
        assert len(vacancy.industry) == 100

    def test_vacancy_with_unicode_skills(self):
        """Test vacancy with unicode characters in skills."""
        vacancy = Vacancy(
            title="Developer",
            description="Job description",
            required_skills=["Python", "Русский язык", "中文"],
        )
        assert "Русский язык" in vacancy.required_skills

    def test_vacancy_create_with_empty_additional_requirements(self):
        """Test vacancy creation with empty additional requirements."""
        request = VacancyCreateRequest(
            title="Developer",
            description="Job description",
            required_skills=["Python"],
            additional_requirements=[],
        )
        assert request.additional_requirements == []

    def test_vacance_update_with_no_changes(self, sample_vacancy, mock_db_session):
        """Test update with no actual changes."""
        import asyncio

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_vacancy
        mock_db_session.execute.return_value = mock_result

        update_request = Mock(spec=VacancyUpdateRequest)
        update_request.model_dump.return_value = {}

        async def test_update():
            response = await update_vacancy(
                str(sample_vacancy.id), update_request, mock_db_session
            )
            return response

        response = asyncio.run(test_update())
        assert response.status_code == 200

    def test_large_required_skills_list(self):
        """Test vacancy with many required skills."""
        skills = [f"Skill{i}" for i in range(50)]
        vacancy = Vacancy(
            title="Developer",
            description="Job description",
            required_skills=skills,
        )
        assert len(vacancy.required_skills) == 50


# ============================================================================
# Tests for Real-World Scenarios
# ============================================================================

class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""

    def test_full_remote_vacancy(self):
        """Test creating a full remote position vacancy."""
        request = VacancyCreateRequest(
            title="Senior React Developer",
            description="Looking for a senior React developer for a remote position.",
            required_skills=["React", "TypeScript", "Node.js"],
            min_experience_months=48,
            additional_requirements=["GraphQL", "AWS"],
            industry="Technology",
            work_format="remote",
            location="Remote",
            salary_min=120000,
            salary_max=160000,
            english_level="Advanced",
            employment_type="full-time",
        )
        assert request.work_format == "remote"
        assert request.location == "Remote"

    def test_entry_level_vacancy(self):
        """Test creating an entry level vacancy."""
        request = VacancyCreateRequest(
            title="Junior Python Developer",
            description="Entry level position for recent graduates.",
            required_skills=["Python", "SQL"],
            min_experience_months=0,
            additional_requirements=[],
            industry="Technology",
            employment_type="full-time",
        )
        assert request.min_experience_months == 0
        assert len(request.required_skills) == 2

    def test_contract_position(self):
        """Test creating a contract position vacancy."""
        request = VacancyCreateRequest(
            title="DevOps Engineer",
            description="Contract position for DevOps engineer.",
            required_skills=["Docker", "Kubernetes", "Terraform"],
            employment_type="contract",
            work_format="remote",
        )
        assert request.employment_type == "contract"

    def test_vacancy_with_external_source(self):
        """Test vacancy sourced from external API."""
        request = VacancyCreateRequest(
            title="Data Scientist",
            description="Data scientist position.",
            required_skills=["Python", "Machine Learning"],
            external_id="linkedin-12345",
            source="api",
        )
        assert request.external_id == "linkedin-12345"
        assert request.source == "api"
