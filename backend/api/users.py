"""
User management endpoints for Admin role.

This module provides endpoints for managing users in Keycloak, including
CRUD operations for creating, reading, updating, and deleting users,
as well as managing user roles and permissions.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr

from middleware.auth import TokenData, require_role
from main import keycloak

logger = logging.getLogger(__name__)

router = APIRouter()


class UserCreate(BaseModel):
    """Request model for creating a user."""

    username: str = Field(..., description="Username for the new user")
    email: EmailStr = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    password: str = Field(..., description="Initial password", min_length=8)
    roles: List[str] = Field(
        default_factory=list,
        description="Roles to assign (Admin, Recruiter, Viewer)"
    )
    enabled: bool = Field(True, description="Whether the user account is enabled")


class UserUpdate(BaseModel):
    """Request model for updating a user."""

    email: Optional[EmailStr] = Field(None, description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    enabled: Optional[bool] = Field(None, description="Whether the user account is enabled")


class UserResponse(BaseModel):
    """Response model for a user."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    enabled: bool = Field(..., description="Whether the user account is enabled")
    email_verified: bool = Field(..., description="Whether email is verified")
    roles: List[str] = Field(default_factory=list, description="User's roles")
    created_at: Optional[int] = Field(None, description="Creation timestamp")


class UserListResponse(BaseModel):
    """Response model for listing users."""

    users: List[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total number of users")


class RoleUpdateRequest(BaseModel):
    """Request model for updating user roles."""

    roles: List[str] = Field(
        ...,
        description="Roles to assign (Admin, Recruiter, Viewer)"
    )


class PasswordResetRequest(BaseModel):
    """Request model for resetting user password."""

    new_password: str = Field(
        ...,
        description="New password",
        min_length=8
    )


@router.get(
    "/",
    response_model=UserListResponse,
    tags=["User Management"],
)
async def list_users(
    search: Optional[str] = Query(None, description="Search query for username or email"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    List all users in the system.

    This endpoint returns a list of all users with optional search filtering.
    Requires Admin role.
    """
    try:
        logger.info(f"Admin {token_data.username} listing users with search: {search}")

        # Get users from Keycloak
        users_data = keycloak.get_users(query=search)

        # Apply pagination
        total_count = len(users_data)
        paginated_users = users_data[offset:offset + limit]

        # Get user roles for each user
        users_with_roles = []
        for user in paginated_users:
            user_id = user.get("id")
            try:
                # Get user's roles from Keycloak
                user_roles = keycloak.get_user_roles(user_id=user_id)
                role_names = [
                    role.get("name")
                    for role in user_roles
                    if role.get("name") in ["Admin", "Recruiter", "Viewer"]
                ]
            except Exception as e:
                logger.warning(f"Failed to get roles for user {user_id}: {e}")
                role_names = []

            users_with_roles.append({
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "first_name": user.get("firstName"),
                "last_name": user.get("lastName"),
                "enabled": user.get("enabled", True),
                "email_verified": user.get("emailVerified", False),
                "roles": role_names,
                "created_at": user.get("createdTimestamp"),
            })

        response_data = {
            "users": users_with_roles,
            "total_count": total_count,
        }

        logger.info(f"Returning {len(users_with_roles)} users (total: {total_count})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}",
        ) from e


@router.get("/{user_id}", tags=["User Management"])
async def get_user(
    user_id: str,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Get a specific user by ID.

    This endpoint returns detailed information about a specific user.
    Requires Admin role.
    """
    try:
        logger.info(f"Admin {token_data.username} getting user: {user_id}")

        # Get user from Keycloak
        user = keycloak.get_user(user_id=user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Get user's roles
        try:
            user_roles = keycloak.get_user_roles(user_id=user_id)
            role_names = [
                role.get("name")
                for role in user_roles
                if role.get("name") in ["Admin", "Recruiter", "Viewer"]
            ]
        except Exception as e:
            logger.warning(f"Failed to get roles for user {user_id}: {e}")
            role_names = []

        response_data = {
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "first_name": user.get("firstName"),
            "last_name": user.get("lastName"),
            "enabled": user.get("enabled", True),
            "email_verified": user.get("emailVerified", False),
            "roles": role_names,
            "created_at": user.get("createdTimestamp"),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        ) from e


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["User Management"],
)
async def create_user(
    request: UserCreate,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Create a new user.

    This endpoint creates a new user in Keycloak with the specified
    roles. Requires Admin role.

    The user will receive an email to verify their email address if
    email verification is enabled in Keycloak.
    """
    try:
        logger.info(f"Admin {token_data.username} creating user: {request.username}")

        # Validate roles
        valid_roles = {"Admin", "Recruiter", "Viewer"}
        invalid_roles = set(request.roles) - valid_roles
        if invalid_roles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid roles: {', '.join(invalid_roles)}. Valid roles: {', '.join(valid_roles)}",
            )

        # Check if user already exists
        existing_users = keycloak.get_users(query=request.username)
        if existing_users and any(u.get("username") == request.username for u in existing_users):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username already exists: {request.username}",
            )

        # Create user in Keycloak
        user_id = keycloak.create_user(
            username=request.username,
            email=request.email,
            first_name=request.first_name or "",
            last_name=request.last_name or "",
            password=request.password,
            enabled=request.enabled,
            email_verified=False,
        )

        logger.info(f"User created with ID: {user_id}")

        # Assign roles to user
        if request.roles:
            # Get role representations from Keycloak
            realm_roles = keycloak.get_realm_roles()
            role_representations = [
                role for role in realm_roles if role.get("name") in request.roles
            ]

            if role_representations:
                keycloak.assign_client_roles(
                    user_id=user_id,
                    roles=role_representations,
                )
                logger.info(f"Assigned roles {request.roles} to user {user_id}")

        # Get the created user
        user = keycloak.get_user(user_id=user_id)

        response_data = {
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "first_name": user.get("firstName"),
            "last_name": user.get("lastName"),
            "enabled": user.get("enabled", True),
            "email_verified": user.get("emailVerified", False),
            "roles": request.roles,
            "created_at": user.get("createdTimestamp"),
        }

        logger.info(f"User {request.username} created successfully")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user {request.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        ) from e


@router.put("/{user_id}", tags=["User Management"])
async def update_user(
    user_id: str,
    request: UserUpdate,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Update a user.

    This endpoint updates user information. Requires Admin role.

    Note: Password changes should use the dedicated password reset endpoint.
    Role changes should use the dedicated roles endpoint.
    """
    try:
        logger.info(f"Admin {token_data.username} updating user: {user_id}")

        # Check if user exists
        existing_user = keycloak.get_user(user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Build update payload
        update_payload = {}
        if request.email is not None:
            update_payload["email"] = request.email
        if request.first_name is not None:
            update_payload["firstName"] = request.first_name
        if request.last_name is not None:
            update_payload["lastName"] = request.last_name
        if request.enabled is not None:
            update_payload["enabled"] = request.enabled

        # Update user in Keycloak
        if update_payload:
            keycloak.update_user(
                user_id=user_id,
                **update_payload,
            )
            logger.info(f"User {user_id} updated: {update_payload}")

        # Get the updated user
        updated_user = keycloak.get_user(user_id=user_id)

        # Get user's roles
        try:
            user_roles = keycloak.get_user_roles(user_id=user_id)
            role_names = [
                role.get("name")
                for role in user_roles
                if role.get("name") in ["Admin", "Recruiter", "Viewer"]
            ]
        except Exception as e:
            logger.warning(f"Failed to get roles for user {user_id}: {e}")
            role_names = []

        response_data = {
            "id": updated_user.get("id"),
            "username": updated_user.get("username"),
            "email": updated_user.get("email"),
            "first_name": updated_user.get("firstName"),
            "last_name": updated_user.get("lastName"),
            "enabled": updated_user.get("enabled", True),
            "email_verified": updated_user.get("emailVerified", False),
            "roles": role_names,
            "created_at": updated_user.get("createdTimestamp"),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        ) from e


@router.delete("/{user_id}", tags=["User Management"])
async def delete_user(
    user_id: str,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Delete a user.

    This endpoint permanently deletes a user from Keycloak.
    Requires Admin role.

    Warning: This action cannot be undone.
    """
    try:
        logger.info(f"Admin {token_data.username} deleting user: {user_id}")

        # Check if user exists
        existing_user = keycloak.get_user(user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Prevent self-deletion
        if user_id == token_data.sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        # Delete user from Keycloak
        keycloak.delete_user(user_id=user_id)

        logger.info(f"User {user_id} deleted successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User deleted successfully",
                "id": user_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        ) from e


@router.put("/{user_id}/roles", tags=["User Management"])
async def update_user_roles(
    user_id: str,
    request: RoleUpdateRequest,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Update user roles.

    This endpoint replaces all roles assigned to a user with the
    specified list of roles. Requires Admin role.
    """
    try:
        logger.info(f"Admin {token_data.username} updating roles for user: {user_id}")

        # Validate roles
        valid_roles = {"Admin", "Recruiter", "Viewer"}
        invalid_roles = set(request.roles) - valid_roles
        if invalid_roles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid roles: {', '.join(invalid_roles)}. Valid roles: {', '.join(valid_roles)}",
            )

        # Check if user exists
        existing_user = keycloak.get_user(user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Get all realm roles
        realm_roles = keycloak.get_realm_roles()

        # Get current user roles
        current_user_roles = keycloak.get_user_roles(user_id=user_id)
        current_role_names = {
            role.get("name")
            for role in current_user_roles
            if role.get("name") in valid_roles
        }

        # Remove old roles
        roles_to_remove = [
            role for role in current_user_roles
            if role.get("name") in valid_roles and role.get("name") not in request.roles
        ]
        if roles_to_remove:
            keycloak.delete_client_roles(
                user_id=user_id,
                roles=roles_to_remove,
            )
            logger.info(f"Removed roles {[r.get('name') for r in roles_to_remove]} from user {user_id}")

        # Add new roles
        roles_to_add = [
            role for role in realm_roles
            if role.get("name") in request.roles and role.get("name") not in current_role_names
        ]
        if roles_to_add:
            keycloak.assign_client_roles(
                user_id=user_id,
                roles=roles_to_add,
            )
            logger.info(f"Added roles {[r.get('name') for r in roles_to_add]} to user {user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User roles updated successfully",
                "user_id": user_id,
                "roles": request.roles,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating roles for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user roles: {str(e)}",
        ) from e


@router.put("/{user_id}/password", tags=["User Management"])
async def reset_user_password(
    user_id: str,
    request: PasswordResetRequest,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Reset user password.

    This endpoint resets a user's password. Requires Admin role.

    The user will need to change their password on next login if
    password change policy is enabled in Keycloak.
    """
    try:
        logger.info(f"Admin {token_data.username} resetting password for user: {user_id}")

        # Check if user exists
        existing_user = keycloak.get_user(user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Update password in Keycloak
        keycloak.update_user(
            user_id=user_id,
            password=request.new_password,
        )

        logger.info(f"Password reset for user {user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Password reset successfully",
                "user_id": user_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}",
        ) from e


@router.post("/{user_id}/disable", tags=["User Management"])
async def disable_user(
    user_id: str,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Disable a user account.

    This endpoint disables a user account, preventing login.
    Requires Admin role.
    """
    try:
        logger.info(f"Admin {token_data.username} disabling user: {user_id}")

        # Check if user exists
        existing_user = keycloak.get_user(user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Prevent self-disable
        if user_id == token_data.sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot disable your own account",
            )

        # Disable user in Keycloak
        keycloak.update_user(
            user_id=user_id,
            enabled=False,
        )

        logger.info(f"User {user_id} disabled")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User disabled successfully",
                "user_id": user_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable user: {str(e)}",
        ) from e


@router.post("/{user_id}/enable", tags=["User Management"])
async def enable_user(
    user_id: str,
    token_data: TokenData = Depends(require_role("Admin")),
) -> JSONResponse:
    """
    Enable a user account.

    This endpoint enables a previously disabled user account.
    Requires Admin role.
    """
    try:
        logger.info(f"Admin {token_data.username} enabling user: {user_id}")

        # Check if user exists
        existing_user = keycloak.get_user(user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Enable user in Keycloak
        keycloak.update_user(
            user_id=user_id,
            enabled=True,
        )

        logger.info(f"User {user_id} enabled")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User enabled successfully",
                "user_id": user_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable user: {str(e)}",
        ) from e
