"""
Base interface for learning platform API clients.

This module provides abstract base classes and common data structures for
interacting with external learning platform APIs such as Coursera, Udemy, edX,
and other online learning providers.

The learning platform clients support:
- Course search and discovery by skill/topic
- Course metadata retrieval (title, description, duration, cost)
- Rating and enrollment information
- Authentication and rate limiting
- Error handling and retry logic
- Health checks and connection monitoring

Example:
    >>> from services.learning_platforms.coursera import CourseraClient
    >>> client = CourseraClient()
    >>> courses = client.search_courses_by_skill("python", max_results=5)
    >>> for course in courses:
    ...     print(f"{course['title']}: {course['url']}")
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Course:
    """
    Unified course data structure from learning platforms.

    This class provides a common interface for course data from different
    learning platforms, normalizing field names and formats.

    Attributes:
        platform: Platform name (coursera, udemy, edx, etc.)
        course_id: Unique course identifier from platform
        title: Course title
        description: Course description
        url: Direct URL to course
        instructor: Course instructor name
        skill_level: Difficulty level (beginner, intermediate, advanced, expert)
        duration_hours: Estimated duration in hours
        duration_weeks: Estimated duration in weeks
        cost_amount: Course cost in currency
        currency: Currency code (USD, EUR, etc.)
        access_type: Access type (free, paid, freemium, subscription)
        rating: Average rating (0-5)
        rating_count: Number of ratings/reviews
        enrollment_count: Number of enrolled students
        topics_covered: List of topics/skills covered
        prerequisites: Required prior knowledge/skills
        language: Course language code
        certificate_offered: Whether completion certificate is offered
        is_self_paced: Whether course is self-paced
        image_url: URL to course thumbnail/image
        last_updated: When course data was last updated

    Example:
        >>> course = Course(
        ...     platform="coursera",
        ...     course_id="python-101",
        ...     title="Introduction to Python",
        ...     url="https://www.coursera.org/learn/python",
        ...     skill_level="beginner",
        ...     duration_hours=20.0,
        ...     cost_amount=0.0,
        ...     currency="USD",
        ...     rating=4.8,
        ...     rating_count=12000
        ... )
        >>> print(course.title)
        Introduction to Python
    """

    # Platform identifiers
    platform: str = ""
    course_id: str = ""
    title: str = ""
    description: str = ""
    url: str = ""
    instructor: str = ""

    # Content details
    skill_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    topics_covered: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    language: str = "en"
    is_self_paced: bool = True

    # Time investment
    duration_hours: float = 0.0
    duration_weeks: float = 0.0

    # Cost and access
    cost_amount: float = 0.0
    currency: str = "USD"
    access_type: str = "free"  # free, paid, freemium, subscription

    # Quality metrics
    rating: float = 0.0
    rating_count: int = 0
    enrollment_count: int = 0
    certificate_offered: bool = False

    # Media
    image_url: Optional[str] = None

    # Metadata
    last_updated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert course to dictionary for JSON serialization.

        Returns:
            Dictionary representation of course data
        """
        return {
            "platform": self.platform,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "instructor": self.instructor,
            "skill_level": self.skill_level,
            "topics_covered": self.topics_covered,
            "prerequisites": self.prerequisites,
            "language": self.language,
            "is_self_paced": self.is_self_paced,
            "duration_hours": self.duration_hours,
            "duration_weeks": self.duration_weeks,
            "cost_amount": self.cost_amount,
            "currency": self.currency,
            "access_type": self.access_type,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "enrollment_count": self.enrollment_count,
            "certificate_offered": self.certificate_offered,
            "image_url": self.image_url,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Course":
        """
        Create Course instance from dictionary.

        Args:
            data: Dictionary containing course data

        Returns:
            Course instance
        """
        return cls(
            platform=data.get("platform", ""),
            course_id=data.get("course_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            instructor=data.get("instructor", ""),
            skill_level=data.get("skill_level", "intermediate"),
            topics_covered=data.get("topics_covered", []),
            prerequisites=data.get("prerequisites", []),
            language=data.get("language", "en"),
            is_self_paced=data.get("is_self_paced", True),
            duration_hours=data.get("duration_hours", 0.0),
            duration_weeks=data.get("duration_weeks", 0.0),
            cost_amount=data.get("cost_amount", 0.0),
            currency=data.get("currency", "USD"),
            access_type=data.get("access_type", "free"),
            rating=data.get("rating", 0.0),
            rating_count=data.get("rating_count", 0),
            enrollment_count=data.get("enrollment_count", 0),
            certificate_offered=data.get("certificate_offered", False),
            image_url=data.get("image_url"),
            last_updated=data.get("last_updated"),
        )


@dataclass
class SearchResult:
    """
    Search result from learning platform API.

    Attributes:
        courses: List of courses matching search criteria
        total_results: Total number of results available
        page: Current page number
        results_per_page: Number of results per page
        has_more: Whether more results are available
        platform: Platform that provided results
        search_query: Original search query
        filters_applied: Filters that were applied to search
    """

    courses: List[Course] = field(default_factory=list)
    total_results: int = 0
    page: int = 1
    results_per_page: int = 20
    has_more: bool = False
    platform: str = ""
    search_query: str = ""
    filters_applied: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return {
            "courses": [course.to_dict() for course in self.courses],
            "total_results": self.total_results,
            "page": self.page,
            "results_per_page": self.results_per_page,
            "has_more": self.has_more,
            "platform": self.platform,
            "search_query": self.search_query,
            "filters_applied": self.filters_applied,
        }


class LearningPlatformClient(ABC):
    """
    Abstract base class for learning platform API clients.

    All learning platform clients must inherit from this class and implement
    the required methods. This ensures a consistent interface across different
    platforms.

    Example:
        >>> class MyPlatformClient(LearningPlatformClient):
        ...     def search_courses(self, query, **kwargs):
        ...         # Implementation here
        ...         pass
        ...
        >>> client = MyPlatformClient()
        >>> results = client.search_courses("python")
    """

    # Platform identifier
    PLATFORM_NAME: str = ""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
    ):
        """
        Initialize learning platform client.

        Args:
            enabled: Whether the client is enabled (defaults to settings)
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay_seconds: Initial delay between retries (exponential backoff)
        """
        settings = get_settings()

        self.enabled = enabled if enabled is not None else True
        self.timeout_seconds = timeout_seconds or 30
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        logger.info(
            f"{self.__class__.__name__} initialized (enabled={self.enabled}, "
            f"timeout={self.timeout_seconds}s)"
        )

    @abstractmethod
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
        Search for courses by query string.

        Args:
            query: Search query (skill name, topic, or keyword)
            skill_level: Filter by skill level (beginner, intermediate, advanced)
            language: Filter by language code (en, es, etc.)
            max_results: Maximum number of results to return
            page: Page number for pagination
            **kwargs: Additional platform-specific filters

        Returns:
            SearchResult containing matching courses

        Raises:
            NotImplementedError: If not implemented by subclass
            ConnectionError: If API connection fails
            ValueError: If invalid parameters provided
        """
        raise NotImplementedError("Subclasses must implement search_courses")

    @abstractmethod
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """
        Get detailed course information by ID.

        Args:
            course_id: Unique course identifier

        Returns:
            Course object with detailed information, or None if not found

        Raises:
            NotImplementedError: If not implemented by subclass
            ConnectionError: If API connection fails
        """
        raise NotImplementedError("Subclasses must implement get_course_by_id")

    @abstractmethod
    def search_courses_by_skill(
        self,
        skill: str,
        skill_level: Optional[str] = None,
        max_results: int = 10,
        **kwargs,
    ) -> List[Course]:
        """
        Search for courses relevant to a specific skill.

        This is a convenience method that wraps search_courses with
        skill-specific defaults and filters.

        Args:
            skill: Skill name to search for
            skill_level: Required skill level
            max_results: Maximum number of results
            **kwargs: Additional platform-specific filters

        Returns:
            List of matching Course objects

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement search_courses_by_skill")

    def health_check(self) -> Dict[str, Any]:
        """
        Check API connection health and status.

        Returns:
            Dictionary with health status information

        Example:
            >>> client = CourseraClient()
            >>> health = client.health_check()
            >>> print(health)
            {'status': 'healthy', 'enabled': True, 'connected': True}
        """
        result = {
            "platform": self.PLATFORM_NAME,
            "status": "unhealthy",
            "enabled": self.enabled,
            "connected": False,
            "error": None,
        }

        if not self.enabled:
            result["error"] = f"{self.PLATFORM_NAME} client is disabled"
            return result

        try:
            # Try a simple API request
            # Subclasses can override for more specific health checks
            test_result = self._test_connection()
            result["connected"] = test_result
            result["status"] = "healthy" if test_result else "degraded"

            if not test_result:
                result["error"] = "Connection test failed"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"{self.PLATFORM_NAME} health check failed: {e}")

        return result

    def _test_connection(self) -> bool:
        """
        Test connection to the API.

        Default implementation returns True. Subclasses should override
        with actual connection testing logic.

        Returns:
            True if connection successful, False otherwise
        """
        return True

    def _build_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.

        Args:
            attempt: Current retry attempt number

        Returns:
            Delay in seconds
        """
        return self.retry_delay_seconds * (2**attempt)


# Global client instances
_client_registry: Dict[str, LearningPlatformClient] = {}


def get_client(platform_name: str) -> Optional[LearningPlatformClient]:
    """
    Get or create a learning platform client by name.

    Args:
        platform_name: Platform name (coursera, udemy, etc.)

    Returns:
        Learning platform client instance or None if not found

    Example:
        >>> client = get_client("coursera")
        >>> if client:
        ...     results = client.search_courses("python")
    """
    global _client_registry

    if platform_name in _client_registry:
        return _client_registry[platform_name]

    # Import and create client
    try:
        if platform_name.lower() == "coursera":
            from services.learning_platforms.coursera import CourseraClient

            client = CourseraClient()
        elif platform_name.lower() == "udemy":
            from services.learning_platforms.udemy import UdemyClient

            client = UdemyClient()
        else:
            logger.warning(f"Unknown learning platform: {platform_name}")
            return None

        _client_registry[platform_name] = client
        return client

    except ImportError as e:
        logger.error(f"Failed to import {platform_name} client: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create {platform_name} client: {e}")
        return None
