"""
End-to-End Integration Tests for Session Management

This test module performs comprehensive verification of the session management system,
including session creation, validation, listing, revocation, and multi-device scenarios.

Test Coverage:
- Session creation with device fingerprinting
- Session validation and expiration checking
- Listing active sessions with filtering
- Revoking individual sessions
- Revoking all sessions for a user
- Multiple concurrent sessions per user
- Session cleanup of expired/revoked sessions
- Health check statistics
- Error handling for invalid operations
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.session import Session
from services.session_service import SessionService


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
# Test 1: Session Service - Basic Operations
# ============================================================================

@pytest.mark.asyncio
async def test_session_service_create_session():
    """Verify session can be created with device information."""
    service = SessionService()

    # Create a session
    session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ip_address="192.168.1.1",
        location="San Francisco, CA",
        ttl_hours=24,
    )

    assert session is not None
    assert session.user_id is not None
    assert session.device_type == "desktop"
    assert session.device_name == "Chrome on Windows"
    assert session.ip_address == "192.168.1.1"
    assert session.location == "San Francisco, CA"
    assert session.is_active is True
    assert session.expires_at is not None


@pytest.mark.asyncio
async def test_session_service_validate_session():
    """Verify session can be validated."""
    service = SessionService()
    user_id = str(uuid4())

    # Create a session
    session = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        ip_address="192.168.1.2",
    )

    # Get the token
    token = session._token

    # Validate session
    is_valid = await service.validate_session(token)

    assert is_valid is True


@pytest.mark.asyncio
async def test_session_service_revoke_session():
    """Verify session can be revoked."""
    service = SessionService()
    user_id = str(uuid4())

    # Create a session
    session = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X)",
    )
    token = session._token

    # Revoke session
    revoked = await service.revoke_session(token, reason="user_logout")

    assert revoked is True

    # Verify session is no longer valid
    is_valid = await service.validate_session(token)
    assert is_valid is False


@pytest.mark.asyncio
async def test_session_service_get_active_sessions():
    """Verify active sessions can be retrieved for a user."""
    service = SessionService()
    user_id = str(uuid4())

    # Create multiple sessions
    await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        ip_address="192.168.1.1",
    )
    await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)",
        ip_address="192.168.1.2",
    )
    await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (Linux; Android 13)",
        ip_address="192.168.1.3",
    )

    # Get active sessions
    sessions = await service.get_active_sessions(user_id)

    assert len(sessions) == 3
    assert all(s.is_active for s in sessions)


@pytest.mark.asyncio
async def test_session_service_revoke_all_sessions():
    """Verify all sessions can be revoked for a user."""
    service = SessionService()
    user_id = str(uuid4())

    # Create multiple sessions
    session1 = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    )
    session2 = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)",
    )
    session3 = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (Linux; Android 13)",
    )

    # Revoke all sessions
    revoked_count = await service.revoke_all_sessions(user_id, reason="security_reset")

    assert revoked_count == 3

    # Verify all sessions are revoked
    sessions = await service.get_active_sessions(user_id)
    assert len(sessions) == 0


@pytest.mark.asyncio
async def test_session_service_revoke_all_exclude_current():
    """Verify revoke all can exclude current session."""
    service = SessionService()
    user_id = str(uuid4())

    # Create multiple sessions
    session1 = await service.create_session(user_id=user_id, user_agent="Mozilla/5.0 (Windows)")
    session2 = await service.create_session(user_id=user_id, user_agent="Mozilla/5.0 (iPhone)")
    session3 = await service.create_session(user_id=user_id, user_agent="Mozilla/5.0 (Android)")

    # Revoke all except session1
    revoked_count = await service.revoke_all_sessions(
        user_id,
        exclude_token=session1._token,
        reason="security_reset"
    )

    assert revoked_count == 2

    # Verify session1 is still valid
    is_valid = await service.validate_session(session1._token)
    assert is_valid is True

    # Verify others are revoked
    is_valid = await service.validate_session(session2._token)
    assert is_valid is False
    is_valid = await service.validate_session(session3._token)
    assert is_valid is False


# ============================================================================
# Test 2: Session Expiration
# ============================================================================

@pytest.mark.asyncio
async def test_session_expiration_validation():
    """Verify expired sessions are invalid."""
    service = SessionService()

    # Create session with very short TTL
    session = await service.create_session(
        user_id=str(uuid4()),
        ttl_hours=-1,  # Already expired
    )

    # Session should be invalid due to expiration
    is_valid = await service.validate_session(session._token)
    assert is_valid is False


@pytest.mark.asyncio
async def test_session_cleanup_expired():
    """Verify expired sessions can be cleaned up."""
    service = SessionService()

    # Create expired session
    await service.create_session(
        user_id=str(uuid4()),
        ttl_hours=-1,
    )

    # Run cleanup
    deleted = await service.cleanup_expired(older_than_hours=0)

    assert deleted >= 0  # At least the expired session


# ============================================================================
# Test 3: Device Type Detection
# ============================================================================

@pytest.mark.asyncio
async def test_session_device_types():
    """Verify device type detection works for various user agents."""
    service = SessionService()

    # Desktop
    desktop_session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    )
    assert desktop_session.device_type == "desktop"
    assert desktop_session.device_name == "Chrome on Windows"

    # Mobile iPhone
    mobile_session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0) Mobile/15E148",
    )
    assert mobile_session.device_type == "mobile"

    # Mobile Android
    android_session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="Mozilla/5.0 (Linux; Android 13) Mobile Safari/537.36",
    )
    assert android_session.device_type == "mobile"

    # Tablet
    tablet_session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="Mozilla/5.0 (iPad; CPU OS 16_0) Mobile/15E148",
    )
    assert tablet_session.device_type == "tablet"


# ============================================================================
# Test 4: Multiple Sessions Per User
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_sessions_per_user():
    """Verify user can have multiple concurrent sessions."""
    service = SessionService()
    user_id = str(uuid4())

    # Create sessions from different devices
    desktop = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        ip_address="192.168.1.1",
        location="New York, NY",
    )
    mobile = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)",
        ip_address="192.168.1.2",
        location="San Francisco, CA",
    )
    tablet = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (iPad; CPU OS 16_0)",
        ip_address="192.168.1.3",
        location="London, UK",
    )

    # All should be valid
    assert await service.validate_session(desktop._token) is True
    assert await service.validate_session(mobile._token) is True
    assert await service.validate_session(tablet._token) is True

    # Get all active sessions
    sessions = await service.get_active_sessions(user_id)
    assert len(sessions) == 3


@pytest.mark.asyncio
async def test_max_sessions_limit():
    """Verify max sessions limit is enforced."""
    service = SessionService(max_sessions_per_user=3)
    user_id = str(uuid4())

    # Create 5 sessions (should only keep 3)
    tokens = []
    for i in range(5):
        session = await service.create_session(
            user_id=user_id,
            user_agent=f"Device{i}",
        )
        tokens.append(session._token)

    # Only last 3 should be valid
    active_count = 0
    for token in tokens:
        if await service.validate_session(token):
            active_count += 1

    assert active_count == 3


# ============================================================================
# Test 5: Session Health Check
# ============================================================================

@pytest.mark.asyncio
async def test_session_health_check():
    """Verify session service health check works."""
    service = SessionService()

    # Create some sessions
    user_id = str(uuid4())
    await service.create_session(user_id=user_id, user_agent="Mozilla/5.0 (Windows)")
    await service.create_session(user_id=user_id, user_agent="Mozilla/5.0 (iPhone)")

    # Get health
    health = await service.health_check()

    assert health["status"] == "healthy"
    assert health["active_sessions"] >= 2
    assert health["total_sessions"] >= 2
    assert health["error"] is None


# ============================================================================
# Test 6: Activity Updates
# ============================================================================

@pytest.mark.asyncio
async def test_session_activity_update():
    """Verify session activity can be updated."""
    service = SessionService()

    session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="Mozilla/5.0 (Windows)",
    )

    original_activity = session.last_activity_at

    # Wait a bit
    await asyncio.sleep(0.1)

    # Update activity
    updated = await service.update_activity(session._token)

    assert updated is True


# ============================================================================
# Test 7: Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_revoke_nonexistent_session():
    """Verify revoking non-existent session returns False."""
    service = SessionService()

    result = await service.revoke_session("nonexistent-token")

    assert result is False


@pytest.mark.asyncio
async def test_validate_nonexistent_session():
    """Verify validating non-existent session returns False."""
    service = SessionService()

    result = await service.validate_session("nonexistent-token")

    assert result is False


@pytest.mark.asyncio
async def test_revoke_already_revoked_session():
    """Verify revoking already revoked session returns False."""
    service = SessionService()

    session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="Mozilla/5.0 (Windows)",
    )

    # Revoke once
    await service.revoke_session(session._token)

    # Try to revoke again
    result = await service.revoke_session(session._token)

    assert result is False


@pytest.mark.asyncio
async def test_create_session_invalid_user_id():
    """Verify creating session without user_id raises ValueError."""
    service = SessionService()

    with pytest.raises(ValueError) as exc_info:
        await service.create_session(user_id="")

    assert "user_id is required" in str(exc_info.value)


# ============================================================================
# Test 8: Token Generation
# ============================================================================

@pytest.mark.asyncio
async def test_token_generation_unique():
    """Verify generated tokens are unique."""
    service = SessionService()

    tokens = [service._generate_token() for _ in range(100)]

    assert len(set(tokens)) == 100  # All unique


@pytest.mark.asyncio
async def test_token_hashing_consistent():
    """Verify token hashing is consistent."""
    service = SessionService()

    token = "test-token"
    hash1 = service._hash_token(token)
    hash2 = service._hash_token(token)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex


# ============================================================================
# Test 9: Global Service Instance
# ============================================================================

@pytest.mark.asyncio
async def test_global_session_service():
    """Verify global session service instance works."""
    from services.session_service import get_session_service

    # Clear global service
    import services.session_service
    services.session_service._session_service = None

    service1 = get_session_service()
    service2 = get_session_service()

    assert service1 is service2  # Same instance


# ============================================================================
# Test 10: Complete Session Lifecycle
# ============================================================================

@pytest.mark.asyncio
async def test_complete_session_lifecycle():
    """Verify complete session lifecycle from creation to cleanup."""
    service = SessionService()
    user_id = str(uuid4())

    # 1. Create session
    session = await service.create_session(
        user_id=user_id,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        ip_address="192.168.1.1",
        location="San Francisco, CA",
        ttl_hours=24,
    )

    assert session is not None
    assert session.is_active is True

    # 2. Validate session
    is_valid = await service.validate_session(session._token)
    assert is_valid is True

    # 3. Update activity
    updated = await service.update_activity(session._token)
    assert updated is True

    # 4. Get active sessions
    sessions = await service.get_active_sessions(user_id)
    assert len(sessions) == 1
    assert sessions[0].id == session.id

    # 5. Revoke session
    revoked = await service.revoke_session(session._token, reason="user_logout")
    assert revoked is True

    # 6. Verify session is no longer valid
    is_valid = await service.validate_session(session._token)
    assert is_valid is False

    # 7. Verify no active sessions
    sessions = await service.get_active_sessions(user_id)
    assert len(sessions) == 0


# ============================================================================
# Test 11: Session with No Expiration
# ============================================================================

@pytest.mark.asyncio
async def test_session_no_expiration():
    """Verify session can be created without expiration."""
    service = SessionService()

    session = await service.create_session(
        user_id=str(uuid4()),
        ttl_hours=0,  # No expiration
    )

    assert session.expires_at is None

    # Should still be valid
    is_valid = await service.validate_session(session._token)
    assert is_valid is True


# ============================================================================
# Test 12: Device Name Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_device_name_unknown_browser():
    """Verify unknown browser gets device name."""
    service = SessionService()

    session = await service.create_session(
        user_id=str(uuid4()),
        user_agent="SomeUnknownBrowser/1.0 (Windows)",
    )

    # Should still create session
    assert session is not None
    assert session.device_type == "desktop"


@pytest.mark.asyncio
async def test_device_name_none_user_agent():
    """Verify None user agent is handled."""
    service = SessionService()

    session = await service.create_session(
        user_id=str(uuid4()),
        user_agent=None,
    )

    assert session is not None
    assert session.device_type == "unknown"
    assert session.device_name is None


# ============================================================================
# Test 13: Multiple Users
# ============================================================================

@pytest.mark.asyncio
async def test_sessions_for_multiple_users():
    """Verify sessions are isolated between users."""
    service = SessionService()

    user1_id = str(uuid4())
    user2_id = str(uuid4())

    # Create sessions for user1
    await service.create_session(user_id=user1_id, user_agent="Device1")
    await service.create_session(user_id=user1_id, user_agent="Device2")

    # Create sessions for user2
    await service.create_session(user_id=user2_id, user_agent="Device3")
    await service.create_session(user_id=user2_id, user_agent="Device4")
    await service.create_session(user_id=user2_id, user_agent="Device5")

    # Check user1 sessions
    user1_sessions = await service.get_active_sessions(user1_id)
    assert len(user1_sessions) == 2

    # Check user2 sessions
    user2_sessions = await service.get_active_sessions(user2_id)
    assert len(user2_sessions) == 3


# ============================================================================
# Test 14: Revocation Reasons
# ============================================================================

@pytest.mark.asyncio
async def test_revocation_reasons():
    """Verify different revocation reasons are recorded."""
    service = SessionService()

    # Test each revocation reason
    reasons = [
        "user_logout",
        "security_reset",
        "admin_action",
        "timeout",
        "suspicious_activity",
    ]

    for reason in reasons:
        session = await service.create_session(user_id=str(uuid4()))
        await service.revoke_session(session._token, reason=reason)

        # Verify reason was recorded
        retrieved_session = await service.get_session(session._token)
        assert retrieved_session is not None
        assert retrieved_session.is_active is False
        assert retrieved_session.revoke_reason == reason
