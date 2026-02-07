"""
API Docs Authentication Middleware Module

This module provides HTTP Basic authentication for API documentation endpoints.
It protects /docs, /redoc, and /openapi.json endpoints from unauthorized access.

Features:
- HTTP Basic authentication for API docs
- Configurable username and password
- Secure password comparison using secrets.compare_digest
- Can be enabled/disabled via configuration

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.docs_auth import DocsAuthMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(DocsAuthMiddleware)
"""
import base64
import binascii
import logging
import secrets
from typing import Callable, Optional

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class DocsAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add HTTP Basic authentication to API documentation endpoints.

    This middleware protects the following endpoints:
    - /docs (Swagger UI)
    - /redoc (ReDoc)
    - /openapi.json (OpenAPI schema)

    Authentication is enforced using HTTP Basic Auth with credentials
    from application settings. This prevents unauthorized access to
    API documentation in production environments.

    Attributes:
        docs_username: Username for API docs authentication
        docs_password: Password for API docs authentication
        docs_enabled: Whether API docs should be accessible at all

    Example:
        >>> from fastapi import FastAPI
        >>> from config import get_settings
        >>> app = FastAPI()
        >>> settings = get_settings()
        >>> app.add_middleware(
        ...     DocsAuthMiddleware,
        ...     docs_username=settings.security_api_docs_username,
        ...     docs_password=settings.security_api_docs_password,
        ...     docs_enabled=settings.security_api_docs_enabled
        ... )

    Security:
        Password comparison uses secrets.compare_digest() to prevent
        timing attacks. Authentication credentials are validated
        against the configured username and password.
    """

    def __init__(
        self,
        app,
        docs_username: str = "admin",
        docs_password: str = "admin",
        docs_enabled: bool = True,
    ):
        """
        Initialize the docs authentication middleware.

        Args:
            app: The FastAPI application instance
            docs_username: Username for API docs authentication (default: "admin")
            docs_password: Password for API docs authentication (default: "admin")
            docs_enabled: Whether API docs should be accessible (default: True)

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> app.add_middleware(
            ...     DocsAuthMiddleware,
            ...     docs_username="docs_user",
            ...     docs_password="secure_password"
            ... )
        """
        super().__init__(app)

        self.docs_username = docs_username
        self.docs_password = docs_password
        self.docs_enabled = docs_enabled

        # Paths that require authentication
        self.protected_paths = ["/docs", "/redoc", "/openapi.json"]

        logger.info(
            f"Docs auth middleware initialized "
            f"(enabled={docs_enabled}, paths={self.protected_paths})"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and authenticate docs endpoints.

        This method:
        1. Checks if the request is for a docs endpoint
        2. If so, validates HTTP Basic authentication
        3. Returns 401 if authentication fails or is missing
        4. Otherwise, processes the request normally

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler, or 401 if auth fails

        Raises:
            HTTPException: If authentication is required but fails

        Example:
            The middleware automatically processes all requests to docs endpoints.
            >>> # Request to /docs with valid auth:
            >>> # Authorization: Basic YWRtaW46YWRtaW4=
            >>> # Returns: 200 OK with Swagger UI HTML
            >>>
            >>> # Request to /docs without auth:
            >>> # Returns: 401 Unauthorized with WWW-Authenticate header
        """
        # Check if this is a docs endpoint
        if request.url.path in self.protected_paths:
            # Check if docs are enabled
            if not self.docs_enabled:
                logger.warning(
                    f"Docs access attempted but disabled: {request.url.path}"
                )
                return Response(
                    content='{"detail": "API documentation is disabled"}',
                    status_code=status.HTTP_404_NOT_FOUND,
                    media_type="application/json",
                )

            # Validate authentication
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Basic "):
                logger.warning(
                    f"Docs access without auth: {request.url.path}"
                )
                return Response(
                    content='{"detail": "Not authenticated"}',
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={
                        "WWW-Authenticate": 'Basic realm="API Documentation"',
                    },
                    media_type="application/json",
                )

            try:
                # Decode Basic Auth header
                auth_decoded = base64.b64decode(
                    auth_header.split(" ")[1]
                ).decode("utf-8")
                username, password = auth_decoded.split(":", 1)

                # Verify credentials using constant-time comparison
                correct_username = secrets.compare_digest(
                    username, self.docs_username
                )
                correct_password = secrets.compare_digest(
                    password, self.docs_password
                )

                if not (correct_username and correct_password):
                    logger.warning(
                        f"Docs access with invalid credentials: {request.url.path}"
                    )
                    return Response(
                        content='{"detail": "Invalid authentication credentials"}',
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        headers={
                            "WWW-Authenticate": 'Basic realm="API Documentation"',
                        },
                        media_type="application/json",
                    )

                logger.debug(
                    f"Docs access granted: {request.url.path} (user={username})"
                )

            except (binascii.Error, ValueError) as e:
                logger.warning(
                    f"Docs access with malformed auth: {request.url.path} - {e}"
                )
                return Response(
                    content='{"detail": "Invalid authentication header format"}',
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    headers={
                        "WWW-Authenticate": 'Basic realm="API Documentation"',
                    },
                    media_type="application/json",
                )

        # Process request normally for non-docs endpoints or authenticated docs requests
        return await call_next(request)
