"""
Candidate comparison endpoints for side-by-side match analysis.

This module provides endpoints for comparing multiple candidates against a single
job vacancy, returning comprehensive match results with score breakdowns,
skill details, and rankings for easy side-by-side comparison.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path to import from data_extractor service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor"))

from database import get_db
from models.job_vacancy import JobVacancy
from models.resume import Resume

from analyzers import get_unified_matcher
from i18n.backend_translations import get_error_message, get_success_message

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Directory where uploaded resumes are stored (from centralized config)
UPLOAD_DIR = settings.upload_dir


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


class CandidateComparisonRequest(BaseModel):
    """Request model for candidate comparison endpoint."""

    vacancy_id: str = Field(..., description="ID of the job vacancy to compare against")
    resume_ids: List[str] = Field(
        ...,
        description="List of resume IDs to compare (1-10 candidates)",
        min_length=1,
        max_length=10
    )


class CandidateMatchScore(BaseModel):
    """Score breakdown for a single candidate."""

    overall_score: float = Field(..., description="Overall match score (0-1)")
    keyword_score: float = Field(..., description="Keyword matching score (0-1)")
    tfidf_score: float = Field(..., description="TF-IDF weighted score (0-1)")
    vector_score: float = Field(..., description="Vector semantic similarity score (0-1)")


class CandidateMatchResult(BaseModel):
    """Match result for a single candidate."""

    resume_id: str = Field(..., description="Resume identifier")
    filename: str = Field(..., description="Original resume filename")
    match_score: CandidateMatchScore = Field(..., description="Score breakdown")
    passed: bool = Field(..., description="Whether candidate passed the threshold")
    recommendation: str = Field(..., description="Hiring recommendation")
    matched_skills: List[str] = Field(..., description="Skills that matched")
    missing_skills: List[str] = Field(..., description="Skills that are missing")
    rank: int = Field(..., description="Rank among candidates (1=best)")


class ComparisonSummary(BaseModel):
    """Summary statistics for the comparison."""

    total_candidates: int = Field(..., description="Number of candidates compared")
    best_score: float = Field(..., description="Highest match score")
    average_score: float = Field(..., description="Average match score")
    worst_score: float = Field(..., description="Lowest match score")
    passed_count: int = Field(..., description="Number of candidates passing threshold")


class CandidateComparisonResponse(BaseModel):
    """Complete candidate comparison response."""

    vacancy_id: str = Field(..., description="Vacancy identifier")
    vacancy_title: str = Field(..., description="Job vacancy title")
    candidates: List[CandidateMatchResult] = Field(
        ..., description="Match results for all candidates, ranked by score"
    )
    summary: ComparisonSummary = Field(..., description="Comparison summary statistics")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


@router.post(
    "/compare-candidates",
    response_model=CandidateComparisonResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching"],
)
async def compare_candidates(
    http_request: Request,
    request: CandidateComparisonRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Compare multiple candidates against a job vacancy side-by-side.

    This endpoint performs comprehensive matching using three complementary approaches
    (Keyword, TF-IDF, and Vector) for each candidate and returns ranked results
    for easy comparison.

    Features:
    - Side-by-side comparison of multiple candidates
    - Detailed score breakdown (Keyword 50%, TF-IDF 30%, Vector 20%)
    - Automatic ranking by overall score
    - Summary statistics (best, average, worst scores)
    - Matched and missing skills for each candidate
    - Hiring recommendations for each candidate

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Comparison request with vacancy_id and resume_ids
        db: Async database session

    Returns:
        JSON response with:
        - vacancy_id: ID of the job vacancy
        - vacancy_title: Title of the job vacancy
        - candidates: List of candidate match results, ranked by score
        - summary: Comparison statistics
        - processing_time_ms: Total processing time

    Raises:
        HTTPException(404): If vacancy or any resume is not found
        HTTPException(500): If matching processing fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "vacancy_id": "vacancy-123",
        ...     "resume_ids": ["resume-1", "resume-2", "resume-3"]
        ... }
        >>> response = requests.post(
        ...     "/api/matching/compare-candidates",
        ...     json=data
        ... )
        >>> response.json()
        {
            "vacancy_id": "vacancy-123",
            "vacancy_title": "Python Developer",
            "candidates": [
                {
                    "resume_id": "resume-2",
                    "filename": "john_doe.pdf",
                    "match_score": {
                        "overall_score": 0.85,
                        "keyword_score": 0.90,
                        "tfidf_score": 0.80,
                        "vector_score": 0.75
                    },
                    "passed": true,
                    "recommendation": "good",
                    "matched_skills": ["Python", "Django", "SQL"],
                    "missing_skills": ["React"],
                    "rank": 1
                },
                ...
            ],
            "summary": {
                "total_candidates": 3,
                "best_score": 0.85,
                "average_score": 0.72,
                "worst_score": 0.58,
                "passed_count": 2
            },
            "processing_time_ms": 850.5
        }
    """
    locale = _extract_locale(http_request)
    start_time = time.time()

    try:
        logger.info(
            f"Starting candidate comparison: vacancy_id={request.vacancy_id}, "
            f"candidates={len(request.resume_ids)}"
        )

        # Step 1: Fetch vacancy from database
        try:
            vacancy_uuid = UUID(request.vacancy_id)
            vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
            vacancy_result = await db.execute(vacancy_query)
            vacancy = vacancy_result.scalar_one_or_none()

            if not vacancy:
                error_msg = get_error_message("vacancy_not_found", locale)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )

            logger.info(f"Found vacancy: {vacancy.title}")

        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale, field="vacancy_id")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Step 2: Prepare vacancy data
        vacancy_data = {
            "id": str(vacancy.id),
            "title": vacancy.title,
            "description": vacancy.description,
            "required_skills": vacancy.required_skills or [],
            "min_experience_months": vacancy.min_experience_months,
            "additional_requirements": vacancy.additional_requirements or [],
        }

        # Step 3: Process each resume
        candidate_results = []
        unified_matcher = get_unified_matcher()

        for resume_id in request.resume_ids:
            try:
                # Fetch resume from database
                try:
                    resume_uuid = UUID(resume_id)
                    resume_query = select(Resume).where(Resume.id == resume_uuid)
                    resume_result = await db.execute(resume_query)
                    resume = resume_result.scalar_one_or_none()

                    if not resume:
                        logger.warning(f"Resume {resume_id} not found, skipping")
                        continue

                    logger.info(f"Processing resume: {resume.filename}")

                except ValueError:
                    logger.warning(f"Invalid resume_id format: {resume_id}, skipping")
                    continue

                # Get resume text
                resume_text = None

                # Try raw_text from database first
                if resume.raw_text and len(resume.raw_text.strip()) >= 10:
                    resume_text = resume.raw_text
                    logger.info(f"Using raw_text from database for resume {resume_id}")
                else:
                    # Try to extract from file
                    file_path = None
                    for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
                        potential_path = UPLOAD_DIR / f"{resume_id}{ext}"
                        if potential_path.exists():
                            file_path = potential_path
                            break

                    if file_path:
                        try:
                            from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

                            file_ext = file_path.suffix.lower()
                            if file_ext == ".pdf":
                                result = extract_text_from_pdf(str(file_path))
                            elif file_ext == ".docx":
                                result = extract_text_from_docx(str(file_path))
                            else:
                                logger.warning(f"Unsupported file type: {file_ext}")
                                continue

                            resume_text = result.get("text", "")

                            if not resume_text or len(resume_text.strip()) < 10:
                                logger.warning(f"Could not extract text from {file_path}")
                                continue

                        except Exception as e:
                            logger.error(f"Error extracting text from file: {e}")
                            continue
                    else:
                        logger.warning(f"No file found for resume {resume_id}")
                        continue

                if not resume_text or len(resume_text.strip()) < 10:
                    logger.warning(f"No text available for resume {resume_id}")
                    continue

                # Extract skills using pattern matching
                from analyzers.hf_skill_extractor import extract_resume_skills

                skills_result = extract_resume_skills(
                    resume_text, method="pattern", top_n=30
                )
                resume_skills = skills_result.get("skills", [])

                logger.info(f"Extracted {len(resume_skills)} skills from resume {resume_id}")

                # Perform unified matching
                match_result = unified_matcher.match(
                    resume_text=resume_text,
                    resume_skills=resume_skills,
                    job_title=vacancy.title,
                    job_description=vacancy.description,
                    required_skills=vacancy_data["required_skills"],
                    context=vacancy.title.lower(),
                )

                # Store candidate result
                candidate_results.append(
                    {
                        "resume_id": resume_id,
                        "filename": resume.filename,
                        "overall_score": match_result.overall_score,
                        "keyword_score": match_result.keyword_score,
                        "tfidf_score": match_result.tfidf_score,
                        "vector_score": match_result.vector_score,
                        "passed": match_result.passed,
                        "recommendation": match_result.recommendation,
                        "matched_skills": match_result.matched_skills,
                        "missing_skills": match_result.missing_skills,
                    }
                )

                logger.info(
                    f"Completed matching for resume {resume_id}: "
                    f"score={match_result.overall_score:.2f}"
                )

            except Exception as e:
                logger.error(f"Error processing resume {resume_id}: {e}", exc_info=True)
                # Continue with other resumes
                continue

        # Step 4: Check if we have any results
        if not candidate_results:
            error_msg = get_error_message("no_valid_resumes", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Step 5: Rank candidates by overall score (descending)
        candidate_results.sort(key=lambda x: x["overall_score"], reverse=True)

        # Step 6: Add ranks and build response
        ranked_candidates = []
        for idx, result in enumerate(candidate_results, start=1):
            ranked_candidates.append(
                CandidateMatchResult(
                    resume_id=result["resume_id"],
                    filename=result["filename"],
                    match_score=CandidateMatchScore(
                        overall_score=round(result["overall_score"], 3),
                        keyword_score=round(result["keyword_score"], 3),
                        tfidf_score=round(result["tfidf_score"], 3),
                        vector_score=round(result["vector_score"], 3),
                    ),
                    passed=result["passed"],
                    recommendation=result["recommendation"],
                    matched_skills=result["matched_skills"],
                    missing_skills=result["missing_skills"],
                    rank=idx,
                )
            )

        # Step 7: Calculate summary statistics
        scores = [r["overall_score"] for r in candidate_results]
        best_score = round(max(scores), 3)
        worst_score = round(min(scores), 3)
        average_score = round(sum(scores) / len(scores), 3)
        passed_count = sum(1 for r in candidate_results if r["passed"])

        summary = ComparisonSummary(
            total_candidates=len(candidate_results),
            best_score=best_score,
            average_score=average_score,
            worst_score=worst_score,
            passed_count=passed_count,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Build response
        response_data = {
            "vacancy_id": request.vacancy_id,
            "vacancy_title": vacancy.title,
            "candidates": [c.model_dump() for c in ranked_candidates],
            "summary": summary.model_dump(),
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Candidate comparison completed: {len(candidate_results)} candidates, "
            f"best_score={best_score:.2f}, avg_score={average_score:.2f}, "
            f"processing_time={processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in candidate comparison: {e}", exc_info=True)
        error_msg = get_error_message("processing_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
