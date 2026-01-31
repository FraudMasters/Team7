"""
Workflow stage configuration management endpoints.

This module provides endpoints for managing organization-specific hiring workflow stages,
including CRUD operations for creating, reading, updating, and deleting workflow stage
configurations with customizable names, order, colors, and descriptions.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models.workflow_stage_config import WorkflowStageConfig
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class WorkflowStageCreate(BaseModel):
    """Request model for creating a workflow stage."""

    organization_id: str = Field(..., description="Organization ID that owns this workflow stage")
    stage_name: str = Field(..., min_length=1, max_length=100, description="Name of the workflow stage")
    stage_order: int = Field(..., ge=0, description="Order of this stage in the workflow")
    is_default: bool = Field(False, description="Whether this is a default stage for new organizations")
    is_active: bool = Field(True, description="Whether this stage is currently active")
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Hex color code for UI display (e.g., #3B82F6)")
    description: Optional[str] = Field(None, max_length=500, description="Description of what happens in this stage")


class WorkflowStageUpdate(BaseModel):
    """Request model for updating a workflow stage."""

    stage_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the workflow stage")
    stage_order: Optional[int] = Field(None, ge=0, description="Order of this stage in the workflow")
    is_default: Optional[bool] = Field(None, description="Whether this is a default stage for new organizations")
    is_active: Optional[bool] = Field(None, description="Whether this stage is currently active")
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Hex color code for UI display")
    description: Optional[str] = Field(None, max_length=500, description="Description of what happens in this stage")


class WorkflowStageResponse(BaseModel):
    """Response model for a single workflow stage."""

    id: str = Field(..., description="Unique identifier for the workflow stage")
    organization_id: str = Field(..., description="Organization ID that owns this workflow stage")
    stage_name: str = Field(..., description="Name of the workflow stage")
    stage_order: int = Field(..., description="Order of this stage in the workflow")
    is_default: bool = Field(..., description="Whether this is a default stage")
    is_active: bool = Field(..., description="Whether this stage is currently active")
    color: Optional[str] = Field(None, description="Hex color code for UI display")
    description: Optional[str] = Field(None, description="Description of what happens in this stage")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class WorkflowStageListResponse(BaseModel):
    """Response model for listing workflow stages."""

    organization_id: str = Field(..., description="Organization ID")
    stages: List[WorkflowStageResponse] = Field(..., description="List of workflow stages")
    total_count: int = Field(..., description="Total number of stages")


@router.post(
    "/",
    response_model=WorkflowStageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Workflow Stages"],
)
async def create_workflow_stage(
    request: WorkflowStageCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a workflow stage for an organization.

    This endpoint creates a new workflow stage configuration for a specific organization,
    allowing customization of the hiring pipeline with stage names, order, colors, and descriptions.

    Args:
        request: Request body containing workflow stage details
        db: Database session

    Returns:
        JSON response with created workflow stage details

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/workflow-stages/",
        ...     json={
        ...         "organization_id": "org-123",
        ...         "stage_name": "Technical Interview",
        ...         "stage_order": 3,
        ...         "is_default": False,
        ...         "is_active": True,
        ...         "color": "#3B82F6",
        ...         "description": "Technical assessment with engineering team"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "stage-uuid",
            "organization_id": "org-123",
            "stage_name": "Technical Interview",
            "stage_order": 3,
            "is_default": false,
            "is_active": true,
            "color": "#3B82F6",
            "description": "Technical assessment with engineering team",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
    """
    try:
        logger.info(f"Creating workflow stage '{request.stage_name}' for organization: {request.organization_id}")

        # Check if stage with same name already exists for this organization
        existing = await db.execute(
            select(WorkflowStageConfig).where(
                WorkflowStageConfig.organization_id == request.organization_id,
                WorkflowStageConfig.stage_name == request.stage_name,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workflow stage '{request.stage_name}' already exists for this organization",
            )

        # Create new workflow stage
        new_stage = WorkflowStageConfig(
            organization_id=request.organization_id,
            stage_name=request.stage_name,
            stage_order=request.stage_order,
            is_default=request.is_default,
            is_active=request.is_active,
            color=request.color,
            description=request.description,
        )
        db.add(new_stage)
        await db.flush()

        response_data = {
            "id": str(new_stage.id),
            "organization_id": new_stage.organization_id,
            "stage_name": new_stage.stage_name,
            "stage_order": new_stage.stage_order,
            "is_default": new_stage.is_default,
            "is_active": new_stage.is_active,
            "color": new_stage.color,
            "description": new_stage.description,
            "created_at": new_stage.created_at.isoformat(),
            "updated_at": new_stage.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created workflow stage '{request.stage_name}' with ID: {new_stage.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow stage: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow stage: {str(e)}",
        ) from e


@router.get("/", tags=["Workflow Stages"])
async def list_workflow_stages(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List workflow stages with optional filters.

    This endpoint retrieves workflow stage configurations with support for
    filtering by organization, active status, and default status.

    Args:
        organization_id: Optional organization ID filter
        is_active: Optional active status filter
        is_default: Optional default status filter
        db: Database session

    Returns:
        JSON response with list of workflow stages

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/workflow-stages/?organization_id=org-123")
        >>> response.json()
        {
            "organization_id": "org-123",
            "stages": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(f"Listing workflow stages with filters - organization_id: {organization_id}, is_active: {is_active}")

        # Build query
        query = select(WorkflowStageConfig)

        if organization_id:
            query = query.where(WorkflowStageConfig.organization_id == organization_id)
        if is_active is not None:
            query = query.where(WorkflowStageConfig.is_active == is_active)
        if is_default is not None:
            query = query.where(WorkflowStageConfig.is_default == is_default)

        query = query.order_by(WorkflowStageConfig.stage_order, WorkflowStageConfig.stage_name)

        result = await db.execute(query)
        stages = result.scalars().all()

        # If organization_id filter was provided, use it in response
        response_org_id = organization_id if organization_id and len(stages) > 0 else "all"

        # Build response
        stages_data = []
        for stage in stages:
            stages_data.append({
                "id": str(stage.id),
                "organization_id": stage.organization_id,
                "stage_name": stage.stage_name,
                "stage_order": stage.stage_order,
                "is_default": stage.is_default,
                "is_active": stage.is_active,
                "color": stage.color,
                "description": stage.description,
                "created_at": stage.created_at.isoformat(),
                "updated_at": stage.updated_at.isoformat(),
            })

        response_data = {
            "organization_id": response_org_id,
            "stages": stages_data,
            "total_count": len(stages_data),
        }

        logger.info(f"Retrieved {len(stages_data)} workflow stages")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing workflow stages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflow stages: {str(e)}",
        ) from e


@router.get("/{stage_id}", tags=["Workflow Stages"])
async def get_workflow_stage(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific workflow stage by ID.

    This endpoint retrieves detailed information about a single workflow stage.

    Args:
        stage_id: UUID of the workflow stage
        db: Database session

    Returns:
        JSON response with workflow stage details

    Raises:
        HTTPException(404): If workflow stage is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/workflow-stages/stage-uuid")
        >>> response.json()
        {
            "id": "stage-uuid",
            "organization_id": "org-123",
            "stage_name": "Technical Interview",
            ...
        }
    """
    try:
        logger.info(f"Retrieving workflow stage: {stage_id}")

        result = await db.execute(
            select(WorkflowStageConfig).where(WorkflowStageConfig.id == UUID(stage_id))
        )
        stage = result.scalar_one_or_none()

        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow stage not found: {stage_id}",
            )

        response_data = {
            "id": str(stage.id),
            "organization_id": stage.organization_id,
            "stage_name": stage.stage_name,
            "stage_order": stage.stage_order,
            "is_default": stage.is_default,
            "is_active": stage.is_active,
            "color": stage.color,
            "description": stage.description,
            "created_at": stage.created_at.isoformat(),
            "updated_at": stage.updated_at.isoformat(),
        }

        logger.info(f"Retrieved workflow stage: {stage_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {stage_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving workflow stage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow stage: {str(e)}",
        ) from e


@router.put("/{stage_id}", tags=["Workflow Stages"])
async def update_workflow_stage(
    stage_id: str,
    request: WorkflowStageUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a workflow stage.

    This endpoint updates an existing workflow stage configuration.
    Only the fields specified in the request body will be updated.

    Args:
        stage_id: UUID of the workflow stage
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated workflow stage details

    Raises:
        HTTPException(404): If workflow stage is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/workflow-stages/stage-uuid",
        ...     json={
        ...         "stage_name": "Updated Technical Interview",
        ...         "is_active": False
        ...     }
        ... )
        >>> response.json()
        {
            "id": "stage-uuid",
            "stage_name": "Updated Technical Interview",
            "is_active": false,
            ...
        }
    """
    try:
        logger.info(f"Updating workflow stage: {stage_id}")

        # Get existing stage
        result = await db.execute(
            select(WorkflowStageConfig).where(WorkflowStageConfig.id == UUID(stage_id))
        )
        stage = result.scalar_one_or_none()

        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow stage not found: {stage_id}",
            )

        # Update fields if provided
        if request.stage_name is not None:
            # Check if new name conflicts with existing stage
            existing = await db.execute(
                select(WorkflowStageConfig).where(
                    WorkflowStageConfig.organization_id == stage.organization_id,
                    WorkflowStageConfig.stage_name == request.stage_name,
                    WorkflowStageConfig.id != UUID(stage_id),
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Workflow stage '{request.stage_name}' already exists for this organization",
                )
            stage.stage_name = request.stage_name

        if request.stage_order is not None:
            stage.stage_order = request.stage_order
        if request.is_default is not None:
            stage.is_default = request.is_default
        if request.is_active is not None:
            stage.is_active = request.is_active
        if request.color is not None:
            stage.color = request.color
        if request.description is not None:
            stage.description = request.description

        await db.commit()
        await db.refresh(stage)

        response_data = {
            "id": str(stage.id),
            "organization_id": stage.organization_id,
            "stage_name": stage.stage_name,
            "stage_order": stage.stage_order,
            "is_default": stage.is_default,
            "is_active": stage.is_active,
            "color": stage.color,
            "description": stage.description,
            "created_at": stage.created_at.isoformat(),
            "updated_at": stage.updated_at.isoformat(),
        }

        logger.info(f"Updated workflow stage: {stage_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {stage_id}",
        )
    except Exception as e:
        logger.error(f"Error updating workflow stage: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow stage: {str(e)}",
        ) from e


@router.delete("/{stage_id}", tags=["Workflow Stages"])
async def delete_workflow_stage(
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a workflow stage.

    This endpoint permanently deletes a workflow stage configuration.
    This action cannot be undone.

    Args:
        stage_id: UUID of the workflow stage
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If workflow stage is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/workflow-stages/stage-uuid")
        >>> response.json()
        {
            "message": "Workflow stage deleted successfully",
            "id": "stage-uuid"
        }
    """
    try:
        logger.info(f"Deleting workflow stage: {stage_id}")

        # Check if stage exists
        result = await db.execute(
            select(WorkflowStageConfig).where(WorkflowStageConfig.id == UUID(stage_id))
        )
        stage = result.scalar_one_or_none()

        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow stage not found: {stage_id}",
            )

        # Delete the stage
        await db.execute(
            delete(WorkflowStageConfig).where(WorkflowStageConfig.id == UUID(stage_id))
        )
        await db.commit()

        logger.info(f"Deleted workflow stage: {stage_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Workflow stage deleted successfully",
                "id": stage_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {stage_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting workflow stage: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workflow stage: {str(e)}",
        ) from e
