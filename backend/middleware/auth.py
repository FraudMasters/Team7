"""
Authentication middleware for FastAPI endpoints.

This module provides dependency injection functions for extracting and validating
authenticated users from JWT tokens. It supports both basic user authentication
and active user verification, as well as role-based access control (RBAC).

Key features:
- Extracts user from JWT access token in Authorization header
- Validates token type and expiration
- Queries user from database
- Verifies user account status (active, verified)
- Provides role-based access control (RBAC) with require_role() and require_admin()

Example usage:
    @router.get("/protected")
    async def protected_endpoint(current_user: User = Depends(get_current_user)):
        return {"message": f"Hello {current_user.email}"}

    @router.get("/admin-only")
    async def admin_endpoint(
        current_user: User = Depends(get_current_active_user)
    ):
        return {"message": f"Welcome admin {current_user.email}"}

    @router.get("/recruiter-only")
    async def recruiter_endpoint(
        current_user: User = Depends(require_role(UserRole.RECRUITER))
    ):
        return {"message": f"Welcome recruiter {current_user.email}"}

    @router.delete("/users/{user_id}")
    async def delete_user(
        user_id: str,
        current_user: User = Depends(require_admin)
    ):
        return {"message": "User deletion authorized"}
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.role import Role, UserRole
from models.user import User
from utils.jwt_handler import decode_token, verify_token_type

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for extracting Authorization header
security = HTTPBearer()


class AuthError(BaseModel):
    """
    Authentication error details.

    Attributes:
        detail: Error message describing what went wrong
    """

    detail: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the current user from JWT access token.

    This dependency function:
    1. Extracts the Bearer token from the Authorization header
    2. Decodes and validates the JWT token
    3. Verifies the token type is "access" (not refresh)
    4. Queries the user from the database
    5. Returns the user object if valid

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session for querying user

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: 401 Unauthorized if:
            - Token is missing or invalid
            - Token is expired
            - Token is wrong type (not access token)
            - User not found in database

    Example:
        @router.get("/profile")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email, "name": current_user.full_name}
    """
    # Extract token from Authorization header
    token: str = credentials.credentials

    # Validate token type and decode
    try:
        # Verify this is an access token (not a refresh token)
        token_data = verify_token_type(token, "access")
        logger.debug(f"Validated access token for user {token_data.email}")
    except JWTError as e:
        logger.warning(f"Invalid token provided: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query user from database
    try:
        result = await db.execute(select(User).where(User.id == token_data.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"User not found in database: {token_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug(f"Successfully retrieved user: {user.email}")
        return user

    except HTTPException:
        # Re-raise HTTPException (user not found)
        raise
    except Exception as e:
        logger.error(f"Database error while fetching user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verify the current user is active and return the user object.

    This dependency extends get_current_user by adding an additional check
    to ensure the user account is active. Inactive users (is_active=False)
    cannot access protected endpoints even with valid credentials.

    Common use cases for inactive accounts:
    - User has been banned/disabled by admin
    - Account has been deactivated
    - Email verification is pending (if using is_verified)

    Args:
        current_user: The authenticated user from get_current_user dependency

    Returns:
        User: The active user object

    Raises:
        HTTPException: 403 Forbidden if user account is not active

    Example:
        @router.post("/sensitive-operation")
        async def sensitive_op(
            current_user: User = Depends(get_current_active_user)
        ):
            # User is guaranteed to be active here
            return {"message": "Operation authorized"}
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact support.",
        )

    logger.debug(f"Active user verified: {current_user.email}")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verify the current user is both active and email-verified.

    This dependency extends get_current_user by checking both:
    - User account is active (is_active=True)
    - User email has been verified (is_verified=True)

    Use this for endpoints that require email verification, such as:
    - Password change
    - Email update
    - Sensitive operations

    Args:
        current_user: The authenticated user from get_current_user dependency

    Returns:
        User: The active and verified user object

    Raises:
        HTTPException: 403 Forbidden if user is not active or not verified

    Example:
        @router.post("/change-email")
        async def change_email(
            new_email: str,
            current_user: User = Depends(get_current_verified_user)
        ):
            # User is guaranteed to be active AND verified here
            return {"message": "Email update authorized"}
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact support.",
        )

    if not current_user.is_verified:
        logger.warning(f"Unverified user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
        )

    logger.debug(f"Active and verified user: {current_user.email}")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Verify the current user is a superuser (admin).

    This dependency enforces superuser-only access to sensitive endpoints.
    Only users with is_superuser=True can access endpoints using this dependency.

    Use this for administrative operations:
    - User management
    - System configuration
    - Admin-only reports

    Args:
        current_user: The active user from get_current_active_user dependency

    Returns:
        User: The superuser object

    Raises:
        HTTPException: 403 Forbidden if user is not a superuser

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: User = Depends(get_current_superuser)
        ):
            # Only superusers can reach this endpoint
            return {"message": "User deletion authorized"}
    """
    if not current_user.is_superuser:
        logger.warning(
            f"Non-superuser attempted admin access: {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required. Access denied.",
        )

    logger.debug(f"Superuser access granted: {current_user.email}")
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory that creates a dependency requiring a specific role.

    This function returns a FastAPI dependency that checks if the current user
    has the specified role. Use it to protect endpoints based on user roles.

    Args:
        required_role: The UserRole enum value required (e.g., UserRole.ADMIN)

    Returns:
        A dependency function that returns the User if authorized

    Raises:
        HTTPException: 403 Forbidden if user lacks the required role

    Example:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(require_role(UserRole.ADMIN)):
        ):
            return {"message": f"Welcome admin {current_user.email}"}

        @router.post("/recruiter-action")
        async def recruiter_action(
            current_user: User = Depends(require_role(UserRole.RECRUITER)):
        ):
            return {"message": "Recruiter action authorized"}
    """

    async def check_role(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """
        Verify the current user has the required role.

        This dependency:
        1. Ensures the user is active (via get_current_active_user)
        2. Queries the roles table for the user's roles
        3. Checks if the user has the required role
        4. Returns the user if authorized, raises 403 otherwise

        Args:
            current_user: The active user from get_current_active_user
            db: Database session for querying roles

        Returns:
            User: The authorized user object

        Raises:
            HTTPException: 403 Forbidden if user lacks the required role
        """
        # Query user's roles from the database
        try:
            result = await db.execute(
                select(Role).where(
                    Role.user_id == current_user.id,
                    Role.role == required_role,
                )
            )
            user_role = result.scalar_one_or_none()

            if user_role is None:
                logger.warning(
                    f"User {current_user.email} attempted access without required role: {required_role.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role.value}' required. Access denied.",
                )

            logger.debug(
                f"User {current_user.email} granted access via role: {required_role.value}"
            )
            return current_user

        except HTTPException:
            # Re-raise HTTPException (authorization failed)
            raise
        except Exception as e:
            logger.error(f"Database error while checking user role: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    return check_role


async def require_admin(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Verify the current user has admin role and return the user object.

    This is a convenience dependency that checks for the ADMIN role.
    It is equivalent to using Depends(require_role(UserRole.ADMIN)).

    Use this for admin-only endpoints:
    - User management
    - System configuration
    - Admin reports

    Args:
        current_user: The active user from get_current_active_user
        db: Database session for querying roles

    Returns:
        User: The admin user object

    Raises:
        HTTPException: 403 Forbidden if user is not an admin

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: User = Depends(require_admin)
        ):
            # Only admins can reach this endpoint
            return {"message": "User deletion authorized"}

    Note:
        This checks the roles table for the ADMIN role assignment.
        For superuser checks, use get_current_superuser instead.
    """
    # Query user's admin role from the database
    try:
        result = await db.execute(
            select(Role).where(
                Role.user_id == current_user.id,
                Role.role == UserRole.ADMIN,
            )
        )
        admin_role = result.scalar_one_or_none()

        if admin_role is None:
            logger.warning(
                f"Non-admin user attempted admin access: {current_user.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required. Access denied.",
            )

        logger.debug(f"Admin access granted: {current_user.email}")
        return current_user

    except HTTPException:
        # Re-raise HTTPException (authorization failed)
        raise
    except Exception as e:
        logger.error(f"Database error while checking admin role: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
