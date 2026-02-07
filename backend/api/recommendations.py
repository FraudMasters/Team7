"""
AI-Powered Candidate Recommendations API endpoints

Provides endpoints for:
- Similar candidates recommendations based on embeddings
- Best fit candidates for vacancies
- Candidates at risk of loss
- Recommendation feedback submission
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
from analyzers.candidate_recommendation_service import (
    get_candidate_recommendation_service,
    CandidateRecommendationService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class SimilarCandidatesRequest(BaseModel):
    """Request to get similar candidates."""

    resume_id: str = Field(..., description="Resume UUID")
    limit: int = Field(10, ge=1, le=50, description="Maximum candidates to return")
    use_experiment: bool = Field(True, description="Include in A/B test experiment")


class SimilarCandidate(BaseModel):
    """A similar candidate recommendation."""

    resume_id: str = Field(..., description="Resume UUID")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    name: Optional[str] = Field(None, description="Candidate name")
    title: Optional[str] = Field(None, description="Current job title")
    shared_skills: List[str] = Field(..., description="Shared skills")
    match_reason: str = Field(..., description="Reason for similarity")
    recommendation_type: str = Field(..., description="Type of recommendation")


class SimilarCandidatesResponse(BaseModel):
    """Response with similar candidates."""

    source_resume_id: str = Field(..., description="Source resume UUID")
    total_candidates: int = Field(..., description="Total candidates found")
    candidates: List[SimilarCandidate] = Field(..., description="Similar candidates list")
    is_experiment: bool = Field(..., description="Part of A/B test")
    experiment_group: Optional[str] = Field(None, description="A/B test group")
    algorithm_version: str = Field(..., description="Algorithm version used")


class BestFitRequest(BaseModel):
    """Request to get best fit candidates for a vacancy."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    limit: int = Field(20, ge=1, le=100, description="Maximum candidates to return")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum match score")
    use_experiment: bool = Field(True, description="Include in A/B test experiment")


class BestFitCandidate(BaseModel):
    """A best fit candidate recommendation."""

    resume_id: str = Field(..., description="Resume UUID")
    match_score: float = Field(..., description="Overall match score (0-1)")
    name: Optional[str] = Field(None, description="Candidate name")
    title: Optional[str] = Field(None, description="Current job title")
    skills_match: List[str] = Field(..., description="Matched skills")
    missing_skills: List[str] = Field(..., description="Missing required skills")
    recommendation: str = Field(..., description="Hiring recommendation")
    years_experience: Optional[float] = Field(None, description="Years of experience")
    recommendation_type: str = Field(..., description="Type of recommendation")


class BestFitResponse(BaseModel):
    """Response with best fit candidates."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    total_candidates: int = Field(..., description="Total candidates found")
    candidates: List[BestFitCandidate] = Field(..., description="Best fit candidates list")
    is_experiment: bool = Field(..., description="Part of A/B test")
    experiment_group: Optional[str] = Field(None, description="A/B test group")
    algorithm_version: str = Field(..., description="Algorithm version used")


class AtRiskRequest(BaseModel):
    """Request to get candidates at risk of loss."""

    limit: int = Field(20, ge=1, le=100, description="Maximum candidates to return")
    min_risk_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum risk score")
    vacancy_id: Optional[str] = Field(None, description="Filter by vacancy UUID")
    use_experiment: bool = Field(True, description="Include in A/B test experiment")


class AtRiskCandidate(BaseModel):
    """A candidate at risk of loss."""

    resume_id: str = Field(..., description="Resume UUID")
    risk_score: float = Field(..., description="Risk score (0-1)")
    risk_level: str = Field(..., description="Risk level (low/medium/high)")
    name: Optional[str] = Field(None, description="Candidate name")
    title: Optional[str] = Field(None, description="Current job title")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    days_since_contact: Optional[int] = Field(None, description="Days since last contact")
    recommended_action: str = Field(..., description="Suggested action")
    recommendation_type: str = Field(..., description="Type of recommendation")


class AtRiskResponse(BaseModel):
    """Response with candidates at risk."""

    total_candidates: int = Field(..., description="Total candidates found")
    candidates: List[AtRiskCandidate] = Field(..., description="At-risk candidates list")
    is_experiment: bool = Field(..., description="Part of A/B test")
    experiment_group: Optional[str] = Field(None, description="A/B test group")
    algorithm_version: str = Field(..., description="Algorithm version used")


class RecommendationFeedbackRequest(BaseModel):
    """Request for recommendation feedback."""

    recommendation_id: str = Field(..., description="CandidateRecommendation UUID")
    was_helpful: bool = Field(..., description="Whether the recommendation was helpful")
    was_contacted: bool = Field(False, description="Whether user contacted the candidate")
    outcome: Optional[str] = Field(None, description="Outcome (hired/rejected/pending)")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating (1-5)")
    comments: Optional[str] = Field(None, description="Additional comments")


class RecommendationFeedbackPathRequest(BaseModel):
    """Request for recommendation feedback (with recommendation_id in path)."""

    was_helpful: bool = Field(..., description="Whether the recommendation was helpful")
    was_contacted: bool = Field(False, description="Whether user contacted the candidate")
    outcome: Optional[str] = Field(None, description="Outcome (hired/rejected/pending)")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating (1-5)")
    comments: Optional[str] = Field(None, description="Additional comments")


class RecommendationFeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    id: str = Field(..., description="Feedback UUID")
    recommendation_id: str = Field(..., description="CandidateRecommendation UUID")
    was_helpful: bool = Field(..., description="Whether recommendation was helpful")
    was_contacted: bool = Field(..., description="Whether candidate was contacted")
    outcome: Optional[str] = Field(None, description="Reported outcome")


@router.get(
    "/similar/{resume_id}",
    response_model=SimilarCandidatesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recommendations"],
)
async def get_similar_candidates_by_id(
    resume_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum candidates to return"),
    use_experiment: bool = Query(True, description="Include in A/B test experiment"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get similar candidates based on a reference candidate (GET endpoint).

    This endpoint uses vector embeddings and collaborative filtering
    to find candidates similar to a given candidate.

    The algorithm considers:
    - Skills similarity (keyword, TF-IDF, vector embeddings)
    - Experience overlap
    - Education similarity
    - Title similarity
    - Collaborative filtering (recruiters who viewed X also viewed Y)

    Args:
        resume_id: Resume UUID as path parameter
        limit: Maximum candidates to return (default: 10, max: 50)
        use_experiment: Include in A/B test experiment (default: True)
        db: Database session

    Returns:
        List of similar candidates with similarity scores and reasons

    Raises:
        HTTPException(404): If resume not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If recommendation fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/recommendations/similar/abc-123-def?limit=10&use_experiment=true"
        ... )
        >>> response.json()
        {
            "source_resume_id": "abc-123-def",
            "total_candidates": 10,
            "candidates": [
                {
                    "resume_id": "xyz-789-uvw",
                    "similarity_score": 0.85,
                    "name": "Jane Doe",
                    "title": "Software Engineer",
                    "shared_skills": ["Python", "FastAPI", "SQL"],
                    "match_reason": "Similar skill set and experience level",
                    "recommendation_type": "similar"
                }
            ],
            "is_experiment": true,
            "experiment_group": "treatment",
            "algorithm_version": "1.0.0"
        }
    """
    try:
        logger.info(f"Finding similar candidates for resume {resume_id}")

        # Parse UUID
        try:
            resume_uuid = UUID(resume_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Get similar candidates
        result = await service.get_similar_candidates(
            db,
            resume_uuid,
            limit=limit,
            use_experiment=use_experiment,
        )

        logger.info(f"Found {len(result.get('candidates', []))} similar candidates for {resume_id}")

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
        logger.error(f"Error finding similar candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar candidates: {str(e)}",
        )


@router.post(
    "/similar",
    response_model=SimilarCandidatesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recommendations"],
)
async def get_similar_candidates(
    request: SimilarCandidatesRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get similar candidates based on a reference candidate.

    This endpoint uses vector embeddings and collaborative filtering
    to find candidates similar to a given candidate.

    The algorithm considers:
    - Skills similarity (keyword, TF-IDF, vector embeddings)
    - Experience overlap
    - Education similarity
    - Title similarity
    - Collaborative filtering (recruiters who viewed X also viewed Y)

    Args:
        request: Similar candidates request with resume_id and limit
        db: Database session

    Returns:
        List of similar candidates with similarity scores and reasons

    Raises:
        HTTPException(404): If resume not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If recommendation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "limit": 10,
        ...     "use_experiment": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/recommendations/similar",
        ...     json=data
        ... )
        >>> response.json()
        {
            "source_resume_id": "abc-123-def",
            "total_candidates": 10,
            "candidates": [
                {
                    "resume_id": "xyz-789-uvw",
                    "similarity_score": 0.85,
                    "name": "Jane Doe",
                    "title": "Software Engineer",
                    "shared_skills": ["Python", "FastAPI", "SQL"],
                    "match_reason": "Similar skill set and experience level",
                    "recommendation_type": "similar"
                }
            ],
            "is_experiment": true,
            "experiment_group": "treatment",
            "algorithm_version": "1.0.0"
        }
    """
    try:
        logger.info(f"Finding similar candidates for resume {request.resume_id}")

        # Parse UUID
        try:
            resume_uuid = UUID(request.resume_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Get similar candidates
        result = await service.get_similar_candidates(
            db,
            resume_uuid,
            limit=request.limit,
            use_experiment=request.use_experiment,
        )

        logger.info(f"Found {len(result.get('candidates', []))} similar candidates for {request.resume_id}")

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
        logger.error(f"Error finding similar candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar candidates: {str(e)}",
        )


@router.post(
    "/best-fit",
    response_model=BestFitResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recommendations"],
)
async def get_best_fit_candidates(
    request: BestFitRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get best fit candidates for a vacancy.

    This endpoint uses ML ranking and collaborative filtering to find
    the best candidates for a specific vacancy.

    The algorithm considers:
    - Skills match (all three matching methods)
    - Experience relevance and duration
    - Education level
    - Title similarity
    - Previous successful placements
    - Resume freshness

    Args:
        request: Best fit request with vacancy_id, limit, and min_score
        db: Database session

    Returns:
        List of best fit candidates with match scores and details

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If recommendation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "vacancy_id": "vac-456-ghi",
        ...     "limit": 20,
        ...     "min_score": 0.6,
        ...     "use_experiment": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/recommendations/best-fit",
        ...     json=data
        ... )
        >>> response.json()
        {
            "vacancy_id": "vac-456-ghi",
            "total_candidates": 15,
            "candidates": [
                {
                    "resume_id": "abc-123-def",
                    "match_score": 0.87,
                    "name": "John Smith",
                    "title": "Senior Python Developer",
                    "skills_match": ["Python", "FastAPI", "PostgreSQL"],
                    "missing_skills": ["Kubernetes"],
                    "recommendation": "excellent",
                    "years_experience": 5.5,
                    "recommendation_type": "best_fit"
                }
            ],
            "is_experiment": true,
            "experiment_group": "treatment",
            "algorithm_version": "1.0.0"
        }
    """
    try:
        logger.info(f"Finding best fit candidates for vacancy {request.vacancy_id}")

        # Parse UUID
        try:
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Get best fit candidates
        result = await service.get_best_fit_candidates(
            db,
            vacancy_uuid,
            limit=request.limit,
            min_score=request.min_score,
            use_experiment=request.use_experiment,
        )

        logger.info(
            f"Found {len(result.get('candidates', []))} best fit candidates for vacancy {request.vacancy_id}"
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
        logger.error(f"Error finding best fit candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find best fit candidates: {str(e)}",
        )


@router.get(
    "/best-fit/{vacancy_id}",
    response_model=BestFitResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recommendations"],
)
async def get_best_fit_candidates_by_id(
    vacancy_id: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum candidates to return"),
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum match score"),
    use_experiment: bool = Query(True, description="Include in A/B test experiment"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get best fit candidates for a vacancy (GET endpoint).

    This endpoint uses ML ranking and collaborative filtering to find
    the best candidates for a specific vacancy.

    The algorithm considers:
    - Skills match (all three matching methods)
    - Experience relevance and duration
    - Education level
    - Title similarity
    - Previous successful placements
    - Resume freshness

    Args:
        vacancy_id: Vacancy UUID as path parameter
        limit: Maximum candidates to return (default: 20, max: 100)
        min_score: Minimum match score (default: 0.5, range: 0.0-1.0)
        use_experiment: Include in A/B test experiment (default: True)
        db: Database session

    Returns:
        List of best fit candidates with match scores and details

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If recommendation fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/recommendations/best-fit/vac-456-ghi?limit=20&min_score=0.6&use_experiment=true"
        ... )
        >>> response.json()
        {
            "vacancy_id": "vac-456-ghi",
            "total_candidates": 15,
            "candidates": [
                {
                    "resume_id": "abc-123-def",
                    "match_score": 0.87,
                    "name": "John Smith",
                    "title": "Senior Python Developer",
                    "skills_match": ["Python", "FastAPI", "PostgreSQL"],
                    "missing_skills": ["Kubernetes"],
                    "recommendation": "excellent",
                    "years_experience": 5.5,
                    "recommendation_type": "best_fit"
                }
            ],
            "is_experiment": true,
            "experiment_group": "treatment",
            "algorithm_version": "1.0.0"
        }
    """
    try:
        logger.info(f"Finding best fit candidates for vacancy {vacancy_id}")

        # Parse UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Get best fit candidates
        result = await service.get_best_fit_candidates(
            db,
            vacancy_uuid,
            limit=limit,
            min_score=min_score,
            use_experiment=use_experiment,
        )

        logger.info(
            f"Found {len(result.get('candidates', []))} best fit candidates for vacancy {vacancy_id}"
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
        logger.error(f"Error finding best fit candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find best fit candidates: {str(e)}",
        )


@router.post(
    "/at-risk",
    response_model=AtRiskResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recommendations"],
)
async def get_at_risk_candidates(
    request: AtRiskRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get candidates at risk of loss (likely to accept competing offers).

    This endpoint uses ML prediction to identify candidates who may be
    at risk of being lost to competitors or losing interest.

    Risk factors analyzed:
    - Days since last contact
    - Stage in hiring pipeline
    - Competitor activity (similar applications)
    - Engagement metrics
    - Market demand for candidate's skills
    - Time since resume update

    Args:
        request: At-risk request with limit, min_risk_score, and optional vacancy_id
        db: Database session

    Returns:
        List of at-risk candidates with risk scores and recommended actions

    Raises:
        HTTPException(422): If vacancy_id UUID format is invalid
        HTTPException(500): If prediction fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "limit": 20,
        ...     "min_risk_score": 0.6,
        ...     "vacancy_id": "vac-456-ghi",
        ...     "use_experiment": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/recommendations/at-risk",
        ...     json=data
        ... )
        >>> response.json()
        {
            "total_candidates": 8,
            "candidates": [
                {
                    "resume_id": "abc-123-def",
                    "risk_score": 0.78,
                    "risk_level": "high",
                    "name": "Jane Doe",
                    "title": "Software Engineer",
                    "risk_factors": [
                        "No contact in 14 days",
                        "Applied to 3 similar roles recently",
                        "High market demand for skills"
                    ],
                    "days_since_contact": 14,
                    "recommended_action": "Contact within 24 hours",
                    "recommendation_type": "at_risk"
                }
            ],
            "is_experiment": true,
            "experiment_group": "treatment",
            "algorithm_version": "1.0.0"
        }
    """
    try:
        logger.info(f"Finding at-risk candidates (min_risk={request.min_risk_score})")

        # Parse vacancy UUID if provided
        vacancy_uuid = None
        if request.vacancy_id:
            try:
                vacancy_uuid = UUID(request.vacancy_id)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid vacancy UUID format: {e}",
                )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Get at-risk candidates
        result = await service.get_at_risk_candidates(
            db,
            limit=request.limit,
            min_risk_score=request.min_risk_score,
            vacancy_id=vacancy_uuid,
            use_experiment=request.use_experiment,
        )

        logger.info(f"Found {len(result.get('candidates', []))} at-risk candidates")

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
        logger.error(f"Error finding at-risk candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find at-risk candidates: {str(e)}",
        )


@router.get(
    "/at-risk",
    response_model=AtRiskResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recommendations"],
)
async def get_at_risk_candidates_by_query(
    limit: int = Query(20, ge=1, le=100, description="Maximum candidates to return"),
    min_risk_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum risk score"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy UUID"),
    use_experiment: bool = Query(True, description="Include in A/B test experiment"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get candidates at risk of loss (GET endpoint).

    This endpoint uses ML prediction to identify candidates who may be
    at risk of being lost to competitors or losing interest.

    Risk factors analyzed:
    - Days since last contact
    - Stage in hiring pipeline
    - Competitor activity (similar applications)
    - Engagement metrics
    - Market demand for candidate's skills
    - Time since resume update

    Args:
        limit: Maximum candidates to return (default: 20, max: 100)
        min_risk_score: Minimum risk score threshold (default: 0.5, range: 0.0-1.0)
        vacancy_id: Optional vacancy UUID to filter candidates
        use_experiment: Include in A/B test experiment (default: True)
        db: Database session

    Returns:
        List of at-risk candidates with risk scores and recommended actions

    Raises:
        HTTPException(422): If vacancy_id UUID format is invalid
        HTTPException(500): If prediction fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/recommendations/at-risk?limit=20&min_risk_score=0.6&use_experiment=true"
        ... )
        >>> response.json()
        {
            "total_candidates": 8,
            "candidates": [
                {
                    "resume_id": "abc-123-def",
                    "risk_score": 0.78,
                    "risk_level": "high",
                    "name": "Jane Doe",
                    "title": "Software Engineer",
                    "risk_factors": [
                        "No contact in 14 days",
                        "Applied to 3 similar roles recently",
                        "High market demand for skills"
                    ],
                    "days_since_contact": 14,
                    "recommended_action": "Contact within 24 hours",
                    "recommendation_type": "at_risk"
                }
            ],
            "is_experiment": true,
            "experiment_group": "treatment",
            "algorithm_version": "1.0.0"
        }
    """
    try:
        logger.info(f"Finding at-risk candidates (min_risk={min_risk_score})")

        # Parse vacancy UUID if provided
        vacancy_uuid = None
        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid vacancy UUID format: {e}",
                )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Get at-risk candidates
        result = await service.get_at_risk_candidates(
            db,
            limit=limit,
            min_risk_score=min_risk_score,
            vacancy_id=vacancy_uuid,
            use_experiment=use_experiment,
        )

        logger.info(f"Found {len(result.get('candidates', []))} at-risk candidates")

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
        logger.error(f"Error finding at-risk candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find at-risk candidates: {str(e)}",
        )


@router.post(
    "/feedback",
    response_model=RecommendationFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Recommendations"],
)
async def submit_recommendation_feedback(
    request: RecommendationFeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Submit feedback on a recommendation.

    This endpoint allows recruiters to provide feedback on recommendations,
    which is used to continuously improve the recommendation algorithms.

    Feedback types:
    - was_helpful: Thumbs up/down on whether recommendation was useful
    - was_contacted: Whether user contacted the recommended candidate
    - outcome: What actually happened (hired, rejected, pending)
    - rating: 1-5 star rating
    - comments: Free-form feedback

    Args:
        request: Feedback request with recommendation_id and feedback data
        db: Database session

    Returns:
        Created feedback record

    Raises:
        HTTPException(404): If recommendation_id not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If feedback submission fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "recommendation_id": "rec-123-abc",
        ...     "was_helpful": True,
        ...     "was_contacted": True,
        ...     "outcome": "hired",
        ...     "rating": 5,
        ...     "comments": "Excellent recommendation, candidate was perfect fit"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/recommendations/feedback",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "fb-456-def",
            "recommendation_id": "rec-123-abc",
            "was_helpful": true,
            "was_contacted": true,
            "outcome": "hired"
        }
    """
    try:
        logger.info(f"Submitting feedback for recommendation {request.recommendation_id}")

        # Parse UUID
        try:
            recommendation_uuid = UUID(request.recommendation_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Submit feedback
        result = await service.submit_feedback(
            db,
            recommendation_uuid,
            was_helpful=request.was_helpful,
            was_contacted=request.was_contacted,
            outcome=request.outcome,
            rating=request.rating,
            comments=request.comments,
        )

        logger.info(f"Feedback submitted for recommendation {request.recommendation_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
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
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}",
        )


@router.post(
    "/{recommendation_id}/feedback",
    response_model=RecommendationFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Recommendations"],
)
async def submit_recommendation_feedback_by_id(
    recommendation_id: str,
    request: RecommendationFeedbackPathRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Submit feedback on a recommendation (with recommendation_id in path).

    This endpoint allows recruiters to provide feedback on recommendations,
    which is used to continuously improve the recommendation algorithms.

    Feedback types:
    - was_helpful: Thumbs up/down on whether recommendation was useful
    - was_contacted: Whether user contacted the recommended candidate
    - outcome: What actually happened (hired, rejected, pending)
    - rating: 1-5 star rating
    - comments: Free-form feedback

    Args:
        recommendation_id: CandidateRecommendation UUID as path parameter
        request: Feedback request with feedback data (no recommendation_id needed)
        db: Database session

    Returns:
        Created feedback record

    Raises:
        HTTPException(404): If recommendation_id not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If feedback submission fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "was_helpful": True,
        ...     "was_contacted": True,
        ...     "outcome": "hired",
        ...     "rating": 5,
        ...     "comments": "Excellent recommendation"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/recommendations/rec-123-abc/feedback",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "fb-456-def",
            "recommendation_id": "rec-123-abc",
            "was_helpful": true,
            "was_contacted": true,
            "outcome": "hired"
        }
    """
    try:
        logger.info(f"Submitting feedback for recommendation {recommendation_id}")

        # Parse UUID
        try:
            recommendation_uuid = UUID(recommendation_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Get recommendation service
        service = get_candidate_recommendation_service()

        # Submit feedback
        result = await service.submit_feedback(
            db,
            recommendation_uuid,
            was_helpful=request.was_helpful,
            was_contacted=request.was_contacted,
            outcome=request.outcome,
            rating=request.rating,
            comments=request.comments,
        )

        logger.info(f"Feedback submitted for recommendation {recommendation_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
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
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}",
        )


@router.get(
    "/types",
    tags=["Recommendations"],
)
async def get_recommendation_types() -> JSONResponse:
    """
    Get available recommendation types and their descriptions.

    Returns information about the different types of recommendations
    available in the system.

    Returns:
        List of recommendation types with descriptions
    """
    types = [
        {
            "type": "similar",
            "name": "Similar Candidates",
            "description": "Candidates similar to a given candidate based on skills, experience, and collaborative filtering",
            "endpoint": "/api/recommendations/similar",
        },
        {
            "type": "best_fit",
            "name": "Best Fit Candidates",
            "description": "Top-ranked candidates for a specific vacancy based on ML scoring",
            "endpoint": "/api/recommendations/best-fit",
        },
        {
            "type": "at_risk",
            "name": "Candidates at Risk",
            "description": "Candidates who may be lost to competitors or lose interest",
            "endpoint": "/api/recommendations/at-risk",
        },
    ]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"types": types},
    )
