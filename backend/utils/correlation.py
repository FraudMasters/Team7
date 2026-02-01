"""
Correlation ID Utility Module

This module provides functionality for managing correlation IDs across the application.
Correlation IDs are used to track requests through the system, enabling distributed
tracing and log aggregation.

Features:
- Generate unique correlation IDs using UUID4
- Context-aware correlation ID management
- Thread-safe correlation ID storage
- Integration with logging for traceable logs

Example:
    >>> from utils.correlation import generate_correlation_id, get_correlation_id
    >>> cor_id = generate_correlation_id()
    >>> set_correlation_id(cor_id)
    >>> print(get_correlation_id())
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
"""
import logging
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable for storing the correlation ID
# ContextVars are thread-safe and async-safe, perfect for request-scoped data
_correlation_id: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)

logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """
    Generate a new unique correlation ID.

    Uses UUID4 to generate a random, unique identifier that can be used
    to correlate logs and traces across the system.

    Returns:
        A unique correlation ID string (UUID4 format)

    Example:
        >>> cor_id = generate_correlation_id()
        >>> len(cor_id)
        36
        >>> cor_id.count('-')
        4
    """
    return str(uuid.uuid4())


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Retrieves the correlation ID stored in the current context.
    Returns None if no correlation ID has been set.

    Returns:
        The current correlation ID or None if not set

    Example:
        >>> cor_id = get_correlation_id()
        >>> if cor_id:
        ...     print(f"Tracking request: {cor_id}")
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in the current context.

    Stores the provided correlation ID in the current context,
    making it available to all code running in this context.

    Args:
        correlation_id: The correlation ID to store

    Raises:
        ValueError: If correlation_id is None or empty

    Example:
        >>> cor_id = generate_correlation_id()
        >>> set_correlation_id(cor_id)
        >>> get_correlation_id() == cor_id
        True
    """
    if not correlation_id:
        raise ValueError("correlation_id cannot be None or empty")

    _correlation_id.set(correlation_id)
    logger.debug(f"Set correlation ID: {correlation_id}")


def clear_correlation_id() -> None:
    """
    Clear the correlation ID from the current context.

    Removes the correlation ID from the current context.
    This is useful for cleanup at the end of a request.

    Example:
        >>> set_correlation_id("test-id")
        >>> clear_correlation_id()
        >>> get_correlation_id() is None
        True
    """
    _correlation_id.set(None)
    logger.debug("Cleared correlation ID")


def get_or_generate_correlation_id(provided_id: Optional[str] = None) -> str:
    """
    Get existing correlation ID or generate a new one.

    If a correlation ID is provided, use it. Otherwise, check if there's
    already one set in the context. If neither exists, generate a new one.

    Args:
        provided_id: Optional correlation ID from client (e.g., from request header)

    Returns:
        A correlation ID string (never None)

    Example:
        >>> # Use provided ID
        >>> cor_id = get_or_generate_correlation_id("client-id-123")
        >>> # Use existing context ID
        >>> cor_id = get_or_generate_correlation_id()
        >>> # Generate new ID if none exists
        >>> cor_id = get_or_generate_correlation_id()
    """
    if provided_id:
        # Use the provided ID
        set_correlation_id(provided_id)
        return provided_id

    # Check if there's already one in context
    existing_id = get_correlation_id()
    if existing_id:
        return existing_id

    # Generate a new one
    new_id = generate_correlation_id()
    set_correlation_id(new_id)
    return new_id


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.

    This filter automatically adds the correlation ID to all log records,
    making it easy to trace requests through log files.

    Attributes:
        correlation_id_attribute: Name of the attribute to add to log records

    Example:
        >>> import logging
        >>> filter = CorrelationIdFilter()
        >>> logger = logging.getLogger(__name__)
        >>> logger.addFilter(filter)
        >>> # Now all logs will include correlation_id if available
    """

    def __init__(self, correlation_id_attribute: str = "correlation_id") -> None:
        """
        Initialize the correlation ID filter.

        Args:
            correlation_id_attribute: Name of the attribute to add to log records
        """
        super().__init__()
        self.correlation_id_attribute = correlation_id_attribute

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to the log record.

        Args:
            record: The log record to filter

        Returns:
            True (always allow the record to be logged)

        Example:
            The filter automatically adds correlation_id to all records.
            Configure your log formatter to use it:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - '
                '[%(correlation_id)s] - %(message)s'
            )
        """
        # Add correlation ID to the log record
        record.correlation_id = get_correlation_id() or "N/A"
        return True
