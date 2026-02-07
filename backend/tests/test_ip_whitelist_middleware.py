"""
Unit Tests for IP Whitelist Middleware

This test module verifies the core IP whitelist middleware functionality including
IP validation against CIDR ranges, IP range matching, client IP extraction from
various headers, path exclusion handling, and whitelist enforcement behavior.

Test Coverage:
- Middleware initialization with default and custom configurations
- Client IP extraction from various headers (X-Forwarded-For, X-Real-IP, CF-Connecting-IP)
- IP validation against CIDR notation (IPv4 and IPv6)
- IP validation against start/end IP ranges
- Path exclusion logic for health endpoints and API docs
- Whitelist enforcement with security config integration
- Strict mode behavior when no whitelist is configured
- Logging of blocked access attempts
- Error handling and fail-open behavior
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import Request, Response, status
from starlette.responses import JSONResponse

from middleware.ip_whitelist_middleware import IPWhitelistMiddleware


class TestMiddlewareInitialization:
    """Test suite for IP whitelist middleware initialization."""

    def test_initialization_with_default_exclude_paths(self):
        """Test middleware initialization with default excluded paths."""
        app = MagicMock()

        middleware = IPWhitelistMiddleware(app)

        assert middleware.app == app
        assert "/health" in middleware.exclude_paths
        assert "/ready" in middleware.exclude_paths
        assert "/docs" in middleware.exclude_paths
        assert "/redoc" in middleware.exclude_paths
        assert "/openapi.json" in middleware.exclude_paths
        assert len(middleware.exclude_paths) == 5

    def test_initialization_with_custom_exclude_paths(self):
        """Test middleware initialization with custom excluded paths."""
        app = MagicMock()
        custom_paths = ["/health", "/custom-status"]

        middleware = IPWhitelistMiddleware(app, exclude_paths=custom_paths)

        assert middleware.exclude_paths == custom_paths
        assert len(middleware.exclude_paths) == 2


class TestPathExclusion:
    """Test suite for path exclusion logic."""

    def test_is_excluded_path_for_health(self):
        """Test that /health path is excluded."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._is_excluded_path("/health") is True
        assert middleware._is_excluded_path("/health/detailed") is True

    def test_is_excluded_path_for_docs(self):
        """Test that documentation paths are excluded."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._is_excluded_path("/docs") is True
        assert middleware._is_excluded_path("/redoc") is True
        assert middleware._is_excluded_path("/openapi.json") is True

    def test_is_excluded_path_for_api_endpoints(self):
        """Test that API endpoints are not excluded."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._is_excluded_path("/api/resumes") is False
        assert middleware._is_excluded_path("/api/jobs") is False
        assert middleware._is_excluded_path("/api/security/config") is False


class TestClientIPExtraction:
    """Test suite for client IP extraction from request headers."""

    @pytest.mark.asyncio
    async def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting client IP from X-Forwarded-For header."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        # Create mock request with X-Forwarded-For header
        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}

        client_ip = middleware._get_client_ip(request)

        assert client_ip == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_client_ip_from_x_real_ip(self):
        """Test extracting client IP from X-Real-IP header."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        request = MagicMock(spec=Request)
        request.headers = {"X-Real-IP": "192.168.1.100"}

        client_ip = middleware._get_client_ip(request)

        assert client_ip == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_client_ip_from_cf_connecting_ip(self):
        """Test extracting client IP from CF-Connecting-IP header (Cloudflare)."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        request = MagicMock(spec=Request)
        request.headers = {"CF-Connecting-IP": "192.168.1.100"}

        client_ip = middleware._get_client_ip(request)

        assert client_ip == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_client_ip_from_client_host(self):
        """Test extracting client IP from request.client.host as fallback."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        client_ip = middleware._get_client_ip(request)

        assert client_ip == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_client_ip_priority_order(self):
        """Test that X-Forwarded-For takes priority over other headers."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        request = MagicMock(spec=Request)
        request.headers = {
            "X-Forwarded-For": "1.1.1.1",
            "X-Real-IP": "2.2.2.2",
            "CF-Connecting-IP": "3.3.3.3",
        }
        request.client = MagicMock()
        request.client.host = "4.4.4.4"

        client_ip = middleware._get_client_ip(request)

        assert client_ip == "1.1.1.1"

    @pytest.mark.asyncio
    async def test_get_client_ip_returns_none_when_not_found(self):
        """Test that None is returned when no IP can be extracted."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = None

        client_ip = middleware._get_client_ip(request)

        assert client_ip is None


class TestCIDRValidation:
    """Test suite for CIDR notation IP validation."""

    def test_ip_in_cidr_ipv4_single_ip(self):
        """Test CIDR validation for /32 (single IP)."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_cidr("192.168.1.100", "192.168.1.100/32") is True
        assert middleware._ip_in_cidr("192.168.1.101", "192.168.1.100/32") is False

    def test_ip_in_cidr_ipv4_class_c(self):
        """Test CIDR validation for /24 network."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_cidr("192.168.1.1", "192.168.1.0/24") is True
        assert middleware._ip_in_cidr("192.168.1.255", "192.168.1.0/24") is True
        assert middleware._ip_in_cidr("192.168.2.1", "192.168.1.0/24") is False

    def test_ip_in_cidr_ipv4_class_b(self):
        """Test CIDR validation for /16 network."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_cidr("10.0.1.1", "10.0.0.0/16") is True
        assert middleware._ip_in_cidr("10.0.255.255", "10.0.0.0/16") is True
        assert middleware._ip_in_cidr("10.1.0.1", "10.0.0.0/16") is False

    def test_ip_in_cidr_ipv4_class_a(self):
        """Test CIDR validation for /8 network."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_cidr("10.1.2.3", "10.0.0.0/8") is True
        assert middleware._ip_in_cidr("10.255.255.255", "10.0.0.0/8") is True
        assert middleware._ip_in_cidr("11.0.0.1", "10.0.0.0/8") is False

    def test_ip_in_cidr_ipv6(self):
        """Test CIDR validation for IPv6 addresses."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_cidr("2001:db8::1", "2001:db8::/32") is True
        assert middleware._ip_in_cidr("2001:db8:ffff::1", "2001:db8::/32") is True
        assert middleware._ip_in_cidr("2001:db9::1", "2001:db8::/32") is False

    def test_ip_in_cidr_invalid_cidr(self):
        """Test that invalid CIDR notation returns False."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_cidr("192.168.1.1", "invalid-cidr") is False
        assert middleware._ip_in_cidr("192.168.1.1", "192.168.1.0/33") is False  # Invalid prefix

    def test_ip_in_cidr_invalid_ip(self):
        """Test that invalid IP address returns False."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_cidr("not-an-ip", "192.168.1.0/24") is False


class TestIPRangeValidation:
    """Test suite for IP range validation (start/end IPs)."""

    def test_ip_in_range_ipv4_basic(self):
        """Test IP range validation for basic IPv4 range."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_range("192.168.1.50", "192.168.1.1", "192.168.1.100") is True
        assert middleware._ip_in_range("192.168.1.1", "192.168.1.1", "192.168.1.100") is True
        assert middleware._ip_in_range("192.168.1.100", "192.168.1.1", "192.168.1.100") is True
        assert middleware._ip_in_range("192.168.1.0", "192.168.1.1", "192.168.1.100") is False
        assert middleware._ip_in_range("192.168.1.101", "192.168.1.1", "192.168.1.100") is False

    def test_ip_in_range_ipv6(self):
        """Test IP range validation for IPv6 addresses."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_range("2001:db8::50", "2001:db8::1", "2001:db8::100") is True
        assert middleware._ip_in_range("2001:db8::101", "2001:db8::1", "2001:db8::100") is False

    def test_ip_in_range_invalid_ips(self):
        """Test that invalid IP addresses return False."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        assert middleware._ip_in_range("not-an-ip", "192.168.1.1", "192.168.1.100") is False
        assert middleware._ip_in_range("192.168.1.50", "not-valid", "192.168.1.100") is False
        assert middleware._ip_in_range("192.168.1.50", "192.168.1.1", "not-valid") is False


class TestIPMatchingWithWhitelistEntry:
    """Test suite for IP matching against whitelist entries."""

    def test_ip_matches_rule_with_cidr(self):
        """Test IP matching against CIDR whitelist entry."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        # Create mock whitelist entry with CIDR
        whitelist_entry = MagicMock()
        whitelist_entry.cidr_notation = "192.168.1.0/24"
        whitelist_entry.start_ip = None
        whitelist_entry.end_ip = None

        assert middleware._ip_matches_rule("192.168.1.100", whitelist_entry) is True
        assert middleware._ip_matches_rule("192.168.2.1", whitelist_entry) is False

    def test_ip_matches_rule_with_ip_range(self):
        """Test IP matching against IP range whitelist entry."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        whitelist_entry = MagicMock()
        whitelist_entry.cidr_notation = None
        whitelist_entry.start_ip = "192.168.1.1"
        whitelist_entry.end_ip = "192.168.1.100"

        assert middleware._ip_matches_rule("192.168.1.50", whitelist_entry) is True
        assert middleware._ip_matches_rule("192.168.1.101", whitelist_entry) is False

    def test_ip_matches_rule_with_both_cidr_and_range(self):
        """Test IP matching when both CIDR and range are specified (CIDR takes priority)."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        whitelist_entry = MagicMock()
        whitelist_entry.cidr_notation = "10.0.0.0/8"
        whitelist_entry.start_ip = "192.168.1.1"
        whitelist_entry.end_ip = "192.168.1.100"

        # CIDR should match
        assert middleware._ip_matches_rule("10.1.2.3", whitelist_entry) is True

    def test_ip_matches_rule_with_no_rules(self):
        """Test IP matching when no CIDR or range is specified."""
        app = MagicMock()
        middleware = IPWhitelistMiddleware(app)

        whitelist_entry = MagicMock()
        whitelist_entry.cidr_notation = None
        whitelist_entry.start_ip = None
        whitelist_entry.end_ip = None

        assert middleware._ip_matches_rule("192.168.1.100", whitelist_entry) is False


class TestDispatchLogic:
    """Test suite for request dispatch logic through middleware."""

    @pytest.mark.asyncio
    async def test_excluded_path_passes_through(self):
        """Test that excluded paths pass through without IP validation."""
        app = MagicMock()
        call_next = AsyncMock(return_value=Response())
        middleware = IPWhitelistMiddleware(app)

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/health"

        response = await middleware.dispatch(request, call_next)

        assert call_next.called
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_with_no_client_ip_passes_through(self):
        """Test that requests with no extractable client IP pass through (fail open)."""
        app = MagicMock()
        call_next = AsyncMock(return_value=Response())
        middleware = IPWhitelistMiddleware(app)

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.headers = {}
        request.client = None

        response = await middleware.dispatch(request, call_next)

        assert call_next.called
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("middleware.ip_whitelist_middleware.async_session_maker")
    async def test_allowed_ip_passes_through(self, mock_session_maker):
        """Test that allowed IPs pass through middleware."""
        app = MagicMock()
        call_next = AsyncMock(return_value=Response())
        middleware = IPWhitelistMiddleware(app)

        # Mock database session
        mock_db = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_db

        # Mock security config (IP whitelist disabled)
        from models.security_config import SecurityConfig
        mock_config = MagicMock(spec=SecurityConfig)
        mock_config.ip_whitelist_enabled = False

        # Mock database query results
        from sqlalchemy import select
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        request.method = "GET"

        response = await middleware.dispatch(request, call_next)

        assert call_next.called
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("middleware.ip_whitelist_middleware.async_session_maker")
    async def test_blocked_ip_returns_403(self, mock_session_maker):
        """Test that blocked IPs receive 403 Forbidden response."""
        app = MagicMock()
        call_next = AsyncMock(return_value=Response())
        middleware = IPWhitelistMiddleware(app)

        # Mock database session
        mock_db = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_db

        # Mock security config (IP whitelist enabled, strict mode)
        from models.security_config import SecurityConfig
        mock_config = MagicMock(spec=SecurityConfig)
        mock_config.ip_whitelist_enabled = True
        mock_config.ip_whitelist_strict = True

        # Mock empty whitelist
        from models.ip_whitelist import IPWhitelist
        mock_whitelist_result = MagicMock()
        mock_whitelist_result.scalars.return_value.all.return_value = []

        # Setup database query to return different results
        execute_results = [MagicMock(), MagicMock()]
        execute_results[0].scalar_one_or_none.return_value = mock_config
        execute_results[1].scalars.return_value.all.return_value = []

        async def mock_execute(query):
            if "SecurityConfig" in str(query):
                return execute_results[0]
            else:
                return execute_results[1]

        mock_db.execute = mock_execute

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        request.method = "GET"

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not call_next.called


class TestErrorHandling:
    """Test suite for error handling in middleware."""

    @pytest.mark.asyncio
    @patch("middleware.ip_whitelist_middleware.async_session_maker")
    async def test_database_error_fails_open(self, mock_session_maker):
        """Test that database errors cause middleware to fail open (allow request)."""
        app = MagicMock()
        call_next = AsyncMock(return_value=Response())
        middleware = IPWhitelistMiddleware(app)

        # Mock database session to raise exception
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection error")
        mock_session_maker.return_value.__aenter__.return_value = mock_db

        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/api/test"
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"
        request.method = "GET"

        response = await middleware.dispatch(request, call_next)

        # Should fail open and allow request
        assert call_next.called
        assert response.status_code == 200
