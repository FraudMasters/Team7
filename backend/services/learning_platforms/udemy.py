"""
Udemy learning platform API client.

This module provides a client for interacting with the Udemy API to search
and retrieve course information. The client supports course search by skill/topic,
detailed course information retrieval, OAuth 2.0 authentication, and proper
error handling with retry logic.

The Udemy API uses OAuth 2.0 with client credentials flow and provides access to:
- Course catalog search
- Course details and metadata
- Instructor information
- Pricing and enrollment data

Example:
    >>> from services.learning_platforms.udemy import UdemyClient
    >>> client = UdemyClient()
    >>> results = client.search_courses("python", max_results=5)
    >>> for course in results.courses:
    ...     print(f"{course.title}: {course.rating}/5.0")
"""
import base64
import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings
from .base import Course, LearningPlatformClient, SearchResult

logger = logging.getLogger(__name__)


class UdemyClient(LearningPlatformClient):
    """
    Udemy API client for course search and retrieval.

    This client provides methods to search for courses on Udemy and retrieve
    detailed course information. It handles OAuth 2.0 authentication, rate limiting,
    and error recovery with retry logic.

    Attributes:
        PLATFORM_NAME: Platform identifier ("udemy")
        client_id: Udemy API client ID
        client_secret: Udemy API client secret
        base_url: Udemy API base URL
        enabled: Whether the client is enabled
        timeout_seconds: Request timeout in seconds
        access_token: OAuth access token for API requests

    Example:
        >>> client = UdemyClient()
        >>> results = client.search_courses_by_skill("python")
        >>> print(f"Found {len(results)} courses")
        5
    """

    PLATFORM_NAME = "udemy"

    # Udemy API endpoints
    SEARCH_ENDPOINT = "/api-2.0/courses/"
    COURSES_ENDPOINT = "/api-2.0/courses/"
    TOKEN_ENDPOINT = "/oauth/v2/token"

    # Skill level mappings for Udemy
    # Udemy uses: "All Levels", "Beginner", "Intermediate", "Expert", "Intermediate Level"
    SKILL_LEVEL_MAP = {
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Expert",
        "expert": "Expert",
    }

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
    ):
        """
        Initialize Udemy API client.

        Args:
            client_id: Udemy API client ID (defaults to settings)
            client_secret: Udemy API client secret (defaults to settings)
            base_url: Udemy API base URL (defaults to settings)
            enabled: Whether client is enabled (defaults to settings)
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            retry_delay_seconds: Initial retry delay with exponential backoff
        """
        settings = get_settings()

        self.client_id = client_id or settings.udemy_client_id
        self.client_secret = client_secret or settings.udemy_client_secret
        self.base_url = base_url or settings.udemy_base_url
        self.enabled = enabled if enabled is not None else settings.udemy_enabled

        # Check if credentials are configured
        if not self.client_id or not self.client_secret:
            logger.warning("Udemy API credentials not configured, client will be disabled")
            self.enabled = False

        super().__init__(
            enabled=self.enabled,
            timeout_seconds=timeout_seconds or settings.udemy_timeout_seconds,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )

        # OAuth token storage
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

        # HTTP client for API requests
        self._client: Optional[httpx.Client] = None
        self._auth_client: Optional[httpx.Client] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize HTTP clients for API and authentication.

        Creates httpx clients with appropriate headers.
        Handles initialization errors gracefully.
        """
        if not self.enabled:
            logger.info("Udemy client is disabled, skipping HTTP client initialization")
            return

        try:
            # API client (Authorization header added dynamically)
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AgentHR/1.0",
                    "Accept": "application/json",
                },
                timeout=self.timeout_seconds,
            )

            # Auth client (separate client for OAuth requests)
            self._auth_client = httpx.Client(
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                timeout=self.timeout_seconds,
            )

            logger.info("Udemy HTTP clients initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Udemy HTTP client: {e}")
            self.enabled = False
            self._client = None
            self._auth_client = None

    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth access token, refreshing if expired.

        Returns:
            Access token or None if authentication fails
        """
        # Check if token is still valid
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        # Token expired or not set, get new token
        if not self._auth_client:
            logger.error("Udemy auth client not initialized")
            return None

        try:
            # Prepare Basic Auth header
            credentials = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()

            headers = {
                "Authorization": f"Basic {credentials}",
            }

            data = {
                "grant_type": "client_credentials",
            }

            response = self._auth_client.post(
                self.TOKEN_ENDPOINT,
                data=data,
                headers=headers,
            )
            response.raise_for_status()

            token_data = response.json()

            self._access_token = token_data.get("access_token")
            # Set expiration to 30 seconds before actual expiry for safety
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in - 30

            logger.info("Successfully refreshed Udemy access token")
            return self._access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"Udemy OAuth HTTP error: {e.response.status_code}")
            if e.response.status_code == 401:
                logger.error("Udemy OAuth authentication failed - check client credentials")
            return None

        except Exception as e:
            logger.error(f"Failed to get Udemy access token: {e}", exc_info=True)
            return None

    def _test_connection(self) -> bool:
        """
        Test connection to Udemy API.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled or self._client is None:
            return False

        try:
            # Try to get access token and make a simple search request
            token = self._get_access_token()
            if not token:
                return False

            headers = {"Authorization": f"Bearer {token}"}
            response = self._client.get(
                f"{self.SEARCH_ENDPOINT}?page_size=1",
                headers=headers,
            )
            return response.status_code in (200, 401, 403)

        except Exception as e:
            logger.error(f"Udemy connection test failed: {e}")
            return False

    def search_courses(
        self,
        query: str,
        skill_level: Optional[str] = None,
        language: Optional[str] = None,
        max_results: int = 20,
        page: int = 1,
        **kwargs,
    ) -> SearchResult:
        """
        Search for courses on Udemy.

        Args:
            query: Search query (skill name, topic, or keyword)
            skill_level: Filter by skill level (beginner, intermediate, advanced)
            language: Filter by language code (en, es, etc.)
            max_results: Maximum number of results to return
            page: Page number for pagination
            **kwargs: Additional Udemy-specific filters:
                - category: Course category ID
                - price: Price filter ("price-free" or "price-paid")
                - avg_rating: Minimum average rating (e.g., "4.5")
                - subcategory: Subcategory ID

        Returns:
            SearchResult with matching courses

        Raises:
            ConnectionError: If API connection fails
            ValueError: If invalid parameters provided
        """
        if not self.enabled or self._client is None:
            logger.warning("Udemy client is disabled or not initialized")
            return SearchResult(
                courses=[],
                platform=self.PLATFORM_NAME,
                search_query=query,
                filters_applied=kwargs,
            )

        # Get OAuth token
        token = self._get_access_token()
        if not token:
            logger.error("Failed to get Udemy access token")
            return SearchResult(
                courses=[],
                platform=self.PLATFORM_NAME,
                search_query=query,
                filters_applied=kwargs,
            )

        # Build search parameters
        params = {
            "search": query,
            "page_size": min(max_results, 100),  # Udemy API limit
            "page": page,
        }

        # Add skill level filter
        if skill_level:
            mapped_level = self.SKILL_LEVEL_MAP.get(skill_level.lower())
            if mapped_level:
                params["instructional_level"] = mapped_level

        # Add language filter (Udemy uses locale codes)
        if language:
            params["locale"] = language

        # Add additional filters
        params.update(kwargs)

        logger.debug(f"Searching Udemy with params: {params}")

        # Make request with retry logic
        courses = []
        total_results = 0

        for attempt in range(self.max_retries):
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = self._client.get(
                    self.SEARCH_ENDPOINT,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()

                data = response.json()

                # Parse response
                courses, total_results = self._parse_search_response(data)

                logger.info(
                    f"Udemy search returned {len(courses)} courses "
                    f"(total: {total_results})"
                )

                break

            except httpx.HTTPStatusError as e:
                logger.error(f"Udemy API HTTP error: {e.response.status_code}")
                if e.response.status_code == 401:
                    # Token expired, refresh and retry
                    self._access_token = None
                    token = self._get_access_token()
                    if token and attempt < self.max_retries - 1:
                        continue
                    raise ConnectionError("Udemy API authentication failed") from e
                elif e.response.status_code == 429:
                    # Rate limited - wait and retry
                    delay = self._build_retry_delay(attempt)
                    logger.warning(f"Udemy rate limited, waiting {delay}s before retry")
                    time.sleep(delay)
                    continue
                else:
                    raise ConnectionError(f"Udemy API error: {e}") from e

            except httpx.RequestError as e:
                logger.error(f"Udemy API request error: {e}")
                if attempt < self.max_retries - 1:
                    delay = self._build_retry_delay(attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise ConnectionError(f"Udemy API request failed: {e}") from e

            except Exception as e:
                logger.error(f"Unexpected error searching Udemy: {e}", exc_info=True)
                raise

        return SearchResult(
            courses=courses,
            total_results=total_results,
            page=page,
            results_per_page=max_results,
            has_more=len(courses) == max_results,
            platform=self.PLATFORM_NAME,
            search_query=query,
            filters_applied=params,
        )

    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """
        Get detailed course information by Udemy course ID.

        Args:
            course_id: Udemy course ID (numeric as string)

        Returns:
            Course object with detailed information, or None if not found

        Raises:
            ConnectionError: If API connection fails
        """
        if not self.enabled or self._client is None:
            logger.warning("Udemy client is disabled or not initialized")
            return None

        # Get OAuth token
        token = self._get_access_token()
        if not token:
            logger.error("Failed to get Udemy access token")
            return None

        logger.debug(f"Fetching Udemy course: {course_id}")

        for attempt in range(self.max_retries):
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = self._client.get(
                    f"{self.COURSES_ENDPOINT}{course_id}/",
                    headers=headers,
                )
                response.raise_for_status()

                data = response.json()
                course = self._parse_course(data)

                logger.info(f"Successfully fetched Udemy course: {course_id}")
                return course

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Udemy course not found: {course_id}")
                    return None
                elif e.response.status_code == 401:
                    # Token expired, refresh and retry
                    self._access_token = None
                    token = self._get_access_token()
                    if token and attempt < self.max_retries - 1:
                        continue
                    raise ConnectionError("Udemy API authentication failed") from e
                else:
                    logger.error(f"Udemy API HTTP error: {e.response.status_code}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self._build_retry_delay(attempt))
                        continue
                    raise ConnectionError(f"Udemy API error: {e}") from e

            except httpx.RequestError as e:
                logger.error(f"Udemy API request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self._build_retry_delay(attempt))
                    continue
                raise ConnectionError(f"Udemy API request failed: {e}") from e

            except Exception as e:
                logger.error(f"Unexpected error fetching Udemy course: {e}", exc_info=True)
                raise

        return None

    def search_courses_by_skill(
        self,
        skill: str,
        skill_level: Optional[str] = None,
        max_results: int = 10,
        **kwargs,
    ) -> List[Course]:
        """
        Search for courses relevant to a specific skill.

        Args:
            skill: Skill name to search for
            skill_level: Required skill level (beginner, intermediate, advanced)
            max_results: Maximum number of results
            **kwargs: Additional Udemy-specific filters

        Returns:
            List of matching Course objects
        """
        result = self.search_courses(
            query=skill,
            skill_level=skill_level,
            max_results=max_results,
            **kwargs,
        )
        return result.courses

    def _parse_search_response(self, data: Dict[str, Any]) -> tuple[List[Course], int]:
        """
        Parse Udemy search API response.

        Args:
            data: Raw API response data

        Returns:
            Tuple of (list of Course objects, total results count)
        """
        courses = []

        # Udemy API response structure
        results = data.get("results", [])
        total_results = data.get("count", len(results))

        for course_data in results:
            try:
                course = self._parse_course(course_data)
                if course:
                    courses.append(course)
            except Exception as e:
                logger.warning(f"Failed to parse course from search results: {e}")
                continue

        return courses, total_results

    def _parse_course(self, data: Dict[str, Any]) -> Optional[Course]:
        """
        Parse course data from Udemy API response.

        Args:
            data: Raw course data from API

        Returns:
            Course object or None if parsing fails
        """
        try:
            # Extract basic info
            course_id = str(data.get("id", ""))
            title = data.get("title", "")
            description = data.get("headline", "")
            url = data.get("url", "")

            # Extract instructor(s)
            instructors = data.get("instructors", [])
            instructor_name = ""
            if instructors and len(instructors) > 0:
                instructor_name = instructors[0].get("display_name", "")

            # Extract skill level
            instructional_level = data.get("instructional_level", {})
            if isinstance(instructional_level, str):
                skill_level_raw = instructional_level
            else:
                skill_level_raw = instructional_level.get("title", "Intermediate")

            skill_level_map = {
                "Beginner": "beginner",
                "All Levels": "beginner",
                "Intermediate Level": "intermediate",
                "Intermediate": "intermediate",
                "Expert": "advanced",
                "Advanced": "advanced",
            }
            skill_level = skill_level_map.get(skill_level_raw, "intermediate").lower()

            # Extract duration (Udemy provides content length in minutes)
            content_info = data.get("content_info", "")
            duration_hours = 0.0
            if isinstance(content_info, str):
                import re

                # Parse duration like "15 hours on-demand video"
                match = re.search(r"(\d+(?:\.\d+)?)\s*hours?", content_info.lower())
                if match:
                    duration_hours = float(match.group(1))

            # Extract pricing
            price_detail = data.get("price_detail", {})
            price_amount = price_detail.get("amount", 0)
            cost_amount = float(price_amount) if price_amount else 0.0

            # Extract ratings
            rating = float(data.get("avg_rating", 0))
            rating_count = int(data.get("num_reviews", 0))
            enrollment_count = int(data.get("num_subscribers", 0))

            # Extract image
            image = data.get("image_480x270", "") or data.get("image", "")

            # Determine access type based on price
            access_type = "free" if cost_amount == 0 else "paid"

            # Extract language
            language = data.get("locale", {}).get("simple_english_title", "en").lower()
            # Map to ISO code
            language_map = {
                "english": "en",
                "spanish": "es",
                "french": "fr",
                "german": "de",
                "portuguese": "pt",
                "japanese": "ja",
                "chinese": "zh",
            }
            language = language_map.get(language, language[:2])

            return Course(
                platform=self.PLATFORM_NAME,
                course_id=course_id,
                title=title,
                description=description,
                url=url,
                instructor=instructor_name,
                skill_level=skill_level,
                topics_covered=[],  # Udemy doesn't provide this in basic search
                prerequisites=[],
                language=language,
                is_self_paced=True,
                duration_hours=duration_hours,
                duration_weeks=0.0,
                cost_amount=cost_amount,
                currency="USD",
                access_type=access_type,
                rating=rating,
                rating_count=rating_count,
                enrollment_count=enrollment_count,
                certificate_offered=True,  # Most Udemy courses offer certificates
                image_url=image,
            )

        except Exception as e:
            logger.error(f"Failed to parse Udemy course data: {e}", exc_info=True)
            return None

    def close(self) -> None:
        """
        Close HTTP clients and cleanup resources.

        Call this when shutting down the application.
        """
        if self._client is not None:
            try:
                self._client.close()
                logger.info("Udemy API client closed")
            except Exception as e:
                logger.error(f"Error closing Udemy API client: {e}")
            finally:
                self._client = None

        if self._auth_client is not None:
            try:
                self._auth_client.close()
            except Exception as e:
                logger.error(f"Error closing Udemy auth client: {e}")
            finally:
                self._auth_client = None


# Global Udemy client instance
_udemy_client: Optional[UdemyClient] = None


def get_udemy_client() -> UdemyClient:
    """
    Get or create global Udemy client instance.

    Returns:
        Global UdemyClient instance

    Example:
        >>> client = get_udemy_client()
        >>> courses = client.search_courses_by_skill("python")
    """
    global _udemy_client
    if _udemy_client is None:
        _udemy_client = UdemyClient()
    return _udemy_client
