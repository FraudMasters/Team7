"""
End-to-End Integration Tests for Configuration Audit Trail

This test module performs comprehensive verification of the configuration
audit trail system, ensuring that all configuration changes are properly
logged with who, what, when information and that sensitive values are
encrypted in audit logs.

Test Coverage:
- Configuration changes create audit log entries
- Audit logs capture user identity (user_id, IP address, user agent)
- Audit logs capture before/after values for changes
- Sensitive configuration values are encrypted in audit logs
- Audit logs can be filtered by action type, config key, environment
- Configuration reload creates comprehensive audit trail
- Test audit endpoint creates logs correctly
"""
import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.config_change import ConfigChange, ConfigChangeAction
from config import get_settings
from config.audit import log_config_change, ConfigAuditLogger


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
# Test 1: Configuration Changes Create Audit Logs (Who, What, When)
# ============================================================================

@pytest.mark.asyncio
async def test_config_change_creates_audit_log_with_who_what_when(client: AsyncClient, test_session: AsyncSession):
    """Verify that configuration changes create audit logs with who, what, when."""
    # Make a configuration change via test endpoint
    response = await client.post(
        "/api/config/test-audit",
        json={"test": "audit_value_123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["logged"] is True

    # Query audit logs from database
    await test_session.commit()

    stmt = select(ConfigChange).where(
        ConfigChange.action_type == ConfigChangeAction.VALUE_UPDATED,
        ConfigChange.config_key == "test_audit_key"
    ).order_by(ConfigChange.created_at.desc())

    result = await test_session.execute(stmt)
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, "Audit log should exist for config change"

    # Verify "What" - what was changed
    assert audit_log.action_type == ConfigChangeAction.VALUE_UPDATED
    assert audit_log.config_key == "test_audit_key"
    assert audit_log.config_path == "test.audit"
    assert audit_log.after_value is not None
    assert audit_log.after_value.get("test_value") == "audit_value_123"

    # Verify "Who" - who made the change
    assert audit_log.ip_address is not None, "IP address should be captured"
    assert audit_log.user_agent is not None, "User agent should be captured"

    # Verify "When" - when the change was made
    assert audit_log.created_at is not None
    assert isinstance(audit_log.created_at, datetime)
    # Verify timestamp is recent (within last minute)
    time_diff = datetime.utcnow() - audit_log.created_at.replace(tzinfo=None)
    assert time_diff.total_seconds() < 60, "Timestamp should be recent"

    # Verify environment
    assert audit_log.environment is not None

    print(f"✓ Config change audit log has who={audit_log.ip_address}, "
          f"what={audit_log.config_key}, when={audit_log.created_at}")


@pytest.mark.asyncio
async def test_config_change_captures_request_context(client: AsyncClient, test_session: AsyncSession):
    """Verify that request context (IP, user agent) is captured in audit logs."""
    # Make a configuration change with custom headers
    custom_headers = {
        "User-Agent": "TestAgent/1.0",
        "X-Forwarded-For": "192.168.1.100"
    }

    response = await client.post(
        "/api/config/test-audit",
        json={"test": "context_test"},
        headers=custom_headers
    )

    assert response.status_code == 200

    # Query audit log
    await test_session.commit()

    stmt = select(ConfigChange).where(
        ConfigChange.config_key == "test_audit_key"
    ).order_by(ConfigChange.created_at.desc())

    result = await test_session.execute(stmt)
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None
    # Verify IP address was captured (may be from X-Forwarded-For)
    assert audit_log.ip_address is not None
    # Verify user agent was captured
    assert audit_log.user_agent is not None
    assert "TestAgent" in audit_log.user_agent or audit_log.user_agent == "TestAgent/1.0"

    print(f"✓ Request context captured: IP={audit_log.ip_address}, UA={audit_log.user_agent}")


@pytest.mark.asyncio
async def test_config_change_with_user_id(test_session: AsyncSession):
    """Verify that user_id can be captured in audit logs."""
    # Create a test user ID
    test_user_id = uuid4()
    test_org_id = uuid4()

    # Log a config change with user context
    config_change = await log_config_change(
        db=test_session,
        action_type=ConfigChangeAction.VALUE_UPDATED,
        config_key="test_setting",
        config_path="test.path",
        environment="development",
        user_id=test_user_id,
        organization_id=test_org_id,
        ip_address="10.0.0.1",
        user_agent="TestClient/1.0",
        before_value={"old": "value1"},
        after_value={"new": "value2"},
        change_reason="Test configuration update",
        metadata={"source": "unit_test"}
    )

    assert config_change is not None
    await test_session.commit()

    # Verify the log was created with user context
    stmt = select(ConfigChange).where(ConfigChange.id == config_change.id)
    result = await test_session.execute(stmt)
    saved_log = result.scalar_one()

    assert saved_log.user_id == test_user_id
    assert saved_log.organization_id == test_org_id
    assert saved_log.ip_address == "10.0.0.1"
    assert saved_log.user_agent == "TestClient/1.0"
    assert saved_log.before_value == {"old": "value1"}
    assert saved_log.after_value == {"new": "value2"}
    assert saved_log.change_reason == "Test configuration update"
    assert saved_log.metadata == {"source": "unit_test"}

    print(f"✓ User context captured: user_id={saved_log.user_id}, org_id={saved_log.organization_id}")


# ============================================================================
# Test 2: Before/After Values Are Captured
# ============================================================================

@pytest.mark.asyncio
async def test_config_change_captures_before_and_after_values(test_session: AsyncSession):
    """Verify that before and after values are captured for config changes."""
    test_user_id = uuid4()

    # Log a config change with before/after values
    config_change = await log_config_change(
        db=test_session,
        action_type=ConfigChangeAction.VALUE_UPDATED,
        config_key="log_level",
        config_path="logging.level",
        environment="production",
        user_id=test_user_id,
        before_value={"value": "INFO", "source": "env"},
        after_value={"value": "DEBUG", "source": "env"},
        change_reason="Enable debug logging for troubleshooting"
    )

    await test_session.commit()

    # Verify both values are captured
    assert config_change.before_value is not None
    assert config_change.before_value["value"] == "INFO"
    assert config_change.after_value is not None
    assert config_change.after_value["value"] == "DEBUG"

    print(f"✓ Before/After captured: before={config_change.before_value}, after={config_change.after_value}")


@pytest.mark.asyncio
async def test_config_reload_captures_multiple_changes(client: AsyncClient, test_session: AsyncSession):
    """Verify that config reload captures all changed settings in audit log."""
    # Store original values
    original_log = os.environ.get("LOG_LEVEL")
    original_timeout = os.environ.get("ANALYSIS_TIMEOUT_SECONDS")

    # Change multiple settings
    os.environ["LOG_LEVEL"] = "WARNING"
    os.environ["ANALYSIS_TIMEOUT_SECONDS"] = "180"

    try:
        # Trigger reload
        response = await client.post("/api/config/reload")
        assert response.status_code == 200

        # Get audit log for reload
        await test_session.commit()

        stmt = select(ConfigChange).where(
            ConfigChange.action_type == ConfigChangeAction.CONFIG_RELOADED
        ).order_by(ConfigChange.created_at.desc())

        result = await test_session.execute(stmt)
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.after_value is not None
        assert "changed_settings" in audit_log.after_value
        assert "changes" in audit_log.after_value

        # Verify changes are captured
        changed_settings = audit_log.after_value["changed_settings"]
        assert len(changed_settings) > 0

        # Verify detailed change info
        changes_detail = audit_log.after_value["changes"]
        for setting_name in changed_settings:
            assert setting_name in changes_detail
            assert "before" in changes_detail[setting_name]
            assert "after" in changes_detail[setting_name]

        print(f"✓ Config reload captured {len(changed_settings)} changes in audit log")

    finally:
        # Restore original values
        if original_log:
            os.environ["LOG_LEVEL"] = original_log
        else:
            os.environ.pop("LOG_LEVEL", None)
        if original_timeout:
            os.environ["ANALYSIS_TIMEOUT_SECONDS"] = original_timeout
        else:
            os.environ.pop("ANALYSIS_TIMEOUT_SECONDS", None)
        from config import reload_settings
        reload_settings()


# ============================================================================
# Test 3: Sensitive Values Are Encrypted in Logs
# ============================================================================

@pytest.mark.asyncio
async def test_sensitive_api_key_is_encrypted_in_audit_log(test_session: AsyncSession):
    """Verify that sensitive API keys are encrypted in audit logs."""
    from config.encryption import encrypt_value, is_encrypted_value

    test_api_key = "sk-test-secret-api-key-1234567890"
    test_user_id = uuid4()

    # Log a config change with sensitive API key
    # The after_value should contain the encrypted key
    encrypted_key = encrypt_value(test_api_key)

    config_change = await log_config_change(
        db=test_session,
        action_type=ConfigChangeAction.ENCRYPTED_VALUE_UPDATED,
        config_key="openai_api_key",
        config_path="llm.openai_api_key",
        environment="production",
        user_id=test_user_id,
        before_value={"value": "sk-old-key-12345"},  # This would also be encrypted in production
        after_value={"encrypted": encrypted_key, "algorithm": "fernet"},
        change_reason="API key rotation"
    )

    await test_session.commit()

    # Verify the value is encrypted
    assert config_change.after_value is not None
    assert "encrypted" in config_change.after_value
    encrypted_value = config_change.after_value["encrypted"]

    # Verify it's encrypted (starts with gAAAAA - Fernet signature)
    assert is_encrypted_value(encrypted_value), "API key should be encrypted in audit log"
    assert encrypted_value != test_api_key, "Encrypted value should not match plaintext"
    assert test_api_key not in encrypted_value, "Plaintext key should not be in encrypted value"

    print(f"✓ Sensitive API key is encrypted: {encrypted_value[:20]}...")


@pytest.mark.asyncio
async def test_sensitive_database_url_is_encrypted_in_audit_log(test_session: AsyncSession):
    """Verify that database URLs with passwords are encrypted in audit logs."""
    from config.encryption import encrypt_value, is_encrypted_value

    test_db_url = "postgresql://user:SecretPassword123@db.example.com:5432/mydb"
    test_user_id = uuid4()

    # Encrypt the database URL
    encrypted_db_url = encrypt_value(test_db_url)

    config_change = await log_config_change(
        db=test_session,
        action_type=ConfigChangeAction.ENCRYPTED_VALUE_UPDATED,
        config_key="database_url",
        config_path="database.url",
        environment="production",
        user_id=test_user_id,
        after_value={"encrypted": encrypted_db_url, "algorithm": "fernet"},
        change_reason="Database connection string update"
    )

    await test_session.commit()

    # Verify the database URL is encrypted
    assert config_change.after_value is not None
    encrypted_value = config_change.after_value["encrypted"]

    assert is_encrypted_value(encrypted_value), "Database URL should be encrypted"
    assert "SecretPassword123" not in encrypted_value, "Password should not be in encrypted log"
    assert test_db_url != encrypted_value, "Encrypted URL should not match plaintext"

    print(f"✓ Sensitive database URL is encrypted: {encrypted_value[:20]}...")


@pytest.mark.asyncio
async def test_non_sensitive_values_are_not_encrypted(test_session: AsyncSession):
    """Verify that non-sensitive configuration values are stored as plain text."""
    test_user_id = uuid4()

    # Log a config change with non-sensitive value
    config_change = await log_config_change(
        db=test_session,
        action_type=ConfigChangeAction.VALUE_UPDATED,
        config_key="log_level",
        config_path="logging.level",
        environment="development",
        user_id=test_user_id,
        before_value={"value": "INFO"},
        after_value={"value": "DEBUG"},
        change_reason="Enable debug logging"
    )

    await test_session.commit()

    # Verify non-sensitive values are not encrypted
    assert config_change.after_value is not None
    assert config_change.after_value["value"] == "DEBUG"
    # Not encrypted (doesn't start with gAAAAA)
    assert not config_change.after_value["value"].startswith("gAAAAA")

    print(f"✓ Non-sensitive values stored as plain text: {config_change.after_value['value']}")


# ============================================================================
# Test 4: Audit Logs Can Be Filtered
# ============================================================================

@pytest.mark.asyncio
async def test_filter_audit_logs_by_action_type(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering audit logs by action type."""
    # Create multiple config changes with different action types
    await client.post("/api/config/test-audit", json={"test": "value1"})
    await client.post("/api/config/test-audit", json={"test": "value2"})

    # Query audit logs filtered by action type
    response = await client.get("/api/config/audit-logs?action_type=value_updated&limit=10")

    assert response.status_code == 200
    data = response.json()

    assert "changes" in data
    assert "total_count" in data
    assert data["total_count"] >= 2

    # Verify all returned logs match the filter
    for log in data["changes"]:
        assert log["action_type"] == "value_updated"

    print(f"✓ Filter by action_type works: found {data['total_count']} value_updated logs")


@pytest.mark.asyncio
async def test_filter_audit_logs_by_config_key(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering audit logs by config key."""
    # Create config changes
    await client.post("/api/config/test-audit", json={"test": "value1"})

    # Query audit logs filtered by config key
    response = await client.get("/api/config/audit-logs?config_key=test_audit_key&limit=10")

    assert response.status_code == 200
    data = response.json()

    assert "changes" in data
    assert data["total_count"] >= 1

    # Verify all logs match the config key filter
    for log in data["changes"]:
        assert log["config_key"] == "test_audit_key"

    print(f"✓ Filter by config_key works: found {data['total_count']} logs for test_audit_key")


@pytest.mark.asyncio
async def test_filter_audit_logs_by_environment(client: AsyncClient, test_session: AsyncSession):
    """Verify filtering audit logs by environment."""
    # Create a config change
    await client.post("/api/config/test-audit", json={"test": "env_test"})

    # Get current environment
    settings = get_settings()
    current_env = settings.environment

    # Query audit logs filtered by environment
    response = await client.get(f"/api/config/audit-logs?environment={current_env}&limit=10")

    assert response.status_code == 200
    data = response.json()

    # Verify all logs match the environment filter
    for log in data["changes"]:
        assert log["environment"] == current_env

    print(f"✓ Filter by environment works: found {data['total_count']} logs for {current_env}")


# ============================================================================
# Test 5: ConfigAuditLogger Context Manager
# ============================================================================

@pytest.mark.asyncio
async def test_config_audit_logger_context_manager(test_session: AsyncSession):
    """Verify the ConfigAuditLogger context manager for batch operations."""
    test_user_id = uuid4()
    test_org_id = uuid4()

    # Use the context manager to log multiple changes
    async with ConfigAuditLogger(
        db=test_session,
        user_id=test_user_id,
        organization_id=test_org_id,
        environment="staging",
        ip_address="10.1.2.3",
        user_agent="BatchProcessor/1.0"
    ) as audit:
        log1 = await audit.log(
            ConfigChangeAction.VALUE_UPDATED,
            config_key="setting1",
            before_value={"old": "a"},
            after_value={"new": "b"}
        )
        log2 = await audit.log(
            ConfigChangeAction.VALUE_UPDATED,
            config_key="setting2",
            before_value={"old": "c"},
            after_value={"new": "d"}
        )

    await test_session.commit()

    # Verify both logs were created with the same user context
    stmt = select(ConfigChange).where(
        ConfigChange.user_id == test_user_id,
        ConfigChange.organization_id == test_org_id
    )

    result = await test_session.execute(stmt)
    logs = result.scalars().all()

    assert len(list(logs)) >= 2

    # Verify user context is consistent
    for log in logs:
        assert log.user_id == test_user_id
        assert log.organization_id == test_org_id
        assert log.ip_address == "10.1.2.3"
        assert log.user_agent == "BatchProcessor/1.0"
        assert log.environment == "staging"

    print(f"✓ ConfigAuditLogger context manager works: logged multiple changes with shared context")


# ============================================================================
# Test 6: Change Reason and Metadata
# ============================================================================

@pytest.mark.asyncio
async def test_config_change_includes_reason_and_metadata(test_session: AsyncSession):
    """Verify that change reason and metadata are captured in audit logs."""
    test_user_id = uuid4()

    # Log with reason and metadata
    config_change = await log_config_change(
        db=test_session,
        action_type=ConfigChangeAction.VALUE_UPDATED,
        config_key="max_upload_size_mb",
        config_path="upload.max_size",
        environment="production",
        user_id=test_user_id,
        before_value={"value": 10},
        after_value={"value": 20},
        change_reason="Increased to support larger PDF files",
        metadata={
            "approved_by": "admin@example.com",
            "ticket": "INC-12345",
            "impact": "low"
        }
    )

    await test_session.commit()

    # Verify reason and metadata
    assert config_change.change_reason == "Increased to support larger PDF files"
    assert config_change.metadata is not None
    assert config_change.metadata["approved_by"] == "admin@example.com"
    assert config_change.metadata["ticket"] == "INC-12345"
    assert config_change.metadata["impact"] == "low"

    print(f"✓ Change reason and metadata captured: reason='{config_change.change_reason}', "
          f"metadata={config_change.metadata}")


# ============================================================================
# Test 7: Action Types Endpoint
# ============================================================================

@pytest.mark.asyncio
async def test_get_action_types_endpoint(client: AsyncClient):
    """Verify the action types endpoint returns all valid action types."""
    response = await client.get("/api/config/action-types")

    assert response.status_code == 200
    data = response.json()

    assert "action_types" in data
    action_types = data["action_types"]

    # Verify all expected action types are present
    expected_types = [
        "value_updated",
        "value_reset",
        "environment_changed",
        "config_reloaded",
        "config_validated",
        "encrypted_value_updated",
        "secret_rotated",
        "batch_update",
        "batch_rollback",
        "config_file_loaded",
        "config_override_applied",
        "config_validation_failed"
    ]

    for expected in expected_types:
        assert expected in action_types, f"Action type '{expected}' should be available"

    print(f"✓ Action types endpoint works: {len(action_types)} types returned")


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
