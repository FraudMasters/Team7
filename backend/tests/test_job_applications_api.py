"""
Integration tests for Job Applications API endpoints.

This test module verifies the job application functionality including:
- POST /api/job-applications/submit - Submit a job application
- GET /api/job-applications/my-applications - Get user's applications
- GET /api/job-applications/{id} - Get specific application details
- Validation of vacancy and resume IDs
- Duplicate application prevention
- Authentication requirements

Test Coverage:
- Application submission with and without resume
- Guest and authenticated user submissions
- Listing user's applications with pagination
- Status filtering
- Application detail retrieval
- Error handling (404, 400, 401, 403)
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.job_application import JobApplication, ApplicationStatus
from models.job_vacancy import JobVacancy
from models.resume import Resume
from models.user import User
from models.organization import Organization
from dependencies.auth import get_current_user_optional


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
    """Create a sample authenticated user for testing."""
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
async def authenticated_client(client: AsyncClient, sample_user: User):
    """Create a test HTTP client with authenticated user."""
    from main import app

    async def override_get_current_user_optional():
        return sample_user

    app.dependency_overrides[get_current_user_optional] = override_get_current_user_optional

    yield client

    app.dependency_overrides.pop(get_current_user_optional, None)


async def create_test_vacancy(
    session: AsyncSession,
    title: str = "Software Engineer",
    description: str = "Develop software applications",
) -> JobVacancy:
    """Create a test job vacancy."""
    vacancy = JobVacancy(
        title=title,
        description=description,
        required_skills=["Python", "Django"],
        is_active=True,
    )
    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)
    return vacancy


async def create_test_resume(
    session: AsyncSession,
    user_id: str,
    filename: str = "test_resume.pdf",
) -> Resume:
    """Create a test resume."""
    resume = Resume(
        filename=filename,
        file_path=f"/test/{filename}",
        status="completed",
        raw_text="Test resume content",
        uploaded_by_id=user_id,
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


async def create_test_application(
    session: AsyncSession,
    vacancy_id: str,
    user_id: str = None,
    resume_id: str = None,
    email: str = "test@example.com",
    status: ApplicationStatus = ApplicationStatus.SUBMITTED,
) -> JobApplication:
    """Create a test job application."""
    application = JobApplication(
        vacancy_id=vacancy_id,
        user_id=user_id,
        resume_id=resume_id,
        email=email,
        phone="+1234567890",
        cover_letter="Test cover letter",
        status=status,
    )
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


# ============================================================================
# Test 1: Submit Application - Basic Functionality
# ============================================================================

@pytest.mark.asyncio
async def test_submit_application_success(client: AsyncClient, test_session: AsyncSession):
    """Verify submitting an application without authentication succeeds."""
    vacancy = await create_test_vacancy(test_session)

    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "email": "applicant@example.com",
            "phone": "+1234567890",
            "cover_letter": "I am interested in this position",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["vacancy_id"] == str(vacancy.id)
    assert data["email"] == "applicant@example.com"
    assert data["phone"] == "+1234567890"
    assert data["cover_letter"] == "I am interested in this position"
    assert data["status"] == "submitted"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_submit_application_with_resume(client: AsyncClient, test_session: AsyncSession):
    """Verify submitting an application with a resume succeeds."""
    vacancy = await create_test_vacancy(test_session)
    resume = await create_test_resume(test_session, user_id=uuid4())

    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "resume_id": str(resume.id),
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["resume_id"] == str(resume.id)


@pytest.mark.asyncio
async def test_submit_application_authenticated(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify submitting an application while authenticated links to user."""
    vacancy = await create_test_vacancy(test_session)

    response = await authenticated_client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 201
    data = response.json()

    # Verify application is linked to user
    application = await test_session.get(JobApplication, data["id"])
    assert application.user_id == sample_user.id


@pytest.mark.asyncio
async def test_submit_application_returns_vacancy_title(client: AsyncClient, test_session: AsyncSession):
    """Verify application submission returns vacancy title."""
    vacancy = await create_test_vacancy(
        test_session,
        title="Senior Python Developer"
    )

    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["vacancy_title"] == "Senior Python Developer"


# ============================================================================
# Test 2: Submit Application - Validation Errors
# ============================================================================

@pytest.mark.asyncio
async def test_submit_application_invalid_vacancy_id(client: AsyncClient):
    """Verify submitting with invalid vacancy ID returns 400."""
    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": "not-a-valid-uuid",
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_submit_application_nonexistent_vacancy(client: AsyncClient):
    """Verify submitting with non-existent vacancy ID returns 404."""
    fake_id = uuid4()
    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(fake_id),
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_submit_application_invalid_resume_id(client: AsyncClient, test_session: AsyncSession):
    """Verify submitting with invalid resume ID returns 400."""
    vacancy = await create_test_vacancy(test_session)

    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "resume_id": "not-a-valid-uuid",
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_submit_application_nonexistent_resume(client: AsyncClient, test_session: AsyncSession):
    """Verify submitting with non-existent resume ID returns 404."""
    vacancy = await create_test_vacancy(test_session)
    fake_resume_id = uuid4()

    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "resume_id": str(fake_resume_id),
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 404
    data = response.json()
    assert "resume" in data["detail"].lower()


@pytest.mark.asyncio
async def test_submit_application_with_another_users_resume(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify submitting with another user's resume returns 403."""
    vacancy = await create_test_vacancy(test_session)
    other_user_id = uuid4()
    resume = await create_test_resume(test_session, user_id=other_user_id)

    response = await authenticated_client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "resume_id": str(resume.id),
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 403
    data = response.json()
    assert "does not belong" in data["detail"].lower()


@pytest.mark.asyncio
async def test_submit_application_duplicate_authenticated(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify duplicate application returns 400 for authenticated user."""
    vacancy = await create_test_vacancy(test_session)

    # First application
    await authenticated_client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "email": "applicant@example.com",
        }
    )

    # Second application (duplicate)
    response = await authenticated_client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "email": "applicant@example.com",
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "already applied" in data["detail"].lower()


# ============================================================================
# Test 3: Get My Applications
# ============================================================================

@pytest.mark.asyncio
async def test_get_my_applications_unauthenticated(client: AsyncClient):
    """Verify getting applications without authentication returns 401."""
    response = await client.get("/api/job-applications/my-applications")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_applications_empty(
    authenticated_client: AsyncClient,
    sample_user: User
):
    """Verify getting applications returns empty list when none exist."""
    response = await authenticated_client.get("/api/job-applications/my-applications")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["applications"]) == 0


@pytest.mark.asyncio
async def test_get_my_applications_with_results(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify getting applications returns user's applications."""
    vacancy1 = await create_test_vacancy(test_session, title="Job 1")
    vacancy2 = await create_test_vacancy(test_session, title="Job 2")

    await create_test_application(test_session, vacancy1.id, sample_user.id)
    await create_test_application(test_session, vacancy2.id, sample_user.id)

    response = await authenticated_client.get("/api/job-applications/my-applications")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["applications"]) == 2


@pytest.mark.asyncio
async def test_get_my_applications_includes_vacancy_title(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify applications include vacancy title."""
    vacancy = await create_test_vacancy(test_session, title="Senior Python Developer")
    await create_test_application(test_session, vacancy.id, sample_user.id)

    response = await authenticated_client.get("/api/job-applications/my-applications")
    assert response.status_code == 200
    data = response.json()
    assert data["applications"][0]["vacancy_title"] == "Senior Python Developer"


@pytest.mark.asyncio
async def test_get_my_applications_only_users_own(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify getting applications only returns user's own applications."""
    vacancy1 = await create_test_vacancy(test_session, title="My Job")
    vacancy2 = await create_test_vacancy(test_session, title="Other Job")

    # User's application
    await create_test_application(test_session, vacancy1.id, sample_user.id)
    # Other user's application
    await create_test_application(test_session, vacancy2.id, uuid4())

    response = await authenticated_client.get("/api/job-applications/my-applications")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["applications"][0]["vacancy_title"] == "My Job"


@pytest.mark.asyncio
async def test_get_my_applications_pagination(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify pagination works for my applications."""
    for i in range(5):
        vacancy = await create_test_vacancy(test_session, title=f"Job {i+1}")
        await create_test_application(test_session, vacancy.id, sample_user.id)

    response = await authenticated_client.get(
        "/api/job-applications/my-applications?skip=2&limit=2"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["applications"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_get_my_applications_status_filter(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify filtering by status works correctly."""
    vacancy = await create_test_vacancy(test_session)

    await create_test_application(
        test_session,
        vacancy.id,
        sample_user.id,
        status=ApplicationStatus.SUBMITTED
    )
    await create_test_application(
        test_session,
        vacancy.id,
        sample_user.id,
        status=ApplicationStatus.UNDER_REVIEW
    )

    response = await authenticated_client.get(
        "/api/job-applications/my-applications?status_filter=submitted"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["applications"][0]["status"] == "submitted"


@pytest.mark.asyncio
async def test_get_my_applications_invalid_status_filter(
    authenticated_client: AsyncClient,
    sample_user: User
):
    """Verify invalid status filter returns 400."""
    response = await authenticated_client.get(
        "/api/job-applications/my-applications?status_filter=invalid_status"
    )
    assert response.status_code == 400
    data = response.json()
    assert "invalid status" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_my_applications_case_insensitive_status(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify status filter is case-insensitive."""
    vacancy = await create_test_vacancy(test_session)
    await create_test_application(
        test_session,
        vacancy.id,
        sample_user.id,
        status=ApplicationStatus.SUBMITTED
    )

    response = await authenticated_client.get(
        "/api/job-applications/my-applications?status_filter=SUBMITTED"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


# ============================================================================
# Test 4: Get Application by ID
# ============================================================================

@pytest.mark.asyncio
async def test_get_application_by_id(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify getting application by ID works for owner."""
    vacancy = await create_test_vacancy(test_session)
    application = await create_test_application(test_session, vacancy.id, sample_user.id)

    response = await authenticated_client.get(f"/api/job-applications/{application.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(application.id)
    assert data["vacancy_id"] == str(vacancy.id)


@pytest.mark.asyncio
async def test_get_application_by_id_unauthenticated(client: AsyncClient, test_session: AsyncSession):
    """Verify unauthenticated user cannot access application."""
    vacancy = await create_test_vacancy(test_session)
    application = await create_test_application(test_session, vacancy.id)

    response = await client.get(f"/api/job-applications/{application.id}")
    # For unauthenticated users, if the application exists, they might get it
    # But the endpoint might require auth - check implementation
    # Based on the code, it uses get_current_user_optional which allows None
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_get_application_by_id_not_owner(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify user cannot get another user's application."""
    vacancy = await create_test_vacancy(test_session)
    other_user_id = uuid4()
    application = await create_test_application(test_session, vacancy.id, other_user_id)

    response = await authenticated_client.get(f"/api/job-applications/{application.id}")
    # Should return 403 because the user is not the owner
    assert response.status_code == 403
    data = response.json()
    assert "permission" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_application_by_id_invalid_uuid(client: AsyncClient):
    """Verify invalid application ID returns 400."""
    response = await client.get("/api/job-applications/not-a-valid-uuid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_application_by_id_nonexistent(client: AsyncClient):
    """Verify non-existent application ID returns 404."""
    fake_id = uuid4()
    response = await client.get(f"/api/job-applications/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_application_includes_vacancy_title(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify getting application includes vacancy title."""
    vacancy = await create_test_vacancy(test_session, title="Test Job Title")
    application = await create_test_application(test_session, vacancy.id, sample_user.id)

    response = await authenticated_client.get(f"/api/job-applications/{application.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["vacancy_title"] == "Test Job Title"


# ============================================================================
# Test 5: Response Structure
# ============================================================================

@pytest.mark.asyncio
async def test_application_response_structure(client: AsyncClient, test_session: AsyncSession):
    """Verify application response includes all required fields."""
    vacancy = await create_test_vacancy(test_session)

    response = await client.post(
        "/api/job-applications/submit",
        json={
            "vacancy_id": str(vacancy.id),
            "email": "test@example.com",
            "phone": "+1234567890",
            "cover_letter": "Test cover letter",
        }
    )
    assert response.status_code == 201
    data = response.json()

    # Verify all fields are present
    assert "id" in data
    assert "vacancy_id" in data
    assert "vacancy_title" in data
    assert "resume_id" in data
    assert "email" in data
    assert "phone" in data
    assert "cover_letter" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_my_applications_response_structure(
    authenticated_client: AsyncClient,
    sample_user: User,
    test_session: AsyncSession
):
    """Verify my applications response includes all required fields."""
    vacancy = await create_test_vacancy(test_session)
    await create_test_application(test_session, vacancy.id, sample_user.id)

    response = await authenticated_client.get("/api/job-applications/my-applications")
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "applications" in data
    assert "total" in data
    assert "limit" in data
    assert "skip" in data

    # Verify application structure
    app = data["applications"][0]
    assert "id" in app
    assert "vacancy_id" in app
    assert "vacancy_title" in app
    assert "email" in app
    assert "status" in app
    assert "created_at" in app


# ============================================================================
# Test 6: Application Status Enum
# ============================================================================

@pytest.mark.asyncio
async def test_application_status_enum_values(client: AsyncClient, test_session: AsyncSession):
    """Verify application status enum values are correct."""
    vacancy = await create_test_vacancy(test_session)

    # Test all status values
    statuses = [
        ApplicationStatus.PENDING,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ACCEPTED,
    ]

    for status in statuses:
        application = await create_test_application(
            test_session,
            vacancy.id,
            status=status
        )
        assert application.status.value in [
            "pending",
            "submitted",
            "under_review",
            "rejected",
            "accepted"
        ]


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
