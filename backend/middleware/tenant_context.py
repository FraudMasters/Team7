"""
Tenant Context Middleware Module

This module provides middleware for automatic tenant context management
across HTTP requests in multi-tenant agency mode. It extracts tenant IDs
from request headers and makes them available throughout the request context.

Features:
- Extract tenant ID from request headers (client tenant context)
- Store tenant ID in request state for easy access
- Validate tenant ID format
- Log tenant context for debugging
- Helper functions to retrieve tenant context
- Support for agency-level and client-level data isolation

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.tenant_context import TenantContextMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(TenantContextMiddleware)
"""
import logging
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Header name for tenant ID (client tenant ID)
TENANT_ID_HEADER = "X-Tenant-ID"

# Header name for agency ID
AGENCY_ID_HEADER = "X-Agency-ID"


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage tenant context for HTTP requests in multi-tenant agency mode.

    This middleware automatically handles tenant context for each request:
    1. Checks for tenant ID in request headers (X-Tenant-ID)
    2. Checks for agency ID in request headers (X-Agency-ID)
    3. Validates the tenant/agency ID formats (UUID)
    4. Stores the IDs in the request state
    5. Makes them available for downstream processing and data filtering

    This enables multi-tenant agency support and complete data isolation between
    client tenants while allowing agency-level cross-client access.

    Attributes:
        tenant_header_name: The HTTP header name for tenant IDs
        agency_header_name: The HTTP header name for agency IDs
        require_tenant: Whether tenant ID is required in requests
        require_agency: Whether agency ID is required in requests

    Example:
        The middleware is automatically applied to all requests.
        Access the tenant/agency IDs in your endpoints:
        >>> @app.get("/api/test")
        >>> async def test_endpoint(request: Request):
        ...     tenant_id = request.state.tenant_id
        ...     agency_id = request.state.agency_id
        ...     return {"tenant_id": tenant_id, "agency_id": agency_id}
    """

    def __init__(
        self,
        app,
        tenant_header_name: str = TENANT_ID_HEADER,
        agency_header_name: str = AGENCY_ID_HEADER,
        require_tenant: bool = False,
        require_agency: bool = False,
    ):
        """
        Initialize the tenant context middleware.

        Args:
            app: The FastAPI application instance
            tenant_header_name: The HTTP header name for tenant ID (default: X-Tenant-ID)
            agency_header_name: The HTTP header name for agency ID (default: X-Agency-ID)
            require_tenant: Whether tenant ID must be present in requests (default: False)
            require_agency: Whether agency ID must be present in requests (default: False)

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = TenantContextMiddleware(app, require_tenant=True)
            >>> app.add_middleware(TenantContextMiddleware)
        """
        super().__init__(app)
        self.tenant_header_name = tenant_header_name
        self.agency_header_name = agency_header_name
        self.require_tenant = require_tenant
        self.require_agency = require_agency
        logger.info(
            f"Tenant context middleware initialized - "
            f"tenant_header: {tenant_header_name}, "
            f"agency_header: {agency_header_name}, "
            f"require_tenant: {require_tenant}, "
            f"require_agency: {require_agency}"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and manage tenant context.

        This method:
        1. Extracts tenant ID and agency ID from headers
        2. Validates the IDs format (UUID)
        3. Stores them in request state
        4. Processes the request
        5. Logs tenant/agency context for debugging

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler

        Example:
            The middleware automatically processes all requests.
            No manual intervention required.
        """
        # Extract tenant ID from request headers
        tenant_id_str = request.headers.get(self.tenant_header_name)
        tenant_id = None

        if tenant_id_str:
            # Trim whitespace
            tenant_id_str = tenant_id_str.strip()

            # Validate UUID format
            if tenant_id_str:
                try:
                    tenant_id = UUID(tenant_id_str)
                    logger.debug(
                        f"Request {request.method} {request.url.path} "
                        f"[tenant_id={tenant_id}]"
                    )
                except ValueError:
                    logger.warning(
                        f"Invalid UUID format for {self.tenant_header_name} "
                        f"in request {request.method} {request.url.path}: {tenant_id_str}"
                    )
            else:
                logger.warning(
                    f"Empty {self.tenant_header_name} header provided in request "
                    f"{request.method} {request.url.path}"
                )
        elif self.require_tenant:
            # Tenant ID is required but not provided
            logger.warning(
                f"Missing required {self.tenant_header_name} header in request "
                f"{request.method} {request.url.path}"
            )

        # Extract agency ID from request headers
        agency_id_str = request.headers.get(self.agency_header_name)
        agency_id = None

        if agency_id_str:
            # Trim whitespace
            agency_id_str = agency_id_str.strip()

            # Validate format (agency IDs are strings, not UUIDs)
            if agency_id_str:
                agency_id = agency_id_str
                logger.debug(
                    f"Request {request.method} {request.url.path} "
                    f"[agency_id={agency_id}]"
                )
            else:
                logger.warning(
                    f"Empty {self.agency_header_name} header provided in request "
                    f"{request.method} {request.url.path}"
                )
        elif self.require_agency:
            # Agency ID is required but not provided
            logger.warning(
                f"Missing required {self.agency_header_name} header in request "
                f"{request.method} {request.url.path}"
            )

        # Store tenant ID and agency ID in request state for easy access in endpoints
        request.state.tenant_id = tenant_id
        request.state.agency_id = agency_id

        try:
            # Process request
            response = await call_next(request)

            logger.debug(
                f"Response {request.method} {request.url.path} "
                f"[status={response.status_code}, tenant_id={tenant_id}, "
                f"agency_id={agency_id}]"
            )

            return response

        except Exception as e:
            # Log error with tenant/agency context
            logger.error(
                f"Request error: {request.method} {request.url.path} "
                f"[tenant_id={tenant_id}, agency_id={agency_id}] - {e}",
                exc_info=True,
            )
            raise


def get_tenant_context(request: Request) -> Optional[UUID]:
    """
    Helper function to get tenant ID from request.

    This is a convenience function to retrieve the tenant ID
    from the request state. Returns None if not present.

    Args:
        request: The FastAPI request object

    Returns:
        The tenant ID (client tenant UUID) for this request, or None if not present

    Example:
        >>> from fastapi import Request
        >>> from middleware.tenant_context import get_tenant_context
        >>> @app.get("/api/test")
        >>> async def test(request: Request):
        ...     tenant_id = get_tenant_context(request)
        ...     return {"tenant_id": str(tenant_id) if tenant_id else None}
    """
    # Try to get from request state
    if hasattr(request.state, "tenant_id"):
        return request.state.tenant_id

    # Not found in request state
    return None


def get_agency_context(request: Request) -> Optional[str]:
    """
    Helper function to get agency ID from request.

    This is a convenience function to retrieve the agency ID
    from the request state. Returns None if not present.

    Args:
        request: The FastAPI request object

    Returns:
        The agency ID for this request, or None if not present

    Example:
        >>> from fastapi import Request
        >>> from middleware.tenant_context import get_agency_context
        >>> @app.get("/api/test")
        >>> async def test(request: Request):
        ...     agency_id = get_agency_context(request)
        ...     return {"agency_id": agency_id}
    """
    # Try to get from request state
    if hasattr(request.state, "agency_id"):
        return request.state.agency_id

    # Not found in request state
    return None


def require_tenant_context(request: Request) -> UUID:
    """
    Helper function to get tenant ID from request, raising an error if not present.

    This is a convenience function to retrieve the tenant ID
    from the request state. Raises ValueError if not present.

    Args:
        request: The FastAPI request object

    Returns:
        The tenant ID (client tenant UUID) for this request

    Raises:
        ValueError: If tenant ID is not present in the request

    Example:
        >>> from fastapi import Request
        >>> from middleware.tenant_context import require_tenant_context
        >>> @app.get("/api/test")
        >>> async def test(request: Request):
        ...     tenant_id = require_tenant_context(request)
        ...     return {"tenant_id": str(tenant_id)}
    """
    tenant_id = get_tenant_context(request)
    if tenant_id is None:
        raise ValueError("Tenant context is required but not provided")
    return tenant_id


def require_agency_context(request: Request) -> str:
    """
    Helper function to get agency ID from request, raising an error if not present.

    This is a convenience function to retrieve the agency ID
    from the request state. Raises ValueError if not present.

    Args:
        request: The FastAPI request object

    Returns:
        The agency ID for this request

    Raises:
        ValueError: If agency ID is not present in the request

    Example:
        >>> from fastapi import Request
        >>> from middleware.tenant_context import require_agency_context
        >>> @app.get("/api/test")
        >>> async def test(request: Request):
        ...     agency_id = require_agency_context(request)
        ...     return {"agency_id": agency_id}
    """
    agency_id = get_agency_context(request)
    if agency_id is None:
        raise ValueError("Agency context is required but not provided")
    return agency_id
