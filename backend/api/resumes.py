"""
Resume upload and management endpoints.

This module provides endpoints for uploading resume files (PDF, DOCX),
validating file format and size, storing files, and creating database records.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.resume import Resume, ResumeStatus

logger = logging.getLogger(__name__)
settings = get_settings()

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

# Directory for storing uploaded resumes
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ResumeUploadResponse(BaseModel):
    """Response model for resume upload endpoint."""

    id: str = Field(..., description="Unique identifier for the uploaded resume")
    filename: str = Field(..., description="Original filename of the uploaded resume")
    status: str = Field(..., description="Processing status of the resume")
    message: str = Field(..., description="Success message")


class ResumeListItem(BaseModel):
    """Response model for a single resume in a list."""

    id: str = Field(..., description="Unique identifier")
    filename: str = Field(..., description="Filename")
    status: str = Field(..., description="Processing status")
    created_at: str = Field(..., description="Creation timestamp")
    language: Optional[str] = Field(None, description="Detected language")


def validate_file_type(filename: str, content_type: str, locale: str = "en") -> None:
    """
    Validate that the file type is allowed.

    Args:
        filename: Name of the uploaded file
        content_type: MIME type of the file
        locale: Language code for translated error messages

    Raises:
        HTTPException: If file type is not allowed
    """
    # Check file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in settings.allowed_file_types:
        allowed = ", ".join(settings.allowed_file_types)
        error_msg = get_error_message("invalid_file_type", locale, file_ext=file_ext, allowed=allowed)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=error_msg,
        )

    # Check content type for additional validation
    allowed_content_types = {
        ".pdf": ["application/pdf"],
        ".docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ],
    }

    if file_ext in allowed_content_types:
        if content_type not in allowed_content_types[file_ext]:
            logger.warning(
                f"Content type mismatch for {filename}: {content_type} not in {allowed_content_types[file_ext]}"
            )


def validate_file_size(file_size: int, locale: str = "en") -> None:
    """
    Validate that the file size is within allowed limits.

    Args:
        file_size: Size of the file in bytes
        locale: Language code for translated error messages

    Raises:
        HTTPException: If file size exceeds maximum allowed
    """
    max_size = settings.max_upload_size_bytes
    if file_size > max_size:
        max_mb = settings.max_upload_size_mb
        size_mb = file_size / 1024 / 1024
        error_msg = get_error_message("file_too_large", locale, size=size_mb, max_mb=max_mb)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg,
        )


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resumes"],
)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Upload a resume file for analysis.

    This endpoint accepts resume files in PDF or DOCX format, validates the file
    type and size, stores the file, and creates a database record for tracking.

    Args:
        request: FastAPI request object (for Accept-Language header)
        file: Uploaded resume file (PDF or DOCX)
        db: Database session

    Returns:
        JSON response with resume ID, filename, and status

    Raises:
        HTTPException(415): If file type is not supported
        HTTPException(413): If file size exceeds maximum allowed
        HTTPException(500): If file storage or database operation fails

    Examples:
        >>> import requests
        >>> with open("resume.pdf", "rb") as f:
        ...     response = requests.post("http://localhost:8000/api/resumes/upload", files={"file": f})
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "resume.pdf",
            "status": "pending",
            "message": "Resume uploaded successfully"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Received file upload: {file.filename} ({file_size} bytes)")

        # Validate file type
        validate_file_type(file.filename or "unknown", file.content_type or "application/octet-stream", locale)

        # Validate file size
        validate_file_size(file_size, locale)

        # Generate UUID for the resume
        resume_id = uuid4()
        safe_filename = Path(file.filename or "resume").name
        file_extension = Path(safe_filename).suffix
        stored_filename = f"{resume_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename

        # Save file to disk
        logger.info(f"Saving file to: {file_path}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create database record
        new_resume = Resume(
            id=resume_id,
            filename=file.filename or "unknown",
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            status=ResumeStatus.PENDING,
        )

        db.add(new_resume)
        await db.commit()
        await db.refresh(new_resume)

        # Get translated success message
        success_message = get_success_message("file_uploaded", locale)

        response_data = {
            "id": str(resume_id),
            "filename": file.filename or "unknown",
            "status": ResumeStatus.PENDING.value,
            "message": success_message,
        }

        logger.info(f"Resume uploaded successfully: {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/",
    response_model=list[ResumeListItem],
    tags=["Resumes"],
)
async def list_resumes(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all resumes in the database.

    Returns a paginated list of all resumes with their basic information.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of resumes

    Example:
        >>> response = requests.get("http://localhost:8000/api/resumes/?limit=10")
        >>> resumes = response.json()
    """
    try:
        # Query resumes from database
        query = select(Resume).order_by(Resume.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        resumes = result.scalars().all()

        # Convert to response format
        resumes_list = []
        for resume in resumes:
            # Extract technical skills
            skills = []

            # Try to get from raw_text first
            if resume.raw_text:
                try:
                    from analyzers import extract_resume_entities
                    entities = extract_resume_entities(resume.raw_text[:5000])
                    skills = entities.get("technical_skills") or entities.get("skills") or []
                except Exception as e:
                    logger.warning(f"Failed to extract skills from raw_text for resume {resume.id}: {e}")

            # If no skills and raw_text is empty, try extracting from file
            if not skills and resume.file_path:
                try:
                    from pathlib import Path
                    from services.data_extractor.extract import extract_text_from_docx, extract_text_from_pdf

                    file_path = Path(resume.file_path)
                    if file_path.exists():
                        if file_path.suffix == ".docx":
                            result = extract_text_from_docx(str(file_path))
                            text = result.get("text", "")
                        elif file_path.suffix == ".pdf":
                            result = extract_text_from_pdf(str(file_path))
                            text = result.get("text", "")
                        else:
                            text = ""

                        if text and len(text) > 100:
                            try:
                                from analyzers import extract_resume_entities
                                entities = extract_resume_entities(text[:5000])
                                skills = entities.get("technical_skills") or entities.get("skills") or []
                            except Exception as e:
                                logger.warning(f"Failed to extract skills from file for resume {resume.id}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to extract skills from file for resume {resume.id}: {e}")

            resumes_list.append({
                "id": str(resume.id),
                "filename": resume.filename,
                "status": resume.status.value,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "language": resume.language,
                "skills": skills[:15],  # Include skills for display
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=resumes_list,
        )

    except Exception as e:
        logger.error(f"Error listing resumes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumes: {str(e)}",
        ) from e


@router.get("/{resume_id}", tags=["Resumes"])
async def get_resume(request: Request, resume_id: str, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Get resume information by ID with extracted text and best vacancy match.

    Args:
        request: FastAPI request object (for Accept-Language header)
        resume_id: Unique identifier of the resume
        db: Database session

    Returns:
        JSON response with resume details, extracted text, skills, and best match

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/resumes/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "resume.pdf",
            "status": "completed",
            "raw_text": "Resume content here...",
            "technical_skills": ["Python", "Django"],
            "best_match": {"vacancy_title": "Senior Developer", "match_percentage": 85}
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    # Import analysis functions
    from analyzers import (
        extract_resume_keywords_hf as extract_resume_keywords,
        extract_resume_entities,
        check_grammar_resume,
        EnhancedSkillMatcher,
    )
    from models.job_vacancy import JobVacancy

    try:
        # First, try to find resume in database
        from models.resume import Resume as ResumeModel
        from pathlib import Path

        resume_query = select(ResumeModel).where(ResumeModel.id == UUID(resume_id))
        resume_result = await db.execute(resume_query)
        resume_record = resume_result.scalar_one_or_none()

        # Determine file path
        file_path = None
        if resume_record and resume_record.file_path:
            file_path = Path(resume_record.file_path)
            filename = resume_record.filename
        else:
            # Fallback: look for file by resume_id
            upload_dir = Path("data/uploads")
            resume_files = list(upload_dir.glob(f"{resume_id}.*"))
            if resume_files:
                file_path = resume_files[0]
                filename = file_path.name
            else:
                # Try numeric ID fallback
                resume_files = list(upload_dir.glob("*.*"))
                filename = f"resume_{resume_id[:8]}"

        if not file_path or not file_path.exists():
            logger.warning(f"Resume file not found for id: {resume_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": resume_id,
                    "filename": filename,
                    "status": "error",
                    "message": "Resume file not found",
                    "raw_text": "",
                    "errors": [],
                    "grammar_errors": [],
                    "keywords": [],
                    "technical_skills": [],
                    "total_experience_months": 0,
                    "best_match": None,
                },
            )

        # Extract text from resume
        if file_path.suffix == ".pdf":
            from services.data_extractor.extract import extract_text_from_pdf
            result = extract_text_from_pdf(str(file_path))
            text = result.get("text", "") if result else ""
        elif file_path.suffix == ".docx":
            from services.data_extractor.extract import extract_text_from_docx
            result = extract_text_from_docx(str(file_path))
            text = result.get("text", "") if result else ""
        else:
            text = ""

        if not text or len(text.strip()) < 10:
            logger.warning(f"Could not extract text from resume: {resume_id}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": resume_id,
                    "filename": filename,
                    "status": "error",
                    "message": "Could not extract text from resume",
                    "raw_text": "",
                    "errors": [],
                    "grammar_errors": [],
                    "keywords": [],
                    "technical_skills": [],
                    "total_experience_months": 0,
                    "best_match": None,
                },
            )

        # Run analysis
        logger.info(f"Running analysis for resume: {resume_id}")

        # Extract keywords
        keywords_data = extract_resume_keywords(text[:3000])
        keywords = keywords_data.get("keywords", [])

        # Extract entities (technical skills)
        entities_data = extract_resume_entities(text[:5000])
        entities = entities_data.get("technical_skills") or entities_data.get("skills") or []

        # Grammar check
        grammar_data = check_grammar_resume(text[:2000])
        grammar_errors = grammar_data.get("errors", [])

        # Find best matching vacancy
        best_match = None
        try:
            # Get all vacancies
            vacancy_query = select(JobVacancy)
            vacancy_result = await db.execute(vacancy_query)
            vacancies = vacancy_result.scalars().all()

            matcher = EnhancedSkillMatcher()
            best_match_pct = 0
            best_match_data = None

            for vacancy in vacancies:
                required_skills = vacancy.required_skills or []
                if not required_skills:
                    continue

                match_results = matcher.match_multiple(
                    resume_skills=entities,
                    required_skills=required_skills,
                )

                matched = [s for s, r in match_results.items() if r.get("matched")]
                match_pct = (len(matched) / len(required_skills) * 100) if required_skills else 0

                if match_pct > best_match_pct:
                    best_match_pct = match_pct
                    missing = [s for s, r in match_results.items() if not r.get("matched")]
                    best_match_data = {
                        "vacancy_id": str(vacancy.id),
                        "vacancy_title": vacancy.title,
                        "match_percentage": round(match_pct, 1),
                        "matched_skills": matched,
                        "missing_skills": missing,
                        "salary_min": vacancy.salary_min,
                        "salary_max": vacancy.salary_max,
                        "location": vacancy.location,
                    }

            best_match = best_match_data
        except Exception as e:
            logger.warning(f"Could not calculate best match: {e}")

        logger.info(f"Analysis completed for resume: {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": resume_id,
                "filename": filename,
                "status": "completed",
                "message": "Analysis completed successfully",
                "raw_text": text,
                "errors": [],
                "grammar_errors": grammar_errors,
                "keywords": keywords[:20],
                "technical_skills": entities[:30],
                "total_experience_months": 0,
                "best_match": best_match,
            },
        )

    except Exception as e:
        logger.error(f"Error analyzing resume {resume_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": resume_id,
                "filename": "unknown",
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "raw_text": "",
                "errors": [],
                "grammar_errors": [],
                "keywords": [],
                "technical_skills": [],
                "total_experience_months": 0,
                "best_match": None,
            },
        )

@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Resumes"])
async def delete_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete a resume by ID.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume to delete
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If resume not found

    Example:
        >>> response = requests.delete("http://localhost:8000/api/resumes/123")
        >>> response.status_code
        204
    """
    try:
        # First, try to find resume in database
        from models.resume import Resume as ResumeModel
        from pathlib import Path

        resume_record = None
        file_path = None

        # Try to parse as UUID for database lookup
        try:
            resume_query = select(ResumeModel).where(ResumeModel.id == UUID(resume_id))
            resume_result = await db.execute(resume_query)
            resume_record = resume_result.scalar_one_or_none()
        except ValueError:
            pass

        # Determine file path
        if resume_record and resume_record.file_path:
            file_path = Path(resume_record.file_path)

        # Delete from database if found
        if resume_record:
            await db.delete(resume_record)
            await db.commit()

        # Delete file from disk if exists
        if file_path and file_path.exists():
            file_path.unlink()

        logger.info(f"Deleted resume: {resume_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume: {str(e)}",
        ) from e

