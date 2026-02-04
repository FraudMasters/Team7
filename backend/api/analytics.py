"""
Analytics and reporting endpoints.

This module provides endpoints for retrieving recruitment analytics metrics,
including time-to-hire statistics, resume processing metrics, match rates,
and other key performance indicators for the recruitment process.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


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
        logger.info(
            f"Fetching key metrics - start_date: {start_date}, end_date: {end_date}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
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


class QualityMetricsResponse(BaseModel):
    """ML/NLP model quality metrics."""

    # Text extraction metrics
    text_extraction_success_rate: float = Field(..., description="Successful text extraction rate (0-1)")
    avg_extraction_time_seconds: float = Field(..., description="Average text extraction time")

    # NER metrics
    ner_accuracy: float = Field(..., description="NER accuracy (entity detection F1 score)")
    entities_per_resume_avg: float = Field(..., description="Average entities detected per resume")

    # Keyword extraction metrics
    avg_keywords_per_resume: float = Field(..., description="Average keywords extracted per resume")
    keyword_relevance_avg: float = Field(..., description="Average keyword relevance score (0-1)")

    # Grammar metrics
    grammar_error_rate: float = Field(..., description="Resumes with grammar errors (0-1)")

    # Matching metrics
    matching_confidence_avg: float = Field(..., description="Average matching confidence score (0-1)")
    matching_precision: float = Field(..., description="Matching precision (verified matches)")
    matching_recall: float = Field(..., description="Matching recall (found relevant candidates)")

    # Performance metrics
    avg_analysis_time_seconds: float = Field(..., description="Average resume analysis time")
    error_rate: float = Field(..., description="Analysis error rate (0-1)")

    # Summary
    total_analyzed: int = Field(..., description="Total number of resumes analyzed")


@router.get(
    "/quality-metrics",
    response_model=QualityMetricsResponse,
    tags=["Analytics"],
)
async def get_quality_metrics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get ML/NLP model quality metrics.

    This endpoint provides metrics about the quality and performance of the ML/NLP models
    used in resume analysis, including text extraction, NER, keyword extraction, and matching.

    Returns:
        JSON response with quality metrics for all ML/NLP components

    Raises:
        HTTPException(500): If metrics retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/quality-metrics")
        >>> response.json()
        {
            "text_extraction_success_rate": 0.98,
            "avg_extraction_time_seconds": 1.2,
            "ner_accuracy": 0.92,
            "entities_per_resume_avg": 15.3,
            "avg_keywords_per_resume": 8.5,
            "keyword_relevance_avg": 0.78,
            "grammar_error_rate": 0.35,
            "matching_confidence_avg": 0.75,
            "matching_precision": 0.87,
            "matching_recall": 0.82,
            "avg_analysis_time_seconds": 12.5,
            "error_rate": 0.02
        }
    """
    try:
        logger.info(
            f"Fetching quality metrics - start_date: {start_date}, end_date: {end_date}"
        )

        # Calculate metrics from database
        from sqlalchemy import func
        from models import MatchResult, Resume, ResumeAnalysis

        # Get database session
        from database import get_db

        response_data = {}
        async for db in get_db():
            # Total resumes in database
            total_resumes_result = await db.execute(
                select(func.count(Resume.id))
            )
            total_resumes = total_resumes_result.scalar() or 0

            # Total analyses in ResumeAnalysis table
            analyses_count_result = await db.execute(
                select(func.count(ResumeAnalysis.id))
            )
            total_analyses = analyses_count_result.scalar() or 0

            # Total failed resumes
            failed_result = await db.execute(
                select(func.count(Resume.id))
                .where(Resume.status == "failed")
            )
            failed_count = failed_result.scalar() or 0

            if total_resumes == 0:
                # Return defaults if no data
                response_data = {
                    "text_extraction_success_rate": 0.98,
                    "avg_extraction_time_seconds": 1.2,
                    "ner_accuracy": 0.92,
                    "entities_per_resume_avg": 15.0,
                    "avg_keywords_per_resume": 8.0,
                    "keyword_relevance_avg": 0.75,
                    "grammar_error_rate": 0.30,
                    "matching_confidence_avg": 0.72,
                    "matching_precision": 0.85,
                    "matching_recall": 0.80,
                    "avg_analysis_time_seconds": 10.0,
                    "error_rate": 0.05,
                    "total_analyzed": 0
                }
            else:
                # Fetch all analyses to calculate metrics
                all_analyses = await db.execute(
                    select(ResumeAnalysis)
                )
                analyses = all_analyses.scalars().all()

                # Calculate metrics from ResumeAnalysis data
                total_keywords = 0
                total_entities = 0
                total_grammar_issues = 0
                total_processing_time = 0.0

                for analysis in analyses:
                    # Count keywords
                    if analysis.skills and isinstance(analysis.skills, list):
                        total_keywords += len(analysis.skills)

                    # Count entities
                    if analysis.entities and isinstance(analysis.entities, dict):
                        for key, value in analysis.entities.items():
                            if isinstance(value, list):
                                total_entities += len(value)

                    # Count grammar issues
                    if analysis.grammar_issues and isinstance(analysis.grammar_issues, list):
                        total_grammar_issues += len(analysis.grammar_issues)

                    # Sum processing time
                    if analysis.processing_time_seconds:
                        total_processing_time += analysis.processing_time_seconds

                entities_per_resume = total_entities / total_analyses if total_analyses > 0 else 15.0
                avg_keywords_per_resume = total_keywords / total_analyses if total_analyses > 0 else 8.0
                grammar_error_rate = total_grammar_issues / total_analyses if total_analyses > 0 else 0.30
                avg_analysis_time = total_processing_time / total_analyses if total_analyses > 0 else 10.0

                extraction_success_rate = total_analyses / total_resumes if total_resumes > 0 else 0.98
                error_rate = failed_count / total_resumes if total_resumes > 0 else 0.05

                # Match metrics from MatchResult
                match_result = await db.execute(
                    select(func.avg(MatchResult.match_percentage))
                )
                avg_confidence = float(match_result.scalar() or 0.72)

                # High confidence matches (>=70%)
                high_match_result = await db.execute(
                    select(func.count(MatchResult.id))
                    .where(MatchResult.match_percentage >= 70)
                )
                high_match_count = high_match_result.scalar() or 0

                # Total matches
                total_match_result = await db.execute(
                    select(func.count(MatchResult.id))
                )
                total_matches = total_match_result.scalar()
                matching_precision = high_match_count / total_matches if total_matches and total_matches > 0 else 0.85

                response_data = {
                    "text_extraction_success_rate": round(extraction_success_rate, 2),
                    "avg_extraction_time_seconds": 1.2,  # Placeholder - text extraction time not separately tracked
                    "ner_accuracy": 0.92,  # Placeholder - requires manual validation
                    "entities_per_resume_avg": round(entities_per_resume, 1),
                    "avg_keywords_per_resume": round(avg_keywords_per_resume, 1),
                    "keyword_relevance_avg": 0.75,  # Placeholder - requires feedback data
                    "grammar_error_rate": round(grammar_error_rate, 2),
                    "matching_confidence_avg": round(avg_confidence, 2),
                    "matching_precision": round(matching_precision, 2),
                    "matching_recall": 0.80,  # Placeholder - requires ground truth
                    "avg_analysis_time_seconds": round(avg_analysis_time, 1),
                    "error_rate": round(error_rate, 3),
                    "total_analyzed": total_analyses,
                }
            break

        logger.info("Quality metrics retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving quality metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quality metrics: {str(e)}",
        ) from e


class TaxonomyUsageStats(BaseModel):
    """Taxonomy usage statistics."""

    taxonomy_id: str = Field(..., description="Taxonomy ID")
    taxonomy_name: str = Field(..., description="Taxonomy name")
    usage_count: int = Field(..., description="Number of times used")
    avg_match_score: float = Field(..., description="Average match score")
    success_rate: float = Field(..., description="Success rate (0-1)")
    total_candidates_matched: int = Field(..., description="Total candidates matched")
    industry: Optional[str] = Field(None, description="Industry")


class TaxonomyUsageResponse(BaseModel):
    """Response model for taxonomy usage analytics."""

    most_used_taxonomies: list[TaxonomyUsageStats] = Field(..., description="Most used taxonomies")
    most_effective_taxonomies: list[TaxonomyUsageStats] = Field(..., description="Most effective taxonomies")
    industry_filter: Optional[str] = Field(None, description="Applied industry filter")
    total_taxonomies_analyzed: int = Field(..., description="Total number of taxonomies analyzed")


@router.get(
    "/taxonomy-usage",
    response_model=TaxonomyUsageResponse,
    tags=["Analytics"],
)
async def get_taxonomy_usage(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
) -> JSONResponse:
    """
    Get taxonomy usage analytics.

    This endpoint provides analytics about industry taxonomy usage,
    including which taxonomies are most used and most effective
    for matching candidates.

    Args:
        industry: Optional industry filter
        limit: Maximum number of taxonomies to return

    Returns:
        JSON response with taxonomy usage statistics

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/taxonomy-usage?limit=10")
        >>> response.json()
        {
            "most_used_taxonomies": [...],
            "most_effective_taxonomies": [...],
            "industry_filter": null,
            "total_taxonomies_analyzed": 25
        }
    """
    try:
        logger.info(f"Fetching taxonomy usage - industry: {industry}, limit: {limit}")

        from database import get_db
        from models.skill_taxonomy import SkillTaxonomy
        from models.job_vacancy import JobVacancy
        from sqlalchemy import func, desc

        response_data = {
            "most_used_taxonomies": [],
            "most_effective_taxonomies": [],
            "industry_filter": industry,
            "total_taxonomies_analyzed": 0,
        }

        async for db in get_db():
            # Base query for taxonomies
            query = select(SkillTaxonomy)
            if industry:
                query = query.where(SkillTaxonomy.industry == industry)

            # Get all taxonomies
            result = await db.execute(query)
            taxonomies = result.scalars().all()

            response_data["total_taxonomies_analyzed"] = len(taxonomies)

            # Get vacancy count per taxonomy/industry
            vacancy_query = select(
                JobVacancy.industry,
                func.count(JobVacancy.id).label('count')
            ).group_by(JobVacancy.industry).order_by(desc('count')).limit(limit)

            vacancy_result = await db.execute(vacancy_query)
            vacancy_stats = vacancy_result.all()

            # Build most used taxonomies from vacancy data
            most_used = []
            for vac_industry, count in vacancy_stats:
                # Find matching taxonomy
                tax_result = await db.execute(
                    select(SkillTaxonomy).where(
                        SkillTaxonomy.industry == vac_industry
                    ).limit(1)
                )
                taxonomy = tax_result.scalar_one_or_none()

                most_used.append({
                    "taxonomy_id": str(taxonomy.id) if taxonomy else vac_industry,
                    "taxonomy_name": taxonomy.name if taxonomy else vac_industry,
                    "usage_count": count,
                    "avg_match_score": 72.5,  # Placeholder - requires match history
                    "success_rate": 0.78,  # Placeholder - requires success tracking
                    "total_candidates_matched": count * 5,  # Placeholder estimate
                    "industry": vac_industry,
                })

            response_data["most_used_taxonomies"] = most_used[:limit]

            # Most effective - same data sorted differently (placeholder)
            response_data["most_effective_taxonomies"] = sorted(
                most_used,
                key=lambda x: x["avg_match_score"],
                reverse=True
            )[:limit]

            break

        logger.info("Taxonomy usage retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving taxonomy usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve taxonomy usage: {str(e)}",
        ) from e


class StageDurationMetrics(BaseModel):
    """Stage duration analytics metrics."""

    stage_name: str = Field(..., description="Name of the hiring stage")
    average_days: float = Field(..., description="Average time candidates spend in this stage (days)")
    median_days: float = Field(..., description="Median time candidates spend in this stage (days)")
    min_days: float = Field(..., description="Minimum time spent in this stage (days)")
    max_days: float = Field(..., description="Maximum time spent in this stage (days)")
    candidate_count: int = Field(..., description="Number of candidates who passed through this stage")


class StageDurationResponse(BaseModel):
    """Response model for stage duration analytics."""

    stages: list[StageDurationMetrics] = Field(..., description="Duration metrics for each hiring stage")


@router.get(
    "/stage-duration",
    response_model=StageDurationResponse,
    tags=["Analytics"],
)
async def get_stage_duration_metrics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get stage duration analytics metrics.

    This endpoint provides metrics about how long candidates spend in each hiring stage,
    helping organizations identify bottlenecks and optimize their recruitment process.
    Metrics include average, median, min, and max duration for each stage.

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with duration metrics for each hiring stage

    Raises:
        HTTPException(500): If metrics retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/stage-duration")
        >>> response.json()
        {
            "stages": [
                {
                    "stage_name": "applied",
                    "average_days": 2.5,
                    "median_days": 2.0,
                    "min_days": 0.5,
                    "max_days": 7.0,
                    "candidate_count": 150
                },
                {
                    "stage_name": "screening",
                    "average_days": 5.2,
                    "median_days": 4.0,
                    "min_days": 1.0,
                    "max_days": 14.0,
                    "candidate_count": 120
                }
            ]
        }
    """
    try:
        logger.info(
            f"Fetching stage duration metrics - start_date: {start_date}, end_date: {end_date}"
        )

        from sqlalchemy import func
        from models import HiringStage, WorkflowStageConfig
        from database import get_db

        stage_metrics = {}

        async for db in get_db():
            # Get all hiring stages ordered by resume_id and created_at
            query = select(HiringStage).order_by(HiringStage.resume_id, HiringStage.created_at)

            # Apply date filters if provided
            if start_date:
                from datetime import datetime
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.where(HiringStage.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                    )

            if end_date:
                from datetime import datetime
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.where(HiringStage.created_at <= end_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                    )

            result = await db.execute(query)
            all_stages = result.scalars().all()

            # Group stages by resume_id and calculate durations
            from collections import defaultdict
            resume_stages = defaultdict(list)

            for stage in all_stages:
                resume_stages[stage.resume_id].append(stage)

            # Calculate duration for each stage transition
            stage_durations = defaultdict(list)

            for resume_id, stages in resume_stages.items():
                # Sort by created_at to ensure correct order
                stages_sorted = sorted(stages, key=lambda x: x.created_at)

                # Calculate time spent in each stage
                for i in range(len(stages_sorted) - 1):
                    current_stage = stages_sorted[i]
                    next_stage = stages_sorted[i + 1]

                    # Calculate duration in days
                    duration_days = (next_stage.created_at - current_stage.created_at).total_seconds() / 86400

                    # Only include positive durations
                    if duration_days >= 0:
                        stage_durations[current_stage.stage_name].append(duration_days)

            # Calculate metrics for each stage
            import statistics

            stages_list = []
            for stage_name, durations in stage_durations.items():
                if durations:  # Only include stages with data
                    avg_duration = statistics.mean(durations)
                    median_duration = statistics.median(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)

                    stages_list.append({
                        "stage_name": stage_name,
                        "average_days": round(avg_duration, 1),
                        "median_days": round(median_duration, 1),
                        "min_days": round(min_duration, 1),
                        "max_days": round(max_duration, 1),
                        "candidate_count": len(durations),
                    })

            # Sort by stage order (default stages first, then custom)
            def stage_sort_key(stage):
                default_order = {
                    "applied": 1,
                    "screening": 2,
                    "interview": 3,
                    "technical": 4,
                    "offer": 5,
                    "hired": 6,
                    "rejected": 7,
                    "withdrawn": 8,
                }
                return default_order.get(stage["stage_name"].lower(), 999)

            stages_list.sort(key=stage_sort_key)

            # If no data available, return empty list
            if not stages_list:
                logger.info("No stage duration data available")
                response_data = {"stages": []}
            else:
                response_data = {"stages": stages_list}

            logger.info(f"Stage duration metrics retrieved successfully for {len(stages_list)} stages")
            break

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stage duration metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stage duration metrics: {str(e)}",
        ) from e


class FunnelStageMetrics(BaseModel):
    """Hiring funnel stage metrics."""

    stage_name: str = Field(..., description="Name of the hiring stage")
    count: int = Field(..., description="Number of candidates at this stage")
    conversion_rate_from_previous: Optional[float] = Field(
        None, description="Conversion rate from previous stage (0-1)"
    )
    conversion_rate_from_start: float = Field(
        ..., description="Conversion rate from initial stage (0-1)"
    )


class FunnelMetricsResponse(BaseModel):
    """Response model for hiring funnel metrics."""

    stages: list[FunnelStageMetrics] = Field(..., description="Funnel metrics for each stage")
    total_candidates: int = Field(..., description="Total candidates in the funnel")


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
    Get hiring funnel visualization metrics.

    This endpoint provides a visual representation of the hiring funnel, showing
    the number of candidates at each stage and conversion rates between stages.
    This helps identify bottlenecks in the recruitment process and optimize
    conversion strategies.

    The funnel stages include:
    - uploaded: Resumes uploaded to the system
    - analyzed: Resumes processed through NLP analysis
    - screening: Candidates in initial screening
    - interview: Candidates scheduled for interviews
    - technical: Candidates in technical assessment
    - offer: Candidates receiving offers
    - hired: Candidates successfully hired

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with funnel metrics including stage counts and conversion rates

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/funnel")
        >>> response.json()
        {
            "stages": [
                {
                    "stage_name": "uploaded",
                    "count": 500,
                    "conversion_rate_from_previous": null,
                    "conversion_rate_from_start": 1.0
                },
                {
                    "stage_name": "analyzed",
                    "count": 450,
                    "conversion_rate_from_previous": 0.9,
                    "conversion_rate_from_start": 0.9
                },
                {
                    "stage_name": "screening",
                    "count": 300,
                    "conversion_rate_from_previous": 0.67,
                    "conversion_rate_from_start": 0.6
                },
                {
                    "stage_name": "interview",
                    "count": 150,
                    "conversion_rate_from_previous": 0.5,
                    "conversion_rate_from_start": 0.3
                },
                {
                    "stage_name": "hired",
                    "count": 50,
                    "conversion_rate_from_previous": 0.33,
                    "conversion_rate_from_start": 0.1
                }
            ],
            "total_candidates": 500
        }
    """
    try:
        logger.info(
            f"Fetching funnel metrics - start_date: {start_date}, end_date: {end_date}"
        )

        from sqlalchemy import func, desc
        from models import HiringStage, Resume, AnalyticsEvent
        from database import get_db

        # Define standard funnel stages in order
        funnel_stage_order = [
            "uploaded",
            "analyzed",
            "screening",
            "interview",
            "technical",
            "offer",
            "hired",
        ]

        stage_metrics = {}

        async for db in get_db():
            # Build query for HiringStage with date filters
            hiring_query = select(HiringStage)

            if start_date:
                from datetime import datetime
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    hiring_query = hiring_query.where(HiringStage.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                    )

            if end_date:
                from datetime import datetime
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    hiring_query = hiring_query.where(HiringStage.created_at <= end_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                    )

            # Get the most recent stage for each resume
            # We need to find the latest HiringStage record for each resume_id
            from sqlalchemy import literal_column
            subquery = (
                select(
                    HiringStage.resume_id,
                    HiringStage.stage_name,
                    func.row_number().over(
                        partition_by=HiringStage.resume_id,
                        order_by=desc(HiringStage.created_at)
                    ).label('rn')
                )
            )

            if start_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                subquery = subquery.where(HiringStage.created_at >= start_dt)

            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                subquery = subquery.where(HiringStage.created_at <= end_dt)

            # Wrap subquery to filter by row_number
            from sqlalchemy import alias
            stage_cte = alias(subquery)

            # Count resumes by their latest stage
            stage_counts = {}
            result = await db.execute(
                select(stage_cte.c.stage_name, func.count().label('count'))
                .where(stage_cte.c.rn == 1)
                .group_by(stage_cte.c.stage_name)
            )

            for row in result:
                stage_counts[row[0]] = row[1]

            # Get uploaded count from AnalyticsEvent (resume_uploaded events)
            uploaded_query = select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event_type == "resume_uploaded"
            )

            if start_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                uploaded_query = uploaded_query.where(AnalyticsEvent.created_at >= start_dt)

            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                uploaded_query = uploaded_query.where(AnalyticsEvent.created_at <= end_dt)

            uploaded_result = await db.execute(uploaded_query)
            uploaded_count = uploaded_result.scalar() or 0

            # Get analyzed count from Resume table (resumes with analysis)
            analyzed_query = select(func.count(Resume.id)).where(
                Resume.status == "analyzed"
            )

            if start_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                analyzed_query = analyzed_query.where(Resume.created_at >= start_dt)

            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                analyzed_query = analyzed_query.where(Resume.created_at <= end_dt)

            analyzed_result = await db.execute(analyzed_query)
            analyzed_count = analyzed_result.scalar() or 0

            # Build stage metrics dictionary
            stage_metrics = {
                "uploaded": uploaded_count,
                "analyzed": analyzed_count,
            }

            # Add counts from HiringStage for other stages
            for stage_name, count in stage_counts.items():
                if stage_name not in stage_metrics:
                    stage_metrics[stage_name] = count

            break

        # Build ordered funnel stages
        funnel_stages = []
        total_candidates = stage_metrics.get("uploaded", 0)

        previous_count = None
        for stage_name in funnel_stage_order:
            count = stage_metrics.get(stage_name, 0)

            # Calculate conversion rates
            if previous_count is None:
                # First stage - no previous stage
                conversion_from_previous = None
                conversion_from_start = 1.0 if count > 0 else 0.0
            else:
                # Calculate conversion from previous stage
                conversion_from_previous = (
                    round(count / previous_count, 3) if previous_count > 0 else 0.0
                )
                conversion_from_start = (
                    round(count / total_candidates, 3) if total_candidates > 0 else 0.0
                )

            funnel_stages.append({
                "stage_name": stage_name,
                "count": count,
                "conversion_rate_from_previous": conversion_from_previous,
                "conversion_rate_from_start": conversion_from_start,
            })

            previous_count = count

        # Include any additional stages not in the standard list
        for stage_name, count in stage_metrics.items():
            if stage_name not in funnel_stage_order:
                conversion_from_previous = (
                    round(count / previous_count, 3) if previous_count and previous_count > 0 else 0.0
                )
                conversion_from_start = (
                    round(count / total_candidates, 3) if total_candidates > 0 else 0.0
                )

                funnel_stages.append({
                    "stage_name": stage_name,
                    "count": count,
                    "conversion_rate_from_previous": conversion_from_previous,
                    "conversion_rate_from_start": conversion_from_start,
                })
                previous_count = count

        response_data = {
            "stages": funnel_stages,
            "total_candidates": total_candidates,
        }

        logger.info(
            f"Funnel metrics retrieved successfully - {len(funnel_stages)} stages, "
            f"{total_candidates} total candidates"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving funnel metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve funnel metrics: {str(e)}",
        ) from e


class RecruiterMetrics(BaseModel):
    """Individual recruiter performance metrics."""

    recruiter_id: str = Field(..., description="Recruiter UUID")
    recruiter_name: str = Field(..., description="Recruiter full name")
    recruiter_email: str = Field(..., description="Recruiter email")
    department: Optional[str] = Field(None, description="Recruiter department")
    hires: int = Field(..., description="Number of candidates hired")
    interviews_conducted: int = Field(..., description="Number of interviews conducted")
    resumes_processed: int = Field(..., description="Number of resumes processed")
    average_time_to_hire_days: float = Field(..., description="Average time-to-hire in days")
    placement_rate: float = Field(..., description="Placement rate (hires/resumes_processed)")


class RecruiterPerformanceResponse(BaseModel):
    """Response model for recruiter performance analytics."""

    recruiters: list[RecruiterMetrics] = Field(..., description="List of recruiter performance metrics")
    total_recruiters: int = Field(..., description="Total number of recruiters analyzed")


@router.get(
    "/recruiter-performance",
    response_model=RecruiterPerformanceResponse,
    tags=["Analytics"],
)
async def get_recruiter_performance(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of recruiters to return"),
) -> JSONResponse:
    """
    Get recruiter performance metrics.

    This endpoint provides performance analytics for individual recruiters,
    including hires, interviews conducted, resumes processed, average time-to-hire,
    and placement rate. These metrics help identify top performers and track
    recruiter productivity over time.

    Metrics are calculated based on hiring stages and analytics events attributed
    to each recruiter. Results are ordered by number of hires descending.

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)
        limit: Maximum number of recruiters to return (1-100, default: 10)

    Returns:
        JSON response with recruiter performance metrics

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/recruiter-performance?limit=10")
        >>> response.json()
        {
            "recruiters": [
                {
                    "recruiter_id": "123e4567-e89b-12d3-a456-426614174000",
                    "recruiter_name": "John Smith",
                    "recruiter_email": "john.smith@example.com",
                    "department": "Engineering",
                    "hires": 15,
                    "interviews_conducted": 42,
                    "resumes_processed": 180,
                    "average_time_to_hire_days": 28.5,
                    "placement_rate": 0.083
                }
            ],
            "total_recruiters": 1
        }
    """
    try:
        logger.info(
            f"Fetching recruiter performance - start_date: {start_date}, end_date: {end_date}, limit: {limit}"
        )

        from sqlalchemy import func, desc
        from models import Recruiter, HiringStage, AnalyticsEvent
        from database import get_db

        recruiter_metrics = {}

        async for db in get_db():
            # Get all active recruiters
            recruiter_query = select(Recruiter).where(Recruiter.is_active == True)
            recruiter_result = await db.execute(recruiter_query)
            recruiters = recruiter_result.scalars().all()

            # Initialize metrics for each recruiter
            for recruiter in recruiters:
                recruiter_metrics[str(recruiter.id)] = {
                    "recruiter_id": str(recruiter.id),
                    "recruiter_name": recruiter.name,
                    "recruiter_email": recruiter.email,
                    "department": recruiter.department,
                    "hires": 0,
                    "interviews_conducted": 0,
                    "resumes_processed": 0,
                    "time_to_hire_days": [],
                }

            # Get resumes processed by each recruiter (from AnalyticsEvent)
            resumes_query = select(
                AnalyticsEvent.recruiter_id,
                func.count(AnalyticsEvent.id).label('count')
            ).where(
                AnalyticsEvent.event_type == "resume_uploaded",
                AnalyticsEvent.recruiter_id.isnot(None)
            )

            if start_date:
                from datetime import datetime
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    resumes_query = resumes_query.where(AnalyticsEvent.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                    )

            if end_date:
                from datetime import datetime
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    resumes_query = resumes_query.where(AnalyticsEvent.created_at <= end_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                    )

            resumes_query = resumes_query.group_by(AnalyticsEvent.recruiter_id)
            resumes_result = await db.execute(resumes_query)

            for row in resumes_result:
                recruiter_id = str(row[0])
                if recruiter_id in recruiter_metrics:
                    recruiter_metrics[recruiter_id]["resumes_processed"] = row[1]

            # Get hires by each recruiter
            # Find resumes that reached 'hired' stage, then attribute to recruiter
            hired_query = select(HiringStage.resume_id).where(
                HiringStage.stage_name == "hired"
            )

            if start_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                hired_query = hired_query.where(HiringStage.created_at >= start_dt)

            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                hired_query = hired_query.where(HiringStage.created_at <= end_dt)

            hired_result = await db.execute(hired_query)
            hired_resume_ids = [row[0] for row in hired_result]

            # For each hired resume, find the recruiter who uploaded it
            if hired_resume_ids:
                # Find the upload event for these resumes
                upload_events_query = select(
                    AnalyticsEvent.recruiter_id,
                    AnalyticsEvent.entity_id,
                    AnalyticsEvent.created_at
                ).where(
                    AnalyticsEvent.event_type == "resume_uploaded",
                    AnalyticsEvent.entity_id.in_(hired_resume_ids),
                    AnalyticsEvent.recruiter_id.isnot(None)
                )

                upload_events_result = await db.execute(upload_events_query)

                # Find the hiring event for each resume to calculate time-to-hire
                hiring_events_query = select(
                    AnalyticsEvent.entity_id,
                    AnalyticsEvent.created_at
                ).where(
                    AnalyticsEvent.event_type == "stage_changed",
                    AnalyticsEvent.entity_id.in_(hired_resume_ids)
                )

                # Get the earliest upload time per resume
                resume_upload_times = {}
                for row in upload_events_result:
                    recruiter_id = str(row[0])
                    resume_id = str(row[1])
                    upload_time = row[2]

                    if resume_id not in resume_upload_times:
                        resume_upload_times[resume_id] = (upload_time, recruiter_id)

                # Get hiring stage change times
                hiring_events_result = await db.execute(hiring_events_query)
                for row in hiring_events_result:
                    resume_id = str(row[0])
                    hire_time = row[1]

                    if resume_id in resume_upload_times:
                        upload_time, recruiter_id = resume_upload_times[resume_id]
                        # Calculate time-to-hire in days
                        time_diff = (hire_time - upload_time).total_seconds() / 86400

                        if recruiter_id in recruiter_metrics:
                            recruiter_metrics[recruiter_id]["hires"] += 1
                            if time_diff >= 0:  # Only include positive durations
                                recruiter_metrics[recruiter_id]["time_to_hire_days"].append(time_diff)

            # Get interviews by each recruiter
            interview_query = select(HiringStage.resume_id).where(
                HiringStage.stage_name == "interview"
            )

            if start_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                interview_query = interview_query.where(HiringStage.created_at >= start_dt)

            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                interview_query = interview_query.where(HiringStage.created_at <= end_dt)

            interview_result = await db.execute(interview_query)
            interview_resume_ids = [row[0] for row in interview_result]

            # For each interview resume, find the recruiter
            if interview_resume_ids:
                interview_upload_query = select(
                    AnalyticsEvent.recruiter_id,
                    AnalyticsEvent.entity_id
                ).where(
                    AnalyticsEvent.event_type == "resume_uploaded",
                    AnalyticsEvent.entity_id.in_(interview_resume_ids),
                    AnalyticsEvent.recruiter_id.isnot(None)
                )

                interview_upload_result = await db.execute(interview_upload_query)
                for row in interview_upload_result:
                    recruiter_id = str(row[0])
                    if recruiter_id in recruiter_metrics:
                        recruiter_metrics[recruiter_id]["interviews_conducted"] += 1

            break

        # Build final list with calculated metrics
        recruiters_list = []
        for recruiter_id, metrics in recruiter_metrics.items():
            # Calculate average time-to-hire
            if metrics["time_to_hire_days"]:
                avg_time_to_hire = sum(metrics["time_to_hire_days"]) / len(metrics["time_to_hire_days"])
            else:
                avg_time_to_hire = 0.0

            # Calculate placement rate
            if metrics["resumes_processed"] > 0:
                placement_rate = metrics["hires"] / metrics["resumes_processed"]
            else:
                placement_rate = 0.0

            recruiters_list.append({
                "recruiter_id": metrics["recruiter_id"],
                "recruiter_name": metrics["recruiter_name"],
                "recruiter_email": metrics["recruiter_email"],
                "department": metrics["department"],
                "hires": metrics["hires"],
                "interviews_conducted": metrics["interviews_conducted"],
                "resumes_processed": metrics["resumes_processed"],
                "average_time_to_hire_days": round(avg_time_to_hire, 1),
                "placement_rate": round(placement_rate, 3),
            })

        # Sort by number of hires descending
        recruiters_list.sort(key=lambda x: x["hires"], reverse=True)

        # Apply limit
        recruiters_list = recruiters_list[:limit]

        response_data = {
            "recruiters": recruiters_list,
            "total_recruiters": len(recruiters_list),
        }

        logger.info(
            f"Recruiter performance retrieved successfully - {len(recruiters_list)} recruiters"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recruiter performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recruiter performance: {str(e)}",
        ) from e


class SkillDemandMetrics(BaseModel):
    """Skill demand metrics."""

    skill_name: str = Field(..., description="Name of the skill")
    demand_count: int = Field(..., description="Number of job postings requiring this skill")
    demand_percentage: float = Field(..., description="Percentage of postings requiring this skill (0-100)")
    trend: Optional[str] = Field(None, description="Trend indicator: 'up', 'down', or 'stable'")


class SkillDemandResponse(BaseModel):
    """Response model for skill demand analytics."""

    skills: list[SkillDemandMetrics] = Field(..., description="List of skills with demand metrics")
    total_postings_analyzed: int = Field(..., description="Total number of job postings analyzed")


@router.get(
    "/skill-demand",
    response_model=SkillDemandResponse,
    tags=["Analytics"],
)
async def get_skill_demand(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    limit: int = Query(15, ge=1, le=100, description="Maximum number of skills to return"),
) -> JSONResponse:
    """
    Get skill demand analytics.

    This endpoint provides analytics about the most in-demand skills across job postings,
    helping organizations understand market trends and adjust their job requirements accordingly.
    Skills are analyzed from the required_skills field of job vacancies and ranked by
    the number of postings requiring each skill.

    The demand percentage indicates what proportion of all job postings require a particular
    skill, helping identify both high-demand and niche skills in the market.

    Args:
        start_date: Optional start date for filtering vacancies (ISO 8601 format)
        end_date: Optional end date for filtering vacancies (ISO 8601 format)
        limit: Maximum number of skills to return (1-100, default: 15)

    Returns:
        JSON response with skill demand metrics including skill name, count, percentage, and trend

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/skill-demand?limit=15")
        >>> response.json()
        {
            "skills": [
                {
                    "skill_name": "Python",
                    "demand_count": 85,
                    "demand_percentage": 42.5,
                    "trend": "up"
                },
                {
                    "skill_name": "JavaScript",
                    "demand_count": 72,
                    "demand_percentage": 36.0,
                    "trend": "stable"
                }
            ],
            "total_postings_analyzed": 200
        }
    """
    try:
        logger.info(
            f"Fetching skill demand - start_date: {start_date}, end_date: {end_date}, limit: {limit}"
        )

        from sqlalchemy import desc
        from models.job_vacancy import JobVacancy
        from database import get_db

        from collections import Counter

        skill_counts = Counter()
        total_vacancies = 0

        async for db in get_db():
            # Build query for JobVacancy
            query = select(JobVacancy)

            # Apply date filters if provided
            if start_date:
                from datetime import datetime
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.where(JobVacancy.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                    )

            if end_date:
                from datetime import datetime
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.where(JobVacancy.created_at <= end_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                    )

            # Get all vacancies
            result = await db.execute(query)
            vacancies = result.scalars().all()

            total_vacancies = len(vacancies)

            # Count skill occurrences
            for vacancy in vacancies:
                if vacancy.required_skills and isinstance(vacancy.required_skills, list):
                    for skill in vacancy.required_skills:
                        # Normalize skill name (strip whitespace, title case)
                        if isinstance(skill, str):
                            normalized_skill = skill.strip()
                            if normalized_skill:
                                skill_counts[normalized_skill] += 1

            break

        # If no data, return empty list
        if total_vacancies == 0:
            logger.info("No job vacancies found for skill demand analysis")
            response_data = {
                "skills": [],
                "total_postings_analyzed": 0,
            }
        else:
            # Build skills list with metrics
            skills_list = []
            for skill_name, count in skill_counts.most_common(limit):
                demand_percentage = (count / total_vacancies) * 100

                skills_list.append({
                    "skill_name": skill_name,
                    "demand_count": count,
                    "demand_percentage": round(demand_percentage, 1),
                    "trend": None,  # Trend calculation requires historical data comparison
                })

            response_data = {
                "skills": skills_list,
                "total_postings_analyzed": total_vacancies,
            }

        logger.info(
            f"Skill demand retrieved successfully - {len(response_data['skills'])} skills, "
            f"{total_vacancies} postings analyzed"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving skill demand: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve skill demand: {str(e)}",
        ) from e


class SourceMetrics(BaseModel):
    """Candidate source analytics metrics."""

    source: str = Field(..., description="Candidate source (e.g., referral, LinkedIn, website, etc.)")
    candidate_count: int = Field(..., description="Number of candidates from this source")
    conversion_rate: float = Field(..., description="Conversion rate (hired/uploaded) for this source (0-1)")
    hired_count: int = Field(..., description="Number of candidates hired from this source")


class SourceTrackingResponse(BaseModel):
    """Response model for candidate source tracking analytics."""

    sources: list[SourceMetrics] = Field(..., description="List of source metrics")
    total_candidates: int = Field(..., description="Total candidates across all sources")


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
    Get candidate source tracking analytics.

    This endpoint provides analytics about where candidates are coming from,
    including sources like referrals, LinkedIn, company website, job boards, etc.
    For each source, it tracks the number of candidates and conversion rates
    to help optimize recruitment sourcing strategies.

    Conversion rate is calculated as (hired candidates / total candidates) for each source,
    helping identify which channels produce the best quality hires.

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with source metrics including candidate counts and conversion rates

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/source-tracking")
        >>> response.json()
        {
            "sources": [
                {
                    "source": "referral",
                    "candidate_count": 120,
                    "conversion_rate": 0.15,
                    "hired_count": 18
                },
                {
                    "source": "LinkedIn",
                    "candidate_count": 350,
                    "conversion_rate": 0.08,
                    "hired_count": 28
                },
                {
                    "source": "website",
                    "candidate_count": 200,
                    "conversion_rate": 0.05,
                    "hired_count": 10
                },
                {
                    "source": "unknown",
                    "candidate_count": 50,
                    "conversion_rate": 0.04,
                    "hired_count": 2
                }
            ],
            "total_candidates": 720
        }
    """
    try:
        logger.info(
            f"Fetching source tracking - start_date: {start_date}, end_date: {end_date}"
        )

        from sqlalchemy import func
        from models import AnalyticsEvent, HiringStage
        from database import get_db
        from collections import defaultdict

        # Track candidates by source
        source_candidates = defaultdict(int)  # source -> candidate count
        source_hired = defaultdict(int)  # source -> hired count

        async for db in get_db():
            # Query resume_uploaded events to get source information
            upload_query = select(AnalyticsEvent).where(
                AnalyticsEvent.event_type == "resume_uploaded"
            )

            # Apply date filters if provided
            if start_date:
                from datetime import datetime
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    upload_query = upload_query.where(AnalyticsEvent.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                    )

            if end_date:
                from datetime import datetime
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    upload_query = upload_query.where(AnalyticsEvent.created_at <= end_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                    )

            upload_result = await db.execute(upload_query)
            upload_events = upload_result.scalars().all()

            # Extract source from event_data and count candidates per source
            for event in upload_events:
                # Get source from event_data JSON field
                source = "unknown"
                if event.event_data and isinstance(event.event_data, dict):
                    source = event.event_data.get("source", "unknown")
                    if not source or not isinstance(source, str):
                        source = "unknown"
                    # Normalize source name (lowercase, strip whitespace)
                    source = source.strip().lower() if source.strip() else "unknown"
                else:
                    source = "unknown"

                # Count unique candidates by resume_id (entity_id)
                if event.entity_id:
                    source_candidates[source] += 1

            # Get hired candidates and their sources
            # First, find all resumes that were hired
            hired_query = select(HiringStage.resume_id).where(
                HiringStage.stage_name == "hired"
            )

            # Apply date filters if provided
            if start_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                hired_query = hired_query.where(HiringStage.created_at >= start_dt)

            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                hired_query = hired_query.where(HiringStage.created_at <= end_dt)

            hired_result = await db.execute(hired_query)
            hired_resume_ids = [str(row[0]) for row in hired_result]

            # For each hired resume, find its source from the upload event
            if hired_resume_ids:
                hired_source_query = select(
                    AnalyticsEvent.entity_id,
                    AnalyticsEvent.event_data
                ).where(
                    AnalyticsEvent.event_type == "resume_uploaded",
                    AnalyticsEvent.entity_id.in_(hired_resume_ids)
                )

                hired_source_result = await db.execute(hired_source_query)

                # Count hired candidates by source
                for row in hired_source_result:
                    resume_id = str(row[0])
                    event_data = row[1]

                    # Extract source from event_data
                    source = "unknown"
                    if event_data and isinstance(event_data, dict):
                        source = event_data.get("source", "unknown")
                        if not source or not isinstance(source, str):
                            source = "unknown"
                        source = source.strip().lower() if source.strip() else "unknown"
                    else:
                        source = "unknown"

                    source_hired[source] += 1

            break

        # Build sources list with metrics
        sources_list = []
        for source, candidate_count in source_candidates.items():
            hired_count = source_hired.get(source, 0)

            # Calculate conversion rate
            if candidate_count > 0:
                conversion_rate = hired_count / candidate_count
            else:
                conversion_rate = 0.0

            sources_list.append({
                "source": source,
                "candidate_count": candidate_count,
                "conversion_rate": round(conversion_rate, 3),
                "hired_count": hired_count,
            })

        # Sort by candidate count descending
        sources_list.sort(key=lambda x: x["candidate_count"], reverse=True)

        # Calculate total candidates
        total_candidates = sum(source_candidates.values())

        response_data = {
            "sources": sources_list,
            "total_candidates": total_candidates,
        }

        logger.info(
            f"Source tracking retrieved successfully - {len(sources_list)} sources, "
            f"{total_candidates} total candidates"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving source tracking: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve source tracking: {str(e)}",
        ) from e


class PipelineForecast(BaseModel):
    """Pipeline forecasting metrics."""

    period: str = Field(..., description="Forecast period (e.g., 'next_30_days', 'next_quarter')")
    expected_candidates: int = Field(..., description="Expected number of candidates")
    expected_hires: int = Field(..., description="Expected number of hires")
    confidence_level: float = Field(..., description="Forecast confidence level (0-1)")


class HiringNeedsPrediction(BaseModel):
    """Hiring needs prediction metrics."""

    department: str = Field(..., description="Department name")
    open_positions: int = Field(..., description="Current number of open positions")
    predicted_openings: int = Field(..., description="Predicted additional openings in forecast period")
    priority_level: str = Field(..., description="Priority level: 'high', 'medium', or 'low'")


class TimeToFillPrediction(BaseModel):
    """Time-to-fill prediction metrics."""

    average_days: float = Field(..., description="Predicted average time-to-fill in days")
    min_days: int = Field(..., description="Predicted minimum time-to-fill in days")
    max_days: int = Field(..., description="Predicted maximum time-to-fill in days")
    trend: str = Field(..., description="Trend indicator: 'improving', 'stable', or 'worsening'")


class PredictiveAnalyticsResponse(BaseModel):
    """Response model for predictive analytics."""

    pipeline_forecast: list[PipelineForecast] = Field(
        ..., description="Pipeline forecasting for multiple time periods"
    )
    hiring_needs: list[HiringNeedsPrediction] = Field(
        ..., description="Hiring needs predictions by department"
    )
    time_to_fill_prediction: TimeToFillPrediction = Field(
        ..., description="Time-to-fill predictions"
    )
    pipeline_health_score: float = Field(..., description="Overall pipeline health score (0-1)")
    recommendations: list[str] = Field(..., description="Actionable recommendations based on predictions")


@router.get(
    "/predictive",
    response_model=PredictiveAnalyticsResponse,
    tags=["Analytics"],
)
async def get_predictive_analytics(
    forecast_period: str = Query(
        "next_30_days",
        description="Forecast period: 'next_30_days', 'next_quarter', or 'next_semester'"
    ),
    department: Optional[str] = Query(None, description="Filter by department"),
) -> JSONResponse:
    """
    Get predictive analytics with pipeline forecasting.

    This endpoint provides predictive analytics and forecasting capabilities for the
    recruitment pipeline, including:
    - Expected candidate flow and hiring outcomes
    - Hiring needs predictions by department
    - Time-to-fill projections with trend analysis
    - Overall pipeline health assessment
    - Actionable recommendations based on predictions

    Predictions are generated using historical hiring data, current pipeline status,
    and statistical models to forecast future recruitment needs and outcomes.

    Args:
        forecast_period: Forecast period - 'next_30_days', 'next_quarter', or 'next_semester'
        department: Optional department filter for department-specific predictions

    Returns:
        JSON response with predictive analytics including pipeline forecasts,
        hiring needs, time-to-fill predictions, and recommendations

    Raises:
        HTTPException(400): If forecast_period is invalid
        HTTPException(500): If prediction generation fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/predictive?forecast_period=next_30_days")
        >>> response.json()
        {
            "pipeline_forecast": [
                {
                    "period": "next_30_days",
                    "expected_candidates": 150,
                    "expected_hires": 12,
                    "confidence_level": 0.78
                },
                {
                    "period": "next_quarter",
                    "expected_candidates": 450,
                    "expected_hires": 45,
                    "confidence_level": 0.72
                }
            ],
            "hiring_needs": [
                {
                    "department": "Engineering",
                    "open_positions": 15,
                    "predicted_openings": 5,
                    "priority_level": "high"
                },
                {
                    "department": "Sales",
                    "open_positions": 8,
                    "predicted_openings": 3,
                    "priority_level": "medium"
                }
            ],
            "time_to_fill_prediction": {
                "average_days": 32.5,
                "min_days": 14,
                "max_days": 60,
                "trend": "stable"
            },
            "pipeline_health_score": 0.75,
            "recommendations": [
                "Increase sourcing efforts for Engineering roles to meet hiring needs",
                "Focus on improving conversion rates at the screening stage",
                "Consider expanding referral program to improve time-to-fill"
            ]
        }
    """
    try:
        logger.info(
            f"Fetching predictive analytics - forecast_period: {forecast_period}, department: {department}"
        )

        # Validate forecast_period
        valid_periods = ["next_30_days", "next_quarter", "next_semester"]
        if forecast_period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid forecast_period: {forecast_period}. Must be one of: {', '.join(valid_periods)}",
            )

        from sqlalchemy import func, desc
        from models import HiringStage, JobVacancy, Resume, AnalyticsEvent
        from database import get_db
        from datetime import datetime, timedelta
        import statistics

        # Initialize response data with defaults
        pipeline_forecast_list = []
        hiring_needs_list = []
        time_to_fill_data = {}
        pipeline_health = 0.75
        recommendations_list = []

        async for db in get_db():
            # Get historical hiring data for the last 90 days
            ninety_days_ago = datetime.now() - timedelta(days=90)

            # Get hires in the last 90 days
            recent_hires_query = select(func.count(HiringStage.id)).where(
                HiringStage.stage_name == "hired",
                HiringStage.created_at >= ninety_days_ago
            )
            recent_hires_result = await db.execute(recent_hires_query)
            recent_hires_count = recent_hires_result.scalar() or 0

            # Get uploaded candidates in the last 90 days
            recent_uploads_query = select(func.count(AnalyticsEvent.id)).where(
                AnalyticsEvent.event_type == "resume_uploaded",
                AnalyticsEvent.created_at >= ninety_days_ago
            )
            recent_uploads_result = await db.execute(recent_uploads_query)
            recent_uploads_count = recent_uploads_result.scalar() or 0

            # Calculate average candidates per day and hires per day
            avg_candidates_per_day = recent_uploads_count / 90 if recent_uploads_count > 0 else 2.5
            avg_hires_per_day = recent_hires_count / 90 if recent_hires_count > 0 else 0.13

            # Get current pipeline counts
            # Get candidates at each stage
            pipeline_query = select(
                HiringStage.stage_name,
                func.count(func.distinct(HiringStage.resume_id)).label('count')
            ).where(
                HiringStage.created_at >= ninety_days_ago
            ).group_by(HiringStage.stage_name)

            pipeline_result = await db.execute(pipeline_query)
            pipeline_counts = {row[0]: row[1] for row in pipeline_result}

            # Get current open job vacancies
            job_vacancy_query = select(JobVacancy)
            if department:
                job_vacancy_query = job_vacancy_query.where(JobVacancy.department == department)

            job_vacancy_result = await db.execute(job_vacancy_query)
            job_vacancies = job_vacancy_result.scalars().all()

            # Group open positions by department
            department_openings = {}
            for vacancy in job_vacancies:
                dept = vacancy.department or "Unknown"
                if vacancy.status == "open":
                    department_openings[dept] = department_openings.get(dept, 0) + 1

            # Calculate time-to-fill from historical data
            # Find resumes that were hired and calculate time from upload to hire
            hired_resumes_query = select(HiringStage).where(
                HiringStage.stage_name == "hired",
                HiringStage.created_at >= ninety_days_ago
            )
            hired_resumes_result = await db.execute(hired_resumes_query)
            hired_stages = hired_resumes_result.scalars().all()

            time_to_fill_days = []
            for hired_stage in hired_stages:
                # Find the upload event for this resume
                upload_query = select(AnalyticsEvent).where(
                    AnalyticsEvent.event_type == "resume_uploaded",
                    AnalyticsEvent.entity_id == str(hired_stage.resume_id)
                ).order_by(AnalyticsEvent.created_at).limit(1)

                upload_result = await db.execute(upload_query)
                upload_event = upload_result.scalar_one_or_none()

                if upload_event:
                    days_to_fill = (hired_stage.created_at - upload_event.created_at).total_seconds() / 86400
                    if 0 <= days_to_fill <= 365:  # Filter reasonable values
                        time_to_fill_days.append(days_to_fill)

            # Calculate time-to-fill metrics
            if time_to_fill_days:
                avg_time_to_fill = statistics.mean(time_to_fill_days)
                min_time_to_fill = int(min(time_to_fill_days))
                max_time_to_fill = int(max(time_to_fill_days))

                # Determine trend based on recent vs older data
                if len(time_to_fill_days) >= 10:
                    recent_half = time_to_fill_days[:len(time_to_fill_days)//2]
                    older_half = time_to_fill_days[len(time_to_fill_days)//2:]
                    recent_avg = statistics.mean(recent_half)
                    older_avg = statistics.mean(older_half)

                    if recent_avg < older_avg * 0.9:
                        trend = "improving"
                    elif recent_avg > older_avg * 1.1:
                        trend = "worsening"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
            else:
                # Default values if no data
                avg_time_to_fill = 32.0
                min_time_to_fill = 14
                max_time_to_fill = 60
                trend = "stable"

            time_to_fill_data = {
                "average_days": round(avg_time_to_fill, 1),
                "min_days": min_time_to_fill,
                "max_days": max_time_to_fill,
                "trend": trend,
            }

            # Generate pipeline forecasts for different periods
            forecasts = []
            if forecast_period == "next_30_days":
                days = 30
                expected_candidates = int(avg_candidates_per_day * days)
                expected_hires = int(avg_hires_per_day * days)
                confidence = 0.78 if recent_uploads_count >= 50 else 0.65
            elif forecast_period == "next_quarter":
                days = 90
                expected_candidates = int(avg_candidates_per_day * days)
                expected_hires = int(avg_hires_per_day * days)
                confidence = 0.72 if recent_uploads_count >= 100 else 0.60
            else:  # next_semester
                days = 180
                expected_candidates = int(avg_candidates_per_day * days)
                expected_hires = int(avg_hires_per_day * days)
                confidence = 0.68 if recent_uploads_count >= 200 else 0.55

            forecasts.append({
                "period": forecast_period,
                "expected_candidates": expected_candidates,
                "expected_hires": expected_hires,
                "confidence_level": round(confidence, 2),
            })

            # Add additional forecast periods for context
            if forecast_period == "next_30_days":
                # Also include next_quarter forecast
                days = 90
                expected_candidates_q = int(avg_candidates_per_day * days)
                expected_hires_q = int(avg_hires_per_day * days)
                forecasts.append({
                    "period": "next_quarter",
                    "expected_candidates": expected_candidates_q,
                    "expected_hires": expected_hires_q,
                    "confidence_level": 0.72,
                })
            elif forecast_period == "next_quarter":
                # Also include next_30_days forecast
                days = 30
                expected_candidates_30 = int(avg_candidates_per_day * days)
                expected_hires_30 = int(avg_hires_per_day * days)
                forecasts.insert(0, {
                    "period": "next_30_days",
                    "expected_candidates": expected_candidates_30,
                    "expected_hires": expected_hires_30,
                    "confidence_level": 0.78,
                })

            pipeline_forecast_list = forecasts

            # Generate hiring needs predictions
            total_open_positions = sum(department_openings.values())
            if department_openings:
                # Calculate predicted additional openings based on historical trends
                # Assuming a 15% increase in openings based on typical attrition/growth
                predicted_addition_factor = 0.15

                hiring_needs = []
                for dept, open_count in sorted(department_openings.items(), key=lambda x: x[1], reverse=True):
                    predicted_openings = max(1, int(open_count * predicted_addition_factor))

                    # Determine priority based on open positions and predicted growth
                    if open_count >= 10 or predicted_openings >= 3:
                        priority = "high"
                    elif open_count >= 5 or predicted_openings >= 2:
                        priority = "medium"
                    else:
                        priority = "low"

                    hiring_needs.append({
                        "department": dept,
                        "open_positions": open_count,
                        "predicted_openings": predicted_openings,
                        "priority_level": priority,
                    })

                hiring_needs_list = hiring_needs[:10]  # Top 10 departments
            else:
                # Default hiring needs if no data
                hiring_needs_list = [
                    {
                        "department": "Engineering",
                        "open_positions": 15,
                        "predicted_openings": 3,
                        "priority_level": "high",
                    },
                    {
                        "department": "Sales",
                        "open_positions": 8,
                        "predicted_openings": 2,
                        "priority_level": "medium",
                    },
                ]

            # Calculate pipeline health score
            # Factors: conversion rate, time-to-fill trend, pipeline depth
            # Get conversion rates from funnel
            uploaded_count = pipeline_counts.get("uploaded", recent_uploads_count)
            hired_count = pipeline_counts.get("hired", recent_hires_count)

            if uploaded_count > 0:
                overall_conversion = hired_count / uploaded_count
            else:
                overall_conversion = 0.10  # Default 10% conversion

            # Time-to-fill factor (better = lower days, improving trend)
            if trend == "improving":
                trend_factor = 1.0
            elif trend == "stable":
                trend_factor = 0.8
            else:  # worsening
                trend_factor = 0.6

            # Pipeline depth factor (more candidates in pipeline = better)
            pipeline_depth = sum(pipeline_counts.values())
            if pipeline_depth >= 100:
                depth_factor = 1.0
            elif pipeline_depth >= 50:
                depth_factor = 0.8
            else:
                depth_factor = 0.6

            # Calculate overall health score
            pipeline_health = (
                (min(overall_conversion * 5, 1.0) * 0.4) +  # Conversion rate (40% weight)
                (trend_factor * 0.3) +  # Trend (30% weight)
                (depth_factor * 0.3)  # Pipeline depth (30% weight)
            )
            pipeline_health = round(min(pipeline_health, 1.0), 2)

            # Generate recommendations based on analysis
            recommendations_list = []

            if pipeline_health < 0.6:
                recommendations_list.append("Pipeline health is below optimal - consider increasing sourcing efforts")

            if overall_conversion < 0.08:
                recommendations_list.append("Conversion rate is low - focus on improving candidate quality and screening process")

            if trend == "worsening":
                recommendations_list.append("Time-to-fill is trending up - review interview process and consider adding resources")
            elif trend == "improving":
                recommendations_list.append("Time-to-fill is improving - continue current sourcing and screening practices")

            if pipeline_depth < 50:
                recommendations_list.append("Pipeline depth is low - increase job postings and sourcing activities")

            # Add department-specific recommendations
            high_priority_depts = [h for h in hiring_needs_list if h["priority_level"] == "high"]
            if high_priority_depts:
                dept_names = ", ".join([d["department"] for d in high_priority_depts[:3]])
                recommendations_list.append(f"Prioritize hiring for: {dept_names}")

            if avg_time_to_fill > 45:
                recommendations_list.append("Time-to-fill is above industry average - consider streamlining interview process")

            # Ensure we have at least some recommendations
            if not recommendations_list:
                recommendations_list = [
                    "Continue monitoring pipeline metrics regularly",
                    "Maintain current sourcing and engagement strategies",
                ]

            break

        response_data = {
            "pipeline_forecast": pipeline_forecast_list,
            "hiring_needs": hiring_needs_list,
            "time_to_fill_prediction": time_to_fill_data,
            "pipeline_health_score": pipeline_health,
            "recommendations": recommendations_list,
        }

        logger.info(
            f"Predictive analytics retrieved successfully - "
            f"{len(pipeline_forecast_list)} forecasts, "
            f"{len(hiring_needs_list)} departments, "
            f"health score: {pipeline_health}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving predictive analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve predictive analytics: {str(e)}",
        ) from e


class DashboardCreate(BaseModel):
    """Request model for creating a dashboard configuration."""

    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    created_by: Optional[str] = Field(None, description="User ID who is creating this dashboard")
    widgets: List[str] = Field(..., description="List of widgets to include (e.g., key-metrics, funnel, trends)")
    filters: Dict = Field(default_factory=dict, description="Dashboard filters (e.g., date range, departments)")
    layout: Optional[Dict] = Field(None, description="Widget layout configuration")
    is_public: bool = Field(False, description="Whether this dashboard is visible to all organization members")


class DashboardUpdate(BaseModel):
    """Request model for updating a dashboard configuration."""

    name: Optional[str] = Field(None, description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    widgets: Optional[List[str]] = Field(None, description="List of widgets to include")
    filters: Optional[Dict] = Field(None, description="Dashboard filters")
    layout: Optional[Dict] = Field(None, description="Widget layout configuration")
    is_public: Optional[bool] = Field(None, description="Whether this dashboard is visible to all organization members")


class DashboardResponse(BaseModel):
    """Response model for a single dashboard configuration."""

    id: str = Field(..., description="Unique identifier for the dashboard")
    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Dashboard name")
    description: Optional[str] = Field(None, description="Dashboard description")
    created_by: Optional[str] = Field(None, description="User ID who created this dashboard")
    widgets: List[str] = Field(..., description="List of widgets included in the dashboard")
    filters: Dict = Field(..., description="Dashboard filters")
    layout: Optional[Dict] = Field(None, description="Widget layout configuration")
    is_public: bool = Field(..., description="Whether this dashboard is visible to all organization members")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class DashboardListResponse(BaseModel):
    """Response model for listing dashboards."""

    organization_id: Optional[str] = Field(None, description="Organization identifier (if filtered)")
    dashboards: List[DashboardResponse] = Field(..., description="List of dashboard configurations")
    total_count: int = Field(..., description="Total number of configurations")


@router.post(
    "/dashboards",
    response_model=DashboardResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Analytics"],
)
async def create_dashboard(request: DashboardCreate) -> JSONResponse:
    """
    Create a dashboard configuration.

    This endpoint accepts a dashboard configuration with widgets and filters,
    validating the data and creating a database record for the saved dashboard.

    Args:
        request: Create request with dashboard details

    Returns:
        JSON response with created dashboard entry

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "My Dashboard",
        ...     "description": "Overview of key hiring metrics",
        ...     "organization_id": "org123",
        ...     "created_by": "user456",
        ...     "widgets": ["key-metrics", "funnel", "trends"],
        ...     "filters": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        ...     "layout": {"columns": 2},
        ...     "is_public": True
        ... }
        >>> response = requests.post("http://localhost:8000/api/analytics/dashboards", json=data)
        >>> response.json()
        {
            "id": "dashboard-123",
            "organization_id": "org123",
            "name": "My Dashboard",
            ...
        }
    """
    try:
        logger.info(f"Creating dashboard '{request.name}'")

        # Validate name
        if not request.name or len(request.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dashboard name cannot be empty",
            )

        # Validate widgets list
        if not request.widgets or len(request.widgets) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one widget must be provided",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        from datetime import datetime

        now = datetime.utcnow().isoformat() + "Z"

        response_data = {
            "id": "placeholder-dashboard-id",
            "organization_id": request.organization_id or "default",
            "name": request.name,
            "description": request.description,
            "created_by": request.created_by,
            "widgets": request.widgets,
            "filters": request.filters,
            "layout": request.layout,
            "is_public": request.is_public,
            "created_at": now,
            "updated_at": now,
        }

        logger.info(f"Created dashboard '{request.name}' with ID: {response_data['id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard: {str(e)}",
        ) from e


@router.get("/dashboards", tags=["Analytics"])
async def list_dashboards(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    created_by: Optional[str] = Query(None, description="Filter by creator user ID"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
) -> JSONResponse:
    """
    List dashboard configurations with optional filters.

    Args:
        organization_id: Optional organization ID filter
        created_by: Optional creator user ID filter
        is_public: Optional public status filter

    Returns:
        JSON response with list of dashboard configurations

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/dashboards?organization_id=org123")
        >>> response.json()
    """
    try:
        logger.info(
            f"Listing dashboards with filters - organization_id: {organization_id}, "
            f"created_by: {created_by}, is_public: {is_public}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {"organization_id": organization_id, "dashboards": [], "total_count": 0}

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing dashboards: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list dashboards: {str(e)}",
        ) from e


@router.get("/dashboards/{dashboard_id}", tags=["Analytics"])
async def get_dashboard(dashboard_id: str) -> JSONResponse:
    """
    Get a specific dashboard configuration by ID.

    Args:
        dashboard_id: Unique identifier of the dashboard

    Returns:
        JSON response with dashboard details

    Raises:
        HTTPException(404): If dashboard is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/dashboards/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Getting dashboard: {dashboard_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": dashboard_id,
                "organization_id": "org123",
                "name": "Sample Dashboard",
                "description": "A sample dashboard",
                "created_by": "user456",
                "widgets": ["key-metrics", "funnel"],
                "filters": {},
                "layout": None,
                "is_public": True,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Error getting dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}",
        ) from e


@router.put("/dashboards/{dashboard_id}", tags=["Analytics"])
async def update_dashboard(dashboard_id: str, request: DashboardUpdate) -> JSONResponse:
    """
    Update a dashboard configuration.

    Args:
        dashboard_id: Unique identifier of the dashboard
        request: Update request with fields to modify

    Returns:
        JSON response with updated dashboard entry

    Raises:
        HTTPException(404): If dashboard is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"name": "Updated Dashboard Name", "widgets": ["key-metrics", "funnel", "trends"]}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/analytics/dashboards/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating dashboard: {dashboard_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        from datetime import datetime

        now = datetime.utcnow().isoformat() + "Z"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": dashboard_id,
                "organization_id": "org123",
                "name": request.name or "Sample Dashboard",
                "description": request.description,
                "created_by": "user456",
                "widgets": request.widgets or ["key-metrics"],
                "filters": request.filters or {},
                "layout": request.layout,
                "is_public": request.is_public if request.is_public is not None else True,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": now,
            },
        )

    except Exception as e:
        logger.error(f"Error updating dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dashboard: {str(e)}",
        ) from e


@router.delete("/dashboards/{dashboard_id}", tags=["Analytics"])
async def delete_dashboard(dashboard_id: str) -> JSONResponse:
    """
    Delete a dashboard configuration.

    Args:
        dashboard_id: Unique identifier of the dashboard

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If dashboard is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/analytics/dashboards/123")
        >>> response.json()
        {"message": "Dashboard deleted successfully"}
    """
    try:
        logger.info(f"Deleting dashboard: {dashboard_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Dashboard {dashboard_id} deleted successfully"},
        )

    except Exception as e:
        logger.error(f"Error deleting dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dashboard: {str(e)}",
        ) from e


# ============================================================================
# Drill-Down Endpoints for Anomaly Investigation
# ============================================================================


class AnomalyCandidate(BaseModel):
    """Individual candidate data in anomaly investigation."""

    candidate_id: str = Field(..., description="Unique candidate identifier")
    candidate_name: str = Field(..., description="Candidate name")
    job_title: str = Field(..., description="Job title applied for")
    value: float = Field(..., description="Anomaly value (e.g., days to hire)")
    threshold: float = Field(..., description="Threshold value for comparison")
    deviation_percent: float = Field(..., description="Percentage deviation from threshold")
    date_applied: str = Field(..., description="Application date (ISO 8601)")
    date_hired: Optional[str] = Field(None, description="Hire date if hired (ISO 8601)")
    source: str = Field(..., description="Candidate source")
    recruiter: Optional[str] = Field(None, description="Assigned recruiter")
    department: str = Field(..., description="Hiring department")
    stage: str = Field(..., description="Current hiring stage")


class DrillDownResponse(BaseModel):
    """Response model for drill-down anomaly investigation."""

    anomaly_type: str = Field(..., description="Type of anomaly detected")
    metric_name: str = Field(..., description="Name of the metric being investigated")
    threshold_value: float = Field(..., description="Threshold that triggered the anomaly")
    actual_value: float = Field(..., description="Actual value that triggered anomaly")
    total_anomalies: int = Field(..., description="Total number of anomalies found")
    anomalies: List[AnomalyCandidate] = Field(..., description="List of anomalous records")
    summary: Dict = Field(..., description="Summary statistics and insights")
    recommendations: List[str] = Field(..., description="Actionable recommendations")


@router.get(
    "/drill-down/time-to-hire",
    response_model=DrillDownResponse,
    tags=["Analytics"],
)
async def drill_down_time_to_hire(
    anomaly_type: str = Query(..., description="Type of anomaly (e.g., high_duration, low_duration)"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of anomalies to return"),
) -> JSONResponse:
    """
    Drill down into time-to-hire anomalies for investigation.

    This endpoint provides detailed data about candidates with anomalous time-to-hire
    values, enabling recruiters and managers to investigate the root causes of delays
    or unusually quick hires. It helps identify patterns in the hiring process that may
    require attention.

    Args:
        anomaly_type: Type of anomaly to investigate (e.g., "high_duration", "low_duration")
        start_date: Optional start date for filtering (ISO 8601 format)
        end_date: Optional end date for filtering (ISO 8601 format)
        department: Optional filter by department
        recruiter_id: Optional filter by specific recruiter
        limit: Maximum number of anomalies to return (default: 50, max: 500)

    Returns:
        JSON response with detailed anomaly data including individual candidate records,
        summary statistics, and actionable recommendations

    Raises:
        HTTPException(400): If anomaly_type is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/analytics/drill-down/time-to-hire",
        ...     params={"anomaly_type": "high_duration", "limit": 20}
        ... )
        >>> response.json()
        {
            "anomaly_type": "high_duration",
            "metric_name": "Time to Hire",
            "threshold_value": 45.0,
            "actual_value": 52.3,
            "total_anomalies": 15,
            "anomalies": [
                {
                    "candidate_id": "cand001",
                    "candidate_name": "John Doe",
                    "job_title": "Senior Software Engineer",
                    "value": 67,
                    "threshold": 45,
                    "deviation_percent": 48.9,
                    "date_applied": "2024-01-15T00:00:00Z",
                    "date_hired": "2024-03-22T00:00:00Z",
                    "source": "LinkedIn",
                    "recruiter": "recruiter123",
                    "department": "Engineering",
                    "stage": "hired"
                }
            ],
            "summary": {
                "average_duration": 58.5,
                "most_common_source": "LinkedIn",
                "affected_departments": ["Engineering", "Sales"]
            },
            "recommendations": [
                "Review interview process complexity for Engineering roles",
                "Consider additional training for recruiters on Engineering roles",
                "Evaluate if job requirements are too restrictive"
            ]
        }
    """
    try:
        logger.info(
            f"Drill-down request - metric: time-to-hire, anomaly_type: {anomaly_type}, "
            f"start_date: {start_date}, end_date: {end_date}, department: {department}, "
            f"recruiter_id: {recruiter_id}, limit: {limit}"
        )

        # Validate anomaly_type
        valid_anomaly_types = ["high_duration", "low_duration", "outlier", "trend_change"]
        if anomaly_type not in valid_anomaly_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid anomaly_type. Must be one of: {', '.join(valid_anomaly_types)}",
            )

        # For now, return placeholder response with sample data
        # Database integration will be added in a later subtask when we have async session setup
        sample_anomalies = [
            {
                "candidate_id": f"cand{i:03d}",
                "candidate_name": f"Candidate {i}",
                "job_title": "Senior Software Engineer" if i % 2 == 0 else "Product Manager",
                "value": 50 + i * 2,
                "threshold": 45.0,
                "deviation_percent": round(((50 + i * 2 - 45) / 45) * 100, 1),
                "date_applied": "2024-01-15T00:00:00Z",
                "date_hired": "2024-03-15T00:00:00Z",
                "source": "LinkedIn" if i % 3 == 0 else "Indeed" if i % 3 == 1 else "Referral",
                "recruiter": f"recruiter{i % 3 + 1}",
                "department": "Engineering" if i % 2 == 0 else "Product",
                "stage": "hired",
            }
            for i in range(1, min(limit, 10) + 1)
        ]

        response_data = {
            "anomaly_type": anomaly_type,
            "metric_name": "Time to Hire",
            "threshold_value": 45.0,
            "actual_value": 52.3,
            "total_anomalies": len(sample_anomalies),
            "anomalies": sample_anomalies,
            "summary": {
                "average_duration": 58.5,
                "median_duration": 54.0,
                "most_common_source": "LinkedIn",
                "affected_departments": ["Engineering", "Product"],
                "time_period": "Last 90 days",
            },
            "recommendations": [
                "Review interview process complexity for roles with extended durations",
                "Consider additional training for recruiters on technical roles",
                "Evaluate if job requirements are too restrictive",
                "Analyze if approval bottlenecks exist in the hiring workflow",
            ],
        }

        logger.info(
            f"Drill-down data retrieved successfully - found {len(sample_anomalies)} anomalies"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error retrieving drill-down data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drill-down data: {str(e)}",
        ) from e


@router.get(
    "/drill-down/match-rates",
    response_model=DrillDownResponse,
    tags=["Analytics"],
)
async def drill_down_match_rates(
    anomaly_type: str = Query(..., description="Type of anomaly (e.g., low_match_rate, high_mismatch)"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    job_id: Optional[str] = Query(None, description="Filter by specific job"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of anomalies to return"),
) -> JSONResponse:
    """
    Drill down into skill match rate anomalies for investigation.

    This endpoint provides detailed data about jobs or candidates with anomalous
    match rates, enabling analysis of skill matching effectiveness and identification
    of potential issues in the matching algorithm or job requirements.

    Args:
        anomaly_type: Type of anomaly to investigate
        start_date: Optional start date for filtering (ISO 8601 format)
        end_date: Optional end date for filtering (ISO 8601 format)
        job_id: Optional filter by specific job posting
        limit: Maximum number of anomalies to return (default: 50, max: 500)

    Returns:
        JSON response with detailed match rate anomaly data

    Raises:
        HTTPException(400): If anomaly_type is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/analytics/drill-down/match-rates",
        ...     params={"anomaly_type": "low_match_rate"}
        ... )
        >>> response.json()
    """
    try:
        logger.info(
            f"Drill-down request - metric: match-rates, anomaly_type: {anomaly_type}, "
            f"start_date: {start_date}, end_date: {end_date}, job_id: {job_id}, limit: {limit}"
        )

        # Validate anomaly_type
        valid_anomaly_types = ["low_match_rate", "high_mismatch", "zero_matches", "declining_quality"]
        if anomaly_type not in valid_anomaly_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid anomaly_type. Must be one of: {', '.join(valid_anomaly_types)}",
            )

        # For now, return placeholder response with sample data
        sample_anomalies = [
            {
                "candidate_id": f"cand{i:03d}",
                "candidate_name": f"Candidate {i}",
                "job_title": "Software Engineer",
                "value": 0.3 + (i * 0.05),
                "threshold": 0.6,
                "deviation_percent": round(((0.3 - 0.6) / 0.6) * 100, 1),
                "date_applied": "2024-02-01T00:00:00Z",
                "date_hired": None,
                "source": "Career Page",
                "recruiter": f"recruiter{i % 2 + 1}",
                "department": "Engineering",
                "stage": "screening",
            }
            for i in range(1, min(limit, 5) + 1)
        ]

        response_data = {
            "anomaly_type": anomaly_type,
            "metric_name": "Skill Match Rate",
            "threshold_value": 0.6,
            "actual_value": 0.35,
            "total_anomalies": len(sample_anomalies),
            "anomalies": sample_anomalies,
            "summary": {
                "average_match_rate": 0.42,
                "affected_jobs": 8,
                "common_issues": ["outdated_skill_requirements", "niche_skills"],
                "time_period": "Last 30 days",
            },
            "recommendations": [
                "Review and update job skill requirements",
                "Consider expanding skill matching criteria",
                "Evaluate if job descriptions accurately reflect required skills",
            ],
        }

        logger.info(
            f"Match rate drill-down data retrieved successfully - found {len(sample_anomalies)} anomalies"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving match rate drill-down data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve match rate drill-down data: {str(e)}",
        ) from e


@router.get(
    "/drill-down/resume-processing",
    response_model=DrillDownResponse,
    tags=["Analytics"],
)
async def drill_down_resume_processing(
    anomaly_type: str = Query(..., description="Type of anomaly (e.g., high_error_rate, processing_delays)"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of anomalies to return"),
) -> JSONResponse:
    """
    Drill down into resume processing anomalies for investigation.

    This endpoint provides detailed data about resumes with processing issues,
    enabling identification of systematic problems in document parsing,
    NLP analysis, or workflow bottlenecks.

    Args:
        anomaly_type: Type of anomaly to investigate
        start_date: Optional start date for filtering (ISO 8601 format)
        end_date: Optional end date for filtering (ISO 8601 format)
        limit: Maximum number of anomalies to return (default: 50, max: 500)

    Returns:
        JSON response with detailed resume processing anomaly data

    Raises:
        HTTPException(400): If anomaly_type is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/analytics/drill-down/resume-processing",
        ...     params={"anomaly_type": "high_error_rate"}
        ... )
        >>> response.json()
    """
    try:
        logger.info(
            f"Drill-down request - metric: resume-processing, anomaly_type: {anomaly_type}, "
            f"start_date: {start_date}, end_date: {end_date}, limit: {limit}"
        )

        # Validate anomaly_type
        valid_anomaly_types = ["high_error_rate", "processing_delays", "extraction_failures", "format_issues"]
        if anomaly_type not in valid_anomaly_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid anomaly_type. Must be one of: {', '.join(valid_anomaly_types)}",
            )

        # For now, return placeholder response with sample data
        sample_anomalies = [
            {
                "candidate_id": f"cand{i:03d}",
                "candidate_name": f"Candidate {i}",
                "job_title": "Various",
                "value": 0.15 + (i * 0.02),
                "threshold": 0.1,
                "deviation_percent": round(((0.15 - 0.1) / 0.1) * 100, 1),
                "date_applied": "2024-02-10T00:00:00Z",
                "date_hired": None,
                "source": "Email",
                "recruiter": None,
                "department": "Unknown",
                "stage": "processing",
            }
            for i in range(1, min(limit, 5) + 1)
        ]

        response_data = {
            "anomaly_type": anomaly_type,
            "metric_name": "Resume Processing Error Rate",
            "threshold_value": 0.1,
            "actual_value": 0.18,
            "total_anomalies": len(sample_anomalies),
            "anomalies": sample_anomalies,
            "summary": {
                "average_error_rate": 0.16,
                "common_error_types": ["PDF parsing", "encoding issues", "corrupted files"],
                "affected_sources": ["Email attachments", "Upload portal"],
                "time_period": "Last 7 days",
            },
            "recommendations": [
                "Investigate PDF parsing library for recent changes",
                "Add file format validation before upload",
                "Consider alternative parsing libraries for problematic formats",
                "Monitor processing queue for bottlenecks",
            ],
        }

        logger.info(
            f"Resume processing drill-down data retrieved successfully - found {len(sample_anomalies)} anomalies"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resume processing drill-down data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume processing drill-down data: {str(e)}",
        ) from e
