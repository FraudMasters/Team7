"""
Analytics and reporting endpoints.

This module provides endpoints for retrieving recruitment analytics metrics,
including time-to-hire statistics, resume processing metrics, match rates,
and other key performance indicators for the recruitment process.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> None:
    """
    Validate date range parameters.

    Args:
        start_date: Optional start date string in ISO 8601 format
        end_date: Optional end date string in ISO 8601 format

    Raises:
        HTTPException(422): If date format is invalid or start_date > end_date
    """
    if start_date is None and end_date is None:
        return

    parsed_start: Optional[datetime] = None
    parsed_end: Optional[datetime] = None

    # Validate start_date format
    if start_date is not None:
        try:
            parsed_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid start_date format: {start_date}. Expected ISO 8601 format (e.g., '2024-01-01' or '2024-01-01T00:00:00Z')",
            ) from e

    # Validate end_date format
    if end_date is not None:
        try:
            parsed_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid end_date format: {end_date}. Expected ISO 8601 format (e.g., '2024-12-31' or '2024-12-31T23:59:59Z')",
            ) from e

    # Validate date range logic
    if parsed_start is not None and parsed_end is not None:
        if parsed_start > parsed_end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"start_date ({start_date}) must be before or equal to end_date ({end_date})",
            )


class TimeToHireMetrics(BaseModel):
    """Time-to-hire performance metrics."""

    average_days: float = Field(..., description="Average time-to-hire in days")
    median_days: float = Field(..., description="Median time-to-hire in days")
    min_days: int = Field(..., description="Minimum time-to-hire in days")
    max_days: int = Field(..., description="Maximum time-to-hire in days")
    percentile_25: float = Field(..., description="25th percentile time-to-hire in days")
    percentile_75: float = Field(..., description="75th percentile time-to-hire in days")


class ResumeMetrics(BaseModel):
    """Resume processing metrics."""

    total_processed: int = Field(..., description="Total number of resumes processed")
    processed_this_month: int = Field(..., description="Resumes processed this month")
    processed_this_week: int = Field(..., description="Resumes processed this week")
    processing_rate_avg: float = Field(..., description="Average processing rate (resumes per day)")


class MatchRateMetrics(BaseModel):
    """Skill matching performance metrics."""

    overall_match_rate: float = Field(..., description="Overall skill match rate (0-1)")
    high_confidence_matches: int = Field(..., description="Number of high confidence matches (>0.8)")
    low_confidence_matches: int = Field(..., description="Number of low confidence matches (<0.5)")
    average_confidence: float = Field(..., description="Average confidence score across all matches (0-1)")


class KeyMetricsResponse(BaseModel):
    """Response model for key analytics metrics."""

    time_to_hire: TimeToHireMetrics = Field(..., description="Time-to-hire performance metrics")
    resumes: ResumeMetrics = Field(..., description="Resume processing metrics")
    match_rates: MatchRateMetrics = Field(..., description="Skill matching metrics")


class FunnelStage(BaseModel):
    """Represents a single stage in the recruitment funnel."""

    stage_name: str = Field(..., description="Name of the funnel stage")
    count: int = Field(..., description="Number of candidates/resumes at this stage")
    conversion_rate: float = Field(..., description="Conversion rate from previous stage (0-1)")


class FunnelMetricsResponse(BaseModel):
    """Response model for funnel visualization metrics."""

    stages: list[FunnelStage] = Field(..., description="List of funnel stages with counts and conversion rates")
    total_resumes: int = Field(..., description="Total number of resumes uploaded")
    overall_hire_rate: float = Field(..., description="Overall conversion rate from upload to hire (0-1)")


class SkillDemandItem(BaseModel):
    """Represents a single skill with its demand metrics."""

    skill_name: str = Field(..., description="Name of the skill")
    demand_count: int = Field(..., description="Number of job postings requesting this skill")
    demand_percentage: float = Field(..., description="Percentage of total job postings requesting this skill (0-1)")
    trend_percentage: float = Field(..., description="Trend percentage change from previous period (e.g., 0.15 for +15%)")


class SkillDemandResponse(BaseModel):
    """Response model for skill demand analytics."""

    skills: list[SkillDemandItem] = Field(..., description="List of skills with demand metrics, sorted by demand_count")
    total_postings_analyzed: int = Field(..., description="Total number of job postings analyzed")


class SourceTrackingItem(BaseModel):
    """Represents a single source with its vacancy metrics."""

    source_name: str = Field(..., description="Name of the vacancy source (e.g., 'LinkedIn', 'Referral', 'Indeed')")
    vacancy_count: int = Field(..., description="Number of vacancies from this source")
    percentage: float = Field(..., description="Percentage of total vacancies from this source (0-1)")
    average_time_to_fill: float = Field(..., description="Average time to fill (in days) for vacancies from this source")


class SourceTrackingResponse(BaseModel):
    """Response model for source tracking analytics."""

    sources: list[SourceTrackingItem] = Field(..., description="List of sources with vacancy metrics, sorted by vacancy_count")
    total_vacancies: int = Field(..., description="Total number of vacancies analyzed")


class RecruiterPerformanceItem(BaseModel):
    """Represents performance metrics for a single recruiter."""

    recruiter_id: str = Field(..., description="Unique identifier for the recruiter")
    recruiter_name: str = Field(..., description="Full name of the recruiter")
    hires: int = Field(..., description="Number of candidates hired")
    interviews_conducted: int = Field(..., description="Number of interviews conducted")
    resumes_processed: int = Field(..., description="Number of resumes processed")
    average_time_to_hire: float = Field(..., description="Average time-to-hire in days")
    offer_acceptance_rate: float = Field(..., description="Offer acceptance rate (0-1)")
    candidate_satisfaction_score: float = Field(..., description="Average candidate satisfaction score (0-5)")


class RecruiterPerformanceResponse(BaseModel):
    """Response model for recruiter performance comparison."""

    recruiters: list[RecruiterPerformanceItem] = Field(..., description="List of recruiters with performance metrics, sorted by hires")
    total_recruiters: int = Field(..., description="Total number of recruiters analyzed")
    period_start_date: str = Field(..., description="Start date of the analysis period (ISO 8601 format)")
    period_end_date: str = Field(..., description="End date of the analysis period (ISO 8601 format)")


@router.get(
    "/key-metrics",
    response_model=KeyMetricsResponse,
    tags=["Analytics"],
)
async def get_key_metrics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get key recruitment analytics metrics.

    This endpoint provides essential metrics for monitoring recruitment performance,
    including time-to-hire statistics, resume processing metrics, and skill match rates.
    These metrics help recruitment managers optimize their hiring process and identify
    areas for improvement.

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with key metrics including time-to-hire, resumes processed, and match rates

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/key-metrics")
        >>> response.json()
        {
            "time_to_hire": {
                "average_days": 32.5,
                "median_days": 28.0,
                "min_days": 7,
                "max_days": 90,
                "percentile_25": 21.0,
                "percentile_75": 45.0
            },
            "resumes": {
                "total_processed": 1250,
                "processed_this_month": 180,
                "processed_this_week": 42,
                "processing_rate_avg": 8.5
            },
            "match_rates": {
                "overall_match_rate": 0.78,
                "high_confidence_matches": 890,
                "low_confidence_matches": 156,
                "average_confidence": 0.72
            }
        }
    """
    try:
        # Validate date range parameters
        validate_date_range(start_date, end_date)

        logger.info(
            f"Fetching key metrics - start_date: {start_date}, end_date: {end_date}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        # Note: Date range filtering will be applied to database queries once integrated
        response_data = {
            "time_to_hire": {
                "average_days": 32.5,
                "median_days": 28.0,
                "min_days": 7,
                "max_days": 90,
                "percentile_25": 21.0,
                "percentile_75": 45.0,
            },
            "resumes": {
                "total_processed": 1250,
                "processed_this_month": 180,
                "processed_this_week": 42,
                "processing_rate_avg": 8.5,
            },
            "match_rates": {
                "overall_match_rate": 0.78,
                "high_confidence_matches": 890,
                "low_confidence_matches": 156,
                "average_confidence": 0.72,
            },
        }

        logger.info("Key metrics retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving key metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve key metrics: {str(e)}",
        ) from e


@router.get(
    "/funnel",
    response_model=FunnelMetricsResponse,
    tags=["Analytics"],
)
async def get_funnel_metrics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get recruitment funnel visualization metrics.

    This endpoint provides a comprehensive view of the recruitment pipeline,
    tracking candidate progression from resume upload through to hiring.
    Each stage includes counts and conversion rates, enabling visualization
    of drop-off points and pipeline efficiency.

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with funnel stages, counts, conversion rates, and overall hire rate

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/funnel")
        >>> response.json()
        {
            "stages": [
                {
                    "stage_name": "resumes_uploaded",
                    "count": 1000,
                    "conversion_rate": 1.0
                },
                {
                    "stage_name": "resumes_processed",
                    "count": 950,
                    "conversion_rate": 0.95
                },
                {
                    "stage_name": "candidates_matched",
                    "count": 720,
                    "conversion_rate": 0.758
                },
                {
                    "stage_name": "candidates_shortlisted",
                    "count": 360,
                    "conversion_rate": 0.5
                },
                {
                    "stage_name": "candidates_interviewed",
                    "count": 180,
                    "conversion_rate": 0.5
                },
                {
                    "stage_name": "candidates_hired",
                    "count": 45,
                    "conversion_rate": 0.25
                }
            ],
            "total_resumes": 1000,
            "overall_hire_rate": 0.045
        }
    """
    try:
        # Validate date range parameters
        validate_date_range(start_date, end_date)

        logger.info(
            f"Fetching funnel metrics - start_date: {start_date}, end_date: {end_date}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        # These numbers represent a typical recruitment funnel with realistic conversion rates
        # Note: Date range filtering will be applied to database queries once integrated
        response_data = {
            "stages": [
                {
                    "stage_name": "resumes_uploaded",
                    "count": 1000,
                    "conversion_rate": 1.0,
                },
                {
                    "stage_name": "resumes_processed",
                    "count": 950,
                    "conversion_rate": 0.95,
                },
                {
                    "stage_name": "candidates_matched",
                    "count": 720,
                    "conversion_rate": 0.758,
                },
                {
                    "stage_name": "candidates_shortlisted",
                    "count": 360,
                    "conversion_rate": 0.5,
                },
                {
                    "stage_name": "candidates_interviewed",
                    "count": 180,
                    "conversion_rate": 0.5,
                },
                {
                    "stage_name": "candidates_hired",
                    "count": 45,
                    "conversion_rate": 0.25,
                },
            ],
            "total_resumes": 1000,
            "overall_hire_rate": 0.045,
        }

        logger.info("Funnel metrics retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving funnel metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve funnel metrics: {str(e)}",
        ) from e


@router.get(
    "/skill-demand",
    response_model=SkillDemandResponse,
    tags=["Analytics"],
)
async def get_skill_demand(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of skills to return"),
) -> JSONResponse:
    """
    Get skill demand analytics aggregating most requested skills.

    This endpoint provides insights into the most in-demand skills in the job market,
    aggregating data from job postings to identify trending skills. Each skill includes
    demand count, percentage of total postings, and trend information to help recruitment
    teams and job seekers understand market demands.

    Args:
        start_date: Optional start date for filtering job postings (ISO 8601 format)
        end_date: Optional end date for filtering job postings (ISO 8601 format)
        limit: Maximum number of skills to return (default: 20, range: 1-100)

    Returns:
        JSON response with list of skills sorted by demand count, including demand metrics

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/skill-demand?limit=10")
        >>> response.json()
        {
            "skills": [
                {
                    "skill_name": "Python",
                    "demand_count": 245,
                    "demand_percentage": 0.425,
                    "trend_percentage": 0.18
                },
                {
                    "skill_name": "JavaScript",
                    "demand_count": 198,
                    "demand_percentage": 0.344,
                    "trend_percentage": 0.12
                },
                {
                    "skill_name": "React",
                    "demand_count": 176,
                    "demand_percentage": 0.305,
                    "trend_percentage": 0.22
                }
            ],
            "total_postings_analyzed": 576
        }
    """
    try:
        # Validate date range parameters
        validate_date_range(start_date, end_date)

        logger.info(
            f"Fetching skill demand - start_date: {start_date}, end_date: {end_date}, limit: {limit}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        # These represent typical in-demand tech skills with realistic metrics
        # Note: Date range filtering will be applied to database queries once integrated
        response_data = {
            "skills": [
                {
                    "skill_name": "Python",
                    "demand_count": 245,
                    "demand_percentage": 0.425,
                    "trend_percentage": 0.18,
                },
                {
                    "skill_name": "JavaScript",
                    "demand_count": 198,
                    "demand_percentage": 0.344,
                    "trend_percentage": 0.12,
                },
                {
                    "skill_name": "React",
                    "demand_count": 176,
                    "demand_percentage": 0.305,
                    "trend_percentage": 0.22,
                },
                {
                    "skill_name": "SQL",
                    "demand_count": 154,
                    "demand_percentage": 0.267,
                    "trend_percentage": 0.08,
                },
                {
                    "skill_name": "AWS",
                    "demand_count": 142,
                    "demand_percentage": 0.246,
                    "trend_percentage": 0.25,
                },
                {
                    "skill_name": "Docker",
                    "demand_count": 128,
                    "demand_percentage": 0.222,
                    "trend_percentage": 0.19,
                },
                {
                    "skill_name": "Kubernetes",
                    "demand_count": 115,
                    "demand_percentage": 0.199,
                    "trend_percentage": 0.28,
                },
                {
                    "skill_name": "TypeScript",
                    "demand_count": 108,
                    "demand_percentage": 0.187,
                    "trend_percentage": 0.31,
                },
                {
                    "skill_name": "Node.js",
                    "demand_count": 98,
                    "demand_percentage": 0.170,
                    "trend_percentage": 0.14,
                },
                {
                    "skill_name": "Machine Learning",
                    "demand_count": 87,
                    "demand_percentage": 0.151,
                    "trend_percentage": 0.35,
                },
            ][:limit],
            "total_postings_analyzed": 576,
        }

        logger.info("Skill demand data retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving skill demand: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve skill demand: {str(e)}",
        ) from e


@router.get(
    "/source-tracking",
    response_model=SourceTrackingResponse,
    tags=["Analytics"],
)
async def get_source_tracking(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get source tracking analytics aggregating vacancies by source.

    This endpoint provides insights into vacancy distribution across different sources,
    such as job boards, referrals, and recruitment agencies. Each source includes
    vacancy count, percentage distribution, and average time-to-fill metrics to help
    recruitment teams optimize their sourcing strategy and allocate resources effectively.

    Args:
        start_date: Optional start date for filtering vacancies (ISO 8601 format)
        end_date: Optional end date for filtering vacancies (ISO 8601 format)

    Returns:
        JSON response with list of sources sorted by vacancy count, including distribution and performance metrics

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/source-tracking")
        >>> response.json()
        {
            "sources": [
                {
                    "source_name": "LinkedIn",
                    "vacancy_count": 156,
                    "percentage": 0.312,
                    "average_time_to_fill": 28.5
                },
                {
                    "source_name": "Indeed",
                    "vacancy_count": 98,
                    "percentage": 0.196,
                    "average_time_to_fill": 32.0
                },
                {
                    "source_name": "Referral",
                    "vacancy_count": 87,
                    "percentage": 0.174,
                    "average_time_to_fill": 21.0
                },
                {
                    "source_name": "Company Website",
                    "vacancy_count": 72,
                    "percentage": 0.144,
                    "average_time_to_fill": 35.5
                },
                {
                    "source_name": "Recruitment Agency",
                    "vacancy_count": 54,
                    "percentage": 0.108,
                    "average_time_to_fill": 24.0
                },
                {
                    "source_name": "Other",
                    "vacancy_count": 33,
                    "percentage": 0.066,
                    "average_time_to_fill": 38.0
                }
            ],
            "total_vacancies": 500
        }
    """
    try:
        # Validate date range parameters
        validate_date_range(start_date, end_date)

        logger.info(
            f"Fetching source tracking - start_date: {start_date}, end_date: {end_date}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        # These represent typical vacancy sources with realistic distribution and time-to-fill metrics
        # Note: Date range filtering will be applied to database queries once integrated
        response_data = {
            "sources": [
                {
                    "source_name": "LinkedIn",
                    "vacancy_count": 156,
                    "percentage": 0.312,
                    "average_time_to_fill": 28.5,
                },
                {
                    "source_name": "Indeed",
                    "vacancy_count": 98,
                    "percentage": 0.196,
                    "average_time_to_fill": 32.0,
                },
                {
                    "source_name": "Referral",
                    "vacancy_count": 87,
                    "percentage": 0.174,
                    "average_time_to_fill": 21.0,
                },
                {
                    "source_name": "Company Website",
                    "vacancy_count": 72,
                    "percentage": 0.144,
                    "average_time_to_fill": 35.5,
                },
                {
                    "source_name": "Recruitment Agency",
                    "vacancy_count": 54,
                    "percentage": 0.108,
                    "average_time_to_fill": 24.0,
                },
                {
                    "source_name": "Other",
                    "vacancy_count": 33,
                    "percentage": 0.066,
                    "average_time_to_fill": 38.0,
                },
            ],
            "total_vacancies": 500,
        }

        logger.info("Source tracking data retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving source tracking: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve source tracking: {str(e)}",
        ) from e


@router.get(
    "/recruiter-performance",
    response_model=RecruiterPerformanceResponse,
    tags=["Analytics"],
)
async def get_recruiter_performance(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recruiters to return"),
) -> JSONResponse:
    """
    Get recruiter performance comparison metrics.

    This endpoint provides comparative performance metrics for recruiters,
    enabling managers to identify top performers, best practices, and areas
    for improvement. Metrics include hires, interviews conducted, resumes
    processed, time-to-hire averages, offer acceptance rates, and candidate
    satisfaction scores.

    Args:
        start_date: Optional start date for filtering performance data (ISO 8601 format)
        end_date: Optional end date for filtering performance data (ISO 8601 format)
        limit: Maximum number of recruiters to return (default: 20, range: 1-100)

    Returns:
        JSON response with list of recruiters sorted by number of hires, including performance metrics

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/recruiter-performance?limit=5")
        >>> response.json()
        {
            "recruiters": [
                {
                    "recruiter_id": "REC001",
                    "recruiter_name": "Sarah Johnson",
                    "hires": 24,
                    "interviews_conducted": 87,
                    "resumes_processed": 342,
                    "average_time_to_hire": 28.5,
                    "offer_acceptance_rate": 0.92,
                    "candidate_satisfaction_score": 4.7
                },
                {
                    "recruiter_id": "REC002",
                    "recruiter_name": "Michael Chen",
                    "hires": 19,
                    "interviews_conducted": 72,
                    "resumes_processed": 298,
                    "average_time_to_hire": 31.2,
                    "offer_acceptance_rate": 0.89,
                    "candidate_satisfaction_score": 4.5
                }
            ],
            "total_recruiters": 12,
            "period_start_date": "2024-01-01T00:00:00Z",
            "period_end_date": "2024-12-31T23:59:59Z"
        }
    """
    try:
        # Validate date range parameters
        validate_date_range(start_date, end_date)

        logger.info(
            f"Fetching recruiter performance - start_date: {start_date}, end_date: {end_date}, limit: {limit}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        # These represent typical recruiter performance metrics with realistic variations
        # Note: Date range filtering will be applied to database queries once integrated
        response_data = {
            "recruiters": [
                {
                    "recruiter_id": "REC001",
                    "recruiter_name": "Sarah Johnson",
                    "hires": 24,
                    "interviews_conducted": 87,
                    "resumes_processed": 342,
                    "average_time_to_hire": 28.5,
                    "offer_acceptance_rate": 0.92,
                    "candidate_satisfaction_score": 4.7,
                },
                {
                    "recruiter_id": "REC002",
                    "recruiter_name": "Michael Chen",
                    "hires": 19,
                    "interviews_conducted": 72,
                    "resumes_processed": 298,
                    "average_time_to_hire": 31.2,
                    "offer_acceptance_rate": 0.89,
                    "candidate_satisfaction_score": 4.5,
                },
                {
                    "recruiter_id": "REC003",
                    "recruiter_name": "Emily Rodriguez",
                    "hires": 18,
                    "interviews_conducted": 68,
                    "resumes_processed": 276,
                    "average_time_to_hire": 29.8,
                    "offer_acceptance_rate": 0.94,
                    "candidate_satisfaction_score": 4.8,
                },
                {
                    "recruiter_id": "REC004",
                    "recruiter_name": "David Kim",
                    "hires": 15,
                    "interviews_conducted": 54,
                    "resumes_processed": 234,
                    "average_time_to_hire": 33.7,
                    "offer_acceptance_rate": 0.87,
                    "candidate_satisfaction_score": 4.3,
                },
                {
                    "recruiter_id": "REC005",
                    "recruiter_name": "Jessica Martinez",
                    "hires": 14,
                    "interviews_conducted": 61,
                    "resumes_processed": 289,
                    "average_time_to_hire": 30.4,
                    "offer_acceptance_rate": 0.91,
                    "candidate_satisfaction_score": 4.6,
                },
                {
                    "recruiter_id": "REC006",
                    "recruiter_name": "Robert Thompson",
                    "hires": 12,
                    "interviews_conducted": 48,
                    "resumes_processed": 198,
                    "average_time_to_hire": 35.1,
                    "offer_acceptance_rate": 0.85,
                    "candidate_satisfaction_score": 4.2,
                },
                {
                    "recruiter_id": "REC007",
                    "recruiter_name": "Amanda Foster",
                    "hires": 11,
                    "interviews_conducted": 52,
                    "resumes_processed": 215,
                    "average_time_to_hire": 32.6,
                    "offer_acceptance_rate": 0.88,
                    "candidate_satisfaction_score": 4.4,
                },
                {
                    "recruiter_id": "REC008",
                    "recruiter_name": "Christopher Lee",
                    "hires": 10,
                    "interviews_conducted": 43,
                    "resumes_processed": 187,
                    "average_time_to_hire": 34.8,
                    "offer_acceptance_rate": 0.86,
                    "candidate_satisfaction_score": 4.1,
                },
                {
                    "recruiter_id": "REC009",
                    "recruiter_name": "Rachel Green",
                    "hires": 9,
                    "interviews_conducted": 39,
                    "resumes_processed": 165,
                    "average_time_to_hire": 37.2,
                    "offer_acceptance_rate": 0.83,
                    "candidate_satisfaction_score": 4.0,
                },
                {
                    "recruiter_id": "REC010",
                    "recruiter_name": "James Wilson",
                    "hires": 8,
                    "interviews_conducted": 35,
                    "resumes_processed": 143,
                    "average_time_to_hire": 36.5,
                    "offer_acceptance_rate": 0.84,
                    "candidate_satisfaction_score": 4.2,
                },
            ][:limit],
            "total_recruiters": 10,
            "period_start_date": "2024-01-01T00:00:00Z",
            "period_end_date": "2024-12-31T23:59:59Z",
        }

        logger.info("Recruiter performance data retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving recruiter performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recruiter performance: {str(e)}",
        ) from e
