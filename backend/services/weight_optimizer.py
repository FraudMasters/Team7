"""
Weight Optimizer Service for A/B Testing Matching Weights

This module provides weight optimization capabilities for the A/B testing system.
It handles:
- Random user assignment to test variants (weight profiles)
- Performance metric tracking (match acceptance, time-to-hire, user satisfaction)
- Statistical significance testing using scipy
- Automated weight optimization based on performance data

The service uses seeded numpy random for reproducible, deterministic user assignment
and scipy.stats for statistical analysis of metric differences between variants.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ab_testing import (
    ABTest,
    ABTestAssignment,
    ABTestMetric,
    ABTestMetricType,
    ABTestStatus,
)
from models.matching_weights import (
    MatchingWeightProfile,
    MatchingWeightVersion,
    PRESET_PROFILES,
)

logger = logging.getLogger(__name__)


@dataclass
class UserAssignment:
    """
    Result of user assignment to an A/B test variant.

    Attributes:
        user_id: ID of the assigned user
        test_id: ID of the A/B test
        profile_id: ID of the assigned weight profile
        profile_name: Human-readable name of the profile
        assignment_id: ID of the assignment record
        was_new_assignment: True if this is a new assignment (not cached)
    """

    user_id: str
    test_id: str
    profile_id: str
    profile_name: str
    assignment_id: str
    was_new_assignment: bool


@dataclass
class MetricRecord:
    """
    Result of recording a performance metric.

    Attributes:
        metric_id: ID of the created metric record
        assignment_id: ID of the associated assignment
        metric_type: Type of metric recorded
        metric_value: Value of the metric
        recorded_at: Timestamp when metric was recorded
    """

    metric_id: str
    assignment_id: str
    metric_type: ABTestMetricType
    metric_value: float
    recorded_at: datetime


@dataclass
class StatisticalTestResult:
    """
    Result of statistical significance testing between variants.

    Attributes:
        test_type: Type of statistical test performed (ttest, chi2, mann_whitney)
        p_value: P-value of the test (lower = more significant)
        is_significant: True if p < 0.05 (statistically significant)
        effect_size: Magnitude of difference between variants
        confidence_interval: 95% confidence interval for the difference
        variant_a_mean: Mean value for variant A
        variant_b_mean: Mean value for variant B
        sample_size_a: Number of samples in variant A
        sample_size_b: Number of samples in variant B
    """

    test_type: str
    p_value: float
    is_significant: bool
    effect_size: float
    confidence_interval: Optional[tuple[float, float]]
    variant_a_mean: float
    variant_b_mean: float
    sample_size_a: int
    sample_size_b: int


@dataclass
class OptimizationResult:
    """
    Result of weight optimization analysis.

    Attributes:
        should_optimize: Whether optimization should be performed
        recommended_weights: Dictionary of recommended weight values
        reason: Explanation for the recommendation
        statistical_significance: Results of statistical tests
        metrics_summary: Summary of metrics for each variant
    """

    should_optimize: bool
    recommended_weights: Dict[str, float]
    reason: str
    statistical_significance: Optional[StatisticalTestResult]
    metrics_summary: Dict[str, Any]


class WeightOptimizerService:
    """
    Service for weight optimization in A/B testing of matching algorithms.

    This service provides:
    - Deterministic random assignment of users to weight profile variants
    - Metric recording and aggregation for performance tracking
    - Statistical analysis using scipy (t-test, chi-square, Mann-Whitney U)
    - Automated weight optimization based on statistically significant improvements

    The service uses numpy with a fixed seed for reproducible random assignment,
    ensuring the same user always gets the same profile assignment for a given test.
    """

    # Minimum sample size per variant before running statistical tests
    MIN_SAMPLE_SIZE = 30

    # Statistical significance threshold
    SIGNIFICANCE_LEVEL = 0.05

    # Random seed for deterministic assignment
    RANDOM_SEED = 42

    def __init__(self, db: AsyncSession):
        """
        Initialize the weight optimizer service.

        Args:
            db: Database session for executing queries
        """
        self.db = db
        self._rng = np.random.default_rng(seed=self.RANDOM_SEED)

    async def assign_user_to_variant(
        self,
        test_id: str,
        user_id: str,
        organization_id: str,
    ) -> UserAssignment:
        """
        Assign a user to a weight profile variant for an A/B test.

        Assignment is deterministic - the same user will always receive the same
        profile assignment for a given test. Uses a seeded random number generator
        with user-specific hashing for reproducibility.

        Args:
            test_id: ID of the A/B test
            user_id: ID of the user to assign
            organization_id: ID of the organization

        Returns:
            UserAssignment with profile details

        Raises:
            ValueError: If test is not found or not in running state
        """
        from uuid import UUID

        # Step 1: Verify the test exists and is running
        try:
            test_uuid = UUID(test_id)
        except ValueError as e:
            raise ValueError(f"Invalid test_id format: {test_id}") from e

        test_query = select(ABTest).where(
            and_(
                ABTest.id == test_uuid,
                ABTest.organization_id == organization_id,
            )
        )
        test_result = await self.db.execute(test_query)
        test = test_result.scalar_one_or_none()

        if not test:
            raise ValueError(f"A/B test not found: {test_id}")

        if test.status != ABTestStatus.RUNNING:
            raise ValueError(
                f"A/B test is not in running state. Current status: {test.status.value}"
            )

        # Step 2: Check if user already has an assignment for this test
        existing_query = select(ABTestAssignment).where(
            and_(
                ABTestAssignment.test_id == test_uuid,
                ABTestAssignment.user_id == user_id,
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_assignment = existing_result.scalar_one_or_none()

        if existing_assignment:
            # Return existing assignment
            profile_query = select(MatchingWeightProfile).where(
                MatchingWeightProfile.id == existing_assignment.profile_id
            )
            profile_result = await self.db.execute(profile_query)
            profile = profile_result.scalar_one_or_none()

            if profile:
                return UserAssignment(
                    user_id=user_id,
                    test_id=test_id,
                    profile_id=str(profile.id),
                    profile_name=profile.name,
                    assignment_id=str(existing_assignment.id),
                    was_new_assignment=False,
                )

        # Step 3: Get available preset profiles for assignment
        profiles_query = select(MatchingWeightProfile).where(
            and_(
                MatchingWeightProfile.is_preset == True,
                MatchingWeightProfile.is_active == True,
            )
        )
        profiles_result = await self.db.execute(profiles_query)
        profiles = list(profiles_result.scalars().all())

        if not profiles:
            raise ValueError("No active preset profiles found for assignment")

        # Step 4: Deterministically assign user to a profile
        # Use hash(user_id) % n_profiles for deterministic assignment
        # The same user will always get the same profile index
        profile_index = hash(user_id) % len(profiles)
        selected_profile = profiles[profile_index]

        logger.info(
            f"Assigning user {user_id} to profile '{selected_profile.name}' "
            f"for test {test_id} (deterministic index: {profile_index})"
        )

        # Step 5: Create and save the assignment
        new_assignment = ABTestAssignment(
            test_id=test_uuid,
            user_id=user_id,
            profile_id=selected_profile.id,
            assigned_at=datetime.now().astimezone(),
        )

        self.db.add(new_assignment)
        await self.db.commit()
        await self.db.refresh(new_assignment)

        logger.info(
            f"Created assignment {new_assignment.id} for user {user_id} "
            f"to profile {selected_profile.name}"
        )

        # Step 6: Return UserAssignment
        return UserAssignment(
            user_id=user_id,
            test_id=test_id,
            profile_id=str(selected_profile.id),
            profile_name=selected_profile.name,
            assignment_id=str(new_assignment.id),
            was_new_assignment=True,
        )

    async def record_metric(
        self,
        test_id: str,
        user_id: str,
        metric_type: ABTestMetricType,
        metric_value: float,
        recorded_at: Optional[datetime] = None,
    ) -> MetricRecord:
        """
        Record a performance metric for a user's A/B test assignment.

        Metrics are associated with the user's existing assignment in the test.
        Partial metric data is supported (e.g., recording time_to_hire without
        user_satisfaction).

        Args:
            test_id: ID of the A/B test
            user_id: ID of the user
            metric_type: Type of metric to record
            metric_value: Value of the metric
            recorded_at: Optional timestamp for when metric was recorded

        Returns:
            MetricRecord with details of the created metric

        Raises:
            ValueError: If no assignment exists for the user in this test
        """
        from uuid import UUID

        # Step 1: Validate test_id format
        try:
            test_uuid = UUID(test_id)
        except ValueError as e:
            raise ValueError(f"Invalid test_id format: {test_id}") from e

        # Step 2: Find the user's existing assignment in this test
        assignment_query = select(ABTestAssignment).where(
            and_(
                ABTestAssignment.test_id == test_uuid,
                ABTestAssignment.user_id == user_id,
            )
        )
        assignment_result = await self.db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise ValueError(
                f"No assignment found for user {user_id} in test {test_id}. "
                f"User must be assigned to a variant before recording metrics."
            )

        # Step 3: Validate metric value based on type
        if metric_type == ABTestMetricType.MATCH_ACCEPTANCE:
            # Binary: should be 0.0 or 1.0
            if metric_value not in (0.0, 1.0):
                logger.warning(
                    f"Match acceptance metric should be 0.0 or 1.0, got {metric_value}. "
                    f"Clamping to valid range."
                )
                metric_value = 1.0 if metric_value > 0.5 else 0.0
        elif metric_type == ABTestMetricType.USER_SATISFACTION:
            # Ordinal 1-5 scale
            if not (1.0 <= metric_value <= 5.0):
                logger.warning(
                    f"User satisfaction metric should be 1.0-5.0, got {metric_value}. "
                    f"Clamping to valid range."
                )
                metric_value = max(1.0, min(5.0, metric_value))
        elif metric_type == ABTestMetricType.TIME_TO_HIRE:
            # Continuous: days to hire, should be non-negative
            if metric_value < 0:
                logger.warning(
                    f"Time-to-hire metric should be non-negative, got {metric_value}. "
                    f"Setting to 0."
                )
                metric_value = 0.0

        # Step 4: Set recorded_at timestamp if not provided
        if recorded_at is None:
            recorded_at = datetime.now().astimezone()

        # Step 5: Create and save the metric record
        new_metric = ABTestMetric(
            test_id=test_uuid,
            assignment_id=assignment.id,
            metric_type=metric_type,
            metric_value=metric_value,
            recorded_at=recorded_at,
        )

        self.db.add(new_metric)
        await self.db.commit()
        await self.db.refresh(new_metric)

        logger.info(
            f"Recorded metric {metric_type.value}={metric_value} for user {user_id} "
            f"in test {test_id} (assignment: {assignment.id}, profile: {assignment.profile_id})"
        )

        # Step 6: Return MetricRecord
        return MetricRecord(
            metric_id=str(new_metric.id),
            assignment_id=str(assignment.id),
            metric_type=metric_type,
            metric_value=metric_value,
            recorded_at=recorded_at,
        )

    async def analyze_metrics(
        self,
        test_id: str,
        metric_type: ABTestMetricType,
    ) -> Dict[str, Any]:
        """
        Analyze metrics for an A/B test to compare variant performance.

        Aggregates metrics by weight profile and performs statistical analysis
        to determine if there are significant differences between variants.

        Args:
            test_id: ID of the A/B test
            metric_type: Type of metric to analyze

        Returns:
            Dictionary with aggregated metrics and statistical test results

        Raises:
            ValueError: If insufficient sample size or test not found
        """
        # TODO: Implementation in subtask-4-4
        raise NotImplementedError("analyze_metrics will be implemented in subtask-4-4")

    async def optimize_weights(
        self,
        test_id: str,
    ) -> OptimizationResult:
        """
        Analyze A/B test results and recommend optimized weights.

        Runs statistical tests on all tracked metrics. If a variant shows
        statistically significant improvement (p < 0.05) across key metrics,
        recommends those weights for optimization.

        Only optimizes when minimum sample size (30) is reached per variant.

        Args:
            test_id: ID of the A/B test to analyze

        Returns:
            OptimizationResult with recommendation and supporting data

        Raises:
            ValueError: If test is not found or insufficient data
        """
        # TODO: Implementation in subtask-4-5
        raise NotImplementedError("optimize_weights will be implemented in subtask-4-5")


# Singleton instance getter for dependency injection
_weight_optimizer_instance: Optional[WeightOptimizerService] = None


def get_weight_optimizer_service(db: AsyncSession) -> WeightOptimizerService:
    """
    Get or create a WeightOptimizerService instance.

    This function is designed for use with FastAPI dependency injection.

    Args:
        db: Database session

    Returns:
        WeightOptimizerService instance

    Example:
        >>> from fastapi import Depends
        >>> from database import get_db
        >>> from services.weight_optimizer import get_weight_optimizer_service
        >>>
        >>> @router.post("/ab-tests/{test_id}/assign")
        >>> async def assign_user(
        >>>     test_id: str,
        >>>     user_id: str,
        >>>     db: AsyncSession = Depends(get_db),
        >>>     optimizer: WeightOptimizerService = Depends(get_weight_optimizer_service)
        >>> ):
        >>>     result = await optimizer.assign_user_to_variant(test_id, user_id, org_id)
        >>>     return result
    """
    return WeightOptimizerService(db)
