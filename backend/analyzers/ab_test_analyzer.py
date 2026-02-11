"""
A/B Testing Statistical Significance Analyzer for ML Models

This module provides statistical analysis tools for A/B testing machine learning
model comparisons. The system supports:
- Chi-square tests for categorical outcome comparisons
- T-tests (independent and paired) for continuous metric comparisons
- Confidence interval calculations
- Statistical power analysis
- Sample size recommendations
- Bayesian analysis for posterior probability calculations
"""
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from numpy import typing as npt
from scipy import stats

from models.ml_model_version import MLModelVersion
from models.model_performance_history import ModelPerformanceHistory

logger = logging.getLogger(__name__)


class SignificanceLevel(Enum):
    """Statistical significance levels for hypothesis testing."""
    P001 = 0.001  # Highly significant
    P01 = 0.01    # Very significant
    P05 = 0.05    # Significant (default)
    P10 = 0.10    # Marginally significant


class TestType(Enum):
    """Types of statistical tests available."""
    CHI_SQUARE = "chi_square"
    T_TEST_INDEPENDENT = "t_test_independent"
    T_TEST_PAIRED = "t_test_paired"
    WELCH_T_TEST = "welch_t_test"
    MANN_WHITNEY = "mann_whitney"


class TestResult(Enum):
    """Results of statistical hypothesis tests."""
    SIGNIFICANT = "significant"
    NOT_SIGNIFICANT = "not_significant"
    INCONCLUSIVE = "inconclusive"


@dataclass
class StatisticalTestResult:
    """
    Container for statistical test results.

    Attributes:
        test_type: Type of statistical test performed
        statistic: Test statistic value
        p_value: P-value from the test
        is_significant: Whether result is statistically significant
        significance_level: Significance level used
        confidence_interval: Confidence interval for the difference (if applicable)
        effect_size: Effect size measure (Cohen's d for t-tests, Cramer's V for chi-square)
        interpretation: Human-readable interpretation of results
    """
    test_type: TestType
    statistic: float
    p_value: float
    is_significant: bool
    significance_level: float
    confidence_interval: Optional[Tuple[float, float]] = None
    effect_size: Optional[float] = None
    interpretation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "test_type": self.test_type.value,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "is_significant": self.is_significant,
            "significance_level": self.significance_level,
            "confidence_interval": list(self.confidence_interval) if self.confidence_interval else None,
            "effect_size": self.effect_size,
            "interpretation": self.interpretation,
        }


@dataclass
class ABTestComparison:
    """
    Container for complete A/B test comparison results.

    Attributes:
        control_model_id: UUID of control model
        treatment_model_id: UUID of treatment/experimental model
        control_metrics: Metrics for control model
        treatment_metrics: Metrics for treatment model
        statistical_tests: Dictionary of test name to StatisticalTestResult
        winner: Which model performed better ('control', 'treatment', or 'tie')
        confidence: Confidence level in the result (0-1)
        recommendation: Recommendation for action
        sample_sizes: Sample sizes for each group
    """
    control_model_id: str
    treatment_model_id: str
    control_metrics: Dict[str, float]
    treatment_metrics: Dict[str, float]
    statistical_tests: Dict[str, StatisticalTestResult]
    winner: str
    confidence: float
    recommendation: str
    sample_sizes: Dict[str, int]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison to dictionary for JSON serialization."""
        return {
            "control_model_id": self.control_model_id,
            "treatment_model_id": self.treatment_model_id,
            "control_metrics": self.control_metrics,
            "treatment_metrics": self.treatment_metrics,
            "statistical_tests": {
                k: v.to_dict() if isinstance(v, StatisticalTestResult) else v
                for k, v in self.statistical_tests.items()
            },
            "winner": self.winner,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "sample_sizes": self.sample_sizes,
            "timestamp": self.timestamp,
        }


class ABTestAnalyzer:
    """
    A/B Testing Statistical Significance Analyzer for ML Model Comparison.

    This class provides methods to perform statistical significance tests
    when comparing two model versions in an A/B testing scenario. It supports
    various test types and provides comprehensive analysis of results.

    Attributes:
        default_significance_level: Default significance level for hypothesis tests
        min_sample_size: Minimum sample size required for reliable testing

    Example:
        >>> analyzer = ABTestAnalyzer()
        >>> control_data = {'successes': 850, 'failures': 150, 'sample_size': 1000}
        >>> treatment_data = {'successes': 890, 'failures': 110, 'sample_size': 1000}
        >>> result = analyzer.chi_square_test(control_data, treatment_data)
        >>> print(f"Significant: {result.is_significant}, p-value: {result.p_value:.4f}")
    """

    # Default configuration
    DEFAULT_SIGNIFICANCE_LEVEL = 0.05
    DEFAULT_MIN_SAMPLE_SIZE = 30
    DEFAULT_MIN_EFFECT_SIZE = 0.1  # Cohen's d threshold for small effect

    # Effect size thresholds (Cohen's conventions)
    EFFECT_SIZE_SMALL = 0.2
    EFFECT_SIZE_MEDIUM = 0.5
    EFFECT_SIZE_LARGE = 0.8

    def __init__(
        self,
        default_significance_level: float = DEFAULT_SIGNIFICANCE_LEVEL,
        min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    ) -> None:
        """
        Initialize the A/B test analyzer.

        Args:
            default_significance_level: Default significance level (alpha) for tests
            min_sample_size: Minimum sample size required for reliable testing
        """
        self.default_significance_level = default_significance_level
        self.min_sample_size = min_sample_size

    def chi_square_test(
        self,
        control_data: Dict[str, int],
        treatment_data: Dict[str, int],
        significance_level: Optional[float] = None,
    ) -> StatisticalTestResult:
        """
        Perform chi-square test of independence for categorical outcomes.

        Tests whether there is a significant difference in success/failure rates
        between control and treatment groups.

        Args:
            control_data: Dictionary with 'successes' and 'failures' counts for control
            treatment_data: Dictionary with 'successes' and 'failures' counts for treatment
            significance_level: Significance level for the test (defaults to instance default)

        Returns:
            StatisticalTestResult with test statistic, p-value, and interpretation

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> control = {'successes': 850, 'failures': 150}
            >>> treatment = {'successes': 890, 'failures': 110}
            >>> result = analyzer.chi_square_test(control, treatment)
            >>> print(f"Chi-square statistic: {result.statistic:.2f}")
        """
        alpha = significance_level or self.default_significance_level

        try:
            # Extract counts
            control_successes = control_data.get("successes", 0)
            control_failures = control_data.get("failures", 0)
            treatment_successes = treatment_data.get("successes", 0)
            treatment_failures = treatment_data.get("failures", 0)

            # Build contingency table
            observed = np.array([
                [control_successes, control_failures],
                [treatment_successes, treatment_failures],
            ])

            # Check minimum sample size
            total_samples = observed.sum()
            if total_samples < self.min_sample_size:
                return StatisticalTestResult(
                    test_type=TestType.CHI_SQUARE,
                    statistic=0.0,
                    p_value=1.0,
                    is_significant=False,
                    significance_level=alpha,
                    interpretation=f"Insufficient sample size ({total_samples} < {self.min_sample_size})",
                )

            # Perform chi-square test
            statistic, p_value, dof, expected = stats.chi2_contingency(observed)

            # Check for low expected frequencies (Fisher's exact may be better)
            low_expected = np.any(expected < 5)

            # Calculate Cramer's V for effect size
            n = observed.sum()
            min_dim = min(observed.shape) - 1
            cramers_v = math.sqrt(statistic / (n * min_dim)) if n > 0 and min_dim > 0 else 0

            # Determine significance
            is_significant = p_value < alpha

            # Generate interpretation
            if is_significant:
                control_rate = control_successes / (control_successes + control_failures) if (control_successes + control_failures) > 0 else 0
                treatment_rate = treatment_successes / (treatment_successes + treatment_failures) if (treatment_successes + treatment_failures) > 0 else 0

                interpretation = (
                    f"Statistically significant difference detected (p={p_value:.4f}). "
                    f"Control success rate: {control_rate:.1%}, Treatment success rate: {treatment_rate:.1%}. "
                    f"Effect size (Cramer's V): {cramers_v:.3f} ({self._interpret_effect_size(cramers_v, 'cramers_v')})."
                )
            else:
                interpretation = (
                    f"No statistically significant difference detected (p={p_value:.4f} >= {alpha}). "
                    f"Effect size (Cramer's V): {cramers_v:.3f}."
                )

            if low_expected:
                interpretation += " Note: Some expected frequencies < 5, consider Fisher's exact test."

            logger.info(
                f"Chi-square test: statistic={statistic:.3f}, p={p_value:.4f}, "
                f"significant={is_significant}, cramers_v={cramers_v:.3f}"
            )

            return StatisticalTestResult(
                test_type=TestType.CHI_SQUARE,
                statistic=float(statistic),
                p_value=float(p_value),
                is_significant=is_significant,
                significance_level=alpha,
                effect_size=cramers_v,
                interpretation=interpretation,
            )

        except Exception as e:
            logger.error(f"Error performing chi-square test: {e}", exc_info=True)
            return StatisticalTestResult(
                test_type=TestType.CHI_SQUARE,
                statistic=0.0,
                p_value=1.0,
                is_significant=False,
                significance_level=alpha,
                interpretation=f"Error performing test: {str(e)}",
            )

    def t_test_independent(
        self,
        control_values: npt.NDArray[np.float64],
        treatment_values: npt.NDArray[np.float64],
        significance_level: Optional[float] = None,
        equal_var: bool = False,
    ) -> StatisticalTestResult:
        """
        Perform independent samples t-test for continuous metrics.

        Tests whether there is a significant difference in means between
        control and treatment groups.

        Args:
            control_values: Array of metric values for control group
            treatment_values: Array of metric values for treatment group
            significance_level: Significance level for the test
            equal_var: Whether to assume equal variances (False uses Welch's t-test)

        Returns:
            StatisticalTestResult with test statistic, p-value, confidence interval, and effect size

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> control = np.array([0.82, 0.85, 0.79, 0.88, 0.84])
            >>> treatment = np.array([0.86, 0.89, 0.87, 0.91, 0.88])
            >>> result = analyzer.t_test_independent(control, treatment)
            >>> print(f"T-statistic: {result.statistic:.2f}, p-value: {result.p_value:.4f}")
        """
        alpha = significance_level or self.default_significance_level
        test_type = TestType.T_TEST_INDEPENDENT if equal_var else TestType.WELCH_T_TEST

        try:
            # Convert to numpy arrays if needed
            control = np.asarray(control_values, dtype=np.float64)
            treatment = np.asarray(treatment_values, dtype=np.float64)

            # Check sample sizes
            n1, n2 = len(control), len(treatment)
            if n1 < self.min_sample_size or n2 < self.min_sample_size:
                return StatisticalTestResult(
                    test_type=test_type,
                    statistic=0.0,
                    p_value=1.0,
                    is_significant=False,
                    significance_level=alpha,
                    interpretation=f"Insufficient sample size (control={n1}, treatment={n2}, min={self.min_sample_size})",
                )

            # Perform t-test
            statistic, p_value = stats.ttest_ind(control, treatment, equal_var=equal_var)

            # Calculate confidence interval for mean difference
            mean_diff = np.mean(treatment) - np.mean(control)

            # Standard error of the difference
            if equal_var:
                # Pooled standard error
                pooled_var = ((n1 - 1) * np.var(control, ddof=1) + (n2 - 1) * np.var(treatment, ddof=1)) / (n1 + n2 - 2)
                se_diff = np.sqrt(pooled_var * (1/n1 + 1/n2))
                df = n1 + n2 - 2
            else:
                # Welch's standard error
                se_diff = np.sqrt(np.var(control, ddof=1)/n1 + np.var(treatment, ddof=1)/n2)
                # Welch-Satterthwaite degrees of freedom
                s1_sq, s2_sq = np.var(control, ddof=1), np.var(treatment, ddof=1)
                df = ((s1_sq/n1 + s2_sq/n2)**2) / ((s1_sq/n1)**2/(n1-1) + (s2_sq/n2)**2/(n2-1))

            # Critical value for confidence interval
            t_critical = stats.t.ppf(1 - alpha/2, df)
            ci_lower = mean_diff - t_critical * se_diff
            ci_upper = mean_diff + t_critical * se_diff

            # Calculate Cohen's d for effect size
            pooled_std = np.sqrt((np.var(control, ddof=1) + np.var(treatment, ddof=1)) / 2)
            cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

            # Determine significance
            is_significant = p_value < alpha

            # Generate interpretation
            control_mean = np.mean(control)
            treatment_mean = np.mean(treatment)

            if is_significant:
                interpretation = (
                    f"Statistically significant difference in means (t={statistic:.3f}, p={p_value:.4f}). "
                    f"Control mean: {control_mean:.4f}, Treatment mean: {treatment_mean:.4f}. "
                    f"Mean difference: {mean_diff:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]). "
                    f"Effect size (Cohen's d): {cohens_d:.3f} ({self._interpret_effect_size(abs(cohens_d), 'cohens_d')})."
                )
            else:
                interpretation = (
                    f"No statistically significant difference in means (t={statistic:.3f}, p={p_value:.4f}). "
                    f"Control mean: {control_mean:.4f}, Treatment mean: {treatment_mean:.4f}. "
                    f"Mean difference: {mean_diff:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]). "
                    f"Effect size (Cohen's d): {cohens_d:.3f}."
                )

            logger.info(
                f"Independent t-test (equal_var={equal_var}): t={statistic:.3f}, p={p_value:.4f}, "
                f"mean_diff={mean_diff:.4f}, cohens_d={cohens_d:.3f}"
            )

            return StatisticalTestResult(
                test_type=test_type,
                statistic=float(statistic),
                p_value=float(p_value),
                is_significant=is_significant,
                significance_level=alpha,
                confidence_interval=(float(ci_lower), float(ci_upper)),
                effect_size=float(cohens_d),
                interpretation=interpretation,
            )

        except Exception as e:
            logger.error(f"Error performing independent t-test: {e}", exc_info=True)
            return StatisticalTestResult(
                test_type=test_type,
                statistic=0.0,
                p_value=1.0,
                is_significant=False,
                significance_level=alpha,
                interpretation=f"Error performing test: {str(e)}",
            )

    def t_test_paired(
        self,
        control_values: npt.NDArray[np.float64],
        treatment_values: npt.NDArray[np.float64],
        significance_level: Optional[float] = None,
    ) -> StatisticalTestResult:
        """
        Perform paired samples t-test for matched/metric pairs.

        Tests whether there is a significant difference between paired observations,
        useful when the same samples are evaluated by both models.

        Args:
            control_values: Array of metric values for control (one per sample)
            treatment_values: Array of metric values for treatment (matched to control)
            significance_level: Significance level for the test

        Returns:
            StatisticalTestResult with test statistic, p-value, and interpretation

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> control = np.array([0.82, 0.85, 0.79, 0.88, 0.84])
            >>> treatment = np.array([0.86, 0.89, 0.87, 0.91, 0.88])
            >>> result = analyzer.t_test_paired(control, treatment)
            >>> print(f"T-statistic: {result.statistic:.2f}")
        """
        alpha = significance_level or self.default_significance_level

        try:
            # Convert to numpy arrays
            control = np.asarray(control_values, dtype=np.float64)
            treatment = np.asarray(treatment_values, dtype=np.float64)

            # Check sample sizes match
            if len(control) != len(treatment):
                return StatisticalTestResult(
                    test_type=TestType.T_TEST_PAIRED,
                    statistic=0.0,
                    p_value=1.0,
                    is_significant=False,
                    significance_level=alpha,
                    interpretation="Sample sizes must match for paired t-test",
                )

            n = len(control)
            if n < self.min_sample_size:
                return StatisticalTestResult(
                    test_type=TestType.T_TEST_PAIRED,
                    statistic=0.0,
                    p_value=1.0,
                    is_significant=False,
                    significance_level=alpha,
                    interpretation=f"Insufficient sample size ({n} < {self.min_sample_size})",
                )

            # Perform paired t-test
            statistic, p_value = stats.ttest_rel(control, treatment)

            # Calculate differences
            differences = treatment - control
            mean_diff = np.mean(differences)
            std_diff = np.std(differences, ddof=1)

            # Confidence interval for mean difference
            se_diff = std_diff / np.sqrt(n)
            t_critical = stats.t.ppf(1 - alpha/2, n - 1)
            ci_lower = mean_diff - t_critical * se_diff
            ci_upper = mean_diff + t_critical * se_diff

            # Cohen's d for paired data (using standard deviation of differences)
            cohens_d = mean_diff / std_diff if std_diff > 0 else 0

            # Determine significance
            is_significant = p_value < alpha

            # Generate interpretation
            control_mean = np.mean(control)
            treatment_mean = np.mean(treatment)

            if is_significant:
                interpretation = (
                    f"Statistically significant paired difference (t={statistic:.3f}, p={p_value:.4f}). "
                    f"Control mean: {control_mean:.4f}, Treatment mean: {treatment_mean:.4f}. "
                    f"Mean difference: {mean_diff:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]). "
                    f"Effect size (Cohen's d): {cohens_d:.3f} ({self._interpret_effect_size(abs(cohens_d), 'cohens_d')})."
                )
            else:
                interpretation = (
                    f"No statistically significant paired difference (t={statistic:.3f}, p={p_value:.4f}). "
                    f"Control mean: {control_mean:.4f}, Treatment mean: {treatment_mean:.4f}. "
                    f"Mean difference: {mean_diff:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]). "
                    f"Effect size (Cohen's d): {cohens_d:.3f}."
                )

            logger.info(
                f"Paired t-test: t={statistic:.3f}, p={p_value:.4f}, "
                f"mean_diff={mean_diff:.4f}, cohens_d={cohens_d:.3f}"
            )

            return StatisticalTestResult(
                test_type=TestType.T_TEST_PAIRED,
                statistic=float(statistic),
                p_value=float(p_value),
                is_significant=is_significant,
                significance_level=alpha,
                confidence_interval=(float(ci_lower), float(ci_upper)),
                effect_size=float(cohens_d),
                interpretation=interpretation,
            )

        except Exception as e:
            logger.error(f"Error performing paired t-test: {e}", exc_info=True)
            return StatisticalTestResult(
                test_type=TestType.T_TEST_PAIRED,
                statistic=0.0,
                p_value=1.0,
                is_significant=False,
                significance_level=alpha,
                interpretation=f"Error performing test: {str(e)}",
            )

    def compare_models(
        self,
        control_model_id: str,
        treatment_model_id: str,
        control_metrics: Dict[str, Any],
        treatment_metrics: Dict[str, Any],
        significance_level: Optional[float] = None,
        db_session: Optional[Any] = None,
    ) -> ABTestComparison:
        """
        Perform comprehensive A/B comparison between two model versions.

        Runs multiple statistical tests and provides an overall comparison
        with recommendations for promotion decisions.

        Args:
            control_model_id: UUID of control model version
            treatment_model_id: UUID of treatment/experimental model version
            control_metrics: Metrics dictionary for control model
            treatment_metrics: Metrics dictionary for treatment model
            significance_level: Significance level for all tests
            db_session: Optional database session for fetching additional data

        Returns:
            ABTestComparison with comprehensive analysis results

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> comparison = analyzer.compare_models(
            ...     'control-uuid', 'treatment-uuid',
            ...     {'accuracy': 0.85, 'f1_score': 0.83, 'sample_size': 1000},
            ...     {'accuracy': 0.87, 'f1_score': 0.86, 'sample_size': 1000}
            ... )
            >>> print(f"Winner: {comparison.winner}")
            >>> print(f"Recommendation: {comparison.recommendation}")
        """
        alpha = significance_level or self.default_significance_level
        statistical_tests: Dict[str, StatisticalTestResult] = {}

        try:
            # Extract sample sizes
            control_sample = control_metrics.get("sample_size", 0)
            treatment_sample = treatment_metrics.get("sample_size", 0)

            # Run chi-square test if success/failure counts are available
            if all(k in control_metrics and k in treatment_metrics for k in ["successes", "failures"]):
                chi_result = self.chi_square_test(
                    {"successes": control_metrics["successes"], "failures": control_metrics["failures"]},
                    {"successes": treatment_metrics["successes"], "failures": treatment_metrics["failures"]},
                    significance_level=alpha,
                )
                statistical_tests["chi_square"] = chi_result

            # Run t-tests for continuous metrics
            continuous_metrics = ["accuracy", "f1_score", "precision", "recall", "auc_score", "ndcg_score", "mrr_score"]

            for metric in continuous_metrics:
                control_val = control_metrics.get(metric)
                treatment_val = treatment_metrics.get(metric)

                # If we have arrays of values, run t-test
                if isinstance(control_val, (list, np.ndarray)) and isinstance(treatment_val, (list, np.ndarray)):
                    result = self.t_test_independent(
                        np.array(control_val),
                        np.array(treatment_val),
                        significance_level=alpha,
                        equal_var=False,
                    )
                    statistical_tests[f"t_test_{metric}"] = result

            # If we have individual metric values, we can still do comparison
            # using the metrics directly if sample sizes are available
            if control_sample > 0 and treatment_sample > 0:
                # Create comparison tests for key metrics
                for metric in ["f1_score", "accuracy"]:
                    if metric in control_metrics and metric in treatment_metrics:
                        c_val = control_metrics[metric]
                        t_val = treatment_metrics[metric]

                        if isinstance(c_val, (int, float)) and isinstance(t_val, (int, float)):
                            # Estimate standard error from sample size if not provided
                            # Assuming binomial variance for accuracy-like metrics
                            variance_proxy = max(c_val * (1 - c_val), t_val * (1 - t_val))

                            # Create synthetic distributions for testing
                            # This is an approximation when we only have summary statistics
                            control_std = np.sqrt(variance_proxy / control_sample) if control_sample > 0 else 0.01
                            treatment_std = np.sqrt(variance_proxy / treatment_sample) if treatment_sample > 0 else 0.01

                            # Use z-test approximation for large samples
                            if control_sample >= 30 and treatment_sample >= 30:
                                se_diff = np.sqrt(control_std**2 + treatment_std**2)
                                z_stat = (t_val - c_val) / se_diff if se_diff > 0 else 0
                                p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

                                statistical_tests[f"z_test_{metric}"] = StatisticalTestResult(
                                    test_type=TestType.T_TEST_INDEPENDENT,  # Using as proxy
                                    statistic=float(z_stat),
                                    p_value=float(p_value),
                                    is_significant=p_value < alpha,
                                    significance_level=alpha,
                                    confidence_interval=(
                                        float(t_val - c_val - 1.96 * se_diff),
                                        float(t_val - c_val + 1.96 * se_diff),
                                    ),
                                    effect_size=float((t_val - c_val) / np.sqrt(variance_proxy) if variance_proxy > 0 else 0),
                                    interpretation=f"Z-test approximation for {metric}: z={z_stat:.3f}, p={p_value:.4f}",
                                )

            # Determine winner based on F1 score (primary) or accuracy
            control_f1 = control_metrics.get("f1_score", 0) or 0
            treatment_f1 = treatment_metrics.get("f1_score", 0) or 0

            control_accuracy = control_metrics.get("accuracy", 0) or 0
            treatment_accuracy = treatment_metrics.get("accuracy", 0) or 0

            # Calculate confidence based on statistical test results
            significant_tests = [t for t in statistical_tests.values() if t.is_significant]
            confidence = len(significant_tests) / len(statistical_tests) if statistical_tests else 0.5

            # Determine winner
            if treatment_f1 > control_f1:
                winner = "treatment"
                diff_pct = (treatment_f1 - control_f1) / control_f1 * 100 if control_f1 > 0 else 0
            elif control_f1 > treatment_f1:
                winner = "control"
                diff_pct = (control_f1 - treatment_f1) / treatment_f1 * 100 if treatment_f1 > 0 else 0
            else:
                winner = "tie"
                diff_pct = 0

            # Generate recommendation
            recommendation = self._generate_recommendation(
                winner, confidence, diff_pct, statistical_tests, control_sample, treatment_sample
            )

            logger.info(
                f"A/B comparison complete: control={control_model_id}, treatment={treatment_model_id}, "
                f"winner={winner}, confidence={confidence:.2%}"
            )

            return ABTestComparison(
                control_model_id=control_model_id,
                treatment_model_id=treatment_model_id,
                control_metrics=control_metrics,
                treatment_metrics=treatment_metrics,
                statistical_tests=statistical_tests,
                winner=winner,
                confidence=confidence,
                recommendation=recommendation,
                sample_sizes={"control": control_sample, "treatment": treatment_sample},
            )

        except Exception as e:
            logger.error(
                f"Error comparing models {control_model_id} vs {treatment_model_id}: {e}",
                exc_info=True,
            )
            return ABTestComparison(
                control_model_id=control_model_id,
                treatment_model_id=treatment_model_id,
                control_metrics=control_metrics,
                treatment_metrics=treatment_metrics,
                statistical_tests={},
                winner="inconclusive",
                confidence=0.0,
                recommendation=f"Error during analysis: {str(e)}",
                sample_sizes={"control": control_sample, "treatment": treatment_sample},
            )

    def analyze_from_database(
        self,
        control_model_id: str,
        treatment_model_id: str,
        db_session: Any,
        dataset_type: str = "production",
        significance_level: Optional[float] = None,
    ) -> Optional[ABTestComparison]:
        """
        Perform A/B comparison using data from the database.

        Fetches performance history for both models and performs
        statistical comparison.

        Args:
            control_model_id: UUID of control model version
            treatment_model_id: UUID of treatment model version
            db_session: Database session
            dataset_type: Type of dataset to analyze (production, test, etc.)
            significance_level: Significance level for tests

        Returns:
            ABTestComparison with analysis results or None if data unavailable

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> comparison = analyzer.analyze_from_database(
            ...     'control-uuid', 'treatment-uuid', db, 'production'
            ... )
            >>> if comparison and comparison.winner == 'treatment':
            ...     print("Treatment model performed better")
        """
        if db_session is None:
            logger.debug("No database session provided for A/B analysis")
            return None

        try:
            # Fetch performance history for control model
            control_records = (
                db_session.query(ModelPerformanceHistory)
                .filter(
                    ModelPerformanceHistory.model_version_id == control_model_id,
                    ModelPerformanceHistory.dataset_type == dataset_type,
                )
                .order_by(ModelPerformanceHistory.created_at.desc())
                .limit(100)
                .all()
            )

            # Fetch performance history for treatment model
            treatment_records = (
                db_session.query(ModelPerformanceHistory)
                .filter(
                    ModelPerformanceHistory.model_version_id == treatment_model_id,
                    ModelPerformanceHistory.dataset_type == dataset_type,
                )
                .order_by(ModelPerformanceHistory.created_at.desc())
                .limit(100)
                .all()
            )

            if not control_records or not treatment_records:
                logger.warning(
                    f"Insufficient data for A/B analysis: "
                    f"control={len(control_records)}, treatment={len(treatment_records)}"
                )
                return None

            # Aggregate metrics
            control_metrics = self._aggregate_metrics(control_records)
            treatment_metrics = self._aggregate_metrics(treatment_records)

            # Perform comparison
            return self.compare_models(
                control_model_id,
                treatment_model_id,
                control_metrics,
                treatment_metrics,
                significance_level,
                db_session,
            )

        except Exception as e:
            logger.error(
                f"Error analyzing A/B test from database: {e}",
                exc_info=True,
            )
            return None

    def calculate_required_sample_size(
        self,
        expected_effect_size: float = 0.1,
        power: float = 0.8,
        significance_level: Optional[float] = None,
        test_type: str = "two_sided",
    ) -> int:
        """
        Calculate required sample size for detecting an effect.

        Uses power analysis to determine the minimum sample size needed
        to detect a statistically significant effect.

        Args:
            expected_effect_size: Expected effect size (Cohen's d)
            power: Statistical power (1 - beta, probability of detecting true effect)
            significance_level: Significance level (alpha)
            test_type: Type of test ('two_sided', 'larger', 'smaller')

        Returns:
            Required sample size per group

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> n = analyzer.calculate_required_sample_size(expected_effect_size=0.2, power=0.8)
            >>> print(f"Need {n} samples per group")
        """
        alpha = significance_level or self.default_significance_level

        try:
            # Use scipy's power analysis
            # For t-test, we use TTestPower
            from scipy.stats import ttest_ind
            from statsmodels.stats.power import TTestIndPower

            power_analysis = TTestIndPower()

            # Calculate required sample size
            # For two-sided test: alternative='two-sided'
            # For one-sided tests: alternative='larger' or 'smaller'
            alternative_map = {
                "two_sided": "two-sided",
                "larger": "larger",
                "smaller": "smaller",
            }
            alternative = alternative_map.get(test_type, "two-sided")

            n = power_analysis.solve_power(
                effect_size=expected_effect_size,
                power=power,
                alpha=alpha,
                alternative=alternative,
            )

            required_n = int(np.ceil(n))

            logger.info(
                f"Sample size calculation: effect_size={expected_effect_size}, "
                f"power={power}, alpha={alpha}, n_per_group={required_n}"
            )

            return required_n

        except ImportError:
            # Fallback calculation if statsmodels not available
            logger.warning("statsmodels not available, using approximation for sample size")
            return self._approximate_sample_size(expected_effect_size, power, alpha)
        except Exception as e:
            logger.error(f"Error calculating sample size: {e}", exc_info=True)
            return 1000  # Safe default

    def _approximate_sample_size(
        self,
        effect_size: float,
        power: float,
        alpha: float,
    ) -> int:
        """
        Approximate sample size calculation without statsmodels.

        Uses the formula: n = 2 * ((z_alpha + z_beta) / effect_size)^2
        """
        try:
            z_alpha = stats.norm.ppf(1 - alpha/2)  # Two-sided
            z_beta = stats.norm.ppf(power)

            n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            return int(np.ceil(n))
        except Exception:
            return 1000

    def calculate_bayesian_probability(
        self,
        control_successes: int,
        control_trials: int,
        treatment_successes: int,
        treatment_trials: int,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
    ) -> Dict[str, float]:
        """
        Calculate Bayesian probability that treatment is better than control.

        Uses Beta-Binomial conjugate prior model to compute posterior
        probability of treatment being superior.

        Args:
            control_successes: Number of successes in control group
            control_trials: Total trials in control group
            treatment_successes: Number of successes in treatment group
            treatment_trials: Total trials in treatment group
            prior_alpha: Alpha parameter for Beta prior (default: 1 = uniform)
            prior_beta: Beta parameter for Beta prior (default: 1 = uniform)

        Returns:
            Dictionary with posterior probabilities and credible intervals

        Example:
            >>> analyzer = ABTestAnalyzer()
            >>> result = analyzer.calculate_bayesian_probability(850, 1000, 890, 1000)
            >>> print(f"P(treatment > control) = {result['prob_treatment_better']:.2%}")
        """
        try:
            # Posterior parameters (conjugate update)
            control_alpha = prior_alpha + control_successes
            control_beta = prior_beta + (control_trials - control_successes)

            treatment_alpha = prior_alpha + treatment_successes
            treatment_beta = prior_beta + (treatment_trials - treatment_successes)

            # Monte Carlo estimation of P(treatment > control)
            n_samples = 100000
            control_samples = np.random.beta(control_alpha, control_beta, n_samples)
            treatment_samples = np.random.beta(treatment_alpha, treatment_beta, n_samples)

            prob_treatment_better = np.mean(treatment_samples > control_samples)
            prob_control_better = 1 - prob_treatment_better

            # Expected values (posterior means)
            control_rate = control_alpha / (control_alpha + control_beta)
            treatment_rate = treatment_alpha / (treatment_alpha + treatment_beta)

            # Credible intervals (95%)
            control_ci = (
                stats.beta.ppf(0.025, control_alpha, control_beta),
                stats.beta.ppf(0.975, control_alpha, control_beta),
            )
            treatment_ci = (
                stats.beta.ppf(0.025, treatment_alpha, treatment_beta),
                stats.beta.ppf(0.975, treatment_alpha, treatment_beta),
            )

            # Probability of meaningful improvement (>1% relative)
            relative_improvement = treatment_samples / control_samples - 1
            prob_meaningful_improvement = np.mean(relative_improvement > 0.01)

            result = {
                "prob_treatment_better": float(prob_treatment_better),
                "prob_control_better": float(prob_control_better),
                "control_expected_rate": float(control_rate),
                "treatment_expected_rate": float(treatment_rate),
                "control_credible_interval": [float(control_ci[0]), float(control_ci[1])],
                "treatment_credible_interval": [float(treatment_ci[0]), float(treatment_ci[1])],
                "prob_meaningful_improvement": float(prob_meaningful_improvement),
                "expected_relative_improvement": float(np.mean(relative_improvement) * 100),
            }

            logger.info(
                f"Bayesian analysis: P(treatment>control)={prob_treatment_better:.2%}, "
                f"expected improvement={result['expected_relative_improvement']:.1f}%"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating Bayesian probability: {e}", exc_info=True)
            return {
                "prob_treatment_better": 0.5,
                "prob_control_better": 0.5,
                "error": str(e),
            }

    def _aggregate_metrics(
        self, records: List[ModelPerformanceHistory]
    ) -> Dict[str, Any]:
        """
        Aggregate metrics from performance history records.

        Args:
            records: List of ModelPerformanceHistory records

        Returns:
            Dictionary with aggregated metrics
        """
        if not records:
            return {}

        try:
            # Get latest record for primary metrics
            latest = records[0]

            # Calculate aggregates
            f1_scores = [float(r.f1_score) for r in records if r.f1_score is not None]
            accuracies = [float(r.accuracy) for r in records if r.accuracy is not None]
            precisions = [float(r.precision) for r in records if r.precision is not None]
            recalls = [float(r.recall) for r in records if r.recall is not None]
            sample_sizes = [r.sample_size for r in records if r.sample_size is not None]

            return {
                "accuracy": float(latest.accuracy) if latest.accuracy else None,
                "precision": float(latest.precision) if latest.precision else None,
                "recall": float(latest.recall) if latest.recall else None,
                "f1_score": float(latest.f1_score) if latest.f1_score else None,
                "auc_score": float(latest.auc_score) if latest.auc_score else None,
                "sample_size": sum(sample_sizes) if sample_sizes else 0,
                "record_count": len(records),
                "avg_f1_score": sum(f1_scores) / len(f1_scores) if f1_scores else None,
                "avg_accuracy": sum(accuracies) / len(accuracies) if accuracies else None,
            }

        except Exception as e:
            logger.error(f"Error aggregating metrics: {e}", exc_info=True)
            return {}

    def _interpret_effect_size(self, effect_size: float, measure: str = "cohens_d") -> str:
        """
        Interpret effect size magnitude.

        Args:
            effect_size: The effect size value
            measure: Type of effect size measure ('cohens_d' or 'cramers_v')

        Returns:
            Human-readable interpretation
        """
        if measure == "cohens_d":
            abs_d = abs(effect_size)
            if abs_d < self.EFFECT_SIZE_SMALL:
                return "negligible"
            elif abs_d < self.EFFECT_SIZE_MEDIUM:
                return "small"
            elif abs_d < self.EFFECT_SIZE_LARGE:
                return "medium"
            else:
                return "large"
        elif measure == "cramers_v":
            # Cramer's V interpretation depends on degrees of freedom
            if effect_size < 0.1:
                return "negligible"
            elif effect_size < 0.3:
                return "small"
            elif effect_size < 0.5:
                return "medium"
            else:
                return "large"
        else:
            return "unknown"

    def _generate_recommendation(
        self,
        winner: str,
        confidence: float,
        diff_pct: float,
        statistical_tests: Dict[str, StatisticalTestResult],
        control_sample: int,
        treatment_sample: int,
    ) -> str:
        """
        Generate actionable recommendation based on test results.

        Args:
            winner: Which model won ('control', 'treatment', or 'tie')
            confidence: Confidence level in the result
            diff_pct: Percentage difference in performance
            statistical_tests: Dictionary of statistical test results
            control_sample: Sample size for control
            treatment_sample: Sample size for treatment

        Returns:
            Human-readable recommendation string
        """
        # Check sample size adequacy
        min_required = max(self.min_sample_size, 100)

        if control_sample < min_required or treatment_sample < min_required:
            return (
                f"Continue A/B test to gather more data. "
                f"Current samples: control={control_sample}, treatment={treatment_sample} "
                f"(recommend {min_required}+ per group)."
            )

        # Check significance
        significant_tests = [t for t in statistical_tests.values() if t.is_significant]

        if winner == "treatment":
            if confidence >= 0.8 and len(significant_tests) >= 1:
                return (
                    f"STRONG RECOMMENDATION: Promote treatment model. "
                    f"Statistically significant improvement of {diff_pct:.1f}% "
                    f"with {confidence:.0%} confidence."
                )
            elif confidence >= 0.5:
                return (
                    f"MODERATE RECOMMENDATION: Consider promoting treatment model. "
                    f"Shows improvement of {diff_pct:.1f}% but needs more data for high confidence. "
                    f"Consider continuing test or canary deployment."
                )
            else:
                return (
                    f"WEAK RECOMMENDATION: Treatment shows improvement of {diff_pct:.1f}% "
                    f"but results are not statistically significant. Continue testing."
                )
        elif winner == "control":
            if confidence >= 0.8 and len(significant_tests) >= 1:
                return (
                    f"STRONG RECOMMENDATION: Keep control model. "
                    f"Treatment underperforms by {diff_pct:.1f}% "
                    f"with {confidence:.0%} confidence."
                )
            else:
                return (
                    f"MODERATE RECOMMENDATION: Keep control model. "
                    f"Treatment does not show significant improvement."
                )
        else:
            return (
                f"NO RECOMMENDATION: Models perform equivalently. "
                f"Consider other factors (cost, latency, complexity) for decision."
            )
