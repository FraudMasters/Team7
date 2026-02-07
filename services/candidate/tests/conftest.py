"""
Shared pytest configuration and fixtures for candidate service tests.

This module provides:
1. Custom test markers for categorizing tests
2. Common fixtures for database, HTTP client, and sample data
3. Test configuration and utilities
"""
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from models.base import Base
from models.candidate import Candidate, CandidateStatus
from models.candidate_note import CandidateNote
from models.candidate_tag import CandidateTag
from models.candidate_activity import CandidateActivity, CandidateActivityType

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


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
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
# Sample Data Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def sample_candidate_tag(test_db: AsyncSession):
    """
    Create a sample candidate tag for testing.

    Returns:
        CandidateTag: The created tag object
    """
    tag = CandidateTag(
        id=uuid4(),
        organization_id=str(uuid4()),
        tag_name="High Priority",
        color="#EF4444",
        is_active=True,
        tag_order=0,
    )
    test_db.add(tag)
    await test_db.commit()
    await test_db.refresh(tag)
    return tag


@pytest.fixture(scope="function")
async def sample_candidate(test_db: AsyncSession, sample_candidate_tag):
    """
    Create a sample candidate for testing.

    Returns:
        Candidate: The created candidate object
    """
    resume_id = uuid4()
    candidate = Candidate(
        id=uuid4(),
        resume_id=resume_id,
        full_name="Ivan Ivanov",
        email="ivan@example.com",
        phone="+79001234567",
        current_position="Senior Python Developer",
        current_company="Tech Corp",
        years_of_experience=8,
        expected_salary="150000-200000",
        location="Moscow",
        linkedin_url="https://linkedin.com/in/ivanivanov",
        portfolio_url="https://ivanivanov.dev",
        source="LinkedIn",
        status=CandidateStatus.NEW,
        tags=[str(sample_candidate_tag.id)],
        rating=5,
        is_active=True,
        notes_count=0,
    )
    test_db.add(candidate)
    await test_db.commit()
    await test_db.refresh(candidate)
    return candidate


@pytest.fixture(scope="function")
async def sample_candidates(test_db: AsyncSession):
    """
    Create multiple sample candidates with varied attributes for testing.

    This fixture creates 5 candidates with different:
    - Skills (backend, frontend, data science, DevOps, mobile)
    - Experience levels (junior to senior)
    - Locations
    - Statuses

    Returns:
        list[Candidate]: List of created candidate objects
    """
    candidates_data = [
        {
            "full_name": "John Doe",
            "email": "john@example.com",
            "current_position": "Senior Python Developer",
            "current_company": "Tech Corp",
            "years_of_experience": 8,
            "location": "Remote",
            "status": CandidateStatus.INTERVIEW,
            "rating": 5,
        },
        {
            "full_name": "Jane Smith",
            "email": "jane@example.com",
            "current_position": "Fullstack Developer",
            "current_company": "Startup Inc",
            "years_of_experience": 5,
            "location": "New York",
            "status": CandidateStatus.SCREENING,
            "rating": 4,
        },
        {
            "full_name": "Bob Johnson",
            "email": "bob@example.com",
            "current_position": "Junior Developer",
            "current_company": "Web Agency",
            "years_of_experience": 2,
            "location": "San Francisco",
            "status": CandidateStatus.NEW,
            "rating": 3,
        },
        {
            "full_name": "Alice Williams",
            "email": "alice@example.com",
            "current_position": "Data Scientist",
            "current_company": "Data Co",
            "years_of_experience": 6,
            "location": "Remote",
            "status": CandidateStatus.TECHNICAL,
            "rating": 5,
        },
        {
            "full_name": "Charlie Brown",
            "email": "charlie@example.com",
            "current_position": "DevOps Engineer",
            "current_company": "Cloud Corp",
            "years_of_experience": 4,
            "location": "London",
            "status": CandidateStatus.OFFER,
            "rating": 4,
        },
    ]

    candidates = []
    for data in candidates_data:
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            **data,
            is_active=True,
            notes_count=0,
        )
        test_db.add(candidate)
        candidates.append(candidate)

    await test_db.commit()
    for candidate in candidates:
        await test_db.refresh(candidate)

    return candidates


@pytest.fixture(scope="function")
async def sample_candidate_note(test_db: AsyncSession, sample_candidate):
    """
    Create a sample candidate note for testing.

    Returns:
        CandidateNote: The created note object
    """
    note = CandidateNote(
        id=uuid4(),
        candidate_id=sample_candidate.id,
        recruiter_id=uuid4(),
        content="Strong technical skills, good culture fit",
        is_private=False,
        is_pinned=False,
    )
    test_db.add(note)
    await test_db.commit()
    await test_db.refresh(note)
    return note


@pytest.fixture(scope="function")
async def sample_candidate_activity(test_db: AsyncSession, sample_candidate):
    """
    Create a sample candidate activity for testing.

    Returns:
        CandidateActivity: The created activity object
    """
    activity = CandidateActivity(
        id=uuid4(),
        activity_type=CandidateActivityType.STAGE_CHANGED,
        candidate_id=sample_candidate.id,
        from_stage=CandidateStatus.NEW.value,
        to_stage=CandidateStatus.SCREENING.value,
        recruiter_id=uuid4(),
        reason="Passed initial resume screen",
        activity_data={"interview_date": "2024-01-15"},
    )
    test_db.add(activity)
    await test_db.commit()
    await test_db.refresh(activity)
    return activity
