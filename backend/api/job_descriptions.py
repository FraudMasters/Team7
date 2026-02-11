"""
Job description generation endpoints for creating AI-powered job descriptions.

This module provides endpoints for generating professional job descriptions
based on role title, required skills, and experience requirements using LLMs.
"""
import logging
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from analyzers.job_description_generator import JobDescriptionGenerator as AnalyzerJobDescriptionGenerator
from config import get_settings
from i18n.backend_translations import get_error_message, get_success_message

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class GenerateJobDescriptionRequest(BaseModel):
    """Request model for generating job descriptions."""

    title: str = Field(..., description="Job title (e.g., 'Senior Python Developer')")
    required_skills: List[str] = Field(
        ..., description="List of required technical skills"
    )
    min_experience_months: Optional[int] = Field(
        default=None, description="Minimum experience in months"
    )
    seniority_level: Optional[str] = Field(
        default=None, description="Seniority level (junior, mid, senior, lead)"
    )
    industry: Optional[str] = Field(
        default=None, description="Industry sector (e.g., 'Technology', 'Finance')"
    )
    work_format: Optional[str] = Field(
        default=None, description="Work format (remote, office, hybrid)"
    )
    location: Optional[str] = Field(
        default=None, description="Job location"
    )
    employment_type: Optional[str] = Field(
        default=None, description="Employment type (full-time, part-time, contract)"
    )
    salary_range: Optional[str] = Field(
        default=None, description="Salary range (e.g., '$80,000 - $120,000')"
    )
    additional_requirements: Optional[List[str]] = Field(
        default=None, description="Additional preferred skills/qualifications"
    )
    tone: Optional[str] = Field(
        default="professional", description="Tone for the description (professional, casual, formal, friendly)"
    )
    language: Optional[str] = Field(
        default="en", description="Language for the job description (en, ru)"
    )


class JobDescriptionResponse(BaseModel):
    """Response model for job description data."""

    title: str = Field(..., description="Job title")
    summary: str = Field(..., description="Brief summary of the role")
    responsibilities: List[str] = Field(..., description="Key responsibilities")
    requirements: List[str] = Field(..., description="Requirements and qualifications")
    benefits: List[str] = Field(..., description="Benefits and perks")
    company_culture: str = Field(..., description="Company culture description")
    interview_process: str = Field(..., description="Interview process overview")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model name used")
    generated_at: str = Field(..., description="Timestamp of generation")
    # Bias checking fields from the analyzer
    inclusive_language_score: Optional[float] = Field(
        default=None, description="Inclusiveness score (0-1)"
    )
    bias_warnings: List[str] = Field(
        default_factory=list, description="Bias warnings detected"
    )


# ============================================================================
# Helper Functions
# ============================================================================

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
# API Endpoints
# ============================================================================

@router.post(
    "/generate",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Job Descriptions"],
)
async def generate_job_description(
    http_request: Request, request: GenerateJobDescriptionRequest
) -> JSONResponse:
    """
    Generate a professional job description based on role requirements.

    This endpoint creates comprehensive, inclusive job descriptions using LLMs.
    The description includes a summary, key responsibilities, requirements,
    benefits, company culture overview, interview process information, and
    bias checking results to ensure inclusive language.

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Generate request with job details

    Returns:
        JSON response with generated job description including bias checking results

    Raises:
        HTTPException(400): If validation fails
        HTTPException(500): If generation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/job-descriptions/generate",
        ...     json={
        ...         "title": "Senior Python Developer",
        ...         "required_skills": ["Python", "Django", "PostgreSQL"],
        ...         "min_experience_months": 60
        ...     }
        ... )
        >>> response.json()
        {
            "title": "Senior Python Developer",
            "summary": "We are looking for a skilled Senior Python Developer...",
            "responsibilities": [...],
            "requirements": [...],
            "inclusive_language_score": 0.95,
            "bias_warnings": []
            ...
        }
    """
    locale = _extract_locale(http_request)
    start_time = time.time()

    try:
        logger.info(f"Generating job description for title: {request.title}")

        # Validate required fields
        if not request.title or not request.title.strip():
            error_msg = get_error_message("missing_required_field", locale, field="title")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        if not request.required_skills or len(request.required_skills) == 0:
            error_msg = get_error_message("missing_required_field", locale, field="required_skills")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Validate seniority level if provided
        valid_seniority_levels = ["junior", "mid", "middle", "senior", "lead", "principal", "entry"]
        if request.seniority_level:
            if request.seniority_level.lower() not in valid_seniority_levels:
                logger.warning(f"Unusual seniority level: {request.seniority_level}")

        # Validate work format if provided
        valid_work_formats = ["remote", "office", "hybrid", "on-site", "onsite"]
        if request.work_format:
            if request.work_format.lower() not in [w.lower() for w in valid_work_formats]:
                logger.warning(f"Unusual work format: {request.work_format}")

        # Validate tone if provided
        valid_tones = ["professional", "casual", "formal", "friendly"]
        if request.tone and request.tone.lower() not in valid_tones:
            logger.warning(f"Invalid tone, defaulting to professional: {request.tone}")
            request.tone = "professional"

        # Generate job description using the analyzer module
        generator = AnalyzerJobDescriptionGenerator()
        result = await generator.generate_description(
            title=request.title,
            required_skills=request.required_skills,
            min_experience_months=request.min_experience_months,
            seniority_level=request.seniority_level,
            industry=request.industry,
            work_format=request.work_format,
            location=request.location,
            employment_type=request.employment_type,
            salary_range=request.salary_range,
            additional_requirements=request.additional_requirements,
            tone=request.tone or "professional",
            language=request.language or "en",
        )

        # Build response WITH bias checking results
        response_data = {
            "title": result.title,
            "summary": result.summary,
            "responsibilities": result.responsibilities,
            "requirements": result.requirements,
            "benefits": result.benefits,
            "company_culture": result.company_culture,
            "interview_process": result.interview_process,
            "provider": result.provider,
            "model": result.model,
            "generated_at": result.generated_at,
            "inclusive_language_score": result.inclusive_language_score,
            "bias_warnings": result.bias_warnings,
        }

        processing_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Job description generated for title: {request.title} "
            f"in {processing_time_ms:.2f}ms "
            f"(inclusive_score: {result.inclusive_language_score:.2f}, "
            f"{len(result.bias_warnings)} bias warnings)"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        error_msg = get_error_message("invalid_input", locale)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error generating job description: {e}", exc_info=True)
        error_msg = get_error_message("internal_server_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
