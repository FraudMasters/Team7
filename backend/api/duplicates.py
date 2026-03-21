"""
Duplicate detection and management endpoints.

This module provides endpoints for listing potential duplicate resumes,
managing the duplicate review queue, and merging duplicate candidates.
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.duplicate_resume import DuplicateResume
from models.duplicate_review import DuplicateReview, ReviewStatus
from models.resume import Resume
from models.merge_history import MergeHistory
from services.candidate_merger import get_candidate_merger, MergeStrategy

logger = logging.getLogger(__name__)

router = APIRouter()


class DuplicateResumeItem(BaseModel):
    """Response model for a single duplicate resume pair."""

    id: str = Field(..., description="Unique identifier of the duplicate record")
    organization_id: str = Field(..., description="Organization ID")
    original_resume_id: str = Field(..., description="ID of the original resume")
    duplicate_resume_id: str = Field(..., description="ID of the duplicate resume")
    original_filename: Optional[str] = Field(None, description="Filename of original resume")
    duplicate_filename: Optional[str] = Field(None, description="Filename of duplicate resume")
    content_hash: str = Field(..., description="SHA-256 hash of the duplicate content")
    detection_timestamp: str = Field(..., description="When the duplicate was detected")
    batch_job_id: Optional[str] = Field(None, description="Batch job ID if from batch upload")


class DuplicateListResponse(BaseModel):
    """Response model for listing duplicate resumes."""

    duplicates: List[DuplicateResumeItem] = Field(..., description="List of duplicate resume pairs")
    total_count: int = Field(..., description="Total number of duplicate pairs")
    organization_id: str = Field(..., description="Organization ID")


class MergeCandidatesRequest(BaseModel):
    """Request model for merging two candidate profiles."""

    primary_id: str = Field(..., description="UUID of the primary resume to keep")
    duplicate_id: str = Field(..., description="UUID of the duplicate resume to merge from")
    reason: Optional[str] = Field(None, description="Optional reason for merging")
    merged_by_user_id: Optional[str] = Field(None, description="ID of user performing the merge")
    strategy: Optional[str] = Field(
        "most_complete",
        description="Merge strategy: most_recent, most_complete, prefer_primary"
    )


class MergeCandidatesResponse(BaseModel):
    """Response model for candidate merge operation."""

    merge_id: str = Field(..., description="UUID of the merge history record")
    primary_resume_id: str = Field(..., description="UUID of the primary resume")
    duplicate_resume_id: str = Field(..., description="UUID of the duplicate resume")
    merge_timestamp: str = Field(..., description="When the merge was performed")
    message: str = Field(..., description="Success message")
    can_undo: bool = Field(..., description="Whether this merge can be undone")
    conflicts_resolved: int = Field(0, description="Number of conflicts resolved")
    conflicts_detected: List[str] = Field(default_factory=list, description="List of fields with conflicts")


# Review queue models
class ReviewQueueItem(BaseModel):
    """Response model for a single review queue item."""

    id: str = Field(..., description="Review queue item ID")
    organization_id: str = Field(..., description="Organization ID")
    original_resume_id: str = Field(..., description="Original resume ID")
    duplicate_resume_id: str = Field(..., description="Duplicate resume ID")
    original_filename: Optional[str] = Field(None, description="Original resume filename")
    duplicate_filename: Optional[str] = Field(None, description="Duplicate resume filename")
    confidence_score: float = Field(..., description="Similarity confidence score (0.0 to 1.0)")
    status: str = Field(..., description="Review status (pending, in_review, approved, rejected)")
    assigned_reviewer_id: Optional[str] = Field(None, description="Assigned reviewer ID")
    queue_entered_at: str = Field(..., description="When duplicate entered the queue")
    review_started_at: Optional[str] = Field(None, description="When review started")
    review_completed_at: Optional[str] = Field(None, description="When review completed")
    decision_reason: Optional[str] = Field(None, description="Reason for approval/rejection")
    batch_job_id: Optional[str] = Field(None, description="Batch job ID if from batch upload")
    wait_time_hours: Optional[float] = Field(None, description="Hours waiting in queue")
    created_at: str = Field(..., description="Record creation timestamp")
    updated_at: str = Field(..., description="Record update timestamp")


class ReviewQueueListResponse(BaseModel):
    """Response model for review queue list."""

    total: int = Field(..., description="Total number of items matching filters")
    items: List[ReviewQueueItem] = Field(..., description="Review queue items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items returned")


class ApproveReviewRequest(BaseModel):
    """Request model for approving a duplicate."""

    decision_reason: Optional[str] = Field(None, description="Optional reason for approval")
    reviewer_id: Optional[str] = Field(None, description="ID of user approving the duplicate")


class ApproveReviewResponse(BaseModel):
    """Response model for approving a duplicate."""

    id: str = Field(..., description="Review queue item ID")
    status: str = Field(..., description="New status (approved)")
    review_completed_at: str = Field(..., description="When review was completed")
    message: str = Field(..., description="Success message")


class RejectReviewRequest(BaseModel):
    """Request model for rejecting a duplicate."""

    decision_reason: Optional[str] = Field(None, description="Optional reason for rejection")
    reviewer_id: Optional[str] = Field(None, description="ID of user rejecting the duplicate")


class RejectReviewResponse(BaseModel):
    """Response model for rejecting a duplicate."""

    id: str = Field(..., description="Review queue item ID")
    status: str = Field(..., description="New status (rejected)")
    review_completed_at: str = Field(..., description="When review was completed")
    message: str = Field(..., description="Success message")


class PreUploadCheckRequest(BaseModel):
    """Request model for pre-upload duplicate check."""

    content_hash: str = Field(..., description="SHA-256 hash of the file content")
    organization_id: str = Field(..., description="Organization ID")
    filename: Optional[str] = Field(None, description="Original filename (optional)")


class DuplicateMatch(BaseModel):
    """Model for a single duplicate match."""

    resume_id: str = Field(..., description="ID of the matching resume")
    filename: str = Field(..., description="Filename of the matching resume")
    detection_timestamp: str = Field(..., description="When the duplicate was detected")
    status: str = Field(..., description="Resume status")


class PreUploadCheckResponse(BaseModel):
    """Response model for pre-upload duplicate check."""

    is_duplicate: bool = Field(..., description="Whether duplicates were found")
    duplicate_count: int = Field(..., description="Number of duplicate matches found")
    matches: List[DuplicateMatch] = Field(default_factory=list, description="List of matching resumes")
    message: str = Field(..., description="Response message")


@router.post(
    "/check",
    response_model=PreUploadCheckResponse,
    status_code=status.HTTP_200_OK,
    tags=["Duplicates"],
)
async def check_duplicate_before_upload(
    request: PreUploadCheckRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Check for duplicate resumes before uploading.

    This endpoint allows checking if a resume with the same content hash already
    exists in the system before uploading. This prevents duplicate uploads and
    provides information about existing matching resumes.

    Args:
        request: Pre-upload check request with content hash and organization ID
        db: Database session

    Returns:
        JSON response indicating if duplicates exist and matching resume details

    Raises:
        HTTPException(400): If request parameters are invalid
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> import hashlib
        >>> # Calculate SHA-256 hash of file content
        >>> with open("resume.pdf", "rb") as f:
        ...     content_hash = hashlib.sha256(f.read()).hexdigest()
        >>> response = requests.post(
        ...     "/api/duplicates/check",
        ...     json={
        ...         "content_hash": content_hash,
        ...         "organization_id": "org-123",
        ...         "filename": "john_doe_resume.pdf"
        ...     }
        ... )
        >>> response.json()
        {
            "is_duplicate": true,
            "duplicate_count": 2,
            "matches": [
                {
                    "resume_id": "resume-uuid-1",
                    "filename": "john_doe_resume.pdf",
                    "detection_timestamp": "2026-03-20T15:30:00Z",
                    "status": "completed"
                },
                {
                    "resume_id": "resume-uuid-2",
                    "filename": "john_doe_cv.pdf",
                    "detection_timestamp": "2026-03-19T10:00:00Z",
                    "status": "completed"
                }
            ],
            "message": "Found 2 duplicate resumes"
        }
    """
    try:
        # Validate request
        if not request.content_hash or not request.content_hash.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="content_hash is required and cannot be empty",
            )

        if not request.organization_id or not request.organization_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id is required and cannot be empty",
            )

        # Validate content_hash format (SHA-256 should be 64 hex characters)
        if len(request.content_hash) != 64 or not all(c in '0123456789abcdefABCDEF' for c in request.content_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="content_hash must be a valid SHA-256 hash (64 hexadecimal characters)",
            )

        logger.info(
            f"Pre-upload duplicate check - organization_id: {request.organization_id}, "
            f"content_hash: {request.content_hash[:16]}..., filename: {request.filename}"
        )

        # Query for existing resumes with the same content hash
        stmt = (
            select(Resume)
            .where(
                Resume.organization_id == request.organization_id,
                Resume.content_hash == request.content_hash
            )
            .order_by(Resume.created_at.desc())
        )

        result = await db.execute(stmt)
        matching_resumes = result.scalars().all()

        duplicate_count = len(matching_resumes)
        is_duplicate = duplicate_count > 0

        # Build list of matching resumes
        matches = []
        for resume in matching_resumes:
            matches.append(
                DuplicateMatch(
                    resume_id=str(resume.id),
                    filename=resume.filename,
                    detection_timestamp=resume.created_at.isoformat(),
                    status=resume.status.value,
                )
            )

        # Build response message
        if is_duplicate:
            message = f"Found {duplicate_count} duplicate resume{'s' if duplicate_count > 1 else ''}"
        else:
            message = "No duplicates found"

        logger.info(
            f"Pre-upload check complete - organization_id: {request.organization_id}, "
            f"is_duplicate: {is_duplicate}, count: {duplicate_count}"
        )

        response_data = PreUploadCheckResponse(
            is_duplicate=is_duplicate,
            duplicate_count=duplicate_count,
            matches=matches,
            message=message,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking for duplicates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check for duplicates: {str(e)}",
        )


@router.get(
    "",
    response_model=DuplicateListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Duplicates"],
)
async def list_duplicates(
    organization_id: str = Query(..., description="Organization ID to filter duplicates"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List potential duplicate resumes for an organization.

    This endpoint returns all detected duplicate resume pairs for a given organization,
    with pagination support. Each duplicate pair includes the original and duplicate
    resume IDs, filenames, detection timestamp, and content hash.

    Args:
        organization_id: Organization ID to filter duplicates
        limit: Maximum number of results to return (default: 100, max: 1000)
        offset: Number of results to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of duplicate resume pairs and total count

    Raises:
        HTTPException(400): If organization_id is invalid
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/duplicates?organization_id=org-123&limit=50&offset=0"
        ... )
        >>> response.json()
        {
            "duplicates": [
                {
                    "id": "dup-uuid",
                    "organization_id": "org-123",
                    "original_resume_id": "resume-1",
                    "duplicate_resume_id": "resume-2",
                    "original_filename": "john_doe_resume.pdf",
                    "duplicate_filename": "john_doe_resume_copy.pdf",
                    "content_hash": "abc123...",
                    "detection_timestamp": "2026-03-21T10:30:00Z",
                    "batch_job_id": "batch-123"
                }
            ],
            "total_count": 15,
            "organization_id": "org-123"
        }
    """
    try:
        # Validate organization_id
        if not organization_id or not organization_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id is required and cannot be empty",
            )

        logger.info(
            f"Listing duplicates for organization: {organization_id}, "
            f"limit={limit}, offset={offset}"
        )

        # Get total count
        count_stmt = (
            select(func.count(DuplicateResume.id))
            .where(DuplicateResume.organization_id == organization_id)
        )
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # Get duplicate records with related resume data
        stmt = (
            select(DuplicateResume)
            .where(DuplicateResume.organization_id == organization_id)
            .options(
                selectinload(DuplicateResume.original_resume),
                selectinload(DuplicateResume.duplicate_resume),
            )
            .order_by(DuplicateResume.detection_timestamp.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        duplicates = result.scalars().all()

        logger.info(
            f"Found {len(duplicates)} duplicates (total: {total_count}) "
            f"for organization: {organization_id}"
        )

        # Build response
        duplicate_items = []
        for dup in duplicates:
            # Get filenames from related resume objects if available
            original_filename = None
            duplicate_filename = None

            if dup.original_resume:
                original_filename = dup.original_resume.filename
            if dup.duplicate_resume:
                duplicate_filename = dup.duplicate_resume.filename

            duplicate_items.append(
                DuplicateResumeItem(
                    id=str(dup.id),
                    organization_id=dup.organization_id,
                    original_resume_id=str(dup.original_resume_id),
                    duplicate_resume_id=str(dup.duplicate_resume_id),
                    original_filename=original_filename,
                    duplicate_filename=duplicate_filename,
                    content_hash=dup.content_hash,
                    detection_timestamp=dup.detection_timestamp.isoformat(),
                    batch_job_id=str(dup.batch_job_id) if dup.batch_job_id else None,
                )
            )

        response_data = DuplicateListResponse(
            duplicates=duplicate_items,
            total_count=total_count,
            organization_id=organization_id,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing duplicates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve duplicates: {str(e)}",
        )


@router.post(
    "/merge",
    response_model=MergeCandidatesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Duplicates"],
)
async def merge_candidates(
    request: MergeCandidatesRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Merge two candidate profiles into a single profile.

    This endpoint merges a duplicate resume into a primary resume, creating
    a merge history record for audit and undo capability. The primary resume
    is retained while the duplicate is marked as merged.

    Args:
        request: Merge request containing primary_id and duplicate_id
        db: Database session

    Returns:
        JSON response with merge operation details

    Raises:
        HTTPException(400): If request is invalid or resume IDs are the same
        HTTPException(404): If either resume is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/duplicates/merge",
        ...     json={
        ...         "primary_id": "resume-uuid-1",
        ...         "duplicate_id": "resume-uuid-2",
        ...         "reason": "Same candidate, keep most recent resume"
        ...     }
        ... )
        >>> response.json()
        {
            "merge_id": "merge-uuid",
            "primary_resume_id": "resume-uuid-1",
            "duplicate_resume_id": "resume-uuid-2",
            "merge_timestamp": "2026-03-21T10:30:00Z",
            "message": "Successfully merged candidates",
            "can_undo": true
        }
    """
    try:
        # Validate request
        if not request.primary_id or not request.primary_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="primary_id is required and cannot be empty",
            )

        if not request.duplicate_id or not request.duplicate_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="duplicate_id is required and cannot be empty",
            )

        if request.primary_id == request.duplicate_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="primary_id and duplicate_id must be different",
            )

        logger.info(
            f"Merging candidates: primary={request.primary_id}, "
            f"duplicate={request.duplicate_id}"
        )

        # Validate both resumes exist
        primary_stmt = select(Resume).where(Resume.id == request.primary_id)
        primary_result = await db.execute(primary_stmt)
        primary_resume = primary_result.scalar_one_or_none()

        if not primary_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Primary resume not found: {request.primary_id}",
            )

        duplicate_stmt = select(Resume).where(Resume.id == request.duplicate_id)
        duplicate_result = await db.execute(duplicate_stmt)
        duplicate_resume = duplicate_result.scalar_one_or_none()

        if not duplicate_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Duplicate resume not found: {request.duplicate_id}",
            )

        # Verify both resumes belong to the same organization
        if primary_resume.organization_id != duplicate_resume.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot merge resumes from different organizations",
            )

        # Use CandidateMerger service to perform actual data merge
        merger = get_candidate_merger(db)

        try:
            # Perform the merge using CandidateMerger service
            merge_result = await merger.merge_candidates(
                primary_resume_id=str(request.primary_id),
                duplicate_resume_id=str(request.duplicate_id),
                strategy=request.strategy or MergeStrategy.MOST_COMPLETE,
            )

            logger.info(
                f"Merge result: {merge_result.conflicts_resolved} conflicts resolved, "
                f"{len(merge_result.conflicts_detected)} conflicts detected"
            )

            # Apply merged data to primary resume
            # Note: merge_result.merged_data contains the merged Resume fields
            for field, value in merge_result.merged_data.get("resume", {}).items():
                if hasattr(primary_resume, field) and field not in ["id", "created_at"]:
                    setattr(primary_resume, field, value)

            # Apply merged analysis data if ResumeAnalysis exists
            # This is handled by CandidateMerger.merge_candidates internally

            # Save merge history using the service (includes undo data)
            merge_history = await merger.save_merge_history(
                source_resume_id=str(request.duplicate_id),
                target_resume_id=str(request.primary_id),
                organization_id=str(primary_resume.organization_id),
                merge_result=merge_result,
                merged_by_user_id=request.merged_by_user_id,
                reason=request.reason,
                can_undo=True,
            )

        except ValueError as e:
            logger.error(f"Merge validation error: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid merge request: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Merge operation failed: {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to merge candidates: {str(e)}",
            )

        await db.commit()
        await db.refresh(merge_history)

        logger.info(
            f"Successfully merged candidates: merge_id={merge_history.id}, "
            f"primary={request.primary_id}, duplicate={request.duplicate_id}, "
            f"conflicts_resolved={merge_result.conflicts_resolved}"
        )

        response_data = MergeCandidatesResponse(
            merge_id=str(merge_history.id),
            primary_resume_id=str(request.primary_id),
            duplicate_resume_id=str(request.duplicate_id),
            merge_timestamp=merge_history.merge_timestamp.isoformat(),
            message=f"Successfully merged candidates ({merge_result.conflicts_resolved} conflicts resolved)",
            can_undo=merge_history.can_undo,
            conflicts_resolved=merge_result.conflicts_resolved,
            conflicts_detected=merge_result.conflicts_detected,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging candidates: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge candidates: {str(e)}",
        )


@router.get(
    "/review-queue",
    response_model=ReviewQueueListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Duplicates"],
)
async def list_review_queue(
    organization_id: str = Query(..., description="Organization ID to filter review queue"),
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, in_review, approved, rejected)"),
    assigned_reviewer_id: Optional[str] = Query(None, description="Filter by assigned reviewer ID"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum confidence score"),
    sort_by: Optional[str] = Query("confidence_score", description="Sort by: confidence_score, wait_time, created_at"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List duplicates in the review queue with filtering and sorting.

    Returns a paginated list of duplicate review items with their associated resume
    information. Supports filtering by status, reviewer, and confidence score range.

    Default sorting is by confidence score (highest first), then by wait time (oldest first).

    Args:
        organization_id: Organization ID to filter review queue
        status_filter: Optional filter by review status
        assigned_reviewer_id: Optional filter by assigned reviewer
        min_confidence: Optional minimum confidence score filter
        max_confidence: Optional maximum confidence score filter
        sort_by: Sort field (confidence_score, wait_time, created_at)
        sort_order: Sort order (asc or desc)
        skip: Number of items to skip for pagination
        limit: Maximum number of items to return
        db: Database session

    Returns:
        JSON response with list of review queue items

    Raises:
        HTTPException(400): Invalid filter parameter format
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all pending items
        >>> response = requests.get("/api/duplicates/review-queue?organization_id=org-123&status_filter=pending")
        >>> # Get high confidence items
        >>> response = requests.get("/api/duplicates/review-queue?organization_id=org-123&min_confidence=0.8")
        >>> # Sort by wait time (oldest first)
        >>> response = requests.get("/api/duplicates/review-queue?organization_id=org-123&sort_by=wait_time&sort_order=asc")
    """
    try:
        # Validate organization_id
        if not organization_id or not organization_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id is required and cannot be empty",
            )

        logger.info(
            f"Fetching review queue - organization_id: {organization_id}, "
            f"status_filter: {status_filter}, assigned_reviewer_id: {assigned_reviewer_id}, "
            f"skip: {skip}, limit: {limit}"
        )

        # Build query filters
        filters = [DuplicateReview.organization_id == organization_id]

        if status_filter:
            try:
                status_enum = ReviewStatus(status_filter)
                filters.append(DuplicateReview.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}. Must be one of: pending, in_review, approved, rejected",
                )

        if assigned_reviewer_id:
            filters.append(DuplicateReview.assigned_reviewer_id == assigned_reviewer_id)

        if min_confidence is not None:
            filters.append(DuplicateReview.confidence_score >= min_confidence)

        if max_confidence is not None:
            filters.append(DuplicateReview.confidence_score <= max_confidence)

        # Get total count
        count_stmt = select(func.count(DuplicateReview.id)).where(*filters)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # Build sort clause
        if sort_by == "confidence_score":
            sort_column = DuplicateReview.confidence_score
        elif sort_by == "wait_time":
            sort_column = DuplicateReview.queue_entered_at
        elif sort_by == "created_at":
            sort_column = DuplicateReview.created_at
        else:
            sort_column = DuplicateReview.confidence_score

        if sort_order == "asc":
            sort_clause = sort_column.asc()
        else:
            sort_clause = sort_column.desc()

        # Get review queue items with related resume data
        stmt = (
            select(DuplicateReview)
            .where(*filters)
            .options(
                selectinload(DuplicateReview.original_resume),
                selectinload(DuplicateReview.duplicate_resume),
            )
            .order_by(sort_clause)
            .limit(limit)
            .offset(skip)
        )

        result = await db.execute(stmt)
        review_items = result.scalars().all()

        logger.info(
            f"Found {len(review_items)} review items (total: {total_count}) "
            f"for organization: {organization_id}"
        )

        # Build response
        queue_items = []
        now = datetime.utcnow()

        for item in review_items:
            # Get filenames from related resume objects if available
            original_filename = None
            duplicate_filename = None

            if item.original_resume:
                original_filename = item.original_resume.filename
            if item.duplicate_resume:
                duplicate_filename = item.duplicate_resume.filename

            # Calculate wait time in hours
            wait_time_hours = None
            if item.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
                wait_time_delta = now - item.queue_entered_at
                wait_time_hours = wait_time_delta.total_seconds() / 3600

            queue_items.append(
                ReviewQueueItem(
                    id=str(item.id),
                    organization_id=item.organization_id,
                    original_resume_id=str(item.original_resume_id),
                    duplicate_resume_id=str(item.duplicate_resume_id),
                    original_filename=original_filename,
                    duplicate_filename=duplicate_filename,
                    confidence_score=item.confidence_score,
                    status=item.status.value,
                    assigned_reviewer_id=item.assigned_reviewer_id,
                    queue_entered_at=item.queue_entered_at.isoformat(),
                    review_started_at=item.review_started_at.isoformat() if item.review_started_at else None,
                    review_completed_at=item.review_completed_at.isoformat() if item.review_completed_at else None,
                    decision_reason=item.decision_reason,
                    batch_job_id=str(item.batch_job_id) if item.batch_job_id else None,
                    wait_time_hours=wait_time_hours,
                    created_at=item.created_at.isoformat(),
                    updated_at=item.updated_at.isoformat(),
                )
            )

        response_data = ReviewQueueListResponse(
            total=total_count,
            items=queue_items,
            skip=skip,
            limit=limit,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review queue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve review queue: {str(e)}",
        )


@router.post(
    "/review-queue/{review_id}/approve",
    response_model=ApproveReviewResponse,
    status_code=status.HTTP_200_OK,
    tags=["Duplicates"],
)
async def approve_duplicate(
    review_id: str,
    request: ApproveReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Approve a duplicate in the review queue.

    Marks a duplicate review item as approved, indicating that the two resumes
    are confirmed to be duplicates and should be merged. Updates the status to
    'approved' and records the completion timestamp and decision reason.

    Args:
        review_id: UUID of the review queue item to approve
        request: Approval request with optional decision reason and reviewer ID
        db: Database session

    Returns:
        JSON response with updated review item details

    Raises:
        HTTPException(400): If review_id is invalid
        HTTPException(404): If review item is not found
        HTTPException(409): If review item is already approved or rejected
        HTTPException(500): If database update fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/duplicates/review-queue/review-uuid/approve",
        ...     json={
        ...         "decision_reason": "Confirmed same candidate by email and phone",
        ...         "reviewer_id": "user-123"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "review-uuid",
            "status": "approved",
            "review_completed_at": "2026-03-21T10:30:00Z",
            "message": "Duplicate approved successfully"
        }
    """
    try:
        # Validate review_id
        if not review_id or not review_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="review_id is required and cannot be empty",
            )

        logger.info(f"Approving duplicate review: {review_id}")

        # Find the review item
        stmt = select(DuplicateReview).where(DuplicateReview.id == review_id)
        result = await db.execute(stmt)
        review_item = result.scalar_one_or_none()

        if not review_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review item not found: {review_id}",
            )

        # Check if already completed
        if review_item.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Review item already completed with status: {review_item.status.value}",
            )

        # Update the review item
        review_item.status = ReviewStatus.APPROVED
        review_item.review_completed_at = datetime.utcnow()

        if request.decision_reason:
            review_item.decision_reason = request.decision_reason

        if request.reviewer_id:
            review_item.assigned_reviewer_id = request.reviewer_id

        # Set review_started_at if not already set
        if not review_item.review_started_at:
            review_item.review_started_at = datetime.utcnow()

        await db.commit()
        await db.refresh(review_item)

        logger.info(f"Successfully approved duplicate review: {review_id}")

        response_data = ApproveReviewResponse(
            id=str(review_item.id),
            status=review_item.status.value,
            review_completed_at=review_item.review_completed_at.isoformat(),
            message="Duplicate approved successfully",
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving duplicate review: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve duplicate: {str(e)}",
        )


@router.post(
    "/review-queue/{review_id}/reject",
    response_model=RejectReviewResponse,
    status_code=status.HTTP_200_OK,
    tags=["Duplicates"],
)
async def reject_duplicate(
    review_id: str,
    request: RejectReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Reject a duplicate in the review queue.

    Marks a duplicate review item as rejected, indicating that the two resumes
    are NOT duplicates and should remain as separate candidates. Updates the
    status to 'rejected' and records the completion timestamp and decision reason.

    Args:
        review_id: UUID of the review queue item to reject
        request: Rejection request with optional decision reason and reviewer ID
        db: Database session

    Returns:
        JSON response with updated review item details

    Raises:
        HTTPException(400): If review_id is invalid
        HTTPException(404): If review item is not found
        HTTPException(409): If review item is already approved or rejected
        HTTPException(500): If database update fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/duplicates/review-queue/review-uuid/reject",
        ...     json={
        ...         "decision_reason": "Different candidates with similar names",
        ...         "reviewer_id": "user-123"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "review-uuid",
            "status": "rejected",
            "review_completed_at": "2026-03-21T10:30:00Z",
            "message": "Duplicate rejected successfully"
        }
    """
    try:
        # Validate review_id
        if not review_id or not review_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="review_id is required and cannot be empty",
            )

        logger.info(f"Rejecting duplicate review: {review_id}")

        # Find the review item
        stmt = select(DuplicateReview).where(DuplicateReview.id == review_id)
        result = await db.execute(stmt)
        review_item = result.scalar_one_or_none()

        if not review_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review item not found: {review_id}",
            )

        # Check if already completed
        if review_item.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Review item already completed with status: {review_item.status.value}",
            )

        # Update the review item
        review_item.status = ReviewStatus.REJECTED
        review_item.review_completed_at = datetime.utcnow()

        if request.decision_reason:
            review_item.decision_reason = request.decision_reason

        if request.reviewer_id:
            review_item.assigned_reviewer_id = request.reviewer_id

        # Set review_started_at if not already set
        if not review_item.review_started_at:
            review_item.review_started_at = datetime.utcnow()

        await db.commit()
        await db.refresh(review_item)

        logger.info(f"Successfully rejected duplicate review: {review_id}")

        response_data = RejectReviewResponse(
            id=str(review_item.id),
            status=review_item.status.value,
            review_completed_at=review_item.review_completed_at.isoformat(),
            message="Duplicate rejected successfully",
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting duplicate review: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject duplicate: {str(e)}",
        )


class ScanExistingResponse(BaseModel):
    """Response model for bulk duplicate scan of existing database."""

    total_resumes_scanned: int = Field(..., description="Total number of resumes scanned")
    duplicates_found: int = Field(..., description="Number of duplicate pairs found")
    duplicates_recorded: int = Field(..., description="Number of duplicates successfully recorded")
    errors: int = Field(0, description="Number of errors encountered during scan")
    organization_id: str = Field(..., description="Organization ID")
    message: str = Field(..., description="Success message")


@router.post(
    "/scan-existing",
    response_model=ScanExistingResponse,
    status_code=status.HTTP_200_OK,
    tags=["Duplicates"],
)
async def scan_existing_database(
    request: Request,
    organization_id: Optional[str] = Query(None, description="Organization ID to scan for duplicates"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Scan existing database for duplicate resumes.

    This endpoint performs a bulk duplicate detection scan on all resumes in the
    organization's database. It computes content hashes for all resume files,
    identifies duplicates, and records them in the DuplicateResume table.

    This is useful for:
    - Initial setup: detecting duplicates in an existing database
    - Periodic maintenance: finding duplicates that may have bypassed detection
    - Data cleanup: identifying duplicate files uploaded before duplicate detection was enabled

    Args:
        organization_id: Organization ID to scan for duplicates
        db: Database session

    Returns:
        JSON response with scan statistics and duplicate count

    Raises:
        HTTPException(400): If organization_id is invalid
        HTTPException(500): If scan fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/duplicates/scan-existing",
        ...     params={"organization_id": "org-123"}
        ... )
        >>> response.json()
        {
            "total_resumes_scanned": 1500,
            "duplicates_found": 25,
            "duplicates_recorded": 25,
            "errors": 0,
            "organization_id": "org-123",
            "message": "Successfully scanned 1500 resumes and found 25 duplicates"
        }
    """
    try:
        # Import organization context utility
        from middleware.organization_context import get_organization_context

        # Get organization_id from query parameter or request context
        if not organization_id:
            organization_id = get_organization_context(request)

        # Validate organization_id
        if not organization_id or not organization_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id is required (provide as query parameter or in X-Organization-ID header)",
            )

        logger.info(f"Starting bulk duplicate scan for organization: {organization_id}")

        # Import utilities
        from utils.duplicate_detector import compute_content_hash_from_file, record_duplicate
        from pathlib import Path

        # Get all resumes for this organization that have files
        stmt = (
            select(Resume)
            .where(Resume.organization_id == organization_id)
            .where(Resume.file_path.isnot(None))
            .where(Resume.status != "FAILED")
            .order_by(Resume.created_at.asc())
        )

        result = await db.execute(stmt)
        resumes = result.scalars().all()

        total_scanned = len(resumes)
        logger.info(f"Found {total_scanned} resumes to scan for organization: {organization_id}")

        if total_scanned == 0:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=ScanExistingResponse(
                    total_resumes_scanned=0,
                    duplicates_found=0,
                    duplicates_recorded=0,
                    errors=0,
                    organization_id=organization_id,
                    message="No resumes found to scan",
                ).model_dump(),
            )

        # Build hash lookup: hash -> list of resume IDs
        hash_lookup = {}
        errors = 0

        for resume in resumes:
            try:
                # Skip if file doesn't exist
                file_path = Path(resume.file_path)
                if not file_path.exists():
                    logger.warning(f"Resume file not found: {resume.file_path}")
                    errors += 1
                    continue

                # Compute content hash
                content_hash = compute_content_hash_from_file(file_path)

                # Update resume's content_hash if not set
                if not resume.content_hash:
                    resume.content_hash = content_hash

                # Track hash -> resume mappings
                if content_hash not in hash_lookup:
                    hash_lookup[content_hash] = []
                hash_lookup[content_hash].append(resume)

            except Exception as e:
                logger.error(f"Error processing resume {resume.id}: {e}")
                errors += 1
                continue

        # Find duplicates: any hash with multiple resumes
        duplicates_found = 0
        duplicates_recorded = 0

        for content_hash, resume_list in hash_lookup.items():
            if len(resume_list) > 1:
                # Sort by creation date to identify the original
                resume_list.sort(key=lambda r: r.created_at)
                original_resume = resume_list[0]

                # All others are duplicates
                for duplicate_resume in resume_list[1:]:
                    duplicates_found += 1

                    # Check if this duplicate is already recorded
                    check_stmt = (
                        select(DuplicateResume)
                        .where(DuplicateResume.organization_id == organization_id)
                        .where(DuplicateResume.original_resume_id == str(original_resume.id))
                        .where(DuplicateResume.duplicate_resume_id == str(duplicate_resume.id))
                    )
                    check_result = await db.execute(check_stmt)
                    existing = check_result.scalar_one_or_none()

                    if existing:
                        logger.debug(
                            f"Duplicate already recorded: original={original_resume.id}, "
                            f"duplicate={duplicate_resume.id}"
                        )
                        continue

                    # Record the duplicate
                    success = await record_duplicate(
                        original_resume_id=str(original_resume.id),
                        duplicate_resume_id=str(duplicate_resume.id),
                        content_hash=content_hash,
                        organization_id=organization_id,
                        db_session=db,
                        batch_job_id=None,
                        match_type="exact",
                        similarity_score=1.0,
                    )

                    if success:
                        duplicates_recorded += 1
                        logger.debug(
                            f"Recorded duplicate: original={original_resume.id}, "
                            f"duplicate={duplicate_resume.id}"
                        )
                    else:
                        errors += 1

        # Commit all changes
        await db.commit()

        logger.info(
            f"Bulk duplicate scan completed for organization {organization_id}: "
            f"scanned={total_scanned}, found={duplicates_found}, "
            f"recorded={duplicates_recorded}, errors={errors}"
        )

        response_data = ScanExistingResponse(
            total_resumes_scanned=total_scanned,
            duplicates_found=duplicates_found,
            duplicates_recorded=duplicates_recorded,
            errors=errors,
            organization_id=organization_id,
            message=f"Successfully scanned {total_scanned} resumes and found {duplicates_found} duplicates",
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during bulk duplicate scan: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan for duplicates: {str(e)}",
        )
