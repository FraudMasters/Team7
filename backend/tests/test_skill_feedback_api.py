"""
Unit Tests for Skill Feedback API Endpoints

This test module performs comprehensive verification of the skill feedback API endpoints,
including CRUD operations, validation, filtering, and error handling.

Test Coverage:
- Create feedback entries (single and batch)
- List feedback with all filter combinations
- Get specific feedback by ID
- Update feedback entries
- Delete feedback entries
- UUID validation for all ID parameters
- Confidence score validation (0-1 range)
- Empty feedback list validation
- Database error handling
- 404 Not Found scenarios
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from database import get_db, Base
from models.skill_feedback import SkillFeedback


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


# Helper function to create test feedback entries
async def create_test_feedback(session: AsyncSession, **kwargs) -> SkillFeedback:
    """Create a test feedback entry with default or provided values."""
    defaults = {
        "resume_id": uuid4(),
        "vacancy_id": uuid4(),
        "match_result_id": uuid4(),
        "skill": "Python",
        "was_correct": True,
        "confidence_score": 0.95,
        "recruiter_correction": None,
        "actual_skill": None,
        "feedback_source": "api",
        "processed": False,
        "extra_metadata": None,
    }
    defaults.update(kwargs)

    feedback = SkillFeedback(**defaults)
    session.add(feedback)
    await session.commit()
    await session.refresh(feedback)
    return feedback


# ============================================================================
# Test 1: Create Feedback - POST /
# ============================================================================


@pytest.mark.asyncio
async def test_create_single_feedback_success(client: AsyncClient, test_session: AsyncSession):
    """Verify creating a single feedback entry succeeds."""
    resume_id = str(uuid4())
    vacancy_id = str(uuid4())

    payload = {
        "feedback": [
            {
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "skill": "Python",
                "was_correct": True,
                "confidence_score": 0.95,
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_count"] == 1
    assert len(data["feedback"]) == 1
    assert data["feedback"][0]["skill"] == "Python"
    assert data["feedback"][0]["was_correct"] is True
    assert data["feedback"][0]["confidence_score"] == 0.95
    assert data["feedback"][0]["processed"] is False
    assert "id" in data["feedback"][0]
    assert "created_at" in data["feedback"][0]


@pytest.mark.asyncio
async def test_create_batch_feedback_success(client: AsyncClient, test_session: AsyncSession):
    """Verify creating multiple feedback entries in a batch succeeds."""
    resume_id = str(uuid4())
    vacancy_id = str(uuid4())

    payload = {
        "feedback": [
            {
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "skill": "Python",
                "was_correct": True,
                "confidence_score": 0.95,
            },
            {
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "skill": "Django",
                "was_correct": False,
                "confidence_score": 0.80,
                "recruiter_correction": "Should be Flask",
            },
            {
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "skill": "React",
                "was_correct": True,
                "confidence_score": 0.92,
            },
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_count"] == 3
    assert len(data["feedback"]) == 3
    assert data["feedback"][0]["skill"] == "Python"
    assert data["feedback"][1]["skill"] == "Django"
    assert data["feedback"][2]["skill"] == "React"


@pytest.mark.asyncio
async def test_create_feedback_with_optional_fields(client: AsyncClient, test_session: AsyncSession):
    """Verify creating feedback with all optional fields succeeds."""
    resume_id = str(uuid4())
    vacancy_id = str(uuid4())
    match_result_id = str(uuid4())

    payload = {
        "feedback": [
            {
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "match_result_id": match_result_id,
                "skill": "Python",
                "was_correct": False,
                "confidence_score": 0.85,
                "recruiter_correction": "Should be Java",
                "actual_skill": "Java",
                "feedback_source": "frontend",
                "extra_metadata": {"context": "Resume parsing", "section": "Skills"},
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_count"] == 1
    assert data["feedback"][0]["recruiter_correction"] == "Should be Java"
    assert data["feedback"][0]["actual_skill"] == "Java"
    assert data["feedback"][0]["feedback_source"] == "frontend"
    assert data["feedback"][0]["extra_metadata"]["context"] == "Resume parsing"


@pytest.mark.asyncio
async def test_create_feedback_empty_list(client: AsyncClient):
    """Verify creating feedback with empty list returns 422 error."""
    payload = {"feedback": []}

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "At least one feedback entry must be provided" in data["detail"]


@pytest.mark.asyncio
async def test_create_feedback_invalid_uuid(client: AsyncClient):
    """Verify creating feedback with invalid UUID returns 422 error."""
    payload = {
        "feedback": [
            {
                "resume_id": "invalid-uuid",
                "vacancy_id": str(uuid4()),
                "skill": "Python",
                "was_correct": True,
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid UUID format" in data["detail"]


@pytest.mark.asyncio
async def test_create_feedback_confidence_score_out_of_range_high(client: AsyncClient):
    """Verify creating feedback with confidence score > 1 returns 422 error."""
    payload = {
        "feedback": [
            {
                "resume_id": str(uuid4()),
                "vacancy_id": str(uuid4()),
                "skill": "Python",
                "was_correct": True,
                "confidence_score": 1.5,
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_create_feedback_confidence_score_out_of_range_low(client: AsyncClient):
    """Verify creating feedback with confidence score < 0 returns 422 error."""
    payload = {
        "feedback": [
            {
                "resume_id": str(uuid4()),
                "vacancy_id": str(uuid4()),
                "skill": "Python",
                "was_correct": True,
                "confidence_score": -0.1,
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_create_feedback_confidence_score_boundary_values(client: AsyncClient, test_session: AsyncSession):
    """Verify creating feedback with confidence score at boundaries (0 and 1) succeeds."""
    resume_id = str(uuid4())
    vacancy_id = str(uuid4())

    payload = {
        "feedback": [
            {
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "skill": "Python",
                "was_correct": True,
                "confidence_score": 0.0,
            },
            {
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "skill": "Java",
                "was_correct": True,
                "confidence_score": 1.0,
            },
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_count"] == 2
    assert data["feedback"][0]["confidence_score"] == 0.0
    assert data["feedback"][1]["confidence_score"] == 1.0


# ============================================================================
# Test 2: List Feedback - GET /
# ============================================================================


@pytest.mark.asyncio
async def test_list_feedback_empty(client: AsyncClient, test_session: AsyncSession):
    """Verify listing feedback returns empty list when no feedback exists."""
    response = await client.get("/api/feedback/")
    assert response.status_code == 200
    data = response.json()
    assert "feedback" in data
    assert data["total_count"] == 0
    assert len(data["feedback"]) == 0


@pytest.mark.asyncio
async def test_list_feedback_returns_all(client: AsyncClient, test_session: AsyncSession):
    """Verify listing feedback returns all feedback entries."""
    await create_test_feedback(test_session, skill="Python")
    await create_test_feedback(test_session, skill="Java")
    await create_test_feedback(test_session, skill="React")

    response = await client.get("/api/feedback/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 3
    assert len(data["feedback"]) == 3


@pytest.mark.asyncio
async def test_list_feedback_filter_by_resume_id(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering feedback by resume ID returns only matching entries."""
    resume_id = uuid4()
    other_resume_id = uuid4()
    vacancy_id = uuid4()

    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, skill="Python")
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, skill="Java")
    await create_test_feedback(test_session, resume_id=other_resume_id, vacancy_id=vacancy_id, skill="React")

    response = await client.get(f"/api/feedback/?resume_id={resume_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for entry in data["feedback"]:
        assert entry["resume_id"] == str(resume_id)


@pytest.mark.asyncio
async def test_list_feedback_filter_by_vacancy_id(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering feedback by vacancy ID returns only matching entries."""
    resume_id = uuid4()
    vacancy_id = uuid4()
    other_vacancy_id = uuid4()

    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, skill="Python")
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, skill="Java")
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=other_vacancy_id, skill="React")

    response = await client.get(f"/api/feedback/?vacancy_id={vacancy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for entry in data["feedback"]:
        assert entry["vacancy_id"] == str(vacancy_id)


@pytest.mark.asyncio
async def test_list_feedback_filter_by_skill(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering feedback by skill name returns only matching entries."""
    resume_id = uuid4()
    vacancy_id = uuid4()

    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, skill="Python")
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, skill="Python")
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, skill="Java")

    response = await client.get("/api/feedback/?skill=Python")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for entry in data["feedback"]:
        assert entry["skill"] == "Python"


@pytest.mark.asyncio
async def test_list_feedback_filter_by_was_correct(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering feedback by correctness returns only matching entries."""
    resume_id = uuid4()
    vacancy_id = uuid4()

    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, was_correct=True)
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, was_correct=True)
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, was_correct=False)

    response = await client.get("/api/feedback/?was_correct=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for entry in data["feedback"]:
        assert entry["was_correct"] is True


@pytest.mark.asyncio
async def test_list_feedback_filter_by_processed(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering feedback by processed status returns only matching entries."""
    resume_id = uuid4()
    vacancy_id = uuid4()

    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, processed=False)
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, processed=False)
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, processed=True)

    response = await client.get("/api/feedback/?processed=false")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for entry in data["feedback"]:
        assert entry["processed"] is False


@pytest.mark.asyncio
async def test_list_feedback_filter_by_feedback_source(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering feedback by feedback source returns only matching entries."""
    resume_id = uuid4()
    vacancy_id = uuid4()

    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, feedback_source="api")
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, feedback_source="api")
    await create_test_feedback(test_session, resume_id=resume_id, vacancy_id=vacancy_id, feedback_source="frontend")

    response = await client.get("/api/feedback/?feedback_source=api")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for entry in data["feedback"]:
        assert entry["feedback_source"] == "api"


@pytest.mark.asyncio
async def test_list_feedback_filter_multiple(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering feedback with multiple filters returns only matching entries."""
    resume_id = uuid4()
    vacancy_id = uuid4()

    await create_test_feedback(
        test_session,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        skill="Python",
        was_correct=True,
        processed=False,
    )
    await create_test_feedback(
        test_session,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        skill="Python",
        was_correct=False,
        processed=False,
    )
    await create_test_feedback(
        test_session,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        skill="Java",
        was_correct=True,
        processed=False,
    )

    response = await client.get(
        f"/api/feedback/?resume_id={resume_id}&skill=Python&was_correct=true&processed=false"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["feedback"][0]["skill"] == "Python"
    assert data["feedback"][0]["was_correct"] is True
    assert data["feedback"][0]["processed"] is False


@pytest.mark.asyncio
async def test_list_feedback_invalid_resume_id_uuid(client: AsyncClient):
    """Verify listing feedback with invalid resume ID UUID returns 422 error."""
    response = await client.get("/api/feedback/?resume_id=invalid-uuid")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid resume_id UUID format" in data["detail"]


@pytest.mark.asyncio
async def test_list_feedback_invalid_vacancy_id_uuid(client: AsyncClient):
    """Verify listing feedback with invalid vacancy ID UUID returns 422 error."""
    response = await client.get("/api/feedback/?vacancy_id=invalid-uuid")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid vacancy_id UUID format" in data["detail"]


# ============================================================================
# Test 3: Get Feedback by ID - GET /{feedback_id}
# ============================================================================


@pytest.mark.asyncio
async def test_get_feedback_by_id_success(client: AsyncClient, test_session: AsyncSession):
    """Verify getting a specific feedback entry by ID succeeds."""
    feedback = await create_test_feedback(test_session, skill="Python")

    response = await client.get(f"/api/feedback/{feedback.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["skill"] == "Python"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_feedback_by_id_not_found(client: AsyncClient, test_session: AsyncSession):
    """Verify getting a non-existent feedback entry returns 404 error."""
    non_existent_id = uuid4()

    response = await client.get(f"/api/feedback/{non_existent_id}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Feedback entry not found" in data["detail"]


@pytest.mark.asyncio
async def test_get_feedback_by_id_invalid_uuid(client: AsyncClient):
    """Verify getting feedback with invalid UUID returns 422 error."""
    response = await client.get("/api/feedback/invalid-uuid")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid feedback_id UUID format" in data["detail"]


# ============================================================================
# Test 4: Update Feedback - PUT /{feedback_id}
# ============================================================================


@pytest.mark.asyncio
async def test_update_feedback_was_correct(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback's was_correct field succeeds."""
    feedback = await create_test_feedback(test_session, was_correct=True)

    update_payload = {"was_correct": False}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["was_correct"] is False


@pytest.mark.asyncio
async def test_update_feedback_confidence_score(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback's confidence score succeeds."""
    feedback = await create_test_feedback(test_session, confidence_score=0.95)

    update_payload = {"confidence_score": 0.75}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["confidence_score"] == 0.75


@pytest.mark.asyncio
async def test_update_feedback_recruiter_correction(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback's recruiter correction succeeds."""
    feedback = await create_test_feedback(test_session, recruiter_correction=None)

    update_payload = {"recruiter_correction": "Should be Django not Flask"}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["recruiter_correction"] == "Should be Django not Flask"


@pytest.mark.asyncio
async def test_update_feedback_actual_skill(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback's actual skill succeeds."""
    feedback = await create_test_feedback(test_session, actual_skill=None)

    update_payload = {"actual_skill": "Django"}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["actual_skill"] == "Django"


@pytest.mark.asyncio
async def test_update_feedback_processed(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback's processed status succeeds."""
    feedback = await create_test_feedback(test_session, processed=False)

    update_payload = {"processed": True}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["processed"] is True


@pytest.mark.asyncio
async def test_update_feedback_extra_metadata(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback's extra metadata succeeds."""
    feedback = await create_test_feedback(test_session, extra_metadata=None)

    update_payload = {"extra_metadata": {"note": "Updated by recruiter", "context": "Review"}}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["extra_metadata"]["note"] == "Updated by recruiter"


@pytest.mark.asyncio
async def test_update_feedback_multiple_fields(client: AsyncClient, test_session: AsyncSession):
    """Verify updating multiple feedback fields at once succeeds."""
    feedback = await create_test_feedback(
        test_session,
        was_correct=True,
        confidence_score=0.95,
        processed=False,
    )

    update_payload = {
        "was_correct": False,
        "confidence_score": 0.65,
        "processed": True,
        "recruiter_correction": "Incorrect skill match",
    }

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["was_correct"] is False
    assert data["confidence_score"] == 0.65
    assert data["processed"] is True
    assert data["recruiter_correction"] == "Incorrect skill match"


@pytest.mark.asyncio
async def test_update_feedback_not_found(client: AsyncClient, test_session: AsyncSession):
    """Verify updating a non-existent feedback entry returns 404 error."""
    non_existent_id = uuid4()

    update_payload = {"was_correct": False}

    response = await client.put(f"/api/feedback/{non_existent_id}", json=update_payload)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Feedback entry not found" in data["detail"]


@pytest.mark.asyncio
async def test_update_feedback_invalid_uuid(client: AsyncClient):
    """Verify updating feedback with invalid UUID returns 422 error."""
    update_payload = {"was_correct": False}

    response = await client.put("/api/feedback/invalid-uuid", json=update_payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid feedback_id UUID format" in data["detail"]


@pytest.mark.asyncio
async def test_update_feedback_confidence_score_out_of_range(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback with invalid confidence score returns 422 error."""
    feedback = await create_test_feedback(test_session, confidence_score=0.95)

    update_payload = {"confidence_score": 1.5}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Confidence score must be between 0 and 1" in data["detail"]


# ============================================================================
# Test 5: Delete Feedback - DELETE /{feedback_id}
# ============================================================================


@pytest.mark.asyncio
async def test_delete_feedback_success(client: AsyncClient, test_session: AsyncSession):
    """Verify deleting a feedback entry succeeds."""
    feedback = await create_test_feedback(test_session, skill="Python")

    response = await client.delete(f"/api/feedback/{feedback.id}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert str(feedback.id) in data["message"]
    assert "deleted successfully" in data["message"]

    # Verify the feedback is actually deleted
    get_response = await client.get(f"/api/feedback/{feedback.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_feedback_not_found(client: AsyncClient, test_session: AsyncSession):
    """Verify deleting a non-existent feedback entry returns 404 error."""
    non_existent_id = uuid4()

    response = await client.delete(f"/api/feedback/{non_existent_id}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Feedback entry not found" in data["detail"]


@pytest.mark.asyncio
async def test_delete_feedback_invalid_uuid(client: AsyncClient):
    """Verify deleting feedback with invalid UUID returns 422 error."""
    response = await client.delete("/api/feedback/invalid-uuid")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "Invalid feedback_id UUID format" in data["detail"]


# ============================================================================
# Test 6: Edge Cases and Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_create_feedback_without_confidence_score(client: AsyncClient, test_session: AsyncSession):
    """Verify creating feedback without confidence score succeeds."""
    payload = {
        "feedback": [
            {
                "resume_id": str(uuid4()),
                "vacancy_id": str(uuid4()),
                "skill": "Python",
                "was_correct": True,
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_count"] == 1
    assert data["feedback"][0]["confidence_score"] is None


@pytest.mark.asyncio
async def test_list_feedback_no_matches(client: AsyncClient, test_session: AsyncSession):
    """Verify listing feedback with filters that match no entries returns empty list."""
    await create_test_feedback(test_session, skill="Python")

    response = await client.get("/api/feedback/?skill=Nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0
    assert len(data["feedback"]) == 0


@pytest.mark.asyncio
async def test_update_feedback_empty_payload(client: AsyncClient, test_session: AsyncSession):
    """Verify updating feedback with empty payload succeeds (no changes)."""
    feedback = await create_test_feedback(test_session, skill="Python", was_correct=True)

    update_payload = {}

    response = await client.put(f"/api/feedback/{feedback.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(feedback.id)
    assert data["skill"] == "Python"
    assert data["was_correct"] is True


@pytest.mark.asyncio
async def test_create_feedback_with_null_match_result_id(client: AsyncClient, test_session: AsyncSession):
    """Verify creating feedback with null match_result_id succeeds."""
    payload = {
        "feedback": [
            {
                "resume_id": str(uuid4()),
                "vacancy_id": str(uuid4()),
                "match_result_id": None,
                "skill": "Python",
                "was_correct": True,
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_count"] == 1
    assert data["feedback"][0]["match_result_id"] is None


@pytest.mark.asyncio
async def test_feedback_timestamps_auto_generated(client: AsyncClient, test_session: AsyncSession):
    """Verify feedback entries have auto-generated timestamps."""
    payload = {
        "feedback": [
            {
                "resume_id": str(uuid4()),
                "vacancy_id": str(uuid4()),
                "skill": "Python",
                "was_correct": True,
            }
        ]
    }

    response = await client.post("/api/feedback/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["feedback"][0]["created_at"] is not None
    assert data["feedback"][0]["updated_at"] is not None

    # Verify timestamps are valid ISO format
    from datetime import datetime
    datetime.fromisoformat(data["feedback"][0]["created_at"])
    datetime.fromisoformat(data["feedback"][0]["updated_at"])
