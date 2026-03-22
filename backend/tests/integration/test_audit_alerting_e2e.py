"""
End-to-End Integration Tests for Audit Alert Configuration and Detection

This test module verifies the complete audit alerting workflow:
1. Create alert configuration for failed logins (threshold: 5 in 10 min)
2. Create test audit logs simulating 6 failed login attempts
3. Run suspicious activity detection service
4. Verify alerts are detected with correct details
5. Check audit logs show alert detection events

Test Coverage:
- Alert configuration API endpoints (GET /api/audit/alerts/)
- Alert type and severity enumeration endpoints
- Suspicious activity detection for failed logins
- Suspicious activity detection for bulk data exports
- Suspicious activity detection for permission changes
- Alert threshold evaluation and time window logic
- Multiple alert types in same time window
"""
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.audit_log import AuditLog, AuditActionType
from models.audit_alert_config import AuditAlertConfig, AlertType, AlertSeverity
from services.audit_alerting import AuditAlertingService, detect_suspicious_activity
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

async def create_failed_login_logs(
    session: AsyncSession,
    count: int = 6,
    user_id: str = None,
    ip_address: str = "192.168.1.100",
    minutes_ago: int = 5,
) -> list[AuditLog]:
    """
    Create test audit logs simulating failed login attempts.

    Args:
        session: Database session
        count: Number of failed login attempts to create
        user_id: User ID for the failed logins (generates random if None)
        ip_address: IP address for the failed logins
        minutes_ago: How many minutes ago the logins occurred

    Returns:
        List of created audit log entries
    """
    if user_id is None:
        user_id = str(uuid4())

    created_logs = []
    base_time = datetime.utcnow() - timedelta(minutes=minutes_ago)

    for i in range(count):
        # Spread failed logins over the time window (e.g., 5 minutes)
        timestamp = base_time + timedelta(seconds=i * 30)

        log_entry = AuditLog(
            id=uuid4(),
            action=AuditActionType.LOGIN_FAILED,
            user_id=user_id,
            ip_address=ip_address,
            user_agent="Mozilla/5.0 (Test Browser)",
            resource_type="auth",
            resource_id=None,
            details={
                "email": f"test.user{i}@example.com",
                "reason": "Invalid password",
                "attempt_number": i + 1,
            },
            created_at=timestamp,
        )
        session.add(log_entry)
        created_logs.append(log_entry)

    await session.commit()
    return created_logs


async def create_bulk_export_logs(
    session: AsyncSession,
    count: int = 105,
    user_id: str = None,
    minutes_ago: int = 5,
) -> list[AuditLog]:
    """
    Create test audit logs simulating bulk data exports.

    Args:
        session: Database session
        count: Number of export events to create
        user_id: User ID for the exports (generates random if None)
        minutes_ago: How many minutes ago the exports occurred

    Returns:
        List of created audit log entries
    """
    if user_id is None:
        user_id = str(uuid4())

    created_logs = []
    base_time = datetime.utcnow() - timedelta(minutes=minutes_ago)

    for i in range(count):
        # Spread exports over the time window
        timestamp = base_time + timedelta(seconds=i * 3)

        log_entry = AuditLog(
            id=uuid4(),
            action=AuditActionType.DATA_EXPORTED,
            user_id=user_id,
            ip_address="192.168.1.200",
            user_agent="Mozilla/5.0 (Test Browser)",
            resource_type="export",
            resource_id=str(uuid4()),
            details={
                "export_type": "candidates",
                "record_count": 100,
                "format": "csv",
            },
            created_at=timestamp,
        )
        session.add(log_entry)
        created_logs.append(log_entry)

    await session.commit()
    return created_logs


async def create_permission_change_logs(
    session: AsyncSession,
    count: int = 4,
    user_id: str = None,
    minutes_ago: int = 5,
) -> list[AuditLog]:
    """
    Create test audit logs simulating permission changes.

    Args:
        session: Database session
        count: Number of permission change events to create
        user_id: User ID making the changes (generates random if None)
        minutes_ago: How many minutes ago the changes occurred

    Returns:
        List of created audit log entries
    """
    if user_id is None:
        user_id = str(uuid4())

    created_logs = []
    base_time = datetime.utcnow() - timedelta(minutes=minutes_ago)

    for i in range(count):
        timestamp = base_time + timedelta(seconds=i * 60)

        log_entry = AuditLog(
            id=uuid4(),
            action=AuditActionType.USER_ROLE_CHANGED,
            user_id=user_id,
            ip_address="192.168.1.150",
            user_agent="Mozilla/5.0 (Test Browser)",
            resource_type="user",
            resource_id=str(uuid4()),
            details={
                "previous_role": "viewer",
                "new_role": "admin",
                "target_user_id": str(uuid4()),
            },
            created_at=timestamp,
        )
        session.add(log_entry)
        created_logs.append(log_entry)

    await session.commit()
    return created_logs


async def create_alert_config(
    session: AsyncSession,
    alert_type: AlertType = AlertType.FAILED_LOGINS,
    threshold: int = 5,
    time_window_minutes: int = 10,
    enabled: bool = True,
    severity: AlertSeverity = AlertSeverity.WARNING,
) -> AuditAlertConfig:
    """
    Create a test alert configuration.

    Args:
        session: Database session
        alert_type: Type of alert to monitor
        threshold: Number of events to trigger alert
        time_window_minutes: Time window for threshold evaluation
        enabled: Whether the alert is enabled
        severity: Alert severity level

    Returns:
        Created alert configuration
    """
    alert_config = AuditAlertConfig(
        id=uuid4(),
        name=f"Test {alert_type.value} Alert",
        alert_type=alert_type,
        description=f"Test alert configuration for {alert_type.value}",
        enabled=enabled,
        severity=severity,
        threshold=threshold,
        time_window_minutes=time_window_minutes,
        action_types=None,  # Monitor all action types for this alert
        recipients={"emails": ["security@example.com"]},
        alert_config={},
        cooldown_minutes=60,
        trigger_count=0,
    )
    session.add(alert_config)
    await session.commit()
    return alert_config


# ============================================================================
# Alert Configuration API Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_alert_types(client: AsyncClient):
    """Test GET /api/audit/alerts/types endpoint."""
    response = await client.get("/api/audit/alerts/types")

    assert response.status_code == 200
    data = response.json()

    assert "alert_types" in data
    assert len(data["alert_types"]) > 0

    # Check that common alert types are present
    alert_type_values = [item["value"] for item in data["alert_types"]]
    assert "failed_logins" in alert_type_values
    assert "bulk_data_export" in alert_type_values
    assert "permission_changes" in alert_type_values


@pytest.mark.asyncio
async def test_get_alert_severities(client: AsyncClient):
    """Test GET /api/audit/alerts/severities endpoint."""
    response = await client.get("/api/audit/alerts/severities")

    assert response.status_code == 200
    data = response.json()

    assert "severities" in data
    assert len(data["severities"]) == 4

    # Check that all severity levels are present
    severity_values = [item["value"] for item in data["severities"]]
    assert "info" in severity_values
    assert "warning" in severity_values
    assert "error" in severity_values
    assert "critical" in severity_values


@pytest.mark.asyncio
async def test_get_alert_configs_empty(client: AsyncClient):
    """Test GET /api/audit/alerts/ endpoint with no configs."""
    response = await client.get("/api/audit/alerts/")

    assert response.status_code == 200
    data = response.json()

    assert "alert_configs" in data
    assert "total_count" in data
    assert data["total_count"] == 0
    assert len(data["alert_configs"]) == 0


@pytest.mark.asyncio
async def test_get_alert_configs_with_data(client: AsyncClient, test_session: AsyncSession):
    """Test GET /api/audit/alerts/ endpoint with alert configs."""
    # Create test alert configs
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
    )
    await create_alert_config(
        test_session,
        alert_type=AlertType.BULK_DATA_EXPORT,
        threshold=100,
        time_window_minutes=10,
    )

    response = await client.get("/api/audit/alerts/")

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 2
    assert len(data["alert_configs"]) == 2

    # Verify alert config structure
    config = data["alert_configs"][0]
    assert "id" in config
    assert "name" in config
    assert "alert_type" in config
    assert "enabled" in config
    assert "severity" in config
    assert "threshold" in config
    assert "time_window_minutes" in config


@pytest.mark.asyncio
async def test_get_alert_configs_filter_by_type(client: AsyncClient, test_session: AsyncSession):
    """Test filtering alert configs by alert type."""
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
    )
    await create_alert_config(
        test_session,
        alert_type=AlertType.BULK_DATA_EXPORT,
    )

    # Filter by failed_logins
    response = await client.get("/api/audit/alerts/?alert_type=failed_logins")

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    assert data["alert_configs"][0]["alert_type"] == "failed_logins"


@pytest.mark.asyncio
async def test_get_alert_configs_filter_by_enabled(client: AsyncClient, test_session: AsyncSession):
    """Test filtering alert configs by enabled status."""
    await create_alert_config(test_session, enabled=True)
    await create_alert_config(test_session, enabled=False)

    # Filter by enabled=true
    response = await client.get("/api/audit/alerts/?enabled=true")

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    assert data["alert_configs"][0]["enabled"] is True


# ============================================================================
# Suspicious Activity Detection Tests
# ============================================================================

@pytest.mark.asyncio
async def test_detect_failed_logins_above_threshold(test_session: AsyncSession):
    """Test detection of failed logins exceeding threshold."""
    # Create alert config: 5 failed logins in 10 minutes
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
    )

    # Create 6 failed login attempts (above threshold)
    user_id = str(uuid4())
    await create_failed_login_logs(
        test_session,
        count=6,
        user_id=user_id,
        ip_address="192.168.1.100",
        minutes_ago=5,
    )

    # Detect suspicious activity
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify alert was triggered
    assert len(alerts) == 1
    alert = alerts[0]

    assert alert["alert_type"] == "FAILED_LOGIN"
    assert alert["severity"] == "warning"
    assert alert["count"] >= 5  # At least threshold
    assert "user_id" in alert or "ip_address" in alert
    assert alert["time_window_minutes"] == 10


@pytest.mark.asyncio
async def test_detect_failed_logins_below_threshold(test_session: AsyncSession):
    """Test that failed logins below threshold don't trigger alert."""
    # Create alert config: 5 failed logins in 10 minutes
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
    )

    # Create only 3 failed login attempts (below threshold)
    user_id = str(uuid4())
    await create_failed_login_logs(
        test_session,
        count=3,
        user_id=user_id,
        minutes_ago=5,
    )

    # Detect suspicious activity
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify no alert was triggered
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_detect_bulk_export_above_threshold(test_session: AsyncSession):
    """Test detection of bulk data exports exceeding threshold."""
    # Create alert config: 100 exports in 10 minutes
    await create_alert_config(
        test_session,
        alert_type=AlertType.BULK_DATA_EXPORT,
        threshold=100,
        time_window_minutes=10,
    )

    # Create 105 export events (above threshold)
    user_id = str(uuid4())
    await create_bulk_export_logs(
        test_session,
        count=105,
        user_id=user_id,
        minutes_ago=5,
    )

    # Detect suspicious activity
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify alert was triggered
    assert len(alerts) == 1
    alert = alerts[0]

    assert alert["alert_type"] == "BULK_EXPORT"
    assert alert["count"] >= 100
    assert alert["time_window_minutes"] == 10


@pytest.mark.asyncio
async def test_detect_permission_changes_above_threshold(test_session: AsyncSession):
    """Test detection of permission changes exceeding threshold."""
    # Create alert config: 3 permission changes in 10 minutes
    await create_alert_config(
        test_session,
        alert_type=AlertType.PERMISSION_CHANGES,
        threshold=3,
        time_window_minutes=10,
    )

    # Create 4 permission change events (above threshold)
    user_id = str(uuid4())
    await create_permission_change_logs(
        test_session,
        count=4,
        user_id=user_id,
        minutes_ago=5,
    )

    # Detect suspicious activity
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify alert was triggered
    assert len(alerts) == 1
    alert = alerts[0]

    assert alert["alert_type"] == "PERMISSION_CHANGE"
    assert alert["count"] >= 3
    assert alert["time_window_minutes"] == 10


@pytest.mark.asyncio
async def test_detect_multiple_alert_types(test_session: AsyncSession):
    """Test detection of multiple alert types in same time window."""
    # Create multiple alert configs
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
    )
    await create_alert_config(
        test_session,
        alert_type=AlertType.BULK_DATA_EXPORT,
        threshold=100,
        time_window_minutes=10,
    )

    # Create failed logins (6 events)
    await create_failed_login_logs(
        test_session,
        count=6,
        user_id=str(uuid4()),
        minutes_ago=5,
    )

    # Create bulk exports (105 events)
    await create_bulk_export_logs(
        test_session,
        count=105,
        user_id=str(uuid4()),
        minutes_ago=5,
    )

    # Detect suspicious activity
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify both alerts were triggered
    assert len(alerts) == 2
    alert_types = {alert["alert_type"] for alert in alerts}
    assert "FAILED_LOGIN" in alert_types
    assert "BULK_EXPORT" in alert_types


@pytest.mark.asyncio
async def test_detect_with_disabled_alert_config(test_session: AsyncSession):
    """Test that disabled alert configs don't trigger alerts."""
    # Create disabled alert config
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
        enabled=False,  # Disabled
    )

    # Create 6 failed login attempts (above threshold)
    await create_failed_login_logs(
        test_session,
        count=6,
        user_id=str(uuid4()),
        minutes_ago=5,
    )

    # Detect suspicious activity
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify no alert was triggered (config is disabled)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_detect_outside_time_window(test_session: AsyncSession):
    """Test that events outside time window don't trigger alerts."""
    # Create alert config: 5 failed logins in 10 minutes
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
    )

    # Create 6 failed login attempts from 20 minutes ago (outside time window)
    await create_failed_login_logs(
        test_session,
        count=6,
        user_id=str(uuid4()),
        minutes_ago=20,  # Outside 10-minute window
    )

    # Detect suspicious activity
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify no alert was triggered (events are too old)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_detect_suspicious_activity_convenience_function(test_session: AsyncSession):
    """Test the convenience function for detecting suspicious activity."""
    # Create alert config
    await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
    )

    # Create failed login attempts
    await create_failed_login_logs(
        test_session,
        count=6,
        user_id=str(uuid4()),
        minutes_ago=5,
    )

    # Use convenience function
    alerts = await detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Verify alert was triggered
    assert len(alerts) >= 1
    assert any(alert["alert_type"] == "FAILED_LOGIN" for alert in alerts)


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_complete_alerting_workflow(client: AsyncClient, test_session: AsyncSession):
    """
    Test complete end-to-end alerting workflow.

    Steps:
    1. Create alert rule for failed logins (threshold: 5 in 10 min)
    2. Simulate 6 failed login attempts
    3. Verify alert is triggered via detection service
    4. Verify alert details are correct
    """
    # Step 1: Create alert rule via database (API POST not yet implemented)
    alert_config = await create_alert_config(
        test_session,
        alert_type=AlertType.FAILED_LOGINS,
        threshold=5,
        time_window_minutes=10,
        severity=AlertSeverity.WARNING,
    )

    # Verify alert config was created
    response = await client.get("/api/audit/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["alert_configs"][0]["alert_type"] == "failed_logins"
    assert data["alert_configs"][0]["threshold"] == 5

    # Step 2: Simulate 6 failed login attempts
    user_id = str(uuid4())
    ip_address = "192.168.1.100"
    failed_logs = await create_failed_login_logs(
        test_session,
        count=6,
        user_id=user_id,
        ip_address=ip_address,
        minutes_ago=5,
    )

    # Verify logs were created
    stmt = select(AuditLog).where(
        AuditLog.action == AuditActionType.LOGIN_FAILED
    )
    result = await test_session.execute(stmt)
    logs = result.scalars().all()
    assert len(logs) == 6

    # Step 3: Run suspicious activity detection
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Step 4: Verify alert is triggered and details are correct
    assert len(alerts) == 1

    alert = alerts[0]
    assert alert["alert_type"] == "FAILED_LOGIN"
    assert alert["severity"] == "warning"
    assert alert["count"] >= 5
    assert alert["threshold"] == 5
    assert alert["time_window_minutes"] == 10

    # Verify alert contains entity information (user_id or ip_address)
    assert "entities" in alert
    assert len(alert["entities"]) > 0

    # Verify timestamps
    assert "earliest_event" in alert
    assert "latest_event" in alert


@pytest.mark.asyncio
async def test_alerting_with_no_configs(test_session: AsyncSession):
    """Test that detection works gracefully when no alert configs exist."""
    # Create some failed login logs
    await create_failed_login_logs(
        test_session,
        count=10,
        user_id=str(uuid4()),
        minutes_ago=5,
    )

    # Run detection with no alert configs
    service = AuditAlertingService(test_session)
    alerts = await service.detect_suspicious_activity(
        time_window_minutes=10,
        organization_id=None,
    )

    # Should return empty list, not error
    assert alerts == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
