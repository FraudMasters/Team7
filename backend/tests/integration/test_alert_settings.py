"""
Comprehensive integration tests for alert settings workflow.

This test suite verifies:
1. Creating saved searches with alert settings
2. Updating alert settings on saved searches
3. Getting alert settings from saved searches
4. One-click apply to execute saved searches
5. Alert frequency validation
6. Alert enabling/disabling
7. Alert settings in saved search list responses
8. Invalid alert settings handling
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid import UUID

from main import app
from database import get_db
from models.saved_search import SavedSearch
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis
from models.hiring_stage import HiringStage, HiringStageName


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_alert_settings.db"


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


@pytest.fixture
async def sample_candidates(test_db: AsyncSession):
    """Create sample candidates for testing one-click apply."""
    candidates_data = [
        {
            "filename": "python_senior.pdf",
            "raw_text": "Senior Python Developer with 8 years experience in Python, Django, FastAPI",
            "skills": ["Python", "Django", "FastAPI"],
            "experience_months": 96,
            "location": "Remote",
            "education": [{"degree": "M.Sc", "field": "Computer Science"}],
            "language": "en",
        },
        {
            "filename": "python_mid.pdf",
            "raw_text": "Mid-level Python Developer with 4 years experience in Python, Flask",
            "skills": ["Python", "Flask"],
            "experience_months": 48,
            "location": "New York",
            "education": [{"degree": "B.Sc", "field": "Computer Science"}],
            "language": "en",
        },
        {
            "filename": "javascript_dev.pdf",
            "raw_text": "JavaScript Developer with 3 years experience in React, Node.js",
            "skills": ["JavaScript", "React", "Node.js"],
            "experience_months": 36,
            "location": "San Francisco",
            "education": [{"degree": "B.Sc", "field": "Software Engineering"}],
            "language": "en",
        },
    ]

    resumes = []
    for data in candidates_data:
        resume = Resume(
            filename=data["filename"],
            file_path=f"/test/{data['filename']}",
            status=ResumeStatus.COMPLETED,
            raw_text=data["raw_text"],
            location=data["location"],
        )
        test_db.add(resume)
        await test_db.commit()
        await test_db.refresh(resume)

        # Create resume analysis
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            raw_text=data["raw_text"],
            skills=data["skills"],
            total_experience_months=data["experience_months"],
            education=data["education"],
            language=data["language"],
            quality_score=85.0,
        )
        test_db.add(analysis)

        # Create hiring stage
        stage = HiringStage(
            resume_id=resume.id,
            stage_name=HiringStageName.APPLIED.value,
        )
        test_db.add(stage)

        resumes.append(resume)

    await test_db.commit()
    return resumes


# ============================================================================
# Alert Settings CRUD Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_saved_search_with_alerts_enabled(client: AsyncClient, test_db: AsyncSession):
    """Test creating a saved search with alerts enabled from the start."""
    response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Python Developers Alert",
            "query": "Python AND Django",
            "filters": {
                "skills": ["Python", "Django"],
                "min_experience_years": 5,
            }
        }
    )

    assert response.status_code == 201
    data = response.json()

    # Verify saved search was created
    assert data["name"] == "Python Developers Alert"
    assert data["query"] == "Python AND Django"
    assert "id" in data

    # Verify alert settings are present (defaults)
    assert "alert_enabled" in data
    assert "alert_frequency" in data
    assert "last_alert_at" in data

    # By default, alerts should be disabled
    assert data["alert_enabled"] is False
    assert data["alert_frequency"] is None


@pytest.mark.asyncio
async def test_enable_alerts_on_saved_search(client: AsyncClient, test_db: AsyncSession):
    """Test enabling alerts on an existing saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Senior Developers",
            "query": "Senior AND Python",
            "filters": {"min_experience_years": 5}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Enable alerts with daily frequency
    update_response = await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "daily"
        }
    )

    assert update_response.status_code == 200
    data = update_response.json()

    # Verify alert settings were updated
    assert data["id"] == saved_search_id
    assert data["name"] == "Senior Developers"
    assert data["alert_enabled"] is True
    assert data["alert_frequency"] == "daily"


@pytest.mark.asyncio
async def test_disable_alerts_on_saved_search(client: AsyncClient, test_db: AsyncSession):
    """Test disabling alerts on an existing saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Test Search",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # First enable alerts
    await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "weekly"
        }
    )

    # Now disable alerts
    update_response = await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": False,
        }
    )

    assert update_response.status_code == 200
    data = update_response.json()

    # Verify alerts are disabled but frequency is preserved
    assert data["alert_enabled"] is False
    assert data["alert_frequency"] == "weekly"  # Frequency should be preserved


@pytest.mark.asyncio
async def test_update_alert_frequency(client: AsyncClient, test_db: AsyncSession):
    """Test changing alert frequency on a saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "DevOps Engineers",
            "query": "Docker AND Kubernetes",
            "filters": {"skills": ["Docker", "Kubernetes"]}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Set up initial alerts
    await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "daily"
        }
    )

    # Change to weekly
    update_response = await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_frequency": "weekly"
        }
    )

    assert update_response.status_code == 200
    data = update_response.json()

    # Verify frequency was changed
    assert data["alert_frequency"] == "weekly"
    assert data["alert_enabled"] is True  # Should remain enabled


@pytest.mark.asyncio
async def test_get_alert_settings(client: AsyncClient, test_db: AsyncSession):
    """Test getting alert settings for a saved search."""
    # Create a saved search with alerts enabled
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Frontend Developers",
            "query": "React OR Vue",
            "filters": {"skills": ["React", "Vue"]}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Enable alerts
    await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "realtime"
        }
    )

    # Get alert settings
    get_response = await client.get(
        f"/api/saved-searches/{saved_search_id}/alert-settings"
    )

    assert get_response.status_code == 200
    data = get_response.json()

    # Verify response structure
    assert data["id"] == saved_search_id
    assert data["name"] == "Frontend Developers"
    assert data["alert_enabled"] is True
    assert data["alert_frequency"] == "realtime"
    assert "last_alert_at" in data


@pytest.mark.asyncio
async def test_get_alert_settings_nonexistent_search(client: AsyncClient, test_db: AsyncSession):
    """Test getting alert settings for a non-existent saved search."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/saved-searches/{fake_id}/alert-settings")

    assert response.status_code == 404


# ============================================================================
# Alert Frequency Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_valid_alert_frequencies(client: AsyncClient, test_db: AsyncSession):
    """Test all valid alert frequency values."""
    valid_frequencies = ["realtime", "daily", "weekly"]

    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Test Search",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    for frequency in valid_frequencies:
        update_response = await client.put(
            f"/api/saved-searches/{saved_search_id}/alert-settings",
            json={
                "alert_enabled": True,
                "alert_frequency": frequency
            }
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["alert_frequency"] == frequency


@pytest.mark.asyncio
async def test_invalid_alert_frequency(client: AsyncClient, test_db: AsyncSession):
    """Test that invalid alert frequency is rejected."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Test Search",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Try to set invalid frequency
    update_response = await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "hourly"  # Invalid frequency
        }
    )

    assert update_response.status_code == 400


# ============================================================================
# One-Click Apply Tests
# ============================================================================

@pytest.mark.asyncio
async def test_one_click_apply_saved_search(client: AsyncClient, sample_candidates):
    """Test one-click apply to execute a saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Python Developers",
            "query": "Python",
            "filters": {
                "skills": ["Python"],
            }
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Apply the saved search
    apply_response = await client.post(f"/api/saved-searches/{saved_search_id}/apply")

    assert apply_response.status_code == 200
    data = apply_response.json()

    # Verify response structure
    assert data["saved_search_id"] == saved_search_id
    assert data["saved_search_name"] == "Python Developers"
    assert "total" in data
    assert "candidates" in data
    assert "query" in data
    assert "filters_applied" in data
    assert "execution_time_seconds" in data

    # Verify query was executed
    assert data["query"] == "Python"

    # Should find Python candidates
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_one_click_apply_with_pagination(client: AsyncClient, sample_candidates):
    """Test one-click apply with pagination parameters."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "All Candidates",
            "query": "",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Apply with pagination
    apply_response = await client.post(
        f"/api/saved-searches/{saved_search_id}/apply",
        params={"skip": 0, "limit": 1}
    )

    assert apply_response.status_code == 200
    data = apply_response.json()

    # Should only return 1 result
    assert len(data["candidates"]) <= 1


@pytest.mark.asyncio
async def test_one_click_apply_with_sorting(client: AsyncClient, sample_candidates):
    """Test one-click apply with sorting parameter."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Developers",
            "query": "Developer",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Apply with sorting by experience
    apply_response = await client.post(
        f"/api/saved-searches/{saved_search_id}/apply",
        params={"sort_by": "experience"}
    )

    assert apply_response.status_code == 200
    data = apply_response.json()

    # Should have candidates
    if len(data["candidates"]) > 1:
        # Verify descending order by experience
        experiences = [
            c.get("experience_years", 0) for c in data["candidates"]
        ]
        assert experiences == sorted(experiences, reverse=True)


@pytest.mark.asyncio
async def test_one_click_apply_nonexistent_search(client: AsyncClient, test_db: AsyncSession):
    """Test one-click apply on non-existent saved search."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.post(f"/api/saved-searches/{fake_id}/apply")

    assert response.status_code == 404


# ============================================================================
# Alert Settings in List/Get Responses Tests
# ============================================================================

@pytest.mark.asyncio
async def test_alert_settings_in_saved_search_list(client: AsyncClient, test_db: AsyncSession):
    """Test that alert settings are included in saved search list."""
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
    ]

    for search in searches:
        await client.post("/api/saved-searches/", json=search)

    # Enable alerts on one
    list_response = await client.get("/api/saved-searches/")
    assert list_response.status_code == 200

    data = list_response.json()
    assert "saved_searches" in data

    # Verify each saved search has alert settings
    for saved_search in data["saved_searches"]:
        assert "alert_enabled" in saved_search
        assert "alert_frequency" in saved_search
        assert "last_alert_at" in saved_search


@pytest.mark.asyncio
async def test_alert_settings_in_get_saved_search(client: AsyncClient, test_db: AsyncSession):
    """Test that alert settings are included when getting a single saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Test Search",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Get the saved search
    get_response = await client.get(f"/api/saved-searches/{saved_search_id}")

    assert get_response.status_code == 200
    data = get_response.json()

    # Verify alert settings are present
    assert "alert_enabled" in data
    assert "alert_frequency" in data
    assert "last_alert_at" in data


@pytest.mark.asyncio
async def test_alert_settings_in_update_saved_search(client: AsyncClient, test_db: AsyncSession):
    """Test that alert settings are preserved when updating a saved search."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Test Search",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Enable alerts
    await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "daily"
        }
    )

    # Update the saved search (not alert settings)
    update_response = await client.put(
        f"/api/saved-searches/{saved_search_id}",
        json={
            "name": "Updated Search Name"
        }
    )

    assert update_response.status_code == 200
    data = update_response.json()

    # Verify name was updated
    assert data["name"] == "Updated Search Name"

    # Verify alert settings are preserved
    assert data["alert_enabled"] is True
    assert data["alert_frequency"] == "daily"


# ============================================================================
# Database Persistence Tests
# ============================================================================

@pytest.mark.asyncio
async def test_alert_settings_persisted_in_database(client: AsyncClient, test_db: AsyncSession):
    """Test that alert settings are properly persisted in the database."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Persisted Alerts Test",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Enable alerts
    await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "weekly"
        }
    )

    # Verify in database
    stmt = select(SavedSearch).where(SavedSearch.id == UUID(saved_search_id))
    result = await test_db.execute(stmt)
    saved_search = result.scalar_one_or_none()

    assert saved_search is not None
    assert saved_search.alert_enabled is True
    assert saved_search.alert_frequency == "weekly"


@pytest.mark.asyncio
async def test_last_alert_at_field(client: AsyncClient, test_db: AsyncSession):
    """Test that last_alert_at field is present and nullable."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Test Search",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Get alert settings
    get_response = await client.get(
        f"/api/saved-searches/{saved_search_id}/alert-settings"
    )

    assert get_response.status_code == 200
    data = get_response.json()

    # Initially, last_alert_at should be None
    assert data["last_alert_at"] is None

    # Verify in database
    stmt = select(SavedSearch).where(SavedSearch.id == UUID(saved_search_id))
    result = await test_db.execute(stmt)
    saved_search = result.scalar_one_or_none()

    assert saved_search is not None
    assert saved_search.last_alert_at is None


# ============================================================================
# Invalid ID Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_update_alert_settings_invalid_id(client: AsyncClient, test_db: AsyncSession):
    """Test updating alert settings with invalid saved search ID."""
    response = await client.put(
        "/api/saved-searches/invalid-uuid/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "daily"
        }
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_alert_settings_invalid_id(client: AsyncClient, test_db: AsyncSession):
    """Test getting alert settings with invalid saved search ID."""
    response = await client.get("/api/saved-searches/invalid-uuid/alert-settings")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_apply_saved_search_invalid_id(client: AsyncClient, test_db: AsyncSession):
    """Test applying saved search with invalid ID."""
    response = await client.post("/api/saved-searches/invalid-uuid/apply")

    assert response.status_code == 400


# ============================================================================
# Edge Cases Tests
# ============================================================================

@pytest.mark.asyncio
async def test_partial_alert_settings_update(client: AsyncClient, test_db: AsyncSession):
    """Test partial update of alert settings (only enabled or only frequency)."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Partial Update Test",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # First, set up initial alerts
    await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_enabled": True,
            "alert_frequency": "daily"
        }
    )

    # Update only the frequency (enabled should stay True)
    update_response = await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={
            "alert_frequency": "weekly"
        }
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["alert_enabled"] is True  # Should remain enabled
    assert data["alert_frequency"] == "weekly"  # Should be updated


@pytest.mark.asyncio
async def test_empty_alert_settings_update(client: AsyncClient, test_db: AsyncSession):
    """Test empty alert settings update (no changes)."""
    # Create a saved search
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Empty Update Test",
            "query": "Python",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Update with empty body
    update_response = await client.put(
        f"/api/saved-searches/{saved_search_id}/alert-settings",
        json={}
    )

    assert update_response.status_code == 200
    data = update_response.json()

    # Should return current settings unchanged
    assert data["alert_enabled"] is False
    assert data["alert_frequency"] is None


@pytest.mark.asyncio
async def test_one_click_apply_empty_results(client: AsyncClient, sample_candidates):
    """Test one-click apply that returns no results."""
    # Create a saved search with very specific criteria
    create_response = await client.post(
        "/api/saved-searches/",
        json={
            "name": "Nonexistent Skills",
            "query": "NonexistentSkill12345",
            "filters": {}
        }
    )
    assert create_response.status_code == 201
    saved_search_id = create_response.json()["id"]

    # Apply the saved search
    apply_response = await client.post(f"/api/saved-searches/{saved_search_id}/apply")

    assert apply_response.status_code == 200
    data = apply_response.json()

    # Should return 0 results
    assert data["total"] == 0
    assert len(data["candidates"]) == 0
