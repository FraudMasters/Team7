"""
API Tests for Vacancy Audit Logging

This test module verifies that all vacancy CRUD operations (create, view, update, delete)
generate proper audit log entries in the database.

Test Coverage:
- VACANCY_CREATED: Creating a new vacancy creates an audit log with after_value
- VACANCY_VIEWED: Viewing a vacancy creates an audit log entry
- VACANCY_UPDATED: Updating a vacancy creates an audit log with before_value and after_value
- VACANCY_DELETED: Deleting a vacancy creates an audit log with before_value
"""
from typing import AsyncGenerator
from uuid import UUID

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
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
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


# ============================================================================
# Test 1: VACANCY_CREATED Audit Log
# ============================================================================

@pytest.mark.asyncio
async def test_create_vacancy_creates_audit_log(client: AsyncClient, test_session: AsyncSession):
    """Verify that creating a vacancy creates an audit log entry with after_value."""
    vacancy_data = {
        "title": "Software Engineer",
        "description": "Develop and maintain software applications",
        "required_skills": ["Python", "FastAPI", "SQL"],
        "min_experience_months": 36,
        "location": "Remote",
        "salary_min": 80000,
        "salary_max": 120000,
    }

    response = await client.post("/api/vacancies/", json=vacancy_data)

    assert response.status_code == 200
    vacancy = response.json()
    vacancy_id = vacancy["id"]

    # Verify audit log was created
    await test_session.commit()

    stmt = select(AuditLog).where(
        AuditLog.action_type == AuditActionType.VACANCY_CREATED,
        AuditLog.entity_type == "vacancy",
        AuditLog.entity_id == UUID(vacancy_id)
    )
    result = await test_session.execute(stmt)
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, "Audit log not found for vacancy creation"
    assert audit_log.after_value is not None, "after_value should be captured for create"
    assert audit_log.after_value.get("title") == "Software Engineer"
    assert audit_log.after_value.get("required_skills") == ["Python", "FastAPI", "SQL"]

    print(f"✓ Vacancy creation created audit log: {audit_log.id}")


# ============================================================================
# Test 2: VACANCY_VIEWED Audit Log
# ============================================================================

@pytest.mark.asyncio
async def test_view_vacancy_creates_audit_log(client: AsyncClient, test_session: AsyncSession):
    """Verify that viewing a vacancy creates an audit log entry."""
    # First create a vacancy
    vacancy_data = {
        "title": "Data Scientist",
        "description": "Analyze data and build ML models",
        "required_skills": ["Python", "Machine Learning"],
    }
    create_response = await client.post("/api/vacancies/", json=vacancy_data)
    vacancy_id = create_response.json()["id"]

    # View the vacancy
    response = await client.get(f"/api/vacancies/{vacancy_id}")
    assert response.status_code == 200

    # Verify audit log was created
    await test_session.commit()

    stmt = select(AuditLog).where(
        AuditLog.action_type == AuditActionType.VACANCY_VIEWED,
        AuditLog.entity_type == "vacancy",
        AuditLog.entity_id == UUID(vacancy_id)
    )
    result = await test_session.execute(stmt)
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, "Audit log not found for vacancy view"
    assert audit_log.action_data is not None

    print(f"✓ Vacancy view created audit log: {audit_log.id}")


# ============================================================================
# Test 3: VACANCY_UPDATED Audit Log
# ============================================================================

@pytest.mark.asyncio
async def test_update_vacancy_creates_audit_log(client: AsyncClient, test_session: AsyncSession):
    """Verify that updating a vacancy creates an audit log with before_value and after_value."""
    # Create a vacancy
    vacancy_data = {
        "title": "Junior Developer",
        "description": "Entry-level development position",
        "required_skills": ["Python"],
        "min_experience_months": 12,
    }
    create_response = await client.post("/api/vacancies/", json=vacancy_data)
    vacancy_id = create_response.json()["id"]

    # Update the vacancy
    update_data = {
        "title": "Senior Developer",
        "description": "Experienced developer position",
        "min_experience_months": 60,
    }
    update_response = await client.put(f"/api/vacancies/{vacancy_id}", json=update_data)
    assert update_response.status_code == 200

    # Verify audit log was created
    await test_session.commit()

    stmt = select(AuditLog).where(
        AuditLog.action_type == AuditActionType.VACANCY_UPDATED,
        AuditLog.entity_type == "vacancy",
        AuditLog.entity_id == UUID(vacancy_id)
    )
    result = await test_session.execute(stmt)
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, "Audit log not found for vacancy update"
    assert audit_log.before_value is not None, "before_value should be captured for update"
    assert audit_log.after_value is not None, "after_value should be captured for update"
    assert audit_log.before_value.get("title") == "Junior Developer"
    assert audit_log.after_value.get("title") == "Senior Developer"
    assert audit_log.before_value.get("min_experience_months") == 12
    assert audit_log.after_value.get("min_experience_months") == 60

    print(f"✓ Vacancy update created audit log with before/after values: {audit_log.id}")


# ============================================================================
# Test 4: VACANCY_DELETED Audit Log
# ============================================================================

@pytest.mark.asyncio
async def test_delete_vacancy_creates_audit_log(client: AsyncClient, test_session: AsyncSession):
    """Verify that deleting a vacancy creates an audit log with before_value."""
    # Create a vacancy
    vacancy_data = {
        "title": "DevOps Engineer",
        "description": "Manage CI/CD pipelines and infrastructure",
        "required_skills": ["Docker", "Kubernetes", "AWS"],
        "location": "Remote",
    }
    create_response = await client.post("/api/vacancies/", json=vacancy_data)
    vacancy_id = create_response.json()["id"]

    # Delete the vacancy
    response = await client.delete(f"/api/vacancies/{vacancy_id}")
    assert response.status_code == 200

    # Verify audit log was created with before_value
    await test_session.commit()

    stmt = select(AuditLog).where(
        AuditLog.action_type == AuditActionType.VACANCY_DELETED,
        AuditLog.entity_type == "vacancy",
        AuditLog.entity_id == UUID(vacancy_id)
    )
    result = await test_session.execute(stmt)
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, "Audit log not found for vacancy delete"
    assert audit_log.before_value is not None, "before_value should be captured for delete"
    assert "title" in audit_log.before_value
    assert audit_log.before_value["title"] == "DevOps Engineer"
    assert "required_skills" in audit_log.before_value
    assert audit_log.before_value["required_skills"] == ["Docker", "Kubernetes", "AWS"]
    assert "created_at" in audit_log.before_value

    print(f"✓ Vacancy delete created audit log with before_value: {audit_log.id}")


# ============================================================================
# Test 5: Multiple Operations on Same Vacancy
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_vacancy_operations_create_distinct_audit_logs(
    client: AsyncClient,
    test_session: AsyncSession
):
    """Verify that multiple operations on the same vacancy create distinct audit log entries."""
    # Create a vacancy
    vacancy_data = {
        "title": "Product Manager",
        "description": "Lead product development initiatives",
        "required_skills": ["Agile", "Roadmapping"],
    }
    create_response = await client.post("/api/vacancies/", json=vacancy_data)
    vacancy_id = create_response.json()["id"]

    # View the vacancy
    await client.get(f"/api/vacancies/{vacancy_id}")

    # Update the vacancy
    update_data = {
        "title": "Senior Product Manager",
        "min_experience_months": 48,
    }
    await client.put(f"/api/vacancies/{vacancy_id}", json=update_data)

    # View again
    await client.get(f"/api/vacancies/{vacancy_id}")

    # Verify all audit logs were created
    await test_session.commit()

    stmt = select(AuditLog).where(
        AuditLog.entity_type == "vacancy",
        AuditLog.entity_id == UUID(vacancy_id)
    ).order_by(AuditLog.created_at)

    result = await test_session.execute(stmt)
    audit_logs = result.scalars().all()

    assert len(audit_logs) == 4, f"Expected 4 audit logs, got {len(audit_logs)}"

    # Verify action types in order
    action_types = [log.action_type for log in audit_logs]
    assert AuditActionType.VACANCY_CREATED in action_types
    assert action_types.count(AuditActionType.VACANCY_VIEWED) == 2
    assert AuditActionType.VACANCY_UPDATED in action_types

    print(f"✓ Multiple operations created {len(audit_logs)} distinct audit logs")


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
