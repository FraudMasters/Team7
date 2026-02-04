"""
Base integration service for HRIS and ATS platforms.

This module provides a foundation for integrating with external HRIS and ATS systems
including Workday, Greenhouse, Lever, BambooHR, and Ashby. It includes common sync
logic, error handling, retry mechanisms, and webhook support.

The base integration service supports:
- Two-way data synchronization with external platforms
- Configurable field mappings per organization
- Automatic retry with exponential backoff for failed operations
- Comprehensive error handling and logging
- Sync status tracking and reporting
- Webhook signature verification
- Rate limiting and quota management
- Health check and connection monitoring
"""
import asyncio
import hashlib
import hmac
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
)
from functools import wraps
from urllib.parse import urlparse

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Type variables for generic return types
T = TypeVar("T")


class IntegrationType(str, Enum):
    """Supported integration platforms"""

    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    BAMBOOHR = "bamboohr"
    ASHBY = "ashby"
    CUSTOM = "custom"


class SyncDirection(str, Enum):
    """Data synchronization direction"""

    PUSH = "push"  # Send data to external platform
    PULL = "pull"  # Fetch data from external platform
    BIDIRECTIONAL = "bidirectional"  # Both directions


class SyncStatus(str, Enum):
    """Status of synchronization operations"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some records succeeded, some failed
    CANCELLED = "cancelled"


class IntegrationErrorType(str, Enum):
    """Types of integration errors"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


@dataclass
class SyncResult:
    """
    Result of a synchronization operation.

    Attributes:
        status: Final sync status
        records_processed: Number of records processed
        records_succeeded: Number of records successfully synced
        records_failed: Number of records that failed to sync
        errors: List of error messages
        started_at: When the sync started
        completed_at: When the sync completed
        duration_seconds: Total duration of the sync
        metadata: Additional sync metadata
    """

    status: SyncStatus
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "status": self.status.value,
            "records_processed": self.records_processed,
            "records_succeeded": self.records_succeeded,
            "records_failed": self.records_failed,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


@dataclass
class IntegrationError:
    """
    Detailed error information from integration operations.

    Attributes:
        error_type: Category of error
        message: Human-readable error message
        code: Error code from the external API
        details: Additional error details
        timestamp: When the error occurred
        retryable: Whether the operation can be retried
    """

    error_type: IntegrationErrorType
    message: str
    code: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retryable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "retryable": self.retryable,
        }


@dataclass
class FieldMapping:
    """
    Mapping between local and external field names.

    Attributes:
        local_field: Field name in local system
        external_field: Field name in external system
        transform: Optional transformation function (e.g., date format conversion)
        required: Whether this field is required
        default_value: Default value if field is missing
    """

    local_field: str
    external_field: str
    transform: Optional[Callable[[Any], Any]] = None
    required: bool = False
    default_value: Any = None


def retry_with_exponential_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_errors: Optional[List[IntegrationErrorType]] = None,
):
    """
    Decorator for retrying operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay after each attempt
        retryable_errors: List of error types that should trigger retries

    Example:
        >>> @retry_with_exponential_backoff(max_attempts=3)
        >>> async def sync_employee(employee_id: str):
        ...     # API call that might fail
        ...     return await api.fetch_employee(employee_id)
    """

    if retryable_errors is None:
        retryable_errors = [
            IntegrationErrorType.RATE_LIMIT,
            IntegrationErrorType.NETWORK,
            IntegrationErrorType.TIMEOUT,
            IntegrationErrorType.INTERNAL,
        ]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except IntegrationServiceError as e:
                    last_exception = e

                    # Check if error is retryable
                    if e.error_type not in retryable_errors:
                        logger.warning(
                            f"Non-retryable error in {func.__name__}: {e.error_type.value}"
                        )
                        raise

                    # Don't retry after last attempt
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Max retry attempts ({max_attempts}) reached for {func.__name__}"
                        )
                        raise

                    # Log retry attempt
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.1f}s delay: {e.message}"
                    )

                    # Wait before retry
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                    raise IntegrationServiceError(
                        error_type=IntegrationErrorType.INTERNAL,
                        message=f"Unexpected error: {str(e)}",
                    )

            # Should never reach here, but just in case
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except IntegrationServiceError as e:
                    last_exception = e

                    if e.error_type not in retryable_errors:
                        logger.warning(
                            f"Non-retryable error in {func.__name__}: {e.error_type.value}"
                        )
                        raise

                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Max retry attempts ({max_attempts}) reached for {func.__name__}"
                        )
                        raise

                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.1f}s delay: {e.message}"
                    )

                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                    raise IntegrationServiceError(
                        error_type=IntegrationErrorType.INTERNAL,
                        message=f"Unexpected error: {str(e)}",
                    )

            raise last_exception

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class IntegrationServiceError(Exception):
    """
    Base exception for integration service errors.

    Attributes:
        error_type: Type of integration error
        message: Human-readable error message
        code: Error code from external API
        details: Additional error details
        retryable: Whether the operation can be retried
    """

    def __init__(
        self,
        error_type: IntegrationErrorType,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = True,
    ):
        self.error_type = error_type
        self.message = message
        self.code = code
        self.details = details or {}
        self.retryable = retryable
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "retryable": self.retryable,
        }


class IntegrationService(ABC):
    """
    Abstract base class for HRIS/ATS integration services.

    This class provides common functionality for all integrations including
    HTTP client management, authentication, retry logic, error handling,
    sync status tracking, and webhook support.

    Subclasses must implement abstract methods for platform-specific operations.

    Attributes:
        integration_type: Type of integration platform
        api_base_url: Base URL for API requests
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        enabled: Whether integration is enabled
        organization_id: Organization identifier
        config: Integration configuration dictionary

    Example:
        >>> class WorkdayService(IntegrationService):
        ...     def __init__(self, organization_id: str, config: Dict[str, Any]):
        ...         super().__init__(
        ...             integration_type=IntegrationType.WORKDAY,
        ...             api_base_url=config.get("api_url"),
        ...             organization_id=organization_id,
        ...             config=config,
        ...         )
        ...
        ...     async def test_connection(self) -> bool:
        ...         # Test API connection
        ...         return True
    """

    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1.0
    DEFAULT_MAX_DELAY = 60.0
    DEFAULT_TIMEOUT = 30.0

    # Rate limiting defaults
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds

    def __init__(
        self,
        integration_type: IntegrationType,
        api_base_url: str,
        organization_id: str,
        config: Dict[str, Any],
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        enabled: bool = True,
    ):
        """
        Initialize the integration service.

        Args:
            integration_type: Type of integration platform
            api_base_url: Base URL for API requests
            organization_id: Organization identifier
            config: Integration configuration including credentials
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enabled: Whether integration is enabled
        """
        self.integration_type = integration_type
        self.api_base_url = api_base_url.rstrip("/")
        self.organization_id = organization_id
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries
        self.enabled = enabled

        # HTTP client for API requests
        self._client: Optional[httpx.AsyncClient] = None
        self._client_sync: Optional[httpx.Client] = None

        # Field mappings for data transformation
        self._field_mappings: Dict[str, List[FieldMapping]] = {}

        # Rate limiting tracking
        self._request_times: List[float] = []
        self._rate_limit = config.get("rate_limit", self.DEFAULT_RATE_LIMIT)
        self._rate_limit_window = config.get(
            "rate_limit_window", self.DEFAULT_RATE_LIMIT_WINDOW
        )

        logger.info(
            f"Initialized {integration_type.value} integration for organization {organization_id}"
        )

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                timeout=self.timeout,
            )
        return self._client

    @property
    def client_sync(self) -> httpx.Client:
        """Get or create sync HTTP client"""
        if self._client_sync is None:
            self._client_sync = httpx.Client(
                base_url=self.api_base_url,
                timeout=self.timeout,
            )
        return self._client_sync

    async def close(self) -> None:
        """Close HTTP connections"""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._client_sync:
            self._client_sync.close()
            self._client_sync = None

    def add_field_mapping(
        self,
        entity_type: str,
        mappings: List[FieldMapping],
    ) -> None:
        """
        Add field mappings for an entity type.

        Args:
            entity_type: Type of entity (e.g., 'employee', 'candidate')
            mappings: List of field mappings
        """
        self._field_mappings[entity_type] = mappings
        logger.debug(f"Added {len(mappings)} field mappings for {entity_type}")

    def transform_fields(
        self,
        entity_type: str,
        data: Dict[str, Any],
        direction: str = "local_to_external",
    ) -> Dict[str, Any]:
        """
        Transform fields based on configured mappings.

        Args:
            entity_type: Type of entity to transform
            data: Source data dictionary
            direction: Transformation direction ('local_to_external' or 'external_to_local')

        Returns:
            Transformed data dictionary
        """
        if entity_type not in self._field_mappings:
            logger.debug(f"No field mappings for {entity_type}, returning data as-is")
            return data

        transformed = {}
        mappings = self._field_mappings[entity_type]

        for mapping in mappings:
            # Determine source and target field names
            if direction == "local_to_external":
                source_field = mapping.local_field
                target_field = mapping.external_field
            else:
                source_field = mapping.external_field
                target_field = mapping.local_field

            # Get value from source data
            value = data.get(source_field, mapping.default_value)

            # Apply transformation if configured
            if value is not None and mapping.transform:
                try:
                    value = mapping.transform(value)
                except Exception as e:
                    logger.error(
                        f"Field transform failed for {source_field}: {e}",
                        exc_info=True,
                    )
                    if mapping.required:
                        raise IntegrationServiceError(
                            error_type=IntegrationErrorType.VALIDATION,
                            message=f"Required field {source_field} transform failed: {e}",
                        )

            # Skip if value is None and field is not required
            if value is None and not mapping.required:
                continue

            transformed[target_field] = value

        logger.debug(f"Transformed {entity_type} data: {len(transformed)} fields")
        return transformed

    async def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting.

        Raises:
            IntegrationServiceError: If rate limit is exceeded
        """
        now = time.time()

        # Remove old request times outside the window
        cutoff = now - self._rate_limit_window
        self._request_times = [t for t in self._request_times if t > cutoff]

        # Check if limit is exceeded
        if len(self._request_times) >= self._rate_limit:
            wait_time = self._request_times[0] + self._rate_limit_window - now
            if wait_time > 0:
                logger.warning(f"Rate limit exceeded, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        # Record this request
        self._request_times.append(now)

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        algorithm: str = "sha256",
    ) -> bool:
        """
        Verify webhook signature for security.

        Args:
            payload: Raw request payload
            signature: Signature from request header
            secret: Webhook secret key
            algorithm: Hash algorithm used for signature

        Returns:
            True if signature is valid
        """
        try:
            # Compute expected signature
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                getattr(hashlib, algorithm),
            ).hexdigest()

            # Compare signatures securely
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}", exc_info=True)
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Check integration health and connection status.

        Returns:
            Dictionary with health status details
        """
        result = {
            "integration_type": self.integration_type.value,
            "organization_id": self.organization_id,
            "status": "unhealthy",
            "enabled": self.enabled,
            "api_base_url": self.api_base_url,
            "last_checked": datetime.utcnow().isoformat(),
            "error": None,
        }

        if not self.enabled:
            result["error"] = "Integration is disabled"
            return result

        try:
            # Test connection
            is_connected = await self.test_connection()
            result["status"] = "healthy" if is_connected else "unhealthy"
            result["connected"] = is_connected

        except IntegrationServiceError as e:
            result["error"] = e.to_dict()
            result["status"] = "unhealthy"

        except Exception as e:
            result["error"] = str(e)
            result["status"] = "unhealthy"

        return result

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to the external API.

        Returns:
            True if connection is successful

        Raises:
            IntegrationServiceError: If connection test fails
        """
        pass

    @abstractmethod
    async def sync_employees(self, direction: SyncDirection = SyncDirection.PULL) -> SyncResult:
        """
        Synchronize employee data.

        Args:
            direction: Direction of sync (push, pull, or bidirectional)

        Returns:
            SyncResult with operation details
        """
        pass

    @abstractmethod
    async def sync_candidates(self, direction: SyncDirection = SyncDirection.PULL) -> SyncResult:
        """
        Synchronize candidate data.

        Args:
            direction: Direction of sync

        Returns:
            SyncResult with operation details
        """
        pass

    @abstractmethod
    async def sync_vacancies(self, direction: SyncDirection = SyncDirection.PULL) -> SyncResult:
        """
        Synchronize vacancy/job posting data.

        Args:
            direction: Direction of sync

        Returns:
            SyncResult with operation details
        """
        pass

    def get_sync_status(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a sync operation.

        Args:
            sync_id: Sync operation identifier

        Returns:
            Sync status dictionary or None if not found
        """
        # This would typically query a database for sync status
        # Base implementation returns None
        logger.debug(f"Sync status requested for {sync_id}")
        return None

    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle incoming webhook from the integration platform.

        Args:
            payload: Webhook payload data
            headers: HTTP headers including signature

        Returns:
            Response dictionary

        Raises:
            IntegrationServiceError: If webhook processing fails
        """
        logger.info(f"Received webhook from {self.integration_type.value}")

        # Verify webhook signature
        webhook_secret = self.config.get("webhook_secret")
        if webhook_secret:
            signature = headers.get("X-Signature") or headers.get("X-Hub-Signature-256")
            if not signature:
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHENTICATION,
                    message="Missing webhook signature",
                )

            if not self.verify_webhook_signature(
                payload.get("data", b"").encode() if isinstance(payload, dict) else str(payload).encode(),
                signature,
                webhook_secret,
            ):
                raise IntegrationServiceError(
                    error_type=IntegrationErrorType.AUTHENTICATION,
                    message="Invalid webhook signature",
                )

        # Process webhook (to be implemented by subclasses)
        return {"status": "received", "message": "Webhook processed"}


# Global integration service registry
_integration_services: Dict[str, Dict[str, IntegrationService]] = {}


def register_integration_service(
    organization_id: str,
    service: IntegrationService,
) -> None:
    """
    Register an integration service for an organization.

    Args:
        organization_id: Organization identifier
        service: Integration service instance
    """
    if organization_id not in _integration_services:
        _integration_services[organization_id] = {}

    integration_type = service.integration_type.value
    _integration_services[organization_id][integration_type] = service

    logger.info(f"Registered {integration_type} integration for organization {organization_id}")


def get_integration_service(
    organization_id: str,
    integration_type: IntegrationType,
) -> Optional[IntegrationService]:
    """
    Get registered integration service for an organization.

    Args:
        organization_id: Organization identifier
        integration_type: Type of integration

    Returns:
        IntegrationService instance or None if not found
    """
    services = _integration_services.get(organization_id, {})
    return services.get(integration_type.value)


def list_integration_services(organization_id: str) -> List[str]:
    """
    List all registered integration types for an organization.

    Args:
        organization_id: Organization identifier

    Returns:
        List of integration type names
    """
    services = _integration_services.get(organization_id, {})
    return list(services.keys())
