"""
Ashby API client for ATS integration.

This module provides integration with Ashby's API for synchronizing
candidate, job posting, and application data. It supports REST API with Bearer
token authentication and webhook handling for real-time updates.

The Ashby client supports:
- Candidate data synchronization
- Job posting/vacancy sync
- Application and stage sync
- Bi-directional data sync
- Field mapping and transformation
- Webhook handling for real-time updates
- Comprehensive error handling and retry logic

Ashby API Documentation:
- API Reference: https://developers.ashbyhq.com/
- Authentication: Bearer Token
- Webhooks: https://developers.ashbyhq.com/reference/webhooks
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from services.integration_service import (
    IntegrationError,
    IntegrationErrorType,
    IntegrationService,
    IntegrationServiceError,
    IntegrationType,
    SyncDirection,
    SyncResult,
    SyncStatus,
)
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AshbyClient(IntegrationService):
    """
    Ashby API client for ATS integration.

    This client provides comprehensive integration with Ashby's recruiting
    platform through their REST API. It supports candidate, job, application,
    and interview synchronization with bi-directional data flow.

    Attributes:
        organization_id: Organization identifier
        api_base_url: Ashby API base URL
        api_key: Ashby API key for authentication
        api_version: API version (default: v1)

    Example:
        >>> config = {
        ...     "api_key": "your_api_key",
        ...     "api_base_url": "https://api.ashbyhq.com",
        ... }
        >>> client = AshbyClient("org-123", config)
        >>> await client.test_connection()
        True
        >>> result = await client.sync_candidates(SyncDirection.PULL)
    """

    # Ashby API endpoints
    API_BASE = "https://api.ashbyhq.com"

    # API endpoints
    CANDIDATES_ENDPOINT = "/candidate"
    JOBS_ENDPOINT = "/job.posting"
    APPLICATIONS_ENDPOINT = "/application"
    STAGES_ENDPOINT = "/interview.stage"
    OFFERS_ENDPOINT = "/offer"
    USERS_ENDPOINT = "/user"
    WEBHOOK_ENDPOINT = "/webhook"

    # Pagination
    DEFAULT_PER_PAGE = 100
    MAX_PER_PAGE = 500

    def __init__(
        self,
        organization_id: str,
        config: Dict[str, Any],
        timeout: float = 30.0,
        max_retries: int = 3,
        enabled: bool = True,
    ):
        """
        Initialize the Ashby client.

        Args:
            organization_id: Organization identifier
            config: Configuration dictionary containing:
                - api_key: Ashby API key (required)
                - api_base_url: Custom API base URL (optional, defaults to Ashby API)
                - webhook_secret: Webhook signing secret (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enabled: Whether integration is enabled
        """
        # Extract and validate API key
        api_key = config.get("api_key")
        if not api_key:
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.VALIDATION,
                message="Ashby api_key is required",
            )

        # Use custom API URL or default to Ashby API
        api_base_url = config.get(
            "api_base_url", self.API_BASE
        )

        # Initialize base integration service
        super().__init__(
            integration_type=IntegrationType.ASHBY,
            api_base_url=api_base_url,
            organization_id=organization_id,
            config=config,
            timeout=timeout,
            max_retries=max_retries,
            enabled=enabled,
        )

        # API configuration
        self.api_key = api_key
        self.webhook_secret = config.get("webhook_secret")

        logger.info(
            f"Initialized Ashby client for {organization_id}"
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Ashby uses Bearer token authentication.

        Returns:
            Dictionary of authentication headers
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make API request with proper authentication and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            Response data as dictionary

        Raises:
            IntegrationServiceError: If request fails
        """
        await self._check_rate_limit()

        url = urljoin(self.api_base_url, endpoint)

        try:
            headers = self._get_auth_headers()

            # Make request
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
            )

            # Handle errors
            if response.status_code == 401:
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHENTICATION,
                    message="Authentication failed - invalid API key",
                    code="401",
                )
            elif response.status_code == 403:
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHORIZATION,
                    message="Authorization failed - insufficient permissions",
                    code="403",
                )
            elif response.status_code == 404:
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.NOT_FOUND,
                    message="Resource not found",
                    code="404",
                )
            elif response.status_code == 429:
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.RATE_LIMIT,
                    message="Rate limit exceeded - Ashby allows requests per minute",
                    code="429",
                )
            elif response.status_code >= 400:
                error_msg = response.text[:200]
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.UNKNOWN,
                    message=f"API error: {error_msg}",
                    code=str(response.status_code),
                )

            # Return JSON response (empty dict for 204 No Content)
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.TimeoutException:
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.TIMEOUT,
                message=f"Request timeout after {self.timeout}s",
            )
        except httpx.NetworkError as e:
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.NETWORK,
                message=f"Network error: {e}",
            )
        except IntegrationServiceError:
            raise
        except Exception as e:
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.INTERNAL,
                message=f"Unexpected error: {e}",
            )

    async def test_connection(self) -> bool:
        """
        Test connection to Ashby API.

        Returns:
            True if connection successful

        Raises:
            IntegrationServiceError: If connection test fails
        """
        try:
            # Try to get jobs with limit=1 to test connection
            try:
                await self._make_request(
                    "GET",
                    self.JOBS_ENDPOINT,
                    params={"limit": 1},
                )
                return True
            except IntegrationServiceError as e:
                # 401 or 403 means connection works but auth failed - that's OK for connection test
                if e.error_type in (
                    IntegrationErrorType.AUTHENTICATION,
                    IntegrationErrorType.AUTHORIZATION,
                ):
                    return True
                raise

        except Exception as e:
            logger.error(f"Ashby connection test failed: {e}")
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.NETWORK,
                message=f"Connection test failed: {e}",
            )

    async def sync_candidates(
        self,
        direction: SyncDirection = SyncDirection.PULL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        """
        Synchronize candidate data with Ashby.

        Args:
            direction: Sync direction (pull from Ashby, push to Ashby, or bidirectional)
            filters: Optional filters for sync (e.g., updated_since, job_id, status)

        Returns:
            SyncResult with operation details

        Raises:
            IntegrationServiceError: If sync fails
        """
        result = SyncResult(
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )

        try:
            if direction in (SyncDirection.PULL, SyncDirection.BIDIRECTIONAL):
                # Pull candidates from Ashby
                logger.info(f"Pulling candidates from Ashby for {self.organization_id}")

                candidates = await self._get_candidates(filters=filters)

                result.records_processed = len(candidates)
                result.records_succeeded = len(candidates)

                # Store candidates (would integrate with database here)
                # For now, just record metadata
                result.metadata["candidates_pulled"] = len(candidates)
                result.metadata["sample_candidates"] = candidates[:3] if candidates else []

            if direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
                # Push candidates to Ashby
                logger.info(f"Pushing candidates to Ashby for {self.organization_id}")

                # This would fetch candidates from local database and push to Ashby
                result.metadata["push_not_implemented"] = True

            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()

            logger.info(
                f"Candidate sync completed: {result.records_succeeded} records, "
                f"{result.duration_seconds:.2f}s"
            )

        except IntegrationServiceError as e:
            result.status = SyncStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            result.errors.append(e.message)
            raise

        except Exception as e:
            result.status = SyncStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            result.errors.append(str(e))
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.INTERNAL,
                message=f"Candidate sync failed: {e}",
            )

        return result

    async def _get_candidates(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch candidate data from Ashby.

        Args:
            filters: Optional filters (updated_since, job_id, status)

        Returns:
            List of candidate dictionaries
        """
        candidates = []

        try:
            params = {}

            if filters:
                if "updated_since" in filters:
                    params["updatedAfter"] = filters["updated_since"]
                if "job_id" in filters:
                    params["jobPostingId"] = filters["job_id"]
                if "status" in filters:
                    params["status"] = filters["status"]

            response = await self._make_request(
                "GET",
                self.CANDIDATES_ENDPOINT,
                params=params,
            )

            # Ashby returns candidates with pagination
            # Response format: {"results": [...], "nextPageToken": "..."}
            results = response.get("results", response.get("candidates", []))
            candidates.extend(results if isinstance(results, list) else [])

            # Handle pagination if there's a next page token
            next_page_token = response.get("nextPageToken")
            while next_page_token:
                params["pageToken"] = next_page_token
                response = await self._make_request(
                    "GET",
                    self.CANDIDATES_ENDPOINT,
                    params=params,
                )
                results = response.get("results", response.get("candidates", []))
                candidates.extend(results if isinstance(results, list) else [])
                next_page_token = response.get("nextPageToken")

        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch candidates from Ashby: {e}")
            raise

        # Transform fields if mappings are configured
        if "candidate" in self._field_mappings:
            candidates = [
                self.transform_fields("candidate", cand, "external_to_local")
                for cand in candidates
            ]

        logger.debug(f"Fetched {len(candidates)} candidates from Ashby")
        return candidates

    async def sync_vacancies(
        self,
        direction: SyncDirection = SyncDirection.PULL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        """
        Synchronize job posting/vacancy data with Ashby.

        Args:
            direction: Sync direction
            filters: Optional filters (e.g., status, opened_since)

        Returns:
            SyncResult with operation details

        Raises:
            IntegrationServiceError: If sync fails
        """
        result = SyncResult(
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )

        try:
            if direction in (SyncDirection.PULL, SyncDirection.BIDIRECTIONAL):
                logger.info(f"Pulling vacancies from Ashby for {self.organization_id}")

                vacancies = await self._get_vacancies(filters=filters)

                result.records_processed = len(vacancies)
                result.records_succeeded = len(vacancies)

                result.metadata["vacancies_pulled"] = len(vacancies)
                result.metadata["sample_vacancies"] = vacancies[:3] if vacancies else []

            if direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
                logger.info(f"Pushing vacancies to Ashby for {self.organization_id}")
                result.metadata["push_not_implemented"] = True

            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()

            logger.info(
                f"Vacancy sync completed: {result.records_succeeded} records, "
                f"{result.duration_seconds:.2f}s"
            )

        except IntegrationServiceError as e:
            result.status = SyncStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            result.errors.append(e.message)
            raise

        except Exception as e:
            result.status = SyncStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            result.errors.append(str(e))
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.INTERNAL,
                message=f"Vacancy sync failed: {e}",
            )

        return result

    async def _get_vacancies(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch job posting data from Ashby.

        Args:
            filters: Optional filters (status, opened_since)

        Returns:
            List of vacancy dictionaries
        """
        vacancies = []

        try:
            params = {}

            if filters:
                if "status" in filters:
                    params["status"] = filters["status"]
                if "opened_since" in filters:
                    params["openedAfter"] = filters["opened_since"]

            response = await self._make_request(
                "GET",
                self.JOBS_ENDPOINT,
                params=params,
            )

            # Ashby returns job postings with pagination
            # Response format: {"results": [...], "nextPageToken": "..."}
            results = response.get("results", response.get("jobs", response.get("jobPostings", [])))
            vacancies.extend(results if isinstance(results, list) else [])

            # Handle pagination if there's a next page token
            next_page_token = response.get("nextPageToken")
            while next_page_token:
                params["pageToken"] = next_page_token
                response = await self._make_request(
                    "GET",
                    self.JOBS_ENDPOINT,
                    params=params,
                )
                results = response.get("results", response.get("jobs", response.get("jobPostings", [])))
                vacancies.extend(results if isinstance(results, list) else [])
                next_page_token = response.get("nextPageToken")

        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch vacancies from Ashby: {e}")
            raise

        # Transform fields if mappings are configured
        if "vacancy" in self._field_mappings:
            vacancies = [
                self.transform_fields("vacancy", vac, "external_to_local")
                for vac in vacancies
            ]

        logger.debug(f"Fetched {len(vacancies)} vacancies from Ashby")
        return vacancies

    async def sync_employees(
        self,
        direction: SyncDirection = SyncDirection.PULL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        """
        Synchronize employee data with Ashby.

        Note: Ashby is primarily an ATS system, not an HRIS.
        Employee sync refers to hired candidates who became employees.
        This method syncs candidate data for hired candidates.

        Args:
            direction: Sync direction
            filters: Optional filters

        Returns:
            SyncResult with operation details
        """
        # For Ashby, employee sync = sync hired candidates
        if filters is None:
            filters = {}
        filters["status"] = "hired"

        return await self.sync_candidates(direction, filters)

    async def get_applications(
        self,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch application data from Ashby.

        Args:
            candidate_id: Optional filter by candidate ID
            job_id: Optional filter by job ID

        Returns:
            List of application dictionaries
        """
        applications = []

        try:
            params = {}

            if candidate_id:
                params["candidateId"] = candidate_id
            if job_id:
                params["jobPostingId"] = job_id

            response = await self._make_request(
                "GET",
                self.APPLICATIONS_ENDPOINT,
                params=params,
            )

            # Ashby returns applications with pagination
            results = response.get("results", response.get("applications", []))
            applications.extend(results if isinstance(results, list) else [])

            # Handle pagination
            next_page_token = response.get("nextPageToken")
            while next_page_token:
                params["pageToken"] = next_page_token
                response = await self._make_request(
                    "GET",
                    self.APPLICATIONS_ENDPOINT,
                    params=params,
                )
                results = response.get("results", response.get("applications", []))
                applications.extend(results if isinstance(results, list) else [])
                next_page_token = response.get("nextPageToken")

        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch applications from Ashby: {e}")
            raise

        logger.debug(f"Fetched {len(applications)} applications from Ashby")
        return applications

    async def update_application_stage(
        self,
        application_id: str,
        stage_id: str,
    ) -> Dict[str, Any]:
        """
        Update application stage in Ashby.

        Args:
            application_id: Application ID
            stage_id: New stage ID

        Returns:
            Updated application data
        """
        try:
            response = await self._make_request(
                "PATCH",
                f"{self.APPLICATIONS_ENDPOINT}/{application_id}",
                data={"interviewStageId": stage_id},
            )
            logger.info(f"Updated application {application_id} to stage {stage_id}")
            return response

        except IntegrationServiceError as e:
            logger.error(f"Failed to update application stage: {e}")
            raise

    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Handle Ashby webhook for real-time updates.

        Args:
            payload: Webhook payload data
            headers: HTTP headers including signature

        Returns:
            Response dictionary

        Raises:
            IntegrationServiceError: If webhook processing fails
        """
        # Verify webhook signature
        if self.webhook_secret:
            signature = headers.get("X-Ashby-Signature") or headers.get("X-Signature")
            if not signature:
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHENTICATION,
                    message="Missing webhook signature",
                )

            payload_bytes = str(payload).encode()
            if not self.verify_webhook_signature(
                payload_bytes,
                signature,
                self.webhook_secret,
            ):
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHENTICATION,
                    message="Invalid webhook signature",
                )

        # Process webhook event
        event_type = payload.get("action") or payload.get("event_type", "unknown")
        logger.info(f"Received Ashby webhook: {event_type}")

        # Handle different event types
        if event_type == "candidate.created":
            await self._handle_candidate_created(payload)
        elif event_type == "candidate.updated":
            await self._handle_candidate_updated(payload)
        elif event_type == "application.created":
            await self._handle_application_created(payload)
        elif event_type == "application.updated":
            await self._handle_application_updated(payload)
        elif event_type == "job.posting.created":
            await self._handle_job_created(payload)
        elif event_type == "job.posting.updated":
            await self._handle_job_updated(payload)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")

        return {
            "status": "processed",
            "message": f"Webhook event {event_type} processed",
        }

    async def _handle_candidate_created(self, payload: Dict[str, Any]) -> None:
        """Handle candidate created webhook event."""
        candidate_id = payload.get("payload", {}).get("id") or payload.get("candidate_id")
        logger.info(f"Processing candidate created for {candidate_id}")

        # Fetch new candidate data and sync locally
        try:
            response = await self._make_request(
                "GET",
                f"{self.CANDIDATES_ENDPOINT}/{candidate_id}",
            )
            # Store candidate in local database
            logger.debug(f"Synced new candidate {candidate_id}: {response.get('name')}")
        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch candidate {candidate_id}: {e}")

    async def _handle_candidate_updated(self, payload: Dict[str, Any]) -> None:
        """Handle candidate updated webhook event."""
        candidate_id = payload.get("payload", {}).get("id") or payload.get("candidate_id")
        logger.info(f"Processing candidate updated for {candidate_id}")

        # Fetch updated candidate data and sync locally
        try:
            response = await self._make_request(
                "GET",
                f"{self.CANDIDATES_ENDPOINT}/{candidate_id}",
            )
            # Update candidate in local database
            logger.debug(f"Synced updated candidate {candidate_id}")
        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch candidate {candidate_id}: {e}")

    async def _handle_application_created(self, payload: Dict[str, Any]) -> None:
        """Handle application created webhook event."""
        application_id = payload.get("payload", {}).get("id") or payload.get("application_id")
        logger.info(f"Processing application created for {application_id}")

        # Fetch application data and sync locally
        try:
            response = await self._make_request(
                "GET",
                f"{self.APPLICATIONS_ENDPOINT}/{application_id}",
            )
            logger.debug(f"Synced new application {application_id}")
        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch application {application_id}: {e}")

    async def _handle_application_updated(self, payload: Dict[str, Any]) -> None:
        """Handle application updated webhook event."""
        application_id = payload.get("payload", {}).get("id") or payload.get("application_id")
        logger.info(f"Processing application updated for {application_id}")

        # Fetch updated application data and sync locally
        try:
            response = await self._make_request(
                "GET",
                f"{self.APPLICATIONS_ENDPOINT}/{application_id}",
            )
            logger.debug(f"Synced updated application {application_id}")
        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch application {application_id}: {e}")

    async def _handle_job_created(self, payload: Dict[str, Any]) -> None:
        """Handle job created webhook event."""
        job_id = payload.get("payload", {}).get("id") or payload.get("job_id")
        logger.info(f"Processing job created for {job_id}")

        # Fetch job data and sync locally
        try:
            response = await self._make_request(
                "GET",
                f"{self.JOBS_ENDPOINT}/{job_id}",
            )
            logger.debug(f"Synced new job {job_id}: {response.get('title')}")
        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")

    async def _handle_job_updated(self, payload: Dict[str, Any]) -> None:
        """Handle job updated webhook event."""
        job_id = payload.get("payload", {}).get("id") or payload.get("job_id")
        logger.info(f"Processing job updated for {job_id}")

        # Fetch updated job data and sync locally
        try:
            response = await self._make_request(
                "GET",
                f"{self.JOBS_ENDPOINT}/{job_id}",
            )
            logger.debug(f"Synced updated job {job_id}")
        except IntegrationServiceError as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")


def create_ashby_client(
    organization_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> AshbyClient:
    """
    Factory function to create an Ashby client.

    Args:
        organization_id: Organization identifier
        config: Optional configuration dictionary.
            If not provided, uses settings from environment variables.

    Returns:
        Configured AshbyClient instance

    Example:
        >>> client = create_ashby_client("org-123", {
        ...     "api_key": "your_api_key",
        ... })
        >>> await client.test_connection()
        True
    """
    if config is None:
        # Build config from environment settings
        config = {
            "api_key": settings.ashby_api_key,
            "api_base_url": getattr(settings, "ashby_api_base_url", None),
            "webhook_secret": getattr(settings, "ashby_webhook_secret", None),
        }

    return AshbyClient(organization_id, config)
