"""
Organization Context Middleware Module

This module provides middleware for automatic organization context management
across HTTP requests. It extracts organization IDs from request headers and makes
them available throughout the request context.

Features:
- Extract organization ID from request headers
- Store organization ID in request state for easy access
- Validate organization ID format
- Log organization context for debugging
- Helper function to retrieve organization context

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.organization_context import OrganizationContextMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(OrganizationContextMiddleware)
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Header name for organization ID
ORGANIZATION_ID_HEADER = "X-Organization-ID"


class OrganizationContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage organization context for HTTP requests.

    This middleware automatically handles organization context for each request:
    1. Checks for organization ID in request headers (X-Organization-ID)
    2. Validates the organization ID format
    3. Stores the organization ID in the request state
    4. Makes it available for downstream processing

    This enables multi-tenancy and data isolation across the system.

    Attributes:
        header_name: The HTTP header name to use for organization IDs
        required: Whether organization ID is required in requests

    Example:
        The middleware is automatically applied to all requests.
        Access the organization ID in your endpoints:
        >>> @app.get("/api/test")
        >>> async def test_endpoint(request: Request):
        ...     org_id = request.state.organization_id
        ...     return {"organization_id": org_id}
    """

    def __init__(
        self,
        app,
        header_name: str = ORGANIZATION_ID_HEADER,
        required: bool = False,
    ):
        """
        Initialize the organization context middleware.

        Args:
            app: The FastAPI application instance
            header_name: The HTTP header name for organization ID (default: X-Organization-ID)
            required: Whether organization ID must be present in requests (default: False)

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = OrganizationContextMiddleware(app, required=True)
            >>> app.add_middleware(OrganizationContextMiddleware)
        """
        super().__init__(app)
        self.header_name = header_name
        self.required = required
        logger.info(
            f"Organization context middleware initialized with header: {header_name}, "
            f"required: {required}"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and manage organization context.

        This method:
        1. Extracts organization ID from headers
        2. Validates the organization ID format
        3. Stores it in request state
        4. Processes the request
        5. Logs organization context for debugging

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler

        Example:
            The middleware automatically processes all requests.
            No manual intervention required.
        """
        # Extract organization ID from request headers
        organization_id = request.headers.get(self.header_name)

        # Validate and store organization ID
        if organization_id:
            # Trim whitespace
            organization_id = organization_id.strip()

            # Basic validation - ensure it's not empty after trimming
            if not organization_id:
                organization_id = None
                logger.warning(
                    f"Empty {self.header_name} header provided in request "
                    f"{request.method} {request.url.path}"
                )
            else:
                logger.debug(
                    f"Request {request.method} {request.url.path} "
                    f"[organization_id={organization_id}]"
                )
        elif self.required:
            # Organization ID is required but not provided
            logger.warning(
                f"Missing required {self.header_name} header in request "
                f"{request.method} {request.url.path}"
            )

        # Store organization ID in request state for easy access in endpoints
        request.state.organization_id = organization_id

        try:
            # Process request
            response = await call_next(request)

            logger.debug(
                f"Response {request.method} {request.url.path} "
                f"[status={response.status_code}, organization_id={organization_id}]"
            )

            return response

        except Exception as e:
            # Log error with organization context
            logger.error(
                f"Request error: {request.method} {request.url.path} "
                f"[organization_id={organization_id}] - {e}",
                exc_info=True,
            )
            raise


def get_organization_context(request: Request) -> Optional[str]:
    """
    Helper function to get organization ID from request.

    This is a convenience function to retrieve the organization ID
    from the request state. Returns None if not present.

    Args:
        request: The FastAPI request object

    Returns:
        The organization ID for this request, or None if not present

    Example:
        >>> from fastapi import Request
        >>> from middleware.organization_context import get_organization_context
        >>> @app.get("/api/test")
        >>> async def test(request: Request):
        ...     org_id = get_organization_context(request)
        ...     return {"organization_id": org_id}
    """
    # Try to get from request state
    if hasattr(request.state, "organization_id"):
        return request.state.organization_id

    # Not found in request state
    return None


def require_organization_context(request: Request) -> str:
    """
    Helper function to get organization ID from request, raising an error if not present.

    This is a convenience function to retrieve the organization ID
    from the request state. Raises ValueError if not present.

    Args:
        request: The FastAPI request object

    Returns:
        The organization ID for this request

    Raises:
        ValueError: If organization ID is not present in the request

    Example:
        >>> from fastapi import Request
        >>> from middleware.organization_context import require_organization_context
        >>> @app.get("/api/test")
        >>> async def test(request: Request):
        ...     org_id = require_organization_context(request)
        ...     return {"organization_id": org_id}
    """
    org_id = get_organization_context(request)
    if org_id is None:
        raise ValueError("Organization context is required but not provided")
    return org_id
