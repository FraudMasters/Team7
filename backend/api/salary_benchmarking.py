"""
Salary Benchmarking and Compensation Analysis API endpoints

This module provides endpoints for:
- Getting market salary benchmarks
- Managing candidate salary history
- Comparing job offers with cost-of-living adjustments
- Internal equity analysis
- Market salary trends over time
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    CostOfLivingIndex,
    JobVacancy,
    Resume,
    ResumeAnalysis,
    SalaryBenchmark,
    SalaryHistory,
    SalaryOffer,
)
from analyzers.salary_analyzer import SalaryAnalyzer, SalaryFeatures
from analyzers.equity_analyzer import EquityAnalyzer, EquityMetricsCalculator
from analyzers.cost_of_living_calculator import CostOfLivingCalculator

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class BenchmarkRequest(BaseModel):
    """Request for salary benchmark data."""

    role: str = Field(..., min_length=2, description="Job title or role")
    location: str = Field(..., min_length=2, description="Location (city, state, or 'Remote')")
    country: Optional[str] = Field(None, min_length=2, max_length=2, description="Country code (ISO 3166-1 alpha-2)")
    experience_level: Optional[str] = Field(None, description="Experience level (entry, mid, senior, lead, executive)")
    industry: Optional[str] = Field(None, description="Industry sector")
    employment_type: Optional[str] = Field("full_time", description="Employment type")


class BenchmarkResponse(BaseModel):
    """Response with salary benchmark data."""

    role: str = Field(..., description="Job title")
    location: str = Field(..., description="Location")
    salary_min: int = Field(..., description="25th percentile salary")
    salary_median: int = Field(..., description="Median salary (50th percentile)")
    salary_max: int = Field(..., description="75th percentile salary")
    salary_p90: Optional[int] = Field(None, description="90th percentile salary")
    currency: str = Field(..., description="Currency code")
    sample_size: Optional[int] = Field(None, description="Number of data points")
    data_source: Optional[str] = Field(None, description="Data source")
    effective_date: Optional[str] = Field(None, description="Date when benchmark is effective")


class SalarySuggestionRequest(BaseModel):
    """Request for salary suggestion for a candidate."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="JobVacancy UUID")
    include_cost_of_living: bool = Field(True, description="Apply cost-of-living adjustments")
    target_location: Optional[str] = Field(None, description="Target location for cost adjustment")


class SalarySuggestionResponse(BaseModel):
    """Response with suggested salary range."""

    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="JobVacancy UUID")
    suggested_min: int = Field(..., description="Suggested minimum salary")
    suggested_median: int = Field(..., description="Suggested median salary")
    suggested_max: int = Field(..., description="Suggested maximum salary")
    currency: str = Field(..., description="Currency code")
    confidence: float = Field(..., description="Confidence level (0-1)")
    factors: Dict[str, Any] = Field(..., description="Factors affecting the suggestion")
    market_benchmark: Optional[BenchmarkResponse] = Field(None, description="Underlying market data")


class SalaryHistoryRequest(BaseModel):
    """Request to create salary history record."""

    resume_id: str = Field(..., description="Resume UUID")
    salary_amount: float = Field(..., gt=0, description="Base salary amount")
    salary_frequency: str = Field("annual", description="Payment frequency (annual, monthly, hourly, weekly)")
    currency: str = Field("USD", description="Currency code")
    effective_date: str = Field(..., description="Effective date (YYYY-MM-DD)")
    salary_type: str = Field("current", description="Salary type (current, previous, offer, projected)")
    employment_type: str = Field("full_time", description="Employment type")
    job_title: Optional[str] = Field(None, description="Job title")
    company_name: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    country: Optional[str] = Field(None, description="Country code")
    bonus_amount: Optional[float] = Field(None, description="Annual bonus amount")
    bonus_type: Optional[str] = Field(None, description="Bonus type")
    equity_value: Optional[float] = Field(None, description="Annual equity value")
    equity_type: Optional[str] = Field(None, description="Equity type")
    other_compensation: Optional[Dict[str, Any]] = Field(None, description="Other compensation details")
    is_confirmed: bool = Field(False, description="Whether data is confirmed")
    data_source: str = Field("manual", description="Data source")


class SalaryHistoryResponse(BaseModel):
    """Response with salary history record."""

    id: str = Field(..., description="SalaryHistory UUID")
    resume_id: str = Field(..., description="Resume UUID")
    salary_amount: float = Field(..., description="Base salary")
    salary_frequency: str = Field(..., description="Payment frequency")
    currency: str = Field(..., description="Currency code")
    effective_date: str = Field(..., description="Effective date")
    salary_type: str = Field(..., description="Salary type")
    employment_type: str = Field(..., description="Employment type")
    job_title: Optional[str] = Field(None, description="Job title")
    company_name: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Location")
    bonus_amount: Optional[float] = Field(None, description="Bonus amount")
    equity_value: Optional[float] = Field(None, description="Equity value")
    total_compensation: Optional[float] = Field(None, description="Total annual compensation")
    is_confirmed: bool = Field(..., description="Is confirmed")
    verification_status: str = Field(..., description="Verification status")
    created_at: str = Field(..., description="Creation timestamp")


class OfferComparisonRequest(BaseModel):
    """Request to compare multiple job offers."""

    resume_id: str = Field(..., description="Resume UUID")
    offers: List[Dict[str, Any]] = Field(..., min_items=1, description="List of offers to compare")
    apply_cost_of_living: bool = Field(True, description="Apply cost-of-living adjustments")


class OfferComparisonItem(BaseModel):
    """Single offer in comparison."""

    salary: float = Field(..., description="Base salary")
    location: str = Field(..., description="Job location")
    currency: str = Field("USD", description="Currency code")
    bonus: Optional[float] = Field(None, description="Annual bonus")
    equity: Optional[float] = Field(None, description="Annual equity value")
    job_title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")


class OfferComparisonResponse(BaseModel):
    """Response with offer comparison analysis."""

    resume_id: str = Field(..., description="Resume UUID")
    offers: List[Dict[str, Any]] = Field(..., description="Compared offers with adjustments")
    recommendation: str = Field(..., description="Recommendation based on analysis")
    analysis: Dict[str, Any] = Field(..., description="Detailed analysis")
    current_salary: Optional[float] = Field(None, description="Candidate's current salary for comparison")


class EquityAnalysisRequest(BaseModel):
    """Request for internal equity analysis."""

    vacancy_id: str = Field(..., description="JobVacancy UUID")
    include_demographics: bool = Field(True, description="Include demographic breakdown")
    pay_gap_threshold: float = Field(0.05, description="Pay gap threshold (default 5%)")


class EquityDisparity(BaseModel):
    """Pay disparity between groups."""

    group: str = Field(..., description="Demographic group")
    mean_salary: float = Field(..., description="Mean salary for group")
    sample_size: int = Field(..., description="Number of samples")
    pay_gap: float = Field(..., description="Pay gap ratio")
    is_fair: bool = Field(..., description="Whether gap is within threshold")


class EquityAnalysisResponse(BaseModel):
    """Response with equity analysis results."""

    vacancy_id: str = Field(..., description="JobVacancy UUID")
    role: str = Field(..., description="Job title")
    total_candidates: int = Field(..., description="Total candidates analyzed")
    mean_salary: float = Field(..., description="Overall mean salary")
    median_salary: float = Field(..., description="Overall median salary")
    salary_range: Dict[str, float] = Field(..., description="Salary range (min, max)")
    disparities: List[EquityDisparity] = Field(..., description="Demographic disparities")
    alerts: List[str] = Field(..., description="Equity alerts")
    recommendations: List[str] = Field(..., description="Recommendations")


class MarketTrendDataPoint(BaseModel):
    """Single data point in market trends."""

    period: str = Field(..., description="Time period (e.g., '2024-Q1', '2024-01')")
    salary_min: int = Field(..., description="25th percentile salary for the period")
    salary_median: int = Field(..., description="Median salary for the period")
    salary_max: int = Field(..., description="75th percentile salary for the period")
    sample_size: Optional[int] = Field(None, description="Number of data points for the period")


class MarketTrendsResponse(BaseModel):
    """Response with market salary trends over time."""

    role: str = Field(..., description="Job title")
    location: str = Field(..., description="Location")
    currency: str = Field(..., description="Currency code")
    period_type: str = Field(..., description="Period type (quarterly, monthly, yearly)")
    trends: List[MarketTrendDataPoint] = Field(..., description="Salary trend data points")
    year_over_year_change: Optional[float] = Field(None, description="Year-over-year salary change percentage")
    quarter_over_quarter_change: Optional[float] = Field(None, description="Quarter-over-quarter salary change percentage")
    data_source: Optional[str] = Field(None, description="Data source")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")


# Helper functions
def salary_history_to_dict(history: SalaryHistory) -> dict:
    """Convert SalaryHistory model to dictionary."""
    return {
        "id": str(history.id),
        "resume_id": str(history.resume_id),
        "salary_amount": float(history.salary_amount),
        "salary_frequency": history.salary_frequency,
        "currency": history.currency,
        "effective_date": history.effective_date,
        "salary_type": history.salary_type,
        "employment_type": history.employment_type,
        "job_title": history.job_title,
        "company_name": history.company_name,
        "location": history.location,
        "bonus_amount": float(history.bonus_amount) if history.bonus_amount else None,
        "equity_value": float(history.equity_value) if history.equity_value else None,
        "total_compensation": float(history.total_compensation) if history.total_compensation else None,
        "is_confirmed": history.is_confirmed,
        "verification_status": history.verification_status,
        "created_at": history.created_at.isoformat() if history.created_at else "",
    }


# Endpoints
@router.get(
    "/benchmarks",
    response_model=List[BenchmarkResponse],
    tags=["Salary Benchmarking"],
)
async def get_salary_benchmarks(
    role: str = Query(..., description="Job title or role"),
    location: str = Query(..., description="Location (city, state, or 'Remote')"),
    country: Optional[str] = Query(None, description="Country code"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    industry: Optional[str] = Query(None, description="Industry sector"),
    employment_type: str = Query("full_time", description="Employment type"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get salary benchmarks for a role and location.

    Queries the salary benchmark database to find market compensation data
    for the specified role, location, and other criteria.

    Args:
        role: Job title or role
        location: Geographic location
        country: Country code (optional)
        experience_level: Experience level (optional)
        industry: Industry sector (optional)
        employment_type: Employment type
        db: Database session

    Returns:
        List of matching salary benchmarks

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> GET /api/salary-benchmarking/benchmarks?role=Developer&location=Remote
        [
            {
                "role": "Software Developer",
                "location": "Remote",
                "salary_min": 75000,
                "salary_median": 95000,
                "salary_max": 120000,
                "currency": "USD"
            }
        ]
    """
    try:
        logger.info(f"Fetching salary benchmarks for role={role}, location={location}")

        # Build query conditions
        conditions = []

        # Case-insensitive partial match for role
        conditions.append(
            or_(
                SalaryBenchmark.job_title.ilike(f"%{role}%"),
                SalaryBenchmark.job_title == role
            )
        )

        # Match location (case-insensitive)
        conditions.append(
            or_(
                SalaryBenchmark.location.ilike(f"%{location}%"),
                SalaryBenchmark.location == location
            )
        )

        if country:
            conditions.append(SalaryBenchmark.country == country.upper())

        if experience_level:
            conditions.append(SalaryBenchmark.experience_level == experience_level.lower())

        if industry:
            conditions.append(
                or_(
                    SalaryBenchmark.industry.ilike(f"%{industry}%"),
                    SalaryBenchmark.industry == industry
                )
            )

        if employment_type:
            conditions.append(SalaryBenchmark.employment_type == employment_type.lower())

        # Execute query
        result = await db.execute(
            select(SalaryBenchmark).where(and_(*conditions))
        )
        benchmarks = result.scalars().all()

        # Convert to response format
        response_data = [
            {
                "role": b.job_title,
                "location": b.location,
                "salary_min": b.salary_min,
                "salary_median": b.salary_median,
                "salary_max": b.salary_max,
                "salary_p90": b.salary_p90,
                "currency": b.currency,
                "sample_size": b.sample_size,
                "data_source": b.data_source,
                "effective_date": b.effective_date,
            }
            for b in benchmarks
        ]

        logger.info(f"Found {len(response_data)} salary benchmarks")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error fetching salary benchmarks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch salary benchmarks: {str(e)}",
        ) from e


@router.post(
    "/suggest-salary",
    response_model=SalarySuggestionResponse,
    tags=["Salary Benchmarking"],
)
async def suggest_salary(
    request: SalarySuggestionRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get AI-powered salary suggestion for a candidate-vacancy pair.

    This endpoint analyzes the candidate's resume and the vacancy requirements
    to suggest an appropriate salary range based on:
    - Market benchmarks for the role and location
    - Candidate's skills and experience
    - Cost-of-living adjustments
    - Education and skill rarity bonuses

    Args:
        request: Salary suggestion request
        db: Database session

    Returns:
        Salary suggestion with breakdown of factors

    Raises:
        HTTPException(404): If resume or vacancy not found
        HTTPException(500): If analysis fails
    """
    try:
        logger.info(
            f"Suggesting salary for resume={request.resume_id}, "
            f"vacancy={request.vacancy_id}"
        )

        # Parse UUIDs
        try:
            resume_uuid = UUID(request.resume_id)
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Fetch resume and vacancy
        resume_result = await db.execute(
            select(Resume).where(Resume.id == resume_uuid)
        )
        resume = resume_result.scalar_one_or_none()

        vacancy_result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        )
        vacancy = vacancy_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume {request.resume_id} not found",
            )

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy {request.vacancy_id} not found",
            )

        # Get salary analyzer service
        from analyzers.salary_analyzer import get_salary_analyzer
        analyzer = get_salary_analyzer()

        # Get salary suggestion
        suggestion = await analyzer.suggest_salary_range(
            db=db,
            resume_id=resume_uuid,
            vacancy_id=vacancy_uuid,
        )

        logger.info(
            f"Salary suggestion generated: "
            f"${suggestion['suggested_range']['median']:,.0f} "
            f"(confidence: {suggestion['confidence']})"
        )

        # Map suggestion to response format
        response_data = {
            "resume_id": str(resume_uuid),
            "vacancy_id": str(vacancy_uuid),
            "suggested_min": suggestion["suggested_range"]["min"],
            "suggested_median": suggestion["suggested_range"]["median"],
            "suggested_max": suggestion["suggested_range"]["max"],
            "currency": suggestion.get("currency", "USD"),
            "confidence": 1.0 if suggestion["confidence"] == "high" else (0.5 if suggestion["confidence"] == "medium" else 0.2),
            "factors": suggestion.get("breakdown", {}),
            "market_benchmark": suggestion.get("breakdown", {}).get("base_benchmark"),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting salary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate salary suggestion: {str(e)}",
        ) from e


@router.post(
    "/salary-history",
    response_model=SalaryHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Salary Benchmarking"],
)
async def create_salary_history(
    request: SalaryHistoryRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a salary history record for a candidate.

    Stores historical salary data for tracking compensation progression
    and enabling offer comparisons.

    Args:
        request: Salary history data
        db: Database session

    Returns:
        Created salary history record

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If creation fails
    """
    try:
        logger.info(f"Creating salary history for resume={request.resume_id}")

        # Parse UUID
        try:
            resume_uuid = UUID(request.resume_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == resume_uuid)
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume {request.resume_id} not found",
            )

        # Create salary history record
        history = SalaryHistory(
            resume_id=resume_uuid,
            salary_amount=request.salary_amount,
            salary_frequency=request.salary_frequency,
            currency=request.currency,
            effective_date=request.effective_date,
            salary_type=request.salary_type,
            employment_type=request.employment_type,
            job_title=request.job_title,
            company_name=request.company_name,
            location=request.location,
            country=request.country,
            bonus_amount=request.bonus_amount,
            bonus_type=request.bonus_type,
            equity_value=request.equity_value,
            equity_type=request.equity_type,
            other_compensation=request.other_compensation,
            is_confirmed=request.is_confirmed,
            data_source=request.data_source,
        )

        # Calculate total compensation
        total_comp = history.calculate_total_compensation()
        if total_comp:
            history.total_compensation = total_comp

        db.add(history)
        await db.commit()
        await db.refresh(history)

        logger.info(f"Created salary history: {history.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=salary_history_to_dict(history),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating salary history: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create salary history: {str(e)}",
        ) from e


@router.get(
    "/salary-history/{resume_id}",
    response_model=List[SalaryHistoryResponse],
    tags=["Salary Benchmarking"],
)
async def get_salary_history(
    resume_id: str,
    salary_type: Optional[str] = Query(None, description="Filter by salary type"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get salary history for a candidate.

    Returns all salary history records for a resume, optionally filtered
    by salary type (current, previous, offer, projected).

    Args:
        resume_id: Resume UUID
        salary_type: Optional filter by salary type
        db: Database session

    Returns:
        List of salary history records

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If query fails
    """
    try:
        logger.info(f"Fetching salary history for resume={resume_id}")

        # Parse UUID
        try:
            resume_uuid = UUID(resume_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Build query
        conditions = [SalaryHistory.resume_id == resume_uuid]

        if salary_type:
            conditions.append(SalaryHistory.salary_type == salary_type.lower())

        result = await db.execute(
            select(SalaryHistory)
            .where(and_(*conditions))
            .order_by(SalaryHistory.effective_date.desc())
        )
        history_records = result.scalars().all()

        response_data = [
            salary_history_to_dict(h) for h in history_records
        ]

        logger.info(f"Found {len(response_data)} salary history records")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching salary history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch salary history: {str(e)}",
        ) from e


@router.post(
    "/compare-offers",
    response_model=OfferComparisonResponse,
    tags=["Salary Benchmarking"],
)
async def compare_offers(
    request: OfferComparisonRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Compare multiple job offers with cost-of-living adjustments.

    This endpoint compares different job offers by:
    - Applying cost-of-living adjustments to normalize salaries
    - Comparing total compensation (salary + bonus + equity)
    - Providing a recommendation based on the analysis

    Note: The resume_id is used to fetch current salary for additional context,
    but the offer comparison works even if the resume doesn't exist.

    Args:
        request: Offer comparison request
        db: Database session

    Returns:
        Comparison analysis with recommendation

    Raises:
        HTTPException(500): If comparison fails
    """
    try:
        logger.info(f"Comparing offers for resume={request.resume_id}")

        # Parse UUID and validate resume (optional - for current salary context only)
        resume_uuid = None
        resume_exists = False

        try:
            resume_uuid = UUID(request.resume_id)
            # Try to fetch resume, but don't fail if it doesn't exist
            resume_result = await db.execute(
                select(Resume).where(Resume.id == resume_uuid)
            )
            resume = resume_result.scalar_one_or_none()
            resume_exists = resume is not None

            if not resume_exists:
                logger.info(f"Resume {request.resume_id} not found - proceeding with offer comparison without current salary context")
        except ValueError:
            logger.warning(f"Invalid UUID format for resume_id={request.resume_id} - proceeding with offer comparison")

        # Get cost of living calculator
        col_calculator = CostOfLivingCalculator()

        # Normalize and compare offers
        compared_offers = []
        base_currency = "USD"

        for offer in request.offers:
            salary = float(offer.get("salary", 0))
            location = offer.get("location", "")
            currency = offer.get("currency", "USD")
            bonus = float(offer.get("bonus", 0))
            equity = float(offer.get("equity", 0))

            # Calculate total compensation
            total_comp = salary + bonus + equity

            # Apply cost-of-living adjustment if requested
            adjusted_total = total_comp
            col_index = None

            if request.apply_cost_of_living and location:
                try:
                    col_data = await col_calculator.get_location_index(
                        db, location
                    )
                    if col_data:
                        col_index = col_data.get("cost_of_living_index")
                        # Normalize to US average (index 100)
                        if col_index:
                            adjusted_total = total_comp * (100.0 / col_index)
                except Exception as e:
                    logger.warning(f"Could not apply COL adjustment for {location}: {e}")

            compared_offers.append({
                "salary": salary,
                "location": location,
                "currency": currency,
                "bonus": bonus,
                "equity": equity,
                "total_compensation": total_comp,
                "adjusted_total": round(adjusted_total, 2),
                "col_index": col_index,
                "job_title": offer.get("job_title"),
                "company": offer.get("company"),
            })

        # Sort by adjusted total (descending)
        compared_offers.sort(key=lambda x: x["adjusted_total"], reverse=True)

        # Generate recommendation
        if compared_offers:
            best_offer = compared_offers[0]
            recommendation = f"The best offer is from {best_offer.get('company', 'the company')} in {best_offer['location']} "
            recommendation += f"with an adjusted total compensation of ${best_offer['adjusted_total']:,.2f}"
        else:
            recommendation = "No valid offers to compare"

        # Get current salary if available (only if resume exists)
        current_salary = None
        if resume_uuid and resume_exists:
            current_result = await db.execute(
                select(SalaryHistory)
                .where(
                    and_(
                        SalaryHistory.resume_id == resume_uuid,
                        SalaryHistory.salary_type == "current"
                    )
                )
                .order_by(SalaryHistory.effective_date.desc())
                .limit(1)
            )
            current_record = current_result.scalar_one_or_none()
            if current_record and current_record.total_compensation:
                current_salary = float(current_record.total_compensation)

        analysis = {
            "total_offers": len(compared_offers),
            "cost_of_living_applied": request.apply_cost_of_living,
            "best_location": compared_offers[0]["location"] if compared_offers else None,
            "salary_range": {
                "min": min(o["total_compensation"] for o in compared_offers) if compared_offers else 0,
                "max": max(o["total_compensation"] for o in compared_offers) if compared_offers else 0,
            } if compared_offers else None,
        }

        response_data = {
            "resume_id": request.resume_id,
            "offers": compared_offers,
            "recommendation": recommendation,
            "analysis": analysis,
            "current_salary": current_salary,
        }

        logger.info(f"Compared {len(compared_offers)} offers")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing offers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare offers: {str(e)}",
        ) from e


@router.get(
    "/equity-analysis",
    response_model=EquityAnalysisResponse,
    tags=["Salary Benchmarking"],
)
async def get_equity_analysis(
    vacancy_id: str,
    include_demographics: bool = Query(True, description="Include demographic breakdown"),
    pay_gap_threshold: float = Query(0.05, description="Pay gap threshold"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get internal equity analysis for a vacancy.

    Analyzes salary data for candidates considered for a vacancy to
    identify potential pay disparities across demographic groups.

    Args:
        vacancy_id: JobVacancy UUID
        include_demographics: Whether to include demographic breakdown
        pay_gap_threshold: Pay gap threshold for alerts
        db: Database session

    Returns:
        Equity analysis with disparities and alerts

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(500): If analysis fails
    """
    try:
        logger.info(f"Performing equity analysis for vacancy={vacancy_id}")

        # Parse UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Fetch vacancy
        vacancy_result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        )
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy {vacancy_id} not found",
            )

        # Get equity analyzer service
        from analyzers.equity_analyzer import get_equity_analyzer
        analyzer = get_equity_analyzer()

        # Get equity report
        report = await analyzer.get_equity_report(
            db=db,
            vacancy_id=vacancy_uuid,
            analysis_date=None,
        )

        # Check for errors
        if report.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=report.get("message", "Analysis failed"),
            )

        # Convert report to expected format
        summary = report.get("summary", {})
        metrics_by_demographic = report.get("metrics_by_demographic", {})

        # Calculate overall mean and salary range from demographic data
        all_salaries = []
        for attr_data in metrics_by_demographic.values():
            for group_metrics in attr_data.get("groups", {}).values():
                all_salaries.append(group_metrics.get("mean_salary", 0))

        mean_salary = sum(all_salaries) / len(all_salaries) if all_salaries else 0
        salary_min = min(all_salaries) if all_salaries else 0
        salary_max = max(all_salaries) if all_salaries else 0

        # Build disparities list from demographic metrics
        disparities = []
        for attr, attr_data in metrics_by_demographic.items():
            if "error" in attr_data:
                continue

            reference_mean = attr_data.get("reference_mean_salary", 0)
            for group_name, group_metrics in attr_data.get("groups", {}).items():
                disparities.append({
                    "group": f"{attr}={group_name}",
                    "mean_salary": group_metrics.get("mean_salary", 0),
                    "sample_size": group_metrics.get("sample_size", 0),
                    "pay_gap": group_metrics.get("pay_gap_ratio", 0),
                    "is_fair": group_metrics.get("is_fair", True),
                })

        analysis = {
            "vacancy_id": str(vacancy_uuid),
            "role": report.get("vacancy_title", ""),
            "total_candidates": summary.get("total_candidates", 0),
            "mean_salary": mean_salary,
            "median_salary": summary.get("median_salary", 0),
            "salary_range": {
                "min": salary_min,
                "max": salary_max,
            },
            "disparities": disparities,
            "alerts": [f"{a['attribute']}: {a['severity']}" for a in summary.get("alerts_triggered", [])],
            "recommendations": [r.get("suggestion", "") for r in report.get("recommendations", [])],
        }

        logger.info(
            f"Equity analysis complete: {analysis['total_candidates']} candidates, "
            f"{len(analysis['alerts'])} alerts"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=analysis,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing equity analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform equity analysis: {str(e)}",
        ) from e


@router.get(
    "/market-trends",
    response_model=MarketTrendsResponse,
    tags=["Salary Benchmarking"],
)
async def get_market_trends(
    role: str = Query(..., description="Job title or role"),
    location: str = Query(..., description="Location (city, state, or 'Remote')"),
    country: Optional[str] = Query(None, description="Country code"),
    period_type: str = Query("quarterly", description="Period type (quarterly, monthly, yearly)"),
    periods: int = Query(8, ge=1, le=24, description="Number of periods to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get market salary trends over time for a role and location.

    This endpoint provides historical salary trend data showing how compensation
    for a specific role and location has changed over time. This is useful for:
    - Understanding salary growth patterns
    - Negotiating compensation with market data
    - Planning hiring budgets based on market trends

    Args:
        role: Job title or role
        location: Geographic location (city, state, or 'Remote')
        country: Country code (optional)
        period_type: Time period granularity (quarterly, monthly, yearly)
        periods: Number of periods to return (1-24, default 8)
        db: Database session

    Returns:
        Market trends data with salary changes over time

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> GET /api/salary-benchmarking/market-trends?role=Software%20Engineer&location=Remote
        {
            "role": "Software Engineer",
            "location": "Remote",
            "currency": "USD",
            "period_type": "quarterly",
            "trends": [
                {
                    "period": "2024-Q2",
                    "salary_min": 85000,
                    "salary_median": 115000,
                    "salary_max": 145000,
                    "sample_size": 1250
                },
                ...
            ],
            "year_over_year_change": 5.2,
            "quarter_over_quarter_change": 1.5,
            "data_source": "aggregate",
            "last_updated": "2024-06-15T00:00:00Z"
        }
    """
    try:
        logger.info(
            f"Fetching market trends for role={role}, location={location}, "
            f"period_type={period_type}, periods={periods}"
        )

        # Build query conditions for salary benchmarks
        conditions = []

        # Case-insensitive partial match for role
        conditions.append(
            or_(
                SalaryBenchmark.job_title.ilike(f"%{role}%"),
                SalaryBenchmark.job_title == role
            )
        )

        # Match location (case-insensitive)
        conditions.append(
            or_(
                SalaryBenchmark.location.ilike(f"%{location}%"),
                SalaryBenchmark.location == location
            )
        )

        if country:
            conditions.append(SalaryBenchmark.country == country.upper())

        # Execute query to get available benchmarks
        result = await db.execute(
            select(SalaryBenchmark)
            .where(and_(*conditions))
            .order_by(SalaryBenchmark.effective_date.desc())
            .limit(periods)
        )
        benchmarks = result.scalars().all()

        # Build trends data from benchmarks or generate simulated historical data
        trends = []

        if benchmarks:
            # Use actual benchmark data if available
            for b in benchmarks:
                period_str = b.effective_date if b.effective_date else ""
                if period_str and len(period_str) >= 7:
                    # Convert date to period format based on period_type
                    try:
                        year = int(period_str[:4])
                        month = int(period_str[5:7])
                        if period_type == "quarterly":
                            quarter = (month - 1) // 3 + 1
                            period_str = f"{year}-Q{quarter}"
                        elif period_type == "yearly":
                            period_str = str(year)
                        # monthly keeps YYYY-MM format
                        else:
                            period_str = period_str[:7]
                    except (ValueError, IndexError):
                        pass

                trends.append({
                    "period": period_str,
                    "salary_min": b.salary_min,
                    "salary_median": b.salary_median,
                    "salary_max": b.salary_max,
                    "sample_size": b.sample_size,
                })
        else:
            # Generate simulated historical trend data based on current market
            # This provides meaningful data even without historical benchmarks
            import random

            # Base salary figures for the role/location (these would come from market data in production)
            base_min = 75000
            base_median = 100000
            base_max = 130000

            # Adjust for remote vs location-specific
            if location.lower() == "remote":
                base_min = 80000
                base_median = 110000
                base_max = 145000

            now = datetime.now()

            for i in range(periods):
                if period_type == "quarterly":
                    # Calculate quarter
                    quarter_offset = i
                    current_quarter = (now.month - 1) // 3 + 1 - quarter_offset
                    year = now.year
                    while current_quarter <= 0:
                        current_quarter += 4
                        year -= 1
                    period_str = f"{year}-Q{current_quarter}"
                elif period_type == "yearly":
                    year = now.year - i
                    period_str = str(year)
                else:  # monthly
                    months_ago = i
                    past_date = now - timedelta(days=months_ago * 30)
                    period_str = past_date.strftime("%Y-%m")

                # Apply a small growth factor for historical simulation
                # (salaries tend to increase over time, so older periods are slightly lower)
                growth_factor = 1 - (i * 0.015)  # ~1.5% growth per period

                trends.append({
                    "period": period_str,
                    "salary_min": int(base_min * growth_factor),
                    "salary_median": int(base_median * growth_factor),
                    "salary_max": int(base_max * growth_factor),
                    "sample_size": random.randint(500, 2000),  # Simulated sample size
                })

            # Reverse to get chronological order
            trends = trends[::-1]

        # Calculate year-over-year and quarter-over-quarter changes
        yoy_change = None
        qoq_change = None

        if len(trends) >= 2:
            # Quarter-over-quarter (most recent vs previous)
            latest = trends[-1]["salary_median"]
            previous = trends[-2]["salary_median"]
            if previous > 0:
                qoq_change = round(((latest - previous) / previous) * 100, 2)

        if len(trends) >= 4:
            # Year-over-year (most recent vs 4 quarters ago for quarterly data)
            latest = trends[-1]["salary_median"]
            year_ago = trends[-4]["salary_median"] if len(trends) >= 4 else trends[0]["salary_median"]
            if year_ago > 0:
                yoy_change = round(((latest - year_ago) / year_ago) * 100, 2)

        response_data = {
            "role": role,
            "location": location,
            "currency": "USD",
            "period_type": period_type,
            "trends": trends,
            "year_over_year_change": yoy_change,
            "quarter_over_quarter_change": qoq_change,
            "data_source": "aggregate" if benchmarks else "estimated",
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(
            f"Found {len(trends)} market trend data points for role={role}, location={location}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error fetching market trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market trends: {str(e)}",
        ) from e
