"""
Two-factor authentication endpoints for TOTP and SMS-based 2FA.

This module provides endpoints for setting up, verifying, and managing
two-factor authentication (2FA) for user accounts. Supports TOTP-based
authentication using authenticator apps (Google Authenticator, Authy, etc.)
and SMS-based authentication with verification codes.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.two_factor_auth import TwoFactorAuth
from services.totp_service import get_totp_service

logger = logging.getLogger(__name__)

router = APIRouter()


class TwoFactorStatusResponse(BaseModel):
    """Response model for 2FA status check."""

    enabled: bool = Field(..., description="Whether 2FA is enabled for the user")
    method: Optional[str] = Field(None, description="2FA method: 'totp', 'sms', or 'email'")
    verified: bool = Field(..., description="Whether 2FA setup has been verified")
    has_backup_codes: bool = Field(..., description="Whether backup codes are available")
    last_used_at: Optional[str] = Field(None, description="Last successful 2FA verification timestamp")
    created_at: Optional[str] = Field(None, description="When 2FA was configured")


class TwoFactorSetupRequest(BaseModel):
    """Request model for initiating 2FA setup."""

    user_id: str = Field(..., description="User ID to enable 2FA for")
    method: str = Field(..., description="2FA method: 'totp' or 'sms'")
    phone: Optional[str] = Field(None, description="Phone number for SMS-based 2FA")
    email: Optional[str] = Field(None, description="Email for email-based 2FA")


class TwoFactorSetupResponse(BaseModel):
    """Response model for 2FA setup initiation."""

    user_id: str = Field(..., description="User ID")
    method: str = Field(..., description="2FA method")
    secret: str = Field(..., description="TOTP secret (for TOTP method)")
    provisioning_uri: str = Field(..., description="QR code provisioning URI (for TOTP method)")
    backup_codes: List[str] = Field(..., description="Generated backup codes")
    message: str = Field(..., description="Setup instructions")


class TwoFactorVerifyRequest(BaseModel):
    """Request model for verifying 2FA setup."""

    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="TOTP code or SMS verification code")


class TwoFactorVerifyResponse(BaseModel):
    """Response model for 2FA verification."""

    success: bool = Field(..., description="Whether verification succeeded")
    message: str = Field(..., description="Verification result message")
    enabled: bool = Field(..., description="Whether 2FA is now enabled")


class TwoFactorDisableRequest(BaseModel):
    """Request model for disabling 2FA."""

    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="Current TOTP code to confirm disable action")


class BackupCodesGenerateRequest(BaseModel):
    """Request model for generating new backup codes."""

    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="Current TOTP code to verify before generating codes")


class BackupCodesResponse(BaseModel):
    """Response model for backup codes generation."""

    backup_codes: List[str] = Field(..., description="Newly generated backup codes")
    message: str = Field(..., description="Information about the codes")
    warning: str = Field(..., description="Security warning about saving codes")


@router.get(
    "/status",
    response_model=TwoFactorStatusResponse,
    tags=["2FA"],
)
async def get_2fa_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get two-factor authentication status for a user.

    This endpoint retrieves the current 2FA status including whether it's enabled,
    the method being used, verification status, and backup codes availability.

    Args:
        user_id: User ID to check 2FA status for
        db: Database session

    Returns:
        JSON response with 2FA status information

    Raises:
        HTTPException(400): If user_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/2fa/status?user_id=abc-123")
        >>> response.json()
        {
            "enabled": false,
            "method": null,
            "verified": false,
            "has_backup_codes": false,
            "last_used_at": null,
            "created_at": null
        }
    """
    try:
        logger.info(f"Fetching 2FA status for user: {user_id}")

        # Validate user_id format
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {user_id}",
            )

        # Query existing 2FA configuration
        query = select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_uuid)
        result = await db.execute(query)
        two_factor = result.scalar_one_or_none()

        if two_factor:
            # Check if backup codes exist
            has_backup_codes = bool(two_factor.backup_codes)

            response_data = {
                "enabled": two_factor.is_enabled,
                "method": two_factor.method,
                "verified": two_factor.is_verified,
                "has_backup_codes": has_backup_codes,
                "last_used_at": two_factor.last_used_at.isoformat() if two_factor.last_used_at else None,
                "created_at": two_factor.created_at.isoformat() if two_factor.created_at else None,
            }
            logger.info(f"2FA enabled for user: {user_id}, method: {two_factor.method}")
        else:
            response_data = {
                "enabled": False,
                "method": None,
                "verified": False,
                "has_backup_codes": False,
                "last_used_at": None,
                "created_at": None,
            }
            logger.info(f"2FA not configured for user: {user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving 2FA status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve 2FA status: {str(e)}",
        ) from e


@router.post(
    "/setup",
    response_model=TwoFactorSetupResponse,
    tags=["2FA"],
)
async def setup_2fa(
    request: TwoFactorSetupRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Initiate two-factor authentication setup for a user.

    This endpoint starts the 2FA setup process by generating a TOTP secret
    and provisioning URI for QR code generation. The user must verify the setup
    by entering a valid code before 2FA is activated.

    For TOTP method: Returns a secret and provisioning URI for QR code.
    For SMS method: Returns a secret and would send verification code via SMS.

    Args:
        request: Setup request with user_id, method, and optional phone/email
        db: Database session

    Returns:
        JSON response with secret, provisioning URI, and backup codes

    Raises:
        HTTPException(400): If user_id format is invalid or method is unsupported
        HTTPException(409): If 2FA is already enabled for this user
        HTTPException(500): If setup fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/2fa/setup",
        ...     json={"user_id": "abc-123", "method": "totp"}
        ... )
        >>> response.json()
        {
            "user_id": "abc-123",
            "method": "totp",
            "secret": "JBSWY3DPEHPK3PXP",
            "provisioning_uri": "otpauth://totp/...",
            "backup_codes": ["AB12-CD34-EF56", ...],
            "message": "Scan QR code with authenticator app"
        }
    """
    try:
        logger.info(f"Initiating 2FA setup for user: {request.user_id}, method: {request.method}")

        # Validate user_id format
        try:
            user_uuid = UUID(request.user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {request.user_id}",
            )

        # Validate method
        valid_methods = ["totp", "sms", "email"]
        if request.method not in valid_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid method: {request.method}. Valid methods: {', '.join(valid_methods)}",
            )

        # Check if 2FA already exists for this user
        query = select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_uuid)
        result = await db.execute(query)
        existing_2fa = result.scalar_one_or_none()

        if existing_2fa and existing_2fa.is_enabled:
            logger.warning(f"2FA already enabled for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Two-factor authentication is already enabled for this user",
            )

        # Get TOTP service
        totp_service = get_totp_service()

        # Generate TOTP secret
        secret = totp_service.generate_secret()

        # Generate provisioning URI for QR code
        provisioning_uri = totp_service.generate_provisioning_uri(
            secret=secret,
            identifier=request.user_id,
            name=f"User:{request.user_id}",
        )

        # Generate backup codes
        backup_codes = totp_service.generate_backup_codes()

        # Store backup codes as JSON string
        backup_codes_json = json.dumps(backup_codes)

        if existing_2fa:
            # Update existing 2FA configuration
            existing_2fa.method = request.method
            existing_2fa.totp_secret = secret
            existing_2fa.backup_codes = backup_codes_json
            existing_2fa.phone = request.phone
            existing_2fa.email = request.email
            existing_2fa.is_verified = False  # Reset verification
            existing_2fa.is_enabled = False  # Require verification before enabling
            existing_2fa.updated_at = datetime.utcnow()

            two_factor = existing_2fa
            logger.info(f"Updated existing 2FA configuration for user: {request.user_id}")
        else:
            # Create new 2FA configuration
            two_factor = TwoFactorAuth(
                user_id=user_uuid,
                method=request.method,
                totp_secret=secret,
                backup_codes=backup_codes_json,
                phone=request.phone,
                email=request.email,
                is_enabled=False,  # Will be enabled after verification
                is_verified=False,
            )
            db.add(two_factor)
            logger.info(f"Created new 2FA configuration for user: {request.user_id}")

        await db.commit()

        # Prepare response message based on method
        if request.method == "totp":
            message = "Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)"
        elif request.method == "sms":
            message = "A verification code has been sent to your phone via SMS"
        else:  # email
            message = "A verification code has been sent to your email"

        logger.info(f"2FA setup initiated for user: {request.user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "user_id": request.user_id,
                "method": request.method,
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "backup_codes": backup_codes,
                "message": message,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up 2FA: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set up 2FA: {str(e)}",
        ) from e


@router.post(
    "/verify",
    response_model=TwoFactorVerifyResponse,
    tags=["2FA"],
)
async def verify_2fa(
    request: TwoFactorVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Verify two-factor authentication setup or login.

    This endpoint verifies a TOTP code during 2FA setup or login.
    During setup, a successful verification enables 2FA for the user.
    During login, a successful verification grants access.

    Args:
        request: Verification request with user_id and TOTP code
        db: Database session

    Returns:
        JSON response indicating verification success

    Raises:
        HTTPException(400): If user_id format is invalid or code is missing
        HTTPException(404): If 2FA is not configured for this user
        HTTPException(500): If verification fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/2fa/verify",
        ...     json={"user_id": "abc-123", "code": "123456"}
        ... )
        >>> response.json()
        {
            "success": true,
            "message": "2FA verification successful",
            "enabled": true
        }
    """
    try:
        logger.info(f"Verifying 2FA for user: {request.user_id}")

        # Validate user_id format
        try:
            user_uuid = UUID(request.user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {request.user_id}",
            )

        if not request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code is required",
            )

        # Query existing 2FA configuration
        query = select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_uuid)
        result = await db.execute(query)
        two_factor = result.scalar_one_or_none()

        if not two_factor:
            logger.warning(f"2FA not configured for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Two-factor authentication is not configured for this user",
            )

        # Verify TOTP code
        totp_service = get_totp_service()
        is_valid = totp_service.verify_code(
            secret=two_factor.totp_secret,
            code=request.code,
        )

        if not is_valid:
            logger.warning(f"Invalid 2FA code for user: {request.user_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": False,
                    "message": "Invalid verification code. Please try again.",
                    "enabled": two_factor.is_enabled,
                },
            )

        # Update verification status
        two_factor.is_verified = True
        two_factor.is_enabled = True
        two_factor.last_used_at = datetime.utcnow()
        two_factor.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"2FA verified and enabled for user: {request.user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Two-factor authentication verified successfully",
                "enabled": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying 2FA: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA: {str(e)}",
        ) from e


@router.post(
    "/disable",
    tags=["2FA"],
)
async def disable_2fa(
    request: TwoFactorDisableRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Disable two-factor authentication for a user.

    This endpoint disables 2FA for a user after verifying their identity
    with a current TOTP code. This is a security-sensitive operation that
    requires the user to provide a valid code to confirm the action.

    Args:
        request: Disable request with user_id and confirmation code
        db: Database session

    Returns:
        JSON response indicating disable success

    Raises:
        HTTPException(400): If user_id format is invalid or code is missing
        HTTPException(404): If 2FA is not configured for this user
        HTTPException(401): If the confirmation code is invalid
        HTTPException(500): If disable operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/2fa/disable",
        ...     json={"user_id": "abc-123", "code": "123456"}
        ... )
        >>> response.json()
        {
            "success": true,
            "message": "2FA has been disabled"
        }
    """
    try:
        logger.info(f"Attempting to disable 2FA for user: {request.user_id}")

        # Validate user_id format
        try:
            user_uuid = UUID(request.user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {request.user_id}",
            )

        if not request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code is required to disable 2FA",
            )

        # Query existing 2FA configuration
        query = select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_uuid)
        result = await db.execute(query)
        two_factor = result.scalar_one_or_none()

        if not two_factor:
            logger.warning(f"2FA not configured for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Two-factor authentication is not configured for this user",
            )

        # Verify TOTP code to confirm disable action
        totp_service = get_totp_service()
        is_valid = totp_service.verify_code(
            secret=two_factor.totp_secret,
            code=request.code,
        )

        if not is_valid:
            logger.warning(f"Invalid confirmation code for 2FA disable: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code. Cannot disable 2FA.",
            )

        # Disable 2FA
        two_factor.is_enabled = False
        two_factor.is_verified = False
        two_factor.totp_secret = None  # Clear secret for security
        two_factor.backup_codes = None  # Clear backup codes
        two_factor.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"2FA disabled for user: {request.user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Two-factor authentication has been disabled",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable 2FA: {str(e)}",
        ) from e


@router.post(
    "/backup-codes/generate",
    response_model=BackupCodesResponse,
    tags=["2FA"],
)
async def generate_backup_codes(
    request: BackupCodesGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Generate new backup codes for two-factor authentication.

    This endpoint generates new backup codes for account recovery.
    The user must provide a valid TOTP code to verify their identity
    before new codes are generated. Any existing backup codes are invalidated.

    Args:
        request: Request with user_id and verification code
        db: Database session

    Returns:
        JSON response with newly generated backup codes

    Raises:
        HTTPException(400): If user_id format is invalid or code is missing
        HTTPException(404): If 2FA is not configured for this user
        HTTPException(401): If the verification code is invalid
        HTTPException(500): If code generation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/2fa/backup-codes/generate",
        ...     json={"user_id": "abc-123", "code": "123456"}
        ... )
        >>> response.json()
        {
            "backup_codes": ["AB12-CD34-EF56", ...],
            "message": "Generated 10 new backup codes",
            "warning": "Save these codes securely. Old codes are now invalid."
        }
    """
    try:
        logger.info(f"Generating backup codes for user: {request.user_id}")

        # Validate user_id format
        try:
            user_uuid = UUID(request.user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {request.user_id}",
            )

        if not request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code is required to generate backup codes",
            )

        # Query existing 2FA configuration
        query = select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_uuid)
        result = await db.execute(query)
        two_factor = result.scalar_one_or_none()

        if not two_factor:
            logger.warning(f"2FA not configured for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Two-factor authentication is not configured for this user",
            )

        # Verify TOTP code to confirm identity
        totp_service = get_totp_service()
        is_valid = totp_service.verify_code(
            secret=two_factor.totp_secret,
            code=request.code,
        )

        if not is_valid:
            logger.warning(f"Invalid verification code for backup codes: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code. Cannot generate backup codes.",
            )

        # Generate new backup codes
        new_backup_codes = totp_service.generate_backup_codes()
        backup_codes_json = json.dumps(new_backup_codes)

        # Update backup codes
        two_factor.backup_codes = backup_codes_json
        two_factor.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Generated {len(new_backup_codes)} backup codes for user: {request.user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "backup_codes": new_backup_codes,
                "message": f"Generated {len(new_backup_codes)} new backup codes",
                "warning": "Save these codes securely. Old backup codes are now invalid.",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating backup codes: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate backup codes: {str(e)}",
        ) from e
