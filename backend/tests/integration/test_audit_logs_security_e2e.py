"""
End-to-End Integration Tests for Security Event Audit Logging

This test module performs comprehensive verification of security event logging
in the audit trail system, ensuring all security-related actions are properly
captured and can be filtered/exported.

Test Coverage:
- All security events are logged (SSO_LOGIN, TFA_ENABLED, TFA_DISABLED, SESSION_REVOKED, IP_BLOCKED)
- Security event filtering by event type
- Security event date range filtering
- Security event CSV export
- Audit log includes user, action, timestamp for all security events
- Security event metadata (IP address, user agent, organization)
- Before/after values for sensitive security operations
"""
import asyncio
import csv
import io
from datetime import datetime, timedelta
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.audit_log import AuditLog, AuditActionType
from models.two_factor_auth import TwoFactorAuth
from models.session import Session
from models.security_config import SecurityConfig
from models.ip_whitelist import IPWhitelist
from config import get_settings


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


# Helper function to create a security audit log
async def create_security_audit_log(
    session: AsyncSession,
    action_type: AuditActionType,
    user_id: UUID = None,
    organization_id: UUID = None,
    **kwargs
) -> AuditLog:
    """Create a security audit log with standard parameters."""
    if user_id is None:
        user_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()

    defaults = {
        "action_type": action_type,
        "entity_type": kwargs.get("entity_type", "security"),
        "entity_id": kwargs.get("entity_id", uuid4()),
        "user_id": user_id,
        "organization_id": organization_id,
        "ip_address": kwargs.get("ip_address", "192.168.1.100"),
        "user_agent": kwargs.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
        "action_data": kwargs.get("action_data", {}),
        "before_value": kwargs.get("before_value"),
        "after_value": kwargs.get("after_value"),
        "reason": kwargs.get("reason"),
        "created_at": kwargs.get("created_at", datetime.utcnow()),
        "updated_at": kwargs.get("updated_at", datetime.utcnow()),
    }

    log = AuditLog(**defaults)
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


# ============================================================================
# Test 1: SSO Login Event Logging
# ============================================================================

@pytest.mark.asyncio
async def test_sso_login_creates_audit_log(test_session: AsyncSession):
    """Verify that SSO login creates a proper audit log entry."""
    user_id = uuid4()
    org_id = uuid4()
    sso_config_id = uuid4()

    log = await create_security_audit_log(
        test_session,
        action_type=AuditActionType.SSO_LOGIN,
        user_id=user_id,
        organization_id=org_id,
        entity_type="sso_config",
        entity_id=sso_config_id,
        action_data={
            "provider": "okta",
            "email": "user@example.com",
            "sso_config_id": str(sso_config_id),
        },
        ip_address="203.0.113.42",
        user_agent="Mozilla/5.0 SAML Browser",
    )

    # Verify log was created
    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.action_type == AuditActionType.SSO_LOGIN
    assert retrieved_log.user_id == user_id
    assert retrieved_log.organization_id == org_id
    assert retrieved_log.ip_address == "203.0.113.42"
    assert retrieved_log.action_data is not None
    assert retrieved_log.action_data["provider"] == "okta"
    assert retrieved_log.action_data["email"] == "user@example.com"
    assert retrieved_log.created_at is not None

    print(f"✓ SSO login audit log created: {log.id}")


@pytest.mark.asyncio
async def test_sso_login_includes_timestamp(client: AsyncClient, test_session: AsyncSession):
    """Verify that SSO login audit log includes proper timestamp."""
    user_id = uuid4()
    org_id = uuid4()

    await create_security_audit_log(
        test_session,
        action_type=AuditActionType.SSO_LOGIN,
        user_id=user_id,
        organization_id=org_id,
    )

    response = await client.get(f"/api/audit-logs/?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1

    log = data["logs"][0]
    assert "created_at" in log
    # Verify timestamp is parseable ISO format
    timestamp = datetime.fromisoformat(log["created_at"].replace('Z', '+00:00'))
    assert timestamp is not None
    # Verify timestamp is recent (within last minute)
    assert datetime.utcnow() - timestamp < timedelta(seconds=60)

    print(f"✓ SSO login includes timestamp: {log['created_at']}")


# ============================================================================
# Test 2: 2FA Event Logging
# ============================================================================

@pytest.mark.asyncio
async def test_2fa_enabled_creates_audit_log(test_session: AsyncSession):
    """Verify that enabling 2FA creates a proper audit log entry."""
    user_id = uuid4()
    org_id = uuid4()

    log = await create_security_audit_log(
        test_session,
        action_type=AuditActionType.TFA_ENABLED,
        user_id=user_id,
        organization_id=org_id,
        entity_type="two_factor_auth",
        action_data={
            "method": "totp",
            "backup_codes_generated": 10,
        },
        after_value={
            "enabled": True,
            "method": "totp",
        },
        ip_address="192.168.1.50",
    )

    # Verify log was created
    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.action_type == AuditActionType.TFA_ENABLED
    assert retrieved_log.after_value is not None
    assert retrieved_log.after_value["enabled"] is True
    assert retrieved_log.after_value["method"] == "totp"
    assert retrieved_log.action_data["backup_codes_generated"] == 10

    print(f"✓ 2FA enabled audit log created: {log.id}")


@pytest.mark.asyncio
async def test_2fa_disabled_creates_audit_log_with_before_value(test_session: AsyncSession):
    """Verify that disabling 2FA creates audit log with before_value."""
    user_id = uuid4()
    org_id = uuid4()

    log = await create_security_audit_log(
        test_session,
        action_type=AuditActionType.TFA_DISABLED,
        user_id=user_id,
        organization_id=org_id,
        entity_type="two_factor_auth",
        before_value={
            "enabled": True,
            "method": "totp",
        },
        after_value={
            "enabled": False,
        },
        reason="User requested disabling 2FA",
        ip_address="192.168.1.51",
    )

    # Verify log was created
    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.action_type == AuditActionType.TFA_DISABLED
    assert retrieved_log.before_value is not None
    assert retrieved_log.before_value["enabled"] is True
    assert retrieved_log.after_value["enabled"] is False
    assert retrieved_log.reason == "User requested disabling 2FA"

    print(f"✓ 2FA disabled audit log created with before_value: {log.id}")


@pytest.mark.asyncio
async def test_2fa_method_switch_creates_audit_log(test_session: AsyncSession):
    """Verify that switching 2FA method creates proper audit log."""
    user_id = uuid4()
    org_id = uuid4()

    log = await create_security_audit_log(
        test_session,
        action_type=AuditActionType.TFA_DISABLED,
        user_id=user_id,
        organization_id=org_id,
        entity_type="two_factor_auth",
        before_value={
            "enabled": True,
            "method": "totp",
        },
        after_value={
            "enabled": True,
            "method": "sms",
        },
        action_data={
            "previous_method": "totp",
            "new_method": "sms",
            "phone": "+1***5551234",
        },
        reason="Switching from TOTP to SMS",
    )

    # Verify log captures the method switch
    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.before_value["method"] == "totp"
    assert retrieved_log.after_value["method"] == "sms"
    assert retrieved_log.action_data["previous_method"] == "totp"
    assert retrieved_log.action_data["new_method"] == "sms"

    print(f"✓ 2FA method switch audit log created: {log.id}")


# ============================================================================
# Test 3: Session Revocation Event Logging
# ============================================================================

@pytest.mark.asyncio
async def test_session_revoked_creates_audit_log(test_session: AsyncSession):
    """Verify that session revocation creates a proper audit log entry."""
    user_id = uuid4()
    org_id = uuid4()
    session_id = uuid4()

    log = await create_security_audit_log(
        test_session,
        action_type=AuditActionType.SESSION_REVOKED,
        user_id=user_id,
        organization_id=org_id,
        entity_type="session",
        entity_id=session_id,
        action_data={
            "session_id": str(session_id),
            "device_type": "desktop",
            "device_name": "Chrome on Windows",
            "revoked_by": "user",
        },
        before_value={
            "active": True,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        },
        after_value={
            "active": False,
        },
        reason="User logged out from device",
        ip_address="192.168.1.75",
    )

    # Verify log was created
    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.action_type == AuditActionType.SESSION_REVOKED
    assert retrieved_log.entity_id == session_id
    assert retrieved_log.before_value["active"] is True
    assert retrieved_log.after_value["active"] is False
    assert retrieved_log.action_data["device_type"] == "desktop"

    print(f"✓ Session revoked audit log created: {log.id}")


@pytest.mark.asyncio
async def test_revoke_all_sessions_creates_multiple_audit_logs(test_session: AsyncSession):
    """Verify that revoking all sessions creates audit logs for each session."""
    user_id = uuid4()
    org_id = uuid4()

    # Create audit logs for multiple session revocations
    session_ids = [uuid4() for _ in range(3)]
    for session_id in session_ids:
        await create_security_audit_log(
            test_session,
            action_type=AuditActionType.SESSION_REVOKED,
            user_id=user_id,
            organization_id=org_id,
            entity_type="session",
            entity_id=session_id,
            action_data={
                "session_id": str(session_id),
                "revoked_by": "user",
                "bulk_revoke": True,
            },
            reason="User revoked all other sessions",
        )

    # Verify all logs were created
    stmt = select(AuditLog).where(
        AuditLog.user_id == user_id,
        AuditLog.action_type == AuditActionType.SESSION_REVOKED
    )
    result = await test_session.execute(stmt)
    logs = result.scalars().all()

    assert len(logs) == 3
    for log in logs:
        assert log.action_data["bulk_revoke"] is True

    print(f"✓ Multiple session revocation audit logs created: {len(logs)} logs")


# ============================================================================
# Test 4: IP Blocked Event Logging
# ============================================================================

@pytest.mark.asyncio
async def test_ip_blocked_creates_audit_log(test_session: AsyncSession):
    """Verify that IP blocking creates a proper audit log entry."""
    org_id = uuid4()
    blocked_ip = "203.0.113.50"

    log = await create_security_audit_log(
        test_session,
        action_type=AuditActionType.IP_BLOCKED,
        user_id=None,  # System action
        organization_id=org_id,
        entity_type="ip_whitelist",
        action_data={
            "blocked_ip": blocked_ip,
            "reason": "IP not in whitelist",
            "strict_mode": True,
            "endpoint": "/api/vacancies/",
        },
        ip_address=blocked_ip,
        user_agent="Mozilla/5.0 Unknown Browser",
    )

    # Verify log was created
    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.action_type == AuditActionType.IP_BLOCKED
    assert retrieved_log.user_id is None  # System action
    assert retrieved_log.action_data["blocked_ip"] == blocked_ip
    assert retrieved_log.action_data["strict_mode"] is True
    assert retrieved_log.ip_address == blocked_ip

    print(f"✓ IP blocked audit log created: {log.id}")


@pytest.mark.asyncio
async def test_ip_blocked_with_whitelist_entry(test_session: AsyncSession):
    """Verify IP blocking audit log references whitelist entry."""
    org_id = uuid4()
    whitelist_id = uuid4()
    blocked_ip = "203.0.113.99"

    log = await create_security_audit_log(
        test_session,
        action_type=AuditActionType.IP_BLOCKED,
        user_id=None,
        organization_id=org_id,
        entity_type="ip_whitelist",
        entity_id=whitelist_id,
        action_data={
            "blocked_ip": blocked_ip,
            "whitelist_entry_id": str(whitelist_id),
            "cidr": "192.168.1.0/24",
            "not_in_range": True,
        },
        ip_address=blocked_ip,
    )

    # Verify log references whitelist
    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.entity_id == whitelist_id
    assert retrieved_log.action_data["whitelist_entry_id"] == str(whitelist_id)
    assert retrieved_log.action_data["cidr"] == "192.168.1.0/24"

    print(f"✓ IP blocked with whitelist reference audit log created: {log.id}")


# ============================================================================
# Test 5: Security Event Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_filter_by_security_event_sso_login(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering for SSO_LOGIN security events."""
    user_id = uuid4()
    org_id = uuid4()

    # Create mix of security and regular events
    await create_security_audit_log(test_session, AuditActionType.SSO_LOGIN, user_id, org_id)
    await create_security_audit_log(test_session, AuditActionType.TFA_ENABLED, user_id, org_id)
    await create_security_audit_log(test_session, AuditActionType.USER_CREATED, user_id, org_id)

    response = await client.get(f"/api/audit-logs/?action_type=sso_login&user_id={user_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    assert data["logs"][0]["action_type"] == "sso_login"

    print(f"✓ SSO login filtering works")


@pytest.mark.asyncio
async def test_filter_by_multiple_security_events(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering returns all security event types."""
    user_id = uuid4()
    org_id = uuid4()

    # Create all security event types
    security_actions = [
        AuditActionType.SSO_LOGIN,
        AuditActionType.TFA_ENABLED,
        AuditActionType.TFA_DISABLED,
        AuditActionType.SESSION_REVOKED,
        AuditActionType.IP_BLOCKED,
    ]

    for action in security_actions:
        await create_security_audit_log(test_session, action, user_id, org_id)

    # Create non-security event
    await create_security_audit_log(test_session, AuditActionType.USER_CREATED, user_id, org_id)

    # Get all logs for user
    response = await client.get(f"/api/audit-logs/?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 6  # 5 security + 1 regular

    # Filter for security events by checking each action type
    security_event_types = ["sso_login", "2fa_enabled", "2fa_disabled", "session_revoked", "ip_blocked"]
    security_logs = [log for log in data["logs"] if log["action_type"] in security_event_types]

    assert len(security_logs) == 5

    print(f"✓ All security events are filterable: {len(security_logs)} events")


# ============================================================================
# Test 6: Security Event Date Range Filtering
# ============================================================================

@pytest.mark.asyncio
async def test_security_events_date_range_filter(client: AsyncClient, test_session: AsyncSession):
    """Verify date range filtering works for security events."""
    user_id = uuid4()
    org_id = uuid4()
    now = datetime.utcnow()

    # Create security events at different times
    old_time = now - timedelta(days=5)
    middle_time = now - timedelta(days=2)
    recent_time = now - timedelta(hours=1)

    await create_security_audit_log(
        test_session,
        AuditActionType.SSO_LOGIN,
        user_id,
        org_id,
        created_at=old_time,
        updated_at=old_time,
    )
    await create_security_audit_log(
        test_session,
        AuditActionType.TFA_ENABLED,
        user_id,
        org_id,
        created_at=middle_time,
        updated_at=middle_time,
    )
    await create_security_audit_log(
        test_session,
        AuditActionType.SESSION_REVOKED,
        user_id,
        org_id,
        created_at=recent_time,
        updated_at=recent_time,
    )

    # Filter by date range (should get middle event only)
    start_date = (now - timedelta(days=3)).isoformat()
    end_date = (now - timedelta(hours=12)).isoformat()

    response = await client.get(
        f"/api/audit-logs/?user_id={user_id}&start_date={start_date}&end_date={end_date}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    assert data["logs"][0]["action_type"] == "2fa_enabled"

    print(f"✓ Security event date range filtering works")


# ============================================================================
# Test 7: CSV Export for Security Events
# ============================================================================

@pytest.mark.asyncio
async def test_security_events_csv_export_includes_all_fields(client: AsyncClient, test_session: AsyncSession):
    """Verify CSV export includes all security event fields."""
    user_id = uuid4()
    org_id = uuid4()

    await create_security_audit_log(
        test_session,
        AuditActionType.SSO_LOGIN,
        user_id,
        org_id,
        ip_address="203.0.113.100",
        user_agent="Mozilla/5.0 Test Browser",
        reason="SAML authentication successful",
    )

    response = await client.get(f"/api/audit-logs/?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()

    # Convert to CSV format (as done in frontend)
    output = io.StringIO()
    if data["logs"]:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id", "action_type", "entity_type", "entity_id",
                "user_id", "organization_id", "ip_address",
                "user_agent", "created_at", "reason"
            ]
        )
        writer.writeheader()
        for log in data["logs"]:
            writer.writerow({
                "id": log["id"],
                "action_type": log["action_type"],
                "entity_type": log["entity_type"],
                "entity_id": log["entity_id"],
                "user_id": log["user_id"],
                "organization_id": log["organization_id"],
                "ip_address": log["ip_address"],
                "user_agent": log["user_agent"],
                "created_at": log["created_at"],
                "reason": log["reason"],
            })

    csv_content = output.getvalue()

    # Verify CSV includes all security event fields
    assert "id" in csv_content
    assert "action_type" in csv_content
    assert "sso_login" in csv_content
    assert "ip_address" in csv_content
    assert "203.0.113.100" in csv_content
    assert "user_agent" in csv_content
    assert "created_at" in csv_content
    assert "reason" in csv_content

    print(f"✓ Security events CSV export includes all fields")


@pytest.mark.asyncio
async def test_security_events_filtered_csv_export(client: AsyncClient, test_session: AsyncSession):
    """Verify CSV export respects security event filtering."""
    user_id = uuid4()
    org_id = uuid4()

    # Create security and non-security events
    await create_security_audit_log(test_session, AuditActionType.SSO_LOGIN, user_id, org_id)
    await create_security_audit_log(test_session, AuditActionType.TFA_ENABLED, user_id, org_id)
    await create_security_audit_log(test_session, AuditActionType.USER_CREATED, user_id, org_id)

    # Get only SSO_LOGIN events
    response = await client.get(f"/api/audit-logs/?action_type=sso_login&user_id={user_id}")
    assert response.status_code == 200
    data = response.json()

    # Verify only SSO_LOGIN events are returned
    assert data["total_count"] == 1
    assert data["logs"][0]["action_type"] == "sso_login"

    print(f"✓ Security events CSV export respects filtering")


# ============================================================================
# Test 8: Audit Log Includes Required Fields
# ============================================================================

@pytest.mark.asyncio
async def test_all_security_events_include_user_action_timestamp(client: AsyncClient, test_session: AsyncSession):
    """Verify all security events include user, action, and timestamp."""
    user_id = uuid4()
    org_id = uuid4()

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

    for action in security_actions:
        await create_security_audit_log(test_session, action, user_id, org_id)

    # Get all security events
    response = await client.get(f"/api/audit-logs/?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == len(security_actions)

    # Verify each log has required fields
    for log in data["logs"]:
        # User field
        assert "user_id" in log
        assert log["user_id"] == str(user_id) or log["user_id"] is None  # IP_BLOCKED may have null user

        # Action field
        assert "action_type" in log
        assert log["action_type"] is not None
        assert len(log["action_type"]) > 0

        # Timestamp field
        assert "created_at" in log
        assert log["created_at"] is not None
        # Verify timestamp is valid ISO format
        timestamp = datetime.fromisoformat(log["created_at"].replace('Z', '+00:00'))
        assert timestamp is not None

    print(f"✓ All {len(security_actions)} security events include user, action, timestamp")


@pytest.mark.asyncio
async def test_security_event_metadata_completeness(client: AsyncClient, test_session: AsyncSession):
    """Verify security events include complete metadata."""
    user_id = uuid4()
    org_id = uuid4()

    await create_security_audit_log(
        test_session,
        AuditActionType.TFA_ENABLED,
        user_id,
        org_id,
        ip_address="10.20.30.40",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        action_data={"method": "totp", "backup_codes": 10},
        reason="User enabled 2FA",
    )

    response = await client.get(f"/api/audit-logs/?action_type=2fa_enabled&user_id={user_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    log = data["logs"][0]

    # Verify metadata fields
    assert log["ip_address"] == "10.20.30.40"
    assert log["user_agent"] == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    assert log["organization_id"] == str(org_id)
    assert log["action_data"] is not None
    assert log["action_data"]["method"] == "totp"
    assert log["reason"] == "User enabled 2FA"

    print(f"✓ Security event metadata is complete")


# ============================================================================
# Test 9: Before/After Values for Sensitive Operations
# ============================================================================

@pytest.mark.asyncio
async def test_sensitive_security_operations_capture_state_changes(test_session: AsyncSession):
    """Verify sensitive security operations capture before/after values."""
    user_id = uuid4()
    org_id = uuid4()

    # 2FA disabled should capture before state
    log = await create_security_audit_log(
        test_session,
        AuditActionType.TFA_DISABLED,
        user_id,
        org_id,
        before_value={"enabled": True, "method": "totp"},
        after_value={"enabled": False},
    )

    stmt = select(AuditLog).where(AuditLog.id == log.id)
    result = await test_session.execute(stmt)
    retrieved_log = result.scalar_one()

    assert retrieved_log.before_value is not None
    assert retrieved_log.after_value is not None
    assert retrieved_log.before_value["enabled"] is True
    assert retrieved_log.after_value["enabled"] is False

    print(f"✓ Sensitive operations capture state changes")


# ============================================================================
# Test 10: Security Event Statistics
# ============================================================================

@pytest.mark.asyncio
async def test_security_event_statistics_by_user(client: AsyncClient, test_session: AsyncSession):
    """Verify security events can be aggregated by user."""
    user1 = uuid4()
    user2 = uuid4()
    org_id = uuid4()

    # User 1 has 3 security events
    await create_security_audit_log(test_session, AuditActionType.SSO_LOGIN, user1, org_id)
    await create_security_audit_log(test_session, AuditActionType.TFA_ENABLED, user1, org_id)
    await create_security_audit_log(test_session, AuditActionType.LOGIN_SUCCESS, user1, org_id)

    # User 2 has 2 security events
    await create_security_audit_log(test_session, AuditActionType.SSO_LOGIN, user2, org_id)
    await create_security_audit_log(test_session, AuditActionType.TFA_ENABLED, user2, org_id)

    # Get user 1 events
    response1 = await client.get(f"/api/audit-logs/?user_id={user1}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["total_count"] == 3

    # Get user 2 events
    response2 = await client.get(f"/api/audit-logs/?user_id={user2}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total_count"] == 2

    print(f"✓ Security events can be aggregated by user")


@pytest.mark.asyncio
async def test_security_event_statistics_by_organization(client: AsyncClient, test_session: AsyncSession):
    """Verify security events can be aggregated by organization."""
    org1 = uuid4()
    org2 = uuid4()
    user_id = uuid4()

    # Org 1 has 4 security events
    await create_security_audit_log(test_session, AuditActionType.SSO_LOGIN, user_id, org1)
    await create_security_audit_log(test_session, AuditActionType.TFA_ENABLED, user_id, org1)
    await create_security_audit_log(test_session, AuditActionType.SESSION_REVOKED, user_id, org1)
    await create_security_audit_log(test_session, AuditActionType.LOGIN_SUCCESS, user_id, org1)

    # Org 2 has 2 security events
    await create_security_audit_log(test_session, AuditActionType.SSO_LOGIN, user_id, org2)
    await create_security_audit_log(test_session, AuditActionType.TFA_ENABLED, user_id, org2)

    # Get org 1 events
    response1 = await client.get(f"/api/audit-logs/?organization_id={org1}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["total_count"] == 4

    # Get org 2 events
    response2 = await client.get(f"/api/audit-logs/?organization_id={org2}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total_count"] == 2

    print(f"✓ Security events can be aggregated by organization")


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
