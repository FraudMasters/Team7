"""
Learning platform API clients.

This package provides clients for interacting with various external learning
platform APIs including Coursera, Udemy, and others.

Example:
    from services.learning_platforms.coursera import CourseraClient
    from services.learning_platforms.udemy import UdemyClient

    coursera = CourseraClient()
    udemy = UdemyClient()

    courses = coursera.search_courses_by_skill("python")
"""

from .base import Course, LearningPlatformClient, SearchResult, get_client

__all__ = [
    "Course",
    "LearningPlatformClient",
    "SearchResult",
    "get_client",
]
