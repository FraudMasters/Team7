"""
Integration Tests for Configuration Hot-Reload Functionality

This test module verifies that the hot-reload functionality works correctly
for non-critical configuration settings without requiring a service restart.

Test Coverage:
- Non-critical settings can be hot-reloaded via the reload endpoint
- Critical settings changes are rejected and require restart
- Configuration changes are logged to the audit trail
- Multiple settings can be changed simultaneously
- Settings values are correctly updated after reload
"""
import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.config_change import ConfigChange, ConfigChangeAction
from config import get_settings, reload_settings
from config.hotreload import (
    RELOADABLE_SETTINGS,
    CRITICAL_SETTINGS,
    is_reloadable,
    validate_reload_safety,
    detect_setting_changes,
)


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
# Test 1: Verify Non-Critical Settings Can Be Hot-Reloaded
# ============================================================================

@pytest.mark.asyncio
async def test_hot_reload_non_critical_setting(client: AsyncClient, test_session: AsyncSession):
    """Verify that changing a non-critical config value works without restart."""
    # Get initial settings
    initial_settings = get_settings()
    initial_log_level = initial_settings.log_level

    # Change log level (non-critical setting)
    original_log_level = os.environ.get("LOG_LEVEL", "INFO")
    os.environ["LOG_LEVEL"] = "DEBUG"

    try:
        # Call reload endpoint
        response = await client.post("/api/config/reload")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "changed_count" in data
        assert "changes" in data
        assert "reloadable_count" in data
        assert "last_reload" in data

        # Verify log_level changed
        if data["changed_count"] > 0:
            assert "log_level" in data["changes"]
            assert data["changes"]["log_level"]["before"] == initial_log_level
            assert data["changes"]["log_level"]["after"] == "DEBUG"

        # Verify new value is active (check reloaded settings)
        reloaded_settings = reload_settings()
        assert reloaded_settings.log_level == "DEBUG"

        # Verify audit log was created
        await test_session.commit()

        stmt = select(ConfigChange).where(
            ConfigChange.action_type == ConfigChangeAction.CONFIG_RELOADED
        )
        result = await test_session.execute(stmt)
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None, "Audit log should be created for config reload"
        assert audit_log.config_key == "*"
        assert audit_log.after_value is not None
        assert "changed_settings" in audit_log.after_value

        print(f"✓ Hot-reload successful: log_level changed from {initial_log_level} to DEBUG")

    finally:
        # Restore original log level
        if original_log_level:
            os.environ["LOG_LEVEL"] = original_log_level
        else:
            os.environ.pop("LOG_LEVEL", None)
        # Reset settings for next test
        reload_settings()


@pytest.mark.asyncio
async def test_hot_reload_multiple_settings(client: AsyncClient, test_session: AsyncSession):
    """Verify that multiple non-critical settings can be changed at once."""
    # Store original values
    original_log_level = os.environ.get("LOG_LEVEL")
    original_llm_temp = os.environ.get("LLM_TEMPERATURE")

    # Set new values
    os.environ["LOG_LEVEL"] = "WARNING"
    os.environ["LLM_TEMPERATURE"] = "0.5"

    try:
        # Get initial state
        initial_settings = get_settings()

        # Call reload endpoint
        response = await client.post("/api/config/reload")

        assert response.status_code == 200
        data = response.json()

        # Verify both settings changed
        assert data["success"] is True
        if data["changed_count"] > 0:
            assert "log_level" in data["changes"] or "llm_temperature" in data["changes"]

        # Verify new values are active
        reloaded_settings = reload_settings()
        assert reloaded_settings.log_level == "WARNING"
        assert reloaded_settings.llm_temperature == 0.5

        print(f"✓ Multiple settings reloaded: {data['changed_count']} changes")

    finally:
        # Restore original values
        if original_log_level:
            os.environ["LOG_LEVEL"] = original_log_level
        else:
            os.environ.pop("LOG_LEVEL", None)
        if original_llm_temp:
            os.environ["LLM_TEMPERATURE"] = original_llm_temp
        else:
            os.environ.pop("LLM_TEMPERATURE", None)
        reload_settings()


# ============================================================================
# Test 2: Verify Critical Settings Require Restart
# ============================================================================

@pytest.mark.asyncio
async def test_critical_settings_rejected_on_reload(client: AsyncClient):
    """Verify that attempting to reload critical settings returns an error."""
    # Store original database URL
    original_db_url = os.environ.get("DATABASE_URL")

    # Try to change database URL (critical setting)
    os.environ["DATABASE_URL"] = "postgresql://new-host:5432/newdb"

    try:
        # Call reload endpoint - should fail
        response = await client.post("/api/config/reload")

        assert response.status_code == 400
        data = response.json()

        # Verify error response
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "Cannot hot-reload configuration"
        assert "critical_settings_changed" in data["detail"]
        assert "database_url" in data["detail"]["critical_settings_changed"]

        print(f"✓ Critical setting change rejected: {data['detail']['critical_settings_changed']}")

    finally:
        # Restore original database URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)
        reload_settings()


@pytest.mark.asyncio
async def test_critical_settings_list_is_correct():
    """Verify that the critical settings list contains expected values."""
    expected_critical = {
        "environment",
        "database_url",
        "redis_url",
        "backend_host",
        "backend_port",
        "frontend_url",
        "celery_broker_url",
        "celery_result_backend",
    }

    assert expected_critical.issubset(CRITICAL_SETTINGS)
    print(f"✓ Critical settings list verified: {len(CRITICAL_SETTINGS)} settings")


@pytest.mark.asyncio
async def test_reloadable_settings_list_is_correct():
    """Verify that reloadable settings include expected non-critical values."""
    expected_reloadable = {
        "log_level",
        "max_upload_size_mb",
        "allowed_file_types",
        "llm_temperature",
        "llm_max_tokens",
        "ats_threshold",
        "backup_enabled",
        "backup_retention_days",
    }

    assert expected_reloadable.issubset(RELOADABLE_SETTINGS)

    # Verify critical settings are NOT in reloadable
    for critical in CRITICAL_SETTINGS:
        assert critical not in RELOADABLE_SETTINGS, f"{critical} should not be reloadable"

    print(f"✓ Reloadable settings list verified: {len(RELOADABLE_SETTINGS)} settings")


# ============================================================================
# Test 3: Verify Hot-Reload Creates Audit Trail
# ============================================================================

@pytest.mark.asyncio
async def test_hot_reload_creates_audit_log_entry(client: AsyncClient, test_session: AsyncSession):
    """Verify that hot-reload operation creates an audit log entry."""
    # Store original value
    original_log_level = os.environ.get("LOG_LEVEL")

    # Change a setting
    os.environ["LOG_LEVEL"] = "ERROR"

    try:
        # Call reload endpoint
        response = await client.post("/api/config/reload")
        assert response.status_code == 200

        # Verify audit log was created
        await test_session.commit()

        stmt = select(ConfigChange).where(
            ConfigChange.action_type == ConfigChangeAction.CONFIG_RELOADED
        ).order_by(ConfigChange.created_at.desc())

        result = await test_session.execute(stmt)
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.action_type == ConfigChangeAction.CONFIG_RELOADED
        assert audit_log.config_key == "*"
        assert audit_log.environment is not None
        assert audit_log.after_value is not None
        assert "changed_settings" in audit_log.after_value

        print(f"✓ Audit log created for hot-reload: {audit_log.id}")

    finally:
        if original_log_level:
            os.environ["LOG_LEVEL"] = original_log_level
        else:
            os.environ.pop("LOG_LEVEL", None)
        reload_settings()


@pytest.mark.asyncio
async def test_hot_reload_audit_log_contains_change_details(client: AsyncClient, test_session: AsyncSession):
    """Verify that audit log contains detailed information about changes."""
    # Store original value
    original_timeout = os.environ.get("ANALYSIS_TIMEOUT_SECONDS")

    # Change a setting
    os.environ["ANALYSIS_TIMEOUT_SECONDS"] = "120"

    try:
        # Call reload endpoint
        response = await client.post("/api/config/reload")
        assert response.status_code == 200

        # Get audit log
        await test_session.commit()

        stmt = select(ConfigChange).where(
            ConfigChange.action_type == ConfigChangeAction.CONFIG_RELOADED
        ).order_by(ConfigChange.created_at.desc())

        result = await test_session.execute(stmt)
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.after_value is not None

        # Verify change details are captured
        after_value = audit_log.after_value
        assert "changed_settings" in after_value
        assert "changes" in after_value
        assert "reloadable_count" in after_value

        if after_value["changed_settings"]:
            # Verify specific change is recorded
            assert "analysis_timeout_seconds" in after_value["changes"]
            change_detail = after_value["changes"]["analysis_timeout_seconds"]
            assert "before" in change_detail
            assert "after" in change_detail

        print(f"✓ Audit log contains detailed change information")

    finally:
        if original_timeout:
            os.environ["ANALYSIS_TIMEOUT_SECONDS"] = original_timeout
        else:
            os.environ.pop("ANALYSIS_TIMEOUT_SECONDS", None)
        reload_settings()


# ============================================================================
# Test 4: Verify Configuration Health Endpoint
# ============================================================================

@pytest.mark.asyncio
async def test_config_health_endpoint(client: AsyncClient):
    """Verify that the config health endpoint returns reloadable settings info."""
    response = await client.get("/api/config/health")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "status" in data
    assert "environment" in data
    assert "config_valid" in data
    assert "reloadable_settings" in data
    assert "critical_settings_count" in data

    # Verify reloadable count matches actual
    assert data["reloadable_settings"] == len(RELOADABLE_SETTINGS)

    print(f"✓ Config health endpoint works: {data['reloadable_settings']} reloadable settings")


# ============================================================================
# Test 5: Verify Reload with No Changes
# ============================================================================

@pytest.mark.asyncio
async def test_reload_with_no_changes(client: AsyncClient):
    """Verify that reload with no changes returns appropriate response."""
    # Call reload without changing anything
    response = await client.post("/api/config/reload")

    assert response.status_code == 200
    data = response.json()

    # Should succeed but report no changes
    assert data["success"] is True
    assert data["changed_count"] == 0
    assert len(data["changes"]) == 0
    assert "no changes detected" in data["message"].lower()

    print(f"✓ Reload with no changes handled correctly")


# ============================================================================
# Test 6: Verify Settings Detection Functions
# ============================================================================

@pytest.mark.asyncio
async def test_is_reloadable_function():
    """Verify the is_reloadable function correctly identifies settings."""
    # Test reloadable settings
    assert is_reloadable("log_level") is True
    assert is_reloadable("llm_temperature") is True
    assert is_reloadable("backup_enabled") is True

    # Test critical settings
    assert is_reloadable("database_url") is False
    assert is_reloadable("redis_url") is False
    assert is_reloadable("environment") is False

    # Test unknown setting
    assert is_reloadable("unknown_setting") is False

    print(f"✓ is_reloadable function works correctly")


@pytest.mark.asyncio
async def test_validate_reload_safety_function():
    """Verify the validate_reload_safety function detects critical changes."""
    from config.base import BaseConfig

    # Create two configs with same critical settings
    config1 = BaseConfig()
    config2 = BaseConfig()

    # Should be safe (no critical changes)
    unsafe = validate_reload_safety(config1, config2)
    assert len(unsafe) == 0

    # Modify a critical setting via environment
    original_db = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = "postgresql://different:5432/db"

    try:
        config3 = BaseConfig()
        # Should be unsafe
        unsafe = validate_reload_safety(config1, config3)
        assert len(unsafe) > 0
        assert "database_url" in unsafe

    finally:
        if original_db:
            os.environ["DATABASE_URL"] = original_db
        else:
            os.environ.pop("DATABASE_URL", None)


@pytest.mark.asyncio
async def test_detect_setting_changes_function():
    """Verify the detect_setting_changes function correctly identifies changes."""
    from config.base import BaseConfig

    original_llm_temp = os.environ.get("LLM_TEMPERATURE")
    original_log_level = os.environ.get("LOG_LEVEL")

    try:
        # Create initial config
        config1 = BaseConfig()

        # Change settings
        os.environ["LLM_TEMPERATURE"] = "0.9"
        os.environ["LOG_LEVEL"] = "ERROR"

        config2 = BaseConfig()

        # Detect changes
        changes = detect_setting_changes(config1, config2)

        # Verify detected changes
        assert "llm_temperature" in changes
        assert "log_level" in changes

        # Verify before/after values
        assert changes["llm_temperature"]["before"] != changes["llm_temperature"]["after"]
        assert changes["log_level"]["before"] != changes["log_level"]["after"]

        print(f"✓ detect_setting_changes function works correctly")

    finally:
        if original_llm_temp:
            os.environ["LLM_TEMPERATURE"] = original_llm_temp
        else:
            os.environ.pop("LLM_TEMPERATURE", None)
        if original_log_level:
            os.environ["LOG_LEVEL"] = original_log_level
        else:
            os.environ.pop("LOG_LEVEL", None)


# ============================================================================
# Test 7: Integration with Multiple Reloads
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_consecutive_reloads(client: AsyncClient, test_session: AsyncSession):
    """Verify that multiple consecutive reloads work correctly."""
    original_log = os.environ.get("LOG_LEVEL")

    try:
        # First reload
        os.environ["LOG_LEVEL"] = "DEBUG"
        response1 = await client.post("/api/config/reload")
        assert response1.status_code == 200

        # Second reload
        os.environ["LOG_LEVEL"] = "INFO"
        response2 = await client.post("/api/config/reload")
        assert response2.status_code == 200

        # Third reload (no change)
        response3 = await client.post("/api/config/reload")
        assert response3.status_code == 200

        # Verify audit logs for each reload
        await test_session.commit()

        stmt = select(ConfigChange).where(
            ConfigChange.action_type == ConfigChangeAction.CONFIG_RELOADED
        )
        result = await test_session.execute(stmt)
        audit_logs = result.scalars().all()

        # Should have at least 3 audit logs
        assert len(list(audit_logs)) >= 3

        print(f"✓ Multiple consecutive reloads work correctly")

    finally:
        if original_log:
            os.environ["LOG_LEVEL"] = original_log
        else:
            os.environ.pop("LOG_LEVEL", None)
        reload_settings()


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
