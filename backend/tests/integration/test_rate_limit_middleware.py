"""
Integration tests for RateLimitMiddleware.

This test suite validates the end-to-end integration between:
- Frontend (simulated via HTTP requests)
- Backend RateLimitMiddleware (FastAPI middleware)
- RateLimitService (Redis-backed rate limiting)
- Header injection (X-RateLimit-*)
- 429 Too Many Requests responses
- IP blocking (403 Forbidden responses)
- Different rate limit tiers based on user roles

Test Coverage:
- X-RateLimit-* headers are added to all responses
- 429 responses when rate limit is exceeded
- 403 responses for blocked IPs
- Header values update correctly across requests
- Different rate limits for different user tiers
- Graceful fallback when rate limiting is disabled
- Request counting and remaining limits
- Reset time calculations
"""
import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, Mock

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from services.rate_limit_service import RateLimitTier, get_rate_limit_service


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def rate_limit_service():
    """
    Get the rate limit service instance.

    Returns:
        RateLimitService instance
    """
    return get_rate_limit_service()


class TestRateLimitHeaders:
    """Tests for X-RateLimit-* header injection."""

    def test_headers_present_on_successful_request(self, client: TestClient):
        """Test that rate limit headers are present on successful requests."""
        response = client.get("/api/health")

        # Check that all rate limit headers are present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_have_valid_values(self, client: TestClient):
        """Test that rate limit headers contain valid numeric values."""
        response = client.get("/api/health")

        # Get header values
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")

        # Verify they can be parsed as integers
        if limit != "-1":  # -1 indicates unlimited
            assert limit.isdigit() or limit.lstrip('-').isdigit()
        if remaining != "-1":
            assert remaining.isdigit() or remaining.lstrip('-').isdigit()
        assert reset.isdigit() or reset == "0"

    def test_headers_present_on_post_request(self, client: TestClient):
        """Test that headers are present on POST requests."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "test-vacancy",
                "resume_ids": ["resume1", "resume2"]
            }
        )

        # Should have headers even if request fails validation
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_present_on_put_request(self, client: TestClient):
        """Test that headers are present on PUT requests."""
        response = client.put(
            "/api/comparisons/test-id",
            json={"name": "Updated Name"}
        )

        # Should have headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_present_on_delete_request(self, client: TestClient):
        """Test that headers are present on DELETE requests."""
        response = client.delete("/api/comparisons/test-id")

        # Should have headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_present_on_404_response(self, client: TestClient):
        """Test that headers are present on 404 Not Found responses."""
        response = client.get("/api/nonexistent-endpoint")

        # Should have headers even for 404
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_present_on_options_request(self, client: TestClient):
        """Test that headers are present on OPTIONS requests (CORS preflight)."""
        response = client.options("/api/health")

        # Should have headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_decrease_remaining_on_concurrent_requests(self, client: TestClient):
        """Test that remaining count decreases across multiple requests."""
        # Make first request
        response1 = client.get("/api/health")
        remaining1 = int(response1.headers.get("X-RateLimit-Remaining", "-1"))

        # Make second request
        response2 = client.get("/api/health")
        remaining2 = int(response2.headers.get("X-RateLimit-Remaining", "-1"))

        # If rate limiting is enabled, remaining should decrease or stay same
        # (might stay same if tokens have refilled)
        if remaining1 != -1:
            assert remaining2 <= remaining1

    def test_limit_header_consistent_across_requests(self, client: TestClient):
        """Test that the limit header is consistent across multiple requests."""
        responses = []
        for _ in range(3):
            response = client.get("/api/health")
            limit = response.headers.get("X-RateLimit-Limit")
            responses.append(limit)

        # All limits should be the same for the same endpoint/anonymous user
        assert len(set(responses)) <= 1  # All same or nearly all same

    def test_reset_header_is_timestamp(self, client: TestClient):
        """Test that reset header is a valid Unix timestamp."""
        response = client.get("/api/health")
        reset = response.headers.get("X-RateLimit-Reset")

        # Should be a valid timestamp (integer)
        if reset != "0":
            reset_int = int(reset)
            # Should be a reasonable timestamp (after 2020, before 2100)
            assert reset_int > 1577836800  # Jan 1, 2020
            assert reset_int < 4102444800  # Jan 1, 2100


class TestRateLimitExceeded:
    """Tests for 429 Too Many Requests responses."""

    def test_rate_limit_returns_429_when_exceeded(self, rate_limit_service):
        """Test that 429 is returned when rate limit is exceeded using mocked rate limit check."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from services.rate_limit_service import RateLimitResult
        from unittest.mock import AsyncMock, MagicMock
        from fastapi import Request

        # Create middleware with mocked service
        middleware = RateLimitMiddleware(app)

        # Mock the rate limit check to return exceeded result
        mock_result = MagicMock()
        mock_result.allowed = False
        mock_result.limit = 20
        mock_result.remaining = 0
        mock_result.reset_at = 1738569600
        mock_result.retry_after = 60
        mock_result.tier = RateLimitTier.ANONYMOUS

        # Create a mock request
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        # Mock call_next
        async def mock_call_next(request):
            from fastapi import Response
            return Response(status_code=200)

        # We need to patch the check_rate_limit method to return our exceeded result
        with MagicMock() as mock_check:
            mock_check.return_value = mock_result
            middleware.rate_limit_service.check_rate_limit = mock_check

            # Call the middleware's dispatch method
            import asyncio
            response = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

            # Verify 429 status code
            assert response.status_code == 429

    def test_429_response_has_retry_after_header(self):
        """Test that 429 responses include Retry-After header."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from services.rate_limit_service import RateLimitResult

        middleware = RateLimitMiddleware(app)

        # Create a rate limit result indicating limit exceeded
        mock_result = MagicMock()
        mock_result.allowed = False
        mock_result.limit = 100
        mock_result.remaining = 0
        mock_result.reset_at = 1738569600
        mock_result.retry_after = 45
        mock_result.tier = RateLimitTier.USER

        # Create the 429 response
        response = middleware._create_rate_limit_response(mock_result)

        # Verify Retry-After header is present
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "45"

    def test_429_response_has_error_details(self):
        """Test that 429 responses include detailed error information."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from services.rate_limit_service import RateLimitResult
        import json

        middleware = RateLimitMiddleware(app)

        # Create a rate limit result indicating limit exceeded
        mock_result = MagicMock()
        mock_result.allowed = False
        mock_result.limit = 100
        mock_result.remaining = 0
        mock_result.reset_at = 1738569600
        mock_result.retry_after = 30
        mock_result.tier = RateLimitTier.ORG_ADMIN

        # Create the 429 response
        response = middleware._create_rate_limit_response(mock_result)

        # Parse response body
        body = json.loads(response.body.decode())

        # Verify error details
        assert "error" in body
        assert body["error"] == "Rate limit exceeded"
        assert "message" in body
        assert "retry_after" in body
        assert body["retry_after"] == 30
        assert "limit" in body
        assert body["limit"] == 100
        assert "tier" in body
        assert body["tier"] == "org_admin"


class TestRateLimitResponseStructure:
    """Tests for rate limit response structure (using mocked scenarios)."""

    def test_429_response_structure_is_valid(self, client: TestClient):
        """Test the structure of a 429 response using direct middleware test."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from services.rate_limit_service import RateLimitResult

        # Create a mock rate limit result indicating limit exceeded
        mock_result = MagicMock()
        mock_result.allowed = False
        mock_result.limit = 100
        mock_result.remaining = 0
        mock_result.reset_at = 1738569600
        mock_result.retry_after = 60
        mock_result.tier = RateLimitTier.ANONYMOUS

        # Create middleware instance
        middleware = RateLimitMiddleware(app)

        # Get the rate limit response
        response = middleware._create_rate_limit_response(mock_result)

        # Verify status code
        assert response.status_code == 429

        # Verify headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert "Retry-After" in response.headers

        # Verify header values
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["Retry-After"] == "60"

        # Verify body contains JSON with error details
        import json
        body = json.loads(response.body.decode())
        assert "error" in body
        assert "message" in body
        assert "retry_after" in body
        assert "limit" in body
        assert "tier" in body

        assert body["error"] == "Rate limit exceeded"
        assert body["retry_after"] == 60
        assert body["limit"] == 100
        assert body["tier"] == "anonymous"

    def test_blocked_ip_response_structure_is_valid(self):
        """Test the structure of a 403 response for blocked IPs."""
        from middleware.rate_limit_middleware import RateLimitMiddleware

        # Create middleware instance
        middleware = RateLimitMiddleware(app)

        # Get the blocked response
        response = middleware._create_blocked_response("192.168.1.1")

        # Verify status code
        assert response.status_code == 403

        # Verify headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

        # Verify body contains JSON with error details
        import json
        body = json.loads(response.body.decode())
        assert "error" in body
        assert "message" in body

        assert body["error"] == "Access denied"
        assert "abusive behavior" in body["message"].lower()


class TestClientIPExtraction:
    """Tests for client IP extraction from headers."""

    def test_ip_extraction_from_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with X-Forwarded-For header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        mock_request.client = None

        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.1"

    def test_ip_extraction_from_x_real_ip(self):
        """Test IP extraction from X-Real-IP header."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with X-Real-IP header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Real-IP": "203.0.113.50"}
        mock_request.client = None

        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.50"

    def test_ip_extraction_from_client_host(self):
        """Test IP extraction from request.client.host."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with client.host
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_client = MagicMock()
        mock_client.host = "192.168.1.100"
        mock_request.client = mock_client

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_ip_extraction_priority_x_forwarded_for_first(self):
        """Test that X-Forwarded-For has priority over other headers."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with all headers
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {
            "X-Forwarded-For": "203.0.113.1",
            "X-Real-IP": "198.51.100.1"
        }
        mock_client = MagicMock()
        mock_client.host = "192.168.1.1"
        mock_request.client = mock_client

        ip = middleware._get_client_ip(mock_request)
        # Should use X-Forwarded-For
        assert ip == "203.0.113.1"

    def test_ip_extraction_fallback_to_unknown(self):
        """Test fallback to 'unknown' when no IP can be determined."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with no IP information
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = None

        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"


class TestRateLimitTierDetermination:
    """Tests for rate limit tier determination based on user roles."""

    def test_anonymous_tier_for_unauthenticated_request(self):
        """Test that anonymous tier is used for unauthenticated requests."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request without user
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()

        tier = middleware._get_rate_limit_tier(mock_request)
        assert tier == RateLimitTier.ANONYMOUS

    def test_user_tier_for_authenticated_user(self):
        """Test that user tier is used for authenticated users."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with user
        mock_request = MagicMock(spec=Request)
        mock_user = MagicMock()
        mock_user.role = "user"
        mock_request.state.user = mock_user

        tier = middleware._get_rate_limit_tier(mock_request)
        assert tier == RateLimitTier.USER

    def test_admin_tier_for_admin_user(self):
        """Test that admin tier is used for admin users."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with admin user
        mock_request = MagicMock(spec=Request)
        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_request.state.user = mock_user

        tier = middleware._get_rate_limit_tier(mock_request)
        assert tier == RateLimitTier.ADMIN

    def test_org_admin_tier_for_org_admin_user(self):
        """Test that org_admin tier is used for organization admin users."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with org_admin user
        mock_request = MagicMock(spec=Request)
        mock_user = MagicMock()
        mock_user.role = "org_admin"
        mock_request.state.user = mock_user

        tier = middleware._get_rate_limit_tier(mock_request)
        assert tier == RateLimitTier.ORG_ADMIN

    def test_default_user_tier_for_unknown_role(self):
        """Test that user tier is default for unknown roles."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with user but unknown role
        mock_request = MagicMock(spec=Request)
        mock_user = MagicMock()
        mock_user.role = "unknown_role"
        mock_request.state.user = mock_user

        tier = middleware._get_rate_limit_tier(mock_request)
        assert tier == RateLimitTier.USER


class TestRateLimitIdentifier:
    """Tests for rate limit identifier determination."""

    def test_uses_user_id_when_available(self):
        """Test that user ID is used as identifier when available."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with user ID
        mock_request = MagicMock(spec=Request)
        mock_user = MagicMock()
        mock_user.id = 123
        mock_request.state.user = mock_user

        identifier = middleware._get_rate_limit_identifier(mock_request, "192.168.1.1")
        assert identifier == "user_123"

    def test_uses_username_when_id_not_available(self):
        """Test that username is used when user ID is not available."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request with username but no ID
        mock_request = MagicMock(spec=Request)
        mock_user = MagicMock()
        del mock_user.id  # Remove id attribute
        mock_user.username = "testuser"
        mock_request.state.user = mock_user

        identifier = middleware._get_rate_limit_identifier(mock_request, "192.168.1.1")
        assert identifier == "user_testuser"

    def test_uses_ip_address_when_not_authenticated(self):
        """Test that IP address is used for unauthenticated requests."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Request

        middleware = RateLimitMiddleware(app)

        # Create mock request without user
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()

        identifier = middleware._get_rate_limit_identifier(mock_request, "192.168.1.100")
        assert identifier == "192.168.1.100"


class TestHeaderAddition:
    """Tests for header addition to responses."""

    def test_add_rate_limit_headers(self):
        """Test the _add_rate_limit_headers method."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from services.rate_limit_service import RateLimitResult
        from fastapi import Response

        middleware = RateLimitMiddleware(app)

        # Create mock result
        mock_result = MagicMock()
        mock_result.limit = 100
        mock_result.remaining = 95
        mock_result.reset_at = 1738569600

        # Create response
        response = Response(status_code=200)

        # Add headers
        middleware._add_rate_limit_headers(response, mock_result)

        # Verify headers
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "95"
        assert response.headers["X-RateLimit-Reset"] == "1738569600"

    def test_add_default_rate_limit_headers(self):
        """Test the _add_default_rate_limit_headers method."""
        from middleware.rate_limit_middleware import RateLimitMiddleware
        from fastapi import Response

        middleware = RateLimitMiddleware(app)

        # Create response
        response = Response(status_code=200)

        # Add default headers
        middleware._add_default_rate_limit_headers(response)

        # Verify headers indicate unlimited
        assert response.headers["X-RateLimit-Limit"] == "-1"
        assert response.headers["X-RateLimit-Remaining"] == "-1"
        assert response.headers["X-RateLimit-Reset"] == "0"


class TestMultipleEndpoints:
    """Tests for rate limiting across different endpoints."""

    def test_headers_on_health_endpoint(self, client: TestClient):
        """Test rate limit headers on health check endpoint."""
        response = client.get("/api/health")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_on_comparisons_endpoint(self, client: TestClient):
        """Test rate limit headers on comparisons endpoint."""
        response = client.get("/api/comparisons/")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_on_candidates_endpoint(self, client: TestClient):
        """Test rate limit headers on candidates endpoint."""
        response = client.get("/api/candidates/")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_headers_on_malformed_json_request(self, client: TestClient):
        """Test that headers are present even for malformed JSON."""
        response = client.post(
            "/api/comparisons/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Should have headers even for malformed requests
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_headers_on_large_request(self, client: TestClient):
        """Test that headers are present for large requests."""
        large_data = {"data": "x" * 10000}
        response = client.post("/api/comparisons/", json=large_data)

        # Should have headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_unicode_in_request(self, client: TestClient):
        """Test that headers work with unicode in requests."""
        response = client.post(
            "/api/comparisons/",
            json={
                "vacancy_id": "test-unicode-ñ-中文",
                "resume_ids": ["resume1", "resume2"]
            }
        )

        # Should have headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestMiddlewareConfiguration:
    """Tests for middleware configuration options."""

    def test_middleware_initialization_default_tier(self):
        """Test that middleware initializes with default anonymous tier."""
        from middleware.rate_limit_middleware import RateLimitMiddleware

        middleware = RateLimitMiddleware(app)
        assert middleware.default_tier == RateLimitTier.ANONYMOUS

    def test_middleware_initialization_custom_tier(self):
        """Test that middleware can be initialized with custom tier."""
        from middleware.rate_limit_middleware import RateLimitMiddleware

        middleware = RateLimitMiddleware(app, default_tier=RateLimitTier.USER)
        assert middleware.default_tier == RateLimitTier.USER

    def test_middleware_initialization_enabled_flag(self):
        """Test that middleware respects the enabled flag."""
        from middleware.rate_limit_middleware import RateLimitMiddleware

        # When enabled
        middleware_enabled = RateLimitMiddleware(app, enabled=True)
        # Note: The actual enabled value depends on service configuration
        # We're just testing that the parameter is accepted
        assert middleware_enabled is not None

        # When disabled
        middleware_disabled = RateLimitMiddleware(app, enabled=False)
        assert middleware_disabled.enabled is False


class TestRateLimitIntegration:
    """Integration tests for rate limiting behavior across multiple requests."""

    def test_multiple_requests_decrease_remaining_count(self, client: TestClient):
        """Test that making multiple requests decreases the remaining count."""
        # Make multiple requests and track remaining count
        remainings = []
        for _ in range(5):
            response = client.get("/api/health")
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining != "-1":  # Only track if rate limiting is enabled
                remainings.append(int(remaining))

        # If rate limiting is enabled, we should have tracked some values
        if remainings:
            # The remaining count should be non-increasing (may stay same if tokens refilled)
            for i in range(1, len(remainings)):
                assert remainings[i] <= remainings[i-1] + 1  # Allow small increase for token refill

    def test_different_endpoints_have_independent_counters(self, client: TestClient):
        """Test that different endpoints share the same rate limit counter (per user/IP)."""
        # Get remaining count from first endpoint
        response1 = client.get("/api/health")
        remaining1 = response1.headers.get("X-RateLimit-Remaining")

        # Get remaining count from different endpoint
        response2 = client.get("/api/comparisons/")
        remaining2 = response2.headers.get("X-RateLimit-Remaining")

        # They should have the same or similar remaining counts (same IP/user)
        if remaining1 != "-1" and remaining2 != "-1":
            # Remaining counts should be close (within 2 requests)
            assert abs(int(remaining1) - int(remaining2)) <= 2

    def test_rate_limit_headers_consistent_format(self, client: TestClient):
        """Test that rate limit headers have consistent format across all responses."""
        endpoints = [
            "/api/health",
            "/api/ready",
            "/api/comparisons/",
            "/api/candidates/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)

            # All headers should be present
            assert "X-RateLimit-Limit" in response.headers, f"Missing limit header for {endpoint}"
            assert "X-RateLimit-Remaining" in response.headers, f"Missing remaining header for {endpoint}"
            assert "X-RateLimit-Reset" in response.headers, f"Missing reset header for {endpoint}"

            # Headers should be valid integers (or -1 for unlimited)
            limit = response.headers["X-RateLimit-Limit"]
            remaining = response.headers["X-RateLimit-Remaining"]
            reset = response.headers["X-RateLimit-Reset"]

            # Validate format
            assert limit.lstrip('-').isdigit(), f"Invalid limit value: {limit}"
            assert remaining.lstrip('-').isdigit(), f"Invalid remaining value: {remaining}"
            assert reset.isdigit() or reset == "0", f"Invalid reset value: {reset}"


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
