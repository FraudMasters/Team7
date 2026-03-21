"""
Duplicate detection and management endpoints.

This module provides endpoints for listing potential duplicate resumes,
managing the duplicate review queue, and merging duplicate candidates.
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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


class MergeCandidatesResponse(BaseModel):
    """Response model for candidate merge operation."""

    merge_id: str = Field(..., description="UUID of the merge history record")
    primary_resume_id: str = Field(..., description="UUID of the primary resume")
    duplicate_resume_id: str = Field(..., description="UUID of the duplicate resume")
    merge_timestamp: str = Field(..., description="When the merge was performed")
    message: str = Field(..., description="Success message")
    can_undo: bool = Field(..., description="Whether this merge can be undone")


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

        # Create merge history record
        merge_timestamp = datetime.utcnow()
        merge_history = MergeHistory(
            organization_id=primary_resume.organization_id,
            source_resume_id=request.duplicate_id,
            target_resume_id=request.primary_id,
            merged_by_user_id=request.merged_by_user_id,
            merge_timestamp=merge_timestamp,
            merge_data={
                "primary_filename": primary_resume.filename,
                "duplicate_filename": duplicate_resume.filename,
                "primary_status": primary_resume.status.value,
                "duplicate_status": duplicate_resume.status.value,
            },
            undo_data={
                "duplicate_resume_id": request.duplicate_id,
                "duplicate_organization_id": duplicate_resume.organization_id,
                "duplicate_vacancy_id": duplicate_resume.vacancy_id,
            },
            reason=request.reason,
            can_undo=True,
        )

        db.add(merge_history)

        # TODO: In phase 3, implement actual data merging logic via CandidateMerger service
        # For now, we just create the merge history record

        await db.commit()
        await db.refresh(merge_history)

        logger.info(
            f"Successfully merged candidates: merge_id={merge_history.id}, "
            f"primary={request.primary_id}, duplicate={request.duplicate_id}"
        )

        response_data = MergeCandidatesResponse(
            merge_id=str(merge_history.id),
            primary_resume_id=str(request.primary_id),
            duplicate_resume_id=str(request.duplicate_id),
            merge_timestamp=merge_timestamp.isoformat(),
            message="Successfully merged candidates",
            can_undo=merge_history.can_undo,
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
