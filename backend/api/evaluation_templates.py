"""
Evaluation template management endpoints.

This module provides endpoints for managing standardized evaluation scorecard templates,
including CRUD operations for creating, reading, updating, and deleting templates with
support for customizable criteria and rating scales.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.evaluation_template import EvaluationTemplate
from models.evaluation_criteria import EvaluationCriteria

logger = logging.getLogger(__name__)

router = APIRouter()


class CriteriaCreate(BaseModel):
    """Request model for creating evaluation criteria."""

    name: str = Field(..., min_length=1, max_length=255, description="Criteria name (e.g., 'Technical Skills')")
    description: Optional[str] = Field(None, description="Description of what this criteria measures")
    type: str = Field("custom", description="Type of criteria (skills, experience, cultural_fit, etc.)")
    weight: float = Field(1.0, ge=0, le=1, description="Weight for this criteria in aggregate scoring (0.0-1.0)")
    rating_scale: Optional[str] = Field(None, description="Rating scale (e.g., '1-5')")
    min_score: Optional[int] = Field(1, ge=0, description="Minimum score for this criteria's rating scale")
    max_score: Optional[int] = Field(5, ge=1, description="Maximum score for this criteria's rating scale")
    rating_scale_description: Optional[str] = Field(None, description="Description of rating scale (e.g., '1-5, Poor to Excellent')")
    display_order: int = Field(0, ge=0, description="Order to display this criteria in the template")
    extra_metadata: Optional[dict] = Field(None, description="Additional criteria configuration")


class EvaluationTemplateCreate(BaseModel):
    """Request model for creating an evaluation template."""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Description of when to use this template")
    organization_id: str = Field(..., description="Organization ID that owns this template")
    vacancy_id: Optional[str] = Field(None, description="Optional vacancy ID for role-specific templates")
    is_default: bool = Field(False, description="Whether this is the default template")
    created_by: Optional[str] = Field(None, description="User ID who created this template")
    criteria: List[CriteriaCreate] = Field(..., min_length=1, description="List of evaluation criteria")


class CriteriaUpdate(BaseModel):
    """Request model for updating evaluation criteria."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Criteria name")
    description: Optional[str] = Field(None, description="Description of what this criteria measures")
    type: Optional[str] = Field(None, description="Type of criteria")
    weight: Optional[float] = Field(None, ge=0, le=1, description="Weight for this criteria")
    rating_scale: Optional[str] = Field(None, description="Rating scale (e.g., '1-5')")
    min_score: Optional[int] = Field(None, ge=0, description="Minimum score")
    max_score: Optional[int] = Field(None, ge=1, description="Maximum score")
    rating_scale_description: Optional[str] = Field(None, description="Description of rating scale")
    display_order: Optional[int] = Field(None, ge=0, description="Display order")
    extra_metadata: Optional[dict] = Field(None, description="Additional criteria configuration")


class EvaluationTemplateUpdate(BaseModel):
    """Request model for updating an evaluation template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    is_active: Optional[bool] = Field(None, description="Whether this template is active")
    is_default: Optional[bool] = Field(None, description="Whether this is the default template")
    criteria: Optional[List[CriteriaUpdate]] = Field(None, description="List of criteria to update")


class CriteriaResponse(BaseModel):
    """Response model for evaluation criteria."""

    id: str = Field(..., description="Unique identifier for the criteria")
    template_id: str = Field(..., description="Template ID this criteria belongs to")
    name: str = Field(..., description="Criteria name")
    description: Optional[str] = Field(None, description="Criteria description")
    criteria_type: str = Field(..., description="Criteria type")
    weight: float = Field(..., description="Criteria weight")
    min_score: int = Field(..., description="Minimum score")
    max_score: int = Field(..., description="Maximum score")
    rating_scale_description: Optional[str] = Field(None, description="Rating scale description")
    display_order: int = Field(..., description="Display order")
    extra_metadata: Optional[dict] = Field(None, description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class EvaluationTemplateResponse(BaseModel):
    """Response model for an evaluation template."""

    id: str = Field(..., description="Unique identifier for the template")
    organization_id: str = Field(..., description="Organization ID")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID if role-specific")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    version: int = Field(..., description="Template version")
    is_active: bool = Field(..., description="Whether template is active")
    is_default: bool = Field(..., description="Whether this is the default template")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    criteria: List[CriteriaResponse] = Field(..., description="List of evaluation criteria")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class EvaluationTemplateListResponse(BaseModel):
    """Response model for listing evaluation templates."""

    organization_id: Optional[str] = Field(None, description="Organization ID filter")
    templates: List[EvaluationTemplateResponse] = Field(..., description="List of evaluation templates")
    total_count: int = Field(..., description="Total number of templates")


class TemplateVersionResponse(BaseModel):
    """Response model for a template version."""

    id: str = Field(..., description="Unique identifier for this version")
    organization_id: str = Field(..., description="Organization ID")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID if role-specific")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    version: int = Field(..., description="Version number")
    is_active: bool = Field(..., description="Whether template is active")
    is_default: bool = Field(..., description="Whether this is the default template")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class TemplateVersionListResponse(BaseModel):
    """Response model for listing template versions."""

    template_id: str = Field(..., description="ID of the template entry")
    name: str = Field(..., description="Template name")
    organization_id: str = Field(..., description="Organization ID")
    versions: List[TemplateVersionResponse] = Field(..., description="List of all versions")
    total_count: int = Field(..., description="Total number of versions")


class TemplateVersionCreate(BaseModel):
    """Request model for creating a new version."""

    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    is_active: Optional[bool] = Field(None, description="Whether template is active")
    is_default: Optional[bool] = Field(None, description="Whether this is the default template")


class TemplateClone(BaseModel):
    """Request model for cloning a template."""

    name: str = Field(..., min_length=1, max_length=255, description="Name for the cloned template")
    description: Optional[str] = Field(None, description="Optional description for the cloned template")


@router.post(
    "/",
    response_model=EvaluationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Evaluation Templates"],
)
async def create_evaluation_template(
    request: EvaluationTemplateCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create an evaluation template.

    This endpoint creates a new evaluation template with customizable criteria
    for standardized candidate evaluations. Templates can be organization-wide
    or tied to specific job vacancies.

    Args:
        request: Request body containing template details and criteria
        db: Database session

    Returns:
        JSON response with created template details and criteria

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/evaluation-templates/",
        ...     json={
        ...         "name": "Technical Interview Template",
        ...         "description": "Template for evaluating technical skills",
        ...         "organization_id": "org-123",
        ...         "criteria": [
        ...             {
        ...                 "name": "Technical Skills",
        ...                 "description": "Core technical abilities",
        ...                 "type": "skills",
        ...                 "weight": 0.4,
        ...                 "rating_scale": "1-5"
        ...             }
        ...         ]
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating evaluation template: {request.name} for org: {request.organization_id}")

        # Create new template
        new_template = EvaluationTemplate(
            organization_id=request.organization_id,
            vacancy_id=UUID(request.vacancy_id) if request.vacancy_id else None,
            name=request.name,
            description=request.description,
            is_default=request.is_default,
            created_by=request.created_by,
        )
        db.add(new_template)
        await db.flush()

        # Create criteria
        criteria_list = []
        for criteria_data in request.criteria:
            # Parse rating_scale if provided (e.g., "1-5" -> min=1, max=5)
            min_score = criteria_data.min_score
            max_score = criteria_data.max_score
            if criteria_data.rating_scale:
                try:
                    parts = criteria_data.rating_scale.split("-")
                    if len(parts) == 2:
                        min_score = int(parts[0].strip())
                        max_score = int(parts[1].strip())
                except (ValueError, IndexError):
                    pass

            new_criteria = EvaluationCriteria(
                template_id=new_template.id,
                name=criteria_data.name,
                description=criteria_data.description,
                criteria_type=criteria_data.type,
                weight=criteria_data.weight,
                min_score=min_score,
                max_score=max_score,
                rating_scale_description=criteria_data.rating_scale_description or criteria_data.rating_scale,
                display_order=criteria_data.display_order,
                extra_metadata=criteria_data.extra_metadata,
            )
            db.add(new_criteria)
            criteria_list.append(new_criteria)

        await db.flush()

        # Build response
        criteria_response = [
            {
                "id": str(c.id),
                "template_id": str(c.template_id),
                "name": c.name,
                "description": c.description,
                "criteria_type": c.criteria_type,
                "weight": float(c.weight),
                "min_score": c.min_score,
                "max_score": c.max_score,
                "rating_scale_description": c.rating_scale_description,
                "display_order": c.display_order,
                "extra_metadata": c.extra_metadata,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in criteria_list
        ]

        response_data = {
            "id": str(new_template.id),
            "organization_id": new_template.organization_id,
            "vacancy_id": str(new_template.vacancy_id) if new_template.vacancy_id else None,
            "name": new_template.name,
            "description": new_template.description,
            "version": new_template.version,
            "is_active": new_template.is_active,
            "is_default": new_template.is_default,
            "created_by": new_template.created_by,
            "criteria": criteria_response,
            "created_at": new_template.created_at.isoformat(),
            "updated_at": new_template.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created evaluation template with ID: {new_template.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error creating evaluation template: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create evaluation template: {str(e)}",
        ) from e


@router.get("/", tags=["Evaluation Templates"])
async def list_evaluation_templates(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List evaluation templates with optional filters.

    This endpoint retrieves evaluation templates with support for filtering
    by organization, vacancy, and status.

    Args:
        organization_id: Optional organization ID filter
        vacancy_id: Optional vacancy ID filter
        is_active: Optional active status filter
        is_default: Optional default status filter
        db: Database session

    Returns:
        JSON response with list of templates

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/evaluation-templates/?organization_id=org-123")
        >>> response.json()
        {
            "organization_id": "org-123",
            "templates": [...],
            "total_count": 2
        }
    """
    try:
        logger.info(f"Listing evaluation templates with filters - organization_id: {organization_id}, vacancy_id: {vacancy_id}")

        # Build query
        query = select(EvaluationTemplate)

        if organization_id:
            query = query.where(EvaluationTemplate.organization_id == organization_id)
        if vacancy_id:
            query = query.where(EvaluationTemplate.vacancy_id == UUID(vacancy_id))
        if is_active is not None:
            query = query.where(EvaluationTemplate.is_active == is_active)
        if is_default is not None:
            query = query.where(EvaluationTemplate.is_default == is_default)

        query = query.order_by(EvaluationTemplate.created_at.desc())

        result = await db.execute(query)
        templates = result.scalars().all()

        # If organization_id filter was provided, use it in response
        response_org_id = organization_id if organization_id and len(templates) > 0 else "all"

        # Build response with criteria
        templates_data = []
        for template in templates:
            # Get criteria for this template
            criteria_result = await db.execute(
                select(EvaluationCriteria)
                .where(EvaluationCriteria.template_id == template.id)
                .order_by(EvaluationCriteria.display_order)
            )
            criteria_list = criteria_result.scalars().all()

            criteria_response = [
                {
                    "id": str(c.id),
                    "template_id": str(c.template_id),
                    "name": c.name,
                    "description": c.description,
                    "criteria_type": c.criteria_type,
                    "weight": float(c.weight),
                    "min_score": c.min_score,
                    "max_score": c.max_score,
                    "rating_scale_description": c.rating_scale_description,
                    "display_order": c.display_order,
                    "extra_metadata": c.extra_metadata,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                }
                for c in criteria_list
            ]

            templates_data.append({
                "id": str(template.id),
                "organization_id": template.organization_id,
                "vacancy_id": str(template.vacancy_id) if template.vacancy_id else None,
                "name": template.name,
                "description": template.description,
                "version": template.version,
                "is_active": template.is_active,
                "is_default": template.is_default,
                "created_by": template.created_by,
                "criteria": criteria_response,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat(),
            })

        response_data = {
            "organization_id": response_org_id,
            "templates": templates_data,
            "total_count": len(templates_data),
        }

        logger.info(f"Retrieved {len(templates_data)} evaluation templates")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error listing evaluation templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list evaluation templates: {str(e)}",
        ) from e


@router.get("/{template_id}", tags=["Evaluation Templates"])
async def get_evaluation_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific evaluation template by ID.

    This endpoint retrieves detailed information about a single template
    including all its criteria.

    Args:
        template_id: UUID of the template
        db: Database session

    Returns:
        JSON response with template details

    Raises:
        HTTPException(404): If template is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/evaluation-templates/template-uuid")
        >>> response.json()
        {
            "id": "template-uuid",
            "name": "Technical Interview Template",
            "criteria": [...]
        }
    """
    try:
        logger.info(f"Retrieving evaluation template: {template_id}")

        result = await db.execute(
            select(EvaluationTemplate).where(EvaluationTemplate.id == UUID(template_id))
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation template not found: {template_id}",
            )

        # Get criteria for this template
        criteria_result = await db.execute(
            select(EvaluationCriteria)
            .where(EvaluationCriteria.template_id == template.id)
            .order_by(EvaluationCriteria.display_order)
        )
        criteria_list = criteria_result.scalars().all()

        criteria_response = [
            {
                "id": str(c.id),
                "template_id": str(c.template_id),
                "name": c.name,
                "description": c.description,
                "criteria_type": c.criteria_type,
                "weight": float(c.weight),
                "min_score": c.min_score,
                "max_score": c.max_score,
                "rating_scale_description": c.rating_scale_description,
                "display_order": c.display_order,
                "extra_metadata": c.extra_metadata,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in criteria_list
        ]

        response_data = {
            "id": str(template.id),
            "organization_id": template.organization_id,
            "vacancy_id": str(template.vacancy_id) if template.vacancy_id else None,
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "is_active": template.is_active,
            "is_default": template.is_default,
            "created_by": template.created_by,
            "criteria": criteria_response,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
        }

        logger.info(f"Retrieved evaluation template: {template_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {template_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving evaluation template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evaluation template: {str(e)}",
        ) from e


@router.put("/{template_id}", tags=["Evaluation Templates"])
async def update_evaluation_template(
    template_id: str,
    request: EvaluationTemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an evaluation template.

    This endpoint updates an existing evaluation template.
    Only the fields specified in the request body will be updated.
    Note: Updating criteria replaces all existing criteria.

    Args:
        template_id: UUID of the template
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated template details

    Raises:
        HTTPException(404): If template is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/evaluation-templates/template-uuid",
        ...     json={
        ...         "name": "Updated Template Name",
        ...         "is_active": false
        ...     }
        ... )
        >>> response.json()
        {
            "id": "template-uuid",
            "name": "Updated Template Name",
            ...
        }
    """
    try:
        logger.info(f"Updating evaluation template: {template_id}")

        # Get existing template
        result = await db.execute(
            select(EvaluationTemplate).where(EvaluationTemplate.id == UUID(template_id))
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation template not found: {template_id}",
            )

        # Update fields if provided
        if request.name is not None:
            template.name = request.name
        if request.description is not None:
            template.description = request.description
        if request.is_active is not None:
            template.is_active = request.is_active
        if request.is_default is not None:
            template.is_default = request.is_default

        # Update criteria if provided (replace all existing criteria)
        if request.criteria is not None:
            # Delete existing criteria
            await db.execute(
                delete(EvaluationCriteria).where(EvaluationCriteria.template_id == template.id)
            )

            # Create new criteria
            criteria_list = []
            for criteria_data in request.criteria:
                # Parse rating_scale if provided
                min_score = criteria_data.min_score if criteria_data.min_score is not None else 1
                max_score = criteria_data.max_score if criteria_data.max_score is not None else 5
                if criteria_data.rating_scale:
                    try:
                        parts = criteria_data.rating_scale.split("-")
                        if len(parts) == 2:
                            min_score = int(parts[0].strip())
                            max_score = int(parts[1].strip())
                    except (ValueError, IndexError):
                        pass

                new_criteria = EvaluationCriteria(
                    template_id=template.id,
                    name=criteria_data.name if criteria_data.name is not None else "Unnamed Criteria",
                    description=criteria_data.description,
                    criteria_type=criteria_data.type if criteria_data.type is not None else "custom",
                    weight=criteria_data.weight if criteria_data.weight is not None else 1.0,
                    min_score=min_score,
                    max_score=max_score,
                    rating_scale_description=criteria_data.rating_scale_description or criteria_data.rating_scale,
                    display_order=criteria_data.display_order if criteria_data.display_order is not None else 0,
                    extra_metadata=criteria_data.extra_metadata,
                )
                db.add(new_criteria)
                criteria_list.append(new_criteria)

            await db.flush()

        await db.commit()
        await db.refresh(template)

        # Get criteria for response
        criteria_result = await db.execute(
            select(EvaluationCriteria)
            .where(EvaluationCriteria.template_id == template.id)
            .order_by(EvaluationCriteria.display_order)
        )
        criteria_list = criteria_result.scalars().all()

        criteria_response = [
            {
                "id": str(c.id),
                "template_id": str(c.template_id),
                "name": c.name,
                "description": c.description,
                "criteria_type": c.criteria_type,
                "weight": float(c.weight),
                "min_score": c.min_score,
                "max_score": c.max_score,
                "rating_scale_description": c.rating_scale_description,
                "display_order": c.display_order,
                "extra_metadata": c.extra_metadata,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in criteria_list
        ]

        response_data = {
            "id": str(template.id),
            "organization_id": template.organization_id,
            "vacancy_id": str(template.vacancy_id) if template.vacancy_id else None,
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "is_active": template.is_active,
            "is_default": template.is_default,
            "created_by": template.created_by,
            "criteria": criteria_response,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
        }

        logger.info(f"Updated evaluation template: {template_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {template_id}",
        )
    except Exception as e:
        logger.error(f"Error updating evaluation template: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update evaluation template: {str(e)}",
        ) from e


@router.delete("/{template_id}", tags=["Evaluation Templates"])
async def delete_evaluation_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete an evaluation template.

    This endpoint permanently deletes an evaluation template and all its criteria.
    This action cannot be undone.

    Args:
        template_id: UUID of the template
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If template is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/evaluation-templates/template-uuid")
        >>> response.json()
        {
            "message": "Evaluation template deleted successfully",
            "id": "template-uuid"
        }
    """
    try:
        logger.info(f"Deleting evaluation template: {template_id}")

        # Check if template exists
        result = await db.execute(
            select(EvaluationTemplate).where(EvaluationTemplate.id == UUID(template_id))
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation template not found: {template_id}",
            )

        # Delete the template (criteria will be cascade deleted)
        await db.execute(
            delete(EvaluationTemplate).where(EvaluationTemplate.id == UUID(template_id))
        )
        await db.commit()

        logger.info(f"Deleted evaluation template: {template_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Evaluation template deleted successfully",
                "id": template_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {template_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting evaluation template: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete evaluation template: {str(e)}",
        ) from e


def template_model_to_dict(template: EvaluationTemplate) -> dict:
    """Convert EvaluationTemplate model to dictionary."""
    return {
        "id": str(template.id),
        "organization_id": template.organization_id,
        "vacancy_id": str(template.vacancy_id) if template.vacancy_id else None,
        "name": template.name,
        "description": template.description,
        "version": template.version,
        "is_active": template.is_active,
        "is_default": template.is_default,
        "created_by": template.created_by,
        "created_at": template.created_at.isoformat() if template.created_at else "",
        "updated_at": template.updated_at.isoformat() if template.updated_at else "",
    }


@router.post("/{template_id}/versions", response_model=EvaluationTemplateResponse, status_code=status.HTTP_201_CREATED, tags=["Evaluation Templates"])
async def create_template_version(
    template_id: str,
    request: TemplateVersionCreate,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new version of an evaluation template.

    This endpoint creates a new version of an existing template,
    preserving the previous version. The new version will have
    an incremented version number and will include all criteria
    from the original template.

    Args:
        template_id: ID of the template to version
        request: Update request with fields to modify in the new version
        db: Database session

    Returns:
        JSON response with the newly created version

    Raises:
        HTTPException(404): If template is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Updated Technical Template",
        ...     "description": "Updated description"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/evaluation-templates/123/versions",
        ...     json=data
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating new version for template: {template_id}")

        # Query the template with the highest version number for this template name/org
        query = select(EvaluationTemplate).where(
            EvaluationTemplate.id == UUID(template_id)
        )
        result = await db.execute(query)
        current_template = result.scalar_one_or_none()

        if not current_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found",
            )

        # Find the highest version number for templates with the same name/org
        version_query = select(EvaluationTemplate).where(
            EvaluationTemplate.organization_id == current_template.organization_id,
            EvaluationTemplate.name == current_template.name
        )
        if current_template.vacancy_id:
            version_query = version_query.where(EvaluationTemplate.vacancy_id == current_template.vacancy_id)
        else:
            version_query = version_query.where(EvaluationTemplate.vacancy_id == None)

        version_query = version_query.order_by(EvaluationTemplate.version.desc())
        version_result = await db.execute(version_query)
        latest_version = version_result.scalar_one_or_none()

        # Determine new version number
        new_version_number = (latest_version.version + 1) if latest_version else 1

        # Get current criteria
        criteria_result = await db.execute(
            select(EvaluationCriteria)
            .where(EvaluationCriteria.template_id == current_template.id)
            .order_by(EvaluationCriteria.display_order)
        )
        current_criteria = criteria_result.scalars().all()

        # Create new version
        new_version = EvaluationTemplate(
            organization_id=current_template.organization_id,
            vacancy_id=current_template.vacancy_id,
            name=request.name if request.name is not None else current_template.name,
            description=request.description if request.description is not None else current_template.description,
            is_active=request.is_active if request.is_active is not None else current_template.is_active,
            is_default=request.is_default if request.is_default is not None else False,
            created_by=current_template.created_by,
            version=new_version_number,
        )

        db.add(new_version)
        await db.flush()

        # Copy criteria to new version
        criteria_list = []
        for criteria in current_criteria:
            new_criteria = EvaluationCriteria(
                template_id=new_version.id,
                name=criteria.name,
                description=criteria.description,
                criteria_type=criteria.criteria_type,
                weight=criteria.weight,
                min_score=criteria.min_score,
                max_score=criteria.max_score,
                rating_scale_description=criteria.rating_scale_description,
                display_order=criteria.display_order,
                extra_metadata=criteria.extra_metadata,
            )
            db.add(new_criteria)
            criteria_list.append(new_criteria)

        await db.commit()
        await db.refresh(new_version)

        logger.info(f"Created version {new_version_number} for template {template_id}")

        # Build response
        criteria_response = [
            {
                "id": str(c.id),
                "template_id": str(c.template_id),
                "name": c.name,
                "description": c.description,
                "criteria_type": c.criteria_type,
                "weight": float(c.weight),
                "min_score": c.min_score,
                "max_score": c.max_score,
                "rating_scale_description": c.rating_scale_description,
                "display_order": c.display_order,
                "extra_metadata": c.extra_metadata,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in criteria_list
        ]

        response_data = {
            "id": str(new_version.id),
            "organization_id": new_version.organization_id,
            "vacancy_id": str(new_version.vacancy_id) if new_version.vacancy_id else None,
            "name": new_version.name,
            "description": new_version.description,
            "version": new_version.version,
            "is_active": new_version.is_active,
            "is_default": new_version.is_default,
            "created_by": new_version.created_by,
            "criteria": criteria_response,
            "created_at": new_version.created_at.isoformat(),
            "updated_at": new_version.updated_at.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid template ID format: {template_id}",
        )
    except Exception as e:
        logger.error(f"Error creating template version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template version: {str(e)}",
        ) from e


@router.get("/{template_id}/versions", response_model=TemplateVersionListResponse, tags=["Evaluation Templates"])
async def list_template_versions(
    template_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all versions of an evaluation template.

    This endpoint retrieves all versions of a template with the same
    name and organization, ordered by version number (newest first).

    Args:
        template_id: ID of the template
        db: Database session

    Returns:
        JSON response with list of all versions

    Raises:
        HTTPException(404): If template is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/evaluation-templates/123/versions")
        >>> response.json()
        {
            "template_id": "123",
            "name": "Technical Template",
            "organization_id": "org-123",
            "versions": [...],
            "total_count": 3
        }
    """
    try:
        logger.info(f"Listing versions for template: {template_id}")

        # Get the reference template
        query = select(EvaluationTemplate).where(
            EvaluationTemplate.id == UUID(template_id)
        )
        result = await db.execute(query)
        reference_template = result.scalar_one_or_none()

        if not reference_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found",
            )

        # Get all versions with the same name and organization
        versions_query = select(EvaluationTemplate).where(
            EvaluationTemplate.organization_id == reference_template.organization_id,
            EvaluationTemplate.name == reference_template.name
        )
        if reference_template.vacancy_id:
            versions_query = versions_query.where(EvaluationTemplate.vacancy_id == reference_template.vacancy_id)
        else:
            versions_query = versions_query.where(EvaluationTemplate.vacancy_id == None)

        versions_query = versions_query.order_by(EvaluationTemplate.version.desc())
        versions_result = await db.execute(versions_query)
        all_versions = versions_result.scalars().all()

        # Convert to response format
        versions_response = [template_model_to_dict(version) for version in all_versions]

        response_data = {
            "template_id": template_id,
            "name": reference_template.name,
            "organization_id": reference_template.organization_id,
            "versions": versions_response,
            "total_count": len(versions_response),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid template ID format: {template_id}",
        )
    except Exception as e:
        logger.error(f"Error listing template versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list template versions: {str(e)}",
        ) from e


@router.post("/{template_id}/clone", response_model=EvaluationTemplateResponse, status_code=status.HTTP_201_CREATED, tags=["Evaluation Templates"])
async def clone_template(
    template_id: str,
    request: TemplateClone,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Clone an evaluation template.

    This endpoint creates a new independent copy of an existing template
    with a new name. All criteria from the original template are copied
    to the new clone.

    Args:
        template_id: ID of the template to clone
        request: Clone request with new name and optional description
        db: Database session

    Returns:
        JSON response with the newly created clone

    Raises:
        HTTPException(404): If template is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Cloned Template",
        ...     "description": "A copy of the original template"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/evaluation-templates/123/clone",
        ...     json=data
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Cloning template: {template_id} to new name: {request.name}")

        # Get the source template
        query = select(EvaluationTemplate).where(
            EvaluationTemplate.id == UUID(template_id)
        )
        result = await db.execute(query)
        source_template = result.scalar_one_or_none()

        if not source_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found",
            )

        # Get source criteria
        criteria_result = await db.execute(
            select(EvaluationCriteria)
            .where(EvaluationCriteria.template_id == source_template.id)
            .order_by(EvaluationCriteria.display_order)
        )
        source_criteria = criteria_result.scalars().all()

        # Create cloned template
        cloned_template = EvaluationTemplate(
            organization_id=source_template.organization_id,
            vacancy_id=source_template.vacancy_id,
            name=request.name,
            description=request.description or source_template.description,
            is_default=False,  # Cloned templates are never default
            created_by=source_template.created_by,
            version=1,  # Start at version 1 for new clones
        )

        db.add(cloned_template)
        await db.flush()

        # Clone criteria
        criteria_list = []
        for criteria in source_criteria:
            cloned_criteria = EvaluationCriteria(
                template_id=cloned_template.id,
                name=criteria.name,
                description=criteria.description,
                criteria_type=criteria.criteria_type,
                weight=criteria.weight,
                min_score=criteria.min_score,
                max_score=criteria.max_score,
                rating_scale_description=criteria.rating_scale_description,
                display_order=criteria.display_order,
                extra_metadata=criteria.extra_metadata,
            )
            db.add(cloned_criteria)
            criteria_list.append(cloned_criteria)

        await db.commit()
        await db.refresh(cloned_template)

        logger.info(f"Cloned template {template_id} to new template {cloned_template.id}")

        # Build response
        criteria_response = [
            {
                "id": str(c.id),
                "template_id": str(c.template_id),
                "name": c.name,
                "description": c.description,
                "criteria_type": c.criteria_type,
                "weight": float(c.weight),
                "min_score": c.min_score,
                "max_score": c.max_score,
                "rating_scale_description": c.rating_scale_description,
                "display_order": c.display_order,
                "extra_metadata": c.extra_metadata,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in criteria_list
        ]

        response_data = {
            "id": str(cloned_template.id),
            "organization_id": cloned_template.organization_id,
            "vacancy_id": str(cloned_template.vacancy_id) if cloned_template.vacancy_id else None,
            "name": cloned_template.name,
            "description": cloned_template.description,
            "version": cloned_template.version,
            "is_active": cloned_template.is_active,
            "is_default": cloned_template.is_default,
            "created_by": cloned_template.created_by,
            "criteria": criteria_response,
            "created_at": cloned_template.created_at.isoformat(),
            "updated_at": cloned_template.updated_at.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid template ID format: {template_id}",
        )
    except Exception as e:
        logger.error(f"Error cloning template: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone template: {str(e)}",
        ) from e
