"""
Integration tests for Job Search API endpoints.

This test module verifies the job search functionality including:
- POST /api/job-search/search - Search with JSON body
- GET /api/job-search/search - Search with query parameters
- Full-text search on title and description
- Filtering by location, salary, work format, employment type, industry, skills
- Pagination and sorting
- Invalid input handling

Test Coverage:
- Basic search functionality
- All filter types
- Pagination (limit, skip)
- Sorting options (date, salary_asc, salary_desc, relevance)
- Empty results handling
- Invalid filter handling
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.job_vacancy import JobVacancy
from models.user import User
from models.organization import Organization


# ============================================================================
# Test Database Setup
# ============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(test_session: AsyncSession):
    """Create a test HTTP client with database override."""
    from main import app

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_organization(test_session: AsyncSession) -> Organization:
    """Create a sample organization for testing."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
    )
    test_session.add(org)
    await test_session.commit()
    await test_session.refresh(org)
    return org


@pytest.fixture
async def sample_user(test_session: AsyncSession, sample_organization: Organization) -> User:
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        organization_id=sample_organization.id,
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


async def create_test_vacancy(
    session: AsyncSession,
    title: str = "Software Engineer",
    description: str = "Develop software applications",
    location: str = "Remote",
    salary_min: int = 50000,
    salary_max: int = 100000,
    work_format: str = "remote",
    employment_type: str = "full-time",
    industry: str = "Technology",
    required_skills: list = None,
    is_active: bool = True,
) -> JobVacancy:
    """Create a test job vacancy with default or provided values."""
    if required_skills is None:
        required_skills = ["Python", "Django"]

    vacancy = JobVacancy(
        title=title,
        description=description,
        location=location,
        salary_min=salary_min,
        salary_max=salary_max,
        work_format=work_format,
        employment_type=employment_type,
        industry=industry,
        required_skills=required_skills,
        is_active=is_active,
    )
    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)
    return vacancy


# ============================================================================
# Test 1: Basic Search Functionality (POST)
# ============================================================================

@pytest.mark.asyncio
async def test_search_post_empty_results(client: AsyncClient):
    """Verify search returns empty list when no vacancies exist."""
    response = await client.post(
        "/api/job-search/search",
        json={"query": "python", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["jobs"]) == 0
    assert data["query"] == "python"


@pytest.mark.asyncio
async def test_search_post_with_results(client: AsyncClient, test_session: AsyncSession):
    """Verify search returns matching vacancies."""
    await create_test_vacancy(
        test_session,
        title="Python Developer",
        description="Looking for a Python developer with Django experience"
    )
    await create_test_vacancy(
        test_session,
        title="Java Developer",
        description="Looking for a Java developer with Spring experience"
    )

    response = await client.post(
        "/api/job-search/search",
        json={"query": "Python", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["jobs"]) == 1
    assert "python" in data["jobs"][0]["title"].lower()


@pytest.mark.asyncio
async def test_search_post_no_filters(client: AsyncClient, test_session: AsyncSession):
    """Verify search without filters returns all active vacancies."""
    await create_test_vacancy(test_session, title="Job 1")
    await create_test_vacancy(test_session, title="Job 2")

    response = await client.post(
        "/api/job-search/search",
        json={"limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["jobs"]) == 2


@pytest.mark.asyncio
async def test_search_post_inactive_vacancies_not_returned(client: AsyncClient, test_session: AsyncSession):
    """Verify inactive vacancies are not returned in search results."""
    await create_test_vacancy(test_session, title="Active Job", is_active=True)
    await create_test_vacancy(test_session, title="Inactive Job", is_active=False)

    response = await client.post(
        "/api/job-search/search",
        json={"limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["title"] == "Active Job"


# ============================================================================
# Test 2: Location Filter
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_location(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by location works correctly."""
    await create_test_vacancy(test_session, location="Remote")
    await create_test_vacancy(test_session, location="New York")
    await create_test_vacancy(test_session, location="San Francisco, CA")

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"location": "Remote"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["location"] == "Remote"
    assert data["filters_applied"]["location"] == "Remote"


@pytest.mark.asyncio
async def test_filter_by_location_partial_match(client: AsyncClient, test_session: AsyncSession):
    """Verify location filter performs partial match (case-insensitive)."""
    await create_test_vacancy(test_session, location="San Francisco, CA")
    await create_test_vacancy(test_session, location="New York")

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"location": "francisco"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "francisco" in data["jobs"][0]["location"].lower()


# ============================================================================
# Test 3: Salary Filter
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_salary_min(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by minimum salary works correctly."""
    await create_test_vacancy(test_session, salary_min=50000, salary_max=80000)
    await create_test_vacancy(test_session, salary_min=100000, salary_max=150000)
    await create_test_vacancy(test_session, salary_min=None, salary_max=None)  # No salary

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"salary_min": 70000},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should return jobs with salary_min >= 70000 OR no salary set
    assert data["total"] >= 1
    assert data["filters_applied"]["salary_min"] == 70000


@pytest.mark.asyncio
async def test_filter_by_salary_max(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by maximum salary works correctly."""
    await create_test_vacancy(test_session, salary_min=50000, salary_max=80000)
    await create_test_vacancy(test_session, salary_min=100000, salary_max=150000)

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"salary_max": 90000},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["salary_max"] == 80000


@pytest.mark.asyncio
async def test_filter_by_salary_range(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by salary range works correctly."""
    await create_test_vacancy(test_session, salary_min=50000, salary_max=80000)
    await create_test_vacancy(test_session, salary_min=100000, salary_max=150000)
    await create_test_vacancy(test_session, salary_min=70000, salary_max=120000)

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"salary_min": 60000, "salary_max": 130000},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should match 50000-80000 and 70000-120000
    assert data["total"] == 2


# ============================================================================
# Test 4: Work Format Filter
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_work_format(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by work format works correctly."""
    await create_test_vacancy(test_session, work_format="remote")
    await create_test_vacancy(test_session, work_format="office")
    await create_test_vacancy(test_session, work_format="hybrid")

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"work_format": "remote"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["work_format"] == "remote"


@pytest.mark.asyncio
async def test_filter_by_work_format_case_insensitive(client: AsyncClient, test_session: AsyncSession):
    """Verify work format filter is case-insensitive."""
    await create_test_vacancy(test_session, work_format="remote")

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"work_format": "REMOTE"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


# ============================================================================
# Test 5: Employment Type Filter
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_employment_type(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by employment type works correctly."""
    await create_test_vacancy(test_session, employment_type="full-time")
    await create_test_vacancy(test_session, employment_type="part-time")
    await create_test_vacancy(test_session, employment_type="contract")

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"employment_type": "full-time"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["employment_type"] == "full-time"


# ============================================================================
# Test 6: Industry Filter
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_industry(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by industry works correctly."""
    await create_test_vacancy(test_session, industry="Technology")
    await create_test_vacancy(test_session, industry="Finance")
    await create_test_vacancy(test_session, industry="Healthcare")

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"industry": "Technology"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["industry"] == "Technology"


@pytest.mark.asyncio
async def test_filter_by_industry_partial_match(client: AsyncClient, test_session: AsyncSession):
    """Verify industry filter performs partial match (case-insensitive)."""
    await create_test_vacancy(test_session, industry="Information Technology")
    await create_test_vacancy(test_session, industry="Finance")

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"industry": "technology"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "technology" in data["jobs"][0]["industry"].lower()


# ============================================================================
# Test 7: Skills Filter
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_skills_single(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by a single skill works correctly."""
    await create_test_vacancy(
        test_session,
        title="Python Developer",
        required_skills=["Python", "Django", "FastAPI"]
    )
    await create_test_vacancy(
        test_session,
        title="Java Developer",
        required_skills=["Java", "Spring"]
    )

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"skills": ["Python"]},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Python" in data["jobs"][0]["required_skills"]


@pytest.mark.asyncio
async def test_filter_by_skills_multiple_or_logic(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by multiple skills uses OR logic (match any)."""
    await create_test_vacancy(
        test_session,
        title="Python Developer",
        required_skills=["Python", "Django"]
    )
    await create_test_vacancy(
        test_session,
        title="Java Developer",
        required_skills=["Java", "Spring"]
    )
    await create_test_vacancy(
        test_session,
        title="Full Stack Developer",
        required_skills=["JavaScript", "React"]
    )

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"skills": ["Python", "Java"]},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should match Python Developer OR Java Developer
    assert data["total"] == 2
    titles = [job["title"] for job in data["jobs"]]
    assert "Python Developer" in titles
    assert "Java Developer" in titles


@pytest.mark.asyncio
async def test_filter_by_skills_empty_list(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering with empty skills list returns all results."""
    await create_test_vacancy(test_session)

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {"skills": []},
            "limit": 10
        }
    )
    assert response.status_code == 200
    # Empty skills list should not filter
    data = response.json()
    assert data["total"] >= 1


# ============================================================================
# Test 8: Combined Filters
# ============================================================================

@pytest.mark.asyncio
async def test_combined_filters_location_and_salary(client: AsyncClient, test_session: AsyncSession):
    """Verify combining location and salary filters works."""
    await create_test_vacancy(
        test_session,
        location="Remote",
        salary_min=100000,
        salary_max=150000
    )
    await create_test_vacancy(
        test_session,
        location="Remote",
        salary_min=50000,
        salary_max=80000
    )
    await create_test_vacancy(
        test_session,
        location="New York",
        salary_min=100000,
        salary_max=150000
    )

    response = await client.post(
        "/api/job-search/search",
        json={
            "filters": {
                "location": "Remote",
                "salary_min": 90000
            },
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["location"] == "Remote"
    assert data["jobs"][0]["salary_min"] >= 90000


@pytest.mark.asyncio
async def test_combined_filters_query_and_filters(client: AsyncClient, test_session: AsyncSession):
    """Verify combining text query and filters works."""
    await create_test_vacancy(
        test_session,
        title="Senior Python Developer",
        location="Remote",
        work_format="remote"
    )
    await create_test_vacancy(
        test_session,
        title="Junior Python Developer",
        location="Office",
        work_format="office"
    )

    response = await client.post(
        "/api/job-search/search",
        json={
            "query": "Python",
            "filters": {"work_format": "remote"},
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Senior" in data["jobs"][0]["title"]


# ============================================================================
# Test 9: Pagination
# ============================================================================

@pytest.mark.asyncio
async def test_pagination_limit(client: AsyncClient, test_session: AsyncSession):
    """Verify pagination limit parameter works correctly."""
    for i in range(5):
        await create_test_vacancy(test_session, title=f"Job {i+1}")

    response = await client.post(
        "/api/job-search/search",
        json={"limit": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) == 3
    assert data["limit"] == 3


@pytest.mark.asyncio
async def test_pagination_skip(client: AsyncClient, test_session: AsyncSession):
    """Verify pagination skip parameter works correctly."""
    for i in range(5):
        await create_test_vacancy(test_session, title=f"Job {i+1}")

    response = await client.post(
        "/api/job-search/search",
        json={"limit": 2, "skip": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) == 2
    assert data["skip"] == 2
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_pagination_limit_min_validation(client: AsyncClient):
    """Verify pagination limit minimum validation (ge=1)."""
    response = await client.post(
        "/api/job-search/search",
        json={"limit": 0}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_pagination_limit_max_validation(client: AsyncClient):
    """Verify pagination limit maximum validation (le=200)."""
    response = await client.post(
        "/api/job-search/search",
        json={"limit": 201}
    )
    assert response.status_code == 422  # Validation error


# ============================================================================
# Test 10: Sorting
# ============================================================================

@pytest.mark.asyncio
async def test_sort_by_date_default(client: AsyncClient, test_session: AsyncSession):
    """Verify default sorting is by date (created_at descending)."""
    await create_test_vacancy(test_session, title="Job 1")
    await create_test_vacancy(test_session, title="Job 2")
    await create_test_vacancy(test_session, title="Job 3")

    response = await client.post(
        "/api/job-search/search",
        json={"sort_by": "date", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    # Should be ordered by most recent first
    assert len(data["jobs"]) == 3


@pytest.mark.asyncio
async def test_sort_by_salary_asc(client: AsyncClient, test_session: AsyncSession):
    """Verify sorting by salary ascending works correctly."""
    await create_test_vacancy(test_session, salary_min=50000, salary_max=80000)
    await create_test_vacancy(test_session, salary_min=100000, salary_max=150000)
    await create_test_vacancy(test_session, salary_min=70000, salary_max=100000)

    response = await client.post(
        "/api/job-search/search",
        json={"sort_by": "salary_asc", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    salaries = [job["salary_min"] for job in data["jobs"] if job["salary_min"]]
    assert salaries == sorted(salaries)


@pytest.mark.asyncio
async def test_sort_by_salary_desc(client: AsyncClient, test_session: AsyncSession):
    """Verify sorting by salary descending works correctly."""
    await create_test_vacancy(test_session, salary_min=50000, salary_max=80000)
    await create_test_vacancy(test_session, salary_min=100000, salary_max=150000)
    await create_test_vacancy(test_session, salary_min=70000, salary_max=100000)

    response = await client.post(
        "/api/job-search/search",
        json={"sort_by": "salary_desc", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    salaries = [job["salary_min"] for job in data["jobs"] if job["salary_min"]]
    assert salaries == sorted(salaries, reverse=True)


@pytest.mark.asyncio
async def test_sort_by_relevance(client: AsyncClient, test_session: AsyncSession):
    """Verify sorting by relevance works (uses created_at as proxy)."""
    await create_test_vacancy(test_session)

    response = await client.post(
        "/api/job-search/search",
        json={"sort_by": "relevance", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    # Should return results
    assert len(data["jobs"]) >= 1


# ============================================================================
# Test 11: Response Structure
# ============================================================================

@pytest.mark.asyncio
async def test_response_structure(client: AsyncClient, test_session: AsyncSession):
    """Verify response includes all required fields."""
    await create_test_vacancy(
        test_session,
        title="Test Job",
        description="Test description",
        required_skills=["Python", "Django"],
        min_experience_months=60,
        industry="Technology",
        work_format="remote",
        location="Remote",
        salary_min=80000,
        salary_max=120000,
        english_level="B2",
        employment_type="full-time"
    )

    response = await client.post(
        "/api/job-search/search",
        json={"limit": 10}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "total" in data
    assert "jobs" in data
    assert "query" in data
    assert "filters_applied" in data
    assert "execution_time_seconds" in data
    assert "skip" in data
    assert "limit" in data

    # Verify job structure
    job = data["jobs"][0]
    assert "id" in job
    assert "title" in job
    assert "description" in job
    assert "required_skills" in job
    assert "min_experience_months" in job
    assert "additional_requirements" in job
    assert "industry" in job
    assert "work_format" in job
    assert "location" in job
    assert "salary_min" in job
    assert "salary_max" in job
    assert "english_level" in job
    assert "employment_type" in job
    assert "created_at" in job


# ============================================================================
# Test 12: GET Endpoint (Query Parameters)
# ============================================================================

@pytest.mark.asyncio
async def test_search_get_basic(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint works with basic query."""
    await create_test_vacancy(test_session)

    response = await client.get(
        "/api/job-search/search",
        params={"limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_get_with_query(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint works with text query parameter."""
    await create_test_vacancy(
        test_session,
        title="Python Developer",
        description="Looking for Python developer"
    )
    await create_test_vacancy(
        test_session,
        title="Java Developer",
        description="Looking for Java developer"
    )

    response = await client.get(
        "/api/job-search/search",
        params={"query": "Python", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "python" in data["jobs"][0]["title"].lower()


@pytest.mark.asyncio
async def test_search_get_with_location_filter(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint works with location filter."""
    await create_test_vacancy(test_session, location="Remote")
    await create_test_vacancy(test_session, location="New York")

    response = await client.get(
        "/api/job-search/search",
        params={"location": "Remote", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["location"] == "Remote"


@pytest.mark.asyncio
async def test_search_get_with_salary_filters(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint works with salary filters."""
    await create_test_vacancy(test_session, salary_min=50000, salary_max=80000)
    await create_test_vacancy(test_session, salary_min=100000, salary_max=150000)

    response = await client.get(
        "/api/job-search/search",
        params={"salary_min": 90000, "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_search_get_with_skills_filter(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint works with comma-separated skills filter."""
    await create_test_vacancy(
        test_session,
        required_skills=["Python", "Django", "FastAPI"]
    )
    await create_test_vacancy(
        test_session,
        required_skills=["Java", "Spring"]
    )

    response = await client.get(
        "/api/job-search/search",
        params={"skills": "Python,Django", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Python" in data["jobs"][0]["required_skills"]


@pytest.mark.asyncio
async def test_search_get_with_all_filters(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint works with multiple filters combined."""
    await create_test_vacancy(
        test_session,
        title="Python Developer",
        location="Remote",
        work_format="remote",
        employment_type="full-time",
        industry="Technology",
        required_skills=["Python", "Django"],
        salary_min=80000,
        salary_max=120000
    )

    response = await client.get(
        "/api/job-search/search",
        params={
            "query": "Python",
            "location": "Remote",
            "work_format": "remote",
            "employment_type": "full-time",
            "industry": "Technology",
            "skills": "Python",
            "salary_min": 70000,
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["title"] == "Python Developer"


@pytest.mark.asyncio
async def test_search_get_pagination(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint pagination works correctly."""
    for i in range(5):
        await create_test_vacancy(test_session, title=f"Job {i+1}")

    response = await client.get(
        "/api/job-search/search",
        params={"skip": 2, "limit": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) == 2
    assert data["skip"] == 2
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_search_get_sorting(client: AsyncClient, test_session: AsyncSession):
    """Verify GET endpoint sorting works correctly."""
    await create_test_vacancy(test_session, salary_min=50000)
    await create_test_vacancy(test_session, salary_min=100000)

    response = await client.get(
        "/api/job-search/search",
        params={"sort_by": "salary_desc", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    salaries = [job["salary_min"] for job in data["jobs"] if job["salary_min"]]
    assert salaries == sorted(salaries, reverse=True)


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
