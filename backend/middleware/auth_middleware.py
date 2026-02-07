"""
Authentication Middleware Module

This module provides middleware for validating JWT tokens and checking session validity.
It enforces authentication requirements for protected API endpoints.

Features:
- JWT token validation using Authorization header (Bearer scheme)
- Session validation against active sessions in database
- User context injection into request state for downstream use
- Configurable path exclusions for public endpoints
- Integration with SecurityConfig for enable/disable
- Automatic logging of authentication failures
- Support for both JWT and session-based authentication
- Security event logging for successful and failed authentication attempts

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.auth_middleware import AuthMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(AuthMiddleware)
"""
import hashlib
import logging
from typing import Callable, List, Optional
from uuid import UUID

from fastapi import Request, Response, status
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import get_settings
from database import async_session_maker
from models.audit_log import AuditActionType
from models.session import Session
from services.session_service import get_session_service
from utils.audit_logger import get_request_context, log_audit_event

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce JWT authentication and session validation for HTTP requests.

    This middleware validates incoming requests by:
    1. Checking if request path is excluded from authentication
    2. Extracting JWT token from Authorization header (Bearer scheme)
    3. Validating JWT signature and claims (exp, iat, nbf, issuer, audience)
    4. Checking session validity in database (active, not expired)
    5. Injecting user_id and session info into request state
    6. Returning 401 Unauthorized for missing/invalid tokens
    7. Returning 403 Forbidden for invalid/revoked sessions

    JWT token structure:
    - Header: {"alg": "HS256", "typ": "JWT"}
    - Payload: {"sub": user_id, "iat": issued_at, "exp": expires_at, "iss": issuer, "aud": audience}
    - Signature: HMAC-SHA256(secret_key, header + "." + payload)

    Session validation:
    - Queries sessions table by token hash (SHA-256 of JWT)
    - Checks is_active flag and expires_at timestamp
    - Updates last_activity_at on successful validation

    Attributes:
        exclude_paths: List of path patterns to exclude from authentication (e.g., health endpoints)
        jwt_secret_key: Secret key for JWT validation (from settings)
        jwt_algorithm: Algorithm for JWT validation (default: HS256)
        jwt_issuer: Expected JWT issuer claim (from settings)
        jwt_audience: Expected JWT audience claim (from settings)

    Example:
        The middleware is automatically applied to all requests.
        Public endpoints (health, docs) are excluded by default.
        >>> @app.get("/api/protected")
        >>> async def protected_endpoint(request: Request):
        ...     user_id = request.state.user_id
        ...     return {"message": f"Hello, user {user_id}"}
    """

    # Paths excluded from authentication
    EXCLUDE_PATHS = [
        "/health",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/sso/login",
        "/api/sso/acs",
        "/api/sso/metadata",
    ]

    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        """
        Initialize the authentication middleware.

        Args:
            app: The FastAPI application instance
            exclude_paths: List of path patterns to exclude from authentication

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = AuthMiddleware(app, exclude_paths=["/health"])
            >>> app.add_middleware(AuthMiddleware)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or self.EXCLUDE_PATHS

        settings = get_settings()
        self.jwt_secret_key = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
        self.jwt_issuer = settings.jwt_issuer
        self.jwt_audience = settings.jwt_audience

        logger.info(
            f"Auth middleware initialized (algorithm={self.jwt_algorithm}, "
            f"issuer={self.jwt_issuer}, "
            f"exclude_paths={len(self.exclude_paths)})"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and validate JWT token and session.

        This method:
        1. Checks if request path is excluded from authentication
        2. Extracts JWT token from Authorization header
        3. Validates JWT signature and claims
        4. Validates session in database (active, not expired)
        5. Injects user context into request state
        6. Returns 401 for missing/invalid tokens
        7. Returns 403 for invalid/revoked sessions
        8. Processes authenticated requests normally

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler or error response if authentication fails

        Example:
            The middleware automatically processes all requests.
            No manual intervention required.
        """
        # Check if path is excluded from authentication
        if self._is_excluded_path(request.url.path):
            logger.debug(
                f"Path {request.url.path} is excluded from authentication"
            )
            return await call_next(request)

        # Extract JWT token from Authorization header
        token = self._extract_token(request)

        if not token:
            logger.warning(
                f"No authentication token provided for {request.method} {request.url.path}"
            )
            # Log failed authentication
            await self._log_auth_event(
                request,
                AuditActionType.LOGIN_FAILED,
                error_detail="missing_token",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication required",
                    "detail": "Authorization header with Bearer token is required",
                    "type": "missing_token",
                },
            )

        # Validate JWT token
        payload, error_response = await self._validate_jwt_token(token, request)

        if error_response:
            return error_response

        # Extract user_id from JWT payload
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT token missing 'sub' claim")
            # Log failed authentication
            await self._log_auth_event(
                request,
                AuditActionType.LOGIN_FAILED,
                error_detail="missing_user_claim",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Invalid token",
                    "detail": "Token missing user identifier",
                    "type": "invalid_token",
                },
            )

        # Validate session in database
        session, error_response = await self._validate_session(token, user_id, request)

        if error_response:
            return error_response

        # Inject user context into request state for downstream use
        request.state.user_id = user_id
        request.state.session_id = str(session.id) if session else None
        request.state.token = token

        logger.debug(
            f"Authenticated request: user={user_id}, "
            f"session={session.id if session else None}, "
            f"path={request.url.path}"
        )

        # Log successful authentication event
        await self._log_auth_event(
            request,
            AuditActionType.LOGIN_SUCCESS,
            user_id=user_id,
            session_id=str(session.id) if session else None,
        )

        # Process request normally
        return await call_next(request)

    def _is_excluded_path(self, path: str) -> bool:
        """
        Check if path should be excluded from authentication.

        Args:
            path: Request path

        Returns:
            True if path is excluded, False otherwise

        Example:
            >>> middleware._is_excluded_path("/health")
            True
            >>> middleware._is_excluded_path("/api/resumes")
            False
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Expects format: "Bearer <token>"

        Args:
            request: The FastAPI request object

        Returns:
            JWT token string or None if not found/invalid format

        Example:
            >>> token = middleware._extract_token(request)
            >>> print(f"Token: {token[:20]}...")
        """
        authorization = request.headers.get("Authorization")

        if not authorization:
            return None

        # Check if it's a Bearer token
        if not authorization.startswith("Bearer "):
            logger.warning("Authorization header not using Bearer scheme")
            return None

        # Extract token
        token = authorization[7:].strip()  # Remove "Bearer " prefix

        if not token:
            logger.warning("Empty Bearer token in Authorization header")
            return None

        return token

    async def _validate_jwt_token(
        self, token: str, request: Request
    ) -> tuple[Optional[dict], Optional[JSONResponse]]:
        """
        Validate JWT token signature and claims.

        Args:
            token: JWT token string
            request: The FastAPI request object for logging

        Returns:
            Tuple of (payload, error_response)
            - payload: Decoded JWT payload if valid, None otherwise
            - error_response: JSONResponse with error details if invalid, None otherwise

        Example:
            >>> payload, error = await middleware._validate_jwt_token(token, request)
            >>> if error:
            ...     return error
            >>> user_id = payload["sub"]
        """
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret_key,
                algorithms=[self.jwt_algorithm],
                issuer=self.jwt_issuer,
                audience=self.jwt_audience,
            )

            logger.debug("JWT token validated successfully")
            return payload, None

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            # Log failed authentication
            await self._log_auth_event(
                request,
                AuditActionType.LOGIN_FAILED,
                error_detail="token_expired",
            )
            return None, JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Token expired",
                    "detail": "Authentication token has expired. Please log in again.",
                    "type": "token_expired",
                },
            )

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            # Log failed authentication
            await self._log_auth_event(
                request,
                AuditActionType.LOGIN_FAILED,
                error_detail=f"invalid_token: {str(e)}",
            )
            return None, JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Invalid token",
                    "detail": "Authentication token is invalid",
                    "type": "invalid_token",
                },
            )

        except JWTError as e:
            logger.error(f"JWT validation error: {e}", exc_info=True)
            # Log failed authentication
            await self._log_auth_event(
                request,
                AuditActionType.LOGIN_FAILED,
                error_detail=f"validation_error: {str(e)}",
            )
            return None, JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Token validation failed",
                    "detail": "Failed to validate authentication token",
                    "type": "validation_error",
                },
            )

    async def _validate_session(
        self, token: str, user_id: str, request: Request
    ) -> tuple[Optional[Session], Optional[JSONResponse]]:
        """
        Validate session in database.

        Checks if session exists, is active, and not expired.
        Also updates last_activity_at timestamp.

        Args:
            token: JWT token string
            user_id: User ID from JWT payload
            request: The FastAPI request object

        Returns:
            Tuple of (session, error_response)
            - session: Session object if valid, None otherwise
            - error_response: JSONResponse with error details if invalid, None otherwise

        Example:
            >>> session, error = await middleware._validate_session(token, user_id, request)
            >>> if error:
            ...     return error
            >>> print(f"Session {session.id} is valid")
        """
        try:
            # Get session service
            session_service = get_session_service()

            # Validate session (token is checked against database)
            is_valid = await session_service.validate_session(token)

            if not is_valid:
                logger.warning(
                    f"Session validation failed for user {user_id}, "
                    f"path={request.url.path}, ip={request.client.host if request.client else 'unknown'}"
                )
                # Log failed authentication
                await self._log_auth_event(
                    request,
                    AuditActionType.LOGIN_FAILED,
                    user_id=user_id,
                    error_detail="session_invalid_or_expired",
                )
                return None, JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Session invalid",
                        "detail": "Session is invalid or has expired. Please log in again.",
                        "type": "session_invalid",
                    },
                )

            # Get session details
            session = await session_service.get_session(token)

            if session:
                logger.debug(f"Session {session.id} validated for user {user_id}")
            else:
                logger.debug(f"Session validated (no details returned) for user {user_id}")

            return session, None

        except Exception as e:
            # Log error but don't fail request (fail open for session validation issues)
            logger.error(
                f"Error validating session for user {user_id}: {e}",
                exc_info=True,
            )
            # Return None for session but no error response (allow request to proceed)
            return None, None

    async def _log_auth_event(
        self,
        request: Request,
        action_type: AuditActionType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        """
        Log an authentication event to the audit log.

        This method creates an audit log entry for authentication-related events,
        including successful logins, failed logins, and session validation failures.

        Args:
            request: The FastAPI request object
            action_type: Type of authentication event (LOGIN_SUCCESS, LOGIN_FAILED, etc.)
            user_id: Optional user ID (available only on successful auth)
            session_id: Optional session ID (available only on successful auth)
            error_detail: Optional error details for failed authentication

        Example:
            >>> await middleware._log_auth_event(
            ...     request,
            ...     AuditActionType.LOGIN_SUCCESS,
            ...     user_id="user-123",
            ...     session_id="session-456"
            ... )
        """
        try:
            # Create a database session for audit logging
            async with async_session_maker() as db:
                # Extract IP address and user agent from request
                ip_address, user_agent = get_request_context(request)

                # Convert string IDs to UUID if provided
                user_id_uuid = UUID(user_id) if user_id else None

                # Create action_data with relevant information
                action_data = {
                    "path": request.url.path,
                    "method": request.method,
                }
                if session_id:
                    action_data["session_id"] = session_id
                if error_detail:
                    action_data["error_detail"] = error_detail

                # Log the audit event
                await log_audit_event(
                    db=db,
                    action_type=action_type,
                    entity_type="session",
                    entity_id=UUID(session_id) if session_id else None,
                    user_id=user_id_uuid,
                    organization_id=None,  # Org ID not available in middleware
                    ip_address=ip_address,
                    user_agent=user_agent,
                    action_data=action_data,
                )

                logger.debug(
                    f"Logged auth event: {action_type} for user={user_id}, "
                    f"session={session_id}, ip={ip_address}"
                )

        except Exception as e:
            # Don't fail authentication if audit logging fails
            logger.error(
                f"Failed to log authentication event: {e}",
                exc_info=True,
            )
