"""
Candidates API endpoints for retrieving ranked candidates for vacancies.

Provides endpoints for:
- Getting candidates for a vacancy
- Retrieving ranked resumes for comparison
- Side-by-side candidate comparison data
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


# Response Models
class CandidateInfo(BaseModel):
    """Information about a single candidate."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    rank_score: float = Field(..., description="Overall ranking score (0-1)")
    rank_position: Optional[int] = Field(None, description="Position in ranked list")
    recommendation: str = Field(..., description="Hiring recommendation")
    confidence: float = Field(..., description="Model confidence (0-1)")
    feature_contributions: Dict[str, float] = Field(
        ..., description="Feature contribution scores"
    )
    ranking_factors: Dict[str, Any] = Field(..., description="Detailed factor scores")


class CandidatesListResponse(BaseModel):
    """Response with list of candidates for a vacancy."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    total_candidates: int = Field(..., description="Total number of candidates")
    candidates: List[Dict[str, Any]] = Field(..., description="List of ranked candidates")


@router.get(
    "/",
    tags=["Candidates"],
)
async def get_candidates_for_vacancy(
    vacancy_id: str = Query(..., description="Vacancy UUID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum candidates to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get candidates for a specific vacancy.

    Returns a list of candidates ranked by their match score for the
    specified vacancy, with detailed feature contributions and ranking factors.

    This endpoint leverages the AI-powered ranking service to provide
    intelligent candidate ordering based on multiple factors including:
    - Skills match (keyword, TF-IDF, vector similarity)
    - Experience relevance and duration
    - Education level
    - Title similarity
    - Resume freshness and completeness

    Args:
        vacancy_id: Vacancy UUID
        limit: Maximum number of candidates to return (default: 50, max: 200)
        db: Database session

    Returns:
        List of ranked candidates with detailed scoring information

    Raises:
        HTTPException(422): If vacancy_id is not a valid UUID
        HTTPException(404): If vacancy is not found
        HTTPException(500): If candidate retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/candidates",
        ...     params={"vacancy_id": "vac-456-ghi", "limit": 20}
        ... )
        >>> response.json()
        {
            "vacancy_id": "vac-456-ghi",
            "total_candidates": 20,
            "candidates": [
                {
                    "resume_id": "abc-123-def",
                    "vacancy_id": "vac-456-ghi",
                    "rank_score": 0.85,
                    "rank_position": 1,
                    "recommendation": "excellent",
                    "confidence": 0.88,
                    "feature_contributions": {...},
                    "ranking_factors": {...}
                },
                ...
            ]
        }
    """
    try:
        logger.info(f"Getting candidates for vacancy {vacancy_id}")

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

        # Get ranked candidates for the vacancy
        rankings = await ranking_service.rank_candidates_for_vacancy(
            db,
            vacancy_uuid,
            limit=limit,
        )

        logger.info(
            f"Returning {len(rankings)} candidates for vacancy {vacancy_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "vacancy_id": vacancy_id,
                "total_candidates": len(rankings),
                "candidates": rankings,
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting candidates for vacancy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidates: {str(e)}",
        )
