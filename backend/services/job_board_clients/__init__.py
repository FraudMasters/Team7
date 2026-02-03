"""
Job Board API Clients module

This module provides client services for interacting with various job board APIs
including Indeed, ZipRecruiter, and Glassdoor.

Each client follows a consistent interface for fetching applicant resumes and
metadata from job postings on the respective platforms.
"""
from .indeed_client import (
    IndeedClient,
    IndeedApplicant,
    IndeedFetchResult,
    get_indeed_client,
    get_indeed_client_from_integration,
)

__all__ = [
    "IndeedClient",
    "IndeedApplicant",
    "IndeedFetchResult",
    "get_indeed_client",
    "get_indeed_client_from_integration",
]
