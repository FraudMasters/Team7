"""
Authentication endpoints for Keycloak integration.

This module provides endpoints for user authentication including login,
logout, token refresh, and token validation. These endpoints integrate
with Keycloak using the fastapi-keycloak library for OAuth2/OIDC flows.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from config import get_settings
from middleware.auth import TokenData, get_current_token, get_optional_token

logger = logging.getLogger(__name__)
settings = get_settings()

# Import keycloak instance from main (will be initialized when main.py loads)
from main import keycloak

router = APIRouter()
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Request model for user login."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Response model for successful login."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")
    user_info: dict = Field(..., description="User information from Keycloak")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Response model for successful token refresh."""

    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")


class TokenInfoResponse(BaseModel):
    """Response model for token information."""

    sub: str = Field(..., description="User ID (subject)")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")
    roles: list = Field(default_factory=list, description="User's roles")
    exp: int = Field(..., description="Token expiration timestamp")


class LogoutResponse(BaseModel):
    """Response model for logout."""

    message: str = Field(..., description="Logout status message")


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
)
async def login(request: LoginRequest) -> JSONResponse:
    """
    Authenticate user with Keycloak and return JWT tokens.

    This endpoint accepts username/password credentials, authenticates
    against Keycloak, and returns JWT access and refresh tokens along
    with user information.

    The tokens can be used to access protected API endpoints by including
    them in the Authorization header: `Authorization: Bearer <access_token>`
    """
    try:
        logger.info(f"Login attempt for user: {request.username}")

        # Authenticate with Keycloak using Resource Owner Password Credentials flow
        token_response = keycloak.user_login(
            username=request.username,
            password=request.password,
        )

        # Extract tokens and user info
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 300)
        refresh_expires_in = token_response.get("refresh_expires_in", 1800)

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: No access token returned",
            )

        # Get user info from Keycloak
        user_info = keycloak.get_user_info(access_token)

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_expires_in": refresh_expires_in,
            "user_info": {
                "sub": user_info.get("sub"),
                "username": user_info.get("preferred_username") or user_info.get("username"),
                "email": user_info.get("email"),
                "first_name": user_info.get("given_name"),
                "last_name": user_info.get("family_name"),
                "roles": user_info.get("realm_access", {}).get("roles", []),
                "email_verified": user_info.get("email_verified", False),
            }
        }

        logger.info(f"Login successful for user: {request.username}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for user {request.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        ) from e


@router.post("/logout", response_model=LogoutResponse, tags=["Authentication"])
async def logout(
    refresh_token: Optional[str] = None,
    token_data: Optional[TokenData] = Depends(get_optional_token),
) -> JSONResponse:
    """
    Logout user and invalidate tokens.

    This endpoint logs out the user from Keycloak, invalidating the refresh
    token. The access token will expire naturally based on its expiration time.

    For frontend applications, also clear the tokens from storage.
    """
    try:
        if token_data:
            logger.info(f"Logout request for user: {token_data.username}")
        else:
            logger.info("Logout request (unauthenticated)")

        # If refresh token is provided, logout from Keycloak
        if refresh_token:
            try:
                keycloak.user_logout(refresh_token=refresh_token)
                logger.info("Successfully logged out from Keycloak")
            except Exception as e:
                logger.warning(f"Keycloak logout failed (token may be expired): {e}")
                # Continue with logout response even if Keycloak logout fails

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Logout successful. Please clear your tokens from storage."
            },
        )

    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        # Return success even if logout fails - tokens should be cleared on client side
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Logout processed. Please clear your tokens from storage."
            },
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
)
async def refresh_token(request: RefreshTokenRequest) -> JSONResponse:
    """
    Refresh access token using refresh token.

    This endpoint exchanges a valid refresh token for a new access token
    and refresh token pair. This should be called before the access token
    expires to maintain user session.

    The frontend should implement automatic token refresh using the
    `expires_in` timestamp to refresh tokens before they expire.
    """
    try:
        logger.info("Token refresh request")

        if not request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required",
            )

        # Exchange refresh token for new access token
        token_response = keycloak.refresh_token(request.refresh_token)

        # Extract new tokens
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 300)
        refresh_expires_in = token_response.get("refresh_expires_in", 1800)

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed: No access token returned",
            )

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_expires_in": refresh_expires_in,
        }

        logger.info("Token refresh successful")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
        ) from e


@router.get("/me", response_model=TokenInfoResponse, tags=["Authentication"])
async def get_current_user_info(
    token_data: TokenData = Depends(get_current_token),
) -> JSONResponse:
    """
    Get current authenticated user information.

    This endpoint returns information about the currently authenticated user
    based on the JWT token in the Authorization header. Requires a valid
    access token.

    Use this endpoint to:
    - Verify authentication status
    - Get user profile information
    - Check user roles and permissions
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "sub": token_data.sub,
            "username": token_data.username,
            "email": token_data.email,
            "roles": token_data.roles,
            "exp": token_data.exp,
        },
    )


@router.post("/validate", tags=["Authentication"])
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JSONResponse:
    """
    Validate a JWT token without requiring authentication.

    This endpoint checks if a token is valid and returns basic information
    about the token. Returns 401 if the token is invalid or expired.

    Useful for checking token validity before making API calls or for
    debugging authentication issues.
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided",
            )

        token = credentials.credentials

        # Validate token with Keycloak
        user_info = keycloak.get_user_info(token)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "valid": True,
                "user_info": {
                    "sub": user_info.get("sub"),
                    "username": user_info.get("preferred_username") or user_info.get("username"),
                    "email": user_info.get("email"),
                    "roles": user_info.get("realm_access", {}).get("roles", []),
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        ) from e
