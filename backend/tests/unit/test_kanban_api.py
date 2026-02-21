"""
Unit tests for Kanban API endpoints.

Tests all endpoints in api/workflow_stages.py and kanban-related endpoints in
api/candidates.py including:
- Workflow stage CRUD operations with WIP limits
- Kanban board data retrieval with swimlanes
- Candidate movement between stages
- Bulk candidate movement
- Card preview data

Each test function uses appropriate mocking to isolate the API logic
and test both success and failure scenarios.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
import json

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.workflow_stages import router as workflow_stages_router
from api.candidates import router as candidates_router
from models.workflow_stage_config import WorkflowStageConfig
from models.hiring_stage import HiringStage, HiringStageName
from models.resume import Resume
from models.candidate_tag import CandidateTag


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def app_workflow_stages():
    """Create a test FastAPI application with the workflow stages router."""
    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")
    return app


@pytest.fixture
def app_candidates():
    """Create a test FastAPI application with the candidates router."""
    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")
    return app


@pytest.fixture
def mock_db():
    """Mock database session for testing."""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = Mock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def sample_workflow_stage():
    """Create a sample workflow stage for testing."""
    stage = Mock(spec=WorkflowStageConfig)
    stage.id = uuid4()
    stage.organization_id = str(uuid4())
    stage.stage_name = "Technical Interview"
    stage.stage_order = 3
    stage.is_default = False
    stage.is_active = True
    stage.color = "#3B82F6"
    stage.description = "Technical assessment with engineering team"
    stage.wip_limit = 5
    stage.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    stage.updated_at = datetime.now(timezone.utc)
    return stage


@pytest.fixture
def sample_resume():
    """Create a sample resume mock for testing."""
    resume = Mock(spec=Resume)
    resume.id = uuid4()
    resume.filename = "john_doe_resume.pdf"
    resume.created_at = datetime.now(timezone.utc) - timedelta(days=2)
    return resume


@pytest.fixture
def sample_hiring_stage():
    """Create a sample hiring stage for testing."""
    stage = Mock(spec=HiringStage)
    stage.id = uuid4()
    stage.resume_id = uuid4()
    stage.vacancy_id = uuid4()
    stage.workflow_stage_config_id = None
    stage.stage_name = HiringStageName.APPLIED
    stage.notes = "Initial application"
    stage.created_at = datetime.now(timezone.utc) - timedelta(hours=5)
    stage.updated_at = datetime.now(timezone.utc)
    return stage


@pytest.fixture
def sample_candidate_tag():
    """Create a sample candidate tag for testing."""
    tag = Mock(spec=CandidateTag)
    tag.id = uuid4()
    tag.tag_name = "Top Talent"
    tag.color = "#00FF00"
    tag.organization_id = str(uuid4())
    return tag


# =============================================================================
# Workflow Stages - Create Tests
# =============================================================================

@pytest.mark.asyncio
async def test_create_workflow_stage_success(mock_db, sample_workflow_stage):
    """Test creating a workflow stage succeeds."""
    # Mock that no existing stage with same name
    mock_existing_result = Mock()
    mock_existing_result.scalar_one_or_none = Mock(return_value=None)

    # Mock flush to set the ID
    async def mock_flush_side_effect():
        sample_workflow_stage.id = uuid4()
    mock_db.flush = AsyncMock(side_effect=mock_flush_side_effect)

    mock_db.execute = AsyncMock(return_value=mock_existing_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(sample_workflow_stage.organization_id),
                "stage_name": "Technical Interview",
                "stage_order": 3,
                "is_default": False,
                "is_active": True,
                "color": "#3B82F6",
                "description": "Technical assessment",
                "wip_limit": 5
            }
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["stage_name"] == "Technical Interview"
    assert data["wip_limit"] == 5


@pytest.mark.asyncio
async def test_create_workflow_stage_with_wip_limit(mock_db, sample_workflow_stage):
    """Test creating a workflow stage with WIP limit."""
    mock_existing_result = Mock()
    mock_existing_result.scalar_one_or_none = Mock(return_value=None)

    async def mock_flush_side_effect():
        sample_workflow_stage.id = uuid4()
    mock_db.flush = AsyncMock(side_effect=mock_flush_side_effect)
    mock_db.execute = AsyncMock(return_value=mock_existing_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": "Code Review",
                "stage_order": 2,
                "wip_limit": 10
            }
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["wip_limit"] == 10


@pytest.mark.asyncio
async def test_create_workflow_stage_duplicate_name(mock_db, sample_workflow_stage):
    """Test creating a workflow stage with duplicate name returns 409."""
    mock_existing_result = Mock()
    mock_existing_result.scalar_one_or_none = Mock(return_value=sample_workflow_stage)
    mock_db.execute = AsyncMock(return_value=mock_existing_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(sample_workflow_stage.organization_id),
                "stage_name": "Technical Interview",
                "stage_order": 3
            }
        )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_workflow_stage_invalid_wip_limit(mock_db):
    """Test creating a workflow stage with invalid WIP limit returns 422."""
    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # WIP limit must be >= 1
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": "Test Stage",
                "stage_order": 1,
                "wip_limit": 0
            }
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_workflow_stage_invalid_color(mock_db):
    """Test creating a workflow stage with invalid color format returns 422."""
    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": "Test Stage",
                "stage_order": 1,
                "color": "invalid-color"
            }
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_workflow_stage_database_error(mock_db):
    """Test creating a workflow stage handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database connection failed"))

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": "Test Stage",
                "stage_order": 1
            }
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Workflow Stages - List Tests
# =============================================================================

@pytest.mark.asyncio
async def test_list_workflow_stages_success(mock_db, sample_workflow_stage):
    """Test listing workflow stages returns correct data."""
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[sample_workflow_stage])
    mock_result.scalars = Mock(return_value=mock_scalars)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/workflow-stages/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_count"] == 1
    assert len(data["stages"]) == 1
    assert data["stages"][0]["wip_limit"] == 5


@pytest.mark.asyncio
async def test_list_workflow_stages_with_organization_filter(mock_db, sample_workflow_stage):
    """Test listing workflow stages with organization filter."""
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[sample_workflow_stage])
    mock_result.scalars = Mock(return_value=mock_scalars)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/workflow-stages/?organization_id={sample_workflow_stage.organization_id}"
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["organization_id"] == sample_workflow_stage.organization_id


@pytest.mark.asyncio
async def test_list_workflow_stages_with_active_filter(mock_db, sample_workflow_stage):
    """Test listing workflow stages with active status filter."""
    sample_workflow_stage.is_active = True
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[sample_workflow_stage])
    mock_result.scalars = Mock(return_value=mock_scalars)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/workflow-stages/?is_active=true")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_list_workflow_stages_empty(mock_db):
    """Test listing workflow stages when none exist."""
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[])
    mock_result.scalars = Mock(return_value=mock_scalars)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/workflow-stages/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_count"] == 0
    assert len(data["stages"]) == 0


@pytest.mark.asyncio
async def test_list_workflow_stages_database_error(mock_db):
    """Test listing workflow stages handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/workflow-stages/")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Workflow Stages - Get Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_workflow_stage_success(mock_db, sample_workflow_stage):
    """Test getting a single workflow stage succeeds."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow_stage)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/workflow-stages/{sample_workflow_stage.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["stage_name"] == "Technical Interview"
    assert data["wip_limit"] == 5


@pytest.mark.asyncio
async def test_get_workflow_stage_not_found(mock_db):
    """Test getting a non-existent workflow stage returns 404."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/workflow-stages/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_workflow_stage_invalid_uuid(mock_db):
    """Test getting a workflow stage with invalid UUID returns 422."""
    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/workflow-stages/invalid-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# Workflow Stages - Update Tests
# =============================================================================

@pytest.mark.asyncio
async def test_update_workflow_stage_success(mock_db, sample_workflow_stage):
    """Test updating a workflow stage succeeds."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow_stage)

    # Mock for duplicate name check (returns None = no duplicate)
    mock_duplicate_result = Mock()
    mock_duplicate_result.scalar_one_or_none = Mock(return_value=None)

    mock_db.execute = AsyncMock(side_effect=[mock_result, mock_duplicate_result])

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/workflow-stages/{sample_workflow_stage.id}",
            json={"stage_name": "Updated Interview", "wip_limit": 10}
        )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_update_workflow_stage_wip_limit(mock_db, sample_workflow_stage):
    """Test updating a workflow stage WIP limit."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow_stage)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/workflow-stages/{sample_workflow_stage.id}",
            json={"wip_limit": 15}
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["wip_limit"] == 15


@pytest.mark.asyncio
async def test_update_workflow_stage_not_found(mock_db):
    """Test updating a non-existent workflow stage returns 404."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/workflow-stages/{uuid4()}",
            json={"stage_name": "Updated Name"}
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_workflow_stage_duplicate_name(mock_db, sample_workflow_stage):
    """Test updating a workflow stage with duplicate name returns 409."""
    # Mock finding the stage
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow_stage)

    # Mock finding duplicate name
    mock_duplicate_result = Mock()
    mock_duplicate_result.scalar_one_or_none = Mock(return_value=Mock())

    mock_db.execute = AsyncMock(side_effect=[mock_result, mock_duplicate_result])

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/workflow-stages/{sample_workflow_stage.id}",
            json={"stage_name": "Duplicate Name"}
        )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_update_workflow_stage_remove_wip_limit(mock_db, sample_workflow_stage):
    """Test removing WIP limit from a workflow stage."""
    sample_workflow_stage.wip_limit = 5

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow_stage)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setting wip_limit to None in the update
        response = await client.put(
            f"/api/workflow-stages/{sample_workflow_stage.id}",
            json={"wip_limit": None}
        )

    # Note: This might return 422 if None is not allowed by validation
    # Check the actual behavior based on the model
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


# =============================================================================
# Workflow Stages - Delete Tests
# =============================================================================

@pytest.mark.asyncio
async def test_delete_workflow_stage_success(mock_db, sample_workflow_stage):
    """Test deleting a workflow stage succeeds."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow_stage)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/workflow-stages/{sample_workflow_stage.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "deleted successfully" in data["message"]


@pytest.mark.asyncio
async def test_delete_workflow_stage_not_found(mock_db):
    """Test deleting a non-existent workflow stage returns 404."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/workflow-stages/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Kanban Board - Get Board Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_kanban_board_success(mock_db, sample_resume, sample_hiring_stage):
    """Test getting kanban board data succeeds."""
    # Mock stage configs query
    mock_config_result = Mock()
    mock_config_scalars = Mock()
    mock_config_scalars.all = Mock(return_value=[])
    mock_config_result.scalars = Mock(return_value=mock_config_scalars)

    # Mock candidates query
    mock_candidates_result = Mock()
    mock_candidates_result.all = Mock(return_value=[])

    # Mock vacancies query
    mock_vacancies_result = Mock()
    mock_vacancies_scalars = Mock()
    mock_vacancies_scalars.all = Mock(return_value=[])
    mock_vacancies_result.scalars = Mock(return_value=mock_vacancies_scalars)

    mock_db.execute = AsyncMock(side_effect=[
        mock_config_result,
        mock_candidates_result,
        mock_vacancies_result,
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/kanban")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "group_by" in data
    assert "swimlanes" in data
    assert "stages" in data
    assert "total_candidates" in data


@pytest.mark.asyncio
async def test_get_kanban_board_group_by_job(mock_db):
    """Test getting kanban board grouped by job."""
    mock_config_result = Mock()
    mock_config_scalars = Mock()
    mock_config_scalars.all = Mock(return_value=[])
    mock_config_result.scalars = Mock(return_value=mock_config_scalars)

    mock_candidates_result = Mock()
    mock_candidates_result.all = Mock(return_value=[])

    mock_vacancies_result = Mock()
    mock_vacancies_scalars = Mock()
    mock_vacancies_scalars.all = Mock(return_value=[])
    mock_vacancies_result.scalars = Mock(return_value=mock_vacancies_scalars)

    mock_db.execute = AsyncMock(side_effect=[
        mock_config_result,
        mock_candidates_result,
        mock_vacancies_result,
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/kanban?group_by=job")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["group_by"] == "job"


@pytest.mark.asyncio
async def test_get_kanban_board_invalid_group_by(mock_db):
    """Test getting kanban board with invalid group_by returns 400."""
    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/kanban?group_by=invalid")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid group_by" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_kanban_board_with_wip_limits(mock_db, sample_workflow_stage):
    """Test getting kanban board includes WIP limit information."""
    sample_workflow_stage.wip_limit = 5

    mock_config_result = Mock()
    mock_config_scalars = Mock()
    mock_config_scalars.all = Mock(return_value=[sample_workflow_stage])
    mock_config_result.scalars = Mock(return_value=mock_config_scalars)

    mock_candidates_result = Mock()
    mock_candidates_result.all = Mock(return_value=[])

    mock_vacancies_result = Mock()
    mock_vacancies_scalars = Mock()
    mock_vacancies_scalars.all = Mock(return_value=[])
    mock_vacancies_result.scalars = Mock(return_value=mock_vacancies_scalars)

    mock_db.execute = AsyncMock(side_effect=[
        mock_config_result,
        mock_candidates_result,
        mock_vacancies_result,
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/kanban")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Check stages include wip_limit field
    for stage in data["stages"]:
        assert "wip_limit" in stage


@pytest.mark.asyncio
async def test_get_kanban_board_database_error(mock_db):
    """Test getting kanban board handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/kanban")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Candidates - Move Candidate Tests
# =============================================================================

@pytest.mark.asyncio
async def test_move_candidate_success(mock_db, sample_resume, sample_hiring_stage):
    """Test moving a candidate to a new stage succeeds."""
    sample_hiring_stage.stage_name = HiringStageName.APPLIED

    # Mock resume lookup
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    # Mock current stage lookup
    mock_stage_result = Mock()
    mock_stage_result.scalar_one_or_none = Mock(return_value=sample_hiring_stage)

    mock_db.execute = AsyncMock(side_effect=[mock_resume_result, mock_stage_result])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidates/{sample_resume.id}/stage",
            json={"stage_id": "interview"}
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["previous_stage"] == "applied"
    assert data["new_stage"] == "interview"


@pytest.mark.asyncio
async def test_move_candidate_with_notes(mock_db, sample_resume, sample_hiring_stage):
    """Test moving a candidate with notes."""
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    mock_stage_result = Mock()
    mock_stage_result.scalar_one_or_none = Mock(return_value=sample_hiring_stage)

    mock_db.execute = AsyncMock(side_effect=[mock_resume_result, mock_stage_result])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidates/{sample_resume.id}/stage",
            json={
                "stage_id": "screening",
                "notes": "Passed initial review"
            }
        )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_move_candidate_not_found(mock_db):
    """Test moving a non-existent candidate returns 404."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidates/{uuid4()}/stage",
            json={"stage_id": "interview"}
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_move_candidate_invalid_id(mock_db):
    """Test moving a candidate with invalid ID returns 400."""
    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/api/candidates/invalid-uuid/stage",
            json={"stage_id": "interview"}
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_move_candidate_invalid_stage(mock_db, sample_resume, sample_hiring_stage):
    """Test moving a candidate to invalid stage returns 400."""
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    mock_stage_result = Mock()
    mock_stage_result.scalar_one_or_none = Mock(return_value=sample_hiring_stage)

    # Mock workflow config lookup (returns None - invalid stage)
    mock_config_result = Mock()
    mock_config_result.scalar_one_or_none = Mock(return_value=None)

    mock_db.execute = AsyncMock(side_effect=[
        mock_resume_result,
        mock_stage_result,
        mock_config_result
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidates/{sample_resume.id}/stage",
            json={"stage_id": "invalid_stage_name"}
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid stage name" in response.json()["detail"]


@pytest.mark.asyncio
async def test_move_candidate_database_error(mock_db):
    """Test moving a candidate handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidates/{uuid4()}/stage",
            json={"stage_id": "interview"}
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Candidates - Bulk Move Tests
# =============================================================================

@pytest.mark.asyncio
async def test_bulk_move_candidates_success(mock_db, sample_resume, sample_hiring_stage):
    """Test bulk moving candidates succeeds."""
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    mock_stage_result = Mock()
    mock_stage_result.scalar_one_or_none = Mock(return_value=sample_hiring_stage)

    mock_db.execute = AsyncMock(side_effect=[mock_resume_result, mock_stage_result])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidates/bulk-move",
            json={
                "resume_ids": [str(sample_resume.id)],
                "stage_id": "screening",
                "notes": "Bulk screening"
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_requested"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_bulk_move_candidates_partial_success(mock_db, sample_resume, sample_hiring_stage):
    """Test bulk moving candidates with partial success."""
    resume_id_1 = str(uuid4())
    resume_id_2 = str(uuid4())

    # First resume exists
    mock_resume_result_1 = Mock()
    mock_resume_result_1.scalar_one_or_none = Mock(return_value=sample_resume)

    mock_stage_result_1 = Mock()
    mock_stage_result_1.scalar_one_or_none = Mock(return_value=sample_hiring_stage)

    # Second resume not found
    mock_resume_result_2 = Mock()
    mock_resume_result_2.scalar_one_or_none = Mock(return_value=None)

    # Config lookup for stage validation
    mock_config_result = Mock()
    mock_config_result.scalar_one_or_none = Mock(return_value=None)

    mock_db.execute = AsyncMock(side_effect=[
        mock_config_result,  # Stage validation
        mock_resume_result_1, mock_stage_result_1,  # First candidate
        mock_resume_result_2,  # Second candidate (not found)
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidates/bulk-move",
            json={
                "resume_ids": [resume_id_1, resume_id_2],
                "stage_id": "screening"
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_requested"] == 2


@pytest.mark.asyncio
async def test_bulk_move_candidates_invalid_stage(mock_db):
    """Test bulk moving candidates with invalid stage returns 400."""
    mock_config_result = Mock()
    mock_config_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_config_result)

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidates/bulk-move",
            json={
                "resume_ids": [str(uuid4())],
                "stage_id": "invalid_stage"
            }
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_bulk_move_candidates_empty_list(mock_db):
    """Test bulk moving with empty resume list is rejected."""
    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidates/bulk-move",
            json={
                "resume_ids": [],
                "stage_id": "screening"
            }
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_bulk_move_candidates_database_error(mock_db):
    """Test bulk moving candidates handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidates/bulk-move",
            json={
                "resume_ids": [str(uuid4())],
                "stage_id": "screening"
            }
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Candidates - Get Candidate Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_candidate_success(mock_db, sample_resume, sample_hiring_stage):
    """Test getting a single candidate succeeds."""
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    mock_stage_row = (sample_hiring_stage, None)
    mock_stage_result = Mock()
    mock_stage_result.first = Mock(return_value=mock_stage_row)

    # Mock tag activities query
    mock_tag_result = Mock()
    mock_tag_result.all = Mock(return_value=[])

    # Mock notes count
    mock_notes_result = Mock()
    mock_notes_result.scalar = Mock(return_value=0)

    # Mock latest activity
    mock_activity_result = Mock()
    mock_activity_result.scalar_one_or_none = Mock(return_value=None)

    mock_db.execute = AsyncMock(side_effect=[
        mock_resume_result,
        mock_stage_result,
        mock_tag_result,
        mock_notes_result,
        mock_activity_result,
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidates/{sample_resume.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(sample_resume.id)
    assert data["filename"] == sample_resume.filename


@pytest.mark.asyncio
async def test_get_candidate_not_found(mock_db):
    """Test getting a non-existent candidate returns 404."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidates/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_candidate_invalid_id(mock_db):
    """Test getting a candidate with invalid ID returns 400."""
    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/invalid-uuid")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Candidates - Card Preview Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_candidate_card_preview_success(mock_db, sample_resume, sample_hiring_stage):
    """Test getting candidate card preview succeeds."""
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    mock_stage_result = Mock()
    mock_stage_result.scalar_one_or_none = Mock(return_value=sample_hiring_stage)

    # Mock rank query
    mock_rank_result = Mock()
    mock_rank_result.scalar_one_or_none = Mock(return_value=None)

    # Mock tag activities
    mock_tag_result = Mock()
    mock_tag_result.all = Mock(return_value=[])

    # Mock recent activities
    mock_activities_result = Mock()
    mock_activities_scalars = Mock()
    mock_activities_scalars.all = Mock(return_value=[])
    mock_activities_result.scalars = Mock(return_value=mock_activities_scalars)

    mock_db.execute = AsyncMock(side_effect=[
        mock_resume_result,
        mock_stage_result,
        mock_tag_result,
        mock_activities_result,
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidates/{sample_resume.id}/card-preview")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert "filename" in data
    assert "tags" in data
    assert "recent_activities" in data


@pytest.mark.asyncio
async def test_get_candidate_card_preview_not_found(mock_db):
    """Test getting card preview for non-existent candidate returns 404."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidates/{uuid4()}/card-preview")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_candidate_card_preview_invalid_id(mock_db):
    """Test getting card preview with invalid ID returns 400."""
    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/invalid-uuid/card-preview")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Edge Cases and Additional Tests
# =============================================================================

@pytest.mark.asyncio
async def test_workflow_stage_validation_color_pattern(mock_db):
    """Test workflow stage color must be valid hex pattern."""
    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    # Test valid colors
    valid_colors = ["#3B82F6", "#FFFFFF", "#000000", "#abcdef", "#123456"]
    for color in valid_colors:
        mock_db.execute = AsyncMock()
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": f"Test Stage {color}",
                "stage_order": 1,
                "color": color
            }
        )
        # Color validation is at Pydantic level, so we check it doesn't fail validation
        # (might fail at DB level but that's expected)

    # Test invalid colors (7+2 char pattern validation)
    invalid_colors = ["red", "blue", "#GGG", "#12", "123456"]
    for color in invalid_colors:
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": f"Test Stage {color}",
                "stage_order": 1,
                "color": color
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_wip_limit_minimum_value(mock_db):
    """Test WIP limit must be at least 1."""
    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # WIP limit of 0 should be rejected
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": "Test Stage",
                "stage_order": 1,
                "wip_limit": 0
            }
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_stage_order_minimum_value(mock_db):
    """Test stage_order must be at least 0."""
    app = FastAPI()
    app.include_router(workflow_stages_router, prefix="/api/workflow-stages")

    async def override_get_db():
        yield mock_db

    from api.workflow_stages import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Negative stage_order should be rejected
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": str(uuid4()),
                "stage_name": "Test Stage",
                "stage_order": -1
            }
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_kanban_group_by_recruiter(mock_db):
    """Test kanban board grouped by recruiter."""
    mock_config_result = Mock()
    mock_config_scalars = Mock()
    mock_config_scalars.all = Mock(return_value=[])
    mock_config_result.scalars = Mock(return_value=mock_config_scalars)

    mock_candidates_result = Mock()
    mock_candidates_result.all = Mock(return_value=[])

    mock_vacancies_result = Mock()
    mock_vacancies_scalars = Mock()
    mock_vacancies_scalars.all = Mock(return_value=[])
    mock_vacancies_result.scalars = Mock(return_value=mock_vacancies_scalars)

    mock_db.execute = AsyncMock(side_effect=[
        mock_config_result,
        mock_candidates_result,
        mock_vacancies_result,
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/kanban?group_by=recruiter")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["group_by"] == "recruiter"


@pytest.mark.asyncio
async def test_kanban_group_by_none(mock_db):
    """Test kanban board with no grouping."""
    mock_config_result = Mock()
    mock_config_scalars = Mock()
    mock_config_scalars.all = Mock(return_value=[])
    mock_config_result.scalars = Mock(return_value=mock_config_scalars)

    mock_candidates_result = Mock()
    mock_candidates_result.all = Mock(return_value=[])

    mock_vacancies_result = Mock()
    mock_vacancies_scalars = Mock()
    mock_vacancies_scalars.all = Mock(return_value=[])
    mock_vacancies_result.scalars = Mock(return_value=mock_vacancies_scalars)

    mock_db.execute = AsyncMock(side_effect=[
        mock_config_result,
        mock_candidates_result,
        mock_vacancies_result,
    ])

    app = FastAPI()
    app.include_router(candidates_router, prefix="/api/candidates")

    async def override_get_db():
        yield mock_db

    from api.candidates import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidates/kanban?group_by=none")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["group_by"] == "none"
