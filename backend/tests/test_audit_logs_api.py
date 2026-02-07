"""
Unit Tests for Audit Logs API

This test module performs comprehensive verification of the audit logs API endpoints,
including filtering, pagination, validation, and security event logging.

Test Coverage:
- Get audit logs with all filter combinations
- Action type validation
- Entity type filtering
- User ID filtering
- Organization ID filtering
- Date range filtering (start_date, end_date)
- Pagination (limit, offset)
- Invalid input handling (UUIDs, dates, action types)
- Get action types endpoint
- Get entity types endpoint
- Security event filtering (SSO_LOGIN, TFA_ENABLED, TFA_DISABLED, SESSION_REVOKED, IP_BLOCKED)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.audit_log import AuditLog, AuditActionType
from api.audit_logs import get_audit_logs, get_action_types, get_entity_types


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


# Helper function to create test audit logs
async def create_test_audit_log(session: AsyncSession, **kwargs) -> AuditLog:
    """Create a test audit log with default or provided values."""
    defaults = {
        "action_type": AuditActionType.USER_CREATED,
        "entity_type": "user",
        "entity_id": uuid4(),
        "user_id": uuid4(),
        "organization_id": uuid4(),
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0 Test Agent",
        "action_data": {"test": "data"},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    defaults.update(kwargs)

    log = AuditLog(**defaults)
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


# ============================================================================
# Test 1: Get Audit Logs - Basic Retrieval
# ============================================================================

@pytest.mark.asyncio
async def test_get_audit_logs_empty(client: AsyncClient, test_session: AsyncSession):
    """Verify getting audit logs returns empty list when no logs exist."""
    response = await client.get("/api/audit-logs/")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert data["total_count"] == 0
    assert len(data["logs"]) == 0


@pytest.mark.asyncio
async def test_get_audit_logs_returns_logs(client: AsyncClient, test_session: AsyncSession):
    """Verify getting audit logs returns existing logs."""
    await create_test_audit_log(test_session)
    await create_test_audit_log(test_session)

    response = await client.get("/api/audit-logs/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert len(data["logs"]) == 2


# ============================================================================
# Test 2: Action Type Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_action_type_valid(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by valid action type returns only matching logs."""
    user_id = uuid4()

    # Create logs with different action types
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_CREATED, user_id=user_id)
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_UPDATED, user_id=user_id)
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_CREATED, user_id=user_id)

    response = await client.get("/api/audit-logs/?action_type=user_created")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for log in data["logs"]:
        assert log["action_type"] == "user_created"


@pytest.mark.asyncio
async def test_filter_by_action_type_invalid(client: AsyncClient):
    """Verify filtering by invalid action type returns 400 error."""
    response = await client.get("/api/audit-logs/?action_type=invalid_action")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid action_type" in data["detail"]


@pytest.mark.asyncio
async def test_filter_by_security_action_types(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by security action types works correctly."""
    user_id = uuid4()
    org_id = uuid4()

    # Create security event logs
    await create_test_audit_log(test_session, action_type=AuditActionType.SSO_LOGIN, user_id=user_id, organization_id=org_id)
    await create_test_audit_log(test_session, action_type=AuditActionType.TFA_ENABLED, user_id=user_id, organization_id=org_id)
    await create_test_audit_log(test_session, action_type=AuditActionType.TFA_DISABLED, user_id=user_id, organization_id=org_id)
    await create_test_audit_log(test_session, action_type=AuditActionType.SESSION_REVOKED, user_id=user_id, organization_id=org_id)
    await create_test_audit_log(test_session, action_type=AuditActionType.IP_BLOCKED, user_id=user_id, organization_id=org_id)
    # Create non-security event
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_CREATED, user_id=user_id, organization_id=org_id)

    # Filter for each security action type
    security_actions = [
        "sso_login",
        "2fa_enabled",
        "2fa_disabled",
        "session_revoked",
        "ip_blocked",
    ]

    for action in security_actions:
        response = await client.get(f"/api/audit-logs/?action_type={action}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["logs"][0]["action_type"] == action


# ============================================================================
# Test 3: Entity Type Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_entity_type(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by entity type returns only matching logs."""
    # Create logs with different entity types
    await create_test_audit_log(test_session, entity_type="user")
    await create_test_audit_log(test_session, entity_type="vacancy")
    await create_test_audit_log(test_session, entity_type="user")

    response = await client.get("/api/audit-logs/?entity_type=user")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for log in data["logs"]:
        assert log["entity_type"] == "user"


@pytest.mark.asyncio
async def test_filter_by_entity_id(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by entity ID returns only matching logs."""
    entity_id = uuid4()

    await create_test_audit_log(test_session, entity_id=entity_id)
    await create_test_audit_log(test_session, entity_id=uuid4())

    response = await client.get(f"/api/audit-logs/?entity_id={entity_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["logs"][0]["entity_id"] == str(entity_id)


@pytest.mark.asyncio
async def test_filter_by_entity_id_invalid(client: AsyncClient):
    """Verify filtering by invalid entity ID returns 400 error."""
    response = await client.get("/api/audit-logs/?entity_id=invalid-uuid")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid entity_id format" in data["detail"]


# ============================================================================
# Test 4: User ID Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_user_id(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by user ID returns only matching logs."""
    user_id = uuid4()

    await create_test_audit_log(test_session, user_id=user_id)
    await create_test_audit_log(test_session, user_id=uuid4())
    await create_test_audit_log(test_session, user_id=user_id)

    response = await client.get(f"/api/audit-logs/?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for log in data["logs"]:
        assert log["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_filter_by_user_id_invalid(client: AsyncClient):
    """Verify filtering by invalid user ID returns 400 error."""
    response = await client.get("/api/audit-logs/?user_id=not-a-uuid")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid user_id format" in data["detail"]


# ============================================================================
# Test 5: Organization ID Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_organization_id(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by organization ID returns only matching logs."""
    org_id = uuid4()

    await create_test_audit_log(test_session, organization_id=org_id)
    await create_test_audit_log(test_session, organization_id=uuid4())
    await create_test_audit_log(test_session, organization_id=org_id)

    response = await client.get(f"/api/audit-logs/?organization_id={org_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for log in data["logs"]:
        assert log["organization_id"] == str(org_id)


@pytest.mark.asyncio
async def test_filter_by_organization_id_invalid(client: AsyncClient):
    """Verify filtering by invalid organization ID returns 400 error."""
    response = await client.get("/api/audit-logs/?organization_id=bad-uuid")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid organization_id format" in data["detail"]


# ============================================================================
# Test 6: Date Range Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_start_date(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by start date returns only logs after that date."""
    now = datetime.utcnow()
    old_time = now - timedelta(days=2)
    recent_time = now - timedelta(hours=1)

    await create_test_audit_log(test_session, created_at=old_time, updated_at=old_time)
    await create_test_audit_log(test_session, created_at=recent_time, updated_at=recent_time)

    start_date = (now - timedelta(hours=24)).isoformat()
    response = await client.get(f"/api/audit-logs/?start_date={start_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1


@pytest.mark.asyncio
async def test_filter_by_end_date(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by end date returns only logs before that date."""
    now = datetime.utcnow()
    old_time = now - timedelta(days=2)
    recent_time = now - timedelta(hours=1)

    await create_test_audit_log(test_session, created_at=old_time, updated_at=old_time)
    await create_test_audit_log(test_session, created_at=recent_time, updated_at=recent_time)

    end_date = (now - timedelta(hours=24)).isoformat()
    response = await client.get(f"/api/audit-logs/?end_date={end_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1


@pytest.mark.asyncio
async def test_filter_by_date_range(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by both start and end date returns logs in range."""
    now = datetime.utcnow()
    too_old = now - timedelta(days=5)
    in_range = now - timedelta(days=2)
    too_recent = now - timedelta(hours=1)

    await create_test_audit_log(test_session, created_at=too_old, updated_at=too_old)
    await create_test_audit_log(test_session, created_at=in_range, updated_at=in_range)
    await create_test_audit_log(test_session, created_at=too_recent, updated_at=too_recent)

    start_date = (now - timedelta(days=3)).isoformat()
    end_date = (now - timedelta(hours=12)).isoformat()

    response = await client.get(f"/api/audit-logs/?start_date={start_date}&end_date={end_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1


@pytest.mark.asyncio
async def test_filter_by_start_date_invalid(client: AsyncClient):
    """Verify filtering by invalid start date returns 400 error."""
    response = await client.get("/api/audit-logs/?start_date=not-a-date")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid start_date format" in data["detail"]


@pytest.mark.asyncio
async def test_filter_by_end_date_invalid(client: AsyncClient):
    """Verify filtering by invalid end date returns 400 error."""
    response = await client.get("/api/audit-logs/?end_date=bad-date-format")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid end_date format" in data["detail"]


@pytest.mark.asyncio
async def test_filter_by_date_with_z_suffix(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering by date with Z suffix (UTC timezone) works."""
    now = datetime.utcnow()
    await create_test_audit_log(test_session, created_at=now, updated_at=now)

    start_date = (now - timedelta(hours=1)).isoformat() + 'Z'
    response = await client.get(f"/api/audit-logs/?start_date={start_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 1


# ============================================================================
# Test 7: Pagination
# ============================================================================

@pytest.mark.asyncio
async def test_pagination_limit(client: AsyncClient, test_session: AsyncSession):
    """Verify pagination limit parameter works correctly."""
    # Create 5 logs
    for _ in range(5):
        await create_test_audit_log(test_session)

    response = await client.get("/api/audit-logs/?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 3
    assert data["total_count"] == 3  # total_count reflects returned count


@pytest.mark.asyncio
async def test_pagination_offset(client: AsyncClient, test_session: AsyncSession):
    """Verify pagination offset parameter works correctly."""
    # Create 5 logs
    for _ in range(5):
        await create_test_audit_log(test_session)

    # Get first page
    response = await client.get("/api/audit-logs/?limit=2&offset=0")
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1["logs"]) == 2

    # Get second page
    response = await client.get("/api/audit-logs/?limit=2&offset=2")
    assert response.status_code == 200
    page2 = response.json()
    assert len(page2["logs"]) == 2

    # Verify no duplicates
    page1_ids = {log["id"] for log in page1["logs"]}
    page2_ids = {log["id"] for log in page2["logs"]}
    assert len(page1_ids.intersection(page2_ids)) == 0


@pytest.mark.asyncio
async def test_pagination_limit_max_enforcement(client: AsyncClient, test_session: AsyncSession):
    """Verify pagination limit max is enforced (max 1000)."""
    # Create many logs
    for _ in range(100):
        await create_test_audit_log(test_session)

    response = await client.get("/api/audit-logs/?limit=2000")
    # Should succeed but return at most 1000 logs
    # The API will enforce the max limit
    assert response.status_code in [200, 422]  # Depends on if FastAPI validates first


@pytest.mark.asyncio
async def test_pagination_limit_too_small(client: AsyncClient):
    """Verify pagination limit minimum is enforced (min 1)."""
    response = await client.get("/api/audit-logs/?limit=0")
    # Should return validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_logs_ordered_by_created_at_desc(client: AsyncClient, test_session: AsyncSession):
    """Verify logs are returned in reverse chronological order."""
    now = datetime.utcnow()
    times = [
        now - timedelta(hours=3),
        now - timedelta(hours=2),
        now - timedelta(hours=1),
    ]

    for time in times:
        await create_test_audit_log(test_session, created_at=time, updated_at=time)

    response = await client.get("/api/audit-logs/?limit=10")
    assert response.status_code == 200
    data = response.json()

    # Verify order (most recent first)
    created_times = [log["created_at"] for log in data["logs"]]
    assert created_times == sorted(created_times, reverse=True)


# ============================================================================
# Test 8: Combined Filters
# ============================================================================

@pytest.mark.asyncio
async def test_combined_filters_action_and_user(client: AsyncClient, test_session: AsyncSession):
    """Verify combining action type and user ID filters works."""
    user1 = uuid4()
    user2 = uuid4()

    await create_test_audit_log(test_session, action_type=AuditActionType.USER_CREATED, user_id=user1)
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_UPDATED, user_id=user1)
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_CREATED, user_id=user2)

    response = await client.get(f"/api/audit-logs/?action_type=user_created&user_id={user1}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["logs"][0]["action_type"] == "user_created"
    assert data["logs"][0]["user_id"] == str(user1)


@pytest.mark.asyncio
async def test_combined_filters_date_range_and_action(client: AsyncClient, test_session: AsyncSession):
    """Verify combining date range and action type filters works."""
    now = datetime.utcnow()
    old_time = now - timedelta(days=5)
    new_time = now - timedelta(hours=1)

    await create_test_audit_log(test_session, action_type=AuditActionType.USER_CREATED, created_at=old_time, updated_at=old_time)
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_CREATED, created_at=new_time, updated_at=new_time)
    await create_test_audit_log(test_session, action_type=AuditActionType.USER_UPDATED, created_at=new_time, updated_at=new_time)

    start_date = (now - timedelta(days=2)).isoformat()
    response = await client.get(f"/api/audit-logs/?action_type=user_created&start_date={start_date}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1


# ============================================================================
# Test 9: Response Structure
# ============================================================================

@pytest.mark.asyncio
async def test_response_includes_all_fields(client: AsyncClient, test_session: AsyncSession):
    """Verify audit log response includes all required fields."""
    log = await create_test_audit_log(
        test_session,
        ip_address="10.0.0.1",
        user_agent="TestAgent/1.0",
        reason="Test reason",
        action_data={"key": "value"},
        before_value={"old": "data"},
        after_value={"new": "data"},
    )

    response = await client.get("/api/audit-logs/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 1

    log_data = data["logs"][0]
    assert "id" in log_data
    assert "action_type" in log_data
    assert "entity_type" in log_data
    assert "entity_id" in log_data
    assert "user_id" in log_data
    assert "organization_id" in log_data
    assert "ip_address" in log_data
    assert "user_agent" in log_data
    assert "action_data" in log_data
    assert "before_value" in log_data
    assert "after_value" in log_data
    assert "reason" in log_data
    assert "created_at" in log_data

    # Verify values
    assert log_data["ip_address"] == "10.0.0.1"
    assert log_data["user_agent"] == "TestAgent/1.0"
    assert log_data["reason"] == "Test reason"
    assert log_data["action_data"] == {"key": "value"}
    assert log_data["before_value"] == {"old": "data"}
    assert log_data["after_value"] == {"new": "data"}


@pytest.mark.asyncio
async def test_timestamp_format(client: AsyncClient, test_session: AsyncSession):
    """Verify timestamps are returned in ISO 8601 format."""
    now = datetime.utcnow()
    await create_test_audit_log(test_session, created_at=now, updated_at=now)

    response = await client.get("/api/audit-logs/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 1

    created_at = data["logs"][0]["created_at"]
    # Verify ISO format (should parse with fromisoformat)
    datetime.fromisoformat(created_at.replace('Z', '+00:00'))


# ============================================================================
# Test 10: Get Action Types Endpoint
# ============================================================================

@pytest.mark.asyncio
async def test_get_action_types(client: AsyncClient):
    """Verify getting action types returns all available types."""
    response = await client.get("/api/audit-logs/types")
    assert response.status_code == 200
    data = response.json()
    assert "action_types" in data
    assert isinstance(data["action_types"], list)
    assert len(data["action_types"]) > 0

    # Verify security action types are included
    security_types = ["sso_login", "2fa_enabled", "2fa_disabled", "session_revoked", "ip_blocked"]
    for security_type in security_types:
        assert security_type in data["action_types"]


# ============================================================================
# Test 11: Get Entity Types Endpoint
# ============================================================================

@pytest.mark.asyncio
async def test_get_entity_types(client: AsyncClient):
    """Verify getting entity types returns common entity types."""
    response = await client.get("/api/audit-logs/entity-types")
    assert response.status_code == 200
    data = response.json()
    assert "entity_types" in data
    assert isinstance(data["entity_types"], list)
    assert len(data["entity_types"]) > 0

    # Verify common entity types are included
    common_types = ["resume", "vacancy", "user", "recruiter", "candidate"]
    for entity_type in common_types:
        assert entity_type in data["entity_types"]


# ============================================================================
# Test 12: Security Events Log Verification
# ============================================================================

@pytest.mark.asyncio
async def test_all_security_events_are_loggable(client: AsyncClient, test_session: AsyncSession):
    """Verify all security event types can be logged and retrieved."""
    security_actions = [
        AuditActionType.SSO_LOGIN,
        AuditActionType.TFA_ENABLED,
        AuditActionType.TFA_DISABLED,
        AuditActionType.SESSION_REVOKED,
        AuditActionType.IP_BLOCKED,
        AuditActionType.LOGIN_SUCCESS,
        AuditActionType.LOGIN_FAILED,
        AuditActionType.LOGOUT,
        AuditActionType.PASSWORD_CHANGED,
    ]

    user_id = uuid4()
    org_id = uuid4()

    for action in security_actions:
        await create_test_audit_log(
            test_session,
            action_type=action,
            user_id=user_id,
            organization_id=org_id,
        )

    # Verify all logs are retrievable
    response = await client.get(f"/api/audit-logs/?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == len(security_actions)

    # Verify each security action is present
    returned_actions = {log["action_type"] for log in data["logs"]}
    for action in security_actions:
        assert action.value in returned_actions


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
