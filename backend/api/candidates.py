"""
Candidates and workflow stage management endpoints.

This module provides endpoints for listing candidates (resumes) and moving them
through customizable workflow stages, supporting kanban-style board management.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from database import get_db
from models.resume import Resume
from models.hiring_stage import HiringStage, HiringStageName
from models.workflow_stage_config import WorkflowStageConfig
from models.analytics_event import AnalyticsEvent, AnalyticsEventType

logger = logging.getLogger(__name__)

router = APIRouter()


class CandidateListItem(BaseModel):
    """Response model for a candidate in list view."""

    id: str = Field(..., description="Unique identifier (resume ID)")
    filename: str = Field(..., description="Resume filename")
    current_stage: str = Field(..., description="Current workflow stage")
    stage_name: str = Field(..., description="Display name of current stage")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID if any")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    notes: Optional[str] = Field(None, description="Stage notes")


class MoveCandidateRequest(BaseModel):
    """Request model for moving a candidate to a different stage."""

    stage_id: str = Field(..., description="Target stage ID (workflow_stage_config UUID or stage name)")
    vacancy_id: Optional[str] = Field(None, description="Optional vacancy ID to associate")
    notes: Optional[str] = Field(None, description="Optional notes about the stage change")


class MoveCandidateResponse(BaseModel):
    """Response model for candidate stage movement."""

    id: str = Field(..., description="Hiring stage record ID")
    resume_id: str = Field(..., description="Resume ID")
    previous_stage: str = Field(..., description="Previous stage name")
    new_stage: str = Field(..., description="New stage name")
    message: str = Field(..., description="Success message")


@router.get(
    "/",
    response_model=list[CandidateListItem],
    tags=["Candidates"],
)
async def list_candidates(
    request: Request,
    stage_id: Optional[str] = None,
    vacancy_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all candidates (resumes) with their current workflow stages.

    Returns a paginated list of candidates with their current hiring stage.
    Can be filtered by stage, vacancy, and search term for kanban board views.

    Args:
        request: FastAPI request object
        stage_id: Optional filter by workflow stage ID or name
        vacancy_id: Optional filter by vacancy ID
        search: Optional search term to filter candidates by filename (case-insensitive)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of candidates and their stages

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all candidates
        >>> response = requests.get("http://localhost:8000/api/candidates/")
        >>> # Filter by stage
        >>> response = requests.get("http://localhost:8000/api/candidates/?stage_id=interview")
        >>> # Search by name
        >>> response = requests.get("http://localhost:8000/api/candidates/?search=john")
        >>> # Combine filters
        >>> response = requests.get("http://localhost:8000/api/candidates/?stage_id=interview&search=smith")
        >>> candidates = response.json()
    """
    try:
        logger.info(
            f"Fetching candidates - stage_id: {stage_id}, vacancy_id: {vacancy_id}, "
            f"search: {search}, skip: {skip}, limit: {limit}"
        )

        # Build base query joining resumes with their latest hiring stage
        # Subquery to get the latest hiring stage for each resume
        latest_stage_subq = (
            select(
                HiringStage.resume_id,
                func.max(HiringStage.created_at).label("max_created_at")
            )
            .group_by(HiringStage.resume_id)
            .subquery()
        )

        # Main query with joins
        query = (
            select(
                Resume,
                HiringStage,
                WorkflowStageConfig.stage_name.label("custom_stage_name"),
                WorkflowStageConfig.display_name,
            )
            .outerjoin(
                HiringStage,
                and_(
                    HiringStage.resume_id == Resume.id,
                    HiringStage.created_at == latest_stage_subq.c.max_created_at,
                ),
            )
            .outerjoin(
                WorkflowStageConfig,
                HiringStage.workflow_stage_config_id == WorkflowStageConfig.id,
            )
        )

        # Apply filters
        if stage_id:
            # Check if it's a UUID (custom stage) or stage name
            try:
                stage_uuid = UUID(stage_id)
                query = query.where(HiringStage.workflow_stage_config_id == stage_uuid)
            except ValueError:
                # It's a stage name
                query = query.where(HiringStage.stage_name == stage_id)

        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(HiringStage.vacancy_id == vacancy_uuid)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {vacancy_id}")

        if search:
            # Case-insensitive search on filename
            query = query.where(Resume.filename.ilike(f"%{search}%"))

        # Order by most recently updated
        query = query.order_by(HiringStage.updated_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        rows = result.all()

        # Convert to response format
        candidates_list = []
        for row in rows:
            resume = row[0]
            hiring_stage = row[1]
            custom_stage_name = row[2]
            display_name = row[3]

            # Determine display stage name
            if display_name:
                stage_display = display_name
            elif custom_stage_name:
                stage_display = custom_stage_name
            elif hiring_stage:
                stage_display = hiring_stage.stage_name
            else:
                stage_display = HiringStageName.APPLIED.value

            candidates_list.append({
                "id": str(resume.id),
                "filename": resume.filename,
                "current_stage": hiring_stage.stage_name if hiring_stage else HiringStageName.APPLIED.value,
                "stage_name": stage_display,
                "vacancy_id": str(hiring_stage.vacancy_id) if hiring_stage and hiring_stage.vacancy_id else None,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "updated_at": hiring_stage.updated_at.isoformat() if hiring_stage and hiring_stage.updated_at else resume.created_at.isoformat() if resume.created_at else None,
                "notes": hiring_stage.notes if hiring_stage else None,
            })

        logger.info(f"Retrieved {len(candidates_list)} candidates")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=candidates_list,
        )

    except Exception as e:
        logger.error(f"Error listing candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list candidates: {str(e)}",
        ) from e


@router.get(
    "/{candidate_id}",
    response_model=CandidateListItem,
    tags=["Candidates"],
)
async def get_candidate(
    request: Request,
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific candidate's current stage information.

    Args:
        request: FastAPI request object
        candidate_id: Resume UUID
        db: Database session

    Returns:
        JSON response with candidate details and current stage

    Raises:
        HTTPException(404): If candidate not found
        HTTPException(500): If data retrieval fails
    """
    try:
        logger.info(f"Fetching candidate: {candidate_id}")

        # Parse candidate_id as UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # Get the resume
        resume_query = select(Resume).where(Resume.id == candidate_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {candidate_id}",
            )

        # Get the latest hiring stage
        stage_query = (
            select(HiringStage, WorkflowStageConfig)
            .outerjoin(
                WorkflowStageConfig,
                HiringStage.workflow_stage_config_id == WorkflowStageConfig.id,
            )
            .where(HiringStage.resume_id == candidate_uuid)
            .order_by(HiringStage.created_at.desc())
            .limit(1)
        )
        stage_result = await db.execute(stage_query)
        stage_row = stage_result.first()

        hiring_stage = stage_row[0] if stage_row else None
        workflow_config = stage_row[1] if stage_row else None

        # Determine display stage name
        if workflow_config and workflow_config.display_name:
            stage_display = workflow_config.display_name
        elif workflow_config and workflow_config.stage_name:
            stage_display = workflow_config.stage_name
        elif hiring_stage:
            stage_display = hiring_stage.stage_name
        else:
            stage_display = HiringStageName.APPLIED.value

        candidate_data = {
            "id": str(resume.id),
            "filename": resume.filename,
            "current_stage": hiring_stage.stage_name if hiring_stage else HiringStageName.APPLIED.value,
            "stage_name": stage_display,
            "vacancy_id": str(hiring_stage.vacancy_id) if hiring_stage and hiring_stage.vacancy_id else None,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "updated_at": hiring_stage.updated_at.isoformat() if hiring_stage and hiring_stage.updated_at else resume.created_at.isoformat() if resume.created_at else None,
            "notes": hiring_stage.notes if hiring_stage else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=candidate_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidate: {str(e)}",
        ) from e


@router.put(
    "/{candidate_id}/stage",
    response_model=MoveCandidateResponse,
    tags=["Candidates"],
)
async def move_candidate(
    request: Request,
    candidate_id: str,
    stage_data: MoveCandidateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Move a candidate to a different workflow stage.

    Creates a new HiringStage record to track the stage transition.
    This allows maintaining a complete history of candidate progression.

    Args:
        request: FastAPI request object
        candidate_id: Resume UUID
        stage_data: Stage movement details (stage_id, optional vacancy_id, optional notes)
        db: Database session

    Returns:
        JSON response with new stage information

    Raises:
        HTTPException(400): Invalid candidate ID or stage_id format
        HTTPException(404): Candidate not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"stage_id": "interview", "vacancy_id": "...", "notes": "Passed screening"}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/candidates/123/stage",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Moving candidate {candidate_id} to stage {stage_data.stage_id}")

        # Parse candidate_id as UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # Verify resume exists
        resume_query = select(Resume).where(Resume.id == candidate_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {candidate_id}",
            )

        # Get current/latest stage
        current_stage_query = (
            select(HiringStage)
            .where(HiringStage.resume_id == candidate_uuid)
            .order_by(HiringStage.created_at.desc())
            .limit(1)
        )
        current_stage_result = await db.execute(current_stage_query)
        current_stage = current_stage_result.scalar_one_or_none()

        previous_stage = current_stage.stage_name if current_stage else HiringStageName.APPLIED.value

        # Determine if stage_id is a custom stage UUID or stage name
        workflow_stage_config_id = None
        new_stage_name = stage_data.stage_id

        try:
            # Try parsing as UUID (custom stage)
            stage_uuid = UUID(stage_data.stage_id)

            # Verify the custom stage exists
            config_query = select(WorkflowStageConfig).where(WorkflowStageConfig.id == stage_uuid)
            config_result = await db.execute(config_query)
            workflow_config = config_result.scalar_one_or_none()

            if workflow_config:
                workflow_stage_config_id = stage_uuid
                new_stage_name = workflow_config.stage_name
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Custom stage not found: {stage_data.stage_id}",
                )
        except ValueError:
            # It's a stage name, validate it's a valid enum or allowed value
            try:
                # Check if it's a valid enum value
                HiringStageName(stage_data.stage_id)
            except ValueError:
                # Not a default stage, check if it's a custom stage name
                config_query = select(WorkflowStageConfig).where(
                    WorkflowStageConfig.stage_name == stage_data.stage_id
                )
                config_result = await db.execute(config_query)
                workflow_config = config_result.scalar_one_or_none()

                if not workflow_config:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid stage name: {stage_data.stage_id}",
                    )

                workflow_stage_config_id = workflow_config.id

        # Parse vacancy_id if provided
        vacancy_uuid = None
        if stage_data.vacancy_id:
            try:
                vacancy_uuid = UUID(stage_data.vacancy_id)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {stage_data.vacancy_id}")

        # Create new hiring stage record
        new_hiring_stage = HiringStage(
            resume_id=candidate_uuid,
            vacancy_id=vacancy_uuid,
            workflow_stage_config_id=workflow_stage_config_id,
            stage_name=new_stage_name,
            notes=stage_data.notes,
        )

        db.add(new_hiring_stage)
        await db.commit()
        await db.refresh(new_hiring_stage)

        # Create analytics event for stage change
        analytics_event = AnalyticsEvent(
            event_type=AnalyticsEventType.STAGE_CHANGED,
            entity_type="resume",
            entity_id=candidate_uuid,
            event_data={
                "previous_stage": previous_stage,
                "new_stage": new_stage_name,
                "vacancy_id": str(vacancy_uuid) if vacancy_uuid else None,
                "notes": stage_data.notes,
                "workflow_stage_config_id": str(workflow_stage_config_id) if workflow_stage_config_id else None,
            },
        )
        db.add(analytics_event)
        await db.commit()

        logger.info(
            f"Candidate {candidate_id} moved from {previous_stage} to {new_stage_name}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(new_hiring_stage.id),
                "resume_id": str(candidate_uuid),
                "previous_stage": previous_stage,
                "new_stage": new_stage_name,
                "message": f"Candidate moved to {new_stage_name} stage",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving candidate {candidate_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move candidate: {str(e)}",
        ) from e
