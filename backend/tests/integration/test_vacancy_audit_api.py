"""
Test to verify audit logs API returns vacancy audit entries.

This test verifies that the audit logs API endpoint correctly filters
and returns audit log entries for vacancy operations.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.audit_log import AuditLog, AuditActionType


# Test Database Setup
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


@pytest.mark.asyncio
async def test_audit_logs_api_returns_vacancy_entries(client: AsyncClient, test_session: AsyncSession):
    """
    Verify audit logs API returns vacancy audit entries when filtered by entity_type=vacancy.

    This test:
    1. Creates a vacancy via POST to /api/vacancies/ (generates VACANCY_CREATED audit log)
    2. Queries the audit logs API with entity_type=vacancy
    3. Verifies the response contains the vacancy audit log entry
    4. Verifies response structure includes 'logs' and 'total_count' fields
    5. Verifies all returned logs have entity_type='vacancy'
    """
    # Step 1: Create a vacancy to generate audit log
    vacancy_data = {
        "title": "Software Engineer",
        "description": "Test vacancy for audit log verification",
        "requirements": "Python, FastAPI, SQLAlchemy",
        "min_experience_years": 3,
    }

    create_response = await client.post("/api/vacancies/", json=vacancy_data)
    assert create_response.status_code == 200, f"Failed to create vacancy: {create_response.text}"
    vacancy = create_response.json()
    vacancy_id = vacancy["id"]

    # Commit to ensure audit log is persisted
    await test_session.commit()

    # Step 2: Query audit logs API with entity_type=vacancy filter
    api_response = await client.get(
        "/api/audit-logs/?entity_type=vacancy&limit=10"
    )

    # Step 3: Verify response status and structure
    assert api_response.status_code == 200, f"Expected status 200, got {api_response.status_code}: {api_response.text}"
    data = api_response.json()

    # Verify response has required fields
    assert "logs" in data, "Response should have 'logs' field"
    assert "total_count" in data, "Response should have 'total_count' field"

    # Verify we have at least one audit log
    assert data["total_count"] >= 1, f"Expected at least 1 vacancy audit log, got {data['total_count']}"
    assert len(data["logs"]) >= 1, f"Expected at least 1 log entry, got {len(data['logs'])}"

    # Step 4: Verify the vacancy audit log entry is present
    vacancy_logs = [log for log in data["logs"] if log.get("entity_id") == vacancy_id]

    assert len(vacancy_logs) >= 1, f"Expected to find audit log for vacancy {vacancy_id}, but found none"

    # Get the VACANCY_CREATED log
    created_log = next((log for log in vacancy_logs if log["action_type"] == "vacancy_created"), None)

    assert created_log is not None, "Expected to find VACANCY_CREATED audit log"

    # Verify the audit log details
    assert created_log["entity_type"] == "vacancy", "entity_type should be 'vacancy'"
    assert created_log["entity_id"] == vacancy_id, f"entity_id should match vacancy_id {vacancy_id}"
    assert created_log["action_type"] == "vacancy_created", "action_type should be 'vacancy_created'"
    assert created_log["after_value"] is not None, "VACANCY_CREATED should have after_value"
    assert created_log["after_value"].get("title") == "Software Engineer", "after_value should contain vacancy title"

    print(f"✓ Audit logs API successfully returns vacancy audit entries")
    print(f"  - Total vacancy logs found: {data['total_count']}")
    print(f"  - VACANCY_CREATED log found for vacancy {vacancy_id}")
    print(f"  - Response structure verified: 'logs' and 'total_count' fields present")


@pytest.mark.asyncio
async def test_audit_logs_api_filters_vacancy_operations_only(client: AsyncClient, test_session: AsyncSession):
    """
    Verify audit logs API correctly filters to only return vacancy entries when entity_type=vacancy.

    This test creates both resume and vacancy operations, then verifies that
    filtering by entity_type=vacancy only returns vacancy audit logs.
    """
    # Create a resume (generates resume audit log)
    resume_response = await client.post(
        "/api/resumes/upload",
        files={"file": ("test_resume.pdf", b"Test resume content", "application/pdf")}
    )
    assert resume_response.status_code == 200

    # Create a vacancy (generates vacancy audit log)
    vacancy_response = await client.post(
        "/api/vacancies/",
        json={"title": "Test Vacancy", "description": "Test description"}
    )
    assert vacancy_response.status_code == 200
    vacancy_id = vacancy_response.json()["id"]

    await test_session.commit()

    # Query audit logs with entity_type=vacancy
    api_response = await client.get("/api/audit-logs/?entity_type=vacancy&limit=100")
    assert api_response.status_code == 200
    data = api_response.json()

    # Verify all returned logs have entity_type='vacancy'
    for log in data["logs"]:
        assert log["entity_type"] == "vacancy", f"All logs should have entity_type='vacancy', found {log['entity_type']}"

    # Verify our vacancy log is in the results
    vacancy_logs = [log for log in data["logs"] if log.get("entity_id") == vacancy_id]
    assert len(vacancy_logs) >= 1, "Vacancy audit log should be in filtered results"

    # Verify no resume logs are in the results
    resume_logs = [log for log in data["logs"] if log["entity_type"] == "resume"]
    assert len(resume_logs) == 0, "No resume logs should be in vacancy-filtered results"

    print(f"✓ Audit logs API correctly filters to only vacancy entries")
    print(f"  - Total vacancy logs: {data['total_count']}")
    print(f"  - No resume logs in vacancy-filtered results")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
