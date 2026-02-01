"""
Interview preparation endpoints for generating and managing interview questions.

This module provides endpoints for generating customized interview questions
based on candidate resumes and job requirements, including technical,
behavioral, situational, and skill verification questions.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path to import from data_extractor service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor"))

from analyzers import (
    extract_resume_keywords_hf as extract_resume_keywords,
    extract_resume_entities,
)
from analyzers.interview_question_generator import (
    InterviewQuestionGenerator,
    InterviewPrepResult,
)
from i18n.backend_translations import get_error_message, get_success_message

from database import get_db
from models.interview_prep import InterviewPrep

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")


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


# ============================================================================
# Pydantic Models
# ============================================================================

class InterviewQuestion(BaseModel):
    """A single interview question with metadata."""

    id: str = Field(..., description="Unique identifier for the question")
    text: str = Field(..., description="The question text")
    category: str = Field(..., description="Category: technical, behavioral, situational, skill_verification")
    difficulty: str = Field(default="intermediate", description="Difficulty level (beginner, intermediate, advanced)")
    skills: List[str] = Field(default_factory=list, description="List of relevant skills this question probes")
    rationale: str = Field(default="", description="Why this question is being asked")
    expected_answers: List[str] = Field(default_factory=list, description="Key points to look for in the answer")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")


class GenerateInterviewPrepRequest(BaseModel):
    """Request model for generating interview questions."""

    resume_id: str = Field(..., description="Unique identifier of the resume to analyze")
    vacancy_id: str = Field(..., description="Unique identifier of the job vacancy")
    candidate_skills: Optional[List[str]] = Field(
        default=None, description="Pre-extracted skills from resume (optional, will be extracted if not provided)"
    )
    skill_gaps: Optional[List[str]] = Field(
        default=None, description="Skills required but not found in resume (optional)"
    )


class UpdateInterviewPrepRequest(BaseModel):
    """Request model for updating interview preparation data."""

    custom_questions: Optional[List[str]] = Field(
        default=None, description="Custom questions to add to the interview prep"
    )
    question_feedback: Optional[Dict[str, Any]] = Field(
        default=None, description="Feedback on question usefulness {question_id: rating}"
    )


class InterviewPrepResponse(BaseModel):
    """Response model for interview preparation data."""

    id: str = Field(..., description="Unique identifier for the interview prep")
    resume_id: str = Field(..., description="Resume identifier")
    vacancy_id: str = Field(..., description="Job vacancy identifier")
    technical_questions: List[InterviewQuestion] = Field(
        ..., description="Technical interview questions"
    )
    behavioral_questions: List[InterviewQuestion] = Field(
        ..., description="Behavioral interview questions"
    )
    situational_questions: List[InterviewQuestion] = Field(
        ..., description="Situational interview questions"
    )
    skill_verification_questions: List[InterviewQuestion] = Field(
        ..., description="Skill verification questions"
    )
    areas_to_probe: List[str] = Field(..., description="Experience claims and skills to verify")
    skill_gaps_to_address: List[str] = Field(..., description="Skills the candidate should demonstrate")
    interview_tips: List[str] = Field(default_factory=list, description="Tips for the interviewer")
    custom_questions: List[str] = Field(default_factory=list, description="Recruiter-added custom questions")
    question_feedback: Dict[str, Any] = Field(default_factory=dict, description="Feedback on question usefulness")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model name used")
    generated_at: str = Field(..., description="Timestamp of generation")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class InterviewPrepListResponse(BaseModel):
    """Response model for listing interview prep entries."""

    resume_id: Optional[str] = Field(None, description="Resume ID filter (if applied)")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID filter (if applied)")
    interview_preps: List[InterviewPrepResponse] = Field(..., description="List of interview prep entries")
    total_count: int = Field(..., description="Total number of entries")


# ============================================================================
# Helper Functions
# ============================================================================

def find_resume_file(resume_id: str, locale: str = "en") -> Path:
    """
    Find the resume file by ID.

    Args:
        resume_id: Unique identifier of the resume
        locale: Language code for translated error messages

    Returns:
        Path to the resume file

    Raises:
        HTTPException: If resume file is not found
    """
    # Try common file extensions
    for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
        file_path = UPLOAD_DIR / f"{resume_id}{ext}"
        if file_path.exists():
            return file_path

    # If not found, raise error
    error_msg = get_error_message("file_not_found", locale)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error_msg,
    )


def extract_text_from_file(file_path: Path, locale: str = "en") -> str:
    """
    Extract text from resume file (PDF or DOCX).

    Args:
        file_path: Path to the resume file
        locale: Language code for translated error messages

    Returns:
        Extracted text content

    Raises:
        HTTPException: If text extraction fails
    """
    try:
        # Import extraction functions
        from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            result = extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            result = extract_text_from_docx(file_path)
        else:
            error_msg = get_error_message("invalid_file_type", locale, file_ext=file_ext, allowed=".pdf, .docx")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=error_msg,
            )

        # Check for extraction errors
        if result.get("error"):
            error_msg = get_error_message("extraction_failed", locale)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        text = result.get("text", "")
        if not text or len(text.strip()) < 10:
            error_msg = get_error_message("file_corrupted", locale)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        logger.info(f"Extracted {len(text)} characters from {file_path.name}")
        return text

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}", exc_info=True)
        error_msg = get_error_message("extraction_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


def convert_question_to_dict(question) -> Dict[str, Any]:
    """
    Convert Question object to dictionary.

    Args:
        question: Question object from InterviewQuestionGenerator

    Returns:
        Dictionary representation of the question
    """
    if hasattr(question, 'to_dict'):
        return question.to_dict()
    return {
        "id": getattr(question, 'id', ''),
        "text": getattr(question, 'text', ''),
        "category": getattr(question, 'category', ''),
        "difficulty": getattr(question, 'difficulty', 'intermediate'),
        "skills": getattr(question, 'skills', []),
        "rationale": getattr(question, 'rationale', ''),
        "expected_answers": getattr(question, 'expected_answers', []),
        "follow_up_suggestions": getattr(question, 'follow_up_suggestions', []),
    }


# ============================================================================
# API Endpoints (placeholders - implementation in subsequent subtasks)
# ============================================================================

@router.post(
    "/generate",
    response_model=InterviewPrepResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Interview Prep"],
)
async def generate_interview_prep(
    http_request: Request, request: GenerateInterviewPrepRequest
) -> JSONResponse:
    """
    Generate interview questions for a candidate based on resume and job vacancy.

    This endpoint analyzes a candidate's resume against job requirements and
    generates customized interview questions across multiple categories:
    - Technical questions for skill assessment
    - Behavioral questions for soft skills evaluation
    - Situational questions for problem-solving assessment
    - Skill verification questions to validate claimed experience

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Generate request with resume_id and vacancy_id

    Returns:
        JSON response with generated interview questions

    Raises:
        HTTPException(404): If resume or vacancy is not found
        HTTPException(422): If text extraction fails
        HTTPException(500): If question generation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/interview-prep/generate",
        ...     json={
        ...         "resume_id": "abc123",
        ...         "vacancy_id": "vacancy-456"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "prep-123",
            "resume_id": "abc123",
            "vacancy_id": "vacancy-456",
            "technical_questions": [...],
            "behavioral_questions": [...],
            "areas_to_probe": [...],
            ...
        }
    """
    import time
    from datetime import datetime
    from uuid import UUID, uuid4
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from database import get_db
    from models.job_vacancy import JobVacancy

    # Extract locale from Accept-Language header
    locale = _extract_locale(http_request)

    start_time = time.time()

    # Get database session
    async with get_db() as db:
        try:
            logger.info(
                f"Generating interview prep for resume_id: {request.resume_id}, "
                f"vacancy_id: {request.vacancy_id}"
            )

            # Step 1: Find the resume file
            file_path = find_resume_file(request.resume_id, locale)
            logger.info(f"Found resume file: {file_path}")

            # Step 2: Extract text from file
            resume_text = extract_text_from_file(file_path, locale)

            # Step 3: Get vacancy from database
            try:
                result = await db.execute(
                    select(JobVacancy).where(JobVacancy.id == UUID(request.vacancy_id))
                )
                vacancy = result.scalar_one_or_none()

                if not vacancy:
                    error_msg = get_error_message("vacancy_not_found", locale)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=error_msg,
                    )

                logger.info(f"Found vacancy: {vacancy.title}")

            except ValueError:
                error_msg = get_error_message("invalid_vacancy_id", locale)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

            # Step 4: Detect language from text
            try:
                from langdetect import detect, LangDetectException

                try:
                    detected_lang = detect(resume_text)
                    # Normalize to supported languages
                    language = "ru" if detected_lang == "ru" else "en"
                except LangDetectException:
                    logger.warning("Language detection failed, defaulting to English")
                    language = "en"
            except ImportError:
                logger.warning("langdetect not installed, defaulting to English")
                language = "en"

            logger.info(f"Detected language: {language}")

            # Step 5: Extract candidate skills if not provided
            candidate_skills = request.candidate_skills
            if not candidate_skills:
                logger.info("Extracting candidate skills from resume...")
                try:
                    entities_result = extract_resume_entities(resume_text, language=language)
                    # Handle both 'skills' and 'technical_skills' field names
                    candidate_skills = (
                        entities_result.get("technical_skills")
                        or entities_result.get("skills")
                        or []
                    )
                    logger.info(f"Extracted {len(candidate_skills)} skills")
                except Exception as e:
                    logger.warning(f"Skill extraction failed: {e}")
                    candidate_skills = []

            # Step 6: Identify skill gaps if not provided
            skill_gaps = request.skill_gaps
            if not skill_gaps:
                required_skills = vacancy.required_skills or []
                skill_gaps = [
                    skill for skill in required_skills
                    if skill.lower() not in [s.lower() for s in candidate_skills]
                ]
                logger.info(f"Identified {len(skill_gaps)} skill gaps")

            # Step 7: Generate interview questions using LLM
            logger.info("Generating interview questions...")
            try:
                generator = InterviewQuestionGenerator()
                prep_result = await generator.generate_questions(
                    resume_text=resume_text,
                    job_title=vacancy.title,
                    job_description=vacancy.description,
                    required_skills=vacancy.required_skills or [],
                    candidate_skills=candidate_skills,
                    skill_gaps=skill_gaps,
                    min_experience_months=vacancy.min_experience_months,
                )

                logger.info(
                    f"Generated {len(prep_result.questions)} total questions: "
                    f"{len(prep_result.technical_questions)} technical, "
                    f"{len(prep_result.behavioral_questions)} behavioral, "
                    f"{len(prep_result.situational_questions)} situational, "
                    f"{len(prep_result.skill_verification_questions)} skill verification"
                )

            except Exception as e:
                logger.error(f"Interview question generation failed: {e}", exc_info=True)
                error_msg = get_error_message("interview_prep_generation_failed", locale)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg,
                ) from e

            # Step 8: Build response
            now = datetime.utcnow().isoformat() + "Z"
            prep_id = str(uuid4())

            response_data = {
                "id": prep_id,
                "resume_id": request.resume_id,
                "vacancy_id": request.vacancy_id,
                "technical_questions": [
                    convert_question_to_dict(q) for q in prep_result.technical_questions
                ],
                "behavioral_questions": [
                    convert_question_to_dict(q) for q in prep_result.behavioral_questions
                ],
                "situational_questions": [
                    convert_question_to_dict(q) for q in prep_result.situational_questions
                ],
                "skill_verification_questions": [
                    convert_question_to_dict(q) for q in prep_result.skill_verification_questions
                ],
                "areas_to_probe": prep_result.areas_to_probe,
                "skill_gaps_to_address": prep_result.skill_gaps_to_address,
                "interview_tips": prep_result.interview_tips,
                "custom_questions": [],
                "question_feedback": {},
                "provider": prep_result.provider,
                "model": prep_result.model,
                "generated_at": prep_result.generated_at,
                "created_at": now,
                "updated_at": now,
            }

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Interview prep generated with ID: {prep_id} "
                f"in {processing_time_ms:.2f}ms"
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response_data,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating interview prep: {e}", exc_info=True)
            error_msg = get_error_message("interview_prep_generation_failed", locale)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            ) from e


@router.get(
    "/{prep_id}",
    response_model=InterviewPrepResponse,
    status_code=status.HTTP_200_OK,
    tags=["Interview Prep"],
)
async def get_interview_prep(
    prep_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get interview preparation data by ID.

    Args:
        prep_id: Unique identifier of the interview prep
        db: Database session

    Returns:
        JSON response with interview preparation data

    Raises:
        HTTPException(404): If interview prep is not found
        HTTPException(422): If prep_id is not a valid UUID
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/interview-prep/prep-123")
        >>> response.json()
        {
            "id": "prep-123",
            "resume_id": "abc123",
            "vacancy_id": "vacancy-456",
            "technical_questions": [...],
            "behavioral_questions": [...],
            ...
        }
    """
    try:
        logger.info(f"Retrieving interview prep: {prep_id}")

        # Query database for interview prep
        result = await db.execute(
            select(InterviewPrep).where(InterviewPrep.id == UUID(prep_id))
        )
        prep = result.scalar_one_or_none()

        if not prep:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview preparation not found: {prep_id}",
            )

        # Build response data
        response_data = {
            "id": str(prep.id),
            "resume_id": str(prep.resume_id),
            "vacancy_id": str(prep.vacancy_id),
            "technical_questions": prep.technical_questions or [],
            "behavioral_questions": prep.behavioral_questions or [],
            "situational_questions": prep.situational_questions or [],
            "skill_verification_questions": prep.skill_verification_topics or [],
            "areas_to_probe": prep.areas_to_probe or [],
            "skill_gaps_to_address": [],  # Not stored in DB, computed from vacancy
            "interview_tips": [],  # Not stored in DB
            "custom_questions": prep.custom_questions or [],
            "question_feedback": prep.question_feedback or {},
            "provider": prep.provider or "unknown",
            "model": prep.model or "unknown",
            "generated_at": prep.created_at.isoformat(),
            "created_at": prep.created_at.isoformat(),
            "updated_at": prep.updated_at.isoformat(),
        }

        logger.info(f"Retrieved interview prep: {prep_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {prep_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving interview prep: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interview prep: {str(e)}",
        ) from e


@router.put(
    "/{prep_id}",
    response_model=InterviewPrepResponse,
    status_code=status.HTTP_200_OK,
    tags=["Interview Prep"],
)
async def update_interview_prep(
    prep_id: str,
    request: UpdateInterviewPrepRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update interview preparation data.

    Allows adding custom questions and providing feedback on generated questions.
    Custom questions are appended to the existing list, and feedback is merged
    with existing feedback data.

    Args:
        prep_id: Unique identifier of the interview prep
        request: Update request with custom questions or feedback
        db: Database session

    Returns:
        JSON response with updated interview preparation data

    Raises:
        HTTPException(404): If interview prep is not found
        HTTPException(422): If validation fails or prep_id is invalid UUID
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/interview-prep/prep-123",
        ...     json={"custom_questions": ["What is your greatest achievement?"]}
        ... )
        >>> response.json()
        {
            "id": "prep-123",
            "resume_id": "abc123",
            "vacancy_id": "vacancy-456",
            "custom_questions": ["What is your greatest achievement?"],
            ...
        }
    """
    try:
        logger.info(f"Updating interview prep: {prep_id}")

        # Validate that at least one field is being updated
        if request.custom_questions is None and request.question_feedback is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of 'custom_questions' or 'question_feedback' must be provided",
            )

        # Query database for interview prep
        result = await db.execute(
            select(InterviewPrep).where(InterviewPrep.id == UUID(prep_id))
        )
        prep = result.scalar_one_or_none()

        if not prep:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview preparation not found: {prep_id}",
            )

        # Update custom questions (append to existing list)
        if request.custom_questions is not None:
            # Validate that custom_questions is a list
            if not isinstance(request.custom_questions, list):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="custom_questions must be a list of strings",
                )

            # Validate each question is a non-empty string
            for idx, question in enumerate(request.custom_questions):
                if not isinstance(question, str):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Question at index {idx} must be a string",
                    )
                if len(question.strip()) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Question at index {idx} cannot be empty",
                    )

            # Get existing custom questions or initialize as empty list
            existing_questions = prep.custom_questions if prep.custom_questions else []

            # Append new questions (avoiding duplicates)
            new_questions = [
                q.strip() for q in request.custom_questions
                if q.strip() and q.strip() not in existing_questions
            ]

            prep.custom_questions = existing_questions + new_questions
            logger.info(f"Added {len(new_questions)} custom questions")

        # Update question feedback (merge with existing feedback)
        if request.question_feedback is not None:
            # Validate that question_feedback is a dict
            if not isinstance(request.question_feedback, dict):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="question_feedback must be a dictionary",
                )

            # Get existing feedback or initialize as empty dict
            existing_feedback = prep.question_feedback if prep.question_feedback else {}

            # Merge feedback (new values override old ones)
            existing_feedback.update(request.question_feedback)
            prep.question_feedback = existing_feedback
            logger.info(f"Updated feedback for {len(request.question_feedback)} questions")

        # Update the timestamp
        from datetime import datetime
        prep.updated_at = datetime.utcnow()

        # Save changes to database
        await db.commit()
        await db.refresh(prep)

        logger.info(f"Successfully updated interview prep: {prep_id}")

        # Build response data
        response_data = {
            "id": str(prep.id),
            "resume_id": str(prep.resume_id),
            "vacancy_id": str(prep.vacancy_id),
            "technical_questions": prep.technical_questions or [],
            "behavioral_questions": prep.behavioral_questions or [],
            "situational_questions": prep.situational_questions or [],
            "skill_verification_questions": prep.skill_verification_topics or [],
            "areas_to_probe": prep.areas_to_probe or [],
            "skill_gaps_to_address": [],  # Not stored in DB, computed from vacancy
            "interview_tips": [],  # Not stored in DB
            "custom_questions": prep.custom_questions or [],
            "question_feedback": prep.question_feedback or {},
            "provider": prep.provider or "unknown",
            "model": prep.model or "unknown",
            "generated_at": prep.created_at.isoformat(),
            "created_at": prep.created_at.isoformat(),
            "updated_at": prep.updated_at.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {prep_id}",
        )
    except Exception as e:
        logger.error(f"Error updating interview prep: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update interview prep: {str(e)}",
        ) from e


@router.get(
    "/{prep_id}/export",
    status_code=status.HTTP_200_OK,
    tags=["Interview Prep"],
)
async def export_interview_prep_pdf(
    http_request: Request, prep_id: str, db: AsyncSession = Depends(get_db)
) -> Response:
    """
    Export interview preparation data as PDF.

    This endpoint retrieves interview preparation data and generates a PDF document
    containing all questions categorized by type, areas to probe, skill gaps to address,
    and custom questions added by the recruiter.

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        prep_id: Unique identifier of the interview prep
        db: Database session

    Returns:
        PDF file download with appropriate headers

    Raises:
        HTTPException(404): If interview prep is not found
        HTTPException(422): If prep_id is not a valid UUID
        HTTPException(500): If PDF generation fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/interview-prep/prep-123/export")
        >>> with open("interview_prep.pdf", "wb") as f:
        ...     f.write(response.content)
    """
    import time
    from datetime import datetime

    locale = _extract_locale(http_request)
    start_time = time.time()

    try:
        logger.info(f"Exporting interview prep as PDF: {prep_id}")

        # Step 1: Query database for interview prep
        result = await db.execute(
            select(InterviewPrep).where(InterviewPrep.id == UUID(prep_id))
        )
        prep = result.scalar_one_or_none()

        if not prep:
            error_msg = get_error_message("interview_prep_not_found", locale) if hasattr(get_error_message, '__call__') else f"Interview preparation not found: {prep_id}"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        logger.info(f"Found interview prep: {prep_id}")

        # Step 2: Format interview prep data as PDF
        try:
            pdf_content = _format_interview_prep_as_pdf(prep)
            filename = f"interview_prep_{prep_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(
                f"PDF export completed for prep_id: {prep_id} "
                f"in {processing_time_ms:.2f}ms"
            )

            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "X-Processing-Time-ms": f"{processing_time_ms:.2f}",
                },
            )

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            error_msg = get_error_message("pdf_generation_failed", locale) if hasattr(get_error_message, '__call__') else f"Failed to generate PDF: {str(e)}"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            ) from e

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {prep_id}",
        )
    except Exception as e:
        logger.error(f"Error exporting interview prep: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export interview prep: {str(e)}",
        ) from e


def _format_interview_prep_as_pdf(prep: InterviewPrep) -> bytes:
    """
    Format interview preparation data as PDF document.

    This function converts interview preparation data into a formatted document
    suitable for printing or sharing. Currently returns plain text formatted
    for readability. Can be enhanced to use reportlab or similar library
    for true PDF generation.

    Args:
        prep: InterviewPrep model instance with all the data

    Returns:
        Document content as bytes (text format for now, can be upgraded to PDF)

    Raises:
        Exception: If formatting fails
    """
    try:
        logger.info(f"Formatting interview prep {prep.id} as document")

        # Build formatted text content
        lines = []
        lines.append("=" * 80)
        lines.append("INTERVIEW PREPARATION GUIDE")
        lines.append("=" * 80)
        lines.append(f"ID: {prep.id}")
        lines.append(f"Resume ID: {prep.resume_id}")
        lines.append(f"Vacancy ID: {prep.vacancy_id}")
        lines.append(f"Generated: {prep.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Provider: {prep.provider or 'N/A'}")
        lines.append(f"Model: {prep.model or 'N/A'}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

        # Technical Questions
        technical_questions = prep.technical_questions or []
        if technical_questions:
            lines.append("TECHNICAL QUESTIONS")
            lines.append("-" * 80)
            for idx, q in enumerate(technical_questions, 1):
                if isinstance(q, dict):
                    lines.append(f"\n{idx}. {q.get('text', 'N/A')}")
                    if q.get('skills'):
                        lines.append(f"   Skills: {', '.join(q['skills'])}")
                    if q.get('rationale'):
                        lines.append(f"   Rationale: {q['rationale']}")
                    if q.get('expected_answers'):
                        lines.append(f"   Expected: {', '.join(q['expected_answers'])}")
                else:
                    lines.append(f"{idx}. {q}")
            lines.append("")
            lines.append("")

        # Behavioral Questions
        behavioral_questions = prep.behavioral_questions or []
        if behavioral_questions:
            lines.append("BEHAVIORAL QUESTIONS")
            lines.append("-" * 80)
            for idx, q in enumerate(behavioral_questions, 1):
                if isinstance(q, dict):
                    lines.append(f"\n{idx}. {q.get('text', 'N/A')}")
                    if q.get('rationale'):
                        lines.append(f"   Rationale: {q['rationale']}")
                else:
                    lines.append(f"{idx}. {q}")
            lines.append("")
            lines.append("")

        # Situational Questions
        situational_questions = prep.situational_questions or []
        if situational_questions:
            lines.append("SITUATIONAL QUESTIONS")
            lines.append("-" * 80)
            for idx, q in enumerate(situational_questions, 1):
                if isinstance(q, dict):
                    lines.append(f"\n{idx}. {q.get('text', 'N/A')}")
                else:
                    lines.append(f"{idx}. {q}")
            lines.append("")
            lines.append("")

        # Skill Verification Questions
        skill_verification_questions = prep.skill_verification_topics or []
        if skill_verification_questions:
            lines.append("SKILL VERIFICATION QUESTIONS")
            lines.append("-" * 80)
            for idx, q in enumerate(skill_verification_questions, 1):
                if isinstance(q, dict):
                    lines.append(f"\n{idx}. {q.get('text', 'N/A')}")
                else:
                    lines.append(f"{idx}. {q}")
            lines.append("")
            lines.append("")

        # Areas to Probe
        areas_to_probe = prep.areas_to_probe or []
        if areas_to_probe:
            lines.append("AREAS TO PROBE")
            lines.append("-" * 80)
            for area in areas_to_probe:
                lines.append(f"• {area}")
            lines.append("")
            lines.append("")

        # Custom Questions
        custom_questions = prep.custom_questions or []
        if custom_questions:
            lines.append("CUSTOM QUESTIONS (Added by Recruiter)")
            lines.append("-" * 80)
            for idx, q in enumerate(custom_questions, 1):
                lines.append(f"{idx}. {q}")
            lines.append("")
            lines.append("")

        # Question Feedback
        question_feedback = prep.question_feedback or {}
        if question_feedback:
            lines.append("QUESTION FEEDBACK")
            lines.append("-" * 80)
            for q_id, feedback in question_feedback.items():
                lines.append(f"• Question {q_id}: {feedback}")
            lines.append("")
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append(f"Last Updated: {prep.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("Generated by AgentHR Interview Preparation Assistant")
        lines.append("=" * 80)

        content = "\n".join(lines)
        document_bytes = content.encode("utf-8")

        logger.info(
            f"Document generated: {len(document_bytes)} bytes, "
            f"{len(technical_questions)} technical, "
            f"{len(behavioral_questions)} behavioral, "
            f"{len(situational_questions)} situational, "
            f"{len(skill_verification_questions)} skill verification questions"
        )

        return document_bytes

    except Exception as e:
        logger.error(f"Failed to format interview prep as document: {e}", exc_info=True)
        raise
