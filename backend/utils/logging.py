"""
Structured Logging Configuration Module

This module configures structlog for structured JSON logging with correlation ID support.
It provides a unified logging interface that outputs JSON in production and readable
text in development environments.

Features:
- Structured JSON logging for production environments
- Correlation ID injection for request tracing
- Timestamp and level formatting
- Integration with standard library logging
- Development-friendly console output

Example:
    >>> from utils.logging import configure_logging, get_logger
    >>> configure_logging()
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing request", user_id=123, action="upload")
    {
        "timestamp": "2024-01-15T10:30:45.123Z",
        "level": "info",
        "logger": "module.name",
        "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "message": "Processing request",
        "user_id": 123,
        "action": "upload"
    }
"""
import logging
import sys
from typing import Any, Dict

import structlog
from config import get_settings


def configure_logging(
    json_logs: bool | None = None,
    log_level: str | None = None,
) -> None:
    """
    Configure structured logging for the application.

    This function sets up structlog with appropriate processors for either
    JSON output (production) or human-readable console output (development).
    It integrates with the standard library logging and adds correlation IDs.

    Args:
        json_logs: Force JSON output regardless of environment.
                   If None, uses STRUCTURED_LOGGING_ENABLED setting.
        log_level: Override the default log level.
                   If None, uses LOG_LEVEL setting.

    Raises:
        ValueError: If log_level is not a valid logging level

    Example:
        >>> # Use default settings from config
        >>> configure_logging()
        >>>
        >>> # Force JSON logs for testing
        >>> configure_logging(json_logs=True)
        >>>
        >>> # Override log level
        >>> configure_logging(log_level="DEBUG")
    """
    settings = get_settings()

    # Determine if we should use JSON logs
    if json_logs is None:
        json_logs = settings.structured_logging_enabled

    # Determine log level
    if log_level is None:
        log_level = settings.log_level

    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_level_upper = log_level.upper()
    if log_level_upper not in valid_levels:
        raise ValueError(
            f"Invalid log_level '{log_level}'. Must be one of: {valid_levels}"
        )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_upper,
    )

    # Define shared processors
    shared_processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),
        # Add correlation ID from context
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FILENAME]
        ),
    ]

    if json_logs:
        # Production configuration: JSON output
        structlog.configure(
            processors=shared_processors
            + [
                # Add correlation ID to log output
                _add_correlation_id,
                # Render exception information
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                # JSON renderer
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Development configuration: readable console output
        structlog.configure(
            processors=shared_processors
            + [
                # Add correlation ID to log output
                _add_correlation_id,
                # Render exception information
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                # Console renderer with colors
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Log configuration
    config_logger = structlog.get_logger()
    config_logger.info(
        "Logging configured",
        json_logs=json_logs,
        log_level=log_level_upper,
        structured_logging_enabled=settings.structured_logging_enabled,
    )


def _add_correlation_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Add correlation ID to the log event dictionary.

    This processor extracts the correlation ID from the context and adds it
    to the log event. If no correlation ID is present, it uses "N/A".

    Args:
        logger: The logger instance
        method_name: The logging method name (info, error, etc.)
        event_dict: The event dictionary to modify

    Returns:
        The modified event dictionary with correlation_id added

    Example:
        The processor is automatically called by structlog.
        No manual invocation required.
    """
    from utils.correlation import get_correlation_id

    correlation_id = get_correlation_id()
    event_dict["correlation_id"] = correlation_id or "N/A"
    return event_dict


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Returns a structlog bound logger that automatically includes correlation IDs
    and outputs structured logs in the configured format.

    Args:
        name: Optional logger name. If None, uses the calling module's name.

    Returns:
        A bound structlog instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id=123)
        >>>
        >>> # Get logger with custom name
        >>> logger = get_logger("custom.module")
        >>> logger.error("Database connection failed")
    """
    if name is None:
        # Get the calling module's name
        import inspect

        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            name = frame.f_back.f_globals.get("__name__", "__main__")
        else:
            name = "__main__"

    return structlog.get_logger(name)


class LoggingMixin:
    """
    Mixin class to add logging capabilities to any class.

    This mixin provides a `logger` attribute that is automatically configured
    with the class's module name.

    Attributes:
        logger: Structured logger instance

    Example:
        >>> class MyService(LoggingMixin):
        ...     def process(self):
        ...         self.logger.info("Processing data")
        >>>
        >>> service = MyService()
        >>> service.process()  # Logs with class module name
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """
        Get a logger for this class.

        Returns a logger named after the class's module.

        Returns:
            A bound structlog instance
        """
        return get_logger(self.__class__.__module__)


def bind_context(**kwargs: Any) -> None:
    """
    Bind key-value pairs to the logging context.

    Bound context values are automatically included in all log records
    created in the same context until they are cleared.

    Args:
        **kwargs: Key-value pairs to bind to the context

    Example:
        >>> # Bind user context for all subsequent logs
        >>> bind_context(user_id=123, request_id="abc")
        >>> logger.info("Processing")  # Automatically includes user_id and request_id
        >>>
        >>> # Clear the context
        >>> clear_context()
    """
    structlog.get_logger().bind(**kwargs)


def clear_context() -> None:
    """
    Clear all bound context from the logger.

    Removes any previously bound key-value pairs from the logging context.

    Example:
        >>> bind_context(user_id=123)
        >>> logger.info("With context")  # Includes user_id
        >>> clear_context()
        >>> logger.info("Without context")  # No user_id
    """
    structlog.get_logger().new()


def with_context(**kwargs: Any) -> structlog.BoundLogger:
    """
    Get a logger with temporary context bound to it.

    Returns a new logger instance with the specified context bound.
    The original logger is not modified.

    Args:
        **kwargs: Key-value pairs to bind to the returned logger

    Returns:
        A new logger instance with the context bound

    Example:
        >>> logger = get_logger(__name__)
        >>>
        >>> # Get a logger with temporary context
        >>> context_logger = logger.bind(user_id=123, action="upload")
        >>> context_logger.info("Processing file", filename="resume.pdf")
        >>>
        >>> # Original logger is unchanged
        >>> logger.info("No user_id here")
    """
    return structlog.get_logger().bind(**kwargs)
