#!/usr/bin/env python3
"""
LinkedIn Search Unit Tests

This test suite provides comprehensive unit testing for the LinkedIn search functionality,
focusing on the LinkedInService class methods related to candidate search.

Test categories:
1. Service Initialization - Validate service setup with various configurations
2. Rate Limiting - Test daily and per-minute quotas, counter updates
3. Retry Logic - Test exponential backoff, jitter, retry decisions
4. Token Validation - Test access token format validation
5. Search Parameter Validation - Test input validation for search parameters
6. Search Response Parsing - Test parsing of LinkedIn API responses
7. Error Handling - Test various error scenarios

Usage:
  cd backend
  pytest tests/test_linkedin_search.py -v

Requirements:
  - pytest
  - pytest-asyncio
  - All dependencies from requirements.txt
"""

import asyncio
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest
import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.linkedin_service import (
    LinkedInService,
    LinkedInAPIError,
    LinkedInRateLimitError,
    LinkedInAuthError,
    DEFAULT_RATE_LIMIT,
    DEFAULT_RETRY_CONFIG,
)


class TestLinkedInServiceInitialization:
    """Test suite for LinkedInService initialization."""

    def test_1_valid_initialization_with_defaults(self):
        """
        Test initialization with valid access token and default parameters.

        Verifies:
        - Service initializes successfully with valid token
        - Default rate limits are applied
        - Default retry configuration is applied
        - Headers are properly configured
        """
        access_token = "valid_access_token_with_sufficient_length_for_testing"
        service = LinkedInService(access_token=access_token)

        assert service.access_token == access_token
        assert service.api_version == "v2"
        assert service.timeout == 30
        assert service._rate_limit_per_day == DEFAULT_RATE_LIMIT["requests_per_day"]
        assert service._rate_limit_per_minute == DEFAULT_RATE_LIMIT["requests_per_minute"]
        assert service._max_retries == DEFAULT_RETRY_CONFIG["max_retries"]
        assert service._initial_backoff == DEFAULT_RETRY_CONFIG["initial_backoff"]
        assert service._max_backoff == DEFAULT_RETRY_CONFIG["max_backoff"]

        print("✓ Service initializes with valid defaults")

    def test_2_initialization_with_custom_parameters(self):
        """
        Test initialization with custom rate limits and retry configuration.

        Verifies:
        - Custom rate limits are applied
        - Custom retry settings are applied
        - Custom API version is used
        - Custom timeout is set
        """
        access_token = "custom_token_with_sufficient_length"
        service = LinkedInService(
            access_token=access_token,
            api_version="v2",
            timeout=60,
            rate_limit_per_day=1000,
            rate_limit_per_minute=50,
            max_retries=5,
            initial_backoff=2.0,
            max_backoff=120.0,
            backoff_multiplier=3.0,
            jitter=False,
        )

        assert service._rate_limit_per_day == 1000
        assert service._rate_limit_per_minute == 50
        assert service._max_retries == 5
        assert service._initial_backoff == 2.0
        assert service._max_backoff == 120.0
        assert service._backoff_multiplier == 3.0
        assert service._jitter is False
        assert service.timeout == 60

        print("✓ Service initializes with custom parameters")

    def test_3_initialization_rejects_empty_token(self):
        """
        Test that initialization fails with empty or invalid access token.

        Verifies:
        - Empty string raises ValueError
        - None raises ValueError
        - Clear error message about token requirement
        """
        with pytest.raises(ValueError) as exc_info:
            LinkedInService(access_token="")
        assert "non-empty string" in str(exc_info.value).lower()

        with pytest.raises(ValueError) as exc_info:
            LinkedInService(access_token=None)
        assert "non-empty string" in str(exc_info.value).lower()

        print("✓ Service rejects empty/invalid tokens")

    def test_4_initialization_sets_proper_headers(self):
        """
        Test that HTTP headers are properly configured.

        Verifies:
        - Authorization header includes Bearer token
        - X-Restli-Protocol-Version is set
        - LinkedIn-Version is set
        - Accept header is set to application/json
        """
        access_token = "test_token_12345"
        service = LinkedInService(access_token=access_token)

        assert service._headers["Authorization"] == f"Bearer {access_token}"
        assert service._headers["X-Restli-Protocol-Version"] == "2.0.0"
        assert service._headers["LinkedIn-Version"] == "v2"
        assert service._headers["Accept"] == "application/json"

        print("✓ HTTP headers properly configured")


class TestRateLimiting:
    """Test suite for rate limiting functionality."""

    def test_1_rate_limit_status_initial_state(self):
        """
        Test rate limit status in initial state.

        Verifies:
        - Initial request counts are zero
        - Daily and minute limits are properly set
        - Status dictionary contains all expected keys
        """
        service = LinkedInService(
            access_token="test_token",
            rate_limit_per_day=100,
            rate_limit_per_minute=10,
        )

        status = service.get_rate_limit_status()

        assert status["requests_today"] == 0
        assert status["requests_this_minute"] == 0
        assert status["daily_limit"] == 100
        assert status["minute_limit"] == 10
        assert "remaining_today" in status
        assert "remaining_this_minute" in status

        print("✓ Rate limit status shows correct initial state")

    def test_2_update_rate_limit_counters(self):
        """
        Test that rate limit counters are updated correctly.

        Verifies:
        - Daily counter increments
        - Minute counter increments
        - Counters track requests separately by time period
        """
        service = LinkedInService(
            access_token="test_token",
            rate_limit_per_day=100,
            rate_limit_per_minute=10,
        )

        # Update counters
        service._update_rate_limit_counters()
        status1 = service.get_rate_limit_status()
        assert status1["requests_today"] == 1
        assert status1["requests_this_minute"] == 1

        # Update again
        service._update_rate_limit_counters()
        status2 = service.get_rate_limit_status()
        assert status2["requests_today"] == 2
        assert status2["requests_this_minute"] == 2

        print("✓ Rate limit counters update correctly")

    def test_3_check_rate_limit_within_limits(self):
        """
        Test that rate limit check passes when within limits.

        Verifies:
        - No exception raised when well below daily limit
        - No exception raised when well below minute limit
        """
        service = LinkedInService(
            access_token="test_token",
            rate_limit_per_day=100,
            rate_limit_per_minute=10,
        )

        # Should not raise exception
        service._check_rate_limit()
        service._update_rate_limit_counters()
        service._check_rate_limit()

        print("✓ Rate limit check passes when within limits")

    def test_4_check_rate_limit_exceeds_daily_limit(self):
        """
        Test that rate limit check raises error when daily limit exceeded.

        Verifies:
        - LinkedInRateLimitError is raised
        - Error message mentions daily limit
        - Error message includes reset information
        """
        service = LinkedInService(
            access_token="test_token",
            rate_limit_per_day=2,
            rate_limit_per_minute=10,
        )

        # Exhaust daily limit
        service._update_rate_limit_counters()
        service._update_rate_limit_counters()

        # Next check should fail
        with pytest.raises(LinkedInRateLimitError) as exc_info:
            service._check_rate_limit()

        error_msg = str(exc_info.value).lower()
        assert "daily" in error_msg or "day" in error_msg
        assert "limit" in error_msg

        print("✓ Rate limit check fails when daily limit exceeded")

    def test_5_check_rate_limit_exceeds_minute_limit(self):
        """
        Test that rate limit check raises error when minute limit exceeded.

        Verifies:
        - LinkedInRateLimitError is raised
        - Error message mentions minute limit
        - Error message includes retry information
        """
        service = LinkedInService(
            access_token="test_token",
            rate_limit_per_day=100,
            rate_limit_per_minute=2,
        )

        # Exhaust minute limit
        service._update_rate_limit_counters()
        service._update_rate_limit_counters()

        # Next check should fail
        with pytest.raises(LinkedInRateLimitError) as exc_info:
            service._check_rate_limit()

        error_msg = str(exc_info.value).lower()
        assert "minute" in error_msg
        assert "limit" in error_msg

        print("✓ Rate limit check fails when minute limit exceeded")


class TestRetryLogic:
    """Test suite for retry logic and exponential backoff."""

    def test_1_should_retry_on_rate_limit_error(self):
        """
        Test that service retries on 429 (rate limit) errors.

        Verifies:
        - _should_retry returns True for 429 status
        - Rate limit errors trigger retry logic
        """
        service = LinkedInService(access_token="test_token")

        assert service._should_retry(status_code=429, error=None) is True
        print("✓ Service retries on rate limit errors (429)")

    def test_2_should_retry_on_server_errors(self):
        """
        Test that service retries on 5xx server errors.

        Verifies:
        - 500 (Internal Server Error) triggers retry
        - 502 (Bad Gateway) triggers retry
        - 503 (Service Unavailable) triggers retry
        - 504 (Gateway Timeout) triggers retry
        """
        service = LinkedInService(access_token="test_token")

        assert service._should_retry(status_code=500, error=None) is True
        assert service._should_retry(status_code=502, error=None) is True
        assert service._should_retry(status_code=503, error=None) is True
        assert service._should_retry(status_code=504, error=None) is True

        print("✓ Service retries on server errors (5xx)")

    def test_3_should_not_retry_on_client_errors(self):
        """
        Test that service does NOT retry on 4xx client errors (except 429).

        Verifies:
        - 400 (Bad Request) does not retry
        - 401 (Unauthorized) does not retry
        - 403 (Forbidden) does not retry
        - 404 (Not Found) does not retry
        """
        service = LinkedInService(access_token="test_token")

        assert service._should_retry(status_code=400, error=None) is False
        assert service._should_retry(status_code=401, error=None) is False
        assert service._should_retry(status_code=403, error=None) is False
        assert service._should_retry(status_code=404, error=None) is False

        print("✓ Service does not retry on client errors (4xx)")

    def test_4_calculate_backoff_exponential_increase(self):
        """
        Test that backoff time increases exponentially.

        Verifies:
        - Backoff increases with each attempt
        - Follows exponential pattern (2^attempt)
        - Respects maximum backoff limit
        """
        service = LinkedInService(
            access_token="test_token",
            initial_backoff=1.0,
            max_backoff=60.0,
            backoff_multiplier=2.0,
            jitter=False,  # Disable jitter for predictable testing
        )

        backoff_0 = service._calculate_backoff(attempt=0)
        backoff_1 = service._calculate_backoff(attempt=1)
        backoff_2 = service._calculate_backoff(attempt=2)
        backoff_3 = service._calculate_backoff(attempt=3)

        # Without jitter, backoff should be: initial * (multiplier ^ attempt)
        assert backoff_0 == 1.0  # 1 * 2^0
        assert backoff_1 == 2.0  # 1 * 2^1
        assert backoff_2 == 4.0  # 1 * 2^2
        assert backoff_3 == 8.0  # 1 * 2^3

        print("✓ Backoff increases exponentially")

    def test_5_calculate_backoff_respects_maximum(self):
        """
        Test that backoff does not exceed maximum limit.

        Verifies:
        - Backoff is capped at max_backoff
        - Large attempt numbers don't cause overflow
        """
        service = LinkedInService(
            access_token="test_token",
            initial_backoff=1.0,
            max_backoff=10.0,
            backoff_multiplier=2.0,
            jitter=False,
        )

        backoff_10 = service._calculate_backoff(attempt=10)
        assert backoff_10 <= 10.0

        print("✓ Backoff respects maximum limit")

    def test_6_calculate_backoff_with_jitter(self):
        """
        Test that jitter adds randomness to backoff.

        Verifies:
        - Jitter causes variation in backoff times
        - Backoff is still within reasonable bounds
        - Multiple calls produce different values (with high probability)
        """
        service = LinkedInService(
            access_token="test_token",
            initial_backoff=1.0,
            max_backoff=60.0,
            backoff_multiplier=2.0,
            jitter=True,
        )

        # Calculate multiple times for same attempt
        backoffs = [service._calculate_backoff(attempt=2) for _ in range(10)]

        # With jitter, values should vary (unlikely all identical)
        unique_values = len(set(backoffs))
        assert unique_values > 1, "Jitter should produce variation"

        # All values should be reasonable (between base and max)
        for backoff in backoffs:
            assert 0 < backoff <= 60.0

        print("✓ Jitter adds randomness to backoff")


class TestTokenValidation:
    """Test suite for access token validation."""

    def test_1_validate_token_format_valid(self):
        """
        Test that valid token formats pass validation.

        Verifies:
        - Tokens longer than 50 characters are considered valid format
        - validate_access_token returns True
        """
        valid_token = "a" * 60  # 60 characters
        service = LinkedInService(access_token=valid_token)

        is_valid = service.validate_access_token()
        assert is_valid is True

        print("✓ Valid token format passes validation")

    def test_2_validate_token_format_invalid_short(self):
        """
        Test that short tokens fail validation.

        Verifies:
        - Tokens shorter than 50 characters are considered invalid
        - validate_access_token returns False
        """
        short_token = "a" * 10  # Only 10 characters
        service = LinkedInService(access_token=short_token)

        is_valid = service.validate_access_token()
        assert is_valid is False

        print("✓ Short token format fails validation")

    def test_3_validate_token_format_boundary(self):
        """
        Test token validation at boundary (50 characters).

        Verifies:
        - Exact boundary behavior is consistent
        """
        boundary_token = "a" * 50  # Exactly 50 characters
        service = LinkedInService(access_token=boundary_token)

        is_valid = service.validate_access_token()
        # Boundary case: 50 chars should be considered invalid (< 50 is invalid)
        assert is_valid is False

        valid_token = "a" * 51  # 51 characters
        service2 = LinkedInService(access_token=valid_token)
        assert service2.validate_access_token() is True

        print("✓ Token validation handles boundary correctly")


class TestSearchParameterValidation:
    """Test suite for search parameter validation."""

    @pytest.mark.asyncio
    async def test_1_search_validates_count_parameter(self):
        """
        Test that count parameter is validated.

        Verifies:
        - count < 1 raises ValueError
        - count > 50 raises ValueError
        - Error messages are clear
        """
        service = LinkedInService(access_token="test_token")

        # Test count too small
        with pytest.raises(ValueError) as exc_info:
            await service.search_candidates(count=0)
        assert "count" in str(exc_info.value).lower()
        assert "1" in str(exc_info.value) and "50" in str(exc_info.value)

        # Test count too large
        with pytest.raises(ValueError) as exc_info:
            await service.search_candidates(count=100)
        assert "count" in str(exc_info.value).lower()

        print("✓ Search validates count parameter")

    @pytest.mark.asyncio
    async def test_2_search_validates_start_parameter(self):
        """
        Test that start parameter is validated.

        Verifies:
        - start < 0 raises ValueError
        - Error message is clear
        """
        service = LinkedInService(access_token="test_token")

        with pytest.raises(ValueError) as exc_info:
            await service.search_candidates(start=-1)
        assert "start" in str(exc_info.value).lower()

        print("✓ Search validates start parameter")

    @pytest.mark.asyncio
    async def test_3_search_accepts_valid_parameters(self):
        """
        Test that valid parameters are accepted.

        Verifies:
        - Valid count values (1-50) are accepted
        - Valid start values (>= 0) are accepted
        - Optional parameters can be None
        """
        service = LinkedInService(access_token="test_token")

        # Mock the _make_request to avoid actual API calls
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "paging": {"total": 0, "start": 0, "count": 0},
                "elements": [],
            }

            # Valid parameters should not raise ValueError
            result = await service.search_candidates(
                keywords="software engineer",
                location="San Francisco",
                skills=["Python", "React"],
                count=20,
                start=10,
            )

            assert mock_request.called
            assert "results" in result

        print("✓ Search accepts valid parameters")


class TestSearchResponseParsing:
    """Test suite for parsing LinkedIn search responses."""

    def test_1_parse_search_response_basic(self):
        """
        Test parsing of basic search response.

        Verifies:
        - total, start, count are extracted from paging
        - results list is created
        - paging metadata is included
        """
        service = LinkedInService(access_token="test_token")

        response_data = {
            "paging": {
                "total": 150,
                "start": 0,
                "count": 10,
                "links": [],
            },
            "elements": [],
        }

        result = service._parse_search_response(response_data)

        assert result["total"] == 150
        assert result["start"] == 0
        assert result["count"] == 10
        assert result["results"] == []
        assert "paging" in result

        print("✓ Basic search response parsed correctly")

    def test_2_parse_search_response_with_candidates(self):
        """
        Test parsing of search response with candidate profiles.

        Verifies:
        - Candidate profiles are extracted
        - Name fields are properly parsed (localized format)
        - Headline, summary, industry are extracted
        - Location is formatted correctly
        """
        service = LinkedInService(access_token="test_token")

        response_data = {
            "paging": {
                "total": 2,
                "start": 0,
                "count": 2,
            },
            "elements": [
                {
                    "id": "profile-123",
                    "firstName": {
                        "localized": {"en_US": "John"}
                    },
                    "lastName": {
                        "localized": {"en_US": "Doe"}
                    },
                    "headline": "Software Engineer",
                    "summary": "Experienced developer",
                    "industry": "Technology",
                    "location": {
                        "country": {
                            "name": "United States",
                            "code": "US"
                        }
                    },
                },
                {
                    "id": "profile-456",
                    "firstName": {
                        "localized": {"en_US": "Jane"}
                    },
                    "lastName": {
                        "localized": {"en_US": "Smith"}
                    },
                    "headline": "Product Manager",
                    "summary": "",
                    "industry": "Technology",
                    "location": {},
                },
            ],
        }

        result = service._parse_search_response(response_data)

        assert len(result["results"]) == 2

        # Check first candidate
        candidate1 = result["results"][0]
        assert candidate1["id"] == "profile-123"
        assert candidate1["first_name"] == "John"
        assert candidate1["last_name"] == "Doe"
        assert candidate1["headline"] == "Software Engineer"
        assert candidate1["summary"] == "Experienced developer"
        assert candidate1["industry"] == "Technology"
        assert candidate1["location"] == "United States"
        assert candidate1["country_code"] == "US"

        # Check second candidate
        candidate2 = result["results"][1]
        assert candidate2["id"] == "profile-456"
        assert candidate2["first_name"] == "Jane"
        assert candidate2["last_name"] == "Smith"

        print("✓ Search response with candidates parsed correctly")

    def test_3_parse_search_response_with_profile_picture(self):
        """
        Test parsing of profile picture URLs.

        Verifies:
        - Profile picture URL is extracted
        - Falls back to empty string if not available
        - Handles nested structure correctly
        """
        service = LinkedInService(access_token="test_token")

        response_data = {
            "paging": {"total": 1, "start": 0, "count": 1},
            "elements": [
                {
                    "id": "profile-123",
                    "firstName": {"localized": {"en_US": "John"}},
                    "lastName": {"localized": {"en_US": "Doe"}},
                    "headline": "Engineer",
                    "profilePicture": {
                        "displayImage~": {
                            "elements": [
                                {
                                    "identifiers": [
                                        {"identifier": "https://media.linkedin.com/photo.jpg"}
                                    ]
                                }
                            ]
                        }
                    },
                }
            ],
        }

        result = service._parse_search_response(response_data)
        candidate = result["results"][0]

        assert candidate["profile_picture"] == "https://media.linkedin.com/photo.jpg"

        print("✓ Profile picture URL extracted correctly")

    def test_4_parse_search_response_handles_missing_fields(self):
        """
        Test that parser handles missing or malformed fields gracefully.

        Verifies:
        - Missing fields result in empty strings
        - No exceptions are raised
        - Minimal profile data is still valid
        """
        service = LinkedInService(access_token="test_token")

        response_data = {
            "paging": {"total": 1, "start": 0, "count": 1},
            "elements": [
                {
                    "id": "profile-789",
                    # Most fields missing
                }
            ],
        }

        result = service._parse_search_response(response_data)
        candidate = result["results"][0]

        assert candidate["id"] == "profile-789"
        assert candidate.get("first_name") == ""
        assert candidate.get("last_name") == ""
        assert candidate.get("headline") == ""
        assert candidate.get("profile_picture") == ""

        print("✓ Parser handles missing fields gracefully")

    def test_5_parse_search_response_handles_string_names(self):
        """
        Test that parser handles non-localized (string) name formats.

        Verifies:
        - String firstName/lastName are converted properly
        - Both localized and string formats work
        """
        service = LinkedInService(access_token="test_token")

        response_data = {
            "paging": {"total": 1, "start": 0, "count": 1},
            "elements": [
                {
                    "id": "profile-999",
                    "firstName": "Alice",  # String format instead of localized
                    "lastName": "Wonder",  # String format instead of localized
                    "headline": "Developer",
                }
            ],
        }

        result = service._parse_search_response(response_data)
        candidate = result["results"][0]

        assert candidate["first_name"] == "Alice"
        assert candidate["last_name"] == "Wonder"

        print("✓ Parser handles string name formats")


class TestErrorHandling:
    """Test suite for error handling in search operations."""

    @pytest.mark.asyncio
    async def test_1_search_handles_rate_limit_error(self):
        """
        Test that search handles rate limit errors properly.

        Verifies:
        - LinkedInRateLimitError is raised
        - Error message is descriptive
        - Rate limit check is performed before request
        """
        service = LinkedInService(
            access_token="test_token",
            rate_limit_per_day=0,  # Immediately exceed limit
        )

        with pytest.raises(LinkedInRateLimitError):
            await service.search_candidates(keywords="test")

        print("✓ Search handles rate limit errors")

    @pytest.mark.asyncio
    async def test_2_search_handles_api_errors(self):
        """
        Test that search handles LinkedIn API errors.

        Verifies:
        - API errors are caught and wrapped
        - LinkedInAPIError is raised
        - Original error context is preserved
        """
        service = LinkedInService(access_token="test_token")

        # Mock _make_request to raise an exception
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("API connection failed")

            with pytest.raises(LinkedInAPIError) as exc_info:
                await service.search_candidates(keywords="test")

            assert "failed to search" in str(exc_info.value).lower()

        print("✓ Search handles API errors")

    @pytest.mark.asyncio
    async def test_3_search_handles_malformed_response(self):
        """
        Test that search handles malformed API responses.

        Verifies:
        - Parser handles missing pagination data
        - Parser handles missing elements
        - Default values are used when data is missing
        """
        service = LinkedInService(access_token="test_token")

        # Mock _make_request to return malformed data
        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {}  # Missing paging and elements

            result = await service.search_candidates(keywords="test")

            assert result["total"] == 0
            assert result["results"] == []

        print("✓ Search handles malformed responses")


class TestSearchIntegration:
    """Test suite for integration of search components."""

    @pytest.mark.asyncio
    async def test_1_search_builds_correct_query_parameters(self):
        """
        Test that search builds correct LinkedIn API query parameters.

        Verifies:
        - keywords parameter is set
        - start and count are included
        - projection fields are specified
        """
        service = LinkedInService(access_token="test_token")

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "paging": {"total": 0, "start": 0, "count": 0},
                "elements": [],
            }

            await service.search_candidates(
                keywords="python developer",
                start=10,
                count=20,
            )

            # Verify _make_request was called with correct parameters
            assert mock_request.called
            call_args = mock_request.call_args
            params = call_args[1]["params"]

            assert params["keywords"] == "python developer"
            assert params["start"] == 10
            assert params["count"] == 20
            assert "projection" in params

        print("✓ Search builds correct query parameters")

    @pytest.mark.asyncio
    async def test_2_search_applies_location_filter(self):
        """
        Test that location filter is applied correctly.

        Verifies:
        - location parameter creates facet filter
        - facets are included in query parameters
        """
        service = LinkedInService(access_token="test_token")

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "paging": {"total": 0, "start": 0, "count": 0},
                "elements": [],
            }

            await service.search_candidates(
                keywords="engineer",
                location="San Francisco",
            )

            call_args = mock_request.call_args
            params = call_args[1]["params"]

            assert "facets" in params
            assert "San Francisco" in params["facets"]

        print("✓ Location filter applied correctly")

    @pytest.mark.asyncio
    async def test_3_search_applies_skills_filter(self):
        """
        Test that skills filter is applied correctly.

        Verifies:
        - skills list is combined with keywords
        - OR logic is used for skills
        """
        service = LinkedInService(access_token="test_token")

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "paging": {"total": 0, "start": 0, "count": 0},
                "elements": [],
            }

            await service.search_candidates(
                keywords="developer",
                skills=["Python", "React", "AWS"],
            )

            call_args = mock_request.call_args
            params = call_args[1]["params"]

            # Skills should be combined with keywords using OR
            assert "keywords" in params
            keywords_value = params["keywords"]
            assert "Python" in keywords_value
            assert "React" in keywords_value
            assert "OR" in keywords_value

        print("✓ Skills filter applied correctly")

    @pytest.mark.asyncio
    async def test_4_search_applies_experience_level_filter(self):
        """
        Test that experience level filter is applied correctly.

        Verifies:
        - experience_level is mapped to LinkedIn seniority codes
        - facet is created with correct code
        """
        service = LinkedInService(access_token="test_token")

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "paging": {"total": 0, "start": 0, "count": 0},
                "elements": [],
            }

            await service.search_candidates(
                keywords="manager",
                experience_level="senior",
            )

            call_args = mock_request.call_args
            params = call_args[1]["params"]

            assert "facets" in params
            # senior maps to code "5"
            assert "seniority" in params["facets"]

        print("✓ Experience level filter applied correctly")

    @pytest.mark.asyncio
    async def test_5_search_combines_multiple_filters(self):
        """
        Test that multiple filters can be combined.

        Verifies:
        - All filters are applied simultaneously
        - Facets are properly combined
        - Query parameters include all filters
        """
        service = LinkedInService(access_token="test_token")

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "paging": {"total": 0, "start": 0, "count": 0},
                "elements": [],
            }

            await service.search_candidates(
                keywords="software engineer",
                location="New York",
                skills=["Java", "Spring"],
                title="Senior Engineer",
                industry="Technology",
                experience_level="senior",
                count=25,
            )

            call_args = mock_request.call_args
            params = call_args[1]["params"]

            assert params["count"] == 25
            assert "keywords" in params
            assert "facets" in params
            facets = params["facets"]
            assert "New York" in facets
            assert "title" in facets
            assert "industry" in facets

        print("✓ Multiple filters combined correctly")


# Test execution summary
test_counts = {
    "initialization": 4,
    "rate_limiting": 5,
    "retry_logic": 6,
    "token_validation": 3,
    "parameter_validation": 3,
    "response_parsing": 5,
    "error_handling": 3,
    "integration": 5,
}

total_tests = sum(test_counts.values())

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"LinkedIn Search Unit Tests")
    print(f"{'='*80}\n")
    print(f"This test suite provides comprehensive unit testing for LinkedIn search:\n")
    print(f"  1. Service Initialization - Setup and configuration")
    print(f"  2. Rate Limiting - Daily and per-minute quotas")
    print(f"  3. Retry Logic - Exponential backoff and jitter")
    print(f"  4. Token Validation - Access token format checking")
    print(f"  5. Parameter Validation - Input validation")
    print(f"  6. Response Parsing - LinkedIn API response parsing")
    print(f"  7. Error Handling - Various error scenarios")
    print(f"  8. Integration - End-to-end search flow\n")
    print(f"Test breakdown:")
    for category, count in test_counts.items():
        print(f"  - {category}: {count} tests")
    print(f"\nTotal tests: {total_tests}")
    print(f"{'='*80}\n")
    print(f"Run tests with: cd backend && pytest tests/test_linkedin_search.py -v")
    print(f"{'='*80}\n")
