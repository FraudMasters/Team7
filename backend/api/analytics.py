"""
Analytics and reporting endpoints.

This module provides endpoints for retrieving recruitment analytics metrics,
including time-to-hire statistics, resume processing metrics, match rates,
and other key performance indicators for the recruitment process.
"""
import logging
from typing import Optional

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
        >>> response = requests.get("/api/analytics/key-metrics")
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
        >>> response = requests.get("/api/analytics/quality-metrics")
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
        >>> response = requests.get("/api/analytics/taxonomy-usage?limit=10")
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
        >>> response = requests.get("/api/analytics/stage-duration")
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
        >>> response = requests.get("/api/analytics/funnel")
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
        >>> response = requests.get("/api/analytics/recruiter-performance?limit=10")
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
        >>> response = requests.get("/api/analytics/skill-demand?limit=15")
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
        >>> response = requests.get("/api/analytics/source-tracking")
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


@router.get(
    "/candidate-source-attribution",
    response_model=CandidateSourceAttributionResponse,
    tags=["Analytics"],
)
async def get_candidate_source_attribution(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get candidate source attribution analytics with detailed metrics.

    This endpoint provides comprehensive analytics about candidate sources including
    conversion rates, time-to-hire metrics, and hiring stage distribution for each source.
    It helps recruitment teams understand which sourcing channels produce the best candidates
    and how candidates from different sources progress through the hiring pipeline.

    For each source, the endpoint tracks:
    - Total candidates sourced
    - Number of candidates hired (conversion)
    - Conversion rate (hired/uploaded)
    - Average time-to-hire in days
    - Distribution across all hiring stages

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with detailed source metrics including conversion rates,
        time-to-hire, and stage distribution for each source

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/analytics/candidate-source-attribution")
        >>> response.json()
        {
            "sources": [
                {
                    "source": "referral",
                    "candidate_count": 120,
                    "hired_count": 18,
                    "conversion_rate": 0.15,
                    "average_time_to_hire_days": 28.5,
                    "stage_distribution": [
                        {"stage_name": "applied", "count": 30, "percentage": 0.25},
                        {"stage_name": "screening", "count": 45, "percentage": 0.375},
                        {"stage_name": "interview", "count": 20, "percentage": 0.167},
                        {"stage_name": "offered", "count": 7, "percentage": 0.058},
                        {"stage_name": "hired", "count": 18, "percentage": 0.15}
                    ]
                },
                {
                    "source": "LinkedIn",
                    "candidate_count": 350,
                    "hired_count": 28,
                    "conversion_rate": 0.08,
                    "average_time_to_hire_days": 35.2,
                    "stage_distribution": [
                        {"stage_name": "applied", "count": 200, "percentage": 0.571},
                        {"stage_name": "screening", "count": 80, "percentage": 0.229},
                        {"stage_name": "interview", "count": 35, "percentage": 0.1},
                        {"stage_name": "offered", "count": 7, "percentage": 0.02},
                        {"stage_name": "hired", "count": 28, "percentage": 0.08}
                    ]
                }
            ],
            "total_candidates": 720,
            "date_range": null
        }
    """
    try:
        logger.info(
            f"Fetching candidate source attribution - start_date: {start_date}, end_date: {end_date}"
        )

        from datetime import datetime
        from sqlalchemy import func
        from models import AnalyticsEvent, HiringStage
        from database import get_db
        from collections import defaultdict

        # Track data by source
        source_candidates = defaultdict(int)  # source -> candidate count
        source_hired = defaultdict(int)  # source -> hired count
        source_time_to_hire = defaultdict(list)  # source -> list of time-to-hire days
        source_stages = defaultdict(lambda: defaultdict(int))  # source -> stage_name -> count

        async for db in get_db():
            # Query resume_uploaded events to get source information
            upload_query = select(AnalyticsEvent).where(
                AnalyticsEvent.event_type == "resume_uploaded"
            )

            # Apply date filters if provided
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    upload_query = upload_query.where(AnalyticsEvent.created_at >= start_dt)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                    )

            if end_date:
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
            resume_to_source = {}  # resume_id -> source mapping

            for event in upload_events:
                # Get source from event_data JSON field
                source = "unknown"
                if event.event_data and isinstance(event.event_data, dict):
                    source = event.event_data.get("source", "unknown")
                    if not source or not isinstance(source, str):
                        source = "unknown"
                    # Normalize source name (lowercase, strip whitespace)
                    source = source.strip().lower() if source.strip() else "unknown"

                # Track resume to source mapping
                if event.entity_id:
                    resume_to_source[str(event.entity_id)] = source
                    source_candidates[source] += 1

            # Get all hiring stages to calculate stage distribution and time-to-hire
            stages_query = select(HiringStage).where(
                HiringStage.resume_id.in_(list(resume_to_source.keys()))
            )

            # Apply date filters if provided
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
                if start_dt:
                    stages_query = stages_query.where(HiringStage.created_at >= start_dt)

            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
                if end_dt:
                    stages_query = stages_query.where(HiringStage.created_at <= end_dt)

            stages_result = await db.execute(stages_query)
            all_stages = stages_result.scalars().all()

            # Process all hiring stages
            for stage in all_stages:
                resume_id = str(stage.resume_id)
                source = resume_to_source.get(resume_id, "unknown")

                # Count candidates at each stage
                source_stages[source][stage.stage_name] += 1

                # Track hired candidates and calculate time-to-hire
                if stage.stage_name == "hired":
                    source_hired[source] += 1

                    # Calculate time-to-hire if we have created_at timestamp
                    # Time-to-hire is the time from resume upload to hiring
                    if stage.created_at:
                        # Find the upload event for this resume to get the start time
                        upload_event = next(
                            (e for e in upload_events if str(e.entity_id) == resume_id),
                            None
                        )
                        if upload_event and upload_event.created_at:
                            days_to_hire = (stage.created_at - upload_event.created_at).days
                            if days_to_hire >= 0:  # Only include valid positive values
                                source_time_to_hire[source].append(days_to_hire)

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

            # Calculate average time-to-hire
            time_to_hire_list = source_time_to_hire.get(source, [])
            if time_to_hire_list:
                average_time_to_hire = round(sum(time_to_hire_list) / len(time_to_hire_list), 1)
            else:
                average_time_to_hire = 0.0

            # Build stage distribution
            stage_dist_list = []
            stage_counts = source_stages.get(source, {})
            total_stage_count = sum(stage_counts.values()) if stage_counts else candidate_count

            for stage_name, count in stage_counts.items():
                if total_stage_count > 0:
                    percentage = round(count / total_stage_count, 3)
                else:
                    percentage = 0.0

                stage_dist_list.append({
                    "stage_name": stage_name,
                    "count": count,
                    "percentage": percentage,
                })

            # Sort stage distribution by count descending
            stage_dist_list.sort(key=lambda x: x["count"], reverse=True)

            sources_list.append({
                "source": source,
                "candidate_count": candidate_count,
                "hired_count": hired_count,
                "conversion_rate": round(conversion_rate, 3),
                "average_time_to_hire_days": average_time_to_hire,
                "stage_distribution": stage_dist_list,
            })

        # Sort by candidate count descending
        sources_list.sort(key=lambda x: x["candidate_count"], reverse=True)

        # Calculate total candidates
        total_candidates = sum(source_candidates.values())

        # Build date range string for response
        date_range_str = None
        if start_date or end_date:
            range_parts = []
            if start_date:
                range_parts.append(f"from {start_date}")
            if end_date:
                range_parts.append(f"to {end_date}")
            date_range_str = " ".join(range_parts)

        response_data = {
            "sources": sources_list,
            "total_candidates": total_candidates,
            "date_range": date_range_str,
        }

        logger.info(
            f"Candidate source attribution retrieved successfully - {len(sources_list)} sources, "
            f"{total_candidates} total candidates"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidate source attribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate source attribution: {str(e)}",
        ) from e


class StageDistribution(BaseModel):
    """Hiring stage distribution for a candidate source."""

    stage_name: str = Field(..., description="Name of the hiring stage")
    count: int = Field(..., description="Number of candidates at this stage")
    percentage: float = Field(..., description="Percentage of candidates at this stage (0-1)")


class CandidateSourceMetrics(BaseModel):
    """Candidate source attribution metrics."""

    source: str = Field(..., description="Candidate source (e.g., referral, LinkedIn, website, etc.)")
    candidate_count: int = Field(..., description="Number of candidates from this source")
    hired_count: int = Field(..., description="Number of candidates hired from this source")
    conversion_rate: float = Field(..., description="Conversion rate (hired/uploaded) for this source (0-1)")
    average_time_to_hire_days: float = Field(..., description="Average time-to-hire in days for this source")
    stage_distribution: list[StageDistribution] = Field(..., description="Distribution of candidates across hiring stages")


class CandidateSourceAttributionResponse(BaseModel):
    """Response model for candidate source attribution analytics."""

    sources: list[CandidateSourceMetrics] = Field(..., description="List of candidate source metrics")
    total_candidates: int = Field(..., description="Total candidates across all sources")
    date_range: Optional[str] = Field(None, description="Applied date range filter (if any)")
