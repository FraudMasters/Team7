"""
Candidate note management endpoints.

This module provides endpoints for managing collaborative notes and comments on candidates,
including CRUD operations for creating, reading, updating, and deleting notes with
support for private and team-visible notes.
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
from models.candidate_note import CandidateNote
from models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


class CandidateNoteCreate(BaseModel):
    """Request model for creating a candidate note."""

    resume_id: str = Field(..., description="Resume ID (candidate) this note is about")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (author) of the note")
    content: str = Field(..., min_length=1, max_length=10000, description="Note content")
    is_private: bool = Field(False, description="Whether the note is private (only visible to author)")


class CandidateNoteUpdate(BaseModel):
    """Request model for updating a candidate note."""

    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="Note content")
    is_private: Optional[bool] = Field(None, description="Whether the note is private (only visible to author)")


class CandidateNoteResponse(BaseModel):
    """Response model for a single candidate note."""

    id: str = Field(..., description="Unique identifier for the note")
    resume_id: str = Field(..., description="Resume ID this note is about")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (author) of the note")
    content: str = Field(..., description="Note content")
    is_private: bool = Field(..., description="Whether the note is private")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class CandidateNoteListResponse(BaseModel):
    """Response model for listing candidate notes."""

    resume_id: str = Field(..., description="Resume ID")
    notes: List[CandidateNoteResponse] = Field(..., description="List of candidate notes")
    total_count: int = Field(..., description="Total number of notes")


@router.post(
    "/",
    response_model=CandidateNoteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidate Notes"],
)
async def create_candidate_note(
    request: CandidateNoteCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a candidate note.

    This endpoint creates a new note for a candidate (resume), allowing recruiters
    and hiring managers to collaborate by adding comments and feedback.

    Args:
        request: Request body containing note details
        db: Database session

    Returns:
        JSON response with created note details

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/candidate-notes/",
        ...     json={
        ...         "resume_id": "resume-uuid",
        ...         "content": "Great candidate, strong technical skills",
        ...         "recruiter_id": "recruiter-uuid",
        ...         "is_private": False
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating candidate note for resume: {request.resume_id}")

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(request.resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {request.resume_id}",
            )

        # Create new note
        new_note = CandidateNote(
            resume_id=UUID(request.resume_id),
            recruiter_id=UUID(request.recruiter_id) if request.recruiter_id else None,
            content=request.content,
            is_private=request.is_private,
        )
        db.add(new_note)
        await db.flush()

        response_data = {
            "id": str(new_note.id),
            "resume_id": str(new_note.resume_id),
            "recruiter_id": str(new_note.recruiter_id) if new_note.recruiter_id else None,
            "content": new_note.content,
            "is_private": new_note.is_private,
            "created_at": new_note.created_at.isoformat(),
            "updated_at": new_note.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created candidate note with ID: {new_note.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error creating candidate note: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate note: {str(e)}",
        ) from e


@router.get("/", tags=["Candidate Notes"])
async def list_candidate_notes(
    resume_id: Optional[str] = Query(None, description="Filter by resume ID"),
    is_private: Optional[bool] = Query(None, description="Filter by private status"),
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter (author) ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List candidate notes with optional filters.

    This endpoint retrieves candidate notes with support for filtering
    by resume, private status, and author.

    Args:
        resume_id: Optional resume ID filter
        is_private: Optional private status filter
        recruiter_id: Optional recruiter ID filter
        db: Database session

    Returns:
        JSON response with list of notes

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/candidate-notes/?resume_id=resume-uuid")
        >>> response.json()
        {
            "resume_id": "resume-uuid",
            "notes": [...],
            "total_count": 3
        }
    """
    try:
        logger.info(f"Listing candidate notes with filters - resume_id: {resume_id}, is_private: {is_private}")

        # Build query
        query = select(CandidateNote)

        if resume_id:
            query = query.where(CandidateNote.resume_id == UUID(resume_id))
        if is_private is not None:
            query = query.where(CandidateNote.is_private == is_private)
        if recruiter_id:
            query = query.where(CandidateNote.recruiter_id == UUID(recruiter_id))

        query = query.order_by(CandidateNote.created_at.desc())

        result = await db.execute(query)
        notes = result.scalars().all()

        # If resume_id filter was provided, use it in response
        response_resume_id = resume_id if resume_id and len(notes) > 0 else "all"

        # Build response
        notes_data = []
        for note in notes:
            notes_data.append({
                "id": str(note.id),
                "resume_id": str(note.resume_id),
                "recruiter_id": str(note.recruiter_id) if note.recruiter_id else None,
                "content": note.content,
                "is_private": note.is_private,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
            })

        response_data = {
            "resume_id": response_resume_id,
            "notes": notes_data,
            "total_count": len(notes_data),
        }

        logger.info(f"Retrieved {len(notes_data)} candidate notes")

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
        logger.error(f"Error listing candidate notes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list candidate notes: {str(e)}",
        ) from e


@router.get("/{note_id}", tags=["Candidate Notes"])
async def get_candidate_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific candidate note by ID.

    This endpoint retrieves detailed information about a single note.

    Args:
        note_id: UUID of the note
        db: Database session

    Returns:
        JSON response with note details

    Raises:
        HTTPException(404): If note is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/candidate-notes/note-uuid")
        >>> response.json()
        {
            "id": "note-uuid",
            "resume_id": "resume-uuid",
            "content": "Great candidate",
            ...
        }
    """
    try:
        logger.info(f"Retrieving candidate note: {note_id}")

        result = await db.execute(
            select(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate note not found: {note_id}",
            )

        response_data = {
            "id": str(note.id),
            "resume_id": str(note.resume_id),
            "recruiter_id": str(note.recruiter_id) if note.recruiter_id else None,
            "content": note.content,
            "is_private": note.is_private,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }

        logger.info(f"Retrieved candidate note: {note_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {note_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving candidate note: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate note: {str(e)}",
        ) from e


@router.put("/{note_id}", tags=["Candidate Notes"])
async def update_candidate_note(
    note_id: str,
    request: CandidateNoteUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a candidate note.

    This endpoint updates an existing candidate note.
    Only the fields specified in the request body will be updated.

    Args:
        note_id: UUID of the note
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated note details

    Raises:
        HTTPException(404): If note is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/candidate-notes/note-uuid",
        ...     json={
        ...         "content": "Updated note content",
        ...         "is_private": True
        ...     }
        ... )
        >>> response.json()
        {
            "id": "note-uuid",
            "content": "Updated note content",
            "is_private": true,
            ...
        }
    """
    try:
        logger.info(f"Updating candidate note: {note_id}")

        # Get existing note
        result = await db.execute(
            select(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate note not found: {note_id}",
            )

        # Update fields if provided
        if request.content is not None:
            note.content = request.content
        if request.is_private is not None:
            note.is_private = request.is_private

        await db.commit()
        await db.refresh(note)

        response_data = {
            "id": str(note.id),
            "resume_id": str(note.resume_id),
            "recruiter_id": str(note.recruiter_id) if note.recruiter_id else None,
            "content": note.content,
            "is_private": note.is_private,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }

        logger.info(f"Updated candidate note: {note_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {note_id}",
        )
    except Exception as e:
        logger.error(f"Error updating candidate note: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidate note: {str(e)}",
        ) from e


@router.delete("/{note_id}", tags=["Candidate Notes"])
async def delete_candidate_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a candidate note.

    This endpoint permanently deletes a candidate note.
    This action cannot be undone.

    Args:
        note_id: UUID of the note
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If note is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/candidate-notes/note-uuid")
        >>> response.json()
        {
            "message": "Candidate note deleted successfully",
            "id": "note-uuid"
        }
    """
    try:
        logger.info(f"Deleting candidate note: {note_id}")

        # Check if note exists
        result = await db.execute(
            select(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate note not found: {note_id}",
            )

        # Delete the note
        await db.execute(
            delete(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        await db.commit()

        logger.info(f"Deleted candidate note: {note_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Candidate note deleted successfully",
                "id": note_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {note_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting candidate note: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete candidate note: {str(e)}",
        ) from e
