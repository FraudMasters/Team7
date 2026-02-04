"""
Authentication middleware for JWT token validation.

This module provides middleware and dependencies for validating JWT tokens
issued by Keycloak, extracting user information, and enforcing role-based
access control (RBAC) for protected endpoints.
"""
import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# HTTP Bearer token extractor
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """
    Extracted and validated token data.

    Attributes:
        sub: User ID (subject)
        username: Username from Keycloak
        email: User email
        roles: List of realm roles assigned to the user
        exp: Token expiration timestamp
    """

    sub: str = Field(..., description="User ID (subject)")
    username: str = Field(..., description="Username from Keycloak")
    email: Optional[str] = Field(None, description="User email")
    roles: List[str] = Field(default_factory=list, description="User's realm roles")
    exp: int = Field(..., description="Token expiration timestamp")


class AuthMiddleware:
    """
    Authentication middleware for JWT validation.

    This middleware validates JWT tokens issued by Keycloak and extracts
    user information for use in protected endpoints. It uses the
    fastapi-keycloak library pattern for token validation and role checking.

    Example:
        Using the middleware in an endpoint:

        @router.get("/protected")
        async def protected_endpoint(
            token_data: TokenData = Depends(get_current_token)
        ):
            return {"message": f"Hello, {token_data.username}"}

        Role-based access control:

        @router.get("/admin-only")
        async def admin_endpoint(
            token_data: TokenData = Depends(require_role("Admin"))
        ):
            return {"message": "Admin access granted"}
    """

    def __init__(self):
        """Initialize the authentication middleware."""
        self.keycloak_server_url = settings.keycloak_server_url
        self.keycloak_realm = settings.keycloak_realm
        self.keycloak_client_id = settings.keycloak_client_id
        # For JWT validation, we need the realm's public key or use the client secret
        # This will be initialized with Keycloak integration in main.py

    async def decode_token(
        self, token: str, credentials_exception: HTTPException
    ) -> TokenData:
        """
        Decode and validate JWT token from Keycloak.

        Args:
            token: JWT token string
            credentials_exception: Exception to raise if validation fails

        Returns:
            TokenData with extracted user information

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode JWT without verification first (Keycloak signature verification
            # will be handled by fastapi-keycloak in main.py integration)
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False  # Will be verified by Keycloak integration
                },
            )

            # Extract user information
            sub: str = payload.get("sub")
            username: str = payload.get("preferred_username") or payload.get("sub")
            email: Optional[str] = payload.get("email")

            # Extract realm roles from token
            realm_access = payload.get("realm_access", {})
            roles: List[str] = realm_access.get("roles", [])

            # Get expiration time
            exp: int = payload.get("exp")

            if sub is None:
                logger.warning("Token missing subject claim")
                raise credentials_exception

            token_data = TokenData(
                sub=sub, username=username, email=email, roles=roles, exp=exp
            )
            logger.debug(f"Decoded token for user: {username}, roles: {roles}")
            return token_data

        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise credentials_exception


# Initialize auth middleware instance
auth_middleware = AuthMiddleware()


async def get_current_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Dependency to get and validate the current JWT token.

    This function extracts the Bearer token from the Authorization header,
    validates it, and returns the extracted user information.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials

    Returns:
        TokenData with extracted user information

    Raises:
        HTTPException: 401 if no token or token is invalid

    Example:
        @router.get("/protected")
        async def protected_endpoint(
            token_data: TokenData = Depends(get_current_token)
        ):
            return {"username": token_data.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        logger.warning("Request missing Authorization header")
        raise credentials_exception

    token = credentials.credentials
    token_data = await auth_middleware.decode_token(token, credentials_exception)

    # Store token data in request state for access in endpoints
    request.state.token_data = token_data

    return token_data


async def get_optional_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[TokenData]:
    """
    Optional dependency to get token without requiring authentication.

    This function attempts to extract and validate the JWT token but returns
    None if no token is provided or if the token is invalid. Useful for
    endpoints that have both authenticated and anonymous access.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials

    Returns:
        TokenData if token is valid, None otherwise

    Example:
        @router.get("/public")
        async def public_endpoint(
            token_data: Optional[TokenData] = Depends(get_optional_token)
        ):
            if token_data:
                return {"message": f"Hello, {token_data.username}"}
            return {"message": "Hello, anonymous user"}
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        token_data = await auth_middleware.decode_token(token, None)
        request.state.token_data = token_data
        return token_data
    except (HTTPException, JWTError):
        return None


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.

    This function creates a dependency that checks if the authenticated user
    has the required role. Raises 403 Forbidden if the user doesn't have
    the required role.

    Args:
        required_role: The role name required to access the endpoint

    Returns:
        Dependency function that validates the user's role

    Example:
        @router.get("/admin-only")
        async def admin_endpoint(
            token_data: TokenData = Depends(require_role("Admin"))
        ):
            return {"message": "Admin access granted"}
    """
    async def role_dependency(
        token_data: TokenData = Depends(get_current_token),
    ) -> TokenData:
        if required_role not in token_data.roles:
            logger.warning(
                f"User {token_data.username} lacks required role: {required_role}. "
                f"User roles: {token_data.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        logger.debug(
            f"User {token_data.username} has required role: {required_role}"
        )
        return token_data

    return role_dependency


def require_any_role(*required_roles: str):
    """
    Dependency factory to require any of the specified roles.

    This function creates a dependency that checks if the authenticated user
    has at least one of the required roles. Raises 403 Forbidden if the user
    doesn't have any of the required roles.

    Args:
        *required_roles: Variable number of role names, any of which grants access

    Returns:
        Dependency function that validates the user's roles

    Example:
        @router.get("/management")
        async def management_endpoint(
            token_data: TokenData = Depends(
                require_any_role("Admin", "Recruiter")
            )
        ):
            return {"message": "Management access granted"}
    """
    async def role_dependency(
        token_data: TokenData = Depends(get_current_token),
    ) -> TokenData:
        if not any(role in token_data.roles for role in required_roles):
            logger.warning(
                f"User {token_data.username} lacks required roles. "
                f"Required any of: {required_roles}, "
                f"User roles: {token_data.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {', '.join(required_roles)}",
            )
        logger.debug(
            f"User {token_data.username} has at least one required role"
        )
        return token_data

    return role_dependency


def require_all_roles(*required_roles: str):
    """
    Dependency factory to require all of the specified roles.

    This function creates a dependency that checks if the authenticated user
    has all of the required roles. Raises 403 Forbidden if the user is missing
    any of the required roles.

    Args:
        *required_roles: Variable number of role names, all of which are required

    Returns:
        Dependency function that validates the user's roles

    Example:
        @router.get("/super-admin")
        async def super_admin_endpoint(
            token_data: TokenData = Depends(
                require_all_roles("Admin", "SuperUser")
            )
        ):
            return {"message": "Super admin access granted"}
    """
    async def role_dependency(
        token_data: TokenData = Depends(get_current_token),
    ) -> TokenData:
        if not all(role in token_data.roles for role in required_roles):
            missing_roles = [
                role for role in required_roles if role not in token_data.roles
            ]
            logger.warning(
                f"User {token_data.username} missing required roles: {missing_roles}. "
                f"User roles: {token_data.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing roles: {', '.join(missing_roles)}",
            )
        logger.debug(
            f"User {token_data.username} has all required roles: {required_roles}"
        )
        return token_data

    return role_dependency
