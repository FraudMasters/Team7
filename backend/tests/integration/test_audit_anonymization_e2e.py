"""
End-to-End Integration Tests for GDPR Audit Log Anonymization

This test module verifies the complete audit log anonymization workflow:
1. Create test user and perform several auditable actions
2. Verify audit logs contain user_id, IP address, and user_agent
3. Call anonymization API for test user
4. Verify user_id, IP, user_agent are anonymized in audit logs
5. Verify action patterns and timestamps remain intact

Test Coverage:
- Audit log anonymization endpoint (POST /api/audit-logs/anonymize/{user_id})
- PII fields anonymized (user_id, ip_address, user_agent)
- Non-PII fields preserved (action_type, entity_type, timestamps, action_data)
- Action patterns remain intact for compliance analysis
- Multiple logs for same user are all anonymized
- Edge cases: non-existent user, already anonymized logs
"""
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from uuid import uuid4, UUID

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.audit_log import AuditLog, AuditActionType
from config import get_settings


# Test Database Setup
settings = get_settings()
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
# Helper Functions
# ============================================================================

async def create_user_audit_logs(
    session: AsyncSession,
    user_id: UUID,
    count: int = 5
) -> list[AuditLog]:
    """
    Create test audit logs for a specific user simulating various actions.

    Args:
        session: Database session
        user_id: UUID of the user performing actions
        count: Number of audit logs to create

    Returns:
        List of created audit log entries
    """
    action_types = [
        AuditActionType.RESUME_UPLOADED,
        AuditActionType.VACANCY_CREATED,
        AuditActionType.CANDIDATE_RANKED,
        AuditActionType.DATA_EXPORTED,
        AuditActionType.SETTINGS_UPDATED,
    ]

    entity_types = ["resume", "vacancy", "candidate", "data_export", "settings"]
    ip_addresses = ["192.168.1.100", "10.0.0.5", "172.16.0.1"]
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (X11; Linux x86_64)",
    ]

    created_logs = []

    for i in range(count):
        # Create logs with varying timestamps (over last hour)
        minutes_ago = i * 10
        log_date = datetime.utcnow() - timedelta(minutes=minutes_ago)

        log_entry = AuditLog(
            action_type=action_types[i % len(action_types)],
            entity_type=entity_types[i % len(entity_types)],
            entity_id=str(uuid4()),
            user_id=user_id,
            organization_id=uuid4(),
            ip_address=ip_addresses[i % len(ip_addresses)],
            user_agent=user_agents[i % len(user_agents)],
            action_data={
                "test": True,
                "sequence": i,
                "description": f"Test action {i} by user {user_id}",
            },
            before_value={"status": "pending"} if i % 2 == 0 else None,
            after_value={"status": "completed"} if i % 2 == 0 else None,
            reason=f"Test action {i}" if i % 3 == 0 else None,
            created_at=log_date,
        )

        session.add(log_entry)
        created_logs.append(log_entry)

    await session.commit()
    return created_logs


async def verify_logs_contain_pii(
    session: AsyncSession,
    user_id: UUID
) -> bool:
    """
    Verify that audit logs contain PII (user_id, ip_address, user_agent).

    Args:
        session: Database session
        user_id: UUID of the user

    Returns:
        True if logs contain PII, False otherwise
    """
    query = select(AuditLog).where(AuditLog.user_id == user_id)
    result = await session.execute(query)
    logs = result.scalars().all()

    if not logs:
        return False

    # Check that at least one log has PII
    for log in logs:
        if log.user_id and log.ip_address and log.user_agent:
            return True

    return False


async def verify_logs_anonymized(
    session: AsyncSession,
    original_user_id: UUID
) -> dict:
    """
    Verify that audit logs have been anonymized (PII removed).

    Args:
        session: Database session
        original_user_id: Original UUID of the user (should not be found)

    Returns:
        Dictionary with verification results
    """
    # Query for logs with the original user_id (should be empty)
    query_with_user = select(AuditLog).where(AuditLog.user_id == original_user_id)
    result_with_user = await session.execute(query_with_user)
    logs_with_user = result_with_user.scalars().all()

    # Query for all logs (to check if action data is preserved)
    query_all = select(AuditLog)
    result_all = await session.execute(query_all)
    all_logs = result_all.scalars().all()

    # Find logs that were anonymized (user_id is None but action_data mentions original user)
    anonymized_logs = [
        log for log in all_logs
        if log.user_id is None
        and log.action_data
        and isinstance(log.action_data, dict)
        and str(original_user_id) in str(log.action_data.get("description", ""))
    ]

    return {
        "logs_with_original_user_id": len(logs_with_user),
        "total_logs": len(all_logs),
        "anonymized_logs_found": len(anonymized_logs),
        "all_user_ids_none": all(log.user_id is None for log in anonymized_logs),
        "all_ip_addresses_none": all(log.ip_address is None for log in anonymized_logs),
        "all_user_agents_none": all(log.user_agent is None for log in anonymized_logs),
        "action_types_preserved": all(log.action_type is not None for log in anonymized_logs),
        "timestamps_preserved": all(log.created_at is not None for log in anonymized_logs),
        "action_data_preserved": all(log.action_data is not None for log in anonymized_logs),
    }


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_anonymize_user_logs_success(client: AsyncClient, test_session: AsyncSession):
    """Test successful anonymization of user audit logs."""
    # Create test user ID and audit logs
    test_user_id = uuid4()
    await create_user_audit_logs(test_session, test_user_id, count=5)

    # Verify logs contain PII before anonymization
    has_pii = await verify_logs_contain_pii(test_session, test_user_id)
    assert has_pii, "Test logs should contain PII before anonymization"

    # Call anonymization API
    response = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["anonymized_count"] == 5
    assert "Successfully anonymized 5 audit logs" in data["message"]

    # Verify logs are anonymized in database
    verification = await verify_logs_anonymized(test_session, test_user_id)
    assert verification["logs_with_original_user_id"] == 0, "No logs should have original user_id"
    assert verification["anonymized_logs_found"] == 5, "Should find 5 anonymized logs"
    assert verification["all_user_ids_none"], "All user_ids should be None"
    assert verification["all_ip_addresses_none"], "All IP addresses should be None"
    assert verification["all_user_agents_none"], "All user agents should be None"


@pytest.mark.asyncio
async def test_anonymize_preserves_action_patterns(client: AsyncClient, test_session: AsyncSession):
    """Test that anonymization preserves action types, timestamps, and action data."""
    # Create test user ID and audit logs
    test_user_id = uuid4()
    original_logs = await create_user_audit_logs(test_session, test_user_id, count=5)

    # Store original action types and timestamps
    original_action_types = [log.action_type for log in original_logs]
    original_timestamps = [log.created_at for log in original_logs]
    original_action_data = [log.action_data for log in original_logs]

    # Anonymize logs
    response = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")
    assert response.status_code == 200

    # Verify action patterns preserved
    verification = await verify_logs_anonymized(test_session, test_user_id)
    assert verification["action_types_preserved"], "Action types should be preserved"
    assert verification["timestamps_preserved"], "Timestamps should be preserved"
    assert verification["action_data_preserved"], "Action data should be preserved"

    # Query anonymized logs by action data to verify they still exist
    query = select(AuditLog).where(AuditLog.user_id.is_(None))
    result = await test_session.execute(query)
    anonymized_logs = result.scalars().all()

    # Verify we have the right number of logs
    assert len(anonymized_logs) >= 5, "Should have at least 5 anonymized logs"


@pytest.mark.asyncio
async def test_anonymize_multiple_logs_same_user(client: AsyncClient, test_session: AsyncSession):
    """Test anonymizing multiple audit logs for the same user."""
    test_user_id = uuid4()

    # Create 10 audit logs for the same user
    await create_user_audit_logs(test_session, test_user_id, count=10)

    # Anonymize all logs
    response = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["anonymized_count"] == 10
    assert "Successfully anonymized 10 audit logs" in data["message"]

    # Verify all logs are anonymized
    verification = await verify_logs_anonymized(test_session, test_user_id)
    assert verification["logs_with_original_user_id"] == 0
    assert verification["anonymized_logs_found"] == 10


@pytest.mark.asyncio
async def test_anonymize_nonexistent_user(client: AsyncClient, test_session: AsyncSession):
    """Test anonymizing audit logs for a user that doesn't exist."""
    nonexistent_user_id = uuid4()

    # Call anonymization API for user with no logs
    response = await client.post(f"/api/audit-logs/anonymize/{nonexistent_user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["anonymized_count"] == 0
    assert "No audit logs found for this user" in data["message"]


@pytest.mark.asyncio
async def test_anonymize_invalid_user_id_format(client: AsyncClient, test_session: AsyncSession):
    """Test anonymization with invalid user ID format."""
    invalid_user_id = "not-a-valid-uuid"

    # Call anonymization API with invalid UUID
    response = await client.post(f"/api/audit-logs/anonymize/{invalid_user_id}")

    assert response.status_code == 400
    data = response.json()
    assert "Invalid user_id format" in data["detail"]
    assert "Must be a valid UUID" in data["detail"]


@pytest.mark.asyncio
async def test_anonymize_already_anonymized_logs(client: AsyncClient, test_session: AsyncSession):
    """Test that anonymizing already anonymized logs is idempotent."""
    test_user_id = uuid4()

    # Create audit logs
    await create_user_audit_logs(test_session, test_user_id, count=3)

    # Anonymize once
    response1 = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["anonymized_count"] == 3

    # Try to anonymize again (should find no logs with original user_id)
    response2 = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["anonymized_count"] == 0
    assert "No audit logs found for this user" in data2["message"]


@pytest.mark.asyncio
async def test_anonymize_different_users_independently(client: AsyncClient, test_session: AsyncSession):
    """Test that anonymizing one user doesn't affect another user's logs."""
    user1_id = uuid4()
    user2_id = uuid4()

    # Create logs for both users
    await create_user_audit_logs(test_session, user1_id, count=3)
    await create_user_audit_logs(test_session, user2_id, count=3)

    # Verify both users have PII
    assert await verify_logs_contain_pii(test_session, user1_id)
    assert await verify_logs_contain_pii(test_session, user2_id)

    # Anonymize only user1
    response = await client.post(f"/api/audit-logs/anonymize/{user1_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["anonymized_count"] == 3

    # Verify user1 logs are anonymized
    verification1 = await verify_logs_anonymized(test_session, user1_id)
    assert verification1["logs_with_original_user_id"] == 0

    # Verify user2 logs still have PII
    assert await verify_logs_contain_pii(test_session, user2_id)


@pytest.mark.asyncio
async def test_anonymize_preserves_entity_relationships(client: AsyncClient, test_session: AsyncSession):
    """Test that anonymization preserves entity_type, entity_id, and organization_id."""
    test_user_id = uuid4()
    test_org_id = uuid4()

    # Create log with specific entity relationships
    log_entry = AuditLog(
        action_type=AuditActionType.VACANCY_CREATED,
        entity_type="vacancy",
        entity_id=str(uuid4()),
        user_id=test_user_id,
        organization_id=test_org_id,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        action_data={"vacancy_title": "Software Engineer"},
        created_at=datetime.utcnow(),
    )
    test_session.add(log_entry)
    await test_session.commit()

    # Store original entity relationships
    original_entity_type = log_entry.entity_type
    original_entity_id = log_entry.entity_id
    original_org_id = log_entry.organization_id

    # Anonymize logs
    response = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")
    assert response.status_code == 200

    # Query the anonymized log
    query = select(AuditLog).where(AuditLog.organization_id == test_org_id)
    result = await test_session.execute(query)
    anonymized_log = result.scalars().first()

    # Verify entity relationships are preserved
    assert anonymized_log is not None, "Anonymized log should still exist"
    assert anonymized_log.user_id is None, "user_id should be anonymized"
    assert anonymized_log.ip_address is None, "ip_address should be anonymized"
    assert anonymized_log.user_agent is None, "user_agent should be anonymized"
    assert anonymized_log.entity_type == original_entity_type, "entity_type should be preserved"
    assert anonymized_log.entity_id == original_entity_id, "entity_id should be preserved"
    assert anonymized_log.organization_id == original_org_id, "organization_id should be preserved"


@pytest.mark.asyncio
async def test_anonymize_preserves_before_after_values(client: AsyncClient, test_session: AsyncSession):
    """Test that anonymization preserves before_value and after_value for audit trail."""
    test_user_id = uuid4()

    # Create log with before/after values
    log_entry = AuditLog(
        action_type=AuditActionType.SETTINGS_UPDATED,
        entity_type="settings",
        entity_id=str(uuid4()),
        user_id=test_user_id,
        organization_id=uuid4(),
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        action_data={"setting": "retention_policy"},
        before_value={"retention_days": 90},
        after_value={"retention_days": 365},
        reason="Compliance requirement change",
        created_at=datetime.utcnow(),
    )
    test_session.add(log_entry)
    await test_session.commit()

    # Store original values
    original_before = log_entry.before_value
    original_after = log_entry.after_value
    original_reason = log_entry.reason

    # Anonymize logs
    response = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")
    assert response.status_code == 200

    # Query the anonymized log
    query = select(AuditLog).where(AuditLog.user_id.is_(None))
    result = await test_session.execute(query)
    anonymized_log = result.scalars().first()

    # Verify before/after values are preserved
    assert anonymized_log is not None
    assert anonymized_log.before_value == original_before, "before_value should be preserved"
    assert anonymized_log.after_value == original_after, "after_value should be preserved"
    assert anonymized_log.reason == original_reason, "reason should be preserved"


@pytest.mark.asyncio
async def test_anonymization_creates_audit_trail(client: AsyncClient, test_session: AsyncSession):
    """Test that the anonymization action itself is logged in audit trail."""
    test_user_id = uuid4()

    # Create audit logs for user
    await create_user_audit_logs(test_session, test_user_id, count=3)

    # Count total logs before anonymization
    query_before = select(AuditLog)
    result_before = await test_session.execute(query_before)
    logs_before = result_before.scalars().all()
    count_before = len(logs_before)

    # Anonymize logs
    response = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")
    assert response.status_code == 200

    # Count total logs after anonymization (should have 1 additional log for the anonymization action)
    await test_session.commit()  # Ensure transaction is committed
    query_after = select(AuditLog)
    result_after = await test_session.execute(query_after)
    logs_after = result_after.scalars().all()
    count_after = len(logs_after)

    # The anonymization action itself should be logged
    assert count_after == count_before + 1, "Anonymization should create an audit log entry"

    # Find the anonymization audit log
    anonymization_log = None
    for log in logs_after:
        if (log.entity_type == "audit_log" and
            log.action_data and
            log.action_data.get("anonymized_user_id") == str(test_user_id)):
            anonymization_log = log
            break

    assert anonymization_log is not None, "Should find anonymization audit log"
    assert anonymization_log.action_data["anonymized_count"] == 3
    assert "GDPR Right to Erasure" in anonymization_log.action_data["reason"]


@pytest.mark.asyncio
async def test_complete_anonymization_workflow(client: AsyncClient, test_session: AsyncSession):
    """
    Test complete GDPR anonymization workflow end-to-end.

    Steps:
    1. Create test user with multiple auditable actions
    2. Verify audit logs contain PII (user_id, IP, user_agent)
    3. Call anonymization API
    4. Verify PII is removed
    5. Verify action patterns and timestamps remain intact
    6. Verify anonymization is logged
    """
    # Step 1: Create test user and actions
    test_user_id = uuid4()
    test_org_id = uuid4()

    # Simulate various user actions over time
    actions = [
        (AuditActionType.RESUME_UPLOADED, "resume", "192.168.1.100"),
        (AuditActionType.VACANCY_CREATED, "vacancy", "192.168.1.100"),
        (AuditActionType.CANDIDATE_RANKED, "candidate", "10.0.0.5"),
        (AuditActionType.DATA_EXPORTED, "data_export", "10.0.0.5"),
        (AuditActionType.SETTINGS_UPDATED, "settings", "172.16.0.1"),
    ]

    created_logs = []
    for i, (action_type, entity_type, ip) in enumerate(actions):
        log_entry = AuditLog(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=str(uuid4()),
            user_id=test_user_id,
            organization_id=test_org_id,
            ip_address=ip,
            user_agent=f"Mozilla/5.0 (Test Agent {i})",
            action_data={"action_index": i, "description": f"User action {i}"},
            created_at=datetime.utcnow() - timedelta(minutes=i * 10),
        )
        test_session.add(log_entry)
        created_logs.append(log_entry)

    await test_session.commit()

    # Step 2: Verify audit logs contain PII
    query_before = select(AuditLog).where(AuditLog.user_id == test_user_id)
    result_before = await test_session.execute(query_before)
    logs_before = result_before.scalars().all()

    assert len(logs_before) == 5, "Should have 5 audit logs"
    for log in logs_before:
        assert log.user_id == test_user_id, "user_id should be present"
        assert log.ip_address is not None, "ip_address should be present"
        assert log.user_agent is not None, "user_agent should be present"

    # Step 3: Call anonymization API
    response = await client.post(f"/api/audit-logs/anonymize/{test_user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["anonymized_count"] == 5

    # Step 4: Verify PII is removed
    query_after = select(AuditLog).where(AuditLog.user_id == test_user_id)
    result_after = await test_session.execute(query_after)
    logs_after = result_after.scalars().all()

    assert len(logs_after) == 0, "No logs should have original user_id"

    # Step 5: Verify action patterns and timestamps remain intact
    # Query by organization_id to find the anonymized logs
    query_org = select(AuditLog).where(AuditLog.organization_id == test_org_id)
    result_org = await test_session.execute(query_org)
    anonymized_logs = result_org.scalars().all()

    # Filter out the anonymization audit log itself
    user_logs = [log for log in anonymized_logs if log.entity_type != "audit_log"]
    assert len(user_logs) == 5, "Should still have 5 user action logs"

    # Verify action types are preserved
    action_types_preserved = [log.action_type for log in user_logs]
    assert AuditActionType.RESUME_UPLOADED in action_types_preserved
    assert AuditActionType.VACANCY_CREATED in action_types_preserved
    assert AuditActionType.CANDIDATE_RANKED in action_types_preserved
    assert AuditActionType.DATA_EXPORTED in action_types_preserved
    assert AuditActionType.SETTINGS_UPDATED in action_types_preserved

    # Verify timestamps are preserved (check that logs have different timestamps)
    timestamps = [log.created_at for log in user_logs]
    assert len(set(timestamps)) == 5, "All timestamps should be unique and preserved"

    # Verify PII is removed
    for log in user_logs:
        assert log.user_id is None, "user_id should be anonymized"
        assert log.ip_address is None, "ip_address should be anonymized"
        assert log.user_agent is None, "user_agent should be anonymized"

    # Verify non-PII is preserved
    for log in user_logs:
        assert log.organization_id == test_org_id, "organization_id should be preserved"
        assert log.entity_type is not None, "entity_type should be preserved"
        assert log.entity_id is not None, "entity_id should be preserved"
        assert log.action_data is not None, "action_data should be preserved"

    # Step 6: Verify anonymization is logged
    anonymization_logs = [log for log in anonymized_logs if log.entity_type == "audit_log"]
    assert len(anonymization_logs) == 1, "Should have 1 anonymization audit log"

    anon_log = anonymization_logs[0]
    assert anon_log.action_data["anonymized_user_id"] == str(test_user_id)
    assert anon_log.action_data["anonymized_count"] == 5
    assert "GDPR Right to Erasure" in anon_log.action_data["reason"]

    print("✅ Complete GDPR anonymization workflow verified successfully")
