"""
Configuration change audit logging utilities.

This module provides functions and decorators for automatically logging
configuration changes including value updates, environment switches, hot-reload
operations, and other configuration-related actions that require tracking for
compliance and security.
"""
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from models.config_change import ConfigChange, ConfigChangeAction

logger = logging.getLogger(__name__)


async def log_config_change(
    db: AsyncSession,
    action_type: Union[ConfigChangeAction, str],
    config_key: Optional[str] = None,
    config_path: Optional[str] = None,
    environment: Optional[str] = None,
    user_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    before_value: Optional[dict] = None,
    after_value: Optional[dict] = None,
    change_reason: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[ConfigChange]:
    """
    Log a configuration change to the database.

    This function creates a ConfigChange record with the provided information.
    It's designed to be called from API endpoints, background tasks, or other
    parts of the system that need to track configuration modifications.

    Args:
        db: Database session for persisting the config change log
        action_type: Type of configuration action being logged
        config_key: The configuration key that was changed
        config_path: Dot-notation path for nested configuration values
        environment: Environment where the change occurred
        user_id: ID of the user who made the change
        organization_id: ID of the organization where the change occurred
        ip_address: IP address of the client making the change
        user_agent: User agent string of the client
        before_value: Configuration value before the change
        after_value: Configuration value after the change
        change_reason: Optional explanation for the change
        metadata: Additional metadata about the change

    Returns:
        The created ConfigChange instance, or None if logging failed

    Raises:
        ValueError: If required parameters are invalid
        SQLAlchemyError: If database operation fails

    Examples:
        >>> from models.config_change import ConfigChangeAction
        >>> await log_config_change(
        ...     db=session,
        ...     action_type=ConfigChangeAction.VALUE_UPDATED,
        ...     config_key="database_url",
        ...     config_path="database.url",
        ...     environment="production",
        ...     user_id=user.id,
        ...     before_value={"url": "old-db.example.com"},
        ...     after_value={"url": "new-db.example.com"},
        ...     change_reason="Database migration"
        ... )
    """
    try:
        # Validate action_type
        if isinstance(action_type, str):
            try:
                action_type = ConfigChangeAction(action_type)
            except ValueError:
                logger.warning(f"Unknown config change action type: {action_type}")
                # Create the log with the string value anyway for extensibility

        # Create config change entry
        config_change = ConfigChange(
            action_type=action_type,
            config_key=config_key,
            config_path=config_path,
            environment=environment,
            user_id=user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value=before_value,
            after_value=after_value,
            change_reason=change_reason,
            metadata=metadata,
        )

        db.add(config_change)
        await db.flush()  # Ensure it's written but don't commit yet

        logger.info(
            f"Config change logged: {action_type} on {config_key}:{config_path} "
            f"in {environment} by user:{user_id}"
        )

        return config_change

    except Exception as e:
        logger.error(f"Failed to log config change: {e}")
        # Don't raise - config logging failures shouldn't break the main operation
        return None


def get_request_context(request: Request) -> tuple[Optional[str], Optional[str]]:
    """
    Extract IP address and user agent from a FastAPI Request.

    Args:
        request: FastAPI Request object

    Returns:
        Tuple of (ip_address, user_agent)

    Examples:
        >>> ip, ua = get_request_context(request)
        >>> print(f"Request from {ip} using {ua}")
    """
    if request is None:
        return None, None

    # Get IP address from request
    # Check for proxy headers first (X-Forwarded-For, X-Real-IP)
    ip_address = request.headers.get("X-Forwarded-For")
    if ip_address:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.headers.get("X-Real-IP")
    if not ip_address and request.client:
        ip_address = request.client.host

    # Get user agent
    user_agent = request.headers.get("User-Agent")

    return ip_address, user_agent


def audit_config_change(
    action_type: Union[ConfigChangeAction, str],
    get_config_key: Optional[Callable[[Any], Optional[str]]] = None,
    get_config_path: Optional[Callable[[Any], Optional[str]]] = None,
    get_user_id: Optional[Callable[[Any], Optional[UUID]]] = None,
    get_org_id: Optional[Callable[[Any], Optional[UUID]]] = None,
    include_request_context: bool = True,
    log_before: bool = False,
    extract_before_value: Optional[Callable[[Any], Optional[dict]]] = None,
    extract_after_value: Optional[Callable[[Any], Optional[dict]]] = None,
):
    """
    Decorator for automatically logging configuration changes.

    This decorator wraps a function (typically an API endpoint or service method)
    to automatically create config change logs before or after execution. It can
    extract configuration keys, user IDs, and other context from function arguments
    or return values.

    Args:
        action_type: Type of config change to log
        get_config_key: Optional function to extract config_key from arguments
        get_config_path: Optional function to extract config_path from arguments
        get_user_id: Optional function to extract user_id from arguments
        get_org_id: Optional function to extract organization_id from arguments
        include_request_context: If True and 'request' arg exists, extract IP and user agent
        log_before: If True, log before function execution (useful for deletes/rollbacks)
        extract_before_value: Optional function to extract before_value from arguments
        extract_after_value: Optional function to extract after_value from return value

    Returns:
        Decorated function that automatically logs config changes

    Raises:
        Exception: If the wrapped function raises an exception (config log may still be created)

    Examples:
        >>> @audit_config_change(
        ...     action_type=ConfigChangeAction.VALUE_UPDATED,
        ...     get_config_key=lambda kwargs: kwargs.get("key"),
        ... )
        ... async def update_config(key: str, value: Any, db: AsyncSession):
        ...     # Function implementation
        ...     pass

        >>> # With request context and before/after values
        >>> @audit_config_change(
        ...     action_type=ConfigChangeAction.VALUE_UPDATED,
        ...     get_config_key=lambda kwargs: kwargs.get("config_key"),
        ...     extract_before_value=lambda kwargs: kwargs.get("old_value"),
        ...     extract_after_value=lambda result: result,
        ... )
        ... async def set_config(config_key: str, new_value: Any, request: Request, db: AsyncSession):
        ...     # Update configuration
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract database session
            db: Optional[AsyncSession] = kwargs.get("db")
            if not db and args:
                # Try to get db from positional args
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db = arg
                        break

            if not db:
                # Can't log without database session, just run the function
                logger.warning(
                    f"No database session found for config audit logging on {func.__name__}"
                )
                return await func(*args, **kwargs)

            # Extract request if available
            request: Optional[Request] = kwargs.get("request")
            ip_address, user_agent = None, None
            if include_request_context and request:
                ip_address, user_agent = get_request_context(request)

            # Extract config info
            config_key = None
            if get_config_key:
                config_key = get_config_key(kwargs)

            config_path = None
            if get_config_path:
                config_path = get_config_path(kwargs)

            user_id = None
            if get_user_id:
                user_id = get_user_id(kwargs)

            organization_id = None
            if get_org_id:
                organization_id = get_org_id(kwargs)

            # Extract before value if function provided
            before_value = None
            if extract_before_value:
                before_value = extract_before_value(kwargs)

            # Log before execution if requested
            if log_before:
                await log_config_change(
                    db=db,
                    action_type=action_type,
                    config_key=config_key,
                    config_path=config_path,
                    user_id=user_id,
                    organization_id=organization_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    before_value=before_value,
                )

            # Execute the function
            result = await func(*args, **kwargs)

            # Log after execution (default behavior)
            if not log_before:
                after_value = None
                if extract_after_value:
                    after_value = extract_after_value(result)
                elif isinstance(result, dict):
                    after_value = result
                elif hasattr(result, "__dict__"):
                    # Convert model/object to dict
                    try:
                        after_value = {
                            k: v
                            for k, v in result.__dict__.items()
                            if not k.startswith("_")
                        }
                    except Exception:
                        pass

                await log_config_change(
                    db=db,
                    action_type=action_type,
                    config_key=config_key,
                    config_path=config_path,
                    user_id=user_id,
                    organization_id=organization_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    after_value=after_value,
                )

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Synchronous version for non-async functions
            logger.warning(
                f"Synchronous config audit logging not fully supported for {func.__name__}"
            )
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class ConfigAuditLogger:
    """
    Context manager for batching multiple config change log operations.

    This class provides a convenient way to log multiple related configuration
    changes within a single context, ensuring they all use the same metadata
    (user, organization, etc.)

    Attributes:
        db: Database session
        user_id: Default user ID for all logs in this context
        organization_id: Default organization ID for all logs in this context
        environment: Default environment for all logs in this context
        request: Optional request for extracting IP and user agent

    Examples:
        >>> async with ConfigAuditLogger(
        ...     db, user_id=user.id, environment="production", request=request
        ... ) as audit:
        ...     await audit.log(
        ...         ConfigChangeAction.VALUE_UPDATED,
        ...         config_key="database_url",
        ...         before_value={"old": "value"},
        ...         after_value={"new": "value"}
        ...     )
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        environment: Optional[str] = None,
        request: Optional[Request] = None,
    ):
        """
        Initialize the ConfigAuditLogger context manager.

        Args:
            db: Database session
            user_id: Default user ID for all logs
            organization_id: Default organization ID for all logs
            environment: Default environment for all logs
            request: Optional request for IP and user agent extraction
        """
        self.db = db
        self.user_id = user_id
        self.organization_id = organization_id
        self.environment = environment
        self.ip_address, self.user_agent = (
            get_request_context(request) if request else (None, None)
        )
        self.logs: list[ConfigChange] = []

    async def __aenter__(self) -> "ConfigAuditLogger":
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        pass  # Logs are already flushed in log_config_change

    async def log(
        self,
        action_type: Union[ConfigChangeAction, str],
        config_key: Optional[str] = None,
        config_path: Optional[str] = None,
        before_value: Optional[dict] = None,
        after_value: Optional[dict] = None,
        change_reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[ConfigChange]:
        """
        Log a config change with the context's default metadata.

        Args:
            action_type: Type of config change being logged
            config_key: Configuration key that was changed
            config_path: Dot-notation path for nested configs
            before_value: Configuration value before the change
            after_value: Configuration value after the change
            change_reason: Optional explanation for the change
            metadata: Additional metadata about the change

        Returns:
            The created ConfigChange instance
        """
        config_change = await log_config_change(
            db=self.db,
            action_type=action_type,
            config_key=config_key,
            config_path=config_path,
            environment=self.environment,
            user_id=self.user_id,
            organization_id=self.organization_id,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            before_value=before_value,
            after_value=after_value,
            change_reason=change_reason,
            metadata=metadata,
        )

        if config_change:
            self.logs.append(config_change)

        return config_change
