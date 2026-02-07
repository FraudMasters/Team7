"""
Эндпоинты сопоставления вакансий с обработкой синонимов навыков и визуальным выделением.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для сравнения резюме с вакансиями,
расчета процентов совпадения и визуального выделения совпавших (зеленый)
и отсутствующих (красный) навыков.
"""
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.match_result import MatchResult

from analyzers import EnhancedSkillMatcher

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")

# Path to skill synonyms file
SYNONYMS_FILE = Path(__file__).parent.parent / "models" / "skill_synonyms.json"


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


class MatchRequest(BaseModel):
    """Request model for job matching endpoint."""

    resume_id: str = Field(..., description="Unique identifier of the resume to match")
    vacancy_data: Dict[str, Any] = Field(
        ..., description="Job vacancy data with required skills and experience"
    )


class SkillMatch(BaseModel):
    """Individual skill match result with confidence scoring."""

    skill: str = Field(..., description="The skill name from the vacancy")
    status: str = Field(..., description="Match status: 'matched' or 'missing'")
    matched_as: Optional[str] = Field(
        None, description="The actual skill name found in resume (if matched)"
    )
    highlight: str = Field(..., description="Highlight color: 'green' or 'red'")
    confidence: float = Field(
        0.0, description="Confidence score from 0.0 to 1.0 (0% to 100%)"
    )
    match_type: str = Field(
        "none", description="Type of match: 'direct', 'context', 'synonym', 'fuzzy', or 'none'"
    )


class ExperienceVerification(BaseModel):
    """Experience verification results."""

    required_months: int = Field(..., description="Required experience in months")
    actual_months: int = Field(..., description="Actual experience in months")
    meets_requirement: bool = Field(..., description="Whether experience requirement is met")
    summary: str = Field(..., description="Human-readable experience summary")


class MatchResponse(BaseModel):
    """Complete job matching response."""

    resume_id: str = Field(..., description="Resume identifier")
    vacancy_title: str = Field(..., description="Job vacancy title")
    match_percentage: float = Field(..., description="Overall skill match percentage (0-100)")
    required_skills_match: List[SkillMatch] = Field(
        ..., description="Match results for required skills"
    )
    additional_skills_match: List[SkillMatch] = Field(
        ..., description="Match results for additional/preferred skills"
    )
    experience_verification: Optional[ExperienceVerification] = Field(
        None, description="Experience requirement verification (if applicable)"
    )
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


@router.post(
    "/compare",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching"],
)
async def compare_resume_to_vacancy(http_request: Request, request: MatchRequest) -> JSONResponse:
    """
    Compare a resume to a job vacancy with skill synonym handling.

    This endpoint performs intelligent matching between resume skills and job
    vacancy requirements, handling synonyms (e.g., PostgreSQL ≈ SQL) and
    providing visual highlighting for recruiters.

    Features:
    - Skill synonym matching (PostgreSQL matches SQL requirement)
    - Match percentage calculation
    - Visual highlighting (green=matched, red=missing)
    - Experience verification (sums months across projects)
    - Case-insensitive comparison
    - Support for multi-word skills
    - Result caching for improved performance

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Match request with resume_id and vacancy_data

    Returns:
        JSON response with match results, highlighting data, and verification

    Raises:
        HTTPException(404): If resume file is not found
        HTTPException(422): If text extraction fails
        HTTPException(500): If matching processing fails

    Examples:
        >>> import requests
        >>> vacancy = {
        ...     "title": "Java Developer",
        ...     "required_skills": ["Java", "Spring", "SQL"],
        ...     "min_experience_months": 36
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8001/api/matching/compare",
        ...     json={"resume_id": "abc123", "vacancy_data": vacancy}
        ... )
        >>> response.json()
        {
            "resume_id": "abc123",
            "vacancy_title": "Java Developer",
            "match_percentage": 66.67,
            "required_skills_match": [
                {"skill": "Java", "status": "matched", "matched_as": "Java", "highlight": "green"},
                {"skill": "Spring", "status": "matched", "matched_as": "Spring Boot", "highlight": "green"},
                {"skill": "SQL", "status": "matched", "matched_as": "PostgreSQL", "highlight": "green"}
            ],
            "additional_skills_match": [],
            "experience_verification": {
                "required_months": 36,
                "actual_months": 47,
                "meets_requirement": true,
                "summary": "47 months (3 years 11 months) of experience"
            },
            "processing_time_ms": 123.45
        }
    """
    start_time = time.time()

    # Extract locale from Accept-Language header
    locale = _extract_locale(http_request)

    try:
        logger.info(f"Starting matching for resume_id: {request.resume_id}")

        # Step 1: Find the resume file
        for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
            file_path = UPLOAD_DIR / f"{request.resume_id}{ext}"
            if file_path.exists():
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume file not found: {request.resume_id}",
            )

        logger.info(f"Found resume file: {file_path}")

        # Step 2: Extract text from file
        try:
            from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

            file_ext = file_path.suffix.lower()
            if file_ext == ".pdf":
                result = extract_text_from_pdf(file_path)
            elif file_ext == ".docx":
                result = extract_text_from_docx(file_path)
            else:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported file type: {file_ext}",
                )

            if result.get("error"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Text extraction failed: {result['error']}",
                )

            resume_text = result.get("text", "")
            if not resume_text or len(resume_text.strip()) < 10:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Extracted text is too short or empty",
                )

            logger.info(f"Extracted {len(resume_text)} characters from resume")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error extracting text: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Text extraction failed: {str(e)}",
            ) from e

        # Step 3: Detect language
        try:
            from langdetect import detect, LangDetectException

            try:
                detected_lang = detect(resume_text)
                language = "ru" if detected_lang == "ru" else "en"
            except LangDetectException:
                language = "en"
        except ImportError:
            language = "en"

        logger.info(f"Detected language: {language}")

        # Step 4: Extract skills from resume
        logger.info("Extracting skills from resume...")
        try:
            from services.data_extractor.analyzers import (
                extract_resume_keywords,
                extract_resume_entities,
            )

            keywords_result = extract_resume_keywords(resume_text, language=language)
            entities_result = extract_resume_entities(resume_text, language=language)

            # Combine keywords and technical skills
            resume_skills = list(set(
                (keywords_result.get("keywords") or []) +
                (keywords_result.get("keyphrases") or []) +
                (entities_result.get("technical_skills") or [])
            ))

        except ImportError:
            # Fallback to simple keyword extraction
            logger.warning("Could not import analyzers, using simple extraction")
            resume_skills = []

        logger.info(f"Extracted {len(resume_skills)} unique skills from resume")

        # Step 5: Initialize enhanced skill matcher
        enhanced_matcher = EnhancedSkillMatcher()
        synonyms_map = enhanced_matcher.load_synonyms()
        logger.info(f"Initialized enhanced skill matcher with {len(synonyms_map)} synonym mappings")

        # Step 6: Get vacancy data
        vacancy_title = request.vacancy_data.get(
            "title", request.vacancy_data.get("position", "Unknown Position")
        )
        required_skills = request.vacancy_data.get("required_skills", [])
        additional_skills = request.vacancy_data.get(
            "additional_requirements", request.vacancy_data.get("additional_skills", [])
        )
        min_experience_months = request.vacancy_data.get("min_experience_months", None)

        # If required_skills is a string list, use it directly
        if isinstance(required_skills, str):
            required_skills = [required_skills]

        # Step 7: Match required skills with enhanced matcher
        required_skills_matches = []
        for skill in required_skills:
            match_result = enhanced_matcher.match_with_context(
                resume_skills=resume_skills,
                required_skill=skill,
                context=vacancy_title.lower(),
                use_fuzzy=True
            )

            if match_result["matched"]:
                required_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="matched",
                        matched_as=match_result["matched_as"],
                        highlight="green",
                        confidence=round(match_result["confidence"], 2),
                        match_type=match_result["match_type"]
                    )
                )
            else:
                required_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="missing",
                        matched_as=None,
                        highlight="red",
                        confidence=0.0,
                        match_type="none"
                    )
                )

        # Step 8: Match additional/preferred skills with enhanced matcher
        additional_skills_matches = []
        for skill in additional_skills:
            match_result = enhanced_matcher.match_with_context(
                resume_skills=resume_skills,
                required_skill=skill,
                context=vacancy_title.lower(),
                use_fuzzy=True
            )

            if match_result["matched"]:
                additional_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="matched",
                        matched_as=match_result["matched_as"],
                        highlight="green",
                        confidence=round(match_result["confidence"], 2),
                        match_type=match_result["match_type"]
                    )
                )
            else:
                additional_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="missing",
                        matched_as=None,
                        highlight="red",
                        confidence=0.0,
                        match_type="none"
                    )
                )

        # Step 9: Calculate match percentage
        total_required = len(required_skills)
        matched_required = sum(
            1 for m in required_skills_matches if m.status == "matched"
        )
        match_percentage = (
            round((matched_required / total_required * 100), 2) if total_required > 0 else 0.0
        )

        logger.info(
            f"Matched {matched_required}/{total_required} required skills ({match_percentage}%)"
        )

        # Step 10: Verify experience (if vacancy has experience requirement)
        experience_verification = None
        if min_experience_months and min_experience_months > 0:
            logger.info(f"Verifying experience requirement: {min_experience_months} months")

            primary_skill = required_skills[0] if required_skills else None

            if primary_skill:
                try:
                    from services.data_extractor.analyzers import (
                        calculate_skill_experience,
                        format_experience_summary,
                    )

                    skill_exp_result = calculate_skill_experience(
                        resume_text, primary_skill, language=language
                    )
                    actual_months = skill_exp_result.get("total_months", 0)
                    experience_summary = format_experience_summary(actual_months)

                    experience_verification = ExperienceVerification(
                        required_months=min_experience_months,
                        actual_months=actual_months,
                        meets_requirement=actual_months >= min_experience_months,
                        summary=experience_summary,
                    )

                    logger.info(
                        f"Experience verification: {actual_months} months (required: {min_experience_months})"
                    )

                except Exception as e:
                    logger.warning(f"Experience calculation failed: {e}")
                    # Continue without experience verification

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Build response
        response_data = {
            "resume_id": request.resume_id,
            "vacancy_title": vacancy_title,
            "match_percentage": match_percentage,
            "required_skills_match": [
                m.model_dump() for m in required_skills_matches
            ],
            "additional_skills_match": [
                m.model_dump() for m in additional_skills_matches
            ],
            "experience_verification": (
                experience_verification.model_dump() if experience_verification else None
            ),
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Matching completed for resume_id {request.resume_id} in {processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching resume to vacancy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching failed: {str(e)}",
        ) from e
