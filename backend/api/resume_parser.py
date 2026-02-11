"""
Resume parsing API endpoints.

This module provides endpoints for parsing resume files (PDF, DOCX),
extracting structured data including skills, position, education, work
experience, and calculating experience metrics.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import get_settings
from i18n.backend_translations import get_error_message, get_success_message
from models.parsed_resume import ParsedResume, Skill, Education, WorkExperience, Language, ExperienceSummary, SourceTextLocation
from parsers import PDFParser, DOCXParser
from nlp.resume_entities import extract_resume_entities
from analyzers.experience_calculator import calculate_dual_track_experience

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


class ResumeParseResponse(BaseModel):
    """Response model for resume parse endpoint."""

    success: bool = Field(..., description="Whether parsing was successful")
    data: Optional[ParsedResume] = Field(None, description="Parsed resume data")
    message: str = Field(..., description="Success or error message")
    warnings: list = Field(default_factory=list, description="Parsing warnings")


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


def _parse_document(file_content: bytes, filename: str, file_ext: str) -> Dict:
    """
    Parse document and extract text using appropriate parser.

    Args:
        file_content: File content as bytes
        filename: Original filename
        file_ext: File extension (.pdf or .docx)

    Returns:
        Dictionary with parsing result containing:
        - success: bool
        - text: str (extracted text)
        - error: str (if failed)
    """
    try:
        if file_ext == ".pdf":
            parser = PDFParser()
            result = parser.parse_bytes(file_content, filename)
        elif file_ext == ".docx":
            parser = DOCXParser()
            result = parser.parse_bytes(file_content, filename)
        else:
            return {
                "success": False,
                "error": f"Unsupported file extension: {file_ext}",
                "text": None,
            }

        return result

    except Exception as e:
        logger.error(f"Error parsing document {filename}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "text": None,
        }


def _detect_language(text: str) -> str:
    """
    Detect language of text (simple heuristic).

    Args:
        text: Text to analyze

    Returns:
        Language code ('en' or 'ru')
    """
    if not text:
        return "en"

    # Simple heuristic: check for Cyrillic characters
    cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    total_chars = sum(1 for c in text if c.isalpha())

    if total_chars > 0 and cyrillic_chars / total_chars > 0.3:
        return "ru"

    return "en"


def _build_source_location(
    location: Optional[Tuple[int, int]],
    raw_text: str
) -> Optional[SourceTextLocation]:
    """
    Build SourceTextLocation from character position tuple.

    Args:
        location: Tuple of (start, end) character positions
        raw_text: Full text to extract the source segment from

    Returns:
        SourceTextLocation with text field populated, or None if location is None
    """
    if location is None or not raw_text:
        return None

    try:
        start, end = location
        if 0 <= start < end <= len(raw_text):
            source_text = raw_text[start:end].strip()
            return SourceTextLocation(
                page=None,  # Page info not available from text extraction
                bbox=None,  # BBox not available from text extraction
                text=source_text,
            )
    except (TypeError, ValueError, IndexError):
        pass

    return None


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    tags=["Resume Parser"],
)
async def parse_resume(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """
    Parse a resume file and extract structured data.

    This endpoint accepts resume files in PDF or DOCX format, validates the file
    type and size, extracts text, parses entities (skills, position, education,
    work experience, languages), and calculates experience metrics.

    Args:
        request: FastAPI request object (for Accept-Language header)
        file: Uploaded resume file (PDF or DOCX)

    Returns:
        JSON response with parsed resume data including:
        - skills: List of extracted skills with categories and confidence
        - position: Most recent job position
        - education: List of education entries
        - work_experience: List of work experience entries
        - languages: List of languages with proficiency
        - experience_summary: Total and framework-specific experience

    Raises:
        HTTPException(415): If file type is not supported
        HTTPException(413): If file size exceeds maximum allowed
        HTTPException(500): If parsing or extraction fails

    Examples:
        >>> import requests
        >>> with open("resume.pdf", "rb") as f:
        ...     response = requests.post("/api/resume-parser/parse", files={"file": f})
        >>> response.json()
        {
            "success": true,
            "data": {
                "raw_text": "...",
                "language": "en",
                "position": "Senior Software Engineer",
                "skills": [...],
                "education": [...],
                "work_experience": [...],
                "languages": [...],
                "experience_summary": {...}
            },
            "message": "Resume parsed successfully",
            "warnings": []
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Received resume for parsing: {file.filename} ({file_size} bytes)")

        # Validate file type
        validate_file_type(file.filename or "unknown", file.content_type or "application/octet-stream", locale)

        # Validate file size
        validate_file_size(file_size, locale)

        # Get file extension
        safe_filename = Path(file.filename or "resume").name
        file_ext = Path(safe_filename).suffix.lower()

        # Parse document and extract text
        logger.info(f"Parsing {file_ext} document: {safe_filename}")
        parse_result = _parse_document(file_content, safe_filename, file_ext)

        if not parse_result.get("success"):
            error_msg = parse_result.get("error", "Unknown parsing error")
            logger.error(f"Document parsing failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse document: {error_msg}",
            )

        raw_text = parse_result.get("text", "")
        if not raw_text or len(raw_text.strip()) < 10:
            logger.warning(f"Extracted text is too short or empty: {len(raw_text)} chars")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract sufficient text from document. "
                      "The document may be image-based or password-protected.",
            )

        logger.info(f"Extracted {len(raw_text)} characters from document")

        # Detect language
        language = _detect_language(raw_text)
        logger.info(f"Detected language: {language}")

        # Extract resume entities
        logger.info("Extracting resume entities...")
        entities = extract_resume_entities(raw_text, language=language)

        # Calculate experience (dual-track)
        logger.info("Calculating experience metrics...")
        experience_result = calculate_dual_track_experience(raw_text, language=language)

        # Extract source locations for visual highlighting
        position_data = entities.get("position", {}) or {}
        age_data = entities.get("age", {}) or {}
        education_data = entities.get("education", {}) or {}
        languages_data = entities.get("languages", {}) or {}

        # Get education entries list (from education_data dict)
        education_entries = education_data.get("education_entries") or []

        # Get languages list (from languages_data dict)
        language_entries = languages_data.get("languages") or []

        # Build source locations dictionary for each extracted field
        source_locations = {
            "position": _build_source_location(
                position_data.get("location"), raw_text
            ).model_dump(mode='json') if _build_source_location(position_data.get("location"), raw_text) else None,
            "age": _build_source_location(
                age_data.get("location"), raw_text
            ).model_dump(mode='json') if _build_source_location(age_data.get("location"), raw_text) else None,
            "education": [
                _build_source_location(edu.get("location"), raw_text).model_dump(mode='json')
                if _build_source_location(edu.get("location"), raw_text) else None
                for edu in education_entries
            ],
            "languages": [
                _build_source_location(lang.get("location"), raw_text).model_dump(mode='json')
                if _build_source_location(lang.get("location"), raw_text) else None
                for lang in language_entries
            ],
        }

        # Build parsed resume model
        parsed_resume = ParsedResume(
            raw_text=raw_text,
            language=language,
            position=position_data.get("position"),
            age=age_data.get("age"),
            skills=[
                Skill(
                    name=skill.get("name", ""),
                    original_name=skill.get("original_name", skill.get("name", "")),
                    category=skill.get("category"),
                    variations=skill.get("variations", []),
                    sources=skill.get("sources", []),
                    confidence=skill.get("confidence", 0.0),
                    source_text_location=_build_source_location(skill.get("location"), raw_text),
                )
                for skill in entities.get("skills", [])
            ],
            education=[
                Education(
                    degree=edu.get("degree") or edu.get("level"),
                    institution=edu.get("institution"),
                    field_of_study=edu.get("field_of_study") or edu.get("field"),
                    start_date=edu.get("start_date"),
                    end_date=edu.get("end_date"),
                    gpa=edu.get("gpa"),
                    description=edu.get("description"),
                    source_text_location=_build_source_location(edu.get("location"), raw_text),
                )
                for edu in education_entries
            ],
            work_experience=[
                WorkExperience(
                    company=exp.get("company"),
                    position=exp.get("position"),
                    start_date=exp.get("start_date"),
                    end_date=exp.get("end_date"),
                    duration_months=exp.get("duration_months"),
                    description=exp.get("description"),
                    skills=exp.get("skills", []),
                    location=exp.get("location"),
                    source_text_location=_build_source_location(exp.get("location_char"), raw_text),
                )
                for exp in entities.get("work_experience", [])
            ],
            languages=[
                Language(
                    name=lang.get("language") or lang.get("name", ""),
                    proficiency=lang.get("proficiency"),
                    certification=lang.get("certification"),
                    source_text_location=_build_source_location(lang.get("location"), raw_text),
                )
                for lang in language_entries
            ],
            experience_summary=ExperienceSummary(
                total_months=experience_result.get("total_months", 0),
                total_years=experience_result.get("total_years", 0.0),
                total_years_formatted=experience_result.get("total_years_formatted", "0 years"),
                framework_specific=experience_result.get("framework_specific", {}),
            ) if experience_result.get("total_months", 0) > 0 else None,
            warnings=entities.get("warnings", []),
            processing_metadata={
                "parser": f"{file_ext[1:]}_parser",
                "file_extension": file_ext,
                "text_length": len(raw_text),
                "num_skills": len(entities.get("skills", [])),
                "num_education": len(education_entries),
                "num_work_experience": len(entities.get("work_experience", [])),
                "num_languages": len(language_entries),
            },
        )

        # Get translated success message
        success_message = get_success_message("file_uploaded", locale)

        logger.info(
            f"Resume parsed successfully: "
            f"position={parsed_resume.position}, "
            f"skills={len(parsed_resume.skills)}, "
            f"experience={parsed_resume.experience_summary.total_years if parsed_resume.experience_summary else 0} years"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": parsed_resume.model_dump(mode='json'),
                "source_locations": source_locations,
                "message": success_message,
                "warnings": parsed_resume.warnings,
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error parsing resume: {e}", exc_info=True)
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
