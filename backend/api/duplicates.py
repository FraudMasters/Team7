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
