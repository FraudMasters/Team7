"""
Resume optimization endpoint.

This module provides the endpoint for generating AI-powered resume optimization
suggestions based on job requirements and best practices.
"""
import logging
import time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from analyzers.resume_optimizer import generate_resume_optimization, predict_ranking_improvement
from database import get_db
from i18n.backend_translations import get_error_message
from models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


class OptimizationRequest(BaseModel):
    """Request model for resume optimization."""

    target_job_description: Optional[str] = Field(
        None,
        description="Optional job description for targeted keyword matching"
    )
    check_keywords: bool = Field(True, description="Whether to perform keyword analysis")
    check_formatting: bool = Field(True, description="Whether to provide formatting recommendations")
    check_content: bool = Field(True, description="Whether to provide content improvement suggestions")
    include_ranking_prediction: bool = Field(
        False,
        description="Whether to include before/after ranking prediction (requires vacancy_id)"
    )
    vacancy_id: Optional[str] = Field(
        None,
        description="Optional vacancy ID for ranking prediction and comparison"
    )


class OptimizationSuggestion(BaseModel):
    """Individual optimization suggestion."""

    category: str = Field(..., description="Suggestion category (keywords, structure, readability, etc.)")
    severity: str = Field(..., description="Priority level (high, medium, low)")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed suggestion description")
    suggestion: str = Field(..., description="Recommendation for improvement")
    current_value: Optional[str] = Field(None, description="Current state")
    suggested_value: Optional[str] = Field(None, description="Suggested change")


class RankingPrediction(BaseModel):
    """Before/after ranking prediction for optimization impact."""

    before_score: Optional[float] = Field(None, description="Current ranking score (0-1)")
    after_score: Optional[float] = Field(None, description="Predicted ranking score after optimizations (0-1)")
    improvement_delta: Optional[float] = Field(None, description="Expected improvement in score")
    improvement_percentage: Optional[float] = Field(None, description="Expected improvement percentage")
    before_recommendation: Optional[str] = Field(None, description="Current recommendation category")
    after_recommendation: Optional[str] = Field(None, description="Predicted recommendation after optimizations")


class OptimizationResponse(BaseModel):
    """Response model for resume optimization."""

    resume_id: str
    status: str
    optimized_content: Optional[str] = None
    suggestions: list[OptimizationSuggestion] = []
    missing_keywords: list[str] = []
    formatting_recommendations: list[str] = []
    overall_score: int = 0
    ranking_prediction: Optional[RankingPrediction] = None
    processing_time_seconds: Optional[float] = None
    error: Optional[str] = None


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


def _convert_to_frontend_format(optimization_result: dict) -> list[OptimizationSuggestion]:
    """
    Convert internal optimizer format to frontend suggestion format.

    Args:
        optimization_result: Result from generate_resume_optimization

    Returns:
        List of OptimizationSuggestion objects
    """
    suggestions = []
    internal_suggestions = optimization_result.get("suggestions", [])

    for sugg in internal_suggestions:
        # Map category from internal format to frontend format
        category_map = {
            "keywords": "keyword",
            "structure": "formatting",
            "readability": "formatting",
            "impact": "content",
            "action_verbs": "content",
            "summary": "content",
            "active_language": "content",
            "achievements": "content",
        }

        internal_category = sugg.get("category", "keywords")
        frontend_category = category_map.get(internal_category, "content")

        suggestions.append(OptimizationSuggestion(
            category=frontend_category,
            severity=sugg.get("priority", "medium"),
            title=sugg.get("title", ""),
            description=sugg.get("description", ""),
            suggestion=sugg.get("recommendation", ""),
            current_value=sugg.get("current_state"),
            suggested_value=sugg.get("recommendation"),
        ))

    return suggestions


@router.post(
    "/{resume_id}/optimize",
    response_model=OptimizationResponse,
    tags=["Resumes"],
)
async def optimize_resume(
    request: Request,
    resume_id: str,
    optimization_request: OptimizationRequest = OptimizationRequest(),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Generate AI-powered optimization suggestions for a resume.

    This endpoint analyzes a resume and provides optimization suggestions including:
    - Keyword analysis and missing keywords
    - Formatting recommendations
    - Content improvement suggestions
    - Overall optimization score
    - Before/after ranking prediction (when vacancy_id is provided)

    Args:
        request: FastAPI request object (for Accept-Language header)
        resume_id: Resume ID to optimize
        optimization_request: Optional optimization parameters including:
            - target_job_description: Job description for targeted matching
            - check_keywords: Whether to perform keyword analysis
            - check_formatting: Whether to provide formatting recommendations
            - check_content: Whether to provide content suggestions
            - include_ranking_prediction: Whether to include ranking prediction
            - vacancy_id: Vacancy ID for ranking prediction (required if include_ranking_prediction=True)
        db: Database session

    Returns:
        JSON response with optimization results

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(500): If optimization analysis fails

    Examples:
        >>> import requests
        >>> # Basic optimization
        >>> response = requests.post("http://localhost:8000/api/resumes/abc123/optimize")
        >>> response.json()
        {
            "resume_id": "abc123",
            "status": "completed",
            "suggestions": [...],
            "missing_keywords": ["python", "django"],
            "overall_score": 75
        }

        >>> # With ranking prediction
        >>> response = requests.post(
        ...     "http://localhost:8000/api/resumes/abc123/optimize",
        ...     json={
        ...         "target_job_description": "Python developer",
        ...         "include_ranking_prediction": True,
        ...         "vacancy_id": "vacancy-123"
        ...     }
        ... )
        >>> response.json()
        {
            "resume_id": "abc123",
            "status": "completed",
            "suggestions": [...],
            "ranking_prediction": {
                "before_score": 0.65,
                "after_score": 0.82,
                "improvement_delta": 0.17,
                "improvement_percentage": 26.15
            }
        }
    """
    locale = _extract_locale(request)
    logger.info(f"Optimization request for resume_id: {resume_id}")
    start_time = time.time()

    try:
        # Validate resume_id is a valid UUID
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_resume_id", locale)
            raise HTTPException(status_code=400, detail=error_msg)

        # Query the resume from database
        result = await db.execute(
            select(Resume).where(Resume.id == resume_uuid)
        )
        resume = result.scalar_one_or_none()

        if not resume:
            error_msg = get_error_message("resume_not_found", locale)
            raise HTTPException(status_code=404, detail=error_msg)

        # Check if resume has raw_text for analysis
        if not resume.raw_text:
            logger.warning(f"Resume {resume_id} has no raw_text extracted")
            return JSONResponse(
                status_code=200,
                content={
                    "resume_id": resume_id,
                    "status": "failed",
                    "optimized_content": None,
                    "suggestions": [],
                    "missing_keywords": [],
                    "formatting_recommendations": [],
                    "overall_score": 0,
                    "processing_time_seconds": None,
                    "error": "Resume text not available for analysis",
                }
            )

        # Generate optimization suggestions
        optimization_result = generate_resume_optimization(
            resume_text=resume.raw_text,
            resume_data=None,
            target_job_description=optimization_request.target_job_description,
            check_keywords=optimization_request.check_keywords,
            check_formatting=optimization_request.check_formatting,
            check_content=optimization_request.check_content,
        )

        # Check for errors in optimization
        if optimization_result.get("error"):
            logger.error(f"Optimization failed for resume {resume_id}: {optimization_result['error']}")
            return JSONResponse(
                status_code=200,
                content={
                    "resume_id": resume_id,
                    "status": "failed",
                    "optimized_content": None,
                    "suggestions": [],
                    "missing_keywords": [],
                    "formatting_recommendations": [],
                    "overall_score": 0,
                    "processing_time_seconds": None,
                    "error": optimization_result["error"],
                }
            )

        # Convert to frontend format
        suggestions = _convert_to_frontend_format(optimization_result)
        missing_keywords = optimization_result.get("missing_keywords") or []

        # Generate ranking prediction if requested
        ranking_prediction_data = None
        if optimization_request.include_ranking_prediction and optimization_request.vacancy_id:
            try:
                # Call predict_ranking_improvement with resume text and vacancy_id
                ranking_improvement = predict_ranking_improvement(
                    resume_data=resume.raw_text,
                    vacancy_id=optimization_request.vacancy_id,
                    optimization_suggestions=optimization_result.get("suggestions", [])
                )

                # Format the ranking prediction for the response
                if ranking_improvement:
                    ranking_prediction_data = {
                        "before_score": ranking_improvement.get("before_score"),
                        "after_score": ranking_improvement.get("after_score"),
                        "improvement_delta": ranking_improvement.get("improvement_delta"),
                        "improvement_percentage": ranking_improvement.get("improvement_percentage"),
                        "before_recommendation": ranking_improvement.get("before_recommendation"),
                        "after_recommendation": ranking_improvement.get("after_recommendation"),
                    }
                    logger.info(
                        f"Ranking prediction generated for resume {resume_id}: "
                        f"before={ranking_improvement.get('before_score', 0):.2f}, "
                        f"after={ranking_improvement.get('after_score', 0):.2f}"
                    )
            except Exception as e:
                logger.warning(f"Failed to generate ranking prediction for resume {resume_id}: {e}")
                # Continue without ranking prediction - it's an optional feature

        processing_time = time.time() - start_time

        response_data = {
            "resume_id": resume_id,
            "status": "completed",
            "optimized_content": None,  # Not implemented yet
            "suggestions": [s.model_dump() for s in suggestions],
            "missing_keywords": missing_keywords,
            "formatting_recommendations": [
                s["suggestion"] for s in suggestions
                if s["category"] == "formatting"
            ],
            "overall_score": optimization_result.get("score", 0),
            "ranking_prediction": ranking_prediction_data,
            "processing_time_seconds": round(processing_time, 2),
            "error": None,
        }

        logger.info(
            f"Optimization completed for resume {resume_id}: "
            f"{len(suggestions)} suggestions, score {optimization_result.get('score', 0)}"
        )

        return JSONResponse(status_code=200, content=response_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing optimization for resume {resume_id}: {e}", exc_info=True)
        error_msg = get_error_message("optimization_failed", locale)
        raise HTTPException(status_code=500, detail=error_msg) from e
