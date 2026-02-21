"""
Candidate review queue management endpoints.

This module provides endpoints for:
- Listing candidates in the review queue with filtering and prioritization
- Managing queue item status transitions
- Assigning candidates to recruiters
- Updating candidate priority

Supports systematic candidate review workflow for recruiters.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.resume import Resume
from models.candidate_queue import CandidateQueueItem, QueuePriority, QueueStatus
from models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class QueueItemResponse(BaseModel):
    """Response model for a single queue item."""

    id: str = Field(..., description="Queue item ID")
    resume_id: str = Field(..., description="Resume ID")
    filename: Optional[str] = Field(None, description="Resume filename")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Vacancy title")
    priority: str = Field(..., description="Priority level (urgent, high, medium, low)")
    status: str = Field(..., description="Queue status (pending, in_review, completed, skipped)")
    assigned_recruiter_id: Optional[str] = Field(None, description="Assigned recruiter ID")
    queue_entered_at: str = Field(..., description="When candidate entered the queue")
    review_started_at: Optional[str] = Field(None, description="When review started")
    review_completed_at: Optional[str] = Field(None, description="When review completed")
    notes: Optional[str] = Field(None, description="Notes about the queue item")
    wait_time_hours: Optional[float] = Field(None, description="Hours waiting in queue")
    created_at: str = Field(..., description="Record creation timestamp")
    updated_at: str = Field(..., description="Record update timestamp")


class QueueListResponse(BaseModel):
    """Response model for queue list."""

    total: int = Field(..., description="Total number of items matching filters")
    items: List[QueueItemResponse] = Field(..., description="Queue items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items returned")


class QueueCountsResponse(BaseModel):
    """Response model for queue counts by status."""

    pending: int = Field(0, description="Count of pending items")
    in_review: int = Field(0, description="Count of items in review")
    completed: int = Field(0, description="Count of completed items")
    skipped: int = Field(0, description="Count of skipped items")
    total: int = Field(0, description="Total count across all statuses")


class QueueMetricsResponse(BaseModel):
    """Response model for queue metrics."""

    counts: QueueCountsResponse = Field(..., description="Counts by status")
    average_wait_time_hours: Optional[float] = Field(None, description="Average wait time in queue")
    median_wait_time_hours: Optional[float] = Field(None, description="Median wait time in queue")
    oldest_pending_at: Optional[str] = Field(None, description="When the oldest pending item entered queue")
    throughput_last_24h: int = Field(0, description="Items completed in last 24 hours")
    throughput_last_7d: int = Field(0, description="Items completed in last 7 days")


# Priority ordering for sorting
PRIORITY_ORDER = {
    QueuePriority.URGENT: 0,
    QueuePriority.HIGH: 1,
    QueuePriority.MEDIUM: 2,
    QueuePriority.LOW: 3,
}


@router.get(
    "/",
    response_model=QueueListResponse,
    tags=["Candidate Queue"],
)
async def list_queue(
    request: Request,
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending, in_review, completed, skipped)"),
    priority: Optional[str] = Query(None, description="Filter by priority (urgent, high, medium, low)"),
    assigned_recruiter_id: Optional[str] = Query(None, description="Filter by assigned recruiter ID"),
    entered_after: Optional[str] = Query(None, description="Filter items entered after this date (ISO 8601)"),
    entered_before: Optional[str] = Query(None, description="Filter items entered before this date (ISO 8601)"),
    sort_by: Optional[str] = Query("priority", description="Sort by: priority, wait_time, created_at"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List candidates in the review queue with filtering and prioritization.

    Returns a paginated list of queue items with their associated resume and
    vacancy information. Supports filtering by vacancy, status, priority,
    recruiter, and date range.

    Default sorting is by priority (urgent first), then by wait time (oldest first).

    Args:
        request: FastAPI request object
        vacancy_id: Optional filter by vacancy ID
        status: Optional filter by queue status
        priority: Optional filter by priority level
        assigned_recruiter_id: Optional filter by assigned recruiter
        entered_after: Optional filter items entered after this date
        entered_before: Optional filter items entered before this date
        sort_by: Sort field (priority, wait_time, created_at)
        sort_order: Sort order (asc or desc)
        skip: Number of items to skip for pagination
        limit: Maximum number of items to return
        db: Database session

    Returns:
        JSON response with list of queue items

    Raises:
        HTTPException(400): Invalid filter parameter format
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all pending items
        >>> response = requests.get("/api/candidate-queue/?status=pending")
        >>> # Get high priority items for a vacancy
        >>> response = requests.get("/api/candidate-queue/?vacancy_id=abc-123&priority=high")
        >>> # Sort by wait time (oldest first)
        >>> response = requests.get("/api/candidate-queue/?sort_by=wait_time&sort_order=asc")
    """
    try:
        logger.info(
            f"Fetching queue items - vacancy_id: {vacancy_id}, status: {status}, "
            f"priority: {priority}, assigned_recruiter_id: {assigned_recruiter_id}, "
            f"skip: {skip}, limit: {limit}"
        )

        # Build base query
        query = (
            select(CandidateQueueItem, Resume, JobVacancy)
            .outerjoin(Resume, CandidateQueueItem.resume_id == Resume.id)
            .outerjoin(JobVacancy, CandidateQueueItem.vacancy_id == JobVacancy.id)
        )

        # Apply filters
        if vacancy_id:
            try:
                from uuid import UUID
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(CandidateQueueItem.vacancy_id == vacancy_uuid)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {vacancy_id}")

        if status:
            try:
                status_enum = QueueStatus(status.lower())
                query = query.where(CandidateQueueItem.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Must be one of: pending, in_review, completed, skipped",
                )

        if priority:
            try:
                priority_enum = QueuePriority(priority.lower())
                query = query.where(CandidateQueueItem.priority == priority_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority: {priority}. Must be one of: urgent, high, medium, low",
                )

        if assigned_recruiter_id:
            try:
                from uuid import UUID
                recruiter_uuid = UUID(assigned_recruiter_id)
                query = query.where(CandidateQueueItem.assigned_recruiter_id == recruiter_uuid)
            except ValueError:
                logger.warning(f"Invalid assigned_recruiter_id format: {assigned_recruiter_id}")

        if entered_after:
            try:
                entered_after_dt = datetime.fromisoformat(entered_after.replace('Z', '+00:00'))
                query = query.where(CandidateQueueItem.queue_entered_at >= entered_after_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid entered_after format: {entered_after}. Use ISO 8601 format.",
                )

        if entered_before:
            try:
                entered_before_dt = datetime.fromisoformat(entered_before.replace('Z', '+00:00'))
                query = query.where(CandidateQueueItem.queue_entered_at <= entered_before_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid entered_before format: {entered_before}. Use ISO 8601 format.",
                )

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        if sort_by == "priority":
            # Sort by priority then by queue_entered_at (oldest first within priority)
            query = query.order_by(
                asc(CandidateQueueItem.priority),
                asc(CandidateQueueItem.queue_entered_at)
            )
        elif sort_by == "wait_time":
            if sort_order == "desc":
                query = query.order_by(desc(CandidateQueueItem.queue_entered_at))
            else:
                query = query.order_by(asc(CandidateQueueItem.queue_entered_at))
        elif sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(desc(CandidateQueueItem.created_at))
            else:
                query = query.order_by(asc(CandidateQueueItem.created_at))
        else:
            # Default sort by priority
            query = query.order_by(
                asc(CandidateQueueItem.priority),
                asc(CandidateQueueItem.queue_entered_at)
            )

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        rows = result.all()

        # Calculate wait time for each item
        now = datetime.now(timezone.utc)

        # Build response
        items_list = []
        for row in rows:
            queue_item = row[0]
            resume = row[1]
            vacancy = row[2]

            # Calculate wait time in hours
            wait_time_hours = None
            if queue_item.queue_entered_at:
                entered_at = queue_item.queue_entered_at
                if entered_at.tzinfo is None:
                    entered_at = entered_at.replace(tzinfo=timezone.utc)
                wait_time_hours = (now - entered_at).total_seconds() / 3600

            item_data = {
                "id": str(queue_item.id),
                "resume_id": str(queue_item.resume_id),
                "filename": resume.filename if resume else None,
                "vacancy_id": str(queue_item.vacancy_id) if queue_item.vacancy_id else None,
                "vacancy_title": vacancy.title if vacancy else None,
                "priority": queue_item.priority.value,
                "status": queue_item.status.value,
                "assigned_recruiter_id": str(queue_item.assigned_recruiter_id) if queue_item.assigned_recruiter_id else None,
                "queue_entered_at": queue_item.queue_entered_at.isoformat() if queue_item.queue_entered_at else None,
                "review_started_at": queue_item.review_started_at.isoformat() if queue_item.review_started_at else None,
                "review_completed_at": queue_item.review_completed_at.isoformat() if queue_item.review_completed_at else None,
                "notes": queue_item.notes,
                "wait_time_hours": round(wait_time_hours, 2) if wait_time_hours is not None else None,
                "created_at": queue_item.created_at.isoformat() if queue_item.created_at else None,
                "updated_at": queue_item.updated_at.isoformat() if queue_item.updated_at else None,
            }
            items_list.append(item_data)

        logger.info(f"Retrieved {len(items_list)} queue items (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "items": items_list,
                "skip": skip,
                "limit": limit,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing queue items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list queue items: {str(e)}",
        ) from e


@router.get(
    "/counts",
    response_model=QueueCountsResponse,
    tags=["Candidate Queue"],
)
async def get_queue_counts(
    request: Request,
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get counts of queue items by status.

    Returns the count of queue items in each status category.
    Optionally filtered by vacancy.

    Args:
        request: FastAPI request object
        vacancy_id: Optional filter by vacancy ID
        db: Database session

    Returns:
        JSON response with counts by status

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/candidate-queue/counts")
        >>> response.json()
        {"pending": 10, "in_review": 3, "completed": 45, "skipped": 5, "total": 63}
    """
    try:
        logger.info(f"Fetching queue counts - vacancy_id: {vacancy_id}")

        # Build base query
        base_query = select(CandidateQueueItem)
        if vacancy_id:
            try:
                from uuid import UUID
                vacancy_uuid = UUID(vacancy_id)
                base_query = base_query.where(CandidateQueueItem.vacancy_id == vacancy_uuid)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {vacancy_id}")

        # Get counts by status
        counts = {}
        total = 0

        for status_enum in QueueStatus:
            count_query = select(func.count()).select_from(
                base_query.where(CandidateQueueItem.status == status_enum).subquery()
            )
            result = await db.execute(count_query)
            count = result.scalar() or 0
            counts[status_enum.value] = count
            total += count

        response_data = {
            "pending": counts.get("pending", 0),
            "in_review": counts.get("in_review", 0),
            "completed": counts.get("completed", 0),
            "skipped": counts.get("skipped", 0),
            "total": total,
        }

        logger.info(f"Queue counts: {response_data}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error getting queue counts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue counts: {str(e)}",
        ) from e


@router.get(
    "/metrics",
    response_model=QueueMetricsResponse,
    tags=["Candidate Queue"],
)
async def get_queue_metrics(
    request: Request,
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get queue metrics including wait times and throughput.

    Returns comprehensive metrics about the queue including:
    - Counts by status
    - Average and median wait times
    - Oldest pending item timestamp
    - Throughput (completed items) in last 24h and 7 days

    Args:
        request: FastAPI request object
        vacancy_id: Optional filter by vacancy ID
        db: Database session

    Returns:
        JSON response with queue metrics

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/candidate-queue/metrics")
        >>> response.json()
        {
            "counts": {"pending": 10, "in_review": 3, "completed": 45, "skipped": 5, "total": 63},
            "average_wait_time_hours": 24.5,
            "median_wait_time_hours": 18.2,
            "oldest_pending_at": "2024-01-15T10:00:00Z",
            "throughput_last_24h": 8,
            "throughput_last_7d": 35
        }
    """
    try:
        logger.info(f"Fetching queue metrics - vacancy_id: {vacancy_id}")

        from uuid import UUID
        import statistics

        # Build base filter
        vacancy_uuid = None
        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {vacancy_id}")

        # Get counts by status
        counts = {}
        total = 0

        for status_enum in QueueStatus:
            query = select(func.count()).select_from(CandidateQueueItem).where(
                CandidateQueueItem.status == status_enum
            )
            if vacancy_uuid:
                query = query.where(CandidateQueueItem.vacancy_id == vacancy_uuid)

            result = await db.execute(query)
            count = result.scalar() or 0
            counts[status_enum.value] = count
            total += count

        counts_response = {
            "pending": counts.get("pending", 0),
            "in_review": counts.get("in_review", 0),
            "completed": counts.get("completed", 0),
            "skipped": counts.get("skipped", 0),
            "total": total,
        }

        # Calculate wait times for pending items
        now = datetime.now(timezone.utc)
        pending_query = select(CandidateQueueItem.queue_entered_at).where(
            CandidateQueueItem.status == QueueStatus.PENDING
        )
        if vacancy_uuid:
            pending_query = pending_query.where(CandidateQueueItem.vacancy_id == vacancy_uuid)

        pending_result = await db.execute(pending_query)
        pending_entered_times = [row[0] for row in pending_result.all()]

        average_wait_time_hours = None
        median_wait_time_hours = None
        oldest_pending_at = None

        if pending_entered_times:
            wait_times = []
            for entered_at in pending_entered_times:
                if entered_at:
                    if entered_at.tzinfo is None:
                        entered_at = entered_at.replace(tzinfo=timezone.utc)
                    wait_hours = (now - entered_at).total_seconds() / 3600
                    wait_times.append(wait_hours)

            if wait_times:
                average_wait_time_hours = round(statistics.mean(wait_times), 2)
                median_wait_time_hours = round(statistics.median(wait_times), 2)

            # Get oldest pending timestamp
            oldest_query = select(func.min(CandidateQueueItem.queue_entered_at)).where(
                CandidateQueueItem.status == QueueStatus.PENDING
            )
            if vacancy_uuid:
                oldest_query = oldest_query.where(CandidateQueueItem.vacancy_id == vacancy_uuid)

            oldest_result = await db.execute(oldest_query)
            oldest_pending_at = oldest_result.scalar()
            if oldest_pending_at:
                oldest_pending_at = oldest_pending_at.isoformat()

        # Calculate throughput (completed items)
        from datetime import timedelta

        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        # Throughput last 24h
        throughput_24h_query = select(func.count()).select_from(CandidateQueueItem).where(
            CandidateQueueItem.status == QueueStatus.COMPLETED,
            CandidateQueueItem.review_completed_at >= last_24h
        )
        if vacancy_uuid:
            throughput_24h_query = throughput_24h_query.where(
                CandidateQueueItem.vacancy_id == vacancy_uuid
            )

        throughput_24h_result = await db.execute(throughput_24h_query)
        throughput_24h = throughput_24h_result.scalar() or 0

        # Throughput last 7 days
        throughput_7d_query = select(func.count()).select_from(CandidateQueueItem).where(
            CandidateQueueItem.status == QueueStatus.COMPLETED,
            CandidateQueueItem.review_completed_at >= last_7d
        )
        if vacancy_uuid:
            throughput_7d_query = throughput_7d_query.where(
                CandidateQueueItem.vacancy_id == vacancy_uuid
            )

        throughput_7d_result = await db.execute(throughput_7d_query)
        throughput_7d = throughput_7d_result.scalar() or 0

        response_data = {
            "counts": counts_response,
            "average_wait_time_hours": average_wait_time_hours,
            "median_wait_time_hours": median_wait_time_hours,
            "oldest_pending_at": oldest_pending_at,
            "throughput_last_24h": throughput_24h,
            "throughput_last_7d": throughput_7d,
        }

        logger.info(f"Queue metrics: {response_data}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error getting queue metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue metrics: {str(e)}",
        ) from e


@router.get(
    "/{queue_item_id}",
    response_model=QueueItemResponse,
    tags=["Candidate Queue"],
)
async def get_queue_item(
    request: Request,
    queue_item_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific queue item by ID.

    Args:
        request: FastAPI request object
        queue_item_id: Queue item UUID
        db: Database session

    Returns:
        JSON response with queue item details

    Raises:
        HTTPException(400): Invalid queue item ID format
        HTTPException(404): Queue item not found
        HTTPException(500): If data retrieval fails
    """
    try:
        logger.info(f"Fetching queue item: {queue_item_id}")

        from uuid import UUID

        # Parse queue_item_id as UUID
        try:
            queue_uuid = UUID(queue_item_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid queue item ID format: {queue_item_id}",
            )

        # Get the queue item with related data
        query = (
            select(CandidateQueueItem, Resume, JobVacancy)
            .outerjoin(Resume, CandidateQueueItem.resume_id == Resume.id)
            .outerjoin(JobVacancy, CandidateQueueItem.vacancy_id == JobVacancy.id)
            .where(CandidateQueueItem.id == queue_uuid)
        )

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Queue item not found: {queue_item_id}",
            )

        queue_item = row[0]
        resume = row[1]
        vacancy = row[2]

        # Calculate wait time in hours
        now = datetime.now(timezone.utc)
        wait_time_hours = None
        if queue_item.queue_entered_at:
            entered_at = queue_item.queue_entered_at
            if entered_at.tzinfo is None:
                entered_at = entered_at.replace(tzinfo=timezone.utc)
            wait_time_hours = (now - entered_at).total_seconds() / 3600

        item_data = {
            "id": str(queue_item.id),
            "resume_id": str(queue_item.resume_id),
            "filename": resume.filename if resume else None,
            "vacancy_id": str(queue_item.vacancy_id) if queue_item.vacancy_id else None,
            "vacancy_title": vacancy.title if vacancy else None,
            "priority": queue_item.priority.value,
            "status": queue_item.status.value,
            "assigned_recruiter_id": str(queue_item.assigned_recruiter_id) if queue_item.assigned_recruiter_id else None,
            "queue_entered_at": queue_item.queue_entered_at.isoformat() if queue_item.queue_entered_at else None,
            "review_started_at": queue_item.review_started_at.isoformat() if queue_item.review_started_at else None,
            "review_completed_at": queue_item.review_completed_at.isoformat() if queue_item.review_completed_at else None,
            "notes": queue_item.notes,
            "wait_time_hours": round(wait_time_hours, 2) if wait_time_hours is not None else None,
            "created_at": queue_item.created_at.isoformat() if queue_item.created_at else None,
            "updated_at": queue_item.updated_at.isoformat() if queue_item.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=item_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue item {queue_item_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue item: {str(e)}",
        ) from e
