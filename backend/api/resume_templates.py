"""
Resume template management endpoints.

This module provides endpoints for managing customizable resume formatting templates
with organization branding, including CRUD operations for creating, reading, updating,
and deleting resume templates with support for ATS-friendly layouts and styling.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.resume_template import ResumeTemplate

logger = logging.getLogger(__name__)

router = APIRouter()


def _template_to_dict(template: ResumeTemplate) -> dict:
    """
    Convert ResumeTemplate model to dictionary for API response.

    Args:
        template: ResumeTemplate model instance

    Returns:
        Dictionary representation of the template
    """
    return {
        "id": str(template.id),
        "organization_id": template.organization_id,
        "name": template.name,
        "description": template.description,
        "template_type": template.template_type,
        "layout_config": template.layout_config,
        "style_config": template.style_config,
        "section_config": template.section_config,
        "preview_url": template.preview_url,
        "is_default": template.is_default,
        "is_active": template.is_active,
        "is_ats_compliant": template.is_ats_compliant,
        "created_by": template.created_by,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


class ResumeTemplateCreate(BaseModel):
    """Request model for creating a resume template."""

    organization_id: Optional[str] = Field(None, description="ID of the organization (None for global templates)")
    name: str = Field(..., description="Template name (e.g., 'Modern', 'Classic', 'Creative')", max_length=255)
    description: Optional[str] = Field(None, description="Description of the template style")
    template_type: str = Field(..., description="Type of resume template (e.g., 'modern', 'classic', 'creative', 'ats_friendly')", max_length=100)
    layout_config: Optional[dict] = Field(None, description="Layout configuration (margins, sections, spacing, etc.)")
    style_config: Optional[dict] = Field(None, description="Style configuration (colors, fonts, headings, etc.)")
    section_config: Optional[dict] = Field(None, description="Section configuration (which sections to include and order)")
    preview_url: Optional[str] = Field(None, description="URL to preview image of the template", max_length=512)
    is_default: bool = Field(False, description="Whether this is the default template")
    is_active: bool = Field(True, description="Whether this template is active")
    is_ats_compliant: bool = Field(False, description="Whether this template is ATS-friendly")
    created_by: Optional[str] = Field(None, description="ID of the user creating the template")


class ResumeTemplateUpdate(BaseModel):
    """Request model for updating a resume template."""

    name: Optional[str] = Field(None, description="Template name", max_length=255)
    description: Optional[str] = Field(None, description="Description of the template style")
    layout_config: Optional[dict] = Field(None, description="Layout configuration")
    style_config: Optional[dict] = Field(None, description="Style configuration")
    section_config: Optional[dict] = Field(None, description="Section configuration")
    preview_url: Optional[str] = Field(None, description="URL to preview image", max_length=512)
    is_default: Optional[bool] = Field(None, description="Whether this is the default template")
    is_active: Optional[bool] = Field(None, description="Whether this template is active")
    is_ats_compliant: Optional[bool] = Field(None, description="Whether this template is ATS-friendly")


class ResumeTemplateResponse(BaseModel):
    """Response model for a resume template."""

    id: str = Field(..., description="Unique identifier for the template")
    organization_id: Optional[str] = Field(None, description="ID of the organization (None for global templates)")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Description of the template style")
    template_type: str = Field(..., description="Type of resume template")
    layout_config: Optional[dict] = Field(None, description="Layout configuration")
    style_config: Optional[dict] = Field(None, description="Style configuration")
    section_config: Optional[dict] = Field(None, description="Section configuration")
    preview_url: Optional[str] = Field(None, description="URL to preview image")
    is_default: bool = Field(..., description="Whether this is the default template")
    is_active: bool = Field(..., description="Whether this template is active")
    is_ats_compliant: bool = Field(..., description="Whether this template is ATS-friendly")
    created_by: Optional[str] = Field(None, description="ID of the user who created the template")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ResumeTemplateListResponse(BaseModel):
    """Response model for listing resume templates."""

    templates: List[ResumeTemplateResponse] = Field(..., description="List of resume templates")
    total_count: int = Field(..., description="Total number of templates")


@router.post(
    "/",
    response_model=ResumeTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resume Templates"],
)
async def create_resume_template(
    request: ResumeTemplateCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a resume template.

    This endpoint creates a new resume template with support for custom layouts,
    styling, and sections. Templates can be organization-specific or global.

    Args:
        request: Create request with resume template details
        db: Database session

    Returns:
        JSON response with created resume template

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Modern Professional",
        ...     "template_type": "modern",
        ...     "description": "Clean modern design with sidebar",
        ...     "is_ats_compliant": True,
        ...     "layout_config": {"margins": "normal", "sections": ["header", "experience", "skills"]},
        ...     "style_config": {"primary_color": "#2563eb", "font": "Arial"}
        ... }
        >>> response = requests.post("http://localhost:8000/api/resume-templates/", json=data)
        >>> response.json()
        {
            "id": "...",
            "name": "Modern Professional",
            "template_type": "modern",
            ...
        }
    """
    try:
        logger.info(f"Creating resume template: {request.name}, type: {request.template_type}")

        # Create new ResumeTemplate instance
        new_template = ResumeTemplate(
            organization_id=request.organization_id,
            name=request.name,
            description=request.description,
            template_type=request.template_type,
            layout_config=request.layout_config,
            style_config=request.style_config,
            section_config=request.section_config,
            preview_url=request.preview_url,
            is_default=request.is_default,
            is_active=request.is_active,
            is_ats_compliant=request.is_ats_compliant,
            created_by=request.created_by,
        )

        # Add to database and commit
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)

        template_response = _template_to_dict(new_template)

        logger.info(f"Created resume template with ID: {template_response['id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=template_response,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error creating resume template: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Failed to create resume template",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating resume template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resume template: {str(e)}",
        ) from e


@router.get("/", tags=["Resume Templates"])
async def list_resume_templates(
    db: AsyncSession = Depends(get_db),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID (None for global templates)"),
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    is_ats_compliant: Optional[bool] = Query(None, description="Filter by ATS compliance"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> JSONResponse:
    """
    List resume templates with optional filters.

    This endpoint retrieves a list of resume templates with support for filtering
    by organization, template type, default status, and ATS compliance.

    Args:
        db: Database session
        organization_id: Optional organization ID filter (None for global templates)
        template_type: Optional template type filter
        is_default: Optional default status filter
        is_active: Optional active status filter (default: true)
        is_ats_compliant: Optional ATS compliance filter
        limit: Maximum number of results to return (default: 100, max: 1000)
        offset: Number of results to skip for pagination (default: 0)

    Returns:
        JSON response with list of resume templates

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/resume-templates/?is_ats_compliant=true")
        >>> response.json()
        {
            "templates": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(f"Listing resume templates with filters: organization_id={organization_id}, template_type={template_type}, is_ats_compliant={is_ats_compliant}")

        # Build query
        stmt = select(ResumeTemplate)

        # Apply filters
        if organization_id is not None:
            stmt = stmt.where(ResumeTemplate.organization_id == organization_id)
        if template_type is not None:
            stmt = stmt.where(ResumeTemplate.template_type == template_type)
        if is_default is not None:
            stmt = stmt.where(ResumeTemplate.is_default == is_default)
        if is_active is not None:
            stmt = stmt.where(ResumeTemplate.is_active == is_active)
        if is_ats_compliant is not None:
            stmt = stmt.where(ResumeTemplate.is_ats_compliant == is_ats_compliant)

        # Get total count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = await db.scalar(count_stmt)

        # Apply pagination and ordering
        stmt = stmt.order_by(ResumeTemplate.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        templates = result.scalars().all()

        response_data = {
            "templates": [_template_to_dict(t) for t in templates],
            "total_count": total_count or 0,
        }

        logger.info(f"Retrieved {response_data['total_count']} resume templates")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error listing resume templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Failed to list resume templates",
        ) from e
    except Exception as e:
        logger.error(f"Error listing resume templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resume templates: {str(e)}",
        ) from e


@router.get("/{template_id}", tags=["Resume Templates"])
async def get_resume_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific resume template by ID.

    This endpoint retrieves a single resume template by its unique identifier,
    including all layout, style, and section configurations.

    Args:
        template_id: Unique identifier of the resume template
        db: Database session

    Returns:
        JSON response with resume template details

    Raises:
        HTTPException(404): If template not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/resume-templates/abc123")
        >>> response.json()
        {
            "id": "abc123",
            "name": "Modern Professional",
            "template_type": "modern",
            ...
        }
    """
    try:
        logger.info(f"Getting resume template: {template_id}")

        # Query for template
        stmt = select(ResumeTemplate).where(ResumeTemplate.id == template_id)
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if template is None:
            logger.warning(f"Resume template not found: {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume template not found: {template_id}",
            )

        template_response = _template_to_dict(template)

        logger.info(f"Retrieved resume template: {template_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=template_response,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting resume template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Failed to get resume template",
        ) from e
    except Exception as e:
        logger.error(f"Error getting resume template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resume template: {str(e)}",
        ) from e


@router.put("/{template_id}", tags=["Resume Templates"])
async def update_resume_template(
    template_id: str,
    request: ResumeTemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a resume template.

    This endpoint updates an existing resume template with new values for
    layout, style, section configurations, or other properties.

    Args:
        template_id: Unique identifier of the resume template
        request: Update request with fields to update
        db: Database session

    Returns:
        JSON response with updated resume template

    Raises:
        HTTPException(404): If template not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Updated Modern Professional",
        ...     "style_config": {"primary_color": "#dc2626", "font": "Helvetica"}
        ... }
        >>> response = requests.put("http://localhost:8000/api/resume-templates/abc123", json=data)
        >>> response.json()
        {
            "id": "abc123",
            "name": "Updated Modern Professional",
            ...
        }
    """
    try:
        logger.info(f"Updating resume template: {template_id}")

        # Query for template
        stmt = select(ResumeTemplate).where(ResumeTemplate.id == template_id)
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if template is None:
            logger.warning(f"Resume template not found for update: {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume template not found: {template_id}",
            )

        # Update only provided fields
        if request.name is not None:
            template.name = request.name
        if request.description is not None:
            template.description = request.description
        if request.layout_config is not None:
            template.layout_config = request.layout_config
        if request.style_config is not None:
            template.style_config = request.style_config
        if request.section_config is not None:
            template.section_config = request.section_config
        if request.preview_url is not None:
            template.preview_url = request.preview_url
        if request.is_default is not None:
            template.is_default = request.is_default
        if request.is_active is not None:
            template.is_active = request.is_active
        if request.is_ats_compliant is not None:
            template.is_ats_compliant = request.is_ats_compliant

        # Commit changes
        await db.commit()
        await db.refresh(template)

        template_response = _template_to_dict(template)

        logger.info(f"Updated resume template: {template_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=template_response,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating resume template: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Failed to update resume template",
        ) from e
    except Exception as e:
        logger.error(f"Error updating resume template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resume template: {str(e)}",
        ) from e


@router.delete("/{template_id}", tags=["Resume Templates"])
async def delete_resume_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a resume template.

    This endpoint permanently deletes a resume template from the system.

    Args:
        template_id: Unique identifier of the resume template
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If template not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/resume-templates/abc123")
        >>> response.json()
        {
            "message": "Resume template deleted successfully",
            "id": "abc123"
        }
    """
    try:
        logger.info(f"Deleting resume template: {template_id}")

        # Query for template
        stmt = select(ResumeTemplate).where(ResumeTemplate.id == template_id)
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if template is None:
            logger.warning(f"Resume template not found for deletion: {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume template not found: {template_id}",
            )

        # Delete the template
        await db.delete(template)
        await db.commit()

        logger.info(f"Deleted resume template: {template_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Resume template deleted successfully",
                "id": template_id,
            },
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting resume template: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Failed to delete resume template",
        ) from e
    except Exception as e:
        logger.error(f"Error deleting resume template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume template: {str(e)}",
        ) from e
