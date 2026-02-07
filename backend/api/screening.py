"""
Automated Resume Screening API endpoints

Provides endpoints for:
- Managing screening rules for vacancies (CRUD)
- Triggering manual candidate screening
- Viewing screening results with tier-based filtering
- Accessing screening metrics and analytics
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.screening_service import get_screening_service, ScreeningService
from models.screening_rule import ScreeningRule
from models.screening_result import ScreeningResult
from models.resume import Resume
from models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ScreeningRuleCreate(BaseModel):
    """Request to create a screening rule."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    min_score_threshold: float = Field(50.0, ge=0, le=100, description="Minimum score threshold (0-100)")
    must_have_skills: List[str] = Field(default_factory=list, description="List of must-have skills")
    auto_reject_threshold: float = Field(30.0, ge=0, le=100, description="Auto-reject threshold (0-100)")
    auto_reject_with_notification: bool = Field(False, description="Send notification to rejected candidates")
    high_priority_threshold: float = Field(80.0, ge=0, le=100, description="High priority threshold (0-100)")
    rule_priority: int = Field(100, ge=1, description="Rule priority (lower = higher priority)")
    is_active: bool = Field(True, description="Whether the rule is active")


class ScreeningRuleUpdate(BaseModel):
    """Request to update a screening rule."""

    min_score_threshold: Optional[float] = Field(None, ge=0, le=100, description="Minimum score threshold (0-100)")
    must_have_skills: Optional[List[str]] = Field(None, description="List of must-have skills")
    auto_reject_threshold: Optional[float] = Field(None, ge=0, le=100, description="Auto-reject threshold (0-100)")
    auto_reject_with_notification: Optional[bool] = Field(None, description="Send notification to rejected candidates")
    high_priority_threshold: Optional[float] = Field(None, ge=0, le=100, description="High priority threshold (0-100)")
    rule_priority: Optional[int] = Field(None, ge=1, description="Rule priority (lower = higher priority)")
    is_active: Optional[bool] = Field(None, description="Whether the rule is active")


class ScreeningRuleResponse(BaseModel):
    """Response model for screening rule."""

    id: str = Field(..., description="Rule UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    min_score_threshold: float = Field(..., description="Minimum score threshold")
    must_have_skills: List[str] = Field(..., description="Must-have skills")
    auto_reject_threshold: float = Field(..., description="Auto-reject threshold")
    auto_reject_with_notification: bool = Field(..., description="Auto-reject with notification")
    high_priority_threshold: float = Field(..., description="High priority threshold")
    rule_priority: int = Field(..., description="Rule priority")
    is_active: bool = Field(..., description="Whether rule is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ScreeningRequest(BaseModel):
    """Request to screen a candidate for a vacancy."""

    force_rescreen: bool = Field(False, description="Force re-screening even if already screened")


class ScreeningResultResponse(BaseModel):
    """Response model for screening result."""

    id: str = Field(..., description="Screening result UUID")
    resume_id: str = Field(..., description="Resume UUID")
    vacancy_id: str = Field(..., description="Vacancy UUID")
    screening_rule_id: Optional[str] = Field(None, description="Applied screening rule UUID")
    tier: str = Field(..., description="Assigned tier (HIGH_PRIORITY, REVIEW, REJECT)")
    score_applied: float = Field(..., description="Score applied during screening")
    rejection_reasons: Optional[List[str]] = Field(None, description="Rejection reasons")
    screening_timestamp: str = Field(..., description="Screening timestamp")
    auto_response_sent: bool = Field(..., description="Auto-response sent")
    review_reminder_sent: bool = Field(..., description="Review reminder sent")
    created_at: str = Field(..., description="Creation timestamp")


class ScreeningResultsListResponse(BaseModel):
    """Response model for screening results list."""

    vacancy_id: str = Field(..., description="Vacancy UUID")
    tier: Optional[str] = Field(None, description="Filter by tier")
    total_results: int = Field(..., description="Total number of results")
    results: List[ScreeningResultResponse] = Field(..., description="List of screening results")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error detail")


# Metrics and Analytics Models
class ScreeningVolumeMetrics(BaseModel):
    """Screening volume metrics."""

    total_screenings: int = Field(..., description="Total number of screenings performed")
    screenings_this_month: int = Field(..., description="Screenings performed this month")
    screenings_this_week: int = Field(..., description="Screenings performed this week")
    screening_rate_avg: float = Field(..., description="Average screening rate (screenings per day)")


class TierDistributionMetrics(BaseModel):
    """Tier distribution metrics."""

    high_priority_count: int = Field(..., description="Number of candidates in HIGH_PRIORITY tier")
    high_priority_percentage: float = Field(..., description="Percentage of candidates in HIGH_PRIORITY tier (0-100)")
    review_count: int = Field(..., description="Number of candidates in REVIEW tier")
    review_percentage: float = Field(..., description="Percentage of candidates in REVIEW tier (0-100)")
    reject_count: int = Field(..., description="Number of candidates in REJECT tier")
    reject_percentage: float = Field(..., description="Percentage of candidates in REJECT tier (0-100)")


class ScoreMetrics(BaseModel):
    """Screening score performance metrics."""

    average_score: float = Field(..., description="Average screening score (0-100)")
    median_score: float = Field(..., description="Median screening score (0-100)")
    min_score: float = Field(..., description="Minimum screening score")
    max_score: float = Field(..., description="Maximum screening score")
    percentile_25: float = Field(..., description="25th percentile screening score")
    percentile_75: float = Field(..., description="75th percentile screening score")


class AutoRejectMetrics(BaseModel):
    """Auto-rejection statistics."""

    total_auto_rejected: int = Field(..., description="Total number of auto-rejected candidates")
    auto_rejection_rate: float = Field(..., description="Auto-rejection rate (0-1)")
    notifications_sent: int = Field(..., description="Number of rejection notifications sent")
    notification_rate: float = Field(..., description="Notification send rate (0-1)")


class ScreeningMetricsResponse(BaseModel):
    """Response model for screening metrics."""

    volume: ScreeningVolumeMetrics = Field(..., description="Screening volume metrics")
    tier_distribution: TierDistributionMetrics = Field(..., description="Tier distribution metrics")
    scores: ScoreMetrics = Field(..., description="Score performance metrics")
    auto_reject: AutoRejectMetrics = Field(..., description="Auto-rejection statistics")


@router.post(
    "/rules",
    response_model=ScreeningRuleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Screening"],
)
async def create_screening_rule(
    request: ScreeningRuleCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new screening rule for a vacancy.

    This endpoint creates a new screening rule with configurable thresholds
    and must-have skills. The rule will be used to automatically categorize
    candidates into tiers (High Priority, Review, Reject).

    Thresholds logic:
    - high_priority_threshold: Score above which candidates are marked HIGH_PRIORITY
    - min_score_threshold: Minimum score to pass screening (REVIEW tier)
    - auto_reject_threshold: Score below which candidates are auto-rejected
    - must_have_skills: Hard filter - candidates missing these skills are rejected regardless of score

    Args:
        request: Screening rule creation request
        db: Database session

    Returns:
        Created screening rule

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(422): If validation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "vacancy_id": "vac-123-abc",
        ...     "min_score_threshold": 50.0,
        ...     "auto_reject_threshold": 30.0,
        ...     "high_priority_threshold": 80.0,
        ...     "must_have_skills": ["python", "sql"],
        ...     "auto_reject_with_notification": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/screening/rules",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "rule-456-def",
            "vacancy_id": "vac-123-abc",
            "min_score_threshold": 50.0,
            ...
        }
    """
    try:
        logger.info(f"Creating screening rule for vacancy {request.vacancy_id}")

        # Parse vacancy UUID
        try:
            vacancy_uuid = UUID(request.vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vacancy UUID format: {e}",
            )

        # Verify vacancy exists
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy not found: {request.vacancy_id}",
            )

        # Validate thresholds: high_priority >= min_score >= auto_reject
        if request.high_priority_threshold < request.min_score_threshold:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="high_priority_threshold must be >= min_score_threshold",
            )

        if request.min_score_threshold < request.auto_reject_threshold:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min_score_threshold must be >= auto_reject_threshold",
            )

        # Create screening rule
        rule = ScreeningRule(
            vacancy_id=vacancy_uuid,
            min_score_threshold=request.min_score_threshold,
            auto_reject_threshold=request.auto_reject_threshold,
            high_priority_threshold=request.high_priority_threshold,
            must_have_skills=request.must_have_skills,
            auto_reject_with_notification=request.auto_reject_with_notification,
            rule_priority=request.rule_priority,
            is_active=request.is_active,
        )

        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        logger.info(f"Created screening rule {rule.id} for vacancy {request.vacancy_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(rule.id),
                "vacancy_id": str(rule.vacancy_id),
                "min_score_threshold": float(rule.min_score_threshold),
                "must_have_skills": rule.must_have_skills or [],
                "auto_reject_threshold": float(rule.auto_reject_threshold),
                "auto_reject_with_notification": rule.auto_reject_with_notification,
                "high_priority_threshold": float(rule.high_priority_threshold),
                "rule_priority": int(rule.rule_priority),
                "is_active": rule.is_active,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating screening rule: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create screening rule: {str(e)}",
        )


@router.get(
    "/rules",
    response_model=List[ScreeningRuleResponse],
    status_code=status.HTTP_200_OK,
    tags=["Screening"],
)
async def list_screening_rules(
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy UUID"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List screening rules with optional filtering.

    Returns a list of screening rules, optionally filtered by vacancy
    and/or active status. Results are ordered by rule priority.

    Args:
        vacancy_id: Optional vacancy UUID to filter by
        is_active: Optional active status filter (default: True)
        db: Database session

    Returns:
        List of screening rules

    Examples:
        >>> import requests
        >>> # Get all active rules for a vacancy
        >>> response = requests.get(
        ...     "http://localhost:8000/api/screening/rules?vacancy_id=vac-123-abc&is_active=true"
        ... )
        >>> response.json()
        [
            {
                "id": "rule-456-def",
                "vacancy_id": "vac-123-abc",
                "min_score_threshold": 50.0,
                ...
            }
        ]
    """
    try:
        logger.info(f"Listing screening rules - vacancy_id: {vacancy_id}, is_active: {is_active}")

        # Build query
        query = select(ScreeningRule)

        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(ScreeningRule.vacancy_id == vacancy_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid vacancy UUID format: {vacancy_id}",
                )

        if is_active is not None:
            query = query.where(ScreeningRule.is_active == is_active)

        # Order by priority (lower number = higher priority)
        query = query.order_by(ScreeningRule.rule_priority)

        result = await db.execute(query)
        rules = result.scalars().all()

        rules_data = [
            {
                "id": str(rule.id),
                "vacancy_id": str(rule.vacancy_id),
                "min_score_threshold": float(rule.min_score_threshold),
                "must_have_skills": rule.must_have_skills or [],
                "auto_reject_threshold": float(rule.auto_reject_threshold),
                "auto_reject_with_notification": rule.auto_reject_with_notification,
                "high_priority_threshold": float(rule.high_priority_threshold),
                "rule_priority": int(rule.rule_priority),
                "is_active": rule.is_active,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat(),
            }
            for rule in rules
        ]

        logger.info(f"Found {len(rules_data)} screening rules")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=rules_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing screening rules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list screening rules: {str(e)}",
        )


@router.get(
    "/rules/{vacancy_id}",
    response_model=List[ScreeningRuleResponse],
    status_code=status.HTTP_200_OK,
    tags=["Screening"],
)
async def get_screening_rules_for_vacancy(
    vacancy_id: str,
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get screening rules for a specific vacancy.

    Returns all screening rules for the specified vacancy, optionally
    filtered by active status. Results are ordered by rule priority.

    Args:
        vacancy_id: Vacancy UUID
        is_active: Optional active status filter (default: True)
        db: Database session

    Returns:
        List of screening rules for the vacancy

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(422): If UUID format is invalid
    """
    try:
        logger.info(f"Getting screening rules for vacancy {vacancy_id}")

        # Parse vacancy UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vacancy UUID format: {e}",
            )

        # Verify vacancy exists
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy not found: {vacancy_id}",
            )

        # Build query
        query = select(ScreeningRule).where(ScreeningRule.vacancy_id == vacancy_uuid)

        if is_active is not None:
            query = query.where(ScreeningRule.is_active == is_active)

        query = query.order_by(ScreeningRule.rule_priority)

        result = await db.execute(query)
        rules = result.scalars().all()

        rules_data = [
            {
                "id": str(rule.id),
                "vacancy_id": str(rule.vacancy_id),
                "min_score_threshold": float(rule.min_score_threshold),
                "must_have_skills": rule.must_have_skills or [],
                "auto_reject_threshold": float(rule.auto_reject_threshold),
                "auto_reject_with_notification": rule.auto_reject_with_notification,
                "high_priority_threshold": float(rule.high_priority_threshold),
                "rule_priority": int(rule.rule_priority),
                "is_active": rule.is_active,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat(),
            }
            for rule in rules
        ]

        logger.info(f"Found {len(rules_data)} screening rules for vacancy {vacancy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=rules_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screening rules for vacancy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get screening rules: {str(e)}",
        )


@router.put(
    "/rules/{rule_id}",
    response_model=ScreeningRuleResponse,
    status_code=status.HTTP_200_OK,
    tags=["Screening"],
)
async def update_screening_rule(
    rule_id: str,
    request: ScreeningRuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing screening rule.

    Updates the specified screening rule with the provided values.
    Only the fields specified in the request will be updated.

    Args:
        rule_id: Rule UUID
        request: Screening rule update request
        db: Database session

    Returns:
        Updated screening rule

    Raises:
        HTTPException(404): If rule not found
        HTTPException(422): If validation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "min_score_threshold": 55.0,
        ...     "high_priority_threshold": 85.0
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/screening/rules/rule-456-def",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "rule-456-def",
            "min_score_threshold": 55.0,
            ...
        }
    """
    try:
        logger.info(f"Updating screening rule {rule_id}")

        # Parse rule UUID
        try:
            rule_uuid = UUID(rule_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid rule UUID format: {e}",
            )

        # Get existing rule
        query = select(ScreeningRule).where(ScreeningRule.id == rule_uuid)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Screening rule not found: {rule_id}",
            )

        # Update fields
        update_data = request.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(rule, field, value)

        # Validate thresholds if both are being updated
        current_min = float(rule.min_score_threshold)
        current_auto = float(rule.auto_reject_threshold)
        current_high = float(rule.high_priority_threshold)

        if current_high < current_min:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="high_priority_threshold must be >= min_score_threshold",
            )

        if current_min < current_auto:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min_score_threshold must be >= auto_reject_threshold",
            )

        rule.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(rule)

        logger.info(f"Updated screening rule {rule_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(rule.id),
                "vacancy_id": str(rule.vacancy_id),
                "min_score_threshold": float(rule.min_score_threshold),
                "must_have_skills": rule.must_have_skills or [],
                "auto_reject_threshold": float(rule.auto_reject_threshold),
                "auto_reject_with_notification": rule.auto_reject_with_notification,
                "high_priority_threshold": float(rule.high_priority_threshold),
                "rule_priority": int(rule.rule_priority),
                "is_active": rule.is_active,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screening rule: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update screening rule: {str(e)}",
        )


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Screening"],
)
async def delete_screening_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Deactivate a screening rule.

    Soft-deletes the screening rule by setting is_active to False.
    The rule is not removed from the database but will no longer be used.

    Args:
        rule_id: Rule UUID
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If rule not found
        HTTPException(422): If UUID format is invalid

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/screening/rules/rule-456-def"
        ... )
        >>> response.status_code
        204
    """
    try:
        logger.info(f"Deactivating screening rule {rule_id}")

        # Parse rule UUID
        try:
            rule_uuid = UUID(rule_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid rule UUID format: {e}",
            )

        # Get existing rule
        query = select(ScreeningRule).where(ScreeningRule.id == rule_uuid)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Screening rule not found: {rule_id}",
            )

        # Soft delete by setting is_active to False
        rule.is_active = False
        rule.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Deactivated screening rule {rule_id}")

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting screening rule: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete screening rule: {str(e)}",
        )


@router.post(
    "/screen/{resume_id}/{vacancy_id}",
    response_model=ScreeningResultResponse,
    status_code=status.HTTP_200_OK,
    tags=["Screening"],
)
async def screen_candidate(
    resume_id: str,
    vacancy_id: str,
    request: ScreeningRequest = ScreeningRequest(),
    db: AsyncSession = Depends(get_db),
    screening_service: ScreeningService = Depends(get_screening_service),
) -> JSONResponse:
    """
    Manually trigger screening for a candidate.

    Applies screening rules to categorize a candidate into tiers
    (High Priority, Review, Reject). If force_rescreen is True,
    will re-screen even if a screening result already exists.

    The screening process:
    1. Retrieves active screening rules for the vacancy
    2. Gets candidate's ranking score from CandidateRank
    3. Checks must-have skills (hard filter)
    4. Calculates tier based on score thresholds
    5. Stores ScreeningResult in database

    Args:
        resume_id: Resume UUID
        vacancy_id: Vacancy UUID
        request: Screening request with optional force_rescreen flag
        db: Database session
        screening_service: Screening service

    Returns:
        Screening result with tier and score

    Raises:
        HTTPException(404): If resume or vacancy not found
        HTTPException(422): If UUID format is invalid

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/screening/screen/resume-123/vac-456",
        ...     json={"force_rescreen": false}
        ... )
        >>> response.json()
        {
            "id": "result-789",
            "resume_id": "resume-123",
            "vacancy_id": "vac-456",
            "tier": "HIGH_PRIORITY",
            "score_applied": 85.5,
            ...
        }
    """
    try:
        logger.info(f"Screening candidate {resume_id} for vacancy {vacancy_id}")

        # Parse UUIDs
        try:
            resume_uuid = UUID(resume_id)
            vacancy_uuid = UUID(vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Check if screening result already exists
        if not request.force_rescreen:
            existing_query = select(ScreeningResult).where(
                and_(
                    ScreeningResult.resume_id == resume_uuid,
                    ScreeningResult.vacancy_id == vacancy_uuid,
                )
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                logger.info(f"Screening result already exists for {resume_id}/{vacancy_id}")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "id": str(existing.id),
                        "resume_id": str(existing.resume_id),
                        "vacancy_id": str(existing.vacancy_id),
                        "screening_rule_id": str(existing.screening_rule_id) if existing.screening_rule_id else None,
                        "tier": existing.tier,
                        "score_applied": float(existing.score_applied),
                        "rejection_reasons": existing.rejection_reasons,
                        "screening_timestamp": existing.screening_timestamp.isoformat(),
                        "auto_response_sent": existing.auto_response_sent,
                        "review_reminder_sent": existing.review_reminder_sent,
                        "created_at": existing.created_at.isoformat(),
                    },
                )

        # Apply screening rules
        outcome = await screening_service.apply_screening_rules(
            resume_uuid,
            vacancy_uuid,
        )

        # Get the created screening result
        result_query = select(ScreeningResult).where(
            and_(
                ScreeningResult.resume_id == resume_uuid,
                ScreeningResult.vacancy_id == vacancy_uuid,
            )
        ).order_by(ScreeningResult.created_at.desc())

        result_data = await db.execute(result_query)
        screening_result = result_data.scalar_one()

        logger.info(
            f"Screening completed - tier: {screening_result.tier}, "
            f"score: {screening_result.score_applied:.2f}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(screening_result.id),
                "resume_id": str(screening_result.resume_id),
                "vacancy_id": str(screening_result.vacancy_id),
                "screening_rule_id": str(screening_result.screening_rule_id) if screening_result.screening_rule_id else None,
                "tier": screening_result.tier,
                "score_applied": float(screening_result.score_applied),
                "rejection_reasons": screening_result.rejection_reasons,
                "screening_timestamp": screening_result.screening_timestamp.isoformat(),
                "auto_response_sent": screening_result.auto_response_sent,
                "review_reminder_sent": screening_result.review_reminder_sent,
                "created_at": screening_result.created_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Screening validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error during screening: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening failed: {str(e)}",
        )


@router.get(
    "/results/{vacancy_id}",
    response_model=ScreeningResultsListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Screening"],
)
async def get_screening_results(
    vacancy_id: str,
    tier: Optional[str] = Query(None, description="Filter by tier (HIGH_PRIORITY, REVIEW, REJECT)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get screening results for a vacancy with optional filtering.

    Returns screening results for the specified vacancy, optionally
    filtered by tier. Results are ordered by screening timestamp (most recent first).

    Args:
        vacancy_id: Vacancy UUID
        tier: Optional tier filter (HIGH_PRIORITY, REVIEW, REJECT)
        limit: Maximum results to return (default: 100, max: 500)
        offset: Offset for pagination (default: 0)
        db: Database session

    Returns:
        List of screening results with metadata

    Raises:
        HTTPException(404): If vacancy not found
        HTTPException(422): If UUID or tier format is invalid

    Examples:
        >>> import requests
        >>> # Get all HIGH_PRIORITY candidates for a vacancy
        >>> response = requests.get(
        ...     "http://localhost:8000/api/screening/results/vac-123?tier=HIGH_PRIORITY&limit=50"
        ... )
        >>> response.json()
        {
            "vacancy_id": "vac-123",
            "tier": "HIGH_PRIORITY",
            "total_results": 15,
            "results": [...]
        }
    """
    try:
        logger.info(f"Getting screening results for vacancy {vacancy_id}, tier: {tier}")

        # Parse vacancy UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vacancy UUID format: {e}",
            )

        # Validate tier if provided
        valid_tiers = ["HIGH_PRIORITY", "REVIEW", "REJECT"]
        if tier and tier not in valid_tiers:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
            )

        # Verify vacancy exists
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy not found: {vacancy_id}",
            )

        # Build query
        query = select(ScreeningResult).where(ScreeningResult.vacancy_id == vacancy_uuid)

        if tier:
            query = query.where(ScreeningResult.tier == tier)

        # Get total count
        count_query = select(func.count()).select_from(
            select(ScreeningResult.id).where(
                and_(
                    ScreeningResult.vacancy_id == vacancy_uuid,
                    ScreeningResult.tier == tier if tier else True,
                )
            ).subquery()
        )
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Order by screening timestamp (most recent first)
        query = query.order_by(ScreeningResult.screening_timestamp.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        results = result.scalars().all()

        results_data = [
            {
                "id": str(result.id),
                "resume_id": str(result.resume_id),
                "vacancy_id": str(result.vacancy_id),
                "screening_rule_id": str(result.screening_rule_id) if result.screening_rule_id else None,
                "tier": result.tier,
                "score_applied": float(result.score_applied),
                "rejection_reasons": result.rejection_reasons,
                "screening_timestamp": result.screening_timestamp.isoformat(),
                "auto_response_sent": result.auto_response_sent,
                "review_reminder_sent": result.review_reminder_sent,
                "created_at": result.created_at.isoformat(),
            }
            for result in results
        ]

        logger.info(f"Found {len(results_data)} screening results for vacancy {vacancy_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "vacancy_id": vacancy_id,
                "tier": tier,
                "total_results": total_count,
                "results": results_data,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screening results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get screening results: {str(e)}",
        )


@router.get(
    "/metrics",
    response_model=ScreeningMetricsResponse,
    tags=["Screening"],
)
async def get_screening_metrics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy UUID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get screening metrics and analytics.

    This endpoint provides comprehensive metrics about the screening process,
    including screening volume, tier distribution, score performance, and
    auto-rejection statistics. These metrics help recruitment managers evaluate
    the effectiveness of their screening rules and optimize their hiring process.

    Metrics include:
    - Volume: Total screenings, recent activity, screening rate
    - Tier distribution: Breakdown of candidates by tier (HIGH_PRIORITY, REVIEW, REJECT)
    - Scores: Statistical analysis of screening scores (avg, median, percentiles)
    - Auto-reject: Statistics on auto-rejected candidates and notifications

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)
        vacancy_id: Optional vacancy UUID to filter metrics by
        db: Database session

    Returns:
        JSON response with comprehensive screening metrics

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(422): If vacancy UUID format is invalid
        HTTPException(500): If metrics retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/screening/metrics")
        >>> response.json()
        {
            "volume": {
                "total_screenings": 1250,
                "screenings_this_month": 180,
                "screenings_this_week": 42,
                "screening_rate_avg": 8.5
            },
            "tier_distribution": {
                "high_priority_count": 375,
                "high_priority_percentage": 30.0,
                "review_count": 500,
                "review_percentage": 40.0,
                "reject_count": 375,
                "reject_percentage": 30.0
            },
            "scores": {
                "average_score": 62.5,
                "median_score": 65.0,
                "min_score": 15.0,
                "max_score": 98.0,
                "percentile_25": 45.0,
                "percentile_75": 80.0
            },
            "auto_reject": {
                "total_auto_rejected": 250,
                "auto_rejection_rate": 0.20,
                "notifications_sent": 180,
                "notification_rate": 0.72
            }
        }
    """
    try:
        logger.info(
            f"Fetching screening metrics - start_date: {start_date}, "
            f"end_date: {end_date}, vacancy_id: {vacancy_id}"
        )

        # Build base query
        query = select(ScreeningResult)

        # Apply vacancy filter if provided
        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(ScreeningResult.vacancy_id == vacancy_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid vacancy UUID format: {vacancy_id}",
                )

        # Apply date filters if provided
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.where(ScreeningResult.screening_timestamp >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.where(ScreeningResult.screening_timestamp <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                )

        # Get all screening results
        result = await db.execute(query)
        all_screenings = result.scalars().all()

        # If no screenings found, return empty metrics
        if not all_screenings:
            logger.info("No screening results found")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "volume": {
                        "total_screenings": 0,
                        "screenings_this_month": 0,
                        "screenings_this_week": 0,
                        "screening_rate_avg": 0.0,
                    },
                    "tier_distribution": {
                        "high_priority_count": 0,
                        "high_priority_percentage": 0.0,
                        "review_count": 0,
                        "review_percentage": 0.0,
                        "reject_count": 0,
                        "reject_percentage": 0.0,
                    },
                    "scores": {
                        "average_score": 0.0,
                        "median_score": 0.0,
                        "min_score": 0.0,
                        "max_score": 0.0,
                        "percentile_25": 0.0,
                        "percentile_75": 0.0,
                    },
                    "auto_reject": {
                        "total_auto_rejected": 0,
                        "auto_rejection_rate": 0.0,
                        "notifications_sent": 0,
                        "notification_rate": 0.0,
                    },
                },
            )

        # Calculate volume metrics
        total_screenings = len(all_screenings)

        # Calculate screenings this month and week
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        screenings_this_month = sum(
            1 for s in all_screenings if s.screening_timestamp >= month_start
        )
        screenings_this_week = sum(
            1 for s in all_screenings if s.screening_timestamp >= week_start
        )

        # Calculate screening rate (screenings per day)
        if all_screenings:
            earliest_timestamp = min(s.screening_timestamp for s in all_screenings)
            days_active = max(1, (now - earliest_timestamp).days)
            screening_rate_avg = total_screenings / days_active
        else:
            screening_rate_avg = 0.0

        # Calculate tier distribution
        high_priority_count = sum(1 for s in all_screenings if s.tier == "HIGH_PRIORITY")
        review_count = sum(1 for s in all_screenings if s.tier == "REVIEW")
        reject_count = sum(1 for s in all_screenings if s.tier == "REJECT")

        high_priority_percentage = (high_priority_count / total_screenings * 100) if total_screenings > 0 else 0.0
        review_percentage = (review_count / total_screenings * 100) if total_screenings > 0 else 0.0
        reject_percentage = (reject_count / total_screenings * 100) if total_screenings > 0 else 0.0

        # Calculate score metrics
        scores = [float(s.score_applied) for s in all_screenings]
        scores_sorted = sorted(scores)

        average_score = sum(scores) / len(scores) if scores else 0.0
        median_score = scores_sorted[len(scores_sorted) // 2] if scores_sorted else 0.0
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0

        # Calculate percentiles
        percentile_25_idx = int(len(scores_sorted) * 0.25)
        percentile_75_idx = int(len(scores_sorted) * 0.75)
        percentile_25 = scores_sorted[percentile_25_idx] if len(scores_sorted) > percentile_25_idx else 0.0
        percentile_75 = scores_sorted[percentile_75_idx] if len(scores_sorted) > percentile_75_idx else 0.0

        # Calculate auto-reject metrics
        # Auto-rejected candidates are those with low scores or missing must-have skills
        # We'll identify them by checking if they have rejection reasons related to threshold/skills
        total_auto_rejected = sum(
            1 for s in all_screenings
            if s.tier == "REJECT" and s.rejection_reasons
        )
        auto_rejection_rate = total_auto_rejected / total_screenings if total_screenings > 0 else 0.0

        # Count notifications sent
        notifications_sent = sum(
            1 for s in all_screenings if s.auto_response_sent
        )
        notification_rate = notifications_sent / total_auto_rejected if total_auto_rejected > 0 else 0.0

        response_data = {
            "volume": {
                "total_screenings": total_screenings,
                "screenings_this_month": screenings_this_month,
                "screenings_this_week": screenings_this_week,
                "screening_rate_avg": round(screening_rate_avg, 1),
            },
            "tier_distribution": {
                "high_priority_count": high_priority_count,
                "high_priority_percentage": round(high_priority_percentage, 1),
                "review_count": review_count,
                "review_percentage": round(review_percentage, 1),
                "reject_count": reject_count,
                "reject_percentage": round(reject_percentage, 1),
            },
            "scores": {
                "average_score": round(average_score, 1),
                "median_score": round(median_score, 1),
                "min_score": round(min_score, 1),
                "max_score": round(max_score, 1),
                "percentile_25": round(percentile_25, 1),
                "percentile_75": round(percentile_75, 1),
            },
            "auto_reject": {
                "total_auto_rejected": total_auto_rejected,
                "auto_rejection_rate": round(auto_rejection_rate, 3),
                "notifications_sent": notifications_sent,
                "notification_rate": round(notification_rate, 3),
            },
        }

        logger.info(
            f"Screening metrics retrieved successfully - "
            f"{total_screenings} total screenings, "
            f"{high_priority_count} high priority, "
            f"{review_count} review, "
            f"{reject_count} rejected"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving screening metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve screening metrics: {str(e)}",
        ) from e
