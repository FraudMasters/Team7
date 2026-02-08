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
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from scipy.stats import chi2_contingency, mannwhitneyu, ttest_ind
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
        from uuid import UUID

        # Step 1: Validate test_id and fetch test
        try:
            test_uuid = UUID(test_id)
        except ValueError as e:
            raise ValueError(f"Invalid test_id format: {test_id}") from e

        # Step 2: Query metrics grouped by profile
        # Join ABTestMetric -> ABTestAssignment -> MatchingWeightProfile
        metrics_query = (
            select(
                MatchingWeightProfile.id.label("profile_id"),
                MatchingWeightProfile.name.label("profile_name"),
                MatchingWeightProfile.keyword_weight,
                MatchingWeightProfile.tfidf_weight,
                MatchingWeightProfile.vector_weight,
                ABTestMetric.metric_value,
            )
            .join(ABTestAssignment, ABTestAssignment.profile_id == MatchingWeightProfile.id)
            .join(ABTestMetric, ABTestMetric.assignment_id == ABTestAssignment.id)
            .where(
                and_(
                    ABTestMetric.test_id == test_uuid,
                    ABTestMetric.metric_type == metric_type,
                )
            )
        )

        metrics_result = await self.db.execute(metrics_query)
        metrics_rows = metrics_result.all()

        if not metrics_rows:
            raise ValueError(
                f"No metrics found for test {test_id} and metric type {metric_type.value}"
            )

        # Step 3: Group metrics by profile
        profile_metrics: Dict[str, List[float]] = {}
        profile_info: Dict[str, Dict[str, Any]] = {}

        for row in metrics_rows:
            profile_id_str = str(row.profile_id)
            if profile_id_str not in profile_metrics:
                profile_metrics[profile_id_str] = []
                profile_info[profile_id_str] = {
                    "profile_id": profile_id_str,
                    "profile_name": row.profile_name,
                    "keyword_weight": row.keyword_weight,
                    "tfidf_weight": row.tfidf_weight,
                    "vector_weight": row.vector_weight,
                    "sample_size": 0,
                    "mean": 0.0,
                    "std": 0.0,
                }
            profile_metrics[profile_id_str].append(row.metric_value)

        # Step 4: Check minimum sample size
        for profile_id, values in profile_metrics.items():
            if len(values) < self.MIN_SAMPLE_SIZE:
                raise ValueError(
                    f"Insufficient sample size for profile {profile_id}: "
                    f"{len(values)} < {self.MIN_SAMPLE_SIZE} (minimum required)"
                )

        # Step 5: Calculate summary statistics for each profile
        for profile_id, values in profile_metrics.items():
            arr = np.array(values)
            profile_info[profile_id]["sample_size"] = len(values)
            profile_info[profile_id]["mean"] = float(np.mean(arr))
            profile_info[profile_id]["std"] = float(np.std(arr, ddof=1)) if len(values) > 1 else 0.0

        # Step 6: Run appropriate statistical test based on metric type
        profile_ids = list(profile_metrics.keys())

        if len(profile_ids) < 2:
            raise ValueError(
                f"At least 2 profiles required for analysis, found {len(profile_ids)}"
            )

        # Compare first two profiles (can be extended for multi-variant comparison)
        profile_a_id = profile_ids[0]
        profile_b_id = profile_ids[1]
        values_a = profile_metrics[profile_a_id]
        values_b = profile_metrics[profile_b_id]

        # Choose test based on metric type
        if metric_type == ABTestMetricType.TIME_TO_HIRE:
            test_result = self._analyze_continuous_metric(values_a, values_b)
        elif metric_type == ABTestMetricType.MATCH_ACCEPTANCE:
            test_result = self._analyze_binary_metric(values_a, values_b)
        elif metric_type == ABTestMetricType.USER_SATISFACTION:
            test_result = self._analyze_ordinal_metric(values_a, values_b)
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")

        # Step 7: Return results
        return {
            "metric_type": metric_type.value,
            "profiles": list(profile_info.values()),
            "statistical_test": {
                "test_type": test_result.test_type,
                "p_value": test_result.p_value,
                "is_significant": test_result.is_significant,
                "effect_size": test_result.effect_size,
                "confidence_interval": test_result.confidence_interval,
                "variant_a_mean": test_result.variant_a_mean,
                "variant_b_mean": test_result.variant_b_mean,
                "sample_size_a": test_result.sample_size_a,
                "sample_size_b": test_result.sample_size_b,
            },
            "comparison": {
                "profile_a": profile_a_id,
                "profile_b": profile_b_id,
                "better_profile": profile_a_id if test_result.variant_a_mean > test_result.variant_b_mean else profile_b_id,
                "improvement_pct": (
                    (test_result.variant_a_mean - test_result.variant_b_mean) / test_result.variant_b_mean * 100
                    if test_result.variant_b_mean != 0
                    else 0.0
                ),
            },
        }

    def _analyze_continuous_metric(
        self,
        values_a: List[float],
        values_b: List[float],
    ) -> StatisticalTestResult:
        """
        Analyze continuous metrics using independent t-test.

        Uses scipy.stats.ttest_ind to compare means between two groups.
        Calculates Cohen's d as effect size.

        Args:
            values_a: Metric values for variant A
            values_b: Metric values for variant B

        Returns:
            StatisticalTestResult with t-test results
        """
        arr_a = np.array(values_a)
        arr_b = np.array(values_b)

        # Run independent t-test (assumes unequal variance)
        statistic, p_value = ttest_ind(arr_a, arr_b, equal_var=False)

        # Calculate Cohen's d (effect size)
        pooled_std = np.sqrt(
            ((len(arr_a) - 1) * np.var(arr_a, ddof=1) +
             (len(arr_b) - 1) * np.var(arr_b, ddof=1)) /
            (len(arr_a) + len(arr_b) - 2)
        )
        effect_size = (np.mean(arr_a) - np.mean(arr_b)) / pooled_std if pooled_std > 0 else 0.0

        # Calculate 95% confidence interval for difference
        se_diff = np.sqrt(np.var(arr_a, ddof=1) / len(arr_a) + np.var(arr_b, ddof=1) / len(arr_b))
        margin = 1.96 * se_diff
        diff_mean = float(np.mean(arr_a) - np.mean(arr_b))
        ci = (diff_mean - margin, diff_mean + margin)

        return StatisticalTestResult(
            test_type="ttest",
            p_value=float(p_value),
            is_significant=p_value < self.SIGNIFICANCE_LEVEL,
            effect_size=float(effect_size),
            confidence_interval=ci,
            variant_a_mean=float(np.mean(arr_a)),
            variant_b_mean=float(np.mean(arr_b)),
            sample_size_a=len(arr_a),
            sample_size_b=len(arr_b),
        )

    def _analyze_binary_metric(
        self,
        values_a: List[float],
        values_b: List[float],
    ) -> StatisticalTestResult:
        """
        Analyze binary metrics using chi-square test of independence.

        Uses scipy.stats.chi2_contingency to compare proportions between groups.
        Calculates difference in proportions as effect size.

        Args:
            values_a: Binary metric values (0.0 or 1.0) for variant A
            values_b: Binary metric values (0.0 or 1.0) for variant B

        Returns:
            StatisticalTestResult with chi-square test results
        """
        arr_a = np.array(values_a)
        arr_b = np.array(values_b)

        # Count successes (1.0) and failures (0.0) for each group
        success_a = np.sum(arr_a == 1.0)
        failure_a = np.sum(arr_a == 0.0)
        success_b = np.sum(arr_b == 1.0)
        failure_b = np.sum(arr_b == 0.0)

        # Build contingency table
        observed = np.array([[success_a, failure_a], [success_b, failure_b]])

        # Run chi-square test
        statistic, p_value, dof, expected = chi2_contingency(observed)

        # Effect size: difference in proportions
        prop_a = success_a / len(arr_a) if len(arr_a) > 0 else 0.0
        prop_b = success_b / len(arr_b) if len(arr_b) > 0 else 0.0
        effect_size = float(prop_a - prop_b)

        # Confidence interval for difference in proportions
        se_diff = np.sqrt(
            (prop_a * (1 - prop_a) / len(arr_a)) +
            (prop_b * (1 - prop_b) / len(arr_b))
        )
        margin = 1.96 * se_diff
        ci = (effect_size - margin, effect_size + margin)

        return StatisticalTestResult(
            test_type="chi2",
            p_value=float(p_value),
            is_significant=p_value < self.SIGNIFICANCE_LEVEL,
            effect_size=effect_size,
            confidence_interval=ci,
            variant_a_mean=prop_a,
            variant_b_mean=prop_b,
            sample_size_a=len(arr_a),
            sample_size_b=len(arr_b),
        )

    def _analyze_ordinal_metric(
        self,
        values_a: List[float],
        values_b: List[float],
    ) -> StatisticalTestResult:
        """
        Analyze ordinal metrics using Mann-Whitney U test.

        Uses scipy.stats.mannwhitneyu to compare distributions between groups.
        Calculates rank-biserial correlation as effect size.

        Args:
            values_a: Ordinal metric values (e.g., 1-5 scale) for variant A
            values_b: Ordinal metric values (e.g., 1-5 scale) for variant B

        Returns:
            StatisticalTestResult with Mann-Whitney U test results
        """
        arr_a = np.array(values_a)
        arr_b = np.array(values_b)

        # Run Mann-Whitney U test
        statistic, p_value = mannwhitneyu(arr_a, arr_b, alternative="two-sided")

        # Calculate effect size: rank-biserial correlation
        # r = 1 - (2U / (n1 * n2))
        n1 = len(arr_a)
        n2 = len(arr_b)
        u_stat = min(
            statistic,  # statistic could be U for first group
            n1 * n2 - statistic  # or U for second group
        )
        effect_size = 1 - (2 * u_stat / (n1 * n2))

        # Calculate confidence interval using bootstrap approximation
        # For simplicity, use standard error of the mean difference
        se_diff = np.sqrt(np.var(arr_a, ddof=1) / n1 + np.var(arr_b, ddof=1) / n2)
        margin = 1.96 * se_diff
        diff_mean = float(np.mean(arr_a) - np.mean(arr_b))
        ci = (diff_mean - margin, diff_mean + margin)

        return StatisticalTestResult(
            test_type="mann_whitney",
            p_value=float(p_value),
            is_significant=p_value < self.SIGNIFICANCE_LEVEL,
            effect_size=float(effect_size),
            confidence_interval=ci,
            variant_a_mean=float(np.mean(arr_a)),
            variant_b_mean=float(np.mean(arr_b)),
            sample_size_a=n1,
            sample_size_b=n2,
        )

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
        from uuid import UUID

        # Step 1: Validate test_id and fetch test
        try:
            test_uuid = UUID(test_id)
        except ValueError as e:
            raise ValueError(f"Invalid test_id format: {test_id}") from e

        test_query = select(ABTest).where(ABTest.id == test_uuid)
        test_result = await self.db.execute(test_query)
        test = test_result.scalar_one_or_none()

        if not test:
            raise ValueError(f"A/B test not found: {test_id}")

        # Step 2: Analyze each metric type
        metrics_summary: Dict[str, Any] = {}
        significant_improvements: List[Dict[str, Any]] = []

        for metric_type in ABTestMetricType:
            try:
                analysis = await self.analyze_metrics(test_id, metric_type)
                metrics_summary[metric_type.value] = analysis

                # Check if result is statistically significant
                stat_test = analysis.get("statistical_test", {})
                if stat_test.get("is_significant", False):
                    comparison = analysis.get("comparison", {})
                    significant_improvements.append({
                        "metric_type": metric_type.value,
                        "better_profile": comparison.get("better_profile"),
                        "improvement_pct": comparison.get("improvement_pct", 0.0),
                        "p_value": stat_test.get("p_value"),
                        "effect_size": stat_test.get("effect_size"),
                    })
                    logger.info(
                        f"Significant improvement found for {metric_type.value}: "
                        f"p={stat_test.get('p_value'):.4f}, "
                        f"better_profile={comparison.get('better_profile')}"
                    )
            except ValueError as e:
                # Insufficient data for this metric type
                logger.warning(f"Could not analyze {metric_type.value}: {e}")
                metrics_summary[metric_type.value] = {"error": str(e)}

        # Step 3: Determine if optimization should occur
        # Optimization is recommended if at least one metric shows significant improvement
        should_optimize = len(significant_improvements) > 0

        if not should_optimize:
            # No significant improvements found
            return OptimizationResult(
                should_optimize=False,
                recommended_weights={},
                reason=(
                    "No statistically significant improvements found (p < 0.05). "
                    f"Continue collecting data until minimum sample size ({self.MIN_SAMPLE_SIZE}) "
                    "is reached for all variants."
                ),
                statistical_significance=None,
                metrics_summary=metrics_summary,
            )

        # Step 4: Identify the best profile to recommend
        # Use a voting approach: the profile with the most significant wins is recommended
        profile_win_count: Dict[str, int] = {}
        for improvement in significant_improvements:
            profile_id = improvement["better_profile"]
            profile_win_count[profile_id] = profile_win_count.get(profile_id, 0) + 1

        # Get the profile with the most wins
        best_profile_id = max(profile_win_count, key=profile_win_count.get)

        # Step 5: Get the weights for the best profile
        profile_query = select(MatchingWeightProfile).where(
            MatchingWeightProfile.id == UUID(best_profile_id)
        )
        profile_result = await self.db.execute(profile_query)
        best_profile = profile_result.scalar_one_or_none()

        if not best_profile:
            raise ValueError(f"Best profile not found: {best_profile_id}")

        recommended_weights = {
            "keyword_weight": best_profile.keyword_weight,
            "tfidf_weight": best_profile.tfidf_weight,
            "vector_weight": best_profile.vector_weight,
        }

        # Step 6: Build the reason string
        win_reasons = []
        for improvement in significant_improvements:
            if improvement["better_profile"] == best_profile_id:
                win_reasons.append(
                    f"{improvement['metric_type']}: "
                    f"+{improvement['improvement_pct']:.1f}% "
                    f"(p={improvement['p_value']:.4f})"
                )

        reason = (
            f"Profile '{best_profile.name}' shows statistically significant improvement "
            f"in {len([i for i in significant_improvements if i['better_profile'] == best_profile_id])} "
            f"of {len(significant_improvements)} significant metrics. "
            f"Improvements: {', '.join(win_reasons)}. "
            f"Weights: keyword={recommended_weights['keyword_weight']:.2f}, "
            f"tfidf={recommended_weights['tfidf_weight']:.2f}, "
            f"vector={recommended_weights['vector_weight']:.2f}"
        )

        # Step 7: Create a representative StatisticalTestResult for the primary metric
        # Use match_acceptance as the primary metric if significant, otherwise first significant
        primary_result = None
        for improvement in significant_improvements:
            if improvement["better_profile"] == best_profile_id:
                metric_data = metrics_summary.get(improvement["metric_type"], {})
                stat_data = metric_data.get("statistical_test", {})
                if stat_data:
                    primary_result = StatisticalTestResult(
                        test_type=stat_data.get("test_type", ""),
                        p_value=stat_data.get("p_value", 0.0),
                        is_significant=stat_data.get("is_significant", False),
                        effect_size=stat_data.get("effect_size", 0.0),
                        confidence_interval=stat_data.get("confidence_interval"),
                        variant_a_mean=stat_data.get("variant_a_mean", 0.0),
                        variant_b_mean=stat_data.get("variant_b_mean", 0.0),
                        sample_size_a=stat_data.get("sample_size_a", 0),
                        sample_size_b=stat_data.get("sample_size_b", 0),
                    )
                break

        logger.info(
            f"Optimization recommendation for test {test_id}: "
            f"optimize={should_optimize}, profile={best_profile.name}"
        )

        # Step 8: Return OptimizationResult
        return OptimizationResult(
            should_optimize=should_optimize,
            recommended_weights=recommended_weights,
            reason=reason,
            statistical_significance=primary_result,
            metrics_summary=metrics_summary,
        )


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
