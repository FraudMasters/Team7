"""
Shared pytest configuration and fixtures for backend tests.

This module provides:
1. Custom test markers for categorizing tests
2. Common fixtures for database, HTTP client, and sample data
3. Test configuration and utilities

Markers:
    - unit: Fast, isolated tests that don't use external resources
    - integration: Tests that verify interaction between components
    - slow: Tests that take >1 second to run (e.g., I/O, network)
    - e2e: End-to-end tests that verify complete user workflows
    - property: Property-based tests using hypothesis for fuzz testing
    - contract: Contract tests verifying API/service interfaces
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Import application modules
from main import app
from database import get_db, Base
from config import settings

# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.

    This function is called once at the start of the test run.
    It registers all custom markers used throughout the test suite.
    """
    config.addinivalue_line(
        "markers",
        "unit: Marks tests as unit tests (fast, isolated, no external resources)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Marks tests as integration tests (component interaction)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "e2e: Marks tests as end-to-end tests (complete user workflows)"
    )
    config.addinivalue_line(
        "markers",
        "property: Marks tests as property-based tests (hypothesis fuzzing)"
    )
    config.addinivalue_line(
        "markers",
        "contract: Marks tests as contract tests (API/service interface verification)"
    )
    config.addinivalue_line(
        "markers",
        "performance: Marks tests as performance tests (response time, throughput)"
    )


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an instance of the default event loop for the test session.

    This fixture ensures that all async tests use the same event loop,
    which is necessary for certain database operations.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """
    Create a test database engine.

    Uses in-memory SQLite for fast test execution.
    The engine is created fresh for each test function.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL query debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    This fixture provides a clean database session for each test.
    Changes are automatically rolled back at the end of the test.

    Usage:
        async def test_something(test_db: AsyncSession):
            result = await test_db.execute(select(Model))
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        # Begin a transaction that will be rolled back
        async with session.begin():
            yield session

            # Rollback all changes at the end of the test
            await session.rollback()


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client with database override.

    This fixture provides an AsyncClient for making HTTP requests to the test app.
    The database dependency is overridden to use the test database.

    Usage:
        async def test_api_endpoint(client: AsyncClient):
            response = await client.get("/api/endpoint")
            assert response.status_code == 200
    """
    async def override_get_db():
        yield test_db

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create async HTTP client
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:
        yield ac

    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers(client: AsyncClient) -> dict:
    """
    Create authentication headers for API requests.

    This fixture provides a helper to get authenticated headers.
    Override this fixture in your test module to implement actual authentication.

    Returns:
        dict: Headers dict with Authorization token
    """
    return {"Authorization": "Bearer test_token"}


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def sample_user(test_db: AsyncSession):
    """
    Create a sample user for testing.

    This fixture creates a test user with default attributes.
    Override in specific tests to customize user properties.

    Returns:
        User: The created user object
    """
    from models.user import User
    from models.organization import Organization

    # Create organization
    org = Organization(
        name="Test Organization",
        slug="test-org",
    )
    test_db.add(org)
    await test_db.flush()

    # Create user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        organization_id=org.id,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    return user


@pytest.fixture(scope="function")
async def sample_vacancy(test_db: AsyncSession, sample_user):
    """
    Create a sample vacancy for testing.

    Returns:
        Vacancy: The created vacancy object
    """
    from models.vacancy import Vacancy

    vacancy = Vacancy(
        title="Senior Python Developer",
        description="Test vacancy description",
        location="Remote",
        salary_min=80000,
        salary_max=120000,
        currency="USD",
        created_by_id=sample_user.id,
    )
    test_db.add(vacancy)
    await test_db.commit()
    await test_db.refresh(vacancy)

    return vacancy


@pytest.fixture(scope="function")
async def sample_resume(test_db: AsyncSession, sample_user):
    """
    Create a sample resume for testing.

    Returns:
        Resume: The created resume object
    """
    from models.resume import Resume, ResumeStatus
    from models.resume_analysis import ResumeAnalysis
    from models.hiring_stage import HiringStage, HiringStageName

    resume = Resume(
        filename="test_resume.pdf",
        file_path="/test/test_resume.pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Test resume content with Python, Django, FastAPI skills",
        location="Remote",
        uploaded_by_id=sample_user.id,
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    # Create analysis
    analysis = ResumeAnalysis(
        resume_id=resume.id,
        raw_text=resume.raw_text,
        skills=["Python", "Django", "FastAPI"],
        total_experience_months=60,
        education=[{"degree": "B.Sc", "field": "Computer Science"}],
        language="en",
        quality_score=85.0,
    )
    test_db.add(analysis)

    # Create hiring stage
    stage = HiringStage(
        resume_id=resume.id,
        stage_name=HiringStageName.APPLIED.value,
    )
    test_db.add(stage)

    await test_db.commit()
    await test_db.refresh(resume)

    return resume


@pytest.fixture(scope="function")
async def sample_candidates(test_db: AsyncSession, sample_user):
    """
    Create multiple sample candidates with varied attributes for testing.

    This fixture creates 5 candidates with different:
    - Skills (backend, frontend, data science, DevOps, mobile)
    - Experience levels (junior to senior)
    - Locations
    - Education levels

    Returns:
        list[Resume]: List of created resume objects
    """
    from models.resume import Resume, ResumeStatus
    from models.resume_analysis import ResumeAnalysis
    from models.hiring_stage import HiringStage, HiringStageName

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
            uploaded_by_id=sample_user.id,
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
# File and Temp Directory Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files.

    The directory and its contents are automatically cleaned up after the test.

    Usage:
        def test_with_temp_file(temp_dir: Path):
            test_file = temp_dir / "test.txt"
            test_file.write_text("content")
            assert test_file.exists()
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def sample_resume_file(temp_dir: Path) -> Path:
    """
    Create a sample resume PDF file for testing.

    Returns:
        Path: Path to the created PDF file
    """
    resume_path = temp_dir / "sample_resume.pdf"
    # Create a minimal valid PDF
    resume_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
                           b"2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n"
                           b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\n"
                           b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n"
                           b"trailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF")
    return resume_path


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def mock_settings():
    """
    Provide mocked settings for testing.

    Override specific settings values in your test:
        def test_with_custom_settings(mock_settings):
            mock_settings.SECRET_KEY = "test-secret"
            # Run test with custom setting
    """
    return settings


@pytest.fixture(scope="function")
async def clear_redis():
    """
    Clear Redis test database before and after test.

    Use this fixture when testing Redis-dependent functionality.
    Ensure you have a separate Redis database for testing.
    """
    # Import here to avoid errors if Redis is not installed
    try:
        import redis
        from config import settings

        # Connect to test Redis database
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=15,  # Use separate DB for tests
            decode_responses=True
        )

        # Clear before test
        await r.flushdb()

        yield r

        # Clear after test
        await r.flushdb()
        await r.close()

    except ImportError:
        pytest.skip("Redis not installed")


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def performance_thresholds():
    """
    Define performance thresholds for API endpoints.

    Returns:
        dict: Mapping of endpoint names to max response time (ms)
    """
    return {
        "search": 2000,  # Search should complete in < 2 seconds
        "upload": 5000,  # Upload should complete in < 5 seconds
        "ranking": 3000,  # Ranking should complete in < 3 seconds
        "default": 1000,  # Default threshold for other endpoints
    }


@pytest.fixture(scope="function")
def track_performance(performance_thresholds):
    """
    Context manager to track and assert API performance.

    Usage:
        async def test_api_performance(client, track_performance):
            async with track_performance("search") as tracker:
                response = await client.post("/api/search", json={...})
                # Performance is automatically asserted
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def _track(endpoint_name: str):
        threshold = performance_thresholds.get(
            endpoint_name,
            performance_thresholds["default"]
        )
        start_time = time.time()

        yield {
            "start_time": start_time,
            "endpoint": endpoint_name,
            "threshold": threshold,
        }

        elapsed = time.time() - start_time
        elapsed_ms = elapsed * 1000

        assert elapsed_ms <= threshold, (
            f"{endpoint_name} took {elapsed_ms:.2f}ms, "
            f"exceeding threshold of {threshold}ms"
        )

    return _track
