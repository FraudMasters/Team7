"""
Comprehensive integration tests for advanced candidate search workflow.

This test suite verifies:
1. Full-text search with boolean operators (AND, OR, NOT)
2. Multi-field filtering: skills, experience, education, location, languages
3. Range filters: experience years, match score, date ranges
4. Sorting by relevance, date, experience
5. Pagination with filters
6. Search history tracking
7. Combined filters and search queries
8. Performance optimization (sub-2 second response time)
"""
import pytest
import time
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid import uuid4
from datetime import datetime, timedelta

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis
from models.hiring_stage import HiringStage, HiringStageName
from models.saved_search import SavedSearch
from models.search_history import SearchHistory


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_advanced_search.db"


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
    """Create sample candidates with various attributes for testing."""
    candidates_data = [
        {
            "filename": "john_python_senior.pdf",
            "raw_text": "John Doe - Senior Python Developer with 8 years experience in Python, Django, FastAPI, PostgreSQL",
            "skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
            "experience_months": 96,
            "location": "Remote",
            "education": [{"degree": "M.Sc", "field": "Computer Science"}],
            "language": "en",
        },
        {
            "filename": "jane_fullstack.pdf",
            "raw_text": "Jane Smith - Fullstack Developer with 5 years experience in React, Node.js, Python, MongoDB",
            "skills": ["React", "Node.js", "Python", "MongoDB"],
            "experience_months": 60,
            "location": "New York",
            "education": [{"degree": "B.Sc", "field": "Software Engineering"}],
            "language": "en",
        },
        {
            "filename": "bob_junior.pdf",
            "raw_text": "Bob Johnson - Junior Developer with 2 years experience in Python, JavaScript",
            "skills": ["Python", "JavaScript"],
            "experience_months": 24,
            "location": "San Francisco",
            "education": [{"degree": "B.Sc", "field": "Computer Science"}],
            "language": "en",
        },
        {
            "filename": "alice_data.pdf",
            "raw_text": "Alice Williams - Data Scientist with 6 years experience in Python, Machine Learning, TensorFlow, Pandas",
            "skills": ["Python", "Machine Learning", "TensorFlow", "Pandas"],
            "experience_months": 72,
            "location": "Remote",
            "education": [{"degree": "PhD", "field": "Data Science"}],
            "language": "en",
        },
        {
            "filename": "charlie_devops.pdf",
            "raw_text": "Charlie Brown - DevOps Engineer with 4 years experience in Docker, Kubernetes, AWS, CI/CD",
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "experience_months": 48,
            "location": "London",
            "education": [{"degree": "M.Sc", "field": "Information Technology"}],
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


@pytest.mark.asyncio
async def test_basic_search_with_query(client: AsyncClient, sample_candidates):
    """Test basic full-text search with a query string."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python AND Django",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "candidates" in data
    assert data["total"] >= 1
    assert len(data["candidates"]) >= 1
    assert data["query"] == "Python AND Django"
    assert "execution_time_seconds" in data


@pytest.mark.asyncio
async def test_search_with_boolean_or(client: AsyncClient, sample_candidates):
    """Test search with OR boolean operator."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "React OR Node.js",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    # Should find candidates with either React or Node.js


@pytest.mark.asyncio
async def test_search_with_boolean_not(client: AsyncClient, sample_candidates):
    """Test search with NOT boolean operator."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python NOT Django",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should find Python developers without Django
    assert "candidates" in data


@pytest.mark.asyncio
async def test_filter_by_skills(client: AsyncClient, sample_candidates):
    """Test filtering candidates by skills."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "skills": ["Python", "FastAPI"],
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    assert all("Python" in c.get("skills", []) for c in data["candidates"])


@pytest.mark.asyncio
async def test_filter_by_experience_range(client: AsyncClient, sample_candidates):
    """Test filtering candidates by experience years range."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "min_experience_years": 5,
                "max_experience_years": 8,
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify experience range
    for candidate in data["candidates"]:
        exp_years = candidate.get("experience_years")
        if exp_years is not None:
            assert 5 <= exp_years <= 8


@pytest.mark.asyncio
async def test_filter_by_location(client: AsyncClient, sample_candidates):
    """Test filtering candidates by location."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "location": "Remote",
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    # Should find remote candidates


@pytest.mark.asyncio
async def test_combined_search_and_filters(client: AsyncClient, sample_candidates):
    """Test combining full-text search with filters."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python",
            "filters": {
                "min_experience_years": 5,
                "location": "Remote",
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should find Python developers with 5+ years experience in Remote location
    assert "candidates" in data
    for candidate in data["candidates"]:
        exp_years = candidate.get("experience_years")
        if exp_years is not None:
            assert exp_years >= 5


@pytest.mark.asyncio
async def test_sort_by_relevance(client: AsyncClient, sample_candidates):
    """Test sorting search results by relevance."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python Developer",
            "sort_by": "relevance",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    # Results should be sorted by relevance (ts_rank)


@pytest.mark.asyncio
async def test_sort_by_experience(client: AsyncClient, sample_candidates):
    """Test sorting search results by experience."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "sort_by": "experience",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    if len(data["candidates"]) > 1:
        # Verify descending order by experience
        experiences = [
            c.get("experience_years", 0) for c in data["candidates"]
        ]
        assert experiences == sorted(experiences, reverse=True)


@pytest.mark.asyncio
async def test_sort_by_date(client: AsyncClient, sample_candidates):
    """Test sorting search results by date (newest first)."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "sort_by": "date",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    # Results should be sorted by created_at descending


@pytest.mark.asyncio
async def test_pagination_with_skip_and_limit(client: AsyncClient, sample_candidates):
    """Test pagination with skip and limit parameters."""
    # Get first page
    response = await client.post(
        "/api/search/candidates",
        json={
            "skip": 0,
            "limit": 2,
        }
    )

    assert response.status_code == 200
    first_page = response.json()
    assert len(first_page["candidates"]) <= 2

    # Get second page
    response = await client.post(
        "/api/search/candidates",
        json={
            "skip": 2,
            "limit": 2,
        }
    )

    assert response.status_code == 200
    second_page = response.json()
    assert len(second_page["candidates"]) <= 2

    # Verify different results
    if len(first_page["candidates"]) > 0 and len(second_page["candidates"]) > 0:
        first_ids = {c["id"] for c in first_page["candidates"]}
        second_ids = {c["id"] for c in second_page["candidates"]}
        assert first_ids != second_ids


@pytest.mark.asyncio
async def test_search_history_tracking(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test that search history is tracked after queries."""
    # Perform a search
    await client.post(
        "/api/search/candidates",
        json={
            "query": "Python Developer",
            "filters": {"min_experience_years": 5},
            "limit": 10,
        }
    )

    # Wait a bit for async processing
    await asyncio.sleep(0.1)

    # Check search history
    response = await client.get("/api/search/history?limit=10")

    assert response.status_code == 200
    data = response.json()

    assert "history" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_search_with_query_params(client: AsyncClient, sample_candidates):
    """Test GET endpoint for search with query parameters."""
    response = await client.get(
        "/api/search/candidates",
        params={
            "query": "Python",
            "min_experience_years": 5,
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_search_with_date_range_filter(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test search with date range filters."""
    # Get a candidate from sample data
    candidate = sample_candidates[0]

    # Create date range filters
    date_from = (candidate.created_at - timedelta(days=1)).isoformat()
    date_to = (candidate.created_at + timedelta(days=1)).isoformat()

    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "date_from": date_from,
                "date_to": date_to,
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data


@pytest.mark.asyncio
async def test_empty_search_results(client: AsyncClient, sample_candidates):
    """Test search that returns no results."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "NonExistentSkill12345",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["candidates"]) == 0


@pytest.mark.asyncio
async def test_search_performance(client: AsyncClient, sample_candidates):
    """Test that search completes in under 2 seconds (performance requirement)."""
    start_time = time.time()

    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python AND Developer",
            "filters": {
                "min_experience_years": 3,
                "skills": ["Python", "Django"],
            },
            "limit": 50,
        }
    )

    end_time = time.time()
    execution_time = end_time - start_time

    assert response.status_code == 200
    data = response.json()

    # Verify execution time is tracked
    assert "execution_time_seconds" in data

    # Assert search completes in under 2 seconds (requirement from spec)
    assert execution_time < 2.0, f"Search took {execution_time:.2f}s, expected < 2s"


@pytest.mark.asyncio
async def test_search_response_includes_all_fields(client: AsyncClient, sample_candidates):
    """Test that search response includes all required fields."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python",
            "limit": 1,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    required_fields = ["total", "candidates", "query", "execution_time_seconds", "skip", "limit"]
    for field in required_fields:
        assert field in data

    # Verify candidate fields
    if len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        candidate_fields = [
            "id", "filename", "status", "created_at", "updated_at",
            "current_stage", "skills", "experience_years"
        ]
        for field in candidate_fields:
            assert field in candidate


@pytest.mark.asyncio
async def test_filter_by_vacancy_id(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test filtering candidates by vacancy ID."""
    from models.vacancy import Vacancy

    # Create a test vacancy
    vacancy = Vacancy(
        title="Senior Python Developer",
        description="Test vacancy",
        location="Remote",
    )
    test_db.add(vacancy)
    await test_db.commit()
    await test_db.refresh(vacancy)

    # Associate a candidate with this vacancy
    candidate = sample_candidates[0]
    stage = HiringStage(
        resume_id=candidate.id,
        stage_name=HiringStageName.INTERVIEW.value,
        vacancy_id=vacancy.id,
    )
    test_db.add(stage)
    await test_db.commit()

    # Search for candidates in this vacancy
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "vacancy_id": str(vacancy.id),
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should find at least the candidate we added
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_filter_by_stage_id(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test filtering candidates by stage ID."""
    # Update a candidate to interview stage
    candidate = sample_candidates[0]
    stage = HiringStage(
        resume_id=candidate.id,
        stage_name=HiringStageName.INTERVIEW.value,
    )
    test_db.add(stage)
    await test_db.commit()

    # Search for candidates in interview stage
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "stage_id": "interview",
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    assert all(c["current_stage"] == "interview" for c in data["candidates"])


@pytest.mark.asyncio
async def test_invalid_filter_parameters(client: AsyncClient, sample_candidates):
    """Test that invalid filter parameters return appropriate errors."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "min_experience_years": -5,  # Invalid: negative value
            },
            "limit": 10,
        }
    )

    # Should handle gracefully (may return 400 or 200 with empty results)
    assert response.status_code in [200, 400]


# Import asyncio for sleep
import asyncio
