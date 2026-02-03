"""
Indeed API Client for fetching applicant resumes

This module provides a client for interacting with the Indeed API to fetch
applicant resumes and associated metadata for job postings.

Features:
- Fetch applicants for specific job postings
- Retrieve resume URLs and metadata
- Handle pagination for large result sets
- Proper error handling and logging
- Support for Indeed API authentication

The client integrates with the JobBoardIntegration model to store API
credentials and configuration per organization.
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models import JobBoardIntegration

logger = logging.getLogger(__name__)


@dataclass
class IndeedApplicant:
    """
    Indeed applicant data structure.

    Attributes:
        applicant_id: Unique identifier for the applicant in Indeed
        resume_url: URL to download the resume file
        candidate_name: Full name of the candidate
        candidate_email: Email address of the candidate
        candidate_phone: Phone number of the candidate (optional)
        job_title: Job title applied for
        application_date: Date when the application was submitted
        status: Current status of the application
        metadata: Additional metadata from Indeed
        resume_text: Extracted text from resume (if available)
    """

    applicant_id: str
    resume_url: str
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    job_title: Optional[str] = None
    application_date: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    resume_text: Optional[str] = None


@dataclass
class IndeedFetchResult:
    """
    Result of fetching applicants from Indeed.

    Attributes:
        applicants: List of applicants fetched
        total_count: Total number of applicants available
        page: Current page number
        page_size: Number of applicants per page
        has_more: Whether there are more applicants to fetch
        errors: List of any errors that occurred during fetching
    """

    applicants: List[IndeedApplicant]
    total_count: int
    page: int
    page_size: int
    has_more: bool
    errors: List[str]


class IndeedClient:
    """
    Client for interacting with the Indeed API.

    This client provides methods to fetch applicant resumes from Indeed
    for specified job postings, handling authentication, pagination,
    and error recovery.

    The Indeed API uses API key authentication and provides endpoints
    for retrieving applicants for job postings managed through the
    Indeed employer platform.
    """

    # Indeed API endpoints
    BASE_URL = "https://api.indeed.com/v1"
    APPLICANTS_ENDPOINT = "/jobs/{job_id}/applicants"
    RESUME_ENDPOINT = "/applicants/{applicant_id}/resume"

    # Default pagination settings
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the Indeed API client.

        Args:
            api_key: Indeed API key for authentication
            api_endpoint: Custom API endpoint URL (for testing/overrides)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = api_endpoint or self.BASE_URL
        self.timeout = timeout

        # Initialize HTTP client with proper settings
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

        logger.info(f"IndeedClient initialized with base_url: {self.base_url}")

    async def fetch_applicants(
        self,
        job_id: str,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        status_filter: Optional[str] = None,
        from_date: Optional[str] = None,
    ) -> IndeedFetchResult:
        """
        Fetch applicants for a specific job posting from Indeed.

        Args:
            job_id: Indeed job ID to fetch applicants for
            page: Page number for pagination (1-indexed)
            page_size: Number of applicants per page
            status_filter: Filter by application status (e.g., 'new', 'reviewed')
            from_date: Filter applications from this date onwards (ISO format)

        Returns:
            IndeedFetchResult with applicants and metadata

        Raises:
            ValueError: If API key is not configured or parameters are invalid
            httpx.HTTPError: If the HTTP request fails
        """
        try:
            logger.info(
                f"Fetching applicants for job_id={job_id}, page={page}, "
                f"page_size={page_size}, status_filter={status_filter}"
            )

            # Validate API key
            if not self.api_key:
                raise ValueError("Indeed API key is not configured")

            # Validate page_size
            if page_size > self.MAX_PAGE_SIZE:
                logger.warning(
                    f"page_size {page_size} exceeds maximum {self.MAX_PAGE_SIZE}, "
                    "clamping to maximum"
                )
                page_size = self.MAX_PAGE_SIZE

            # Build query parameters
            params = {
                "page": page,
                "limit": page_size,
            }

            if status_filter:
                params["status"] = status_filter

            if from_date:
                params["from_date"] = from_date

            # Make API request
            response = await self.client.get(
                self.APPLICANTS_ENDPOINT.format(job_id=job_id),
                params=params,
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Convert to IndeedApplicant objects
            applicants = []
            for applicant_data in data.get("applicants", []):
                try:
                    applicant = self._parse_applicant_data(applicant_data)
                    applicants.append(applicant)
                except Exception as e:
                    logger.error(
                        f"Failed to parse applicant data: {e}, "
                        f"data: {applicant_data}"
                    )

            # Calculate pagination metadata
            total_count = data.get("total_count", 0)
            has_more = page * page_size < total_count

            logger.info(
                f"Fetched {len(applicants)} applicants for job_id={job_id}, "
                f"total={total_count}, has_more={has_more}"
            )

            return IndeedFetchResult(
                applicants=applicants,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_more=has_more,
                errors=[],
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error fetching applicants: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            return IndeedFetchResult(
                applicants=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False,
                errors=[error_msg],
            )

        except httpx.RequestError as e:
            error_msg = f"Request error fetching applicants: {str(e)}"
            logger.error(error_msg)
            return IndeedFetchResult(
                applicants=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False,
                errors=[error_msg],
            )

        except Exception as e:
            error_msg = f"Unexpected error fetching applicants: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return IndeedFetchResult(
                applicants=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False,
                errors=[error_msg],
            )

    async def fetch_all_applicants(
        self,
        job_id: str,
        status_filter: Optional[str] = None,
        from_date: Optional[str] = None,
        max_applicants: Optional[int] = None,
    ) -> IndeedFetchResult:
        """
        Fetch all applicants for a job posting, handling pagination automatically.

        Args:
            job_id: Indeed job ID to fetch applicants for
            status_filter: Filter by application status
            from_date: Filter applications from this date onwards
            max_applicants: Maximum number of applicants to fetch (None for unlimited)

        Returns:
            IndeedFetchResult with all applicants and metadata
        """
        try:
            logger.info(f"Fetching all applicants for job_id={job_id}")

            all_applicants = []
            all_errors = []
            page = 1
            total_count = 0
            has_more = True

            while has_more:
                # Check if we've reached the max limit
                if max_applicants and len(all_applicants) >= max_applicants:
                    logger.info(
                        f"Reached max_applicants limit: {max_applicants}, stopping pagination"
                    )
                    break

                result = await self.fetch_applicants(
                    job_id=job_id,
                    page=page,
                    page_size=self.DEFAULT_PAGE_SIZE,
                    status_filter=status_filter,
                    from_date=from_date,
                )

                # Collect applicants and errors
                all_applicants.extend(result.applicants)
                all_errors.extend(result.errors)

                # Update pagination state
                total_count = result.total_count
                has_more = result.has_more and (
                    max_applicants is None or len(all_applicants) < max_applicants
                )
                page += 1

            logger.info(
                f"Fetched total of {len(all_applicants)} applicants for job_id={job_id}"
            )

            return IndeedFetchResult(
                applicants=all_applicants,
                total_count=total_count,
                page=1,
                page_size=len(all_applicants),
                has_more=False,
                errors=all_errors,
            )

        except Exception as e:
            error_msg = f"Error in fetch_all_applicants: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return IndeedFetchResult(
                applicants=[],
                total_count=0,
                page=1,
                page_size=0,
                has_more=False,
                errors=[error_msg],
            )

    async def download_resume(self, resume_url: str) -> bytes:
        """
        Download a resume file from Indeed.

        Args:
            resume_url: URL to download the resume from

        Returns:
            Resume file content as bytes

        Raises:
            ValueError: If resume URL is invalid
            httpx.HTTPError: If download fails
        """
        try:
            logger.info(f"Downloading resume from {resume_url}")

            if not resume_url:
                raise ValueError("Resume URL is required")

            # Make request to download resume
            response = await self.client.get(resume_url)
            response.raise_for_status()

            logger.info(f"Successfully downloaded resume, size={len(response.content)} bytes")
            return response.content

        except Exception as e:
            logger.error(f"Failed to download resume: {e}", exc_info=True)
            raise

    def _parse_applicant_data(self, data: Dict[str, Any]) -> IndeedApplicant:
        """
        Parse applicant data from Indeed API response.

        Args:
            data: Raw applicant data from Indeed API

        Returns:
            IndeedApplicant object

        Raises:
            ValueError: If required fields are missing
        """
        # Extract required fields
        applicant_id = data.get("applicant_id") or data.get("id")
        if not applicant_id:
            raise ValueError("Applicant ID is required")

        resume_url = data.get("resume_url") or data.get("resumeUrl")
        if not resume_url:
            raise ValueError("Resume URL is required")

        candidate_name = data.get("candidate_name") or data.get("name") or ""
        candidate_email = data.get("candidate_email") or data.get("email") or ""

        # Extract optional fields
        candidate_phone = (
            data.get("candidate_phone") or data.get("phone") or data.get("phoneNumber")
        )
        job_title = data.get("job_title") or data.get("jobTitle")
        application_date = data.get("application_date") or data.get("applicationDate")
        status = data.get("status") or data.get("applicationStatus")
        metadata = data.get("metadata", {})
        resume_text = data.get("resume_text") or data.get("resumeText")

        return IndeedApplicant(
            applicant_id=str(applicant_id),
            resume_url=str(resume_url),
            candidate_name=str(candidate_name),
            candidate_email=str(candidate_email),
            candidate_phone=str(candidate_phone) if candidate_phone else None,
            job_title=str(job_title) if job_title else None,
            application_date=str(application_date) if application_date else None,
            status=str(status) if status else None,
            metadata=metadata if isinstance(metadata, dict) else {},
            resume_text=str(resume_text) if resume_text else None,
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("IndeedClient closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def get_indeed_client_from_integration(
    integration: JobBoardIntegration,
) -> IndeedClient:
    """
    Create an IndeedClient from a JobBoardIntegration model.

    Args:
        integration: JobBoardIntegration with Indeed credentials

    Returns:
        Configured IndeedClient instance

    Raises:
        ValueError: If integration is invalid or missing required fields
    """
    if not integration.api_key:
        raise ValueError(f"JobBoardIntegration {integration.id} missing API key")

    return IndeedClient(
        api_key=integration.api_key,
        api_endpoint=integration.api_endpoint or None,
    )


def get_indeed_client() -> Optional[IndeedClient]:
    """
    Create an IndeedClient using global settings.

    This function is designed for use with FastAPI dependency injection
    or for standalone usage outside of the database context.

    Returns:
        IndeedClient instance if API key is configured, None otherwise

    Example:
        >>> from services.job_board_clients.indeed_client import get_indeed_client
        >>>
        >>> client = get_indeed_client()
        >>> if client:
        >>>     result = await client.fetch_applicants(job_id="12345")
    """
    settings = get_settings()

    if not settings.indeed_api_key:
        logger.warning("Indeed API key not configured in settings")
        return None

    return IndeedClient(api_key=settings.indeed_api_key)
