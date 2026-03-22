"""
Authentication and authorization endpoints.

This module provides endpoints for:
- User registration with email validation
- User login with JWT token generation
- Token refresh for maintaining sessions
- User logout and token revocation
- Password reset request and confirmation

Implements secure authentication using bcrypt password hashing and JWT tokens.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from models.role import Role, UserRole
from models.refresh_token import RefreshToken
from models.audit_log import AuditActionType
from utils.security import get_password_hash, verify_password, validate_password_strength
from utils.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    TokenData,
)
from utils.audit_logger import log_audit_event, get_request_context
from config import get_settings
from services.email_service import get_email_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================

class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password (min 8 chars, uppercase, lowercase, digit, special)", min_length=8)
    full_name: Optional[str] = Field(None, description="User's full name")
    role: Optional[str] = Field(None, description="User's role (admin, hiring_manager, job_seeker, recruiter, viewer)")

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class RegisterResponse(BaseModel):
    """Response model for successful registration."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User's email")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user's email is verified")
    message: str = Field(..., description="Success message")


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class LoginResponse(BaseModel):
    """Response model for successful login."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    user: UserInfo = Field(..., description="User information")


class UserInfo(BaseModel):
    """Basic user information."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User's email")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_verified: bool = Field(..., description="Whether the user's email is verified")
    is_superuser: bool = Field(..., description="Whether the user has superuser privileges")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshTokenResponse(BaseModel):
    """Response model for successful token refresh."""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class LogoutRequest(BaseModel):
    """Request model for user logout."""

    refresh_token: str = Field(..., description="Refresh token to revoke")


class LogoutResponse(BaseModel):
    """Response model for successful logout."""

    message: str = Field(..., description="Success message")


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""

    email: EmailStr = Field(..., description="User's email address")


class PasswordResetRequestResponse(BaseModel):
    """Response model for password reset request."""

    message: str = Field(..., description="Success message")


class PasswordResetConfirmRequest(BaseModel):
    """Request model for password reset confirmation."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., description="New password (min 8 chars, uppercase, lowercase, digit, special)", min_length=8)

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class PasswordResetConfirmResponse(BaseModel):
    """Response model for successful password reset."""

    message: str = Field(..., description="Success message")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error message")
    type: str = Field(..., description="Error category")


class RequestEmailVerificationRequest(BaseModel):
    """Request model for email verification token."""

    email: EmailStr = Field(..., description="User's email address")


class RequestEmailVerificationResponse(BaseModel):
    """Response model for email verification token request."""

    message: str = Field(..., description="Success message")


class VerifyEmailRequest(BaseModel):
    """Request model for email verification confirmation."""

    token: str = Field(..., description="Email verification token")


class VerifyEmailResponse(BaseModel):
    """Response model for successful email verification."""

    message: str = Field(..., description="Success message")


# ============================================================
# Endpoints
# ============================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
async def register(
    request: Request,
    request_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Register a new user account.

    Creates a new user account with the provided email and password.
    The password will be hashed using bcrypt before storage. A role
    will be assigned based on the request parameter, defaulting to
    'job_seeker' if not specified.

    Args:
        request_data: Registration data including email, password, optional full_name, and optional role
        db: Database session

    Returns:
        JSON response with created user information

    Raises:
        HTTPException(400): If email is already registered or role is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "email": "user@example.com",
        ...     "password": "SecurePass123!",
        ...     "full_name": "John Doe",
        ...     "role": "job_seeker"
        ... }
        >>> response = requests.post("http://localhost:8000/api/auth/register", json=data)
        >>> response.json()
        {
            "id": "...",
            "email": "user@example.com",
            "full_name": "John Doe",
            "is_active": true,
            "is_verified": false,
            "message": "User registered successfully"
        }
    """
    try:
        logger.info(f"Registration attempt for email: {request_data.email}")

        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == request_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Registration failed: email already registered - {request_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered",
            )

        # Hash the password
        password_hash = get_password_hash(request_data.password)

        # Validate and determine role
        requested_role = request_data.role
        if requested_role is None:
            # Default to job_seeker if no role specified
            user_role_enum = UserRole.JOB_SEEKER
        else:
            # Map string role to UserRole enum
            role_mapping = {
                "admin": UserRole.ADMIN,
                "hiring_manager": UserRole.HIRING_MANAGER,
                "job_seeker": UserRole.JOB_SEEKER,
                "recruiter": UserRole.RECRUITER,
                "viewer": UserRole.VIEWER,
            }
            if requested_role not in role_mapping:
                logger.warning(f"Registration failed: invalid role - {requested_role}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Must be one of: {', '.join(role_mapping.keys())}",
                )
            user_role_enum = role_mapping[requested_role]

        # Create new user
        new_user = User(
            email=request_data.email,
            password_hash=password_hash,
            full_name=request_data.full_name,
            is_active=True,
            is_verified=False,  # Email verification required
            is_superuser=False,
        )
        db.add(new_user)
        await db.flush()  # Flush to get the user ID

        # Assign the specified role
        user_role = Role(
            user_id=new_user.id,
            role=user_role_enum,
        )
        db.add(user_role)

        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id}, role: {user_role_enum.value})")

        # Log audit event for user registration
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.USER_CREATED,
            entity_type="user",
            entity_id=new_user.id,
            user_id=new_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value={
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": user_role_enum.value,
                "is_active": new_user.is_active,
                "is_verified": new_user.is_verified,
            },
        )

        # Send welcome email
        try:
            email_service = get_email_service()

            # Prepare context for email template
            email_context = {
                "email": new_user.email,
                "full_name": new_user.full_name or new_user.email.split("@")[0],
            }

            # Try to send template email first, fall back to plain text
            if not email_service.send_template_email(
                to=new_user.email,
                subject="Welcome to AgentHR",
                template_name=email_service.TEMPLATE_WELCOME,
                context=email_context,
            ):
                # Fall back to plain text email if template fails
                plain_body = f"""Welcome to AgentHR!

Hello {email_context['full_name']},

Thank you for registering with AgentHR. Your account has been created successfully.

Email: {new_user.email}

To get started, please verify your email address by visiting:
{settings.frontend_url}/verify-email

If you have any questions, feel free to contact our support team.

Best regards,
The AgentHR Team
"""
                email_service.send_email(
                    to=new_user.email,
                    subject="Welcome to AgentHR",
                    body=plain_body,
                    html=False,
                )
        except Exception as email_error:
            # Don't fail registration if email sending fails
            logger.warning(f"Failed to send welcome email to {new_user.email}: {email_error}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_user.id),
                "email": new_user.email,
                "full_name": new_user.full_name,
                "is_active": new_user.is_active,
                "is_verified": new_user.is_verified,
                "message": "User registered successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        ) from e


@router.post(
    "/login",
    response_model=LoginResponse,
    tags=["Authentication"],
)
async def login(
    request: Request,
    request_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Authenticate user and generate JWT tokens.

    Validates user credentials and returns JWT access and refresh tokens.
    The access token is short-lived (default 30 minutes) and used for API
    authentication. The refresh token is longer-lived (default 7 days) and
    can be used to obtain new access tokens.

    Args:
        request_data: Login credentials including email and password
        db: Database session

    Returns:
        JSON response with JWT tokens and user information

    Raises:
        HTTPException(401): If credentials are invalid
        HTTPException(403): If user account is inactive
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "email": "user@example.com",
        ...     "password": "SecurePass123!"
        ... }
        >>> response = requests.post("http://localhost:8000/api/auth/login", json=data)
        >>> response.json()
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": "...",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "is_verified": false,
                "is_superuser": false
            }
        }
    """
    try:
        logger.info(f"Login attempt for email: {request_data.email}")

        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request_data.email)
        )
        user = result.scalar_one_or_none()

        # Extract request context for audit logging
        ip_address, user_agent = get_request_context(request)

        # Verify user exists
        if not user:
            logger.warning(f"Login failed: user not found - {request_data.email}")
            # Log failed login attempt
            await log_audit_event(
                db=db,
                action_type=AuditActionType.LOGIN_FAILED,
                entity_type="user",
                ip_address=ip_address,
                user_agent=user_agent,
                action_data={
                    "email": request_data.email,
                    "reason": "user_not_found",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(request_data.password, user.password_hash):
            logger.warning(f"Login failed: invalid password - {request_data.email}")
            # Log failed login attempt
            await log_audit_event(
                db=db,
                action_type=AuditActionType.LOGIN_FAILED,
                entity_type="user",
                entity_id=user.id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                action_data={
                    "email": request_data.email,
                    "reason": "invalid_password",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: user account inactive - {request_data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive. Please contact support.",
            )

        # Create JWT tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
        )
        refresh_token = create_refresh_token(
            user_id=str(user.id),
            email=user.email,
        )

        # Store refresh token in database
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
            is_revoked=False,
        )
        db.add(refresh_token_record)
        await db.commit()

        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")

        # Log successful login
        await log_audit_event(
            db=db,
            action_type=AuditActionType.LOGIN_SUCCESS,
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "email": user.email,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "is_superuser": user.is_superuser,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        ) from e


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    tags=["Authentication"],
)
async def refresh_token(
    request_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Refresh access token using refresh token.

    Validates the refresh token and generates a new access token.
    The refresh token must be valid, not expired, and not revoked.

    Args:
        request_data: Refresh token
        db: Database session

    Returns:
        JSON response with new access token

    Raises:
        HTTPException(401): If refresh token is invalid or expired
        HTTPException(403): If refresh token is revoked
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
        >>> response = requests.post("http://localhost:8000/api/auth/refresh", json=data)
        >>> response.json()
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    """
    try:
        logger.info("Token refresh request received")

        # Decode and verify refresh token
        token_data = verify_token_type(request_data.refresh_token, "refresh")

        # Check if refresh token exists in database and is not revoked
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == request_data.refresh_token,
                RefreshToken.is_revoked == False,
            )
        )
        refresh_token_record = result.scalar_one_or_none()

        if not refresh_token_record:
            logger.warning("Token refresh failed: refresh token not found or revoked")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Check if token is expired
        if refresh_token_record.expires_at < datetime.utcnow():
            logger.warning("Token refresh failed: refresh token expired")
            # Mark as revoked
            refresh_token_record.is_revoked = True
            refresh_token_record.revoked_at = datetime.utcnow()
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        # Verify user still exists and is active
        user_result = await db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            logger.warning(f"Token refresh failed: user not found or inactive - {token_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or inactive",
            )

        # Generate new access token
        new_access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
        )

        logger.info(f"Token refreshed successfully for user: {user.email}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        ) from e


@router.post(
    "/logout",
    response_model=LogoutResponse,
    tags=["Authentication"],
)
async def logout(
    request: Request,
    request_data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Logout user and revoke refresh token.

    Revokes the provided refresh token to prevent further use.
    Clients should also discard their access tokens.

    Args:
        request_data: Refresh token to revoke
        db: Database session

    Returns:
        JSON response with logout confirmation

    Raises:
        HTTPException(401): If refresh token is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
        >>> response = requests.post("http://localhost:8000/api/auth/logout", json=data)
        >>> response.json()
        {"message": "Logged out successfully"}
    """
    try:
        logger.info("Logout request received")

        # Find and revoke the refresh token
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == request_data.refresh_token,
                RefreshToken.is_revoked == False,
            )
        )
        refresh_token_record = result.scalar_one_or_none()

        # Extract request context for audit logging
        ip_address, user_agent = get_request_context(request)

        if refresh_token_record:
            # Revoke the token
            refresh_token_record.is_revoked = True
            refresh_token_record.revoked_at = datetime.utcnow()

            # Log logout event
            await log_audit_event(
                db=db,
                action_type=AuditActionType.LOGOUT,
                entity_type="user",
                entity_id=refresh_token_record.user_id,
                user_id=refresh_token_record.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            await db.commit()
            logger.info("Refresh token revoked successfully")
        else:
            logger.warning("Logout attempted with invalid or already revoked token")
            # Still return success to avoid leaking information

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Logged out successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}",
        ) from e


@router.post(
    "/password-reset-request",
    response_model=PasswordResetRequestResponse,
    tags=["Authentication"],
)
async def password_reset_request(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Request password reset email.

    Initiates the password reset flow for a user. If the email exists
    in the system, a password reset token will be generated and should
    be sent to the user's email (email sending not implemented yet).

    Args:
        request_data: Email address for password reset
        db: Database session

    Returns:
        JSON response confirming request was processed

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"email": "user@example.com"}
        >>> response = requests.post("http://localhost:8000/api/auth/password-reset-request", json=data)
        >>> response.json()
        {"message": "If the email exists, a password reset link has been sent"}
    """
    try:
        logger.info(f"Password reset request for email: {request_data.email}")

        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request_data.email)
        )
        user = result.scalar_one_or_none()

        if user:
            # Generate reset token (use refresh token as reset token for now)
            # In production, this should be a separate token type with shorter expiration
            reset_token = create_refresh_token(
                user_id=str(user.id),
                email=user.email,
                expires_delta=timedelta(hours=1),  # 1 hour expiration
            )

            # Store reset token
            reset_record = RefreshToken(
                user_id=user.id,
                token=reset_token,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_revoked=False,
            )
            db.add(reset_record)
            await db.commit()

            # TODO: Send email with reset token
            # For now, just log it (INSECURE - for development only)
            logger.info(f"Password reset token generated for {user.email}: {reset_token}")

        # Always return success to avoid email enumeration
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "If the email exists, a password reset link has been sent"
            },
        )

    except Exception as e:
        logger.error(f"Error during password reset request: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}",
        ) from e


@router.post(
    "/password-reset-confirm",
    response_model=PasswordResetConfirmResponse,
    tags=["Authentication"],
)
async def password_reset_confirm(
    request: Request,
    request_data: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Confirm password reset with token.

    Validates the password reset token and updates the user's password.
    The token must be valid, not expired, and not revoked.

    Args:
        request_data: Reset token and new password
        db: Database session

    Returns:
        JSON response confirming password was reset

    Raises:
        HTTPException(400): If token is invalid or expired
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        ...     "new_password": "NewSecurePass123!"
        ... }
        >>> response = requests.post("http://localhost:8000/api/auth/password-reset-confirm", json=data)
        >>> response.json()
        {"message": "Password reset successfully"}
    """
    try:
        logger.info("Password reset confirmation received")

        # Decode and verify reset token (using refresh token verification)
        try:
            token_data = decode_token(request_data.token)
        except Exception as e:
            logger.warning(f"Password reset failed: invalid token - {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Check if reset token exists in database and is not revoked
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == request_data.token,
                RefreshToken.is_revoked == False,
            )
        )
        reset_token_record = result.scalar_one_or_none()

        if not reset_token_record:
            logger.warning("Password reset failed: reset token not found or revoked")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Check if token is expired
        if reset_token_record.expires_at < datetime.utcnow():
            logger.warning("Password reset failed: reset token expired")
            # Mark as revoked
            reset_token_record.is_revoked = True
            reset_token_record.revoked_at = datetime.utcnow()
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired",
            )

        # Find user
        user_result = await db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            logger.warning(f"Password reset failed: user not found - {token_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token",
            )

        # Hash new password
        new_password_hash = get_password_hash(request_data.new_password)

        # Update user password
        user.password_hash = new_password_hash

        # Revoke the reset token and all other refresh tokens for this user
        reset_token_record.is_revoked = True
        reset_token_record.revoked_at = datetime.utcnow()

        # Revoke all other refresh tokens for security
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.id != reset_token_record.id,
                RefreshToken.is_revoked == False,
            )
        )
        # Mark all tokens as revoked
        other_tokens_result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.id != reset_token_record.id,
            )
        )
        for token in other_tokens_result.scalars().all():
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Password reset successfully for user: {user.email}")

        # Log password change event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.PASSWORD_CHANGED,
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "reset_method": "password_reset_token",
            },
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Password reset successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during password reset: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}",
        ) from e


@router.post(
    "/request-email-verification",
    response_model=RequestEmailVerificationResponse,
    tags=["Authentication"],
)
async def request_email_verification(
    request_data: RequestEmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Request email verification token.

    Initiates the email verification flow for a user. If the email exists
    in the system, an email verification token will be generated and should
    be sent to the user's email (email sending not implemented yet).

    Args:
        request_data: Email address for verification
        db: Database session

    Returns:
        JSON response confirming request was processed

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"email": "user@example.com"}
        >>> response = requests.post("http://localhost:8000/api/auth/request-email-verification", json=data)
        >>> response.json()
        {"message": "If the email exists, a verification link has been sent"}
    """
    try:
        logger.info(f"Email verification request for email: {request_data.email}")

        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request_data.email)
        )
        user = result.scalar_one_or_none()

        if user:
            # Generate verification token
            verification_token = create_refresh_token(
                user_id=str(user.id),
                email=user.email,
                expires_delta=timedelta(hours=24),  # 24 hour expiration
            )

            # Store verification token
            verification_record = RefreshToken(
                user_id=user.id,
                token=verification_token,
                expires_at=datetime.utcnow() + timedelta(hours=24),
                is_revoked=False,
            )
            db.add(verification_record)
            await db.commit()

            # TODO: Send email with verification token
            # For now, just log it (INSECURE - for development only)
            logger.info(f"Email verification token generated for {user.email}: {verification_token}")

        # Always return success to avoid email enumeration
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "If the email exists, a verification link has been sent"
            },
        )

    except Exception as e:
        logger.error(f"Error during email verification request: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification request failed: {str(e)}",
        ) from e


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    tags=["Authentication"],
)
async def verify_email(
    request: Request,
    request_data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Confirm email verification with token.

    Validates the email verification token and marks the user's email as verified.
    The token must be valid, not expired, and not revoked.

    Args:
        request_data: Verification token
        db: Database session

    Returns:
        JSON response confirming email was verified

    Raises:
        HTTPException(400): If token is invalid or expired
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        ... }
        >>> response = requests.post("http://localhost:8000/api/auth/verify-email", json=data)
        >>> response.json()
        {"message": "Email verified successfully"}
    """
    try:
        logger.info("Email verification confirmation received")

        # Decode and verify verification token (using refresh token verification)
        try:
            token_data = decode_token(request_data.token)
        except Exception as e:
            logger.warning(f"Email verification failed: invalid token - {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        # Check if verification token exists in database and is not revoked
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == request_data.token,
                RefreshToken.is_revoked == False,
            )
        )
        verification_token_record = result.scalar_one_or_none()

        if not verification_token_record:
            logger.warning("Email verification failed: verification token not found or revoked")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        # Check if token is expired
        if verification_token_record.expires_at < datetime.utcnow():
            logger.warning("Email verification failed: verification token expired")
            # Mark as revoked
            verification_token_record.is_revoked = True
            verification_token_record.revoked_at = datetime.utcnow()
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
            )

        # Find user
        user_result = await db.execute(
            select(User).where(User.id == token_data.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            logger.warning(f"Email verification failed: user not found - {token_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        # Update user's verified status
        user.is_verified = True

        # Revoke the verification token
        verification_token_record.is_revoked = True
        verification_token_record.revoked_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Email verified successfully for user: {user.email}")

        # Log email verification event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.USER_UPDATED,
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "email_verified": True,
            },
            before_value={"is_verified": False},
            after_value={"is_verified": True},
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Email verified successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during email verification: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}",
        ) from e
