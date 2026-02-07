"""
import os
Comprehensive integration tests for search alert workflow.

This test suite verifies:
1. Creating saved searches with filters
2. Search alerts created when resumes match saved searches
3. Processing pending search alerts
4. Sending search alert notifications
5. Multiple matches for a single resume
6. No matches scenario
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid import uuid4

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.saved_search import SavedSearch
from models.search_alert import SearchAlert
from tasks.search_alerts_task import (
    check_resume_against_saved_searches,
    send_search_alert_notification,
    process_pending_alerts,
)


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_search_alerts.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_saved_search(client: AsyncClient, test_db: AsyncSession):
    """Test creating a saved search with filters."""
    # Create a saved search
    response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Senior Python Developers",
            "query": "Python AND Django",
            "filters": {
                "skills": ["Python", "Django", "FastAPI"],
                "min_experience_years": 5,
                "location": "Remote",
            }
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Senior Python Developers"
    assert data["query"] == "Python AND Django"
    assert "filters" in data
    assert data["filters"]["skills"] == ["Python", "Django", "FastAPI"]
    assert data["filters"]["min_experience_years"] == 5
    assert data["filters"]["location"] == "Remote"
    assert "id" in data

    # Verify in database
    stmt = select(SavedSearch).where(SavedSearch.id == data["id"])
    result = await test_db.execute(stmt)
    saved_search = result.scalar_one_or_none()

    assert saved_search is not None
    assert saved_search.name == "Senior Python Developers"


@pytest.mark.asyncio
async def test_search_alert_created_on_resume_upload(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that search alerts are created when a new resume matches saved searches."""
    # Step 1: Create a saved search
    search_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Python Developers",
            "query": "Python",
            "filters": {
                "skills": ["Python", "FastAPI"],
                "min_experience_years": 3,
            }
        }
    )
    assert search_response.status_code == 201
    saved_search_id = search_response.json()["id"]

    # Step 2: Create a resume that matches the search
    resume = Resume(
        filename="john_developer.pdf",
        file_path="/test/john.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Experienced Python developer with 5 years of experience in FastAPI and Django",
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    # Step 3: Trigger search alert checking
    resume_data = {
        "skills": ["Python", "FastAPI", "Django"],
        "experience_years": 5,
        "location": "Remote",
        "education": "Bachelor's",
        "raw_text": resume.raw_text,
    }

    result = check_resume_against_saved_searches(
        resume_id=str(resume.id),
        resume_data=resume_data,
    )

    # Wait for task to complete (it's synchronous in test)
    assert result["status"] == "completed"
    assert result["matches_found"] == 1
    assert result["alerts_created"] == 1

    # Step 4: Verify alert was created in database
    stmt = select(SearchAlert).where(
        SearchAlert.saved_search_id == saved_search_id,
        SearchAlert.resume_id == resume.id
    )
    alert_result = await test_db.execute(stmt)
    alert = alert_result.scalar_one_or_none()

    assert alert is not None
    assert alert.is_sent is False
    assert alert.saved_search_id == saved_search_id
    assert alert.resume_id == resume.id


@pytest.mark.asyncio
async def test_multiple_saved_searches_match_resume(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that multiple search alerts are created when a resume matches multiple saved searches."""
    # Create multiple saved searches
    search1_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Python Developers",
            "query": "Python",
            "filters": {"skills": ["Python"]}
        }
    )
    search1_id = search1_response.json()["id"]

    search2_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "FastAPI Developers",
            "query": "FastAPI",
            "filters": {"skills": ["FastAPI"]}
        }
    )
    search2_id = search2_response.json()["id"]

    # Create a resume matching both searches
    resume = Resume(
        filename="fullstack_dev.pdf",
        file_path="/test/fullstack.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Fullstack developer with Python and FastAPI experience",
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    # Trigger search alert checking
    resume_data = {
        "skills": ["Python", "FastAPI", "JavaScript"],
        "experience_years": 4,
        "raw_text": resume.raw_text,
    }

    result = check_resume_against_saved_searches(
        resume_id=str(resume.id),
        resume_data=resume_data,
    )

    assert result["status"] == "completed"
    assert result["matches_found"] == 2
    assert result["alerts_created"] == 2

    # Verify both alerts were created
    stmt = select(SearchAlert).where(SearchAlert.resume_id == resume.id)
    alert_result = await test_db.execute(stmt)
    alerts = alert_result.scalars().all()

    assert len(alerts) == 2
    saved_search_ids = {alert.saved_search_id for alert in alerts}
    assert {str(search1_id), str(search2_id)} == saved_search_ids


@pytest.mark.asyncio
async def test_no_match_no_alert_created(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that no alerts are created when a resume doesn't match saved searches."""
    # Create a saved search with specific requirements
    search_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Senior Java Architects",
            "query": "Java AND Architect",
            "filters": {
                "skills": ["Java", "Spring", "Kubernetes"],
                "min_experience_years": 10,
            }
        }
    )
    assert search_response.status_code == 201

    # Create a resume that doesn't match
    resume = Resume(
        filename="junior_python.pdf",
        file_path="/test/junior.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Junior Python developer with 1 year of experience",
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    # Trigger search alert checking
    resume_data = {
        "skills": ["Python", "Flask"],
        "experience_years": 1,
        "raw_text": resume.raw_text,
    }

    result = check_resume_against_saved_searches(
        resume_id=str(resume.id),
        resume_data=resume_data,
    )

    assert result["status"] == "completed"
    assert result["matches_found"] == 0
    assert result["alerts_created"] == 0

    # Verify no alert was created
    stmt = select(func.count(SearchAlert.id)).where(SearchAlert.resume_id == resume.id)
    count_result = await test_db.execute(stmt)
    alert_count = count_result.scalar()

    assert alert_count == 0


@pytest.mark.asyncio
async def test_process_pending_alerts(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test processing pending search alerts."""
    # Create saved search and resume
    search_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Data Scientists",
            "query": "Python AND ML",
            "filters": {"skills": ["Python", "Machine Learning"]}
        }
    )
    saved_search_id = search_response.json()["id"]

    resume = Resume(
        filename="data_scientist.pdf",
        file_path="/test/ds.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Data scientist with Python and ML experience",
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    # Create pending alert manually
    alert = SearchAlert(
        saved_search_id=saved_search_id,
        resume_id=resume.id,
        is_sent=False,
    )
    test_db.add(alert)
    await test_db.commit()

    # Process pending alerts
    result = process_pending_alerts(batch_size=50)

    assert result["status"] == "completed"
    assert result["total_alerts_processed"] == 1
    assert result["successful_sends"] == 1
    assert result["failed_sends"] == 0

    # Verify alert is now marked as sent
    await test_db.refresh(alert)
    assert alert.is_sent is True
    assert alert.sent_at is not None


@pytest.mark.asyncio
async def test_send_search_alert_notification(client: AsyncClient, test_db: AsyncSession):
    """Test sending a search alert notification."""
    # Create saved search, resume, and alert
    search_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "DevOps Engineers",
            "query": "Docker AND Kubernetes",
            "filters": {"skills": ["Docker", "Kubernetes"]}
        }
    )
    saved_search_id = search_response.json()["id"]

    resume = Resume(
        filename="devops_engineer.pdf",
        file_path="/test/devops.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    alert = SearchAlert(
        saved_search_id=saved_search_id,
        resume_id=resume.id,
        is_sent=False,
    )
    test_db.add(alert)
    await test_db.commit()
    await test_db.refresh(alert)

    # Send notification
    result = send_search_alert_notification(
        alert_id=str(alert.id),
        saved_search_id=str(saved_search_id),
        resume_id=str(resume.id),
        recipient_email="recruiter@example.com",
    )

    assert result["status"] == "sent"
    assert result["alert_id"] == str(alert.id)
    assert result["recipient"] == "recruiter@example.com"
    assert "sent_at" in result
    assert "processing_time_ms" in result


@pytest.mark.asyncio
async def test_list_saved_searches(client: AsyncClient, test_db: AsyncSession):
    """Test listing all saved searches."""
    # Create multiple saved searches
    searches = [
        {
            "name": "Python Developers",
            "query": "Python",
            "filters": {"skills": ["Python"]}
        },
        {
            "name": "Java Developers",
            "query": "Java",
            "filters": {"skills": ["Java"]}
        },
        {
            "name": "Go Developers",
            "query": "Go",
            "filters": {"skills": ["Go"]}
        },
    ]

    for search in searches:
        response = await client.post("/api/saved-searches/", json=search)
        assert response.status_code == 201

    # List all saved searches
    response = await client.get("/api/saved-searches/")
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert "saved_searches" in data
    assert data["total"] >= 3

    search_names = {s["name"] for s in data["saved_searches"]}
    assert "Python Developers" in search_names
    assert "Java Developers" in search_names
    assert "Go Developers" in search_names


@pytest.mark.asyncio
async def test_get_saved_search_by_id(client: AsyncClient, test_db: AsyncSession):
    """Test retrieving a specific saved search by ID."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Frontend Developers",
            "query": "React OR Vue",
            "filters": {"skills": ["React", "Vue", "TypeScript"]}
        }
    )
    assert create_response.status_code == 201
    search_id = create_response.json()["id"]

    # Get the saved search by ID
    get_response = await client.get(f"/api/saved-searches/{search_id}")
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["id"] == search_id
    assert data["name"] == "Frontend Developers"
    assert data["query"] == "React OR Vue"
    assert data["filters"]["skills"] == ["React", "Vue", "TypeScript"]


@pytest.mark.asyncio
async def test_update_saved_search(client: AsyncClient, test_db: AsyncSession):
    """Test updating a saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Backend Developers",
            "query": "Python",
            "filters": {"skills": ["Python"]}
        }
    )
    assert create_response.status_code == 201
    search_id = create_response.json()["id"]

    # Update the saved search
    update_response = await client.put(
        f"/api/saved-searches/{search_id}",
        json={
            "name": "Senior Backend Developers",
            "filters": {
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "min_experience_years": 5
            }
        }
    )
    assert update_response.status_code == 200

    data = update_response.json()
    assert data["id"] == search_id
    assert data["name"] == "Senior Backend Developers"
    assert data["filters"]["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert data["filters"]["min_experience_years"] == 5


@pytest.mark.asyncio
async def test_delete_saved_search(client: AsyncClient, test_db: AsyncSession):
    """Test deleting a saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Temporary Search",
            "query": "Test",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    search_id = create_response.json()["id"]

    # Delete the saved search
    delete_response = await client.delete(f"/api/saved-searches/{search_id}")
    assert delete_response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(f"/api/saved-searches/{search_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_alerts_cascade_delete(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that search alerts are cascade deleted when saved search is deleted."""
    # Create saved search
    search_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Test Search",
            "query": "Test",
            "filters": {"skills": ["Python"]}
        }
    )
    saved_search_id = search_response.json()["id"]

    # Create resume and alert
    resume = Resume(
        filename="test.pdf",
        file_path="/test.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    alert = SearchAlert(
        saved_search_id=saved_search_id,
        resume_id=resume.id,
        is_sent=False,
    )
    test_db.add(alert)
    await test_db.commit()
    await test_db.refresh(alert)

    alert_id = alert.id

    # Delete the saved search
    delete_response = await client.delete(f"/api/saved-searches/{saved_search_id}")
    assert delete_response.status_code == 204

    # Verify alert is cascade deleted
    stmt = select(SearchAlert).where(SearchAlert.id == alert_id)
    result = await test_db.execute(stmt)
    deleted_alert = result.scalar_one_or_none()

    assert deleted_alert is None, "Alert should be cascade deleted"
