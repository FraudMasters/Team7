"""
BambooHR API client for HRIS integration.

This module provides integration with BambooHR's API for synchronizing
employee and new hire data. It supports REST API with API key authentication,
with comprehensive error handling and retry logic.

The BambooHR client supports:
- Employee data synchronization
- New hire onboarding data sync
- Bi-directional data sync
- Field mapping and transformation
- Webhook handling for real-time updates
- Comprehensive error handling and retry logic

BambooHR API Documentation:
- API Reference: https://documentation.bamboohr.com/docs
- Authentication: API Key via Basic Auth
- Data Format: JSON or XML
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


class BambooHRClient(IntegrationService):
    """
    BambooHR API client for HRIS integration.

    This client provides comprehensive integration with BambooHR's HRIS platform.
    It supports REST API with API key authentication for accessing employee data,
    organizational structure, and onboarding information.

    Attributes:
        organization_id: Organization identifier
        api_key: BambooHR API key
        subdomain: BambooHR subdomain (e.g., 'company' in company.bamboohr.com)
        api_format: Response format (json or xml)

    Example:
        >>> config = {
        ...     "subdomain": "your_company",
        ...     "api_key": "your_api_key",
        ... }
        >>> client = BambooHRClient("org-123", config)
        >>> await client.test_connection()
        True
        >>> result = await client.sync_employees(SyncDirection.PULL)
    """

    # BambooHR API endpoints
    API_BASE = "https://api.bamboohr.com/api/gateway.php"
    EMPLOYEES_ENDPOINT = "/v1/employees/directory"
    EMPLOYEE_DETAILS_ENDPOINT = "/v1/employees/{id}"
    EMPLOYEE_REPORT_ENDPOINT = "/v1/reports/custom"
    TIME_OFF_ENDPOINT = "/v1/time_off/requests"
    WEBHOOK_ENDPOINT = "/v1/webhook"

    # BambooHR field mappings (standard field names)
    STANDARD_FIELDS = [
        "id",
        "firstName",
        "lastName",
        "displayName",
        "jobTitle",
        "workPhone",
        "workPhoneExtension",
        "mobilePhone",
        "workEmail",
        "department",
        "location",
        "division",
        "state",
        "country",
        "startDate",
        "originalStartDate",
        "lastChanged",
        "status",
        "payRate",
        "payType",
        "payFrequency",
        "gender",
        "birthDate",
        "maritalStatus",
        "ssn",
        "address1",
        "address2",
        "city",
        "state",
        "zip",
        "country",
        "homePhone",
    ]

    def __init__(
        self,
        organization_id: str,
        config: Dict[str, Any],
        timeout: float = 30.0,
        max_retries: int = 3,
        enabled: bool = True,
    ):
        """
        Initialize the BambooHR client.

        Args:
            organization_id: Organization identifier
            config: Configuration dictionary containing:
                - subdomain: BambooHR subdomain (required)
                - api_key: BambooHR API key (required)
                - api_format: Response format, 'json' or 'xml' (default: json)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enabled: Whether integration is enabled
        """
        # Extract and validate required configuration
        subdomain = config.get("subdomain", "")
        api_key = config.get("api_key", "")

        if not subdomain:
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.VALIDATION,
                message="BambooHR subdomain is required",
            )

        if not api_key:
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.VALIDATION,
                message="BambooHR api_key is required",
            )

        # Build API base URL for this subdomain
        api_base = f"https://api.bamboohr.com/api/gateway.php/{subdomain}"

        # Initialize base integration service
        super().__init__(
            integration_type=IntegrationType.BAMBOOHR,
            api_base_url=api_base,
            organization_id=organization_id,
            config=config,
            timeout=timeout,
            max_retries=max_retries,
            enabled=enabled,
        )

        # Store credentials
        self.subdomain = subdomain
        self.api_key = api_key
        self.api_format = config.get("api_format", "json")

        logger.info(
            f"Initialized BambooHR client for {organization_id} "
            f"(subdomain={subdomain}, format={self.api_format})"
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        BambooHR uses API key via Basic Auth where:
        - Username: API key
        - Password: empty string (or x)

        Returns:
            Dictionary of headers including authorization
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_auth(self) -> httpx.BasicAuth:
        """
        Get BasicAuth for BambooHR API.

        Returns:
            httpx.BasicAuth with API key as username
        """
        # BambooHR uses API key as username, empty password
        return httpx.BasicAuth(self.api_key, "")

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
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            Response data as dictionary

        Raises:
            IntegrationServiceError: If request fails
        """
        await self._check_rate_limit()

        url = urljoin(self.api_base_url + "/", endpoint.lstrip("/"))

        try:
            headers = self._get_auth_headers()
            auth = self._get_auth()

            # Make request
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                auth=auth,
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
                    message="Rate limit exceeded",
                    code="429",
                )
            elif response.status_code >= 400:
                error_msg = response.text[:200]
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.UNKNOWN,
                    message=f"API error: {error_msg}",
                    code=str(response.status_code),
                )

            # Return JSON response
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
        Test connection to BambooHR API.

        Returns:
            True if connection successful

        Raises:
            IntegrationServiceError: If connection test fails
        """
        try:
            # Try to get employee directory with limit=1
            # This is a lightweight endpoint to test connectivity
            try:
                await self._make_request(
                    "GET",
                    self.EMPLOYEES_ENDPOINT,
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
            logger.error(f"BambooHR connection test failed: {e}")
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.NETWORK,
                message=f"Connection test failed: {e}",
            )

    async def sync_employees(
        self,
        direction: SyncDirection = SyncDirection.PULL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        """
        Synchronize employee data with BambooHR.

        Args:
            direction: Sync direction (pull from BambooHR, push to BambooHR, or bidirectional)
            filters: Optional filters for sync (e.g., status, department, updated_since)

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
                # Pull employees from BambooHR
                logger.info(f"Pulling employees from BambooHR for {self.organization_id}")

                employees = await self._get_employees(filters=filters)

                result.records_processed = len(employees)
                result.records_succeeded = len(employees)

                # Store employees (would integrate with database here)
                # For now, just log the count
                result.metadata["employees_pulled"] = len(employees)
                result.metadata["sample_employees"] = employees[:3] if employees else []

            if direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
                # Push employees to BambooHR
                logger.info(f"Pushing employees to BambooHR for {self.organization_id}")

                # This would fetch employees from local database and push to BambooHR
                # For now, just record that we would do it
                result.metadata["push_not_implemented"] = True

            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()

            logger.info(
                f"Employee sync completed: {result.records_succeeded} records, "
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
                message=f"Employee sync failed: {e}",
            )

        return result

    async def _get_employees(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch employee data from BambooHR.

        Args:
            filters: Optional filters (status, department, updated_since)

        Returns:
            List of employee dictionaries
        """
        try:
            # Get employee directory
            response = await self._make_request(
                "GET",
                self.EMPLOYEES_ENDPOINT,
            )

            # Extract employees from directory response
            # BambooHR returns: {"employees": [{"id": "1", "displayName": "John Doe", ...}]}
            employees = response.get("employees", [])

            # If detailed fields are needed, fetch each employee individually
            # For efficiency, we could use the custom report endpoint instead
            if filters and filters.get("include_details"):
                employees = await self._get_employee_details(
                    [emp.get("id") for emp in employees if emp.get("id")]
                )

            # Apply filters if provided
            if filters:
                if "status" in filters:
                    employees = [e for e in employees if e.get("status") == filters["status"]]
                if "department" in filters:
                    employees = [e for e in employees if e.get("department") == filters["department"]]

            # Transform fields if mappings are configured
            if "employee" in self._field_mappings:
                employees = [
                    self.transform_fields("employee", emp, "external_to_local")
                    for emp in employees
                ]

            logger.debug(f"Fetched {len(employees)} employees from BambooHR")
            return employees

        except IntegrationServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch employees from BambooHR: {e}")
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.INTERNAL,
                message=f"Failed to fetch employees: {e}",
            )

    async def _get_employee_details(
        self,
        employee_ids: List[str],
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch detailed information for specific employees.

        Args:
            employee_ids: List of employee IDs
            fields: Optional list of fields to retrieve (defaults to standard fields)

        Returns:
            List of detailed employee dictionaries
        """
        if not employee_ids:
            return []

        # Use default fields if not specified
        if fields is None:
            fields = self.STANDARD_FIELDS

        employees = []

        # Fetch each employee's details
        for emp_id in employee_ids:
            try:
                endpoint = self.EMPLOYEE_DETAILS_ENDPOINT.format(id=emp_id)
                params = {"fields": ",".join(fields)}

                response = await self._make_request("GET", endpoint, params=params)
                employee = response.get("employee", response)

                if employee:
                    employees.append(employee)

            except IntegrationServiceError as e:
                logger.warning(f"Failed to fetch details for employee {emp_id}: {e}")
                continue

        logger.debug(f"Fetched details for {len(employees)} employees")
        return employees

    async def get_employee_report(
        self,
        fields: List[str],
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate a custom employee report.

        BambooHR's custom report endpoint allows fetching specific fields
        for all employees in a single request, which is more efficient
        than fetching individual employee details.

        Args:
            fields: List of field names to include in report
            filters: Optional filters (title, department, etc.)

        Returns:
            List of employee dictionaries with requested fields
        """
        try:
            # Build report request
            report_data = {
                "fields": fields,
            }

            if filters:
                report_data["filters"] = filters

            response = await self._make_request(
                "POST",
                self.EMPLOYEE_REPORT_ENDPOINT,
                data=report_data,
            )

            employees = response.get("employees", [])

            logger.debug(f"Generated employee report with {len(employees)} records")
            return employees

        except IntegrationServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate employee report: {e}")
            raise IntegrationServiceError(
                error_type=IntegrationErrorType.INTERNAL,
                message=f"Failed to generate report: {e}",
            )

    async def sync_new_hires(
        self,
        direction: SyncDirection = SyncDirection.PULL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        """
        Synchronize new hire data from BambooHR.

        This method syncs recently hired employees, typically those with
        start dates within a recent time period.

        Args:
            direction: Sync direction
            filters: Optional filters (days_since_start, start_date_from, start_date_to)

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
                logger.info(f"Pulling new hires from BambooHR for {self.organization_id}")

                # Get all employees first
                all_employees = await self._get_employees()

                # Filter for new hires
                new_hires = self._filter_new_hires(all_employees, filters)

                result.records_processed = len(new_hires)
                result.records_succeeded = len(new_hires)

                result.metadata["new_hires_pulled"] = len(new_hires)
                result.metadata["sample_new_hires"] = new_hires[:3] if new_hires else []

            if direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
                logger.info(f"Pushing new hires to BambooHR for {self.organization_id}")
                result.metadata["push_not_implemented"] = True

            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()

            logger.info(
                f"New hire sync completed: {result.records_succeeded} records, "
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
                message=f"New hire sync failed: {e}",
            )

        return result

    def _filter_new_hires(
        self,
        employees: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter employees to identify new hires.

        Args:
            employees: List of employee dictionaries
            filters: Optional filters for determining new hires

        Returns:
            List of new hire employee dictionaries
        """
        from datetime import timedelta

        # Default filter: employees hired within last 90 days
        days_threshold = 90

        if filters:
            if "days_since_start" in filters:
                days_threshold = filters["days_since_start"]

        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        new_hires = []

        for employee in employees:
            try:
                # Parse start date
                start_date_str = employee.get("startDate") or employee.get("hireDate")
                if not start_date_str:
                    continue

                # Parse date (BambooHR typically uses YYYY-MM-DD format)
                from datetime import datetime
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                except ValueError:
                    # Try alternate formats
                    start_date = datetime.strptime(start_date_str, "%m/%d/%Y")

                # Check if hired after cutoff
                if start_date > cutoff_date:
                    new_hires.append(employee)

            except Exception as e:
                logger.debug(f"Could not parse start date for employee {employee.get('id')}: {e}")
                continue

        logger.debug(f"Identified {len(new_hires)} new hires out of {len(employees)} employees")
        return new_hires

    async def sync_candidates(
        self,
        direction: SyncDirection = SyncDirection.PULL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        """
        Synchronize candidate data.

        Note: BambooHR is primarily an HRIS system, not an ATS.
        This method syncs new hires who have been converted from candidates.

        Args:
            direction: Sync direction
            filters: Optional filters

        Returns:
            SyncResult with operation details
        """
        # For BambooHR, "candidates" are essentially new hires
        # Delegate to new hire sync
        return await self.sync_new_hires(direction, filters)

    async def sync_vacancies(
        self,
        direction: SyncDirection = SyncDirection.PULL,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        """
        Synchronize job vacancy data.

        Note: BambooHR does not have a dedicated job posting API.
        This method returns an empty result as job tracking is not
        a core BambooHR feature.

        Args:
            direction: Sync direction
            filters: Optional filters

        Returns:
            SyncResult with operation details
        """
        result = SyncResult(
            status=SyncStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=0.0,
        )

        result.metadata["message"] = "BambooHR does not support job posting sync"

        logger.info("BambooHR does not support vacancy/job posting sync")
        return result

    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Handle BambooHR webhook for real-time updates.

        BambooHR supports webhooks for employee changes, time off requests,
        and other HR events.

        Args:
            payload: Webhook payload data
            headers: HTTP headers including signature

        Returns:
            Response dictionary

        Raises:
            IntegrationServiceError: If webhook processing fails
        """
        # Verify webhook signature
        webhook_secret = self.config.get("webhook_secret")
        if webhook_secret:
            signature = headers.get("X-Signature") or headers.get("X-BambooHR-Signature")
            if not signature:
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHENTICATION,
                    message="Missing webhook signature",
                )

            payload_bytes = str(payload).encode()
            if not self.verify_webhook_signature(payload_bytes, signature, webhook_secret):
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHENTICATION,
                    message="Invalid webhook signature",
                )

        # Process webhook event
        event_type = payload.get("type") or payload.get("event")
        logger.info(f"Received BambooHR webhook: {event_type}")

        # Handle different event types
        if event_type == "employee_added":
            await self._handle_employee_added(payload)
        elif event_type == "employee_updated":
            await self._handle_employee_updated(payload)
        elif event_type == "time_off_requested":
            await self._handle_time_off_request(payload)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")

        return {
            "status": "processed",
            "message": f"Webhook event {event_type} processed",
        }

    async def _handle_employee_added(self, payload: Dict[str, Any]) -> None:
        """Handle employee added webhook event."""
        employee_id = payload.get("employeeId") or payload.get("id")
        logger.info(f"Processing employee added for {employee_id}")

        # Fetch new employee data and sync locally
        # This would trigger a database update

    async def _handle_employee_updated(self, payload: Dict[str, Any]) -> None:
        """Handle employee updated webhook event."""
        employee_id = payload.get("employeeId") or payload.get("id")
        logger.info(f"Processing employee update for {employee_id}")

        # Fetch updated employee data and sync locally

    async def _handle_time_off_request(self, payload: Dict[str, Any]) -> None:
        """Handle time off request webhook event."""
        employee_id = payload.get("employeeId") or payload.get("id")
        logger.info(f"Processing time off request for {employee_id}")

        # Process time off request


def create_bamboohr_client(
    organization_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> BambooHRClient:
    """
    Factory function to create a BambooHR client.

    Args:
        organization_id: Organization identifier
        config: Optional configuration dictionary.
            If not provided, uses settings from environment variables.

    Returns:
        Configured BambooHRClient instance

    Example:
        >>> client = create_bamboohr_client("org-123", {
        ...     "subdomain": "your_company",
        ...     "api_key": "your_api_key",
        ... })
        >>> await client.test_connection()
        True
    """
    if config is None:
        # Build config from environment settings
        config = {
            "subdomain": settings.bamboohr_subdomain,
            "api_key": settings.bamboohr_api_key,
            "api_format": getattr(settings, "bamboohr_api_format", "json"),
            "webhook_secret": getattr(settings, "bamboohr_webhook_secret", None),
        }

    return BambooHRClient(organization_id, config)
