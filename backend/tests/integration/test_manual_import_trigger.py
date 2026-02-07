"""
Integration tests for manual import trigger functionality.

Tests the POST /api/integrations/{id}/trigger-import endpoint which allows
users to manually trigger job board imports from the frontend UI.
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.backend.main import app
from database import async_session_maker
from models.job_board_integration import JobBoardIntegration
from sqlalchemy import select


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_trigger_manual_import_success(db_session):
    """Test that manual import can be triggered for an enabled integration."""
    # Create a test integration
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Indeed Integration",
        api_endpoint="https://api.indeed.com/v2",
        api_key="test_api_key_12345",
        enabled=True,
        config={}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        # Use test client to trigger import
        client = TestClient(app)
        response = client.post(f"/api/integrations/{integration.id}/trigger-import")

        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["integration_id"] == str(integration.id)
        assert data["integration_name"] == "Test Indeed Integration"
        assert data["message"] == "Import task triggered successfully"
        assert data["status"] == "pending"

        # Clean up
        await db.delete(integration)
        await db.commit()


@pytest.mark.asyncio
async def test_trigger_manual_import_disabled_integration(db_session):
    """Test that manual import fails for a disabled integration."""
    # Create a disabled integration
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Disabled Integration",
        api_endpoint="https://api.indeed.com/v2",
        api_key="test_api_key_12345",
        enabled=False,
        config={}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        # Use test client to trigger import
        client = TestClient(app)
        response = client.post(f"/api/integrations/{integration.id}/trigger-import")

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "disabled" in data["detail"].lower()

        # Clean up
        await db.delete(integration)
        await db.commit()


@pytest.mark.asyncio
async def test_trigger_manual_import_nonexistent_integration(db_session):
    """Test that manual import fails for a non-existent integration."""
    fake_id = uuid4()

    client = TestClient(app)
    response = client.post(f"/api/integrations/{fake_id}/trigger-import")

    # Verify response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_trigger_manual_import_invalid_uuid_format(db_session):
    """Test that manual import fails with invalid UUID format."""
    client = TestClient(app)
    response = client.post("/api/integrations/invalid-uuid-format/trigger-import")

    # Verify response
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_trigger_manual_import_returns_task_id(db_session):
    """Test that the trigger endpoint returns a valid Celery task ID."""
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Task ID Integration",
        api_endpoint="https://api.ziprecruiter.com/v1",
        api_key="test_key_67890",
        enabled=True,
        config={}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        # Trigger import
        client = TestClient(app)
        response = client.post(f"/api/integrations/{integration.id}/trigger-import")

        # Verify task_id format (Celery task IDs are typically UUIDs)
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert len(data["task_id"]) > 0
        assert "-" in data["task_id"]  # UUIDs contain hyphens

        # Clean up
        await db.delete(integration)
        await db.commit()
