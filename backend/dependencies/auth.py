"""
FastAPI dependencies for authentication and authorization.

This module provides dependency injection functions for FastAPI endpoints
to extract the current user from JWT tokens and enforce role-based permissions.
It integrates with the JWT service and authentication service for token
validation and user retrieval.

Dependencies provided:
- get_current_user: Extract and return the authenticated user from JWT token
- require_role: Check if the current user has required role/permissions
- require_permission: Check if the current user has a specific permission
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User, Role
from services.jwt_service import JWTService, get_jwt_service

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for FastAPI
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> User:
    """
    Dependency to extract the current authenticated user from JWT token.

    This function validates the JWT token from the Authorization header,
    retrieves the corresponding user from the database, and returns it.
    It raises an HTTPException if the token is invalid, expired, or the
    user is not found or inactive.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session (injected by FastAPI)
        jwt_service: JWT service instance (injected by FastAPI)

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If authentication fails (401 Unauthorized)
            - Missing or invalid token
            - Expired token
            - User not found
            - User account disabled

    Example:
        @router.get("/profile")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email, "name": current_user.name}
    """
    # Check if credentials are provided
    if credentials is None:
        logger.warning("Authentication attempt without credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Verify and decode the JWT token
        payload = jwt_service.verify_token(token, token_type="access")

        # Extract user ID from token
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing subject claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"User not found for token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Authentication attempt for inactive user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        logger.debug(f"User authenticated successfully: {user.id}")
        return user

    except JWTError as e:
        logger.warning(f"JWT token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        logger.warning(f"Invalid UUID in token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> Optional[User]:
    """
    Optional version of get_current_user that returns None instead of raising.

    This dependency attempts to extract the current user from the JWT token
    but returns None if authentication fails instead of raising an exception.
    Useful for endpoints that have different behavior for authenticated vs
    anonymous users.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session (injected by FastAPI)
        jwt_service: JWT service instance (injected by FastAPI)

    Returns:
        User or None: The authenticated user object, or None if not authenticated

    Example:
        @router.get("/public-data")
        async def get_public_data(
            current_user: Optional[User] = Depends(get_current_user_optional)
        ):
            if current_user:
                return {"data": "customized", "user": current_user.email}
            return {"data": "generic"}
    """
    # Check if credentials are provided
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        # Verify and decode the JWT token
        payload = jwt_service.verify_token(token, token_type="access")

        # Extract user ID from token
        user_id = payload.get("sub")
        if user_id is None:
            return None

        # Get user from database
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        logger.debug(f"Optional authentication successful: {user.id}")
        return user

    except (JWTError, ValueError) as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None


async def require_role(
    *role_names: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to require specific role(s) for endpoint access.

    This function checks if the current authenticated user has one of the
    required roles. If the user's role is not in the allowed list, it raises
    an HTTPException with 403 Forbidden status.

    Args:
        *role_names: One or more role names that are allowed to access the endpoint
        current_user: The authenticated user (injected by get_current_user)
        db: Database session (injected by FastAPI)

    Returns:
        User: The authenticated user (if role check passes)

    Raises:
        HTTPException: If user doesn't have required role (403 Forbidden)

    Example:
        @router.post("/admin/users")
        async def create_user(
            user: User = Depends(require_role("Admin"))
        ):
            # Only users with "Admin" role can access this endpoint
            return {"message": "User created"}
    """
    # Get user's role from database
    result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = result.scalar_one_or_none()

    if role is None:
        logger.error(f"User {current_user.id} has invalid role_id: {current_user.role_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        )

    # Check if user's role is in the allowed roles
    if role.name not in role_names:
        logger.warning(
            f"Access denied: user {current_user.id} with role '{role.name}' "
            f"attempted to access endpoint requiring roles: {role_names}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: one of {role_names}",
        )

    logger.debug(
        f"Role check passed: user {current_user.id} with role '{role.name}'"
    )
    return current_user


async def require_role_level(
    max_level: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to require a minimum role level (hierarchical access control).

    This function checks if the current user's role level is at or below
    the specified max_level. Lower level numbers indicate higher privilege:
    - Level 1: Admin (highest privilege)
    - Level 2: Recruiter
    - Level 3: Viewer (lowest privilege)

    Args:
        max_level: Maximum role level allowed (1 = highest privilege, 3 = lowest)
        current_user: The authenticated user (injected by get_current_user)
        db: Database session (injected by FastAPI)

    Returns:
        User: The authenticated user (if role level check passes)

    Raises:
        HTTPException: If user's role level is too high (403 Forbidden)

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user: User = Depends(require_role_level(max_level=1))  # Admin only
        ):
            # Only users with role level 1 (Admin) can access
            return {"message": "User deleted"}
    """
    # Get user's role from database
    result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = result.scalar_one_or_none()

    if role is None:
        logger.error(f"User {current_user.id} has invalid role_id: {current_user.role_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        )

    # Check if user's role level is at or below max_level
    if role.level > max_level:
        logger.warning(
            f"Access denied: user {current_user.id} with role level {role.level} "
            f"attempted to access endpoint requiring max level {max_level}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role level: {max_level} or higher",
        )

    logger.debug(
        f"Role level check passed: user {current_user.id} with role level {role.level}"
    )
    return current_user


async def require_permission(
    permission: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to require a specific permission for endpoint access.

    This function checks if the current user's role has a specific permission.
    Permissions are stored in the role's permissions JSONB field and checked
    using the Role.has_permission() method.

    Permission format: "resource.action" (e.g., "users.create", "candidates.read")

    Args:
        permission: Permission string to check (e.g., "users.create")
        current_user: The authenticated user (injected by get_current_user)
        db: Database session (injected by FastAPI)

    Returns:
        User: The authenticated user (if permission check passes)

    Raises:
        HTTPException: If user lacks required permission (403 Forbidden)

    Example:
        @router.post("/candidates")
        async def create_candidate(
            user: User = Depends(require_permission("candidates.create"))
        ):
            # Only users with "candidates.create" permission can access
            return {"message": "Candidate created"}
    """
    # Get user's role from database
    result = await db.execute(
        select(Role).where(Role.id == current_user.role_id)
    )
    role = result.scalar_one_or_none()

    if role is None:
        logger.error(f"User {current_user.id} has invalid role_id: {current_user.role_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        )

    # Check if role has the required permission
    if not role.has_permission(permission):
        logger.warning(
            f"Access denied: user {current_user.id} with role '{role.name}' "
            f"lacks permission '{permission}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required permission: {permission}",
        )

    logger.debug(
        f"Permission check passed: user {current_user.id} has permission '{permission}'"
    )
    return current_user


async def require_all_permissions(
    *permissions: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to require ALL specified permissions for endpoint access.

    This function checks if the current user's role has ALL of the specified
    permissions. All permissions must be present for access to be granted.

    Args:
        *permissions: Permission strings that must all be present
        current_user: The authenticated user (injected by get_current_user)
        db: Database session (injected by FastAPI)

    Returns:
        User: The authenticated user (if all permissions are present)

    Raises:
        HTTPException: If user lacks any required permission (403 Forbidden)

    Example:
        @router.post("/analytics/export")
        async def export_analytics(
            user: User = Depends(require_all_permissions("analytics.read", "analytics.export"))
        ):
            # User must have both analytics.read AND analytics.export
            return {"data": "exported"}
    """
    # Get user's role from database
    result = await db.execute(
        select(Role).where(Role.id == current_user.role_id)
    )
    role = result.scalar_one_or_none()

    if role is None:
        logger.error(f"User {current_user.id} has invalid role_id: {current_user.role_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        )

    # Check if role has all required permissions
    missing_permissions = [
        perm for perm in permissions if not role.has_permission(perm)
    ]

    if missing_permissions:
        logger.warning(
            f"Access denied: user {current_user.id} with role '{role.name}' "
            f"lacks permissions: {missing_permissions}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Missing permissions: {', '.join(missing_permissions)}",
        )

    logger.debug(
        f"All permissions check passed: user {current_user.id} has permissions: {permissions}"
    )
    return current_user


async def require_any_permission(
    *permissions: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to require ANY of the specified permissions for endpoint access.

    This function checks if the current user's role has AT LEAST ONE of the
    specified permissions. Access is granted if any permission is present.

    Args:
        *permissions: Permission strings (at least one must be present)
        current_user: The authenticated user (injected by get_current_user)
        db: Database session (injected by FastAPI)

    Returns:
        User: The authenticated user (if any permission is present)

    Raises:
        HTTPException: If user lacks all specified permissions (403 Forbidden)

    Example:
        @router.get("/data")
        async def get_data(
            user: User = Depends(require_any_permission("data.read", "data.admin"))
        ):
            # User needs either data.read OR data.admin
            return {"data": "retrieved"}
    """
    # Get user's role from database
    result = await db.execute(
        select(Role).where(Role.id == current_user.role_id)
    )
    role = result.scalar_one_or_none()

    if role is None:
        logger.error(f"User {current_user.id} has invalid role_id: {current_user.role_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        )

    # Check if role has at least one of the required permissions
    has_permission = any(role.has_permission(perm) for perm in permissions)

    if not has_permission:
        logger.warning(
            f"Access denied: user {current_user.id} with role '{role.name}' "
            f"lacks all permissions: {permissions}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required: one of permissions {', '.join(permissions)}",
        )

    logger.debug(
        f"Any permission check passed: user {current_user.id} has at least one of: {permissions}"
    )
    return current_user
