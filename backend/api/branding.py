"""
Branding settings management endpoints.

This module provides endpoints for managing organization branding settings,
including colors, fonts, logos, and custom styling.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.branding_settings import BrandingSettings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class BrandingSettingsCreate(BaseModel):
    """Request model for creating branding settings."""

    organization_id: str = Field(..., description="Organization ID")
    primary_color: str = Field(..., min_length=7, max_length=7, description="Primary brand color in hex format (e.g., #3B82F6)")
    secondary_color: str = Field(..., min_length=7, max_length=7, description="Secondary brand color in hex format (e.g., #10B981)")
    accent_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Accent color in hex format (e.g., #F59E0B)")
    background_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Background color in hex format (e.g., #FFFFFF)")
    text_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Text color in hex format (e.g., #1F2937)")
    font_family: Optional[str] = Field(None, max_length=100, description="Font family name (e.g., Inter, Roboto)")
    custom_css: Optional[str] = Field(None, description="Custom CSS for advanced styling")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to organization logo")
    favicon_url: Optional[str] = Field(None, max_length=500, description="URL to custom favicon")
    is_active: bool = Field(True, description="Whether these branding settings are active")
    created_by: Optional[str] = Field(None, description="User ID who created these settings")

    @validator('primary_color', 'secondary_color', 'accent_color', 'background_color', 'text_color', pre=True)
    def validate_hex_color(cls, v):
        """Validate hex color format."""
        if v is not None and not v.startswith('#'):
            raise ValueError('Color must start with #')
        if v is not None:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
                raise ValueError('Color must be a valid hex color (e.g., #3B82F6)')
        return v


class BrandingSettingsUpdate(BaseModel):
    """Request model for updating branding settings."""

    primary_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Primary brand color in hex format (e.g., #3B82F6)")
    secondary_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Secondary brand color in hex format (e.g., #10B981)")
    accent_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Accent color in hex format (e.g., #F59E0B)")
    background_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Background color in hex format (e.g., #FFFFFF)")
    text_color: Optional[str] = Field(None, min_length=7, max_length=7, description="Text color in hex format (e.g., #1F2937)")
    font_family: Optional[str] = Field(None, max_length=100, description="Font family name (e.g., Inter, Roboto)")
    custom_css: Optional[str] = Field(None, description="Custom CSS for advanced styling")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to organization logo")
    favicon_url: Optional[str] = Field(None, max_length=500, description="URL to custom favicon")
    is_active: Optional[bool] = Field(None, description="Whether these branding settings are active")

    @validator('primary_color', 'secondary_color', 'accent_color', 'background_color', 'text_color', pre=True)
    def validate_hex_color(cls, v):
        """Validate hex color format."""
        if v is not None and not v.startswith('#'):
            raise ValueError('Color must start with #')
        if v is not None:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
                raise ValueError('Color must be a valid hex color (e.g., #3B82F6)')
        return v


class BrandingSettingsResponse(BaseModel):
    """Response model for branding settings."""

    id: str = Field(..., description="Unique identifier for the branding settings")
    organization_id: str = Field(..., description="Organization ID")
    primary_color: str = Field(..., description="Primary brand color in hex format")
    secondary_color: str = Field(..., description="Secondary brand color in hex format")
    accent_color: str = Field(..., description="Accent color in hex format")
    background_color: Optional[str] = Field(None, description="Background color in hex format")
    text_color: Optional[str] = Field(None, description="Text color in hex format")
    font_family: Optional[str] = Field(None, description="Font family name")
    custom_css: Optional[str] = Field(None, description="Custom CSS for advanced styling")
    logo_url: Optional[str] = Field(None, description="URL to organization logo")
    favicon_url: Optional[str] = Field(None, description="URL to custom favicon")
    is_active: bool = Field(..., description="Whether these branding settings are active")
    created_by: Optional[str] = Field(None, description="User ID who created these settings")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class BrandingSettingsListResponse(BaseModel):
    """Response model for listing branding settings."""

    branding_settings: list[BrandingSettingsResponse] = Field(..., description="List of branding settings")
    total_count: int = Field(..., description="Total number of branding settings")


def branding_to_response(branding: BrandingSettings) -> dict:
    """Convert BrandingSettings model to response dictionary."""
    return {
        "id": str(branding.id),
        "organization_id": branding.organization_id,
        "primary_color": branding.primary_color,
        "secondary_color": branding.secondary_color,
        "accent_color": branding.accent_color,
        "background_color": branding.background_color,
        "text_color": branding.text_color,
        "font_family": branding.font_family,
        "custom_css": branding.custom_css,
        "logo_url": branding.logo_url,
        "favicon_url": branding.favicon_url,
        "is_active": branding.is_active,
        "created_by": branding.created_by,
        "created_at": branding.created_at.isoformat() if branding.created_at else None,
        "updated_at": branding.updated_at.isoformat() if branding.updated_at else None,
    }


@router.post(
    "/",
    response_model=BrandingSettingsResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Branding"],
)
async def create_branding_settings(
    request: BrandingSettingsCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create new branding settings.

    Creates a new branding settings record for an organization with custom colors,
    fonts, logos, and styling options.

    Args:
        request: Request body containing branding settings details
        db: Database session

    Returns:
        JSON response with created branding settings

    Raises:
        HTTPException(400): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/branding/",
        ...     json={
        ...         "organization_id": "test-org-id",
        ...         "primary_color": "#3B82F6",
        ...         "secondary_color": "#10B981"
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating branding settings for organization: {request.organization_id}")

        # Create new branding settings
        branding = BrandingSettings(
            organization_id=request.organization_id,
            primary_color=request.primary_color,
            secondary_color=request.secondary_color,
            accent_color=request.accent_color or "#F59E0B",
            background_color=request.background_color,
            text_color=request.text_color,
            font_family=request.font_family,
            custom_css=request.custom_css,
            logo_url=request.logo_url,
            favicon_url=request.favicon_url,
            is_active=request.is_active,
            created_by=request.created_by,
        )

        db.add(branding)
        await db.commit()
        await db.refresh(branding)

        logger.info(f"Branding settings created successfully: {branding.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=branding_to_response(branding),
        )

    except ValueError as e:
        logger.warning(f"Validation error creating branding settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except SQLAlchemyError as e:
        logger.error(f"Database error creating branding settings: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branding settings: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error creating branding settings: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branding settings: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=BrandingSettingsListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Branding"],
)
async def list_branding_settings(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List branding settings.

    Returns a paginated list of branding settings with optional filtering.

    Args:
        organization_id: Optional organization ID filter
        is_active: Optional active status filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of branding settings

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/branding/")
        >>> response.json()
        {
            "branding_settings": [...],
            "total_count": 10
        }
    """
    try:
        logger.info(f"Listing branding settings with filters: organization_id={organization_id}, is_active={is_active}")

        # Build query
        query = select(BrandingSettings)

        if organization_id:
            query = query.where(BrandingSettings.organization_id == organization_id)
        if is_active is not None:
            query = query.where(BrandingSettings.is_active == is_active)

        # Get total count
        count_query = select(BrandingSettings.id)
        if organization_id:
            count_query = count_query.where(BrandingSettings.organization_id == organization_id)
        if is_active is not None:
            count_query = count_query.where(BrandingSettings.is_active == is_active)

        result_count = await db.execute(count_query)
        total_count = len(result_count.all())

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(BrandingSettings.created_at.desc())
        result = await db.execute(query)
        branding_list = result.scalars().all()

        branding_responses = [branding_to_response(branding) for branding in branding_list]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "branding_settings": branding_responses,
                "total_count": total_count,
            },
        )

    except Exception as e:
        logger.error(f"Error listing branding settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list branding settings: {str(e)}",
        ) from e


@router.get(
    "/{branding_id}",
    response_model=BrandingSettingsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Branding"],
)
async def get_branding_settings(
    branding_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get branding settings by ID.

    Returns the branding settings for the specified ID.

    Args:
        branding_id: Branding settings ID
        db: Database session

    Returns:
        JSON response with branding settings

    Raises:
        HTTPException(404): If branding settings not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/branding/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "organization_id": "test-org-id",
            "primary_color": "#3B82F6",
            ...
        }
    """
    try:
        logger.info(f"Retrieving branding settings: {branding_id}")

        query = select(BrandingSettings).where(BrandingSettings.id == branding_id)
        result = await db.execute(query)
        branding = result.scalar_one_or_none()

        if not branding:
            logger.warning(f"Branding settings not found: {branding_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branding settings not found: {branding_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=branding_to_response(branding),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving branding settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve branding settings: {str(e)}",
        ) from e


@router.put(
    "/{branding_id}",
    response_model=BrandingSettingsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Branding"],
)
async def update_branding_settings(
    branding_id: str,
    request: BrandingSettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update branding settings.

    Updates the branding settings for the specified ID.

    Args:
        branding_id: Branding settings ID
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated branding settings

    Raises:
        HTTPException(404): If branding settings not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/branding/123e4567-e89b-12d3-a456-426614174000",
        ...     json={"primary_color": "#FF5733"}
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "primary_color": "#FF5733",
            ...
        }
    """
    try:
        logger.info(f"Updating branding settings: {branding_id}")

        # Get existing branding settings
        query = select(BrandingSettings).where(BrandingSettings.id == branding_id)
        result = await db.execute(query)
        branding = result.scalar_one_or_none()

        if not branding:
            logger.warning(f"Branding settings not found: {branding_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branding settings not found: {branding_id}",
            )

        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(branding, field, value)

        await db.commit()
        await db.refresh(branding)

        logger.info(f"Branding settings updated successfully: {branding_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=branding_to_response(branding),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error updating branding settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except SQLAlchemyError as e:
        logger.error(f"Database error updating branding settings: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update branding settings: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error updating branding settings: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update branding settings: {str(e)}",
        ) from e


@router.delete(
    "/{branding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Branding"],
)
async def delete_branding_settings(
    branding_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete branding settings.

    Deletes the branding settings for the specified ID.

    Args:
        branding_id: Branding settings ID
        db: Database session

    Returns:
        Empty response with 204 status code

    Raises:
        HTTPException(404): If branding settings not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/branding/123e4567-e89b-12d3-a456-426614174000")
        >>> response.status_code
        204
    """
    try:
        logger.info(f"Deleting branding settings: {branding_id}")

        # Delete branding settings
        query = delete(BrandingSettings).where(BrandingSettings.id == branding_id)
        result = await db.execute(query)
        await db.commit()

        if result.rowcount == 0:
            logger.warning(f"Branding settings not found: {branding_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branding settings not found: {branding_id}",
            )

        logger.info(f"Branding settings deleted successfully: {branding_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting branding settings: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete branding settings: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error deleting branding settings: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete branding settings: {str(e)}",
        ) from e
