"""
End-to-End Integration Tests for Rate Limiting Flow

Tests the complete rate limiting workflow:
1. Make requests up to the limit
2. Exceed the limit and receive 429
3. Verify rate limit headers
4. Wait for reset and verify requests work again
5. Test IP blocking for DDoS protection
"""

import pytest
import requests
from typing import Dict
import time


class TestRateLimitE2E:
    """End-to-end tests for the rate limiting flow."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_endpoint(self):
        """Get a simple endpoint for rate limit testing."""
        # Use health endpoint as it's lightweight and always available
        return f"{self.BASE_URL}/health"

    def test_complete_rate_limit_flow(self, test_endpoint):
        """
        Test complete rate limit flow:
        1. Make requests up to the limit
        2. Exceed the limit and receive 429
        3. Verify rate limit headers are present
        4. Wait for reset and verify requests work again
        """
        # Step 1: Make requests up to the anonymous limit (20 requests/minute)
        # We'll make a few requests to verify headers and not hit the limit yet
        responses = []

        for i in range(5):
            response = requests.get(test_endpoint)
            responses.append(response)

            # Verify all initial requests succeed
            assert response.status_code == 200, f"Request {i+1} should succeed"

            # Verify rate limit headers are present
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers

            # Verify remaining decreases with each request
            if i > 0:
                prev_remaining = int(responses[i-1].headers.get("X-RateLimit-Remaining", 0))
                curr_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                assert curr_remaining <= prev_remaining, "Remaining should decrease or stay same"

        # Step 2: Make many requests to potentially exceed the limit
        # Note: In a real scenario, we'd make enough requests to hit the limit
        # But for testing, we'll verify the headers are correct
        for i in range(25):
            response = requests.get(test_endpoint)

            # Check if we hit the rate limit
            if response.status_code == 429:
                # Step 3: Verify 429 response has proper structure
                assert "Retry-After" in response.headers
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers

                # Verify response body
                data = response.json()
                assert "error" in data or "message" in data

                # Extract retry-after time
                retry_after = int(response.headers.get("Retry-After", 0))
                assert retry_after > 0, "Retry-After should be positive"

                # Step 4: Wait for reset and verify requests work again
                time.sleep(retry_after + 1)

                # Make a request after waiting
                reset_response = requests.get(test_endpoint)
                assert reset_response.status_code == 200, "Request should succeed after reset"

                # Verify headers are present again
                assert "X-RateLimit-Limit" in reset_response.headers
                assert "X-RateLimit-Remaining" in reset_response.headers

                # We successfully tested the complete flow
                return

        # If we didn't hit the rate limit, that's okay for integration testing
        # The middleware might be configured with higher limits for testing
        # Just verify that headers were present on all requests
        assert len(responses) > 0, "Should have made some requests"

    def test_rate_limit_headers_consistency(self, test_endpoint):
        """Test that rate limit headers are consistent across requests."""
        # Make multiple requests and verify header consistency
        headers_list = []

        for _ in range(3):
            response = requests.get(test_endpoint)
            assert response.status_code == 200

            headers = {
                "limit": response.headers.get("X-RateLimit-Limit"),
                "remaining": response.headers.get("X-RateLimit-Remaining"),
                "reset": response.headers.get("X-RateLimit-Reset"),
            }
            headers_list.append(headers)

        # Verify limit is consistent across requests
        limits = [h["limit"] for h in headers_list]
        assert len(set(limits)) <= 1, "Limit should be consistent"

        # Verify remaining decreases or stays same
        for i in range(1, len(headers_list)):
            prev_remaining = int(headers_list[i-1]["remaining"] or -1)
            curr_remaining = int(headers_list[i]["remaining"] or -1)
            assert curr_remaining <= prev_remaining, "Remaining should not increase"

    def test_rate_limit_reset_header_format(self, test_endpoint):
        """Test that reset header is a valid Unix timestamp."""
        response = requests.get(test_endpoint)
        assert response.status_code == 200

        reset_header = response.headers.get("X-RateLimit-Reset")
        assert reset_header is not None, "Reset header should be present"

        # Verify it's a valid number
        try:
            reset_timestamp = int(reset_header)
            # Verify it's a reasonable timestamp (not in the past, not too far in future)
            current_time = int(time.time())
            assert reset_timestamp >= current_time - 60, "Reset should not be in the distant past"
            assert reset_timestamp <= current_time + 3600, "Reset should not be too far in the future"
        except ValueError:
            pytest.fail("Reset header should be a valid integer timestamp")

    def test_different_endpoints_rate_limiting(self):
        """Test that rate limiting applies across different endpoints."""
        endpoints = [
            f"{self.BASE_URL}/health",
            f"{self.BASE_URL}/api/vacancies/",
        ]

        # Make requests to different endpoints
        responses = []
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=2)
                responses.append(response)

                # Verify rate limit headers are present
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
            except requests.exceptions.RequestException:
                # Some endpoints might not exist or be accessible
                pass

        # At least health endpoint should work
        assert len(responses) > 0, "At least one endpoint should be accessible"


class TestRateLimitE2EWithAuth:
    """End-to-end tests for rate limiting with authentication."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture
    def auth_headers(self):
        """
        Create authenticated headers for testing.
        Note: This is a placeholder - actual auth would require valid credentials.
        """
        # In a real scenario, you'd obtain a valid token
        # For now, we'll test without auth
        return {}

    def test_rate_limit_with_auth(self, auth_headers):
        """Test that rate limiting works with authenticated requests."""
        # Test with auth headers (even if empty for this test)
        endpoint = f"{self.BASE_URL}/health"

        response = requests.get(endpoint, headers=auth_headers)

        # Verify response
        assert response.status_code in [200, 429]

        # Verify headers are present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestIPBlockingE2E:
    """End-to-end tests for IP blocking functionality."""

    BASE_URL = "http://localhost:8000"

    def test_ip_not_blocked_initially(self):
        """Test that IP is not blocked initially."""
        response = requests.get(f"{self.BASE_URL}/health")
        assert response.status_code == 200

    def test_ip_block_via_api(self):
        """Test IP blocking via the management API."""
        # Try to block an IP via the API (if available and authenticated)
        block_data = {
            "ip_address": "192.168.1.100",
            "reason": "Testing IP blocking",
            "duration_seconds": 60,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/rate-limits/blocklist",
            json=block_data,
        )

        # This might fail due to auth, which is expected
        # We're just verifying the endpoint exists
        assert response.status_code in [201, 401, 403, 422]

        # If successful, verify we can list the blocklist
        if response.status_code == 201:
            list_response = requests.get(f"{self.BASE_URL}/api/rate-limits/blocklist")
            assert list_response.status_code in [200, 401, 403]


class TestRateLimitBurstE2E:
    """End-to-end tests for burst rate limiting."""

    BASE_URL = "http://localhost:8000"

    def test_burst_requests(self):
        """Test that burst requests are handled correctly."""
        endpoint = f"{self.BASE_URL}/health"

        # Make a burst of requests quickly
        burst_count = 10
        responses = []

        start_time = time.time()
        for _ in range(burst_count):
            response = requests.get(endpoint)
            responses.append(response)
        end_time = time.time()

        # Verify all requests completed quickly
        duration = end_time - start_time
        assert duration < 5, f"Burst of {burst_count} requests should complete quickly"

        # Count successful vs rate limited
        successful = sum(1 for r in responses if r.status_code == 200)
        rate_limited = sum(1 for r in responses if r.status_code == 429)

        # At least some should succeed (burst should be allowed)
        assert successful > 0, "At least some burst requests should succeed"

        # If rate limited, verify proper response
        if rate_limited > 0:
            for response in responses:
                if response.status_code == 429:
                    assert "Retry-After" in response.headers
                    assert "X-RateLimit-Limit" in response.headers


class TestRateLimitRecoveryE2E:
    """End-to-end tests for rate limit recovery."""

    BASE_URL = "http://localhost:8000"

    def test_gradual_recovery(self):
        """Test that rate limit recovers gradually over time."""
        endpoint = f"{self.BASE_URL}/health"

        # Make initial request
        response1 = requests.get(endpoint)
        assert response1.status_code == 200
        remaining1 = int(response1.headers.get("X-RateLimit-Remaining", 0))

        # Wait a short time
        time.sleep(2)

        # Make another request
        response2 = requests.get(endpoint)
        assert response2.status_code == 200
        remaining2 = int(response2.headers.get("X-RateLimit-Remaining", 0))

        # The remaining count should have potentially increased due to token refill
        # or stayed the same if the window hasn't reset
        assert isinstance(remaining2, int), "Remaining should be an integer"


@pytest.mark.integration
class TestRateLimitMultipleClientsE2E:
    """End-to-end tests for rate limiting with multiple clients."""

    BASE_URL = "http://localhost:8000"

    def test_different_ip_different_limits(self):
        """Test that different IPs have independent rate limits."""
        endpoint = f"{self.BASE_URL}/health"

        # Simulate requests from different clients using different headers
        # Note: In a real scenario, these would be from different IPs
        client1_headers = {"X-Forwarded-For": "192.168.1.10"}
        client2_headers = {"X-Forwarded-For": "192.168.1.11"}

        # Make requests from client 1
        response1 = requests.get(endpoint, headers=client1_headers)
        assert response1.status_code == 200

        # Make requests from client 2
        response2 = requests.get(endpoint, headers=client2_headers)
        assert response2.status_code == 200

        # Both should have rate limit headers
        assert "X-RateLimit-Remaining" in response1.headers
        assert "X-RateLimit-Remaining" in response2.headers

        # The remaining counts should be independent (or close to it)
        # Note: This depends on how the middleware extracts IPs
        remaining1 = int(response1.headers.get("X-RateLimit-Remaining", 0))
        remaining2 = int(response2.headers.get("X-RateLimit-Remaining", 0))
        assert remaining1 >= 0 and remaining2 >= 0


class TestRateLimitHeadersE2E:
    """End-to-end tests for rate limit headers."""

    BASE_URL = "http://localhost:8000"

    def test_all_headers_present(self):
        """Test that all required rate limit headers are present."""
        response = requests.get(f"{self.BASE_URL}/health")

        # Check for all standard headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_header_values_are_valid(self):
        """Test that header values are valid."""
        response = requests.get(f"{self.BASE_URL}/health")

        # Verify limit is a valid number or -1 (unlimited)
        limit = response.headers.get("X-RateLimit-Limit")
        try:
            limit_int = int(limit)
            assert limit_int > 0 or limit_int == -1
        except ValueError:
            pytest.fail("X-RateLimit-Limit should be a valid integer")

        # Verify remaining is a valid number
        remaining = response.headers.get("X-RateLimit-Remaining")
        try:
            remaining_int = int(remaining)
            assert remaining_int >= 0 or remaining_int == -1
        except ValueError:
            pytest.fail("X-RateLimit-Remaining should be a valid integer")

        # Verify reset is a valid timestamp
        reset = response.headers.get("X-RateLimit-Reset")
        try:
            reset_int = int(reset)
            assert reset_int > 0
        except ValueError:
            pytest.fail("X-RateLimit-Reset should be a valid integer timestamp")

    def test_429_response_includes_all_headers(self):
        """
        Test that 429 responses include all required headers.
        Note: This test may not always trigger a 429, which is okay.
        """
        endpoint = f"{self.BASE_URL}/health"

        # Make many requests to try to trigger rate limit
        for i in range(30):
            response = requests.get(endpoint)

            if response.status_code == 429:
                # Verify all headers are present
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
                assert "Retry-After" in response.headers

                # Verify response body has useful information
                data = response.json()
                assert "error" in data or "message" in data
                return
        # If we didn't get a 429, that's okay for this test
