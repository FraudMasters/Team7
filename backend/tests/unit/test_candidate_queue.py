"""
Unit tests for candidate queue API endpoints.

Tests all endpoints in api/candidate_queue.py including:
- List queue items with filtering and pagination
- Get queue counts by status
- Get queue metrics (wait times, throughput)
- Get single queue item
- Update queue item priority
- Bulk assign candidates to recruiters

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

from api.candidate_queue import router
from models.candidate_queue import CandidateQueueItem, QueuePriority, QueueStatus


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def app():
    """Create a test FastAPI application with the candidate queue router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")
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
def sample_queue_item():
    """Create a sample queue item for testing."""
    item = Mock(spec=CandidateQueueItem)
    item.id = uuid4()
    item.resume_id = uuid4()
    item.vacancy_id = uuid4()
    item.priority = QueuePriority.MEDIUM
    item.status = QueueStatus.PENDING
    item.assigned_recruiter_id = None
    item.queue_entered_at = datetime.now(timezone.utc) - timedelta(hours=5)
    item.review_started_at = None
    item.review_completed_at = None
    item.notes = "Test notes"
    item.created_at = datetime.now(timezone.utc) - timedelta(hours=5)
    item.updated_at = datetime.now(timezone.utc) - timedelta(hours=5)
    return item


@pytest.fixture
def sample_resume():
    """Create a sample resume mock for testing."""
    resume = Mock()
    resume.id = uuid4()
    resume.filename = "test_resume.pdf"
    return resume


@pytest.fixture
def sample_vacancy():
    """Create a sample vacancy mock for testing."""
    vacancy = Mock()
    vacancy.id = uuid4()
    vacancy.title = "Senior Python Developer"
    return vacancy


# =============================================================================
# List Queue Items Tests
# =============================================================================

@pytest.mark.asyncio
async def test_list_queue_success(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items returns correct data."""
    # Mock database results
    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    # Create test app with mocked dependency
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    # Make request
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/")

    # Assertions
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["skip"] == 0
    assert data["limit"] == 50


@pytest.mark.asyncio
async def test_list_queue_with_status_filter(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items with status filter."""
    sample_queue_item.status = QueueStatus.PENDING

    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/?status=pending")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_list_queue_with_invalid_status(mock_db):
    """Test listing queue items with invalid status returns 400."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/?status=invalid_status")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid status" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_queue_with_priority_filter(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items with priority filter."""
    sample_queue_item.priority = QueuePriority.HIGH

    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/?priority=high")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_list_queue_with_invalid_priority(mock_db):
    """Test listing queue items with invalid priority returns 400."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/?priority=invalid_priority")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid priority" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_queue_with_date_filter(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items with date range filter."""
    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        entered_after = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        response = await client.get(f"/api/candidate-queue/?entered_after={entered_after}")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_list_queue_with_invalid_date_format(mock_db):
    """Test listing queue items with invalid date format returns 400."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/?entered_after=invalid-date")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid entered_after format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_queue_with_pagination(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items with pagination parameters."""
    mock_result = Mock()
    mock_result.all = Mock(return_value=[])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=100)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/?skip=10&limit=20")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["skip"] == 10
    assert data["limit"] == 20


@pytest.mark.asyncio
async def test_list_queue_empty(mock_db):
    """Test listing queue items when queue is empty."""
    mock_result = Mock()
    mock_result.all = Mock(return_value=[])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=0)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_queue_database_error(mock_db):
    """Test listing queue items handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database connection failed"))

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Get Queue Counts Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_queue_counts_success(mock_db):
    """Test getting queue counts returns correct data."""
    # Mock count results for each status
    count_results = []
    for _ in QueueStatus:
        mock_count = Mock()
        mock_count.scalar = Mock(return_value=10)
        count_results.append(mock_count)

    mock_db.execute = AsyncMock(side_effect=count_results)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/counts")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "pending" in data
    assert "in_review" in data
    assert "completed" in data
    assert "skipped" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_queue_counts_with_vacancy_filter(mock_db):
    """Test getting queue counts with vacancy filter."""
    count_results = []
    for _ in QueueStatus:
        mock_count = Mock()
        mock_count.scalar = Mock(return_value=5)
        count_results.append(mock_count)

    mock_db.execute = AsyncMock(side_effect=count_results)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    vacancy_id = str(uuid4())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidate-queue/counts?vacancy_id={vacancy_id}")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_queue_counts_database_error(mock_db):
    """Test getting queue counts handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/counts")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Get Queue Metrics Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_queue_metrics_success(mock_db):
    """Test getting queue metrics returns correct data."""
    # Mock count results for each status
    count_results = []
    for _ in QueueStatus:
        mock_count = Mock()
        mock_count.scalar = Mock(return_value=10)
        count_results.append(mock_count)

    # Mock pending items query (for wait time calculation)
    mock_pending_result = Mock()
    mock_pending_result.all = Mock(return_value=[
        (datetime.now(timezone.utc) - timedelta(hours=2),),
        (datetime.now(timezone.utc) - timedelta(hours=4),),
    ])
    count_results.append(mock_pending_result)

    # Mock oldest pending query
    mock_oldest_result = Mock()
    mock_oldest_result.scalar = Mock(return_value=datetime.now(timezone.utc) - timedelta(hours=4))
    count_results.append(mock_oldest_result)

    # Mock throughput queries
    for _ in range(2):
        mock_throughput = Mock()
        mock_throughput.scalar = Mock(return_value=5)
        count_results.append(mock_throughput)

    mock_db.execute = AsyncMock(side_effect=count_results)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/metrics")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "counts" in data
    assert "average_wait_time_hours" in data
    assert "median_wait_time_hours" in data
    assert "oldest_pending_at" in data
    assert "throughput_last_24h" in data
    assert "throughput_last_7d" in data


@pytest.mark.asyncio
async def test_get_queue_metrics_empty_queue(mock_db):
    """Test getting queue metrics when queue is empty."""
    # Mock count results for each status (all zero)
    count_results = []
    for _ in QueueStatus:
        mock_count = Mock()
        mock_count.scalar = Mock(return_value=0)
        count_results.append(mock_count)

    # Mock pending items query (empty)
    mock_pending_result = Mock()
    mock_pending_result.all = Mock(return_value=[])
    count_results.append(mock_pending_result)

    mock_db.execute = AsyncMock(side_effect=count_results)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/metrics")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["average_wait_time_hours"] is None
    assert data["median_wait_time_hours"] is None


@pytest.mark.asyncio
async def test_get_queue_metrics_database_error(mock_db):
    """Test getting queue metrics handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/metrics")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Get Single Queue Item Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_queue_item_success(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test getting a single queue item returns correct data."""
    mock_result = Mock()
    mock_result.first = Mock(return_value=(sample_queue_item, sample_resume, sample_vacancy))
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidate-queue/{sample_queue_item.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(sample_queue_item.id)
    assert data["priority"] == sample_queue_item.priority.value
    assert data["status"] == sample_queue_item.status.value


@pytest.mark.asyncio
async def test_get_queue_item_not_found(mock_db):
    """Test getting a non-existent queue item returns 404."""
    mock_result = Mock()
    mock_result.first = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidate-queue/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_queue_item_invalid_id(mock_db):
    """Test getting a queue item with invalid ID returns 400."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/invalid-uuid")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid queue item ID format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_queue_item_database_error(mock_db):
    """Test getting a queue item handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidate-queue/{uuid4()}")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Update Priority Tests
# =============================================================================

@pytest.mark.asyncio
async def test_update_priority_success(mock_db, sample_queue_item):
    """Test updating queue item priority succeeds."""
    sample_queue_item.priority = QueuePriority.MEDIUM

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_queue_item)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidate-queue/{sample_queue_item.id}/priority",
            json={"priority": "urgent"}
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["previous_priority"] == "medium"
    assert data["new_priority"] == "urgent"


@pytest.mark.asyncio
async def test_update_priority_not_found(mock_db):
    """Test updating priority for non-existent item returns 404."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidate-queue/{uuid4()}/priority",
            json={"priority": "urgent"}
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_priority_invalid_id(mock_db):
    """Test updating priority with invalid ID returns 400."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/api/candidate-queue/invalid-uuid/priority",
            json={"priority": "urgent"}
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_priority_invalid_value(mock_db, sample_queue_item):
    """Test updating priority with invalid value returns 400."""
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_queue_item)
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidate-queue/{uuid4()}/priority",
            json={"priority": "invalid_priority"}
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid priority" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_priority_database_error(mock_db, sample_queue_item):
    """Test updating priority handles database errors."""
    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/candidate-queue/{uuid4()}/priority",
            json={"priority": "urgent"}
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# =============================================================================
# Assign Candidates Tests
# =============================================================================

@pytest.mark.asyncio
async def test_assign_candidates_success(mock_db, sample_queue_item, sample_resume):
    """Test assigning candidates to recruiter succeeds."""
    resume_id = str(uuid4())
    recruiter_id = str(uuid4())

    # Mock resume lookup
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    # Mock queue item lookup (existing item)
    mock_queue_result = Mock()
    mock_queue_result.scalar_one_or_none = Mock(return_value=sample_queue_item)

    mock_db.execute = AsyncMock(side_effect=[mock_resume_result, mock_queue_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": [resume_id],
                "recruiter_id": recruiter_id
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_requested"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_assign_candidates_multiple(mock_db, sample_queue_item, sample_resume):
    """Test assigning multiple candidates to recruiter."""
    resume_ids = [str(uuid4()), str(uuid4())]
    recruiter_id = str(uuid4())

    # Mock resume and queue lookups for each resume
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    mock_queue_result = Mock()
    mock_queue_result.scalar_one_or_none = Mock(return_value=sample_queue_item)

    # Need results for each resume (2 resumes × 2 queries each)
    mock_db.execute = AsyncMock(side_effect=[
        mock_resume_result, mock_queue_result,  # First resume
        mock_resume_result, mock_queue_result,  # Second resume
    ])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": resume_ids,
                "recruiter_id": recruiter_id
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_requested"] == 2


@pytest.mark.asyncio
async def test_assign_candidates_invalid_recruiter_id(mock_db):
    """Test assigning candidates with invalid recruiter ID returns 400."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": [str(uuid4())],
                "recruiter_id": "invalid-uuid"
            }
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid recruiter_id format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_assign_candidates_invalid_resume_id(mock_db):
    """Test assigning candidates with invalid resume ID handles gracefully."""
    recruiter_id = str(uuid4())

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": ["invalid-uuid"],
                "recruiter_id": recruiter_id
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["successful"] == 0
    assert data["failed"] == 1
    assert "Invalid resume ID format" in data["results"][0]["message"]


@pytest.mark.asyncio
async def test_assign_candidates_resume_not_found(mock_db):
    """Test assigning non-existent resume handles gracefully."""
    resume_id = str(uuid4())
    recruiter_id = str(uuid4())

    # Mock resume lookup returns None
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_resume_result)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": [resume_id],
                "recruiter_id": recruiter_id
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["successful"] == 0
    assert data["failed"] == 1
    assert "Resume not found" in data["results"][0]["message"]


@pytest.mark.asyncio
async def test_assign_candidates_creates_new_queue_item(mock_db, sample_resume):
    """Test assigning candidate creates new queue item if none exists."""
    resume_id = str(uuid4())
    recruiter_id = str(uuid4())

    # Mock resume lookup returns resume
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    # Mock queue item lookup returns None (no existing item)
    mock_queue_result = Mock()
    mock_queue_result.scalar_one_or_none = Mock(return_value=None)

    mock_db.execute = AsyncMock(side_effect=[mock_resume_result, mock_queue_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": [resume_id],
                "recruiter_id": recruiter_id
            }
        )

    assert response.status_code == status.HTTP_200_OK
    # Verify db.add was called to create new queue item
    assert mock_db.add.called


@pytest.mark.asyncio
async def test_assign_candidates_database_error(mock_db):
    """Test assigning candidates handles database errors."""
    resume_id = str(uuid4())
    recruiter_id = str(uuid4())

    mock_db.execute = AsyncMock(side_effect=Exception("Database error"))

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": [resume_id],
                "recruiter_id": recruiter_id
            }
        )

    # Should handle error gracefully and return partial results
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["failed"] == 1


# =============================================================================
# Edge Cases and Additional Tests
# =============================================================================

@pytest.mark.asyncio
async def test_list_queue_with_sorting(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items with different sorting options."""
    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test sort by wait_time
        response = await client.get("/api/candidate-queue/?sort_by=wait_time&sort_order=desc")
        assert response.status_code == status.HTTP_200_OK

        # Test sort by created_at
        response = await client.get("/api/candidate-queue/?sort_by=created_at&sort_order=asc")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_list_queue_wait_time_calculation(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test that wait time is correctly calculated in queue list."""
    # Set queue_entered_at to 2 hours ago
    sample_queue_item.queue_entered_at = datetime.now(timezone.utc) - timedelta(hours=2)

    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Wait time should be approximately 2 hours
    assert data["items"][0]["wait_time_hours"] is not None
    assert 1.9 < data["items"][0]["wait_time_hours"] < 2.1


@pytest.mark.asyncio
async def test_get_queue_item_null_vacancy(mock_db, sample_queue_item, sample_resume):
    """Test getting queue item with null vacancy handles correctly."""
    sample_queue_item.vacancy_id = None

    mock_result = Mock()
    mock_result.first = Mock(return_value=(sample_queue_item, sample_resume, None))
    mock_db.execute = AsyncMock(return_value=mock_result)

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidate-queue/{sample_queue_item.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["vacancy_id"] is None
    assert data["vacancy_title"] is None


@pytest.mark.asyncio
async def test_list_queue_with_vacancy_id_filter(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items with vacancy_id filter."""
    vacancy_id = str(sample_queue_item.vacancy_id)

    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidate-queue/?vacancy_id={vacancy_id}")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_list_queue_with_recruiter_id_filter(mock_db, sample_queue_item, sample_resume, sample_vacancy):
    """Test listing queue items with assigned_recruiter_id filter."""
    recruiter_id = str(uuid4())
    sample_queue_item.assigned_recruiter_id = UUID(recruiter_id)

    mock_result = Mock()
    mock_result.all = Mock(return_value=[
        (sample_queue_item, sample_resume, sample_vacancy)
    ])
    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=1)
    mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/candidate-queue/?assigned_recruiter_id={recruiter_id}")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_assign_candidates_preserves_previous_recruiter(mock_db, sample_queue_item, sample_resume):
    """Test that assigning returns previous recruiter ID when updating."""
    previous_recruiter_id = uuid4()
    sample_queue_item.assigned_recruiter_id = previous_recruiter_id

    new_recruiter_id = str(uuid4())
    resume_id = str(uuid4())

    # Mock resume lookup
    mock_resume_result = Mock()
    mock_resume_result.scalar_one_or_none = Mock(return_value=sample_resume)

    # Mock queue item lookup (existing item with previous recruiter)
    mock_queue_result = Mock()
    mock_queue_result.scalar_one_or_none = Mock(return_value=sample_queue_item)

    mock_db.execute = AsyncMock(side_effect=[mock_resume_result, mock_queue_result])

    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": [resume_id],
                "recruiter_id": new_recruiter_id
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["results"][0]["previous_recruiter_id"] == str(previous_recruiter_id)


@pytest.mark.asyncio
async def test_update_priority_all_levels(mock_db, sample_queue_item):
    """Test updating priority to all valid levels."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    for priority_level in ["urgent", "high", "medium", "low"]:
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_queue_item)
        mock_db.execute = AsyncMock(return_value=mock_result)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/candidate-queue/{uuid4()}/priority",
                json={"priority": priority_level}
            )

        assert response.status_code == status.HTTP_200_OK, f"Failed for priority: {priority_level}"


# =============================================================================
# Request Validation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_assign_candidates_empty_resume_list(mock_db):
    """Test assigning with empty resume list is rejected."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/candidate-queue/assign",
            json={
                "resume_ids": [],
                "recruiter_id": str(uuid4())
            }
        )

    # Pydantic should reject empty list with min_length=1
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_list_queue_limit_bounds(mock_db):
    """Test listing queue respects limit bounds."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test limit below minimum
        response = await client.get("/api/candidate-queue/?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test limit above maximum
        response = await client.get("/api/candidate-queue/?limit=300")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_list_queue_skip_negative(mock_db):
    """Test listing queue rejects negative skip."""
    app = FastAPI()
    app.include_router(router, prefix="/api/candidate-queue")

    async def override_get_db():
        yield mock_db

    from api.candidate_queue import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/candidate-queue/?skip=-1")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
