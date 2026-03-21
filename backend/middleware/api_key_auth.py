"""
API Key Authentication Middleware Module

This module provides middleware for validating API key authentication via X-API-Key header.
It enforces API key requirements for developer API access and tracks usage.

Features:
- API key validation using X-API-Key header
- Key hash lookup against database
- Scope-based authorization
- Automatic last_used_at timestamp updates
- User context injection into request state for downstream use
- Configurable path exclusions for public endpoints
- Integration with SecurityConfig for enable/disable
- Automatic logging of authentication failures
- Security event logging for successful and failed authentication attempts

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.api_key_auth import APIKeyAuthMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(APIKeyAuthMiddleware)
"""
import hashlib
import logging
from datetime import datetime
from typing import Callable, List, Optional
from uuid import UUID

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select

from config import get_settings
from database import async_session_maker
from models.api_key import APIKey
from models.audit_log import AuditActionType
from utils.audit_logger import get_request_context, log_audit_event

logger = logging.getLogger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API key authentication for HTTP requests.

    This middleware validates incoming requests by:
    1. Checking if request path is excluded from API key authentication
    2. Extracting API key from X-API-Key header
    3. Hashing the API key and looking up in database
    4. Validating key is active and not expired
    5. Updating last_used_at timestamp
    6. Injecting api_key info into request state
    7. Returning 401 Unauthorized for missing/invalid keys
    8. Returning 403 Forbidden for inactive/expired keys

    API key structure:
    - Header: X-API-Key: <64-character-hex-key>
    - Database: Stores SHA-256 hash of the key
    - Scopes: JSON array of permissions (e.g., "read:candidates", "write:vacancies")

    Key validation:
    - Queries api_keys table by key_hash (SHA-256 of API key)
    - Checks is_active flag and expires_at timestamp
    - Updates last_used_at on successful validation

    Attributes:
        exclude_paths: List of path patterns to exclude from API key authentication
        enabled: Whether API key authentication is enabled (from settings)

    Example:
        The middleware is automatically applied to all requests when registered.
        Public endpoints (health, docs) are excluded by default.
        >>> @app.get("/api/candidates")
        >>> async def get_candidates(request: Request):
        ...     api_key = request.state.api_key
        ...     return {"message": f"Authenticated with key {api_key.key_prefix}"}
    """

    # Paths excluded from API key authentication
    EXCLUDE_PATHS = [
        "/health",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/sso/login",
        "/api/sso/acs",
        "/api/sso/metadata",
        "/api/auth/",  # Regular auth endpoints
    ]

    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        """
        Initialize the API key authentication middleware.

        Args:
            app: The FastAPI application instance
            exclude_paths: List of path patterns to exclude from API key authentication

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = APIKeyAuthMiddleware(app, exclude_paths=["/health", "/api/public"])
            >>> app.add_middleware(APIKeyAuthMiddleware)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or self.EXCLUDE_PATHS

        settings = get_settings()
        # API key auth is typically opt-in for specific routes, so default to disabled
        # for middleware-wide enforcement. Individual routes can require it via dependencies.
        self.enabled = getattr(settings, 'api_key_auth_enabled', False)

        logger.info(
            f"API key auth middleware initialized (enabled={self.enabled}, "
            f"exclude_paths={len(self.exclude_paths)})"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and validate API key authentication.

        This method:
        1. Checks if request path is excluded from API key authentication
        2. Extracts API key from X-API-Key header
        3. Validates API key against database (hash lookup)
        4. Validates key is active and not expired
        5. Updates last_used_at timestamp
        6. Injects API key context into request state
        7. Returns 401 for missing/invalid keys
        8. Returns 403 for inactive/expired keys
        9. Processes authenticated requests normally

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler or error response if authentication fails

        Example:
            The middleware automatically processes all requests when enabled.
            No manual intervention required.
        """
        # Check if path is excluded from API key authentication
        if not self.enabled or self._is_excluded_path(request.url.path):
            logger.debug(
                f"Path {request.url.path} is excluded from API key authentication "
                f"(enabled={self.enabled})"
            )
            return await call_next(request)

        # Extract API key from X-API-Key header
        api_key = self._extract_api_key(request)

        if not api_key:
            logger.warning(
                f"No API key provided for {request.method} {request.url.path}"
            )
            # Log failed authentication
            await self._log_auth_event(
                request,
                AuditActionType.LOGIN_FAILED,
                error_detail="missing_api_key",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "API key required",
                    "detail": "X-API-Key header is required for this endpoint",
                    "type": "missing_api_key",
                },
            )

        # Validate API key
        api_key_obj, error_response = await self._validate_api_key(api_key, request)

        if error_response:
            return error_response

        # Inject API key info into request state
        request.state.api_key = api_key_obj
        request.state.api_key_id = str(api_key_obj.id)
        request.state.api_key_scopes = api_key_obj.scopes

        # Log successful authentication
        await self._log_auth_event(
            request,
            AuditActionType.LOGIN_SUCCESS,
            api_key_id=str(api_key_obj.id),
        )

        logger.debug(
            f"API key authenticated: {api_key_obj.key_prefix}*** "
            f"(id={api_key_obj.id}, scopes={len(api_key_obj.scopes)})"
        )

        # Process request
        response = await call_next(request)

        return response

    def _is_excluded_path(self, path: str) -> bool:
        """
        Check if a request path is excluded from API key authentication.

        Args:
            path: The request path to check

        Returns:
            True if path is excluded, False otherwise

        Example:
            >>> middleware = APIKeyAuthMiddleware(app)
            >>> middleware._is_excluded_path("/health")
            True
            >>> middleware._is_excluded_path("/api/candidates")
            False
        """
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from X-API-Key header.

        Args:
            request: Incoming HTTP request

        Returns:
            API key string if found, None otherwise

        Example:
            >>> middleware = APIKeyAuthMiddleware(app)
            >>> # Request with X-API-Key: abc123...
            >>> key = middleware._extract_api_key(request)
            >>> key
            'abc123...'
        """
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Strip whitespace
            api_key = api_key.strip()
            if api_key:
                return api_key
        return None

    def _hash_api_key(self, api_key: str) -> str:
        """
        Hash API key using SHA-256.

        Args:
            api_key: The API key to hash

        Returns:
            SHA-256 hash as hex string

        Example:
            >>> middleware = APIKeyAuthMiddleware(app)
            >>> hashed = middleware._hash_api_key("test_key")
            >>> len(hashed)
            64
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def _validate_api_key(
        self, api_key: str, request: Request
    ) -> tuple[Optional[APIKey], Optional[Response]]:
        """
        Validate API key against database.

        This method:
        1. Hashes the provided API key
        2. Queries database for matching key_hash
        3. Validates key is active and not expired
        4. Updates last_used_at timestamp
        5. Returns error response for invalid keys

        Args:
            api_key: The API key to validate
            request: The incoming request (for logging)

        Returns:
            Tuple of (APIKey object, error Response or None)
            If validation succeeds: (APIKey, None)
            If validation fails: (None, error Response)

        Example:
            >>> api_key_obj, error = await middleware._validate_api_key("abc123...", request)
            >>> if error:
            ...     return error
            >>> # Use api_key_obj
        """
        key_hash = self._hash_api_key(api_key)

        try:
            async with async_session_maker() as session:
                # Query for API key by hash
                result = await session.execute(
                    select(APIKey).where(APIKey.key_hash == key_hash)
                )
                api_key_obj = result.scalar_one_or_none()

                if not api_key_obj:
                    logger.warning(f"Invalid API key provided for {request.url.path}")
                    # Log failed authentication
                    await self._log_auth_event(
                        request,
                        AuditActionType.LOGIN_FAILED,
                        error_detail="invalid_api_key",
                    )
                    return None, JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "Invalid API key",
                            "detail": "The provided API key is not valid",
                            "type": "invalid_api_key",
                        },
                    )

                # Check if key is valid (active and not expired)
                if not api_key_obj.is_valid():
                    logger.warning(
                        f"Inactive or expired API key used: {api_key_obj.key_prefix}*** "
                        f"(active={api_key_obj.is_active}, expires_at={api_key_obj.expires_at})"
                    )
                    # Log failed authentication
                    await self._log_auth_event(
                        request,
                        AuditActionType.LOGIN_FAILED,
                        api_key_id=str(api_key_obj.id),
                        error_detail="inactive_or_expired_api_key",
                    )
                    return None, JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "API key inactive or expired",
                            "detail": "The API key is no longer active or has expired",
                            "type": "inactive_api_key",
                        },
                    )

                # Update last_used_at timestamp
                api_key_obj.last_used_at = datetime.utcnow()
                await session.commit()

                logger.debug(
                    f"API key validated: {api_key_obj.key_prefix}*** "
                    f"(id={api_key_obj.id}, active={api_key_obj.is_active})"
                )

                return api_key_obj, None

        except Exception as e:
            logger.error(f"Error validating API key: {e}", exc_info=True)
            # Log failed authentication
            await self._log_auth_event(
                request,
                AuditActionType.LOGIN_FAILED,
                error_detail="database_error",
            )
            return None, JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Authentication error",
                    "detail": "An error occurred while validating the API key",
                    "type": "auth_error",
                },
            )

    async def _log_auth_event(
        self,
        request: Request,
        action_type: AuditActionType,
        api_key_id: Optional[str] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        """
        Log authentication event to audit log.

        Args:
            request: The HTTP request
            action_type: Type of audit action (LOGIN_SUCCESS, LOGIN_FAILED)
            api_key_id: Optional API key ID for successful auth
            error_detail: Optional error detail for failed auth

        Example:
            >>> await middleware._log_auth_event(
            ...     request,
            ...     AuditActionType.LOGIN_SUCCESS,
            ...     api_key_id="123-456-789"
            ... )
        """
        try:
            context = get_request_context(request)

            # Build metadata
            metadata = {
                "method": request.method,
                "path": str(request.url.path),
                "authentication_method": "api_key",
            }

            if api_key_id:
                metadata["api_key_id"] = api_key_id

            if error_detail:
                metadata["error_detail"] = error_detail

            await log_audit_event(
                action_type=action_type,
                user_id=None,  # No user for API key auth
                request_context=context,
                metadata=metadata,
            )
        except Exception as e:
            # Don't fail the request if audit logging fails
            logger.error(f"Failed to log auth event: {e}", exc_info=True)
