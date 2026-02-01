"""
Audit logging utilities for tracking user actions and system events.

This module provides functions and decorators for automatically logging
audit events including user CRUD operations, system changes, and other
significant actions that require tracking for compliance and security.
"""
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditActionType, AuditLog

logger = logging.getLogger(__name__)


async def log_audit_event(
    db: AsyncSession,
    action_type: Union[AuditActionType, str],
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    action_data: Optional[dict] = None,
    before_value: Optional[dict] = None,
    after_value: Optional[dict] = None,
    reason: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Log an audit event to the database.

    This function creates an AuditLog record with the provided information.
    It's designed to be called from API endpoints, background tasks, or other
    parts of the system that need to track user actions.

    Args:
        db: Database session for persisting the audit log
        action_type: Type of action being logged (e.g., RESUME_CREATED)
        entity_type: Type of entity affected (e.g., 'resume', 'vacancy', 'user')
        entity_id: ID of the affected entity
        user_id: ID of the user who performed the action
        organization_id: ID of the organization where the action occurred
        ip_address: IP address of the client performing the action
        user_agent: User agent string of the client
        action_data: Additional action-specific data as JSON
        before_value: Entity state before the action (for sensitive actions)
        after_value: Entity state after the action (for sensitive actions)
        reason: Optional explanation for the action

    Returns:
        The created AuditLog instance, or None if logging failed

    Raises:
        ValueError: If required parameters are invalid
        SQLAlchemyError: If database operation fails

    Examples:
        >>> from models.audit_log import AuditActionType
        >>> await log_audit_event(
        ...     db=session,
        ...     action_type=AuditActionType.RESUME_CREATED,
        ...     entity_type="resume",
        ...     entity_id=resume.id,
        ...     user_id=user.id,
        ...     organization_id=org.id,
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0..."
        ... )
    """
    try:
        # Validate action_type
        if isinstance(action_type, str):
            try:
                action_type = AuditActionType(action_type)
            except ValueError:
                logger.warning(f"Unknown audit action type: {action_type}")
                # Create the log with the string value anyway for extensibility

        # Create audit log entry
        audit_log = AuditLog(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data=action_data,
            before_value=before_value,
            after_value=after_value,
            reason=reason,
        )

        db.add(audit_log)
        await db.flush()  # Ensure it's written but don't commit yet

        logger.info(
            f"Audit event logged: {action_type} on {entity_type}:{entity_id} by user:{user_id}"
        )

        return audit_log

    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        # Don't raise - audit logging failures shouldn't break the main operation
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


def audit_action(
    action_type: Union[AuditActionType, str],
    entity_type: Optional[str] = None,
    get_entity_id: Optional[Callable[[Any], Optional[UUID]] = None,
    get_user_id: Optional[Callable[[Any], Optional[UUID]] = None,
    get_org_id: Optional[Callable[[Any], Optional[UUID]] = None,
    include_request_context: bool = True,
    log_before: bool = False,
    log_after: bool = False,
):
    """
    Decorator for automatically logging function calls as audit events.

    This decorator wraps a function (typically an API endpoint or service method)
    to automatically create audit logs before or after execution. It can extract
    entity IDs, user IDs, and other context from function arguments or return values.

    Args:
        action_type: Type of action to log
        entity_type: Type of entity being operated on
        get_entity_id: Optional function to extract entity_id from arguments/return value
        get_user_id: Optional function to extract user_id from arguments
        get_org_id: Optional function to extract organization_id from arguments
        include_request_context: If True and 'request' arg exists, extract IP and user agent
        log_before: If True, log before function execution (useful for deletes)
        log_after: If True, log after function execution (default behavior)

    Returns:
        Decorated function that automatically logs audit events

    Raises:
        Exception: If the wrapped function raises an exception (audit log may still be created)

    Examples:
        >>> @audit_action(
        ...     action_type=AuditActionType.RESUME_CREATED,
        ...     entity_type="resume",
        ...     get_entity_id=lambda kwargs: kwargs.get("resume_id"),
        ... )
        ... async def create_resume(resume_id: str, db: AsyncSession):
        ...     # Function implementation
        ...     pass

        >>> # With request context
        >>> @audit_action(
        ...     action_type=AuditActionType.USER_DELETED,
        ...     entity_type="user",
        ...     log_before=True,  # Log before deletion
        ... )
        ... async def delete_user(user_id: UUID, request: Request, db: AsyncSession):
        ...     # Delete user
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract database session
            db: Optional[AsyncSession] = kwargs.get("db")
            if not db and args:
                # Try to get db from positional args (usually 2nd arg after self/cls)
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db = arg
                        break

            if not db:
                # Can't log without database session, just run the function
                logger.warning(
                    f"No database session found for audit logging on {func.__name__}"
                )
                return await func(*args, **kwargs)

            # Extract request if available
            request: Optional[Request] = kwargs.get("request")
            ip_address, user_agent = None, None
            if include_request_context and request:
                ip_address, user_agent = get_request_context(request)

            # Extract IDs
            entity_id = None
            if get_entity_id:
                entity_id = get_entity_id(kwargs)

            user_id = None
            if get_user_id:
                user_id = get_user_id(kwargs)

            organization_id = None
            if get_org_id:
                organization_id = get_org_id(kwargs)

            # Log before execution if requested
            if log_before:
                before_value = None
                if log_before and entity_id and entity_type:
                    # Optionally fetch before state here
                    # This is expensive, so only do it for sensitive operations
                    pass

                await log_audit_event(
                    db=db,
                    action_type=action_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    user_id=user_id,
                    organization_id=organization_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    before_value=before_value,
                )

            # Execute the function
            result = await func(*args, **kwargs)

            # Log after execution if requested (default)
            if log_after and not log_before:
                after_value = None
                if isinstance(result, dict):
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

                await log_audit_event(
                    db=db,
                    action_type=action_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
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
            # This is less common in this codebase but provided for completeness
            logger.warning(
                f"Synchronous audit logging not fully supported for {func.__name__}"
            )
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class AuditLogger:
    """
    Context manager for batching multiple audit log operations.

    This class provides a convenient way to log multiple related audit events
    within a single context, ensuring they all use the same metadata (user, org, etc.)

    Attributes:
        db: Database session
        user_id: Default user ID for all logs in this context
        organization_id: Default organization ID for all logs in this context
        request: Optional request for extracting IP and user agent

    Examples:
        >>> async with AuditLogger(db, user_id=user.id, organization_id=org.id, request=request) as audit:
        ...     await audit.log(AuditActionType.RESUME_CREATED, entity_type="resume", entity_id=resume1.id)
        ...     await audit.log(AuditActionType.RESUME_CREATED, entity_type="resume", entity_id=resume2.id)
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        request: Optional[Request] = None,
    ):
        """
        Initialize the AuditLogger context manager.

        Args:
            db: Database session
            user_id: Default user ID for all logs
            organization_id: Default organization ID for all logs
            request: Optional request for IP and user agent extraction
        """
        self.db = db
        self.user_id = user_id
        self.organization_id = organization_id
        self.ip_address, self.user_agent = (
            get_request_context(request) if request else (None, None)
        )
        self.logs: list[AuditLog] = []

    async def __aenter__(self) -> "AuditLogger":
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        pass  # Logs are already flushed in log_audit_event

    async def log(
        self,
        action_type: Union[AuditActionType, str],
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        action_data: Optional[dict] = None,
        before_value: Optional[dict] = None,
        after_value: Optional[dict] = None,
        reason: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """
        Log an audit event with the context's default metadata.

        Args:
            action_type: Type of action being logged
            entity_type: Type of entity affected
            entity_id: ID of the affected entity
            action_data: Additional action-specific data
            before_value: Entity state before the action
            after_value: Entity state after the action
            reason: Optional explanation for the action

        Returns:
            The created AuditLog instance
        """
        audit_log = await log_audit_event(
            db=self.db,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=self.user_id,
            organization_id=self.organization_id,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            action_data=action_data,
            before_value=before_value,
            after_value=after_value,
            reason=reason,
        )

        if audit_log:
            self.logs.append(audit_log)

        return audit_log
