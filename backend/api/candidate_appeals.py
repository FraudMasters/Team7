"""
Candidate appeals management endpoints.

This module provides endpoints for managing candidate appeals against AI ranking
decisions. Candidates can submit appeals with additional context and supporting
documentation, while recruiters can review and take action on appeals through
dedicated workflows. Supports multiple appeal types and status tracking.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candidate_appeal import CandidateAppeal
from schemas.candidate_appeal import (
    AppealCreate,
    AppealResponse,
    AppealListResponse,
    AppealReviewRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=AppealResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidate Appeals"],
)
async def create_appeal(
    request: AppealCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Submit a candidate appeal against a ranking decision.

    This endpoint allows candidates to challenge their AI-generated ranking by
    providing additional context, skills, or documentation that may have been
    missed during initial evaluation. Appeals are reviewed by recruiters who can
    accept, reject, or trigger re-ranking based on the new information provided.

    Args:
        request: Appeal creation request with rank ID, email, type, and explanation
        db: Database session

    Returns:
        JSON response with created appeal details

    Raises:
        HTTPException(422): If validation fails (e.g., invalid email, appeal text too short)
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "candidate_rank_id": "abc-123-uuid",
        ...     "candidate_email": "candidate@example.com",
        ...     "appeal_type": "ranking_position",
        ...     "appeal_text": "I have 5 years of experience with React and advanced TypeScript skills",
        ...     "supporting_documents": {
        ...         "documents": [
        ...             {"filename": "react-cert.pdf", "url": "s3://bucket/cert.pdf", "type": "certification"}
        ...         ]
        ...     }
        ... }
        >>> response = requests.post("/api/candidate-appeals/", json=data)
        >>> response.json()
        {
            "id": "...",
            "status": "pending",
            ...
        }
    """
    try:
        logger.info(f"Creating appeal for candidate rank {request.candidate_rank_id}")

        # Validate appeal type
        valid_appeal_types = ["ranking_position", "score_explanation", "missing_skills"]
        if request.appeal_type not in valid_appeal_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid appeal_type. Must be one of: {', '.join(valid_appeal_types)}",
            )

        # Parse candidate_rank_id to UUID
        try:
            candidate_rank_uuid = UUID(request.candidate_rank_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format for candidate_rank_id: {e}",
            )

        # Create appeal object
        appeal = CandidateAppeal(
            candidate_rank_id=candidate_rank_uuid,
            candidate_email=request.candidate_email,
            appeal_type=request.appeal_type,
            appeal_text=request.appeal_text,
            supporting_documents=request.supporting_documents,
            status="pending",
        )

        # Save to database
        db.add(appeal)
        await db.commit()
        await db.refresh(appeal)

        # Build response
        appeal_response = {
            "id": str(appeal.id),
            "candidate_rank_id": str(appeal.candidate_rank_id),
            "candidate_email": appeal.candidate_email,
            "appeal_type": appeal.appeal_type,
            "appeal_text": appeal.appeal_text,
            "supporting_documents": appeal.supporting_documents,
            "status": appeal.status,
            "reviewer_id": str(appeal.reviewer_id) if appeal.reviewer_id else None,
            "review_notes": appeal.review_notes,
            "resolution_outcome": appeal.resolution_outcome,
            "created_at": appeal.created_at.isoformat() if appeal.created_at else None,
            "updated_at": appeal.updated_at.isoformat() if appeal.updated_at else None,
        }

        logger.info(f"Created appeal {appeal.id} with status 'pending'")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=appeal_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appeal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appeal: {str(e)}",
        ) from e


@router.get(
    "/{appeal_id}",
    response_model=AppealResponse,
    tags=["Candidate Appeals"],
)
async def get_appeal(
    appeal_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific appeal by ID.

    This endpoint retrieves the full details of a candidate appeal, including
    current status, review notes (if applicable), and resolution outcome. Used
    by both candidates to track their appeal status and recruiters to view
    appeal details for review.

    Args:
        appeal_id: UUID of the appeal to retrieve
        db: Database session

    Returns:
        JSON response with appeal details

    Raises:
        HTTPException(404): If appeal not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/candidate-appeals/abc-123-uuid")
        >>> response.json()
        {
            "id": "abc-123-uuid",
            "status": "under_review",
            ...
        }
    """
    try:
        logger.info(f"Retrieving appeal {appeal_id}")

        # Parse appeal_id to UUID
        try:
            appeal_uuid = UUID(appeal_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Query database
        query = select(CandidateAppeal).where(CandidateAppeal.id == appeal_uuid)
        result = await db.execute(query)
        appeal = result.scalar_one_or_none()

        if not appeal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appeal {appeal_id} not found",
            )

        # Build response
        appeal_response = {
            "id": str(appeal.id),
            "candidate_rank_id": str(appeal.candidate_rank_id),
            "candidate_email": appeal.candidate_email,
            "appeal_type": appeal.appeal_type,
            "appeal_text": appeal.appeal_text,
            "supporting_documents": appeal.supporting_documents,
            "status": appeal.status,
            "reviewer_id": str(appeal.reviewer_id) if appeal.reviewer_id else None,
            "review_notes": appeal.review_notes,
            "resolution_outcome": appeal.resolution_outcome,
            "created_at": appeal.created_at.isoformat() if appeal.created_at else None,
            "updated_at": appeal.updated_at.isoformat() if appeal.updated_at else None,
        }

        logger.info(f"Retrieved appeal {appeal_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=appeal_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving appeal {appeal_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appeal: {str(e)}",
        ) from e


@router.get("/", tags=["Candidate Appeals"])
async def list_appeals(
    candidate_email: Optional[str] = Query(None, description="Filter by candidate email"),
    candidate_rank_id: Optional[str] = Query(None, description="Filter by candidate rank ID"),
    appeal_type: Optional[str] = Query(None, description="Filter by appeal type"),
    status: Optional[str] = Query(None, description="Filter by appeal status"),
    reviewer_id: Optional[str] = Query(None, description="Filter by reviewer ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List appeals with optional filters.

    This endpoint returns a list of candidate appeals filtered by various criteria.
    Recruiters can use this to view all pending appeals for review, while candidates
    can use it to track their submitted appeals by providing their email address.

    Args:
        candidate_email: Optional filter by candidate email
        candidate_rank_id: Optional filter by candidate rank ID
        appeal_type: Optional filter by appeal type
        status: Optional filter by status (pending, under_review, accepted, rejected)
        reviewer_id: Optional filter by reviewer ID
        db: Database session

    Returns:
        JSON response with list of appeals and total count

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> # Get all pending appeals
        >>> response = requests.get("/api/candidate-appeals/?status=pending")
        >>> response.json()
        {
            "appeals": [...],
            "total_count": 5
        }

        >>> # Get appeals for specific candidate
        >>> response = requests.get("/api/candidate-appeals/?candidate_email=test@example.com")
        >>> response.json()
        {
            "appeals": [...],
            "total_count": 2
        }
    """
    try:
        logger.info(
            f"Listing appeals with filters: email={candidate_email}, "
            f"rank_id={candidate_rank_id}, type={appeal_type}, status={status}, "
            f"reviewer_id={reviewer_id}"
        )

        # Build query with filters
        query = select(CandidateAppeal)

        if candidate_email:
            query = query.where(CandidateAppeal.candidate_email == candidate_email)

        if candidate_rank_id:
            try:
                rank_uuid = UUID(candidate_rank_id)
                query = query.where(CandidateAppeal.candidate_rank_id == rank_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid UUID format for candidate_rank_id",
                )

        if appeal_type:
            query = query.where(CandidateAppeal.appeal_type == appeal_type)

        if status:
            query = query.where(CandidateAppeal.status == status)

        if reviewer_id:
            try:
                reviewer_uuid = UUID(reviewer_id)
                query = query.where(CandidateAppeal.reviewer_id == reviewer_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid UUID format for reviewer_id",
                )

        # Execute query
        result = await db.execute(query)
        appeals_db = result.scalars().all()

        # Build response
        appeals = []
        for appeal in appeals_db:
            appeals.append({
                "id": str(appeal.id),
                "candidate_rank_id": str(appeal.candidate_rank_id),
                "candidate_email": appeal.candidate_email,
                "appeal_type": appeal.appeal_type,
                "appeal_text": appeal.appeal_text,
                "supporting_documents": appeal.supporting_documents,
                "status": appeal.status,
                "reviewer_id": str(appeal.reviewer_id) if appeal.reviewer_id else None,
                "review_notes": appeal.review_notes,
                "resolution_outcome": appeal.resolution_outcome,
                "created_at": appeal.created_at.isoformat() if appeal.created_at else None,
                "updated_at": appeal.updated_at.isoformat() if appeal.updated_at else None,
            })

        response_data = {
            "appeals": appeals,
            "total_count": len(appeals),
        }

        logger.info(f"Retrieved {len(appeals)} appeals")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing appeals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list appeals: {str(e)}",
        ) from e


@router.patch(
    "/{appeal_id}/review",
    response_model=AppealResponse,
    tags=["Candidate Appeals"],
)
async def review_appeal(
    appeal_id: str,
    request: AppealReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Review and update the status of an appeal (recruiter action).

    This endpoint allows recruiters to review candidate appeals and update the
    status (under_review, accepted, rejected) along with review notes and
    resolution outcomes. When an appeal is accepted, it may trigger a re-ranking
    workflow to incorporate the additional information provided by the candidate.

    Args:
        appeal_id: UUID of the appeal to review
        request: Review request with status, notes, and outcome
        db: Database session

    Returns:
        JSON response with updated appeal details

    Raises:
        HTTPException(404): If appeal not found
        HTTPException(422): If validation fails (e.g., invalid status)
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "status": "accepted",
        ...     "review_notes": "Valid additional skills identified",
        ...     "resolution_outcome": "Re-ranked candidate with updated skill profile"
        ... }
        >>> response = requests.patch("/api/candidate-appeals/abc-123/review", json=data)
        >>> response.json()
        {
            "id": "abc-123",
            "status": "accepted",
            "resolution_outcome": "Re-ranked candidate with updated skill profile",
            ...
        }
    """
    try:
        logger.info(f"Reviewing appeal {appeal_id}")

        # Validate status
        valid_statuses = ["pending", "under_review", "accepted", "rejected"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        # Parse appeal_id to UUID
        try:
            appeal_uuid = UUID(appeal_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Query database
        query = select(CandidateAppeal).where(CandidateAppeal.id == appeal_uuid)
        result = await db.execute(query)
        appeal = result.scalar_one_or_none()

        if not appeal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appeal {appeal_id} not found",
            )

        # Update appeal fields
        appeal.status = request.status
        if request.review_notes is not None:
            appeal.review_notes = request.review_notes
        if request.resolution_outcome is not None:
            appeal.resolution_outcome = request.resolution_outcome
        if request.reviewer_id is not None:
            try:
                reviewer_uuid = UUID(request.reviewer_id)
                appeal.reviewer_id = reviewer_uuid
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid UUID format for reviewer_id",
                )

        # Commit changes
        await db.commit()
        await db.refresh(appeal)

        # Build response
        appeal_response = {
            "id": str(appeal.id),
            "candidate_rank_id": str(appeal.candidate_rank_id),
            "candidate_email": appeal.candidate_email,
            "appeal_type": appeal.appeal_type,
            "appeal_text": appeal.appeal_text,
            "supporting_documents": appeal.supporting_documents,
            "status": appeal.status,
            "reviewer_id": str(appeal.reviewer_id) if appeal.reviewer_id else None,
            "review_notes": appeal.review_notes,
            "resolution_outcome": appeal.resolution_outcome,
            "created_at": appeal.created_at.isoformat() if appeal.created_at else None,
            "updated_at": appeal.updated_at.isoformat() if appeal.updated_at else None,
        }

        logger.info(f"Updated appeal {appeal_id} to status '{request.status}'")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=appeal_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing appeal {appeal_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review appeal: {str(e)}",
        ) from e
