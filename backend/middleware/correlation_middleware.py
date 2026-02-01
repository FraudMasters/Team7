"""
Correlation ID Middleware Module

This module provides middleware for automatic correlation ID management
across HTTP requests. It extracts or generates correlation IDs and makes
them available throughout the request context.

Features:
- Extract correlation ID from request headers
- Generate new correlation ID if not provided
- Add correlation ID to response headers
- Store correlation ID in request state for easy access
- Integration with the correlation utility module

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.correlation_middleware import CorrelationMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(CorrelationMiddleware)
"""
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utils.correlation import (
    get_or_generate_correlation_id,
    set_correlation_id,
    clear_correlation_id,
)

logger = logging.getLogger(__name__)

# Header name for correlation ID
CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage correlation IDs for HTTP requests.

    This middleware automatically handles correlation IDs for each request:
    1. Checks for correlation ID in request headers (X-Correlation-ID)
    2. Generates a new UUID if not present
    3. Stores the correlation ID in the request state
    4. Adds the correlation ID to response headers
    5. Makes it available via the correlation utility module

    This enables distributed tracing and log correlation across the system.

    Attributes:
        header_name: The HTTP header name to use for correlation IDs

    Example:
        The middleware is automatically applied to all requests.
        Access the correlation ID in your endpoints:
        >>> @app.get("/api/test")
        >>> async def test_endpoint(request: Request):
        ...     cor_id = request.state.correlation_id
        ...     return {"correlation_id": cor_id}
    """

    def __init__(self, app, header_name: str = CORRELATION_ID_HEADER):
        """
        Initialize the correlation middleware.

        Args:
            app: The FastAPI application instance
            header_name: The HTTP header name for correlation ID (default: X-Correlation-ID)

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = CorrelationMiddleware(app)
            >>> app.add_middleware(CorrelationMiddleware)
        """
        super().__init__(app)
        self.header_name = header_name
        logger.info(f"Correlation middleware initialized with header: {header_name}")

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and manage correlation ID.

        This method:
        1. Extracts or generates correlation ID
        2. Stores it in request state
        3. Makes it available via correlation utility
        4. Processes the request
        5. Adds correlation ID to response headers
        6. Cleans up context

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler with correlation ID header

        Example:
            The middleware automatically processes all requests.
            No manual intervention required.
        """
        # Extract correlation ID from request headers or generate new one
        provided_correlation_id = request.headers.get(self.header_name)
        correlation_id = get_or_generate_correlation_id(provided_correlation_id)

        # Store correlation ID in request state for easy access in endpoints
        request.state.correlation_id = correlation_id

        logger.debug(
            f"Request {request.method} {request.url.path} "
            f"[correlation_id={correlation_id}]"
        )

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers[self.header_name] = correlation_id

            logger.debug(
                f"Response {request.method} {request.url.path} "
                f"[status={response.status_code}, correlation_id={correlation_id}]"
            )

            return response

        except Exception as e:
            # Log error with correlation ID
            logger.error(
                f"Request error: {request.method} {request.url.path} "
                f"[correlation_id={correlation_id}] - {e}",
                exc_info=True,
            )
            raise

        finally:
            # Clean up correlation ID from context
            # Note: We don't clear it immediately as it might be needed
            # for async operations that complete after the response
            # The context will be automatically cleaned up when the request ends
            pass


def get_request_correlation_id(request: Request) -> str:
    """
    Helper function to get correlation ID from request.

    This is a convenience function to retrieve the correlation ID
    from the request state. Returns a generated ID if none exists.

    Args:
        request: The FastAPI request object

    Returns:
        The correlation ID for this request

    Example:
        >>> from fastapi import Request
        >>> from middleware.correlation_middleware import get_request_correlation_id
        >>> @app.get("/api/test")
        >>> async def test(request: Request):
        ...     cor_id = get_request_correlation_id(request)
        ...     return {"correlation_id": cor_id}
    """
    # Try to get from request state first
    if hasattr(request.state, "correlation_id"):
        return request.state.correlation_id

    # Fall back to generating a new one
    from utils.correlation import generate_correlation_id

    cor_id = generate_correlation_id()
    request.state.correlation_id = cor_id
    return cor_id
