"""
Candidates and workflow stage management endpoints.

This module provides endpoints for:
- Listing candidates (resumes) with their current workflow stages
- Moving candidates through customizable workflow stages (kanban-style board)
- Bulk moving multiple candidates to a stage at once
- Getting ranked candidates for vacancies with AI-powered matching

Supports both kanban-style board management and intelligent candidate ranking.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from analyzers.ranking_service import get_ranking_service, RankingService
from models.resume import Resume
from models.hiring_stage import HiringStage, HiringStageName
from models.workflow_stage_config import WorkflowStageConfig
from models.analytics_event import AnalyticsEvent, AnalyticsEventType
from models.candidate_tag import CandidateTag
from models.candidate_note import CandidateNote
from models.candidate_activity import CandidateActivity, CandidateActivityType

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class TagInfo(BaseModel):
    """Information about a tag assigned to a candidate."""

    id: str = Field(..., description="Tag ID")
    tag_name: str = Field(..., description="Tag name")
    color: Optional[str] = Field(None, description="Tag color code")
    organization_id: str = Field(..., description="Organization ID that owns this tag")


class LatestActivityInfo(BaseModel):
    """Information about the latest activity for a candidate."""

    activity_type: str = Field(..., description="Type of activity")
    created_at: str = Field(..., description="When the activity occurred")


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
    tags: List[TagInfo] = Field(default_factory=list, description="Tags assigned to this candidate")
    notes_count: int = Field(0, description="Number of notes for this candidate")
    latest_activity: Optional[LatestActivityInfo] = Field(None, description="Latest activity for this candidate")


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


class BulkMoveCandidatesRequest(BaseModel):
    """Request model for bulk moving candidates to a different stage."""

    resume_ids: List[str] = Field(..., description="List of resume IDs to move", min_length=1)
    stage_id: str = Field(..., description="Target stage ID (workflow_stage_config UUID or stage name)")
    vacancy_id: Optional[str] = Field(None, description="Optional vacancy ID to associate")
    notes: Optional[str] = Field(None, description="Optional notes about the stage change")


class BulkMoveCandidateResult(BaseModel):
    """Result of moving a single candidate in a bulk operation."""

    resume_id: str = Field(..., description="Resume ID")
    success: bool = Field(..., description="Whether the move was successful")
    previous_stage: Optional[str] = Field(None, description="Previous stage name")
    new_stage: Optional[str] = Field(None, description="New stage name")
    message: str = Field(..., description="Success or error message")


class BulkMoveCandidatesResponse(BaseModel):
    """Response model for bulk candidate stage movement."""

    total_requested: int = Field(..., description="Total number of candidates requested to move")
    successful: int = Field(..., description="Number of successfully moved candidates")
    failed: int = Field(..., description="Number of candidates that failed to move")
    results: List[BulkMoveCandidateResult] = Field(..., description="Individual results for each candidate")


# Ranked candidates models
class CandidateInfo(BaseModel):
    """Information about a single candidate."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    rank_score: float = Field(..., description="Overall ranking score (0-1)")
    rank_position: Optional[int] = Field(None, description="Position in ranked list")
    recommendation: str = Field(..., description="Hiring recommendation")
    confidence: float = Field(..., description="Model confidence (0-1)")
    feature_contributions: Dict[str, float] = Field(
        ..., description="Feature contribution scores"
    )
    ranking_factors: Dict[str, Any] = Field(..., description="Detailed factor scores")


class CandidatesListResponse(BaseModel):
    """Response with list of candidates for a vacancy."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    total_candidates: int = Field(..., description="Total number of candidates")
    candidates: List[Dict[str, Any]] = Field(..., description="List of ranked candidates")


# Stage metrics models
class StageTimeMetrics(BaseModel):
    """Time-based metrics for candidates in a stage."""

    average_days: float = Field(..., description="Average time candidates spend in this stage (days)")
    median_days: float = Field(..., description="Median time candidates spend in this stage (days)")
    min_days: float = Field(..., description="Minimum time spent in this stage (days)")
    max_days: float = Field(..., description="Maximum time spent in this stage (days)")
    candidate_count: int = Field(..., description="Number of candidates who passed through this stage")


class StageDropoffMetrics(BaseModel):
    """Drop-off metrics for a stage."""

    candidates_entered: int = Field(..., description="Number of candidates who entered this stage")
    candidates_exited: int = Field(..., description="Number of candidates who left this stage")
    candidates_current: int = Field(..., description="Number of candidates currently in this stage")
    dropoff_rate: float = Field(..., description="Drop-off rate (0-1), percentage who left without progressing")


class StageMetrics(BaseModel):
    """Combined metrics for a single stage."""

    stage_id: Optional[str] = Field(None, description="Stage UUID (for custom stages)")
    stage_name: str = Field(..., description="Stage name")
    display_name: Optional[str] = Field(None, description="Display name for custom stages")
    time_metrics: StageTimeMetrics = Field(..., description="Time-based metrics")
    dropoff_metrics: StageDropoffMetrics = Field(..., description="Drop-off metrics")


class StageMetricsResponse(BaseModel):
    """Response model for stage metrics."""

    stage_id: Optional[str] = Field(None, description="Requested stage ID filter")
    metrics: List[StageMetrics] = Field(..., description="List of stage metrics")
    total_stages: int = Field(..., description="Total number of stages with metrics")


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

        # Collect all resume IDs for bulk queries
        resume_ids = [str(row[0].id) for row in rows]

        # Bulk fetch: tags assigned to each resume
        tags_by_resume = {}
        if resume_ids:
            # Get all TAG_ADDED and TAG_REMOVED activities for these resumes
            all_tag_activities_result = await db.execute(
                select(CandidateActivity, CandidateTag)
                .outerjoin(
                    CandidateTag,
                    CandidateActivity.tag_id == CandidateTag.id
                )
                .where(
                    CandidateActivity.candidate_id.in_(resume_ids),
                    CandidateActivity.activity_type.in_([
                        CandidateActivityType.TAG_ADDED,
                        CandidateActivityType.TAG_REMOVED
                    ]),
                )
                .order_by(CandidateActivity.candidate_id, CandidateActivity.created_at)
            )
            all_tag_activity_rows = all_tag_activities_result.all()

            # Build a map of (resume_id, tag_id) -> latest activity timestamp
            tag_activity_map = {}  # (resume_id, tag_id) -> [(activity_type, timestamp)]
            for activity, tag in all_tag_activity_rows:
                if tag:
                    key = (str(activity.candidate_id), str(tag.id))
                    if key not in tag_activity_map:
                        tag_activity_map[key] = []
                    tag_activity_map[key].append({
                        "activity_type": activity.activity_type,
                        "timestamp": activity.created_at,
                        "tag_name": tag.tag_name,
                        "tag_color": tag.color,
                        "tag_id": str(tag.id),
                        "organization_id": str(tag.organization_id),
                    })

            # For each (resume, tag) pair, check if the latest activity is TAG_ADDED
            for (resume_id, tag_id), activities in tag_activity_map.items():
                latest = max(activities, key=lambda x: x["timestamp"])
                if latest["activity_type"] == CandidateActivityType.TAG_ADDED:
                    if resume_id not in tags_by_resume:
                        tags_by_resume[resume_id] = []
                    tags_by_resume[resume_id].append({
                        "id": tag_id,
                        "tag_name": latest["tag_name"],
                        "color": latest["tag_color"],
                        "organization_id": latest["organization_id"],
                    })

        # Bulk fetch: notes count for each resume
        notes_count_by_resume = {}
        if resume_ids:
            notes_count_result = await db.execute(
                select(CandidateNote.resume_id, func.count(CandidateNote.id))
                .where(CandidateNote.resume_id.in_(resume_ids))
                .group_by(CandidateNote.resume_id)
            )
            for resume_id, count in notes_count_result.all():
                notes_count_by_resume[str(resume_id)] = count

        # Bulk fetch: latest activity for each resume
        latest_activity_by_resume = {}
        if resume_ids:
            # Use a subquery to get the max created_at for each resume
            latest_activity_subq = (
                select(
                    CandidateActivity.candidate_id,
                    func.max(CandidateActivity.created_at).label("max_created_at")
                )
                .where(CandidateActivity.candidate_id.in_(resume_ids))
                .group_by(CandidateActivity.candidate_id)
                .subquery()
            )

            # Get the latest activity for each resume
            latest_activity_result = await db.execute(
                select(CandidateActivity)
                .join(
                    latest_activity_subq,
                    and_(
                        CandidateActivity.candidate_id == latest_activity_subq.c.candidate_id,
                        CandidateActivity.created_at == latest_activity_subq.c.max_created_at
                    )
                )
            )
            latest_activities = latest_activity_result.scalars().all()
            for activity in latest_activities:
                latest_activity_by_resume[str(activity.candidate_id)] = {
                    "activity_type": activity.activity_type.value,
                    "created_at": activity.created_at.isoformat(),
                }

        # Convert to response format
        candidates_list = []
        for row in rows:
            resume = row[0]
            hiring_stage = row[1]
            custom_stage_name = row[2]
            display_name = row[3]
            resume_id_str = str(resume.id)

            # Determine display stage name
            if display_name:
                stage_display = display_name
            elif custom_stage_name:
                stage_display = custom_stage_name
            elif hiring_stage:
                stage_display = hiring_stage.stage_name
            else:
                stage_display = HiringStageName.APPLIED.value

            # Get tags for this resume
            tags = tags_by_resume.get(resume_id_str, [])

            # Get notes count
            notes_count = notes_count_by_resume.get(resume_id_str, 0)

            # Get latest activity
            latest_activity = latest_activity_by_resume.get(resume_id_str)

            candidates_list.append({
                "id": resume_id_str,
                "filename": resume.filename,
                "current_stage": hiring_stage.stage_name if hiring_stage else HiringStageName.APPLIED.value,
                "stage_name": stage_display,
                "vacancy_id": str(hiring_stage.vacancy_id) if hiring_stage and hiring_stage.vacancy_id else None,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "updated_at": hiring_stage.updated_at.isoformat() if hiring_stage and hiring_stage.updated_at else resume.created_at.isoformat() if resume.created_at else None,
                "notes": hiring_stage.notes if hiring_stage else None,
                "tags": tags,
                "notes_count": notes_count,
                "latest_activity": latest_activity,
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

        # Fetch tags for this resume
        tags = []
        # Get all TAG_ADDED and TAG_REMOVED activities for this resume
        all_tag_activities_result = await db.execute(
            select(CandidateActivity, CandidateTag)
            .outerjoin(
                CandidateTag,
                CandidateActivity.tag_id == CandidateTag.id
            )
            .where(
                CandidateActivity.candidate_id == candidate_uuid,
                CandidateActivity.activity_type.in_([
                    CandidateActivityType.TAG_ADDED,
                    CandidateActivityType.TAG_REMOVED
                ]),
            )
            .order_by(CandidateActivity.created_at)
        )
        all_tag_activity_rows = all_tag_activities_result.all()

        # Build a map of tag_id -> [(activity_type, timestamp)]
        tag_activity_map = {}  # tag_id -> [(activity_type, timestamp, tag_name, tag_color)]
        for activity, tag in all_tag_activity_rows:
            if tag:
                tag_id_str = str(tag.id)
                if tag_id_str not in tag_activity_map:
                    tag_activity_map[tag_id_str] = []
                tag_activity_map[tag_id_str].append({
                    "activity_type": activity.activity_type,
                    "timestamp": activity.created_at,
                    "tag_name": tag.tag_name,
                    "tag_color": tag.color,
                })

        # For each tag, check if the latest activity is TAG_ADDED
        for tag_id, activities in tag_activity_map.items():
            latest = max(activities, key=lambda x: x["timestamp"])
            if latest["activity_type"] == CandidateActivityType.TAG_ADDED:
                tags.append({
                    "id": tag_id,
                    "tag_name": latest["tag_name"],
                    "color": latest["tag_color"],
                })

        # Count notes for this resume
        notes_count_result = await db.execute(
            select(func.count(CandidateNote.id)).where(
                CandidateNote.resume_id == candidate_uuid
            )
        )
        notes_count = notes_count_result.scalar() or 0

        # Get latest activity for this resume
        latest_activity_result = await db.execute(
            select(CandidateActivity)
            .where(CandidateActivity.candidate_id == candidate_uuid)
            .order_by(CandidateActivity.created_at.desc())
            .limit(1)
        )
        latest_activity_rec = latest_activity_result.scalar_one_or_none()

        latest_activity = None
        if latest_activity_rec:
            latest_activity = {
                "activity_type": latest_activity_rec.activity_type.value,
                "created_at": latest_activity_rec.created_at.isoformat(),
            }

        candidate_data = {
            "id": str(resume.id),
            "filename": resume.filename,
            "current_stage": hiring_stage.stage_name if hiring_stage else HiringStageName.APPLIED.value,
            "stage_name": stage_display,
            "vacancy_id": str(hiring_stage.vacancy_id) if hiring_stage and hiring_stage.vacancy_id else None,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "updated_at": hiring_stage.updated_at.isoformat() if hiring_stage and hiring_stage.updated_at else resume.created_at.isoformat() if resume.created_at else None,
            "notes": hiring_stage.notes if hiring_stage else None,
            "tags": tags,
            "notes_count": notes_count,
            "latest_activity": latest_activity,
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


@router.post(
    "/bulk-move",
    response_model=BulkMoveCandidatesResponse,
    tags=["Candidates"],
)
async def bulk_move_candidates(
    request: Request,
    bulk_data: BulkMoveCandidatesRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Bulk move multiple candidates to a different workflow stage.

    Creates new HiringStage records for each candidate to track stage transitions.
    This allows maintaining a complete history of candidate progression for multiple
    candidates at once.

    Args:
        request: FastAPI request object
        bulk_data: Bulk movement details (resume_ids, stage_id, optional vacancy_id, optional notes)
        db: Database session

    Returns:
        JSON response with bulk operation results including success/failure counts

    Raises:
        HTTPException(400): Invalid resume_ids or stage_id format
        HTTPException(404): Candidates or stage not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_ids": ["id1", "id2", "id3"],
        ...     "stage_id": "interview",
        ...     "notes": "Bulk moved to screening"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/candidates/bulk-move",
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"Bulk moving {len(bulk_data.resume_ids)} candidates to stage {bulk_data.stage_id}"
        )

        results = []
        successful_count = 0
        failed_count = 0

        # Determine if stage_id is a custom stage UUID or stage name
        workflow_stage_config_id = None
        new_stage_name = bulk_data.stage_id

        try:
            # Try parsing as UUID (custom stage)
            stage_uuid = UUID(bulk_data.stage_id)

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
                    detail=f"Custom stage not found: {bulk_data.stage_id}",
                )
        except ValueError:
            # It's a stage name, validate it's a valid enum or allowed value
            try:
                # Check if it's a valid enum value
                HiringStageName(bulk_data.stage_id)
            except ValueError:
                # Not a default stage, check if it's a custom stage name
                config_query = select(WorkflowStageConfig).where(
                    WorkflowStageConfig.stage_name == bulk_data.stage_id
                )
                config_result = await db.execute(config_query)
                workflow_config = config_result.scalar_one_or_none()

                if not workflow_config:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid stage name: {bulk_data.stage_id}",
                    )

                workflow_stage_config_id = workflow_config.id

        # Parse vacancy_id if provided
        vacancy_uuid = None
        if bulk_data.vacancy_id:
            try:
                vacancy_uuid = UUID(bulk_data.vacancy_id)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {bulk_data.vacancy_id}")

        # Process each resume_id
        for resume_id in bulk_data.resume_ids:
            try:
                # Parse candidate_id as UUID
                try:
                    candidate_uuid = UUID(resume_id)
                except ValueError:
                    results.append({
                        "resume_id": resume_id,
                        "success": False,
                        "previous_stage": None,
                        "new_stage": None,
                        "message": f"Invalid candidate ID format: {resume_id}",
                    })
                    failed_count += 1
                    continue

                # Verify resume exists
                resume_query = select(Resume).where(Resume.id == candidate_uuid)
                resume_result = await db.execute(resume_query)
                resume = resume_result.scalar_one_or_none()

                if not resume:
                    results.append({
                        "resume_id": resume_id,
                        "success": False,
                        "previous_stage": None,
                        "new_stage": None,
                        "message": f"Candidate not found: {resume_id}",
                    })
                    failed_count += 1
                    continue

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

                # Create new hiring stage record
                new_hiring_stage = HiringStage(
                    resume_id=candidate_uuid,
                    vacancy_id=vacancy_uuid,
                    workflow_stage_config_id=workflow_stage_config_id,
                    stage_name=new_stage_name,
                    notes=bulk_data.notes,
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
                        "notes": bulk_data.notes,
                        "workflow_stage_config_id": str(workflow_stage_config_id) if workflow_stage_config_id else None,
                        "bulk_operation": True,
                    },
                )
                db.add(analytics_event)
                await db.commit()

                results.append({
                    "resume_id": resume_id,
                    "success": True,
                    "previous_stage": previous_stage,
                    "new_stage": new_stage_name,
                    "message": f"Candidate moved to {new_stage_name} stage",
                })
                successful_count += 1

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error moving candidate {resume_id}: {e}", exc_info=True)
                results.append({
                    "resume_id": resume_id,
                    "success": False,
                    "previous_stage": None,
                    "new_stage": None,
                    "message": f"Failed to move candidate: {str(e)}",
                })
                failed_count += 1

        logger.info(
            f"Bulk move completed: {successful_count} successful, {failed_count} failed"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total_requested": len(bulk_data.resume_ids),
                "successful": successful_count,
                "failed": failed_count,
                "results": results,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk move operation: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk move: {str(e)}",
        ) from e


@router.get(
    "/vacancy/{vacancy_id}/ranked",
    tags=["Candidates"],
)
async def get_candidates_for_vacancy(
    vacancy_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum candidates to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get ranked candidates for a specific vacancy.

    Returns a list of candidates ranked by their match score for the
    specified vacancy, with detailed feature contributions and ranking factors.

    This endpoint leverages the AI-powered ranking service to provide
    intelligent candidate ordering based on multiple factors including:
    - Skills match (keyword, TF-IDF, vector similarity)
    - Experience relevance and duration
    - Education level
    - Title similarity
    - Resume freshness and completeness

    Args:
        vacancy_id: Vacancy UUID
        limit: Maximum number of candidates to return (default: 50, max: 200)
        db: Database session

    Returns:
        List of ranked candidates with detailed scoring information

    Raises:
        HTTPException(422): If vacancy_id is not a valid UUID
        HTTPException(404): If vacancy is not found
        HTTPException(500): If candidate retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/candidates/vacancy/vac-456-ghi/ranked",
        ...     params={"limit": 20}
        ... )
        >>> response.json()
        {
            "vacancy_id": "vac-456-ghi",
            "total_candidates": 20,
            "candidates": [
                {
                    "resume_id": "abc-123-def",
                    "vacancy_id": "vac-456-ghi",
                    "rank_score": 0.85,
                    "rank_position": 1,
                    "recommendation": "excellent",
                    "confidence": 0.88,
                    "feature_contributions": {...},
                    "ranking_factors": {...}
                },
                ...
            ]
        }
    """
    try:
        logger.info(f"Getting candidates for vacancy {vacancy_id}")

        # Parse UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid vacancy UUID format",
            )

        # Get ranking service
        ranking_service = get_ranking_service()

        # Get ranked candidates for the vacancy
        rankings = await ranking_service.rank_candidates_for_vacancy(
            db,
            vacancy_uuid,
            limit=limit,
        )

        logger.info(
            f"Returning {len(rankings)} candidates for vacancy {vacancy_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "vacancy_id": vacancy_id,
                "total_candidates": len(rankings),
                "candidates": rankings,
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting candidates for vacancy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidates: {str(e)}",
        ) from e


@router.get(
    "/metrics",
    response_model=StageMetricsResponse,
    tags=["Candidates"],
)
async def get_stage_metrics(
    stage_id: Optional[str] = Query(None, description="Filter by specific stage ID or name"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get stage metrics including time in stage and drop-off rates.

    This endpoint provides comprehensive metrics for workflow stages,
    helping organizations understand their recruitment pipeline efficiency.
    Metrics include:
    - Time in stage: average, median, min, max days candidates spend in each stage
    - Drop-off rates: percentage of candidates who leave from each stage

    Args:
        stage_id: Optional filter by workflow stage ID or name
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)
        db: Database session

    Returns:
        JSON response with stage metrics including time and drop-off data

    Raises:
        HTTPException(400): Invalid date format
        HTTPException(500): If metrics retrieval fails

    Examples:
        >>> import requests
        >>> # Get metrics for all stages
        >>> response = requests.get("http://localhost:8000/api/candidates/metrics")
        >>> # Get metrics for a specific stage
        >>> response = requests.get("http://localhost:8000/api/candidates/metrics?stage_id=interview")
        >>> response.json()
        {
            "stage_id": "interview",
            "metrics": [
                {
                    "stage_id": null,
                    "stage_name": "applied",
                    "display_name": null,
                    "time_metrics": {
                        "average_days": 2.5,
                        "median_days": 2.0,
                        "min_days": 0.5,
                        "max_days": 7.0,
                        "candidate_count": 150
                    },
                    "dropoff_metrics": {
                        "candidates_entered": 150,
                        "candidates_exited": 120,
                        "candidates_current": 30,
                        "dropoff_rate": 0.20
                    }
                }
            ],
            "total_stages": 1
        }
    """
    try:
        logger.info(
            f"Fetching stage metrics - stage_id: {stage_id}, "
            f"start_date: {start_date}, end_date: {end_date}"
        )

        from collections import defaultdict
        import statistics
        from datetime import datetime

        # Parse date filters
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                )

        # Get all hiring stages ordered by resume_id and created_at
        query = select(HiringStage, WorkflowStageConfig).select_from(
            HiringStage
        ).outerjoin(
            WorkflowStageConfig,
            HiringStage.workflow_stage_config_id == WorkflowStageConfig.id,
        ).order_by(HiringStage.resume_id, HiringStage.created_at)

        # Apply date filters if provided
        if start_dt:
            query = query.where(HiringStage.created_at >= start_dt)
        if end_dt:
            query = query.where(HiringStage.created_at <= end_dt)

        # Apply stage filter if provided
        if stage_id:
            try:
                stage_uuid = UUID(stage_id)
                query = query.where(HiringStage.workflow_stage_config_id == stage_uuid)
            except ValueError:
                # It's a stage name
                query = query.where(HiringStage.stage_name == stage_id)

        result = await db.execute(query)
        all_stages = result.all()

        if not all_stages:
            logger.info("No stage data available")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "stage_id": stage_id,
                    "metrics": [],
                    "total_stages": 0,
                },
            )

        # Group stages by resume_id to track progression
        resume_stages = defaultdict(list)
        for hiring_stage, workflow_config in all_stages:
            resume_stages[hiring_stage.resume_id].append({
                "hiring_stage": hiring_stage,
                "workflow_config": workflow_config,
            })

        # Calculate time durations for each stage transition
        stage_durations = defaultdict(list)  # stage_name -> [durations in days]
        stage_entries = defaultdict(int)  # stage_name -> count
        stage_exits = defaultdict(int)  # stage_name -> count
        stage_current = defaultdict(int)  # stage_name -> count

        # Get the current stage for each resume (latest hiring_stage)
        latest_stage_by_resume = {}
        for resume_id, stages in resume_stages.items():
            if stages:
                # Sort by created_at to ensure correct order
                stages_sorted = sorted(stages, key=lambda x: x["hiring_stage"].created_at)
                latest_stage_by_resume[resume_id] = stages_sorted[-1]

        # Process each resume's stage history
        for resume_id, stages in resume_stages.items():
            # Sort by created_at to ensure correct order
            stages_sorted = sorted(stages, key=lambda x: x["hiring_stage"].created_at)

            # Track the latest stage for this resume
            latest = stages_sorted[-1]
            latest_stage_name = latest["hiring_stage"].stage_name
            stage_current[latest_stage_name] += 1

            # Calculate time spent in each stage and track exits
            for i in range(len(stages_sorted) - 1):
                current = stages_sorted[i]
                next_stage = stages_sorted[i + 1]

                current_stage_name = current["hiring_stage"].stage_name
                next_stage_name = next_stage["hiring_stage"].stage_name

                # Count entries to each stage
                stage_entries[current_stage_name] += 1

                # Calculate duration in days
                duration_days = (
                    next_stage["hiring_stage"].created_at - current["hiring_stage"].created_at
                ).total_seconds() / 86400

                # Only include positive durations
                if duration_days >= 0:
                    stage_durations[current_stage_name].append(duration_days)

                # Count exits (moved to a different stage)
                if current_stage_name != next_stage_name:
                    stage_exits[current_stage_name] += 1

            # Also count the last stage as an entry
            if stages_sorted:
                stage_entries[latest_stage_name] += 1

        # Calculate metrics for each stage
        metrics_list = []

        # Get all unique stage names
        all_stage_names = set(stage_durations.keys()) | set(stage_entries.keys())

        for stage_name in all_stage_names:
            # Get workflow config for display name
            config_query = select(WorkflowStageConfig).where(
                WorkflowStageConfig.stage_name == stage_name
            ).limit(1)
            config_result = await db.execute(config_query)
            workflow_config = config_result.scalar_one_or_none()

            # Determine display name
            if workflow_config and workflow_config.display_name:
                display_name = workflow_config.display_name
                stage_uuid_str = str(workflow_config.id)
            else:
                display_name = None
                stage_uuid_str = None

            # Calculate time metrics
            durations = stage_durations.get(stage_name, [])
            if durations:
                avg_duration = statistics.mean(durations)
                median_duration = statistics.median(durations)
                min_duration = min(durations)
                max_duration = max(durations)
                candidate_count = len(durations)
            else:
                avg_duration = 0.0
                median_duration = 0.0
                min_duration = 0.0
                max_duration = 0.0
                candidate_count = 0

            time_metrics = {
                "average_days": round(avg_duration, 1),
                "median_days": round(median_duration, 1),
                "min_days": round(min_duration, 1),
                "max_days": round(max_duration, 1),
                "candidate_count": candidate_count,
            }

            # Calculate drop-off metrics
            entered = stage_entries.get(stage_name, 0)
            exited = stage_exits.get(stage_name, 0)
            current = stage_current.get(stage_name, 0)

            # Drop-off rate: percentage who exited without progressing forward
            # (those who left / total who entered)
            dropoff_rate = exited / entered if entered > 0 else 0.0

            dropoff_metrics = {
                "candidates_entered": entered,
                "candidates_exited": exited,
                "candidates_current": current,
                "dropoff_rate": round(dropoff_rate, 3),
            }

            metrics_list.append({
                "stage_id": stage_uuid_str,
                "stage_name": stage_name,
                "display_name": display_name,
                "time_metrics": time_metrics,
                "dropoff_metrics": dropoff_metrics,
            })

        # Sort by stage order (default stages first, then custom)
        def stage_sort_key(stage):
            default_order = {
                "applied": 1,
                "screening": 2,
                "interview": 3,
                "technical": 4,
                "offer": 5,
                "hired": 6,
                "rejected": 7,
                "withdrawn": 8,
            }
            return default_order.get(stage["stage_name"].lower(), 999)

        metrics_list.sort(key=stage_sort_key)

        logger.info(f"Stage metrics retrieved successfully for {len(metrics_list)} stages")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "stage_id": stage_id,
                "metrics": metrics_list,
                "total_stages": len(metrics_list),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stage metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stage metrics: {str(e)}",
        ) from e
