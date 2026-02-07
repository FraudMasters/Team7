"""
LinkedIn API client service for profile data fetching.

This module provides a client for interacting with the LinkedIn API to fetch
profile data, handle authentication, and respect rate limits.

The service supports:
- OAuth 2.0 authentication with access tokens
- Rate limiting (daily and per-minute quotas)
- Exponential backoff with jitter for retries
- Graceful error handling and recovery
- Profile data fetching and parsing
"""
import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

# LinkedIn API endpoints
LINKEDIN_API_BASE_URL = "https://api.linkedin.com"
LINKEDIN_API_VERSIONS = {
    "v2": "/v2",
    "v1": "/v1",
}

# LinkedIn API rate limits (conservative defaults)
# Actual limits depend on your LinkedIn application tier
DEFAULT_RATE_LIMIT = {
    "requests_per_day": 500,  # Daily quota
    "requests_per_minute": 100,  # Minute-level throttling
}

# Retry configuration with exponential backoff
DEFAULT_RETRY_CONFIG = {
    "max_retries": 3,  # Maximum number of retry attempts
    "initial_backoff": 1.0,  # Initial backoff in seconds
    "max_backoff": 60.0,  # Maximum backoff in seconds
    "backoff_multiplier": 2.0,  # Exponential backoff multiplier
    "jitter": True,  # Add randomness to backoff to prevent thundering herd
}

# Profile fields that can be requested from LinkedIn API
PROFILE_FIELDS = [
    "id",
    "firstName",
    "lastName",
    "profilePicture(displayImage~:playableStreams)",
    "headline",
    "summary",
    "specialties",
    "positions",
    "education",
    "skills",
    "languages",
    "location",
    "industry",
    "emailAddress",
    "phoneNumbers",
    "birthday",
]


class LinkedInAPIError(Exception):
    """Base exception for LinkedIn API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class LinkedInRateLimitError(LinkedInAPIError):
    """Exception raised when rate limit is exceeded."""

    pass


class LinkedInAuthError(LinkedInAPIError):
    """Exception raised for authentication/authorization errors."""

    pass


class LinkedInService:
    """
    Client for interacting with the LinkedIn API.

    This service provides methods to fetch profile data from LinkedIn
    while handling authentication, rate limiting, and error cases.

    Attributes:
        access_token: OAuth 2.0 access token for LinkedIn API
        api_version: LinkedIn API version to use (default: v2)
        timeout: HTTP request timeout in seconds
    """

    def __init__(
        self,
        access_token: str,
        api_version: str = "v2",
        timeout: int = 30,
        rate_limit_per_day: int = DEFAULT_RATE_LIMIT["requests_per_day"],
        rate_limit_per_minute: int = DEFAULT_RATE_LIMIT["requests_per_minute"],
        max_retries: int = DEFAULT_RETRY_CONFIG["max_retries"],
        initial_backoff: float = DEFAULT_RETRY_CONFIG["initial_backoff"],
        max_backoff: float = DEFAULT_RETRY_CONFIG["max_backoff"],
        backoff_multiplier: float = DEFAULT_RETRY_CONFIG["backoff_multiplier"],
        jitter: bool = DEFAULT_RETRY_CONFIG["jitter"],
    ):
        """
        Initialize LinkedIn API client.

        Args:
            access_token: OAuth 2.0 access token for LinkedIn API
            api_version: LinkedIn API version (default: "v2")
            timeout: HTTP request timeout in seconds
            rate_limit_per_day: Maximum API requests per day
            rate_limit_per_minute: Maximum API requests per minute
            max_retries: Maximum number of retry attempts for failed requests
            initial_backoff: Initial backoff delay in seconds
            max_backoff: Maximum backoff delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Whether to add randomness to backoff delays

        Raises:
            ValueError: If access_token is empty
        """
        if not access_token or not isinstance(access_token, str):
            raise ValueError("access_token must be a non-empty string")

        self.access_token = access_token
        self.api_version = api_version
        self.timeout = timeout

        settings = get_settings()

        # Rate limiting state
        self._rate_limit_per_day = rate_limit_per_day
        self._rate_limit_per_minute = rate_limit_per_minute
        self._daily_requests: Dict[str, int] = {}  # date -> count
        self._minute_requests: Dict[str, int] = {}  # minute_key -> count
        self._last_request_time: Optional[float] = None

        # Retry configuration with exponential backoff
        self._max_retries = max_retries
        self._initial_backoff = initial_backoff
        self._max_backoff = max_backoff
        self._backoff_multiplier = backoff_multiplier
        self._jitter = jitter

        # HTTP client configuration
        self._base_url = f"{LINKEDIN_API_BASE_URL}{LINKEDIN_API_VERSIONS.get(api_version, LINKEDIN_API_VERSIONS['v2'])}"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": api_version,
            "Accept": "application/json",
        }

        logger.info(
            f"LinkedInService initialized (api_version={api_version}, "
            f"rate_limit={rate_limit_per_day}/day, {rate_limit_per_minute}/minute, "
            f"max_retries={max_retries})"
        )

    def _check_rate_limit(self) -> None:
        """
        Check if rate limit would be exceeded and raise error if so.

        Raises:
            LinkedInRateLimitError: If rate limit would be exceeded
        """
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        minute_key = now.strftime("%Y-%m-%d_%H:%M")

        # Check daily limit
        daily_count = self._daily_requests.get(date_key, 0)
        if daily_count >= self._rate_limit_per_day:
            logger.warning(
                f"LinkedIn daily rate limit exceeded: {daily_count}/{self._rate_limit_per_day}"
            )
            raise LinkedInRateLimitError(
                f"Daily rate limit exceeded ({self._rate_limit_per_day} requests/day). "
                f"Limit will reset at midnight UTC."
            )

        # Check minute limit
        minute_count = self._minute_requests.get(minute_key, 0)
        if minute_count >= self._rate_limit_per_minute:
            logger.warning(
                f"LinkedIn minute rate limit exceeded: {minute_count}/{self._rate_limit_per_minute}"
            )
            raise LinkedInRateLimitError(
                f"Rate limit exceeded ({self._rate_limit_per_minute} requests/minute). "
                f"Please wait before making more requests."
            )

    def _update_rate_limit_counters(self) -> None:
        """Update rate limit counters after a successful request."""
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        minute_key = now.strftime("%Y-%m-%d_%H:%M")

        # Clean up old entries (older than 2 days for daily, older than 2 minutes for minute)
        cutoff_date = (now - timedelta(days=2)).strftime("%Y-%m-%d")
        cutoff_minute = (now - timedelta(minutes=2)).strftime("%Y-%m-%d_%H:%M")

        self._daily_requests = {
            k: v for k, v in self._daily_requests.items() if k >= cutoff_date
        }
        self._minute_requests = {
            k: v for k, v in self._minute_requests.items() if k >= cutoff_minute
        }

        # Increment counters
        self._daily_requests[date_key] = self._daily_requests.get(date_key, 0) + 1
        self._minute_requests[minute_key] = self._minute_requests.get(minute_key, 0) + 1
        self._last_request_time = time.time()

        logger.debug(
            f"Rate limit counters updated: daily={self._daily_requests[date_key]}/{self._rate_limit_per_day}, "
            f"minute={self._minute_requests[minute_key]}/{self._rate_limit_per_minute}"
        )

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with optional jitter.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Backoff delay in seconds

        Example:
            >>> service = LinkedInService(access_token="token")
            >>> service._calculate_backoff(0)  # First retry
            1.0
            >>> service._calculate_backoff(1)  # Second retry
            2.0
        """
        # Calculate exponential backoff
        backoff = self._initial_backoff * (self._backoff_multiplier ** attempt)

        # Cap at maximum backoff
        backoff = min(backoff, self._max_backoff)

        # Add jitter to prevent thundering herd
        if self._jitter:
            # Add up to 25% randomness
            jitter_range = backoff * 0.25
            backoff += random.uniform(-jitter_range, jitter_range)

        # Ensure non-negative
        backoff = max(0, backoff)

        logger.debug(f"Calculated backoff: {backoff:.2f}s (attempt={attempt})")
        return backoff

    def _should_retry(self, status_code: Optional[int], error: Optional[Exception]) -> bool:
        """
        Determine if a request should be retried based on status code or error.

        Args:
            status_code: HTTP status code from response
            error: Exception that occurred

        Returns:
            True if request should be retried, False otherwise

        Example:
            >>> service = LinkedInService(access_token="token")
            >>> service._should_retry(429, None)  # Rate limit
            True
            >>> service._should_retry(401, None)  # Auth error
            False
            >>> service._should_retry(503, None)  # Server error
            True
        """
        # Retry on rate limit errors (429)
        if status_code == 429:
            return True

        # Retry on server errors (5xx)
        if status_code and 500 <= status_code < 600:
            return True

        # Retry on network errors
        if error and isinstance(error, (httpx.NetworkError, httpx.TimeoutException)):
            return True

        # Don't retry on client errors (4xx except 429)
        if status_code and 400 <= status_code < 500 and status_code != 429:
            return False

        return False

    async def _async_sleep(self, seconds: float) -> None:
        """
        Async sleep wrapper for backoff delays.

        Args:
            seconds: Number of seconds to sleep

        Example:
            >>> await service._async_sleep(1.5)  # Sleep for 1.5 seconds
        """
        try:
            await asyncio.sleep(seconds)
        except Exception as e:
            logger.warning(f"Sleep interrupted: {e}")
            # Continue anyway - sleep interruption is not critical

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the LinkedIn API with retry logic.

        Implements exponential backoff with jitter for retrying failed requests.
        Retries on rate limit errors (429), server errors (5xx), and network errors.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST/PUT requests

        Returns:
            JSON response data as dictionary

        Raises:
            LinkedInAPIError: For API errors after all retries exhausted
            LinkedInRateLimitError: For rate limit errors after all retries exhausted
            LinkedInAuthError: For authentication errors (no retries)
        """
        url = f"{self._base_url}{endpoint}"
        headers = self._headers.copy()

        # Add Content-Type for JSON bodies
        if json_data:
            headers["Content-Type"] = "application/json"

        last_error = None
        last_status_code = None

        # Attempt request with retries
        for attempt in range(self._max_retries + 1):
            try:
                # Check rate limits before making request (except for retries after 429)
                if attempt == 0:
                    self._check_rate_limit()

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(
                        f"Making {method} request to {endpoint} "
                        f"(attempt {attempt + 1}/{self._max_retries + 1})"
                    )

                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                    )

                    # Update rate limit counters on successful response
                    if response.status_code < 500:
                        self._update_rate_limit_counters()

                    # Handle authentication errors (no retries)
                    if response.status_code == 401:
                        error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                        raise LinkedInAuthError(
                            f"Authentication failed: {error_data.get('message', 'Invalid or expired token')}",
                            status_code=401,
                            response_data=error_data,
                        )

                    # Handle rate limit errors (with retry)
                    if response.status_code == 429:
                        retry_after = response.headers.get("X-RateLimit-Reset")
                        if retry_after:
                            try:
                                retry_after_seconds = int(retry_after)
                                logger.warning(
                                    f"Rate limit exceeded. Retry after {retry_after_seconds}s"
                                )
                            except ValueError:
                                retry_after_seconds = None

                        error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                        raise LinkedInRateLimitError(
                            f"Rate limit exceeded. Retry after {retry_after or 'unknown'} seconds.",
                            status_code=429,
                            response_data=error_data,
                        )

                    # Handle other server errors (with retry)
                    if response.status_code >= 500:
                        error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                        error_message = error_data.get("message", f"HTTP {response.status_code}")
                        raise LinkedInAPIError(
                            f"LinkedIn API error: {error_message}",
                            status_code=response.status_code,
                            response_data=error_data,
                        )

                    # Handle client errors (no retries)
                    if response.status_code >= 400:
                        error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                        error_message = error_data.get("message", f"HTTP {response.status_code}")
                        raise LinkedInAPIError(
                            f"LinkedIn API error: {error_message}",
                            status_code=response.status_code,
                            response_data=error_data,
                        )

                    # Successful response
                    if response.status_code == 204:
                        return {}

                    return response.json()

            except (LinkedInRateLimitError, LinkedInAPIError) as e:
                last_error = e
                last_status_code = getattr(e, 'status_code', None)

                # Check if we should retry
                if attempt < self._max_retries and self._should_retry(last_status_code, e):
                    # For rate limit errors, use Retry-After header if available
                    if last_status_code == 429:
                        retry_after = None
                        if isinstance(e, LinkedInRateLimitError) and hasattr(e, 'response_data'):
                            retry_after = e.response_data.get('X-RateLimit-Reset')

                        if retry_after:
                            try:
                                backoff = float(retry_after)
                            except ValueError:
                                backoff = self._calculate_backoff(attempt)
                        else:
                            backoff = self._calculate_backoff(attempt)
                    else:
                        backoff = self._calculate_backoff(attempt)

                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self._max_retries + 1}), "
                        f"retrying in {backoff:.2f}s: {str(e)}"
                    )

                    await self._async_sleep(backoff)
                    continue
                else:
                    # No more retries or shouldn't retry
                    logger.error(
                        f"Request failed after {attempt + 1} attempts: {str(e)}"
                    )
                    raise

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self._max_retries + 1})")

                if attempt < self._max_retries:
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(f"Retrying in {backoff:.2f}s")
                    await self._async_sleep(backoff)
                    continue
                else:
                    logger.error(f"Request timeout after {attempt + 1} attempts")
                    raise LinkedInAPIError(f"Request timeout after {self.timeout} seconds") from e

            except httpx.NetworkError as e:
                last_error = e
                logger.warning(f"Network error (attempt {attempt + 1}/{self._max_retries + 1}): {e}")

                if attempt < self._max_retries:
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(f"Retrying in {backoff:.2f}s")
                    await self._async_sleep(backoff)
                    continue
                else:
                    logger.error(f"Network error after {attempt + 1} attempts")
                    raise LinkedInAPIError(f"Network error: {str(e)}") from e

            except (LinkedInAuthError, LinkedInRateLimitError, LinkedInAPIError):
                # Re-raise LinkedIn-specific exceptions
                raise

            except Exception as e:
                logger.error(f"Unexpected error during LinkedIn API request: {e}")
                raise LinkedInAPIError(f"Unexpected error: {str(e)}") from e

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise LinkedInAPIError("Request failed with unknown error")

    async def get_profile(
        self,
        profile_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Fetch LinkedIn profile data.

        Args:
            profile_id: LinkedIn profile ID (optional, defaults to current user)
            fields: List of profile fields to retrieve
                (defaults to PROFILE_FIELDS)

        Returns:
            Dictionary containing profile data with keys:
                - id: LinkedIn profile ID
                - first_name: Profile first name
                - last_name: Profile last name
                - headline: Profile headline
                - summary: Profile summary/bio
                - positions: List of position objects
                - education: List of education objects
                - skills: List of skill objects
                - email: Email address (if available)
                - phone: Phone number (if available)
                - location: Location information
                - industry: Industry
                - profile_picture: Profile picture URL
                - raw_data: Complete API response

        Raises:
            LinkedInAPIError: For API errors
            LinkedInRateLimitError: For rate limit errors
            LinkedInAuthError: For authentication errors

        Examples:
            >>> service = LinkedInService(access_token="your_token")
            >>> profile = await service.get_profile()
            >>> print(profile["headline"])
        """
        if fields is None:
            fields = PROFILE_FIELDS

        # Use "~" for current user's profile if no profile_id provided
        resource = f"urn:li:person:{profile_id}" if profile_id else "~"

        # Build endpoint with projection for requested fields
        projection = ",".join(fields)
        endpoint = f"/people/{resource}"

        params = {"projection": f"({projection})"}

        try:
            logger.info(f"Fetching LinkedIn profile: {resource}")

            response_data = await self._make_request("GET", endpoint, params=params)

            # Parse and normalize profile data
            profile = self._parse_profile_response(response_data)

            logger.info(
                f"Successfully fetched profile for {profile.get('first_name', '')} {profile.get('last_name', '')}"
            )

            return profile

        except (LinkedInAPIError, LinkedInRateLimitError, LinkedInAuthError):
            raise
        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}")
            raise LinkedInAPIError(f"Failed to fetch profile: {str(e)}") from e

    def _parse_profile_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and normalize LinkedIn profile API response.

        Args:
            response_data: Raw JSON response from LinkedIn API

        Returns:
            Normalized profile dictionary
        """
        profile = {
            "raw_data": response_data,
        }

        # Basic profile info
        profile["id"] = response_data.get("id", "")

        # Name handling (LinkedIn API returns localized names)
        first_name_data = response_data.get("firstName", {})
        last_name_data = response_data.get("lastName", {})

        if isinstance(first_name_data, dict):
            profile["first_name"] = first_name_data.get("localized", {}).get(
                "en_US", first_name_data.get("localized", {})
            )
        else:
            profile["first_name"] = str(first_name_data) if first_name_data else ""

        if isinstance(last_name_data, dict):
            profile["last_name"] = last_name_data.get("localized", {}).get(
                "en_US", last_name_data.get("localized", {})
            )
        else:
            profile["last_name"] = str(last_name_data) if last_name_data else ""

        # Headline and summary
        profile["headline"] = response_data.get("headline", "")
        profile["summary"] = response_data.get("summary", "")

        # Profile picture
        profile_picture = response_data.get("profilePicture", {})
        if profile_picture:
            display_elements = profile_picture.get("displayImage~", {}).get(
                "elements", []
            )
            if display_elements:
                # Get the largest available picture
                picture_url = None
                for element in reversed(display_elements):
                    identifiers = element.get("identifiers", [])
                    if identifiers:
                        picture_url = identifiers[0].get("identifier")
                        break
                profile["profile_picture"] = picture_url or ""
            else:
                profile["profile_picture"] = ""
        else:
            profile["profile_picture"] = ""

        # Location
        location_data = response_data.get("location", {})
        profile["location"] = (
            f"{location_data.get('country', {}).get('name', '')}" if location_data else ""
        )
        profile["country_code"] = location_data.get("country", {}).get("code", "") if location_data else ""

        # Industry
        profile["industry"] = response_data.get("industry", "")

        # Contact information
        profile["email"] = response_data.get("emailAddress", "")

        phone_numbers = response_data.get("phoneNumbers", {}).get("values", [])
        profile["phone"] = phone_numbers[0].get("phoneNumber", "") if phone_numbers else ""

        # Positions (work experience)
        positions_data = response_data.get("positions", {}).get("values", [])
        profile["positions"] = [
            {
                "title": pos.get("title", ""),
                "company": pos.get("companyName", ""),
                "location": pos.get("locationName", ""),
                "start_date": self._parse_date(pos.get("startedAt")),
                "end_date": self._parse_date(pos.get("finishedAt")),
                "current": pos.get("companyName") is not None and pos.get("finishedAt") is None,
                "description": pos.get("description", ""),
            }
            for pos in positions_data
        ]

        # Education
        education_data = response_data.get("education", {}).get("values", [])
        profile["education"] = [
            {
                "school": edu.get("schoolName", ""),
                "degree": edu.get("degreeName", ""),
                "field_of_study": edu.get("fieldOfStudy", ""),
                "start_date": self._parse_date(edu.get("startedAt")),
                "end_date": self._parse_date(edu.get("endedAt")),
                "description": edu.get("notes", ""),
            }
            for edu in education_data
        ]

        # Skills
        skills_data = response_data.get("skills", {}).get("values", [])
        profile["skills"] = [
            skill.get("skill", {}).get("name", "") for skill in skills_data
        ]

        # Languages
        languages_data = response_data.get("languages", {}).get("values", [])
        profile["languages"] = [
            lang.get("name", "") for lang in languages_data
        ]

        return profile

    def _parse_date(self, date_obj: Optional[Dict]) -> Optional[str]:
        """
        Parse LinkedIn date object to ISO format string.

        Args:
            date_obj: LinkedIn date dict with year and month

        Returns:
            ISO format date string or None
        """
        if not date_obj:
            return None

        year = date_obj.get("year")
        month = date_obj.get("month", 1)
        day = date_obj.get("day", 1)

        if year:
            try:
                return f"{year:04d}-{month:02d}-{day:02d}"
            except (ValueError, TypeError):
                return None

        return None

    async def get_profile_by_url(self, profile_url: str) -> Dict[str, Any]:
        """
        Fetch LinkedIn profile by public profile URL.

        Note: This requires additional permissions and may not be available
        with all LinkedIn API access tiers.

        Args:
            profile_url: LinkedIn public profile URL
                (e.g., "https://www.linkedin.com/in/username")

        Returns:
            Dictionary containing profile data

        Raises:
            LinkedInAPIError: For API errors or invalid URL format
            ValueError: If profile_url is invalid

        Examples:
            >>> service = LinkedInService(access_token="your_token")
            >>> profile = await service.get_profile_by_url(
            ...     "https://www.linkedin.com/in/johndoe"
            ... )
        """
        # Extract profile ID or username from URL
        # This is a simplified implementation - LinkedIn's public URL handling
        # requires additional API calls and permissions

        if not profile_url or not isinstance(profile_url, str):
            raise ValueError("profile_url must be a non-empty string")

        # Basic URL validation
        if "linkedin.com/in/" not in profile_url:
            raise ValueError(
                "Invalid LinkedIn profile URL. Expected format: "
                "https://www.linkedin.com/in/username"
            )

        # For now, we'll log a warning as this requires additional permissions
        logger.warning(
            "get_profile_by_url requires additional LinkedIn API permissions. "
            "Use get_profile() with profile_id instead."
        )

        # Try to extract username from URL
        # In production, you would use the LinkedIn API to resolve this
        raise LinkedInAPIError(
            "Profile URL lookup requires additional LinkedIn API permissions. "
            "Please use get_profile() with a profile_id instead."
        )

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dictionary with keys:
                - daily_used: Requests used today
                - daily_limit: Daily request limit
                - daily_remaining: Remaining daily requests
                - minute_used: Requests used this minute
                - minute_limit: Per-minute request limit
                - minute_remaining: Remaining minute requests
                - last_request: Timestamp of last request
        """
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        minute_key = now.strftime("%Y-%m-%d_%H:%M")

        daily_used = self._daily_requests.get(date_key, 0)
        minute_used = self._minute_requests.get(minute_key, 0)

        return {
            "daily_used": daily_used,
            "daily_limit": self._rate_limit_per_day,
            "daily_remaining": max(0, self._rate_limit_per_day - daily_used),
            "minute_used": minute_used,
            "minute_limit": self._rate_limit_per_minute,
            "minute_remaining": max(0, self._rate_limit_per_minute - minute_used),
            "last_request": self._last_request_time,
        }

    def validate_access_token(self) -> bool:
        """
        Validate the current access token format.

        Note: This is a basic validation. For full validation, make an API call.

        Returns:
            True if token format is valid, False otherwise
        """
        if not self.access_token or not isinstance(self.access_token, str):
            return False

        # LinkedIn access tokens are typically long strings (200+ chars)
        return len(self.access_token) > 50
