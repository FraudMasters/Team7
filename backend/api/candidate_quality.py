"""
Candidate quality analytics endpoints.

This module provides endpoints for analyzing candidate quality trends,
correlating match rankings with hiring outcomes to help optimize
the recruitment process and improve matching algorithms.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


class RankingRangeMetrics(BaseModel):
    """Metrics for a specific ranking range."""

    range_label: str = Field(..., description="Range label (e.g., '80-100%')")
    range_min: float = Field(..., description="Minimum score in range (0-1)")
    range_max: float = Field(..., description="Maximum score in range (0-1)")
    candidate_count: int = Field(..., description="Number of candidates in this range")
    hired_count: int = Field(..., description="Number of candidates hired from this range")
    conversion_rate: float = Field(..., description="Conversion rate (hired/total) for this range (0-1)")


class CandidateQualityTrendsResponse(BaseModel):
    """Response model for candidate quality trends."""

    ranking_ranges: list[RankingRangeMetrics] = Field(
        ..., description="Metrics grouped by ranking ranges"
    )
    total_candidates: int = Field(..., description="Total candidates analyzed")
    overall_hire_rate: float = Field(..., description="Overall hire rate across all candidates (0-1)")


@router.get(
    "/candidate-quality-trends",
    response_model=CandidateQualityTrendsResponse,
    tags=["Analytics"],
)
async def get_candidate_quality_trends(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get candidate quality trends correlating match rankings with hiring outcomes.

    This endpoint analyzes how well the matching system predicts hiring success
    by grouping candidates into ranking ranges and calculating conversion rates
    for each range. This helps validate the effectiveness of the matching
    algorithm and identify optimal score thresholds for candidate screening.

    The endpoint groups candidates into five ranking ranges:
    - 0-20%: Poor match
    - 20-40%: Low match
    - 40-60%: Moderate match
    - 60-80%: Good match
    - 80-100%: Excellent match

    For each range, it calculates:
    - Total candidates in that range
    - Number of candidates hired from that range
    - Conversion rate (hired / total)

    This data helps answer questions like:
    - Do higher match scores correlate with better hiring outcomes?
    - What score threshold should we use for candidate screening?
    - Is our matching algorithm accurately predicting candidate quality?

    Args:
        start_date: Optional start date for filtering candidates (ISO 8601 format)
        end_date: Optional end date for filtering candidates (ISO 8601 format)

    Returns:
        JSON response with ranking ranges, hired counts, and conversion rates

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/candidate-quality-trends")
        >>> response.json()
        {
            "ranking_ranges": [
                {
                    "range_label": "80-100%",
                    "range_min": 0.8,
                    "range_max": 1.0,
                    "candidate_count": 150,
                    "hired_count": 45,
                    "conversion_rate": 0.3
                },
                {
                    "range_label": "60-80%",
                    "range_min": 0.6,
                    "range_max": 0.8,
                    "candidate_count": 200,
                    "hired_count": 40,
                    "conversion_rate": 0.2
                }
            ],
            "total_candidates": 1000,
            "overall_hire_rate": 0.15
        }
    """
    try:
        logger.info(
            f"Fetching candidate quality trends - start_date: {start_date}, end_date: {end_date}"
        )

        from datetime import datetime
        from collections import defaultdict
        from sqlalchemy import func

        from database import get_db
        from models import MatchResult, HiringStage

        # Define ranking ranges
        ranking_ranges = [
            {"range_label": "80-100%", "range_min": 0.8, "range_max": 1.0},
            {"range_label": "60-80%", "range_min": 0.6, "range_max": 0.8},
            {"range_label": "40-60%", "range_min": 0.4, "range_max": 0.6},
            {"range_label": "20-40%", "range_min": 0.2, "range_max": 0.4},
            {"range_label": "0-20%", "range_min": 0.0, "range_max": 0.2},
        ]

        # Initialize counters for each range
        range_metrics = defaultdict(lambda: {"candidate_count": 0, "hired_count": 0})

        async for db in get_db():
            # ==============================
            # GET ALL MATCH RESULTS
            # ==============================
            match_query = select(MatchResult)

            # Apply date filters if provided
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    match_query = match_query.where(MatchResult.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                    )

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    match_query = match_query.where(MatchResult.created_at <= end_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                    )

            match_result = await db.execute(match_query)
            all_matches = match_result.scalars().all()

            # Group matches by resume_id and get the best score for each resume
            resume_best_scores = {}  # resume_id -> best_score

            for match in all_matches:
                resume_id = str(match.resume_id)

                # Get the score - prefer overall_score, fall back to match_percentage
                if match.overall_score is not None:
                    score = float(match.overall_score)
                else:
                    score = float(match.match_percentage) / 100.0  # Convert to 0-1 scale

                # Keep the best (highest) score for each resume
                if resume_id not in resume_best_scores or score > resume_best_scores[resume_id]:
                    resume_best_scores[resume_id] = score

            # Count candidates in each ranking range
            for resume_id, score in resume_best_scores.items():
                # Find which range this score falls into
                for range_def in ranking_ranges:
                    if range_def["range_min"] <= score < range_def["range_max"]:
                        range_key = range_def["range_label"]
                        range_metrics[range_key]["candidate_count"] += 1
                        break
                else:
                    # Handle edge case where score == 1.0 (exact max)
                    if score == 1.0:
                        range_key = "80-100%"
                        range_metrics[range_key]["candidate_count"] += 1

            # ==============================
            # GET HIRED RESUMES
            # ==============================
            hired_query = select(HiringStage.resume_id).where(
                HiringStage.stage_name == "hired"
            )

            # Apply date filters if provided
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                hired_query = hired_query.where(HiringStage.created_at >= start_dt)

            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                hired_query = hired_query.where(HiringStage.created_at <= end_dt)

            hired_result = await db.execute(hired_query)
            hired_resume_ids = {str(row[0]) for row in hired_result}

            # Count hired candidates in each ranking range
            for resume_id in hired_resume_ids:
                if resume_id in resume_best_scores:
                    score = resume_best_scores[resume_id]

                    # Find which range this score falls into
                    for range_def in ranking_ranges:
                        if range_def["range_min"] <= score < range_def["range_max"]:
                            range_key = range_def["range_label"]
                            range_metrics[range_key]["hired_count"] += 1
                            break
                    else:
                        # Handle edge case where score == 1.0 (exact max)
                        if score == 1.0:
                            range_key = "80-100%"
                            range_metrics[range_key]["hired_count"] += 1

            break

        # Build the response with ranking ranges in order
        ranking_ranges_list = []
        total_candidates = len(resume_best_scores)
        total_hired = len(hired_resume_ids)

        for range_def in ranking_ranges:
            range_key = range_def["range_label"]
            metrics = range_metrics[range_key]

            candidate_count = metrics["candidate_count"]
            hired_count = metrics["hired_count"]

            # Calculate conversion rate
            if candidate_count > 0:
                conversion_rate = hired_count / candidate_count
            else:
                conversion_rate = 0.0

            ranking_ranges_list.append({
                "range_label": range_key,
                "range_min": range_def["range_min"],
                "range_max": range_def["range_max"],
                "candidate_count": candidate_count,
                "hired_count": hired_count,
                "conversion_rate": round(conversion_rate, 3),
            })

        # Calculate overall hire rate
        if total_candidates > 0:
            overall_hire_rate = total_hired / total_candidates
        else:
            overall_hire_rate = 0.0

        response_data = {
            "ranking_ranges": ranking_ranges_list,
            "total_candidates": total_candidates,
            "overall_hire_rate": round(overall_hire_rate, 3),
        }

        logger.info(
            f"Candidate quality trends retrieved successfully - {total_candidates} candidates, "
            f"{total_hired} hired, {len(ranking_ranges_list)} ranking ranges"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidate quality trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate quality trends: {str(e)}",
        ) from e
