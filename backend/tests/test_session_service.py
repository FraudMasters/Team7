"""
Unit Tests for Session Service

This test module verifies the core session management functionality including
session creation, validation, revocation, token generation, device parsing,
and session cleanup.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.session_service import SessionService, get_session_service


class TestSessionServiceInitialization:
    """Test suite for session service initialization."""

    def test_initialization_with_defaults(self):
        """Test session service initialization with default settings."""
        service = SessionService()

        assert service.default_ttl_hours == 24
        assert service.cleanup_batch_size == 100
        assert service.max_sessions_per_user == 10

    def test_initialization_with_custom_config(self):
        """Test session service initialization with custom configuration."""
        service = SessionService(
            default_ttl_hours=48,
            cleanup_batch_size=200,
            max_sessions_per_user=5,
        )

        assert service.default_ttl_hours == 48
        assert service.cleanup_batch_size == 200
        assert service.max_sessions_per_user == 5

    def test_initialization_unlimited_sessions(self):
        """Test session service initialization with unlimited sessions."""
        service = SessionService(max_sessions_per_user=0)

        assert service.max_sessions_per_user == 0


class TestTokenGeneration:
    """Test suite for token generation and hashing."""

    def test_generate_token(self):
        """Test token generation produces unique, secure tokens."""
        service = SessionService()

        token = service._generate_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) == 43  # URL-safe base64 of 32 bytes

    def test_generate_tokens_unique(self):
        """Test that generated tokens are unique."""
        service = SessionService()

        tokens = [service._generate_token() for _ in range(100)]

        assert len(set(tokens)) == 100  # All tokens should be unique

    def test_hash_token(self):
        """Test token hashing produces consistent SHA-256 hashes."""
        service = SessionService()

        token = "my-test-token"
        hash1 = service._hash_token(token)
        hash2 = service._hash_token(token)

        assert hash1 == hash2  # Same token should produce same hash
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_hash_token_different_for_different_tokens(self):
        """Test that different tokens produce different hashes."""
        service = SessionService()

        hash1 = service._hash_token("token1")
        hash2 = service._hash_token("token2")

        assert hash1 != hash2


class TestDeviceTypeParsing:
    """Test suite for device type parsing from user agent strings."""

    def test_parse_desktop_chrome(self):
        """Test parsing Chrome desktop user agent."""
        service = SessionService()

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        device_type = service._parse_device_type(ua)

        assert device_type == "desktop"

    def test_parse_mobile_iphone(self):
        """Test parsing iPhone user agent."""
        service = SessionService()

        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        device_type = service._parse_device_type(ua)

        assert device_type == "mobile"

    def test_parse_mobile_android(self):
        """Test parsing Android user agent."""
        service = SessionService()

        ua = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36"
        device_type = service._parse_device_type(ua)

        assert device_type == "mobile"

    def test_parse_tablet_ipad(self):
        """Test parsing iPad user agent."""
        service = SessionService()

        ua = "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        device_type = service._parse_device_type(ua)

        assert device_type == "tablet"

    def test_parse_tablet_kindle(self):
        """Test parsing Kindle user agent."""
        service = SessionService()

        ua = "Mozilla/5.0 (Linux; U; Android 4.4.3; en-us; Kindle Fire HDX Build/KTU84M) AppleWebKit/537.36 (KHTML, like Gecko) Silk/3.66 like Chrome/39.0.2171.93 Mobile Safari/537.36"
        device_type = service._parse_device_type(ua)

        assert device_type == "tablet"

    def test_parse_unknown_none(self):
        """Test parsing None user agent returns unknown."""
        service = SessionService()

        device_type = service._parse_device_type(None)

        assert device_type == "unknown"

    def test_parse_unknown_empty_string(self):
        """Test parsing empty user agent returns unknown."""
        service = SessionService()

        device_type = service._parse_device_type("")

        assert device_type == "unknown"


class TestDeviceNameGeneration:
    """Test suite for device name generation."""

    def test_generate_device_name_chrome_windows(self):
        """Test generating device name for Chrome on Windows."""
        service = SessionService()

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        name = service._generate_device_name(ua)

        assert name == "Chrome on Windows"

    def test_generate_device_name_safari_macos(self):
        """Test generating device name for Safari on macOS."""
        service = SessionService()

        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
        name = service._generate_device_name(ua)

        assert name == "Safari on macOS"

    def test_generate_device_name_firefox_linux(self):
        """Test generating device name for Firefox on Linux."""
        service = SessionService()

        ua = "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/120.0"
        name = service._generate_device_name(ua)

        assert name == "Firefox on Linux"

    def test_generate_device_name_edge_windows(self):
        """Test generating device name for Edge on Windows."""
        service = SessionService()

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        name = service._generate_device_name(ua)

        assert name == "Edge on Windows"

    def test_generate_device_name_ios(self):
        """Test generating device name for iOS Safari."""
        service = SessionService()

        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        name = service._generate_device_name(ua)

        assert name == "Safari on iOS"

    def test_generate_device_name_android(self):
        """Test generating device name for Android Chrome."""
        service = SessionService()

        ua = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36"
        name = service._generate_device_name(ua)

        assert name == "Chrome on Android"

    def test_generate_device_name_none(self):
        """Test generating device name for None returns None."""
        service = SessionService()

        name = service._generate_device_name(None)

        assert name is None


class TestSessionCreation:
    """Test suite for session creation."""

    @pytest.mark.asyncio
    async def test_create_session_minimal(self):
        """Test creating a session with minimal parameters."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.id = "session-1"
        mock_session._token = "generated-token"

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            with patch.object(service, "_parse_device_type", return_value="desktop"):
                with patch.object(service, "_generate_device_name", return_value="Chrome on Windows"):
                    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
                    mock_db.commit = AsyncMock()
                    mock_db.refresh = AsyncMock()
                    mock_db.add = MagicMock()

                    with patch("services.session_service.SessionModel") as mock_model:
                        mock_model.return_value = mock_session

                        result = await service.create_session(user_id="user-123")

                        assert result is not None

    @pytest.mark.asyncio
    async def test_create_session_with_all_parameters(self):
        """Test creating a session with all parameters."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.id = "session-1"
        mock_session._token = "custom-token"

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            with patch.object(service, "_parse_device_type", return_value="mobile"):
                with patch.object(service, "_generate_device_name", return_value="Safari on iOS"):
                    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
                    mock_db.commit = AsyncMock()
                    mock_db.refresh = AsyncMock()
                    mock_db.add = MagicMock()

                    with patch("services.session_service.SessionModel") as mock_model:
                        mock_model.return_value = mock_session

                        result = await service.create_session(
                            user_id="user-123",
                            token="custom-token",
                            user_agent="Mozilla/5.0 (iPhone...",
                            ip_address="192.168.1.1",
                            location="San Francisco, CA",
                            ttl_hours=48,
                        )

                        assert result is not None

    @pytest.mark.asyncio
    async def test_create_session_invalid_user_id(self):
        """Test that creating session without user_id raises ValueError."""
        service = SessionService()

        with pytest.raises(ValueError) as exc_info:
            await service.create_session(user_id="")

        assert "user_id is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_session_auto_generates_token(self):
        """Test that session creation auto-generates token if not provided."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.id = "session-1"
        mock_session._token = "auto-token"

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            with patch.object(service, "_generate_token", return_value="auto-token"):
                with patch.object(service, "_parse_device_type", return_value="desktop"):
                    with patch.object(service, "_generate_device_name", return_value="Chrome on Windows"):
                        mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
                        mock_db.commit = AsyncMock()
                        mock_db.refresh = AsyncMock()
                        mock_db.add = MagicMock()

                        with patch("services.session_service.SessionModel") as mock_model:
                            mock_model.return_value = mock_session

                            result = await service.create_session(user_id="user-123")

                            assert result._token == "auto-token"

    @pytest.mark.asyncio
    async def test_create_session_exceeds_max_sessions(self):
        """Test that oldest sessions are revoked when max is exceeded."""
        service = SessionService(max_sessions_per_user=3)

        # Create mock existing sessions
        existing_sessions = [MagicMock(id=f"session-{i}") for i in range(3)]

        # Add a fourth session to trigger revocation
        new_session = MagicMock()
        new_session.id = "session-4"
        new_session._token = "new-token"

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            with patch.object(service, "_parse_device_type", return_value="desktop"):
                with patch.object(service, "_generate_device_name", return_value="Chrome on Windows"):
                    # First call returns 3 existing sessions, second returns empty
                    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(side_effect=[existing_sessions, []]))))
                    mock_db.commit = AsyncMock()
                    mock_db.refresh = AsyncMock()
                    mock_db.add = MagicMock()

                    with patch("services.session_service.SessionModel") as mock_model:
                        mock_model.return_value = new_session

                        result = await service.create_session(user_id="user-123")

                        # Verify oldest session was marked as revoked
                        oldest_session = existing_sessions[-1]
                        assert oldest_session.is_active == False
                        assert oldest_session.revoked_at is not None


class TestSessionValidation:
    """Test suite for session validation."""

    @pytest.mark.asyncio
    async def test_validate_session_valid(self):
        """Test validating a valid session."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.is_active = True
        mock_session.expires_at = None

        with patch.object(service, "get_session", return_value=mock_session):
            with patch("services.session_service.async_session_maker") as mock_maker:
                mock_db = AsyncMock()
                mock_maker.return_value.__aenter__.return_value = mock_db
                mock_db.commit = AsyncMock()
                mock_db.add = MagicMock()

                result = await service.validate_session("valid-token")

                assert result is True

    @pytest.mark.asyncio
    async def test_validate_session_not_found(self):
        """Test validating a non-existent session returns False."""
        service = SessionService()

        with patch.object(service, "get_session", return_value=None):
            result = await service.validate_session("invalid-token")

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_session_revoked(self):
        """Test validating a revoked session returns False."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.is_active = False
        mock_session.is_valid.return_value = False

        with patch.object(service, "get_session", return_value=mock_session):
            result = await service.validate_session("revoked-token")

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_session_expired(self):
        """Test validating an expired session returns False."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.is_active = True
        mock_session.expires_at = datetime.now() - timedelta(hours=1)
        mock_session.is_valid.return_value = False

        with patch.object(service, "get_session", return_value=mock_session):
            result = await service.validate_session("expired-token")

            assert result is False


class TestSessionRetrieval:
    """Test suite for session retrieval."""

    @pytest.mark.asyncio
    async def test_get_session_by_token(self):
        """Test retrieving a session by token."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.id = "session-1"

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_db.execute.return_value = mock_result

            result = await service.get_session("token-123")

            assert result is not None
            assert result.id == "session-1"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Test retrieving non-existent session returns None."""
        service = SessionService()

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            result = await service.get_session("invalid-token")

            assert result is None


class TestSessionRevocation:
    """Test suite for session revocation."""

    @pytest.mark.asyncio
    async def test_revoke_session_success(self):
        """Test revoking a session successfully."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.id = "session-1"
        mock_session.is_active = True

        with patch.object(service, "get_session", return_value=mock_session):
            with patch("services.session_service.async_session_maker") as mock_maker:
                mock_db = AsyncMock()
                mock_maker.return_value.__aenter__.return_value = mock_db
                mock_db.commit = AsyncMock()
                mock_db.add = MagicMock()

                result = await service.revoke_session("token-123", reason="user_logout")

                assert result is True
                assert mock_session.is_active == False
                assert mock_session.revoked_at is not None
                assert mock_session.revoke_reason == "user_logout"

    @pytest.mark.asyncio
    async def test_revoke_session_not_found(self):
        """Test revoking non-existent session returns False."""
        service = SessionService()

        with patch.object(service, "get_session", return_value=None):
            result = await service.revoke_session("invalid-token")

            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_session_already_revoked(self):
        """Test revoking an already revoked session returns False."""
        service = SessionService()

        mock_session = MagicMock()
        mock_session.is_active = False

        with patch.object(service, "get_session", return_value=mock_session):
            result = await service.revoke_session("already-revoked-token")

            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_sessions(self):
        """Test revoking all sessions for a user."""
        service = SessionService()

        mock_sessions = [
            MagicMock(id=f"session-{i}", is_active=True) for i in range(3)
        ]

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_sessions
            mock_db.execute.return_value = mock_result
            mock_db.commit = AsyncMock()
            mock_db.add = MagicMock()

            count = await service.revoke_all_sessions("user-123", reason="security_reset")

            assert count == 3
            for session in mock_sessions:
                assert session.is_active == False
                assert session.revoked_at is not None
                assert session.revoke_reason == "security_reset"

    @pytest.mark.asyncio
    async def test_revoke_all_sessions_exclude_current(self):
        """Test revoking all sessions except current."""
        service = SessionService()

        current_token = "current-token"
        exclude_hash = service._hash_token(current_token)

        current_session = MagicMock(id="session-1", is_active=True)
        other_sessions = [MagicMock(id=f"session-{i}", is_active=True) for i in range(2, 4)]

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            # First call: return sessions without exclusion
            # We'll manually set up the mock to filter properly
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = other_sessions
            mock_db.execute.return_value = mock_result
            mock_db.commit = AsyncMock()
            mock_db.add = MagicMock()

            count = await service.revoke_all_sessions(
                "user-123",
                exclude_token=current_token,
                reason="security_reset"
            )

            assert count == 2  # Only other sessions, not current
            for session in other_sessions:
                assert session.is_active == False


class TestGetActiveSessions:
    """Test suite for getting active sessions."""

    @pytest.mark.asyncio
    async def test_get_active_sessions_for_user(self):
        """Test retrieving all active sessions for a user."""
        service = SessionService()

        mock_sessions = [
            MagicMock(id=f"session-{i}", is_active=True) for i in range(3)
        ]

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_sessions
            mock_db.execute.return_value = mock_result

            result = await service.get_active_sessions("user-123")

            assert len(result) == 3
            assert all(s.is_active for s in result)

    @pytest.mark.asyncio
    async def test_get_active_sessions_empty(self):
        """Test retrieving active sessions when user has none."""
        service = SessionService()

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            result = await service.get_active_sessions("user-123")

            assert len(result) == 0


class TestActivityUpdate:
    """Test suite for activity timestamp updates."""

    @pytest.mark.asyncio
    async def test_update_activity_success(self):
        """Test updating session activity timestamp."""
        service = SessionService()

        mock_session = MagicMock()

        with patch.object(service, "get_session", return_value=mock_session):
            with patch("services.session_service.async_session_maker") as mock_maker:
                mock_db = AsyncMock()
                mock_maker.return_value.__aenter__.return_value = mock_db
                mock_db.commit = AsyncMock()
                mock_db.add = MagicMock()

                result = await service.update_activity("token-123")

                assert result is True
                assert mock_session.last_activity_at is not None

    @pytest.mark.asyncio
    async def test_update_activity_session_not_found(self):
        """Test updating activity for non-existent session returns False."""
        service = SessionService()

        with patch.object(service, "get_session", return_value=None):
            result = await service.update_activity("invalid-token")

            assert result is False


class TestSessionCleanup:
    """Test suite for session cleanup operations."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        service = SessionService()

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            # Mock delete results
            mock_result1 = MagicMock(rowcount=5)
            mock_result2 = MagicMock(rowcount=3)
            mock_db.execute.return_value = MagicMock(side_effect=[mock_result1, mock_result2])
            mock_db.commit = AsyncMock()

            deleted = await service.cleanup_expired(older_than_hours=24)

            assert deleted == 8  # 5 expired + 3 revoked

    @pytest.mark.asyncio
    async def test_cleanup_no_sessions(self):
        """Test cleanup when no sessions to delete."""
        service = SessionService()

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock(rowcount=0)
            mock_db.execute.return_value = mock_result
            mock_db.commit = AsyncMock()

            deleted = await service.cleanup_expired()

            assert deleted == 0


class TestHealthCheck:
    """Test suite for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check returns healthy status."""
        service = SessionService()

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db

            # Mock session counts
            def mock_scalars_side_effect(*args, **kwargs):
                mock_scalars = MagicMock()
                if "expires_at" in str(args):  # Expired query
                    mock_scalars.all.return_value = []
                else:  # Active and total queries
                    mock_scalars.all.return_value = [MagicMock()] * 10
                return mock_scalars

            mock_execute_result = MagicMock()
            mock_execute_result.scalars.side_effect = mock_scalars_side_effect
            mock_db.execute.return_value = mock_execute_result

            result = await service.health_check()

            assert result["status"] == "healthy"
            assert result["active_sessions"] == 10
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_health_check_with_error(self):
        """Test health check handles errors gracefully."""
        service = SessionService()

        with patch("services.session_service.async_session_maker") as mock_maker:
            mock_db = AsyncMock()
            mock_maker.return_value.__aenter__.return_value = mock_db
            mock_db.execute.side_effect = Exception("Database error")

            result = await service.health_check()

            assert result["status"] == "unhealthy"
            assert "Database error" in result["error"]


class TestGlobalServiceInstance:
    """Test suite for global session service instance."""

    def test_get_session_service_singleton(self):
        """Test that get_session_service returns singleton instance."""
        # Clear global service
        import services.session_service
        services.session_service._session_service = None

        service1 = get_session_service()
        service2 = get_session_service()

        assert service1 is service2

    def test_get_session_service_creates_once(self):
        """Test that service is created only once."""
        # Clear global service
        import services.session_service
        services.session_service._session_service = None

        with patch("services.session_service.SessionService") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            service1 = get_session_service()
            service2 = get_session_service()

            # Should only create once
            assert mock_class.call_count == 1
            assert service1 is mock_instance
            assert service2 is mock_instance
