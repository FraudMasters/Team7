"""
Parsing corrections API endpoints.

This module provides endpoints for managing user corrections to parsed resume data.
These corrections enable tracking parsing accuracy, learning from mistakes,
and improving parser accuracy over time.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.parsing_correction import ParsingCorrection

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_locale(request: Optional[Request]) -> str:
    """
    Extract Accept-Language header from request.

    Args:
        request: The incoming FastAPI request (optional)

    Returns:
        Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


# Request/Response Models
class SourceTextLocation(BaseModel):
    """Model for source text location in document."""

    page: Optional[int] = Field(None, description="Page number in document")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x0, y0, x1, y1]")
    text: Optional[str] = Field(None, description="Source text snippet")


class CorrectionCreate(BaseModel):
    """Request model for creating a new parsing correction."""

    field_name: str = Field(
        ...,
        description="Name of the corrected field (e.g., 'position', 'skills', 'work_experience')"
    )
    original_value: Optional[dict] = Field(
        None,
        description="The AI-parsed value before correction"
    )
    corrected_value: Optional[dict] = Field(
        None,
        description="The user's corrected value"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for correction (e.g., 'position_was_incorrect', 'missing_skill')"
    )
    source_text_location: Optional[SourceTextLocation] = Field(
        None,
        description="Location in source document used for parsing"
    )


class CorrectionResponse(BaseModel):
    """Response model for a single correction."""

    id: str = Field(..., description="Correction UUID")
    resume_id: str = Field(..., description="Resume UUID")
    field_name: str = Field(..., description="Name of the corrected field")
    original_value: Optional[dict] = Field(None, description="Original AI-parsed value")
    corrected_value: Optional[dict] = Field(None, description="Corrected value")
    reason: Optional[str] = Field(None, description="Reason for correction")
    source_text_location: Optional[dict] = Field(None, description="Source text location")
    corrected_by: Optional[str] = Field(None, description="ID of user who made correction")
    created_at: Optional[str] = Field(None, description="Timestamp when correction was created")


class CorrectionsListResponse(BaseModel):
    """Response model for list of corrections."""

    success: bool = Field(..., description="Whether request was successful")
    data: List[CorrectionResponse] = Field(..., description="List of corrections")
    count: int = Field(..., description="Total number of corrections")
    message: str = Field(..., description="Success message")


class CorrectionCreateResponse(BaseModel):
    """Response model for creating a correction."""

    success: bool = Field(..., description="Whether correction was created successfully")
    data: CorrectionResponse = Field(..., description="Created correction details")
    message: str = Field(..., description="Success message")


class FieldUpdateRequest(BaseModel):
    """Request model for updating a parsed field."""

    value: str = Field(..., description="The corrected value for the field")
    original_value: Optional[str] = Field(
        None,
        description="The original AI-parsed value before correction"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for correction (e.g., 'position_was_incorrect', 'missing_skill')"
    )


class FieldUpdateResponse(BaseModel):
    """Response model for field update."""

    success: bool = Field(..., description="Whether field was updated successfully")
    data: CorrectionResponse = Field(..., description="Created correction details")
    message: str = Field(..., description="Success message")


@router.get(
    "/{resume_id}",
    response_model=CorrectionsListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Parsing Corrections"],
)
async def get_corrections_for_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    field_name: Optional[str] = None,
) -> JSONResponse:
    """
    Get all parsing corrections for a specific resume.

    This endpoint retrieves all user corrections made to the parsed data
    of a specific resume. Optionally filter by field name.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        db: Database session
        field_name: Optional filter by specific field name

    Returns:
        JSON response with list of corrections

    Raises:
        HTTPException(404): If resume not found (no corrections)
        HTTPException(422): If resume_id format is invalid

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/parsing-corrections/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> response.json()
        {
            "success": true,
            "data": [
                {
                    "id": "456e7890-e89b-12d3-a456-426614174000",
                    "resume_id": "123e4567-e89b-12d3-a456-426614174000",
                    "field_name": "position",
                    "original_value": {"position": "Software Engineer"},
                    "corrected_value": {"position": "Senior Software Engineer"},
                    "reason": "position_was_incorrect",
                    "source_text_location": {"page": 1, "text": "Senior Software Engineer"},
                    "corrected_by": null,
                    "created_at": "2026-02-12T00:00:00Z"
                }
            ],
            "count": 1,
            "message": "Corrections retrieved successfully"
        }
    """
    locale = _extract_locale(request)

    # Validate resume_id format
    try:
        resume_uuid = UUID(resume_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid resume ID format: {resume_id}"
        )

    try:
        # Build query
        query = select(ParsingCorrection).where(
            ParsingCorrection.resume_id == resume_uuid
        ).order_by(ParsingCorrection.created_at.desc())

        # Apply optional filter
        if field_name:
            query = query.where(ParsingCorrection.field_name == field_name)

        # Execute query
        result = await db.execute(query)
        corrections = result.scalars().all()

        # Build response
        corrections_data = [
            CorrectionResponse(
                id=str(correction.id),
                resume_id=str(correction.resume_id),
                field_name=correction.field_name,
                original_value=correction.original_value,
                corrected_value=correction.corrected_value,
                reason=correction.reason,
                source_text_location=correction.source_text_location,
                corrected_by=str(correction.corrected_by) if correction.corrected_by else None,
                created_at=correction.created_at.isoformat() if correction.created_at else None,
            )
            for correction in corrections
        ]

        success_message = get_success_message("corrections_retrieved", locale)

        logger.info(f"Retrieved {len(corrections)} corrections for resume {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": [c.model_dump() for c in corrections_data],
                "count": len(corrections_data),
                "message": success_message,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving corrections for resume {resume_id}: {e}", exc_info=True)
        error_message = get_error_message("corrections_retrieve_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        ) from e


@router.post(
    "/{resume_id}",
    response_model=CorrectionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Parsing Corrections"],
)
async def create_correction(
    request: Request,
    resume_id: str,
    correction: CorrectionCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new parsing correction for a resume.

    This endpoint allows users to submit corrections to AI-parsed resume data.
    Corrections are stored for tracking parsing accuracy and learning from mistakes.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        correction: Correction details (field_name, original_value, corrected_value, reason)
        db: Database session

    Returns:
        JSON response with created correction details

    Raises:
        HTTPException(422): If resume_id format is invalid or validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/parsing-corrections/123e4567-e89b-12d3-a456-426614174000",
        ...     json={
        ...         "field_name": "position",
        ...         "original_value": {"position": "Software Engineer"},
        ...         "corrected_value": {"position": "Senior Software Engineer"},
        ...         "reason": "position_was_incorrect"
        ...     }
        ... )
        >>> response.json()
        {
            "success": true,
            "data": {
                "id": "456e7890-e89b-12d3-a456-426614174000",
                "resume_id": "123e4567-e89b-12d3-a456-426614174000",
                "field_name": "position",
                ...
            },
            "message": "Correction saved successfully"
        }
    """
    locale = _extract_locale(request)

    # Validate resume_id format
    try:
        resume_uuid = UUID(resume_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid resume ID format: {resume_id}"
        )

    # Validate field_name
    valid_fields = {
        "position", "skills", "education", "work_experience",
        "languages", "age", "raw_text", "other"
    }
    if correction.field_name not in valid_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid field_name '{correction.field_name}'. Valid values: {', '.join(sorted(valid_fields))}"
        )

    try:
        # Create new correction record
        new_correction = ParsingCorrection(
            resume_id=resume_uuid,
            field_name=correction.field_name,
            original_value=correction.original_value,
            corrected_value=correction.corrected_value,
            reason=correction.reason,
            source_text_location=correction.source_text_location.model_dump() if correction.source_text_location else None,
        )

        db.add(new_correction)
        await db.commit()
        await db.refresh(new_correction)

        # Build response
        correction_response = CorrectionResponse(
            id=str(new_correction.id),
            resume_id=str(new_correction.resume_id),
            field_name=new_correction.field_name,
            original_value=new_correction.original_value,
            corrected_value=new_correction.corrected_value,
            reason=new_correction.reason,
            source_text_location=new_correction.source_text_location,
            corrected_by=str(new_correction.corrected_by) if new_correction.corrected_by else None,
            created_at=new_correction.created_at.isoformat() if new_correction.created_at else None,
        )

        success_message = get_success_message("correction_saved", locale)

        logger.info(
            f"Created correction {new_correction.id} for resume {resume_id}: "
            f"field={correction.field_name}, reason={correction.reason}"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": correction_response.model_dump(),
                "message": success_message,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating correction for resume {resume_id}: {e}", exc_info=True)
        await db.rollback()
        error_message = get_error_message("correction_save_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        ) from e


@router.put(
    "/{resume_id}/fields/{field_name}",
    response_model=FieldUpdateResponse,
    status_code=status.HTTP_200_OK,
    tags=["Parsing Corrections"],
)
async def update_parsed_field(
    request: Request,
    resume_id: str,
    field_name: str,
    field_update: FieldUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an individual parsed field with correction tracking.

    This endpoint allows users to update a specific parsed field value
    while automatically creating a correction record for tracking purposes.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        field_name: Name of the field to update (e.g., 'position', 'skills', 'education')
        field_update: Request body containing new value, original value, and reason
        db: Database session

    Returns:
        JSON response with created correction details

    Raises:
        HTTPException(404): If resume not found
        HTTPException(422): If resume_id format is invalid or field_name is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/parsing-corrections/123e4567-e89b-12d3-a456-426614174000/fields/position",
        ...     json={
        ...         "value": "Senior Software Engineer",
        ...         "original_value": "Software Engineer",
        ...         "reason": "position_was_incorrect"
        ...     }
        ... )
        >>> response.json()
        {
            "success": true,
            "data": {
                "id": "456e7890-e89b-12d3-a456-426614174000",
                "resume_id": "123e4567-e89b-12d3-a456-426614174000",
                "field_name": "position",
                "original_value": {"position": "Software Engineer"},
                "corrected_value": {"position": "Senior Software Engineer"},
                "reason": "position_was_incorrect",
                "source_text_location": null,
                "corrected_by": null,
                "created_at": "2026-02-12T00:00:00Z"
            },
            "message": "Field updated successfully"
        }
    """
    locale = _extract_locale(request)

    # Validate resume_id format
    try:
        resume_uuid = UUID(resume_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid resume ID format: {resume_id}"
        )

    # Validate field_name
    valid_fields = {
        "position", "skills", "education", "work_experience",
        "languages", "age", "raw_text", "other"
    }
    if field_name not in valid_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid field_name '{field_name}'. Valid values: {', '.join(sorted(valid_fields))}"
        )

    try:
        # Create new correction record to track this update
        new_correction = ParsingCorrection(
            resume_id=resume_uuid,
            field_name=field_name,
            original_value={field_name: field_update.original_value} if field_update.original_value else None,
            corrected_value={field_name: field_update.value},
            reason=field_update.reason,
        )

        db.add(new_correction)
        await db.commit()
        await db.refresh(new_correction)

        # Build response
        correction_response = CorrectionResponse(
            id=str(new_correction.id),
            resume_id=str(new_correction.resume_id),
            field_name=new_correction.field_name,
            original_value=new_correction.original_value,
            corrected_value=new_correction.corrected_value,
            reason=new_correction.reason,
            source_text_location=new_correction.source_text_location,
            corrected_by=str(new_correction.corrected_by) if new_correction.corrected_by else None,
            created_at=new_correction.created_at.isoformat() if new_correction.created_at else None,
        )

        success_message = get_success_message("field_updated", locale)

        logger.info(
            f"Updated field '{field_name}' for resume {resume_id}: "
            f"original={field_update.original_value}, new={field_update.value}, reason={field_update.reason}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": correction_response.model_dump(),
                "message": success_message,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating field '{field_name}' for resume {resume_id}: {e}", exc_info=True)
        await db.rollback()
        error_message = get_error_message("field_update_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        ) from e
