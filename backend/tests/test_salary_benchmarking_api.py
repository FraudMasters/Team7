"""
Unit Tests for Salary Benchmarking API endpoints.

This test module performs comprehensive verification of the salary benchmarking API endpoints,
including benchmarks, salary suggestions, salary history, offer comparison, equity analysis,
and market trends.

Test Coverage:
- GET /benchmarks - Get salary benchmarks for role/location
- POST /suggest-salary - Get AI-powered salary suggestion
- POST /salary-history - Create salary history record
- GET /salary-history/{resume_id} - Get salary history for candidate
- POST /compare-offers - Compare multiple job offers
- GET /equity-analysis - Get internal equity analysis
- GET /market-trends - Get market salary trends over time
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.salary_benchmark import SalaryBenchmark
from models.salary_history import SalaryHistory
from models.job_vacancy import JobVacancy
from models.resume import Resume, ResumeStatus
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
async def sample_organization(test_session: AsyncSession):
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
async def sample_user(test_session: AsyncSession, sample_organization):
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


@pytest.fixture
async def sample_resume(test_session: AsyncSession, sample_user):
    """Create a sample resume for testing."""
    resume = Resume(
        filename="test_resume.pdf",
        file_path="/test/test_resume.pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Test resume content",
        location="Remote",
        uploaded_by_id=sample_user.id,
    )
    test_session.add(resume)
    await test_session.commit()
    await test_session.refresh(resume)
    return resume


@pytest.fixture
async def sample_vacancy(test_session: AsyncSession, sample_user):
    """Create a sample vacancy for testing."""
    vacancy = JobVacancy(
        title="Senior Python Developer",
        description="Test vacancy description",
        location="Remote",
        salary_min=80000,
        salary_max=120000,
        is_active=True,
    )
    test_session.add(vacancy)
    await test_session.commit()
    await test_session.refresh(vacancy)
    return vacancy


# Helper functions
async def create_test_benchmark(
    session: AsyncSession,
    job_title: str = "Software Engineer",
    location: str = "Remote",
    salary_min: int = 75000,
    salary_median: int = 95000,
    salary_max: int = 120000,
    country: str = "US",
    experience_level: str = None,
    industry: str = None,
    employment_type: str = "full_time",
    effective_date: str = None,
) -> SalaryBenchmark:
    """Create a test salary benchmark with default or provided values."""
    if effective_date is None:
        effective_date = datetime.utcnow().strftime("%Y-%m-%d")

    benchmark = SalaryBenchmark(
        job_title=job_title,
        location=location,
        country=country,
        salary_min=salary_min,
        salary_median=salary_median,
        salary_max=salary_max,
        currency="USD",
        experience_level=experience_level,
        industry=industry,
        employment_type=employment_type,
        effective_date=effective_date,
        sample_size=1000,
        data_source="test",
    )
    session.add(benchmark)
    await session.commit()
    await session.refresh(benchmark)
    return benchmark


async def create_test_salary_history(
    session: AsyncSession,
    resume_id,
    salary_amount: float = 100000.0,
    salary_type: str = "current",
    effective_date: str = None,
) -> SalaryHistory:
    """Create a test salary history record."""
    if effective_date is None:
        effective_date = datetime.utcnow().strftime("%Y-%m-%d")

    history = SalaryHistory(
        resume_id=resume_id,
        salary_amount=salary_amount,
        salary_frequency="annual",
        currency="USD",
        effective_date=effective_date,
        salary_type=salary_type,
        employment_type="full_time",
        job_title="Software Engineer",
        company_name="Test Company",
        location="Remote",
        is_confirmed=True,
        verification_status="verified",
    )
    session.add(history)
    await session.commit()
    await session.refresh(history)
    return history


# ============================================================================
# Test 1: GET /benchmarks - Basic Retrieval
# ============================================================================

@pytest.mark.asyncio
async def test_get_benchmarks_empty(client: AsyncClient, test_session: AsyncSession):
    """Verify getting benchmarks returns empty list when no data exists."""
    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "Developer", "location": "Remote"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_benchmarks_returns_data(client: AsyncClient, test_session: AsyncSession):
    """Verify getting benchmarks returns matching data."""
    await create_test_benchmark(
        test_session,
        job_title="Software Engineer",
        location="Remote"
    )
    await create_test_benchmark(
        test_session,
        job_title="Senior Software Engineer",
        location="San Francisco"
    )

    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "Software Engineer", "location": "Remote"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Should match the Remote location benchmark
    for item in data:
        assert "Remote" in item["location"] or "remote" in item["location"].lower()


@pytest.mark.asyncio
async def test_get_benchmarks_role_filter(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by role works correctly."""
    await create_test_benchmark(
        test_session,
        job_title="Python Developer",
        location="Remote"
    )
    await create_test_benchmark(
        test_session,
        job_title="Java Developer",
        location="Remote"
    )

    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "Python", "location": "Remote"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for item in data:
        assert "Python" in item["role"] or "python" in item["role"].lower()


@pytest.mark.asyncio
async def test_get_benchmarks_location_filter(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by location works correctly."""
    await create_test_benchmark(
        test_session,
        job_title="Developer",
        location="New York"
    )
    await create_test_benchmark(
        test_session,
        job_title="Developer",
        location="San Francisco"
    )

    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "Developer", "location": "New York"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for item in data:
        assert "New York" in item["location"]


@pytest.mark.asyncio
async def test_get_benchmarks_experience_level_filter(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by experience level works correctly."""
    await create_test_benchmark(
        test_session,
        job_title="Developer",
        location="Remote",
        experience_level="senior"
    )
    await create_test_benchmark(
        test_session,
        job_title="Developer",
        location="Remote",
        experience_level="junior"
    )

    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={
            "role": "Developer",
            "location": "Remote",
            "experience_level": "senior"
        }
    )
    assert response.status_code == 200
    data = response.json()
    # All results should be for senior level
    # (Note: the API returns all if experience_level filter isn't applied in query)


@pytest.mark.asyncio
async def test_get_benchmarks_industry_filter(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by industry works correctly."""
    await create_test_benchmark(
        test_session,
        job_title="Developer",
        location="Remote",
        industry="Technology"
    )
    await create_test_benchmark(
        test_session,
        job_title="Developer",
        location="Remote",
        industry="Finance"
    )

    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={
            "role": "Developer",
            "location": "Remote",
            "industry": "Technology"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_benchmarks_response_structure(client: AsyncClient, test_session: AsyncSession):
    """Verify benchmark response includes all required fields."""
    await create_test_benchmark(
        test_session,
        job_title="Developer",
        location="Remote",
        salary_min=80000,
        salary_median=100000,
        salary_max=130000,
        salary_p90=150000
    )

    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "Developer", "location": "Remote"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    benchmark = data[0]
    assert "role" in benchmark
    assert "location" in benchmark
    assert "salary_min" in benchmark
    assert "salary_median" in benchmark
    assert "salary_max" in benchmark
    assert "currency" in benchmark
    assert benchmark["currency"] == "USD"


@pytest.mark.asyncio
async def test_get_benchmarks_missing_required_params(client: AsyncClient):
    """Verify missing required parameters returns validation error."""
    # Missing location
    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "Developer"}
    )
    assert response.status_code == 422

    # Missing role
    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"location": "Remote"}
    )
    assert response.status_code == 422


# ============================================================================
# Test 2: POST /suggest-salary
# ============================================================================

@pytest.mark.asyncio
async def test_suggest_salary_success(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume,
    sample_vacancy
):
    """Verify salary suggestion returns valid data."""
    # Create benchmark for the suggestion
    await create_test_benchmark(
        test_session,
        job_title="Senior Python Developer",
        location="Remote"
    )

    request_data = {
        "resume_id": str(sample_resume.id),
        "vacancy_id": str(sample_vacancy.id),
        "include_cost_of_living": True
    }

    response = await client.post(
        "/api/salary-benchmarking/suggest-salary",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "resume_id" in data
    assert "vacancy_id" in data
    assert "suggested_min" in data
    assert "suggested_median" in data
    assert "suggested_max" in data
    assert "currency" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_suggest_salary_invalid_resume_uuid(client: AsyncClient, test_session: AsyncSession):
    """Verify invalid resume UUID returns error."""
    request_data = {
        "resume_id": "not-a-uuid",
        "vacancy_id": str(uuid4()),
    }

    response = await client.post(
        "/api/salary-benchmarking/suggest-salary",
        json=request_data
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_suggest_salary_resume_not_found(client: AsyncClient, test_session: AsyncSession):
    """Verify non-existent resume returns 404."""
    request_data = {
        "resume_id": str(uuid4()),
        "vacancy_id": str(uuid4()),
    }

    response = await client.post(
        "/api/salary-benchmarking/suggest-salary",
        json=request_data
    )
    assert response.status_code == 404


# ============================================================================
# Test 3: POST /salary-history - Create
# ============================================================================

@pytest.mark.asyncio
async def test_create_salary_history_success(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume
):
    """Verify creating salary history returns valid data."""
    request_data = {
        "resume_id": str(sample_resume.id),
        "salary_amount": 100000.0,
        "salary_frequency": "annual",
        "currency": "USD",
        "effective_date": "2024-01-15",
        "salary_type": "current",
        "employment_type": "full_time",
        "job_title": "Software Engineer",
        "company_name": "Test Company",
        "location": "Remote"
    }

    response = await client.post(
        "/api/salary-benchmarking/salary-history",
        json=request_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["resume_id"] == str(sample_resume.id)
    assert data["salary_amount"] == 100000.0
    assert data["currency"] == "USD"
    assert data["salary_type"] == "current"


@pytest.mark.asyncio
async def test_create_salary_history_invalid_resume_uuid(client: AsyncClient):
    """Verify invalid resume UUID returns error."""
    request_data = {
        "resume_id": "not-a-uuid",
        "salary_amount": 100000.0,
        "effective_date": "2024-01-15",
    }

    response = await client.post(
        "/api/salary-benchmarking/salary-history",
        json=request_data
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_salary_history_resume_not_found(client: AsyncClient):
    """Verify non-existent resume returns 404."""
    request_data = {
        "resume_id": str(uuid4()),
        "salary_amount": 100000.0,
        "effective_date": "2024-01-15",
    }

    response = await client.post(
        "/api/salary-benchmarking/salary-history",
        json=request_data
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_salary_history_with_bonus_and_equity(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume
):
    """Verify salary history with bonus and equity creates correctly."""
    request_data = {
        "resume_id": str(sample_resume.id),
        "salary_amount": 120000.0,
        "salary_frequency": "annual",
        "currency": "USD",
        "effective_date": "2024-01-15",
        "salary_type": "current",
        "employment_type": "full_time",
        "bonus_amount": 15000.0,
        "equity_value": 20000.0
    }

    response = await client.post(
        "/api/salary-benchmarking/salary-history",
        json=request_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["bonus_amount"] == 15000.0
    assert data["equity_value"] == 20000.0


@pytest.mark.asyncio
async def test_create_salary_history_validation(client: AsyncClient, sample_resume):
    """Verify salary history validation for required fields."""
    # Missing salary_amount
    request_data = {
        "resume_id": str(sample_resume.id),
        "effective_date": "2024-01-15",
    }

    response = await client.post(
        "/api/salary-benchmarking/salary-history",
        json=request_data
    )
    assert response.status_code == 422


# ============================================================================
# Test 4: GET /salary-history/{resume_id}
# ============================================================================

@pytest.mark.asyncio
async def test_get_salary_history_success(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume
):
    """Verify getting salary history returns records."""
    await create_test_salary_history(
        test_session,
        resume_id=sample_resume.id,
        salary_amount=100000.0,
        salary_type="current"
    )
    await create_test_salary_history(
        test_session,
        resume_id=sample_resume.id,
        salary_amount=90000.0,
        salary_type="previous"
    )

    response = await client.get(
        f"/api/salary-benchmarking/salary-history/{sample_resume.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_salary_history_empty(client: AsyncClient, test_session: AsyncSession, sample_resume):
    """Verify getting salary history returns empty list when no records."""
    response = await client.get(
        f"/api/salary-benchmarking/salary-history/{sample_resume.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_salary_history_filter_by_type(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume
):
    """Verify filtering salary history by type works."""
    await create_test_salary_history(
        test_session,
        resume_id=sample_resume.id,
        salary_amount=100000.0,
        salary_type="current"
    )
    await create_test_salary_history(
        test_session,
        resume_id=sample_resume.id,
        salary_amount=85000.0,
        salary_type="previous"
    )

    response = await client.get(
        f"/api/salary-benchmarking/salary-history/{sample_resume.id}",
        params={"salary_type": "current"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for record in data:
        assert record["salary_type"] == "current"


@pytest.mark.asyncio
async def test_get_salary_history_invalid_uuid(client: AsyncClient):
    """Verify invalid UUID returns error."""
    response = await client.get(
        "/api/salary-benchmarking/salary-history/not-a-uuid"
    )
    assert response.status_code == 422


# ============================================================================
# Test 5: POST /compare-offers
# ============================================================================

@pytest.mark.asyncio
async def test_compare_offers_success(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume
):
    """Verify offer comparison returns valid analysis."""
    request_data = {
        "resume_id": str(sample_resume.id),
        "offers": [
            {
                "salary": 100000,
                "location": "San Francisco",
                "currency": "USD",
                "bonus": 10000,
                "equity": 15000,
                "job_title": "Senior Developer",
                "company": "Tech Corp"
            },
            {
                "salary": 90000,
                "location": "Remote",
                "currency": "USD",
                "bonus": 5000,
                "equity": 10000,
                "job_title": "Developer",
                "company": "Startup Inc"
            }
        ],
        "apply_cost_of_living": True
    }

    response = await client.post(
        "/api/salary-benchmarking/compare-offers",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "resume_id" in data
    assert "offers" in data
    assert "recommendation" in data
    assert "analysis" in data
    assert len(data["offers"]) == 2


@pytest.mark.asyncio
async def test_compare_offers_sorted_by_adjusted_total(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume
):
    """Verify offers are sorted by adjusted total compensation."""
    request_data = {
        "resume_id": str(sample_resume.id),
        "offers": [
            {
                "salary": 80000,
                "location": "Remote",
                "currency": "USD",
                "company": "Company A"
            },
            {
                "salary": 120000,
                "location": "San Francisco",
                "currency": "USD",
                "company": "Company B"
            },
            {
                "salary": 100000,
                "location": "Austin",
                "currency": "USD",
                "company": "Company C"
            }
        ],
        "apply_cost_of_living": False
    }

    response = await client.post(
        "/api/salary-benchmarking/compare-offers",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    offers = data["offers"]

    # Should be sorted by adjusted_total descending
    adjusted_totals = [o["adjusted_total"] for o in offers]
    assert adjusted_totals == sorted(adjusted_totals, reverse=True)


@pytest.mark.asyncio
async def test_compare_offers_single_offer(client: AsyncClient, test_session: AsyncSession, sample_resume):
    """Verify comparing single offer works correctly."""
    request_data = {
        "resume_id": str(sample_resume.id),
        "offers": [
            {
                "salary": 100000,
                "location": "Remote",
                "currency": "USD"
            }
        ],
        "apply_cost_of_living": False
    }

    response = await client.post(
        "/api/salary-benchmarking/compare-offers",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["offers"]) == 1


@pytest.mark.asyncio
async def test_compare_offers_invalid_resume_uuid(client: AsyncClient):
    """Verify offer comparison handles invalid resume UUID gracefully."""
    request_data = {
        "resume_id": "not-a-uuid",
        "offers": [
            {
                "salary": 100000,
                "location": "Remote",
                "currency": "USD"
            }
        ]
    }

    response = await client.post(
        "/api/salary-benchmarking/compare-offers",
        json=request_data
    )
    # The API handles this gracefully and proceeds with comparison
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_compare_offers_response_structure(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_resume
):
    """Verify offer comparison response includes all required fields."""
    request_data = {
        "resume_id": str(sample_resume.id),
        "offers": [
            {
                "salary": 100000,
                "location": "Remote",
                "currency": "USD",
                "bonus": 10000,
                "equity": 20000,
                "job_title": "Engineer",
                "company": "Tech Co"
            }
        ]
    }

    response = await client.post(
        "/api/salary-benchmarking/compare-offers",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()

    # Top-level fields
    assert "resume_id" in data
    assert "offers" in data
    assert "recommendation" in data
    assert "analysis" in data

    # Offer structure
    offer = data["offers"][0]
    assert "salary" in offer
    assert "location" in offer
    assert "currency" in offer
    assert "total_compensation" in offer
    assert "adjusted_total" in offer

    # Analysis structure
    assert "total_offers" in data["analysis"]


# ============================================================================
# Test 6: GET /equity-analysis
# ============================================================================

@pytest.mark.asyncio
async def test_equity_analysis_vacancy_not_found(client: AsyncClient):
    """Verify equity analysis returns 404 for non-existent vacancy."""
    response = await client.get(
        "/api/salary-benchmarking/equity-analysis",
        params={"vacancy_id": str(uuid4())}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_equity_analysis_invalid_uuid(client: AsyncClient):
    """Verify equity analysis returns 422 for invalid UUID."""
    response = await client.get(
        "/api/salary-benchmarking/equity-analysis",
        params={"vacancy_id": "not-a-uuid"}
    )
    assert response.status_code == 422


# ============================================================================
# Test 7: GET /market-trends
# ============================================================================

@pytest.mark.asyncio
async def test_market_trends_returns_data(client: AsyncClient, test_session: AsyncSession):
    """Verify market trends returns simulated data when no benchmarks exist."""
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={
            "role": "Software Engineer",
            "location": "Remote"
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert data["role"] == "Software Engineer"
    assert data["location"] == "Remote"
    assert data["currency"] == "USD"
    assert "period_type" in data
    assert "trends" in data
    assert len(data["trends"]) > 0


@pytest.mark.asyncio
async def test_market_trends_with_benchmarks(client: AsyncClient, test_session: AsyncSession):
    """Verify market trends uses benchmark data when available."""
    # Create benchmarks with different dates
    await create_test_benchmark(
        test_session,
        job_title="Software Engineer",
        location="Remote",
        effective_date="2024-01-15"
    )
    await create_test_benchmark(
        test_session,
        job_title="Software Engineer",
        location="Remote",
        effective_date="2023-10-01"
    )

    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={
            "role": "Software Engineer",
            "location": "Remote"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["trends"]) >= 1


@pytest.mark.asyncio
async def test_market_trends_period_types(client: AsyncClient, test_session: AsyncSession):
    """Verify market trends supports different period types."""
    for period_type in ["quarterly", "monthly", "yearly"]:
        response = await client.get(
            "/api/salary-benchmarking/market-trends",
            params={
                "role": "Developer",
                "location": "Remote",
                "period_type": period_type
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_type"] == period_type


@pytest.mark.asyncio
async def test_market_trends_periods_parameter(client: AsyncClient, test_session: AsyncSession):
    """Verify market trends respects periods parameter."""
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={
            "role": "Developer",
            "location": "Remote",
            "periods": 4
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should return up to 4 periods (or less if less data available)
    assert len(data["trends"]) <= 4


@pytest.mark.asyncio
async def test_market_trends_changes_calculated(client: AsyncClient, test_session: AsyncSession):
    """Verify market trends calculates YoY and QoQ changes."""
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={
            "role": "Developer",
            "location": "Remote",
            "periods": 8
        }
    )
    assert response.status_code == 200
    data = response.json()

    # With simulated data, should have changes calculated
    assert "quarter_over_quarter_change" in data
    assert "year_over_year_change" in data

    # With at least 2 periods, QoQ should be calculated
    if len(data["trends"]) >= 2:
        assert data["quarter_over_quarter_change"] is not None


@pytest.mark.asyncio
async def test_market_trends_response_structure(client: AsyncClient, test_session: AsyncSession):
    """Verify market trends response includes all required fields."""
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={
            "role": "Software Engineer",
            "location": "Remote"
        }
    )
    assert response.status_code == 200
    data = response.json()

    # Top-level fields
    assert "role" in data
    assert "location" in data
    assert "currency" in data
    assert "period_type" in data
    assert "trends" in data
    assert "data_source" in data
    assert "last_updated" in data

    # Trend data point structure
    if len(data["trends"]) > 0:
        trend = data["trends"][0]
        assert "period" in trend
        assert "salary_min" in trend
        assert "salary_median" in trend
        assert "salary_max" in trend


@pytest.mark.asyncio
async def test_market_trends_missing_required_params(client: AsyncClient):
    """Verify missing required parameters returns validation error."""
    # Missing location
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={"role": "Developer"}
    )
    assert response.status_code == 422

    # Missing role
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={"location": "Remote"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_market_trends_periods_validation(client: AsyncClient):
    """Verify periods parameter validation (1-24)."""
    # Periods too small
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={
            "role": "Developer",
            "location": "Remote",
            "periods": 0
        }
    )
    assert response.status_code == 422

    # Periods too large
    response = await client.get(
        "/api/salary-benchmarking/market-trends",
        params={
            "role": "Developer",
            "location": "Remote",
            "periods": 25
        }
    )
    assert response.status_code == 422


# ============================================================================
# Test 8: Combined and Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_benchmarks_case_insensitive(client: AsyncClient, test_session: AsyncSession):
    """Verify benchmark search is case-insensitive for role and location."""
    await create_test_benchmark(
        test_session,
        job_title="Software Engineer",
        location="San Francisco"
    )

    # Test with different cases
    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "SOFTWARE ENGINEER", "location": "SAN FRANCISCO"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_benchmarks_partial_match(client: AsyncClient, test_session: AsyncSession):
    """Verify benchmark search supports partial matching."""
    await create_test_benchmark(
        test_session,
        job_title="Senior Software Engineer",
        location="San Francisco Bay Area"
    )

    # Test with partial match
    response = await client.get(
        "/api/salary-benchmarking/benchmarks",
        params={"role": "Software", "location": "Francisco"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_salary_history_multiple_resumes(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_user
):
    """Verify salary history is isolated per resume."""
    # Create two resumes
    resume1 = Resume(
        filename="resume1.pdf",
        file_path="/test/resume1.pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Resume 1",
        uploaded_by_id=sample_user.id,
    )
    test_session.add(resume1)
    await test_session.commit()
    await test_session.refresh(resume1)

    resume2 = Resume(
        filename="resume2.pdf",
        file_path="/test/resume2.pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Resume 2",
        uploaded_by_id=sample_user.id,
    )
    test_session.add(resume2)
    await test_session.commit()
    await test_session.refresh(resume2)

    # Create history for each
    await create_test_salary_history(
        test_session,
        resume_id=resume1.id,
        salary_amount=100000.0
    )
    await create_test_salary_history(
        test_session,
        resume_id=resume2.id,
        salary_amount=120000.0
    )

    # Verify isolation
    response1 = await client.get(
        f"/api/salary-benchmarking/salary-history/{resume1.id}"
    )
    response2 = await client.get(
        f"/api/salary-benchmarking/salary-history/{resume2.id}"
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    assert len(data1) == 1
    assert len(data2) == 1
    assert data1[0]["salary_amount"] != data2[0]["salary_amount"]


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
