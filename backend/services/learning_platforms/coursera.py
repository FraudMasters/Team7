"""
Coursera learning platform API client.

This module provides a client for interacting with the Coursera API to search
and retrieve course information. The client supports course search by skill/topic,
detailed course information retrieval, and proper error handling with retry logic.

The Coursera API uses OAuth 2.0 authentication and provides access to:
- Course catalog search
- Course details and metadata
- Instructor information
- Enrollment and rating data

Example:
    >>> from services.learning_platforms.coursera import CourseraClient
    >>> client = CourseraClient()
    >>> results = client.search_courses("python", max_results=5)
    >>> for course in results.courses:
    ...     print(f"{course.title}: {course.rating}/5.0")
"""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings
from .base import Course, LearningPlatformClient, SearchResult

logger = logging.getLogger(__name__)


class CourseraClient(LearningPlatformClient):
    """
    Coursera API client for course search and retrieval.

    This client provides methods to search for courses on Coursera and retrieve
    detailed course information. It handles authentication, rate limiting,
    and error recovery with retry logic.

    Attributes:
        PLATFORM_NAME: Platform identifier ("coursera")
        api_key: Coursera API key for authentication
        base_url: Coursera API base URL
        enabled: Whether the client is enabled
        timeout_seconds: Request timeout in seconds

    Example:
        >>> client = CourseraClient()
        >>> results = client.search_courses_by_skill("python")
        >>> print(f"Found {len(results)} courses")
        5
    """

    PLATFORM_NAME = "coursera"

    # Coursera API endpoints
    SEARCH_ENDPOINT = "/api/coursera/search"
    COURSES_ENDPOINT = "/api/coursera/courses"

    # Skill level mappings for Coursera
    SKILL_LEVEL_MAP = {
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
        "expert": "Expert",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
    ):
        """
        Initialize Coursera API client.

        Args:
            api_key: Coursera API key (defaults to settings)
            base_url: Coursera API base URL (defaults to settings)
            enabled: Whether client is enabled (defaults to settings)
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            retry_delay_seconds: Initial retry delay with exponential backoff
        """
        settings = get_settings()

        self.api_key = api_key or settings.coursera_api_key
        self.base_url = base_url or settings.coursera_base_url
        self.enabled = enabled if enabled is not None else settings.coursera_enabled

        # Check if API key is configured
        if not self.api_key:
            logger.warning("Coursera API key not configured, client will be disabled")
            self.enabled = False

        super().__init__(
            enabled=self.enabled,
            timeout_seconds=timeout_seconds or settings.coursera_timeout_seconds,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )

        # HTTP client for API requests
        self._client: Optional[httpx.Client] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize HTTP client with authentication.

        Creates httpx client with appropriate headers and authentication.
        Handles initialization errors gracefully.
        """
        if not self.enabled:
            logger.info("Coursera client is disabled, skipping HTTP client initialization")
            return

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AgentHR/1.0",
            }

            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout_seconds,
            )

            logger.info("Coursera HTTP client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Coursera HTTP client: {e}")
            self.enabled = False
            self._client = None

    def _test_connection(self) -> bool:
        """
        Test connection to Coursera API.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled or self._client is None:
            return False

        try:
            # Try a simple search request
            response = self._client.get(
                f"{self.SEARCH_ENDPOINT}?query=test&limit=1"
            )
            return response.status_code in (200, 401, 403)  # Any response means connection works

        except Exception as e:
            logger.error(f"Coursera connection test failed: {e}")
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
        Search for courses on Coursera.

        Args:
            query: Search query (skill name, topic, or keyword)
            skill_level: Filter by skill level (beginner, intermediate, advanced)
            language: Filter by language code (en, es, etc.)
            max_results: Maximum number of results to return
            page: Page number for pagination
            **kwargs: Additional Coursera-specific filters:
                - domain: Domain filter (e.g., "computer-science")
                - language: Course language
                - category: Course category

        Returns:
            SearchResult with matching courses

        Raises:
            ConnectionError: If API connection fails
            ValueError: If invalid parameters provided
        """
        if not self.enabled or self._client is None:
            logger.warning("Coursera client is disabled or not initialized")
            return SearchResult(
                courses=[],
                platform=self.PLATFORM_NAME,
                search_query=query,
                filters_applied=kwargs,
            )

        # Build search parameters
        params = {
            "query": query,
            "limit": min(max_results, 100),  # Coursera API limit
            "start": (page - 1) * max_results,
        }

        # Add skill level filter
        if skill_level:
            mapped_level = self.SKILL_LEVEL_MAP.get(skill_level.lower())
            if mapped_level:
                params["difficulty"] = mapped_level

        # Add language filter
        if language:
            params["language"] = language

        # Add additional filters
        params.update(kwargs)

        logger.debug(f"Searching Coursera with params: {params}")

        # Make request with retry logic
        courses = []
        total_results = 0

        for attempt in range(self.max_retries):
            try:
                response = self._client.get(self.SEARCH_ENDPOINT, params=params)
                response.raise_for_status()

                data = response.json()

                # Parse response
                courses, total_results = self._parse_search_response(data)

                logger.info(
                    f"Coursera search returned {len(courses)} courses "
                    f"(total: {total_results})"
                )

                break

            except httpx.HTTPStatusError as e:
                logger.error(f"Coursera API HTTP error: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("Coursera API authentication failed - check API key")
                    raise ConnectionError("Coursera API authentication failed") from e
                elif e.response.status_code == 429:
                    # Rate limited - wait and retry
                    delay = self._build_retry_delay(attempt)
                    logger.warning(f"Coursera rate limited, waiting {delay}s before retry")
                    time.sleep(delay)
                    continue
                else:
                    raise ConnectionError(f"Coursera API error: {e}") from e

            except httpx.RequestError as e:
                logger.error(f"Coursera API request error: {e}")
                if attempt < self.max_retries - 1:
                    delay = self._build_retry_delay(attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise ConnectionError(f"Coursera API request failed: {e}") from e

            except Exception as e:
                logger.error(f"Unexpected error searching Coursera: {e}", exc_info=True)
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
        Get detailed course information by Coursera course ID.

        Args:
            course_id: Coursera course ID

        Returns:
            Course object with detailed information, or None if not found

        Raises:
            ConnectionError: If API connection fails
        """
        if not self.enabled or self._client is None:
            logger.warning("Coursera client is disabled or not initialized")
            return None

        logger.debug(f"Fetching Coursera course: {course_id}")

        for attempt in range(self.max_retries):
            try:
                response = self._client.get(f"{self.COURSES_ENDPOINT}/{course_id}")
                response.raise_for_status()

                data = response.json()
                course = self._parse_course(data)

                logger.info(f"Successfully fetched Coursera course: {course_id}")
                return course

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Coursera course not found: {course_id}")
                    return None
                elif e.response.status_code == 401:
                    logger.error("Coursera API authentication failed")
                    raise ConnectionError("Coursera API authentication failed") from e
                else:
                    logger.error(f"Coursera API HTTP error: {e.response.status_code}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self._build_retry_delay(attempt))
                        continue
                    raise ConnectionError(f"Coursera API error: {e}") from e

            except httpx.RequestError as e:
                logger.error(f"Coursera API request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self._build_retry_delay(attempt))
                    continue
                raise ConnectionError(f"Coursera API request failed: {e}") from e

            except Exception as e:
                logger.error(f"Unexpected error fetching Coursera course: {e}", exc_info=True)
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
            **kwargs: Additional Coursera-specific filters

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
        Parse Coursera search API response.

        Args:
            data: Raw API response data

        Returns:
            Tuple of (list of Course objects, total results count)
        """
        courses = []

        # Coursera API response structure may vary
        # Handle both v1 and v3 API formats
        elements = data.get("elements", [])

        if not elements:
            # Try alternative response format
            elements = data.get("courses", [])

        total_results = data.get("paging", {}).get("total", len(elements))

        for element in elements:
            try:
                course = self._parse_course(element)
                if course:
                    courses.append(course)
            except Exception as e:
                logger.warning(f"Failed to parse course from search results: {e}")
                continue

        return courses, total_results

    def _parse_course(self, data: Dict[str, Any]) -> Optional[Course]:
        """
        Parse course data from Coursera API response.

        Args:
            data: Raw course data from API

        Returns:
            Course object or None if parsing fails
        """
        try:
            # Handle different API response formats
            course_id = data.get("id") or data.get("courseId", "")
            name = data.get("name") or data.get("title", "")
            description = data.get("description", "")

            # Extract primary language
            language = "en"
            if "primaryLanguages" in data:
                languages = data.get("primaryLanguages", [])
                language = languages[0] if languages else "en"
            elif "language" in data:
                language = data.get("language", "en")

            # Extract skill level
            skill_level_map = {
                "Beginner": "beginner",
                "Intermediate": "intermediate",
                "Advanced": "advanced",
                "Expert": "expert",
            }
            difficulty = data.get("difficultyLevel", data.get("difficulty", "Intermediate"))
            skill_level = skill_level_map.get(difficulty, "intermediate").lower()

            # Extract duration (convert weeks to hours)
            duration_weeks = 0.0
            duration_hours = 0.0
            if "workload" in data:
                workload = data.get("workload", "")
                # Parse workload like "4-6 hours/week"
                import re

                match = re.search(r"(\d+)-?(\d+)?\s*hours?", workload.lower())
                if match:
                    hours_per_week = float(match.group(1) or match.group(2))
                    # Assume 4 weeks average duration if not specified
                    duration_hours = hours_per_week * 4

            # Extract cost information
            cost_amount = 0.0
            if "price" in data:
                cost_amount = float(data.get("price", 0))

            # Extract certificate availability
            certificate_offered = data.get("certificate", {}).get("eligible", False)

            # Extract ratings
            rating = 0.0
            rating_count = 0
            if "averageRating" in data:
                rating = float(data.get("averageRating", 0))
            if "ratingCount" in data:
                rating_count = int(data.get("ratingCount", 0))

            # Extract enrollment count
            enrollment_count = 0
            if "enrollmentCount" in data:
                enrollment_count = int(data.get("enrollmentCount", 0))

            # Extract instructor(s)
            instructors = data.get("instructors", {})
            instructor_name = ""
            if isinstance(instructors, dict) and "payload" in instructors:
                instructor_payload = instructors.get("payload", [])
                if instructor_payload:
                    instructor_name = instructor_payload[0].get("fullName", "")

            # Extract URL/slug
            slug = data.get("slug", "")
            url = f"https://www.coursera.org/learn/{slug}" if slug else ""

            # Extract image URL
            image_url = data.get("photoUrl", "")

            return Course(
                platform=self.PLATFORM_NAME,
                course_id=str(course_id),
                title=name,
                description=description,
                url=url,
                instructor=instructor_name,
                skill_level=skill_level,
                topics_covered=[],  # Coursera doesn't provide this in basic search
                prerequisites=[],
                language=language,
                is_self_paced=True,
                duration_hours=duration_hours,
                duration_weeks=duration_weeks,
                cost_amount=cost_amount,
                currency="USD",
                access_type="free" if cost_amount == 0 else "paid",
                rating=rating,
                rating_count=rating_count,
                enrollment_count=enrollment_count,
                certificate_offered=certificate_offered,
                image_url=image_url,
            )

        except Exception as e:
            logger.error(f"Failed to parse Coursera course data: {e}", exc_info=True)
            return None

    def close(self) -> None:
        """
        Close HTTP client and cleanup resources.

        Call this when shutting down the application.
        """
        if self._client is not None:
            try:
                self._client.close()
                logger.info("Coursera HTTP client closed")
            except Exception as e:
                logger.error(f"Error closing Coursera HTTP client: {e}")
            finally:
                self._client = None


# Global Coursera client instance
_coursera_client: Optional[CourseraClient] = None


def get_coursera_client() -> CourseraClient:
    """
    Get or create global Coursera client instance.

    Returns:
        Global CourseraClient instance

    Example:
        >>> client = get_coursera_client()
        >>> courses = client.search_courses_by_skill("python")
    """
    global _coursera_client
    if _coursera_client is None:
        _coursera_client = CourseraClient()
    return _coursera_client
