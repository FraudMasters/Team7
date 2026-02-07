"""
Automated Resume Screening Service

This module provides rule-based candidate screening that applies filters,
ML scoring thresholds, and recruiter feedback patterns to automatically
categorize candidates into tiers (High Priority, Review, Reject).

Features:
- Per-vacancy screening rules with configurable thresholds
- Must-have skills as hard filters
- Automated tier categorization (HIGH_PRIORITY, REVIEW, REJECT)
- Integration with existing ranking scores from CandidateRank
- Rejection reason tracking
- Metrics tracking for automation effectiveness

The service builds on existing CandidateRank scores and applies
rule-based filters on top to determine candidate tier.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    CandidateRank,
    JobVacancy,
    Resume,
    ResumeAnalysis,
    ScreeningResult,
    ScreeningRule,
)

logger = logging.getLogger(__name__)


@dataclass
class ScreeningOutcome:
    """
    Result of applying screening rules to a candidate.

    Attributes:
        resume_id: Resume UUID
        vacancy_id: JobVacancy UUID
        tier: Assigned tier (HIGH_PRIORITY, REVIEW, REJECT)
        score_applied: The ranking score used for screening (0-100)
        screening_rule_id: The rule that was applied
        rejection_reasons: List of reasons for rejection (if tier is REJECT)
        screening_timestamp: When screening was performed
        passed_must_have_skills: Whether candidate passed must-have skills check
    """

    resume_id: UUID
    vacancy_id: UUID
    tier: str
    score_applied: float
    screening_rule_id: Optional[UUID]
    rejection_reasons: List[str]
    screening_timestamp: datetime
    passed_must_have_skills: bool


@dataclass
class ScreeningMetrics:
    """
    Metrics tracking for screening automation effectiveness.

    Attributes:
        total_screened: Total number of candidates screened
        high_priority_count: Number of candidates marked as HIGH_PRIORITY
        review_count: Number of candidates marked as REVIEW
        auto_rejected_count: Number of candidates auto-rejected
        average_screening_time_seconds: Average time to screen a candidate
        rejection_reasons_distribution: Breakdown of rejection reasons
    """

    total_screened: int = 0
    high_priority_count: int = 0
    review_count: int = 0
    auto_rejected_count: int = 0
    average_screening_time_seconds: float = 0.0
    rejection_reasons_distribution: Dict[str, int] = None

    def __post_init__(self):
        if self.rejection_reasons_distribution is None:
            self.rejection_reasons_distribution = {}


class ScreeningService:
    """
    Service for automated candidate screening with rule-based filters.

    This service provides automated screening capabilities leveraging:
    - Per-vacancy screening rules with configurable thresholds
    - Must-have skills as hard filters
    - Existing ranking scores from CandidateRank model
    - Tier-based categorization for triage
    - Metrics tracking for automation effectiveness
    """

    # Tier constants
    TIER_HIGH_PRIORITY = "HIGH_PRIORITY"
    TIER_REVIEW = "REVIEW"
    TIER_REJECT = "REJECT"

    # Rejection reason constants
    REASON_BELOW_THRESHOLD = "below_threshold"
    REASON_MISSING_SKILLS = "missing_must_have_skills"
    REASON_NO_RANKING_SCORE = "no_ranking_score_available"

    def __init__(self, db: AsyncSession):
        """
        Initialize the screening service.

        Args:
            db: Database session for executing queries
        """
        self.db = db
        self._metrics = ScreeningMetrics()

    async def apply_screening_rules(
        self,
        resume_id: UUID,
        vacancy_id: UUID,
    ) -> ScreeningOutcome:
        """
        Apply screening rules to a candidate for a specific vacancy.

        This method:
        1. Retrieves active screening rules for the vacancy
        2. Gets the candidate's ranking score (or uses default)
        3. Checks must-have skills
        4. Calculates tier based on thresholds
        5. Stores ScreeningResult in database
        6. Updates metrics

        Args:
            resume_id: Resume UUID
            vacancy_id: JobVacancy UUID

        Returns:
            ScreeningOutcome with tier, score, and rejection reasons

        Raises:
            ValueError: If resume or vacancy not found
        """
        import time
        start_time = time.time()

        try:
            logger.info(
                f"Applying screening rules - resume_id: {resume_id}, "
                f"vacancy_id: {vacancy_id}"
            )

            # Get active screening rules for vacancy
            rules = await self.get_active_screening_rules(vacancy_id)

            if not rules:
                logger.warning(f"No active screening rules found for vacancy {vacancy_id}")
                # Use default thresholds
                rule = None
                min_threshold = 50.0
                auto_reject_threshold = 30.0
                high_priority_threshold = 80.0
                must_have_skills = []
            else:
                # Use highest priority rule (lowest priority number)
                rule = min(rules, key=lambda r: r.rule_priority)
                min_threshold = float(rule.min_score_threshold)
                auto_reject_threshold = float(rule.auto_reject_threshold)
                high_priority_threshold = float(rule.high_priority_threshold)
                must_have_skills = rule.must_have_skills or []

            # Get resume and analysis data
            resume = await self._get_resume(resume_id)
            analysis = await self._get_resume_analysis(resume_id)

            # Get ranking score
            rank_score = await self._get_ranking_score(resume_id, vacancy_id)

            # Convert to 0-100 scale if needed
            score_applied = rank_score * 100 if rank_score is not None else 0.0

            # Check must-have skills
            resume_data = await self._extract_resume_data(resume, analysis)
            passed_must_have_skills = self.check_must_have_skills(
                resume_data, must_have_skills
            )

            # Calculate tier
            tier, rejection_reasons = self.calculate_tier(
                score_applied,
                auto_reject_threshold,
                min_threshold,
                high_priority_threshold,
                passed_must_have_skills,
            )

            # Create ScreeningResult record
            screening_result = ScreeningResult(
                resume_id=resume_id,
                vacancy_id=vacancy_id,
                screening_rule_id=rule.id if rule else None,
                tier=tier,
                score_applied=score_applied,
                rejection_reasons=rejection_reasons if tier == self.TIER_REJECT else None,
                screening_timestamp=datetime.utcnow(),
            )

            self.db.add(screening_result)
            await self.db.commit()

            # Update metrics
            duration = time.time() - start_time
            self._update_metrics(tier, rejection_reasons, duration)

            logger.info(
                f"Screening completed - tier: {tier}, score: {score_applied:.2f}, "
                f"duration: {duration:.3f}s"
            )

            return ScreeningOutcome(
                resume_id=resume_id,
                vacancy_id=vacancy_id,
                tier=tier,
                score_applied=score_applied,
                screening_rule_id=rule.id if rule else None,
                rejection_reasons=rejection_reasons,
                screening_timestamp=datetime.utcnow(),
                passed_must_have_skills=passed_must_have_skills,
            )

        except Exception as e:
            logger.error(f"Error during screening: {e}", exc_info=True)
            await self.db.rollback()
            raise ValueError(f"Screening failed: {str(e)}") from e

    async def get_active_screening_rules(
        self, vacancy_id: UUID
    ) -> List[ScreeningRule]:
        """
        Get all active screening rules for a vacancy.

        Args:
            vacancy_id: JobVacancy UUID

        Returns:
            List of active ScreeningRule objects, ordered by priority
        """
        try:
            query = select(ScreeningRule).where(
                ScreeningRule.vacancy_id == vacancy_id,
                ScreeningRule.is_active == True,
            ).order_by(ScreeningRule.rule_priority)

            result = await self.db.execute(query)
            rules = result.scalars().all()

            return list(rules)

        except Exception as e:
            logger.error(f"Error fetching screening rules: {e}", exc_info=True)
            return []

    def check_must_have_skills(
        self, resume_data: Dict[str, Any], must_have_skills: List[str]
    ) -> bool:
        """
        Check if candidate has all must-have skills.

        This is a hard filter - if any must-have skill is missing,
        the candidate fails screening regardless of score.

        Args:
            resume_data: Dictionary with resume data including skills
            must_have_skills: List of required skill names

        Returns:
            True if all must-have skills are present, False otherwise
        """
        if not must_have_skills:
            # No must-have skills defined - pass by default
            return True

        resume_skills = resume_data.get("skills", [])

        if not resume_skills:
            # Resume has no skills - fail if must-have skills required
            return False

        # Convert to lowercase for case-insensitive comparison
        resume_skills_lower = [s.lower() for s in resume_skills]
        must_have_lower = [s.lower() for s in must_have_skills]

        # Check if all must-have skills are present
        for required_skill in must_have_lower:
            # Check for exact match or partial match (e.g., "python" matches "python 3")
            found = any(
                required_skill == skill or required_skill in skill or skill in required_skill
                for skill in resume_skills_lower
            )

            if not found:
                logger.debug(
                    f"Must-have skill not found: {required_skill} "
                    f"(resume has: {resume_skills_lower})"
                )
                return False

        return True

    def calculate_tier(
        self,
        score: float,
        auto_reject_threshold: float,
        min_threshold: float,
        high_priority_threshold: float,
        passed_must_have_skills: bool,
    ) -> tuple[str, List[str]]:
        """
        Calculate candidate tier based on score and thresholds.

        Tier logic:
        - HIGH_PRIORITY: score >= high_priority_threshold AND passed must-have skills
        - REVIEW: score >= min_threshold AND score < high_priority_threshold AND passed must-have skills
        - REJECT: score < auto_reject_threshold OR failed must-have skills

        Args:
            score: Candidate ranking score (0-100)
            auto_reject_threshold: Score below which auto-reject occurs
            min_threshold: Minimum score to pass screening
            high_priority_threshold: Score above which is high priority
            passed_must_have_skills: Whether candidate passed must-have skills check

        Returns:
            Tuple of (tier, rejection_reasons)
            tier: HIGH_PRIORITY, REVIEW, or REJECT
            rejection_reasons: List of reasons (empty if not rejected)
        """
        rejection_reasons = []

        # Check must-have skills first (hard filter)
        if not passed_must_have_skills:
            rejection_reasons.append(self.REASON_MISSING_SKILLS)
            return self.TIER_REJECT, rejection_reasons

        # Check auto-reject threshold
        if score < auto_reject_threshold:
            rejection_reasons.append(self.REASON_BELOW_THRESHOLD)
            return self.TIER_REJECT, rejection_reasons

        # Check if score meets minimum threshold
        if score < min_threshold:
            rejection_reasons.append(self.REASON_BELOW_THRESHOLD)
            return self.TIER_REJECT, rejection_reasons

        # Check for high priority
        if score >= high_priority_threshold:
            return self.TIER_HIGH_PRIORITY, []

        # Default to review tier
        return self.TIER_REVIEW, []

    def get_screening_metrics(self, include_aggregates: bool = True) -> Dict[str, Any]:
        """
        Get current screening metrics.

        This method returns comprehensive metrics about screening automation
        effectiveness, including tier distributions, rejection patterns,
        and performance timing.

        Args:
            include_aggregates: Whether to include calculated aggregate metrics

        Returns:
            Dictionary with screening metrics including totals,
            breakdowns by tier, rejection reasons, timing, and effectiveness rates

        Example:
            >>> service = ScreeningService(db)
            >>> metrics = service.get_screening_metrics()
            >>> print(f"Auto-reject rate: {metrics['automation_effectiveness']['auto_reject_rate']:.2%}")
        """
        try:
            metrics = {
                "total_screened": self._metrics.total_screened,
                "high_priority_count": self._metrics.high_priority_count,
                "review_count": self._metrics.review_count,
                "auto_rejected_count": self._metrics.auto_rejected_count,
                "average_screening_time_seconds": self._metrics.average_screening_time_seconds,
                "rejection_reasons_distribution": self._metrics.rejection_reasons_distribution.copy(),
            }

            # Calculate automation effectiveness
            if include_aggregates and self._metrics.total_screened > 0:
                metrics["automation_effectiveness"] = {
                    "high_priority_rate": self._metrics.high_priority_count
                    / self._metrics.total_screened,
                    "auto_reject_rate": self._metrics.auto_rejected_count
                    / self._metrics.total_screened,
                    "manual_review_rate": self._metrics.review_count
                    / self._metrics.total_screened,
                }
                metrics["tier_distribution"] = {
                    "high_priority_percentage": (
                        self._metrics.high_priority_count / self._metrics.total_screened * 100
                    ),
                    "review_percentage": (
                        self._metrics.review_count / self._metrics.total_screened * 100
                    ),
                    "rejected_percentage": (
                        self._metrics.auto_rejected_count / self._metrics.total_screened * 100
                    ),
                }
            else:
                metrics["automation_effectiveness"] = {
                    "high_priority_rate": 0.0,
                    "auto_reject_rate": 0.0,
                    "manual_review_rate": 0.0,
                }
                metrics["tier_distribution"] = {
                    "high_priority_percentage": 0.0,
                    "review_percentage": 0.0,
                    "rejected_percentage": 0.0,
                }

            logger.debug(
                f"Retrieved screening metrics: {metrics['total_screened']} total, "
                f"{metrics['auto_rejected_count']} auto-rejected"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error retrieving screening metrics: {e}", exc_info=True)
            return {
                "total_screened": 0,
                "high_priority_count": 0,
                "review_count": 0,
                "auto_rejected_count": 0,
                "average_screening_time_seconds": 0.0,
                "rejection_reasons_distribution": {},
                "automation_effectiveness": {
                    "high_priority_rate": 0.0,
                    "auto_reject_rate": 0.0,
                    "manual_review_rate": 0.0,
                },
                "tier_distribution": {
                    "high_priority_percentage": 0.0,
                    "review_percentage": 0.0,
                    "rejected_percentage": 0.0,
                },
            }

    def reset_metrics(self) -> None:
        """
        Reset all screening metrics to initial values.

        This method is useful for testing or when starting a new
        screening session.

        Example:
            >>> service = ScreeningService(db)
            >>> service.reset_metrics()
            >>> metrics = service.get_screening_metrics()
            >>> assert metrics['total_screened'] == 0
        """
        self._metrics = ScreeningMetrics()
        logger.debug("Screening metrics reset to initial values")

    def _update_metrics(
        self, tier: str, rejection_reasons: List[str], duration: float
    ) -> None:
        """
        Update screening metrics with latest result.

        Args:
            tier: Assigned tier
            rejection_reasons: List of rejection reasons
            duration: Time taken to screen (seconds)
        """
        self._metrics.total_screened += 1

        if tier == self.TIER_HIGH_PRIORITY:
            self._metrics.high_priority_count += 1
        elif tier == self.TIER_REVIEW:
            self._metrics.review_count += 1
        elif tier == self.TIER_REJECT:
            self._metrics.auto_rejected_count += 1

            # Track rejection reasons
            for reason in rejection_reasons:
                if reason not in self._metrics.rejection_reasons_distribution:
                    self._metrics.rejection_reasons_distribution[reason] = 0
                self._metrics.rejection_reasons_distribution[reason] += 1

        # Update average screening time
        if self._metrics.total_screened > 0:
            total_time = (
                self._metrics.average_screening_time_seconds * (self._metrics.total_screened - 1)
                + duration
            )
            self._metrics.average_screening_time_seconds = (
                total_time / self._metrics.total_screened
            )

    async def _get_resume(self, resume_id: UUID) -> Resume:
        """Get resume by ID."""
        query = select(Resume).where(Resume.id == resume_id)
        result = await self.db.execute(query)
        resume = result.scalar_one_or_none()

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        return resume

    async def _get_resume_analysis(self, resume_id: UUID) -> Optional[ResumeAnalysis]:
        """Get resume analysis by resume ID."""
        query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_ranking_score(
        self, resume_id: UUID, vacancy_id: UUID
    ) -> Optional[float]:
        """
        Get ranking score from CandidateRank model.

        Args:
            resume_id: Resume UUID
            vacancy_id: JobVacancy UUID

        Returns:
            Ranking score (0-1) or None if not available
        """
        try:
            query = select(CandidateRank).where(
                CandidateRank.resume_id == resume_id,
                CandidateRank.vacancy_id == vacancy_id,
            )
            result = await self.db.execute(query)
            rank = result.scalar_one_or_none()

            if rank:
                return float(rank.rank_score)

            logger.debug(
                f"No ranking score found for resume {resume_id}, vacancy {vacancy_id}"
            )
            return None

        except Exception as e:
            logger.error(f"Error fetching ranking score: {e}", exc_info=True)
            return None

    async def _extract_resume_data(
        self, resume: Resume, analysis: Optional[ResumeAnalysis]
    ) -> Dict[str, Any]:
        """
        Extract resume data as dictionary for screening.

        Args:
            resume: Resume model
            analysis: ResumeAnalysis model (optional)

        Returns:
            Dictionary with resume data
        """
        data = {
            "id": str(resume.id),
            "filename": resume.filename,
            "status": resume.status.value if resume.status else None,
            "skills": [],
            "experience": {},
            "education": [],
        }

        if analysis:
            if analysis.skills:
                data["skills"] = analysis.skills
            if analysis.education:
                data["education"] = analysis.education
            if analysis.total_experience_months:
                data["experience"] = {
                    "total_months": analysis.total_experience_months
                }

        return data


# Singleton instance getter for dependency injection
_screening_service_instance: Optional[ScreeningService] = None


def get_screening_service(db: AsyncSession) -> ScreeningService:
    """
    Get or create a ScreeningService instance.

    This function is designed for use with FastAPI dependency injection.

    Args:
        db: Database session

    Returns:
        ScreeningService instance

    Example:
        >>> from fastapi import Depends
        >>> from database import get_db
        >>> from services.screening_service import get_screening_service
        >>>
        >>> @router.post("/screen/{resume_id}/{vacancy_id}")
        >>> async def screen_candidate(
        >>>     resume_id: UUID,
        >>>     vacancy_id: UUID,
        >>>     db: AsyncSession = Depends(get_db),
        >>>     screening_service: ScreeningService = Depends(get_screening_service)
        >>> ):
        >>>     result = await screening_service.apply_screening_rules(resume_id, vacancy_id)
        >>>     return result
    """
    return ScreeningService(db)
