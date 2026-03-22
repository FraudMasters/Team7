"""
Resume comparison endpoint.

This module provides the endpoint for comparing a resume against top candidates
for a specific job vacancy, showing how the resume ranks relative to other applicants.
"""
import logging
import time
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from analyzers import get_unified_matcher
from database import get_db
from i18n.backend_translations import get_error_message
from models.job_vacancy import JobVacancy
from models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


class ComparisonRequest(BaseModel):
    """Request model for resume comparison."""

    vacancy_id: str = Field(..., description="ID of the job vacancy to compare against")
    limit: int = Field(5, ge=1, le=20, description="Number of top candidates to compare against (1-20)")


class CandidateScore(BaseModel):
    """Score information for a candidate."""

    resume_id: str = Field(..., description="Resume identifier")
    filename: str = Field(..., description="Original resume filename")
    overall_score: float = Field(..., description="Overall match score (0-1)")
    keyword_score: float = Field(..., description="Keyword matching score (0-1)")
    tfidf_score: float = Field(..., description="TF-IDF weighted score (0-1)")
    vector_score: float = Field(..., description="Vector semantic similarity score (0-1)")
    rank: int = Field(..., description="Rank among all candidates (1=best)")


class ComparisonResult(BaseModel):
    """Comparison result for the target resume."""

    target_resume: CandidateScore = Field(..., description="Score and rank of the target resume")
    top_candidates: List[CandidateScore] = Field(..., description="Top candidates for comparison")
    percentile: float = Field(..., description="Percentile rank of target resume (0-100)")
    better_than_count: int = Field(..., description="Number of candidates the target resume beats")
    worse_than_count: int = Field(..., description="Number of candidates better than target resume")
    recommendation: str = Field(..., description="Recommendation based on ranking")


class ComparisonResponse(BaseModel):
    """Response model for resume comparison."""

    resume_id: str = Field(..., description="Target resume identifier")
    vacancy_id: str = Field(..., description="Vacancy identifier")
    vacancy_title: str = Field(..., description="Job vacancy title")
    comparison: ComparisonResult = Field(..., description="Comparison results")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


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


def _generate_recommendation(rank: int, total_candidates: int, percentile: float) -> str:
    """
    Generate a recommendation based on ranking.

    Args:
        rank: Rank of the target resume (1=best)
        total_candidates: Total number of candidates
        percentile: Percentile rank (0-100)

    Returns:
        Recommendation string
    """
    if percentile >= 90:
        return "excellent"
    elif percentile >= 75:
        return "good"
    elif percentile >= 50:
        return "average"
    elif percentile >= 25:
        return "below_average"
    else:
        return "poor"


@router.post(
    "/{resume_id}/compare-top",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    tags=["Resumes"],
)
async def compare_resume_with_top_candidates(
    http_request: Request,
    resume_id: str,
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Compare a resume against top candidates for a vacancy.

    This endpoint analyzes how a specific resume ranks compared to the top candidates
    for a job vacancy. It performs comprehensive matching using three complementary
    approaches (Keyword, TF-IDF, and Vector) and returns:
    - The target resume's score and rank
    - Top candidates for comparison
    - Percentile ranking
    - Recommendation based on relative performance

    Features:
    - Multi-dimensional scoring (Keyword 50%, TF-IDF 30%, Vector 20%)
    - Percentile-based ranking
    - Comparison against top N candidates
    - Actionable recommendations

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        resume_id: ID of the resume to compare
        request: Comparison request with vacancy_id and limit
        db: Async database session

    Returns:
        JSON response with:
        - resume_id: Target resume identifier
        - vacancy_id: Vacancy identifier
        - vacancy_title: Job title
        - comparison: Detailed comparison results
        - processing_time_ms: Processing time

    Raises:
        HTTPException(400): If resume_id or vacancy_id is invalid
        HTTPException(404): If resume or vacancy is not found
        HTTPException(500): If comparison processing fails

    Examples:
        >>> import requests
        >>> data = {"vacancy_id": "vacancy-123", "limit": 5}
        >>> response = requests.post(
        ...     "/api/resumes/resume-456/compare-top",
        ...     json=data
        ... )
        >>> response.json()
        {
            "resume_id": "resume-456",
            "vacancy_id": "vacancy-123",
            "vacancy_title": "Senior Python Developer",
            "comparison": {
                "target_resume": {
                    "resume_id": "resume-456",
                    "filename": "john_doe.pdf",
                    "overall_score": 0.75,
                    "keyword_score": 0.80,
                    "tfidf_score": 0.70,
                    "vector_score": 0.68,
                    "rank": 3
                },
                "top_candidates": [...],
                "percentile": 82.5,
                "better_than_count": 7,
                "worse_than_count": 2,
                "recommendation": "good"
            },
            "processing_time_ms": 1250.5
        }
    """
    locale = _extract_locale(http_request)
    start_time = time.time()

    try:
        logger.info(
            f"Starting resume comparison: resume_id={resume_id}, "
            f"vacancy_id={request.vacancy_id}, limit={request.limit}"
        )

        # Step 1: Validate and fetch target resume
        try:
            resume_uuid = UUID(resume_id)
            resume_query = select(Resume).where(Resume.id == resume_uuid)
            resume_result = await db.execute(resume_query)
            target_resume = resume_result.scalar_one_or_none()

            if not target_resume:
                error_msg = get_error_message("resume_not_found", locale)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )

            logger.info(f"Found target resume: {target_resume.filename}")

        except ValueError:
            error_msg = get_error_message("invalid_resume_id", locale)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Step 2: Validate and fetch vacancy
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

        # Step 3: Check if target resume has text
        if not target_resume.raw_text or len(target_resume.raw_text.strip()) < 10:
            logger.warning(f"Resume {resume_id} has no raw_text")
            error_msg = get_error_message("resume_text_missing", locale)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg or "Resume text not available for analysis",
            )

        # Step 4: Get all resumes from database for comparison
        all_resumes_query = select(Resume).where(Resume.raw_text.isnot(None))
        all_resumes_result = await db.execute(all_resumes_query)
        all_resumes = all_resumes_result.scalars().all()

        if len(all_resumes) == 0:
            logger.warning("No resumes found in database for comparison")
            error_msg = get_error_message("no_resumes_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg or "No resumes available for comparison",
            )

        logger.info(f"Found {len(all_resumes)} total resumes for comparison")

        # Step 5: Perform matching for all resumes (including target)
        unified_matcher = get_unified_matcher()
        all_results = []

        for resume in all_resumes:
            try:
                # Skip resumes without text
                if not resume.raw_text or len(resume.raw_text.strip()) < 10:
                    continue

                # Extract skills using pattern matching
                from analyzers.hf_skill_extractor import extract_resume_skills

                skills_result = extract_resume_skills(
                    resume.raw_text, method="pattern", top_n=30
                )
                resume_skills = skills_result.get("skills", [])

                # Perform unified matching
                match_result = unified_matcher.match(
                    resume_text=resume.raw_text,
                    resume_skills=resume_skills,
                    job_title=vacancy.title,
                    job_description=vacancy.description,
                    required_skills=vacancy.required_skills or [],
                    context=vacancy.title.lower(),
                )

                all_results.append(
                    {
                        "resume_id": str(resume.id),
                        "filename": resume.filename,
                        "overall_score": match_result.overall_score,
                        "keyword_score": match_result.keyword_score,
                        "tfidf_score": match_result.tfidf_score,
                        "vector_score": match_result.vector_score,
                    }
                )

            except Exception as e:
                logger.warning(f"Error processing resume {resume.id}: {e}")
                continue

        if len(all_results) == 0:
            logger.warning("No valid results after matching")
            error_msg = get_error_message("matching_failed", locale)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "Failed to match resumes",
            )

        # Step 6: Sort by overall score (descending) and assign ranks
        all_results.sort(key=lambda x: x["overall_score"], reverse=True)
        for idx, result in enumerate(all_results, start=1):
            result["rank"] = idx

        # Step 7: Find target resume in results
        target_result = None
        for result in all_results:
            if result["resume_id"] == resume_id:
                target_result = result
                break

        if not target_result:
            logger.error(f"Target resume {resume_id} not found in results")
            error_msg = get_error_message("matching_failed", locale)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg or "Failed to match target resume",
            )

        # Step 8: Get top N candidates (excluding target if it's in top N)
        top_candidates_raw = []
        for result in all_results:
            if result["resume_id"] != resume_id:
                top_candidates_raw.append(result)
                if len(top_candidates_raw) >= request.limit:
                    break

        # Step 9: Build top candidates list
        top_candidates = [
            CandidateScore(
                resume_id=r["resume_id"],
                filename=r["filename"],
                overall_score=round(r["overall_score"], 3),
                keyword_score=round(r["keyword_score"], 3),
                tfidf_score=round(r["tfidf_score"], 3),
                vector_score=round(r["vector_score"], 3),
                rank=r["rank"],
            )
            for r in top_candidates_raw
        ]

        # Step 10: Calculate percentile and comparison metrics
        total_candidates = len(all_results)
        target_rank = target_result["rank"]
        worse_than_count = target_rank - 1
        better_than_count = total_candidates - target_rank

        # Percentile: higher is better (100 = best)
        percentile = round(((total_candidates - target_rank) / total_candidates) * 100, 1)

        # Generate recommendation
        recommendation = _generate_recommendation(target_rank, total_candidates, percentile)

        # Step 11: Build target resume score
        target_score = CandidateScore(
            resume_id=target_result["resume_id"],
            filename=target_result["filename"],
            overall_score=round(target_result["overall_score"], 3),
            keyword_score=round(target_result["keyword_score"], 3),
            tfidf_score=round(target_result["tfidf_score"], 3),
            vector_score=round(target_result["vector_score"], 3),
            rank=target_rank,
        )

        # Step 12: Build comparison result
        comparison = ComparisonResult(
            target_resume=target_score,
            top_candidates=top_candidates,
            percentile=percentile,
            better_than_count=better_than_count,
            worse_than_count=worse_than_count,
            recommendation=recommendation,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Step 13: Build response
        response_data = {
            "resume_id": resume_id,
            "vacancy_id": request.vacancy_id,
            "vacancy_title": vacancy.title,
            "comparison": comparison.model_dump(),
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Comparison completed: target_rank={target_rank}/{total_candidates}, "
            f"percentile={percentile}%, recommendation={recommendation}, "
            f"processing_time={processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in resume comparison: {e}", exc_info=True)
        error_msg = get_error_message("processing_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg or "Comparison processing failed",
        ) from e
