"""
AI-powered Candidate Ranking API endpoints

Provides endpoints for:
- Ranking candidates for vacancies
- Getting ranked candidate lists
- Submitting feedback on rankings
- A/B testing management
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from analyzers.ranking_service import get_ranking_service, RankingService

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class RankCandidateRequest(BaseModel):
    """Request to rank a candidate for a vacancy."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    use_experiment: bool = Field(True, description="Include in A/B test experiment")


class RankingResponse(BaseModel):
    """Response from candidate ranking."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    rank_score: float = Field(..., description="Overall ranking score (0-1)")
    rank_position: Optional[int] = Field(None, description="Position in ranked list")
    recommendation: str = Field(..., description="Hiring recommendation")
    confidence: float = Field(..., description="Model confidence (0-1)")
    is_experiment: bool = Field(..., description="Part of A/B test")
    experiment_group: Optional[str] = Field(None, description="A/B test group")
    model_version: str = Field(..., description="Model version used")
    feature_contributions: Dict[str, float] = Field(..., description="Feature contribution scores")
    ranking_factors: Dict[str, Any] = Field(..., description="Detailed factor scores")


class FeedbackRequest(BaseModel):
    """Request for ranking feedback."""

    rank_id: str = Field(..., description="CandidateRank UUID")
    was_helpful: bool = Field(..., description="Whether the ranking was helpful")
    actual_outcome: Optional[str] = Field(None, description="Actual outcome (hired/rejected/pending)")
    adjusted_score: Optional[float] = Field(None, description="Recruiter's adjusted score")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating (1-5)")
    comments: Optional[str] = Field(None, description="Additional comments")


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    id: str = Field(..., description="Feedback UUID")
    rank_id: str = Field(..., description="CandidateRank UUID")
    was_helpful: bool = Field(..., description="Whether ranking was helpful")
    actual_outcome: Optional[str] = Field(None, description="Actual outcome")


class RankedCandidatesRequest(BaseModel):
    """Request to get ranked candidates for a vacancy."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    limit: int = Field(50, ge=1, le=200, description="Maximum candidates to return")
    include_experiments: bool = Field(True, description="Include A/B test candidates")


@router.post(
    "/rank",
    response_model=RankingResponse,
    status_code=status.HTTP_200_OK,
    tags=["Ranking"],
)
async def rank_candidate(
    request: RankCandidateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Rank a candidate for a specific vacancy using ML models.

    This endpoint uses machine learning to score how well a candidate
    matches a vacancy based on multiple factors including skills,
    experience, education, and semantic similarity.

    The ranking considers:
    - Skills match (keyword, TF-IDF, vector similarity)
    - Experience relevance and duration
    - Education level
    - Title similarity
    - Resume freshness and completeness

    Args:
        request: Ranking request with resume_id and vacancy_id
        db: Database session

    Returns:
        Ranking result with score, recommendation, and feature contributions

    Raises:
        HTTPException(404): If resume or vacancy not found
        HTTPException(500): If ranking fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "vacancy_id": "vac-456-ghi",
        ...     "use_experiment": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/ranking/rank",
        ...     json=data
        ... )
        >>> response.json()
        {
            "resume_id": "abc-123-def",
            "vacancy_id": "vac-456-ghi",
            "rank_score": 0.78,
            "recommendation": "good",
            "confidence": 0.85,
            "is_experiment": true,
            "experiment_group": "treatment",
            "model_version": "1.0.0",
            ...
        }
    """
    try:
        logger.info(f"Ranking candidate {request.resume_id} for vacancy {request.vacancy_id}")

        # Parse UUIDs
        try:
            resume_uuid = UUID(request.resume_id)
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get ranking service
        ranking_service = get_ranking_service()

        # Rank the candidate
        result = await ranking_service.rank_candidate(
            db,
            resume_uuid,
            vacancy_uuid,
            use_experiment=request.use_experiment,
        )

        logger.info(
            f"Ranked candidate {request.resume_id}: score={result['rank_score']:.2f}, "
            f"recommendation={result['recommendation']}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error ranking candidate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ranking failed: {str(e)}",
        )


@router.get(
    "/vacancy/{vacancy_id}/ranked",
    tags=["Ranking"],
)
async def get_ranked_candidates(
    vacancy_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum candidates to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get ranked list of candidates for a vacancy.

    Returns a list of candidates ranked by their match score for the
    specified vacancy, with detailed feature contributions.

    Args:
        vacancy_id: Vacancy UUID
        limit: Maximum number of candidates to return
        db: Database session

    Returns:
        List of ranked candidates

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(500): If ranking fails
    """
    try:
        logger.info(f"Getting ranked candidates for vacancy {vacancy_id}")

        # Parse UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid vacancy UUID format",
            )

        # Get ranking service
        ranking_service = get_ranking_service()

        # Get ranked candidates
        rankings = await ranking_service.rank_candidates_for_vacancy(
            db,
            vacancy_uuid,
            limit=limit,
        )

        logger.info(f"Returning {len(rankings)} ranked candidates for vacancy {vacancy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "vacancy_id": vacancy_id,
                "total_candidates": len(rankings),
                "rankings": rankings,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ranked candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rankings: {str(e)}",
        )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ranking"],
)
async def submit_ranking_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Submit feedback on an AI ranking.

    This endpoint allows recruiters to provide feedback on ranking
    predictions, which is used to continuously improve the ML models.

    Feedback types:
    - was_helpful: Thumbs up/down on whether ranking was useful
    - actual_outcome: What actually happened (hired, rejected, etc.)
    - adjusted_score: If recruiter disagreed with the score
    - rating: 1-5 star rating
    - comments: Free-form feedback

    Args:
        request: Feedback request with rank_id and feedback data
        db: Database session

    Returns:
        Created feedback record

    Raises:
        HTTPException(404): If rank_id not found
        HTTPException(500): If feedback submission fails
    """
    try:
        logger.info(f"Submitting feedback for rank {request.rank_id}")

        # Parse UUID
        try:
            rank_uuid = UUID(request.rank_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid rank UUID format",
            )

        # Get ranking service
        ranking_service = get_ranking_service()

        # Submit feedback
        result = await ranking_service.submit_feedback(
            db,
            rank_uuid,
            was_helpful=request.was_helpful,
            actual_outcome=request.actual_outcome,
            adjusted_score=request.adjusted_score,
            comments=request.comments,
        )

        logger.info(f"Feedback submitted for rank {request.rank_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}",
        )


@router.get(
    "/models/features",
    tags=["Ranking"],
)
async def get_ranking_features() -> JSONResponse:
    """
    Get list of features used in ranking model.

    Returns information about the features that the ML model
    uses to rank candidates.

    Returns:
        Feature list with descriptions
    """
    from analyzers.ranking_service import RankingFeatures

    features = [
        {
            "name": name,
            "description": _get_feature_description(name),
        }
        for name in RankingFeatures.FEATURE_NAMES
    ]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"features": features},
    )


@router.get(
    "/models/importance",
    tags=["Ranking"],
)
async def get_feature_importance() -> JSONResponse:
    """
    Get feature importance from trained model.

    Returns the relative importance of each feature in the
    ranking model's predictions.

    Returns:
        Feature importance scores
    """
    ranking_service = get_ranking_service()
    importance = ranking_service.model.get_feature_importance()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "model_type": ranking_service.model.model_type,
            "model_version": ranking_service.model.version,
            "is_trained": ranking_service.model.is_trained,
            "feature_importance": importance,
        },
    )


@router.post(
    "/models/train",
    tags=["Ranking"],
)
async def train_ranking_model(
    model_type: str = Query("random_forest", description="Model type to train"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Train or retrain the ranking model.

    This endpoint retrains the ML model on current data.
    Use after collecting sufficient feedback data.

    Args:
        model_type: Type of model (random_forest or gradient_boosting)
        db: Database session

    Returns:
        Training metrics
    """
    try:
        logger.info(f"Training {model_type} ranking model")

        # For now, return a placeholder response
        # Actual training would require collected feedback data
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Model training requires historical feedback data",
                "model_type": model_type,
                "note": "Training will be implemented after collecting feedback",
            },
        )

    except Exception as e:
        logger.error(f"Error training model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}",
        )


def _get_feature_description(feature_name: str) -> str:
    """Get human-readable description for a feature."""
    descriptions = {
        "overall_match_score": "Combined match score from all matching methods",
        "keyword_score": "Keyword-based skill matching score",
        "tfidf_score": "TF-IDF weighted skill matching score",
        "vector_score": "Semantic similarity score from sentence transformers",
        "skills_match_ratio": "Ratio of required skills found in resume",
        "experience_months": "Total months of work experience",
        "experience_relevance": "How well experience matches job requirements",
        "education_level": "Highest education level achieved",
        "recent_experience": "Relevant experience in recent years",
        "skill_rarity_score": "Rarity of matched skills (rarer = higher score)",
        "title_similarity": "Similarity between resume and job titles",
        "freshness_score": "How recent the resume is (decays over time)",
        "completeness_score": "How complete the resume profile is",
    }
    return descriptions.get(feature_name, "Feature description not available")
