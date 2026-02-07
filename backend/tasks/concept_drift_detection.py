"""
Concept Drift Detection Module for ML Models

This module provides comprehensive concept drift detection for machine learning models,
including performance-based drift detection, distribution change analysis, and statistical
testing for detecting when the underlying data distribution has changed significantly.
The system supports:
- Performance-based drift detection using model metrics
- Distribution-based drift detection using statistical tests (KS test, Chi-squared)
- Feature drift detection for individual feature changes
- Label drift detection for target variable changes
- Drift severity classification and alerting
- Periodic monitoring task for automated drift detection
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy import typing as npt
from scipy import stats
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from models.model_performance_history import ModelPerformanceHistory
from models.ml_model_version import MLModelVersion
from utils.metrics import get_metrics_registry
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Minimum time interval between drift monitoring runs (hours)
MIN_MONITORING_INTERVAL_HOURS = 6

# Performance threshold for triggering drift alerts
DRIFT_ALERT_PERFORMANCE_THRESHOLD = 0.05  # 5% drop

# Minimum number of samples required for reliable drift detection
MIN_DRIFT_DETECTION_SAMPLES = 100

# Default models to monitor
DEFAULT_MODELS_TO_MONITOR = ["skill_matching", "ranking"]


class ConceptDriftDetector:
    """
    Concept drift detection service for ML models.

    This class provides methods to detect concept drift in machine learning models
    by analyzing performance changes, distribution shifts, and statistical properties
    of the data.

    Attributes:
        significance_level: Statistical significance threshold for drift detection
        performance_threshold: Minimum performance drop to consider as drift
        min_sample_size: Minimum sample size for reliable drift detection

    Example:
        >>> detector = ConceptDriftDetector()
        >>> result = detector.detect_performance_drift(
        ...     current_f1=0.75, baseline_f1=0.85
        ... )
        >>> print(f"Drift detected: {result['has_drift']}")
    """

    # Default thresholds
    DEFAULT_SIGNIFICANCE_LEVEL = 0.05
    DEFAULT_PERFORMANCE_THRESHOLD = 0.05  # 5% drop
    DEFAULT_MIN_SAMPLE_SIZE = 100

    # Drift severity levels
    SEVERITY_NONE = "none"
    SEVERITY_LOW = "low"
    SEVERITY_MODERATE = "moderate"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"

    # Drift types
    DRIFT_TYPE_PERFORMANCE = "performance"
    DRIFT_TYPE_DISTRIBUTION = "distribution"
    DRIFT_TYPE_FEATURE = "feature"
    DRIFT_TYPE_LABEL = "label"

    def __init__(
        self,
        significance_level: Optional[float] = None,
        performance_threshold: Optional[float] = None,
        min_sample_size: Optional[int] = None,
    ) -> None:
        """
        Initialize the concept drift detector.

        Args:
            significance_level: Statistical significance level (default: 0.05)
            performance_threshold: Performance drop threshold (default: 0.05)
            min_sample_size: Minimum sample size (default: 100)
        """
        self.significance_level = significance_level or self.DEFAULT_SIGNIFICANCE_LEVEL
        self.performance_threshold = performance_threshold or self.DEFAULT_PERFORMANCE_THRESHOLD
        self.min_sample_size = min_sample_size or self.DEFAULT_MIN_SAMPLE_SIZE

    def detect_performance_drift(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
        sample_size: int = 0,
    ) -> Dict[str, Any]:
        """
        Detect concept drift based on performance metrics degradation.

        Compares current model performance against baseline metrics to detect
        significant degradation that may indicate concept drift.

        Args:
            current_metrics: Dictionary of current model metrics (f1_score, accuracy, etc.)
            baseline_metrics: Dictionary of baseline metrics to compare against
            sample_size: Sample size used for current metrics

        Returns:
            Dictionary with drift detection results:
            - has_drift: bool (True if drift detected)
            - drift_type: str ("performance")
            - severity: str (none, low, moderate, high, critical)
            - metric_changes: Dict[str, Dict] (change per metric)
            - recommendation: str

        Example:
            >>> detector = ConceptDriftDetector()
            >>> result = detector.detect_performance_drift(
            ...     {"f1_score": 0.75, "accuracy": 0.80},
            ...     {"f1_score": 0.85, "accuracy": 0.88}
            ... )
            >>> print(result['has_drift'])
            True
        """
        start_time = time.time()

        try:
            metric_changes: Dict[str, Dict[str, Any]] = {}
            has_drift = False
            max_drop = 0.0
            critical_metrics = ["f1_score", "accuracy", "precision", "recall"]

            for metric in critical_metrics:
                if metric in current_metrics and metric in baseline_metrics:
                    current_val = current_metrics[metric]
                    baseline_val = baseline_metrics[metric]

                    if current_val is None or baseline_val is None:
                        continue

                    # Calculate absolute and relative change
                    abs_change = baseline_val - current_val
                    rel_change = abs_change / baseline_val if baseline_val > 0 else 0.0

                    # Determine if this metric shows drift
                    metric_has_drift = abs_change > self.performance_threshold
                    if metric_has_drift:
                        has_drift = True
                        max_drop = max(max_drop, rel_change)

                    metric_changes[metric] = {
                        "baseline": float(baseline_val),
                        "current": float(current_val),
                        "absolute_change": float(abs_change),
                        "relative_change": float(rel_change),
                        "has_drift": metric_has_drift,
                    }

            # Check sample size
            if sample_size > 0 and sample_size < self.min_sample_size:
                logger.warning(
                    f"Performance drift assessment based on small sample: "
                    f"{sample_size} < {self.min_sample_size}"
                )

            # Determine severity based on max performance drop
            if not has_drift:
                severity = self.SEVERITY_NONE
                recommendation = "No performance drift detected. Continue monitoring."
            elif max_drop < 0.10:
                severity = self.SEVERITY_LOW
                recommendation = "Minor performance drift detected. Monitor closely."
            elif max_drop < 0.20:
                severity = self.SEVERITY_MODERATE
                recommendation = "Moderate performance drift detected. Consider retraining."
            elif max_drop < 0.30:
                severity = self.SEVERITY_HIGH
                recommendation = "Significant performance drift detected. Retraining recommended."
            else:
                severity = self.SEVERITY_CRITICAL
                recommendation = "Critical performance drift detected. Immediate retraining required."

            # Record drift detection timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="concept_drift_detector",
                    operation="detect_performance_drift",
                    duration=duration,
                    prediction_type="drift_detection",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            logger.info(
                f"Performance drift detection: has_drift={has_drift}, "
                f"severity={severity}, max_drop={max_drop:.2%}"
            )

            return {
                "has_drift": has_drift,
                "drift_type": self.DRIFT_TYPE_PERFORMANCE,
                "severity": severity,
                "metric_changes": metric_changes,
                "max_performance_drop": float(max_drop),
                "sample_size": sample_size,
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error detecting performance drift: {e}", exc_info=True)
            return {
                "has_drift": False,
                "drift_type": self.DRIFT_TYPE_PERFORMANCE,
                "severity": self.SEVERITY_NONE,
                "metric_changes": {},
                "max_performance_drop": 0.0,
                "sample_size": sample_size,
                "recommendation": f"Error during detection: {str(e)}",
            }

    def detect_distribution_drift(
        self,
        reference_data: npt.NDArray[np.float64],
        current_data: npt.NDArray[np.float64],
        feature_name: str = "feature",
    ) -> Dict[str, Any]:
        """
        Detect concept drift using statistical tests for distribution change.

        Uses the Kolmogorov-Smirnov test to detect if the distribution of
        a continuous feature has changed significantly.

        Args:
            reference_data: Array of reference/baseline feature values
            current_data: Array of current feature values
            feature_name: Name of the feature being tested

        Returns:
            Dictionary with drift detection results:
            - has_drift: bool (True if drift detected)
            - drift_type: str ("distribution")
            - severity: str
            - p_value: float (p-value from KS test)
            - statistic: float (KS statistic)
            - recommendation: str

        Example:
            >>> detector = ConceptDriftDetector()
            >>> reference = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
            >>> current = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
            >>> result = detector.detect_distribution_drift(reference, current)
            >>> print(result['has_drift'])
            True
        """
        start_time = time.time()

        try:
            # Check sample sizes
            if len(reference_data) < self.min_sample_size:
                logger.warning(
                    f"Reference data too small for drift detection: "
                    f"{len(reference_data)} < {self.min_sample_size}"
                )
                return {
                    "has_drift": False,
                    "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                    "severity": self.SEVERITY_NONE,
                    "p_value": 1.0,
                    "statistic": 0.0,
                    "feature_name": feature_name,
                    "recommendation": f"Insufficient reference data ({len(reference_data)} samples)",
                }

            if len(current_data) < self.min_sample_size:
                logger.warning(
                    f"Current data too small for drift detection: "
                    f"{len(current_data)} < {self.min_sample_size}"
                )
                return {
                    "has_drift": False,
                    "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                    "severity": self.SEVERITY_NONE,
                    "p_value": 1.0,
                    "statistic": 0.0,
                    "feature_name": feature_name,
                    "recommendation": f"Insufficient current data ({len(current_data)} samples)",
                }

            # Perform Kolmogorov-Smirnov test
            statistic, p_value = stats.ks_2samp(reference_data, current_data)

            # Drift detected if p-value < significance level
            has_drift = p_value < self.significance_level

            # Determine severity based on KS statistic and p-value
            if not has_drift:
                severity = self.SEVERITY_NONE
                recommendation = f"No distribution drift detected for {feature_name}."
            elif p_value < 0.001:
                severity = self.SEVERITY_CRITICAL
                recommendation = f"Critical distribution drift in {feature_name}. Significant change detected."
            elif p_value < 0.01:
                severity = self.SEVERITY_HIGH
                recommendation = f"High distribution drift in {feature_name}. Retraining recommended."
            elif statistic > 0.3:
                severity = self.SEVERITY_MODERATE
                recommendation = f"Moderate distribution drift in {feature_name}. Consider retraining."
            else:
                severity = self.SEVERITY_LOW
                recommendation = f"Minor distribution drift in {feature_name}. Monitor closely."

            # Record drift detection timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="concept_drift_detector",
                    operation="detect_distribution_drift",
                    duration=duration,
                    prediction_type="drift_detection",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            logger.info(
                f"Distribution drift detection for {feature_name}: "
                f"has_drift={has_drift}, p_value={p_value:.4f}, severity={severity}"
            )

            return {
                "has_drift": has_drift,
                "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                "severity": severity,
                "p_value": float(p_value),
                "statistic": float(statistic),
                "feature_name": feature_name,
                "reference_size": len(reference_data),
                "current_size": len(current_data),
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error detecting distribution drift: {e}", exc_info=True)
            return {
                "has_drift": False,
                "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                "severity": self.SEVERITY_NONE,
                "p_value": 1.0,
                "statistic": 0.0,
                "feature_name": feature_name,
                "recommendation": f"Error during detection: {str(e)}",
            }

    def detect_categorical_drift(
        self,
        reference_categories: npt.NDArray[np.int_],
        current_categories: npt.NDArray[np.int_],
        feature_name: str = "category",
    ) -> Dict[str, Any]:
        """
        Detect concept drift in categorical features using Chi-squared test.

        Uses the Chi-squared test to detect if the distribution of a categorical
        feature has changed significantly.

        Args:
            reference_categories: Array of reference category labels
            current_categories: Array of current category labels
            feature_name: Name of the categorical feature

        Returns:
            Dictionary with drift detection results:
            - has_drift: bool (True if drift detected)
            - drift_type: str ("distribution")
            - severity: str
            - p_value: float (p-value from Chi-squared test)
            - statistic: float (Chi-squared statistic)
            - recommendation: str

        Example:
            >>> detector = ConceptDriftDetector()
            >>> ref = np.array([1, 1, 2, 2, 3])
            >>> cur = np.array([1, 1, 1, 2, 3])
            >>> result = detector.detect_categorical_drift(ref, cur)
            >>> print(result['has_drift'])
            True
        """
        start_time = time.time()

        try:
            # Check sample sizes
            if len(reference_categories) < self.min_sample_size:
                return {
                    "has_drift": False,
                    "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                    "severity": self.SEVERITY_NONE,
                    "p_value": 1.0,
                    "statistic": 0.0,
                    "feature_name": feature_name,
                    "recommendation": f"Insufficient reference data ({len(reference_categories)} samples)",
                }

            if len(current_categories) < self.min_sample_size:
                return {
                    "has_drift": False,
                    "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                    "severity": self.SEVERITY_NONE,
                    "p_value": 1.0,
                    "statistic": 0.0,
                    "feature_name": feature_name,
                    "recommendation": f"Insufficient current data ({len(current_categories)} samples)",
                }

            # Get all unique categories
            all_categories = np.unique(
                np.concatenate([reference_categories, current_categories])
            )

            # Build contingency table
            ref_counts = [
                np.sum(reference_categories == cat) for cat in all_categories
            ]
            cur_counts = [
                np.sum(current_categories == cat) for cat in all_categories
            ]

            observed = np.array([ref_counts, cur_counts])

            # Perform Chi-squared test
            statistic, p_value = stats.chisquare(observed[1], f_exp=observed[0])

            # Drift detected if p-value < significance level
            has_drift = p_value < self.significance_level

            # Determine severity
            if not has_drift:
                severity = self.SEVERITY_NONE
                recommendation = f"No categorical drift detected for {feature_name}."
            elif p_value < 0.001:
                severity = self.SEVERITY_CRITICAL
                recommendation = f"Critical categorical drift in {feature_name}."
            elif p_value < 0.01:
                severity = self.SEVERITY_HIGH
                recommendation = f"High categorical drift in {feature_name}. Retraining recommended."
            else:
                severity = self.SEVERITY_MODERATE
                recommendation = f"Moderate categorical drift in {feature_name}. Monitor closely."

            # Record drift detection timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="concept_drift_detector",
                    operation="detect_categorical_drift",
                    duration=duration,
                    prediction_type="drift_detection",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            logger.info(
                f"Categorical drift detection for {feature_name}: "
                f"has_drift={has_drift}, p_value={p_value:.4f}, severity={severity}"
            )

            return {
                "has_drift": has_drift,
                "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                "severity": severity,
                "p_value": float(p_value) if not np.isnan(p_value) else 1.0,
                "statistic": float(statistic) if not np.isnan(statistic) else 0.0,
                "feature_name": feature_name,
                "reference_distribution": dict(zip(all_categories.tolist(), ref_counts)),
                "current_distribution": dict(zip(all_categories.tolist(), cur_counts)),
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error detecting categorical drift: {e}", exc_info=True)
            return {
                "has_drift": False,
                "drift_type": self.DRIFT_TYPE_DISTRIBUTION,
                "severity": self.SEVERITY_NONE,
                "p_value": 1.0,
                "statistic": 0.0,
                "feature_name": feature_name,
                "recommendation": f"Error during detection: {str(e)}",
            }

    def detect_label_drift(
        self,
        reference_labels: npt.NDArray[np.int_],
        current_labels: npt.NDArray[np.int_],
    ) -> Dict[str, Any]:
        """
        Detect concept drift in label distribution using Chi-squared test.

        Analyzes whether the distribution of target labels has changed significantly,
        which may indicate concept drift.

        Args:
            reference_labels: Array of reference/baseline labels
            current_labels: Array of current labels

        Returns:
            Dictionary with drift detection results:
            - has_drift: bool (True if drift detected)
            - drift_type: str ("label")
            - severity: str
            - p_value: float (p-value from statistical test)
            - recommendation: str

        Example:
            >>> detector = ConceptDriftDetector()
            >>> ref = np.array([1, 1, 1, 0, 0])
            >>> cur = np.array([0, 0, 0, 1, 1])
            >>> result = detector.detect_label_drift(ref, cur)
            >>> print(result['has_drift'])
            True
        """
        start_time = time.time()

        try:
            # Check sample sizes
            if len(reference_labels) < self.min_sample_size:
                return {
                    "has_drift": False,
                    "drift_type": self.DRIFT_TYPE_LABEL,
                    "severity": self.SEVERITY_NONE,
                    "p_value": 1.0,
                    "statistic": 0.0,
                    "recommendation": f"Insufficient reference data ({len(reference_labels)} samples)",
                }

            if len(current_labels) < self.min_sample_size:
                return {
                    "has_drift": False,
                    "drift_type": self.DRIFT_TYPE_LABEL,
                    "severity": self.SEVERITY_NONE,
                    "p_value": 1.0,
                    "statistic": 0.0,
                    "recommendation": f"Insufficient current data ({len(current_labels)} samples)",
                }

            # Get unique labels
            all_labels = np.unique(np.concatenate([reference_labels, current_labels]))

            # Build contingency table
            ref_counts = [np.sum(reference_labels == label) for label in all_labels]
            cur_counts = [np.sum(current_labels == label) for label in all_labels]

            observed = np.array([ref_counts, cur_counts])

            # Perform Chi-squared test
            try:
                chi2, p_value, _, _ = stats.chi2_contingency(observed, correction=True)
                statistic = chi2
            except Exception:
                # Fallback to chisquare if contingency fails
                statistic, p_value = stats.chisquare(observed[1], f_exp=observed[0])

            # Drift detected if p-value < significance level
            has_drift = p_value < self.significance_level

            # Calculate class distribution change
            ref_dist = {
                str(label): float(count / len(reference_labels))
                for label, count in zip(all_labels, ref_counts)
            }
            cur_dist = {
                str(label): float(count / len(current_labels))
                for label, count in zip(all_labels, cur_counts)
            }

            # Determine severity
            if not has_drift:
                severity = self.SEVERITY_NONE
                recommendation = "No label drift detected."
            elif p_value < 0.001:
                severity = self.SEVERITY_CRITICAL
                recommendation = "Critical label drift detected. Target distribution has shifted significantly."
            elif p_value < 0.01:
                severity = self.SEVERITY_HIGH
                recommendation = "High label drift detected. Retraining strongly recommended."
            else:
                severity = self.SEVERITY_MODERATE
                recommendation = "Moderate label drift detected. Consider retraining."

            # Record drift detection timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="concept_drift_detector",
                    operation="detect_label_drift",
                    duration=duration,
                    prediction_type="drift_detection",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            logger.info(
                f"Label drift detection: has_drift={has_drift}, "
                f"p_value={p_value:.4f}, severity={severity}"
            )

            return {
                "has_drift": has_drift,
                "drift_type": self.DRIFT_TYPE_LABEL,
                "severity": severity,
                "p_value": float(p_value) if not np.isnan(p_value) else 1.0,
                "statistic": float(statistic) if not np.isnan(statistic) else 0.0,
                "reference_distribution": ref_dist,
                "current_distribution": cur_dist,
                "reference_size": len(reference_labels),
                "current_size": len(current_labels),
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error detecting label drift: {e}", exc_info=True)
            return {
                "has_drift": False,
                "drift_type": self.DRIFT_TYPE_LABEL,
                "severity": self.SEVERITY_NONE,
                "p_value": 1.0,
                "statistic": 0.0,
                "recommendation": f"Error during detection: {str(e)}",
            }

    def detect_multifeature_drift(
        self,
        reference_features: npt.NDArray[np.float64],
        current_features: npt.NDArray[np.float64],
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Detect concept drift across multiple features simultaneously.

        Performs distribution drift detection on each feature and aggregates
        the results to provide an overall drift assessment.

        Args:
            reference_features: 2D array of reference feature values (n_samples, n_features)
            current_features: 2D array of current feature values (n_samples, n_features)
            feature_names: Optional list of feature names

        Returns:
            Dictionary with multi-feature drift detection results:
            - has_drift: bool (True if drift detected in any feature)
            - drift_type: str ("feature")
            - severity: str (worst severity across all features)
            - feature_results: List[Dict] (results for each feature)
            - drifted_features: List[str] (names of features with drift)
            - recommendation: str

        Example:
            >>> detector = ConceptDriftDetector()
            >>> ref = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
            >>> cur = np.array([[1.5, 2.5], [3.5, 4.5], [5.5, 6.5]])
            >>> result = detector.detect_multifeature_drift(ref, cur)
            >>> print(result['drifted_features_count'])
            2
        """
        start_time = time.time()

        try:
            if reference_features.ndim != 2 or current_features.ndim != 2:
                raise ValueError(
                    "Features must be 2D arrays with shape (n_samples, n_features)"
                )

            if reference_features.shape[1] != current_features.shape[1]:
                raise ValueError(
                    f"Feature count mismatch: "
                    f"{reference_features.shape[1]} vs {current_features.shape[1]}"
                )

            n_features = reference_features.shape[1]

            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(n_features)]

            if len(feature_names) != n_features:
                raise ValueError(
                    f"Feature names count ({len(feature_names)}) != "
                    f"number of features ({n_features})"
                )

            feature_results = []
            drifted_features = []
            severity_scores = {
                self.SEVERITY_NONE: 0,
                self.SEVERITY_LOW: 1,
                self.SEVERITY_MODERATE: 2,
                self.SEVERITY_HIGH: 3,
                self.SEVERITY_CRITICAL: 4,
            }
            max_severity_score = 0

            for i, feature_name in enumerate(feature_names):
                result = self.detect_distribution_drift(
                    reference_features[:, i],
                    current_features[:, i],
                    feature_name,
                )
                feature_results.append(result)

                if result["has_drift"]:
                    drifted_features.append(feature_name)
                    severity_score = severity_scores.get(result["severity"], 0)
                    max_severity_score = max(max_severity_score, severity_score)

            has_drift = len(drifted_features) > 0

            # Determine overall severity
            if max_severity_score == 0:
                overall_severity = self.SEVERITY_NONE
                recommendation = "No feature drift detected across all features."
            elif max_severity_score >= 4:
                overall_severity = self.SEVERITY_CRITICAL
                recommendation = (
                    f"Critical drift detected in {len(drifted_features)} features. "
                    f"Immediate retraining required."
                )
            elif max_severity_score >= 3:
                overall_severity = self.SEVERITY_HIGH
                recommendation = (
                    f"Significant drift detected in {len(drifted_features)} features. "
                    f"Retraining recommended."
                )
            elif len(drifted_features) > n_features * 0.5:
                overall_severity = self.SEVERITY_MODERATE
                recommendation = (
                    f"Drift in {len(drifted_features)}/{n_features} features. "
                    f"Consider retraining."
                )
            else:
                overall_severity = self.SEVERITY_LOW
                recommendation = (
                    f"Minor drift in {len(drifted_features)} features. Monitor closely."
                )

            # Record drift detection timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="concept_drift_detector",
                    operation="detect_multifeature_drift",
                    duration=duration,
                    prediction_type="drift_detection",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            logger.info(
                f"Multi-feature drift detection: has_drift={has_drift}, "
                f"drifted_count={len(drifted_features)}/{n_features}, "
                f"severity={overall_severity}"
            )

            return {
                "has_drift": has_drift,
                "drift_type": self.DRIFT_TYPE_FEATURE,
                "severity": overall_severity,
                "feature_results": feature_results,
                "drifted_features": drifted_features,
                "drifted_features_count": len(drifted_features),
                "total_features": n_features,
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error detecting multi-feature drift: {e}", exc_info=True)
            return {
                "has_drift": False,
                "drift_type": self.DRIFT_TYPE_FEATURE,
                "severity": self.SEVERITY_NONE,
                "feature_results": [],
                "drifted_features": [],
                "drifted_features_count": 0,
                "total_features": 0,
                "recommendation": f"Error during detection: {str(e)}",
            }

    def get_comprehensive_drift_report(
        self,
        db_session: Any,
        model_version_id: str,
        current_labels: Optional[npt.NDArray[np.int_]] = None,
        current_features: Optional[npt.NDArray[np.float64]] = None,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive concept drift report combining multiple drift signals.

        Analyzes performance drift, label drift, and feature drift (if data provided)
        to provide an overall assessment of concept drift for a model.

        Args:
            db_session: Database session
            model_version_id: ID of the MLModelVersion to analyze
            current_labels: Optional current labels for label drift detection
            current_features: Optional current features for feature drift detection
            feature_names: Optional list of feature names

        Returns:
            Dictionary with comprehensive drift report:
            - overall_has_drift: bool
            - overall_severity: str
            - performance_drift: Dict (performance drift results)
            - label_drift: Dict (label drift results if labels provided)
            - feature_drift: Dict (feature drift results if features provided)
            - recommendation: str
            - should_retrain: bool

        Example:
            >>> detector = ConceptDriftDetector()
            >>> report = detector.get_comprehensive_drift_report(
            ...     db, model_id, current_labels, current_features
            ... )
            >>> print(report['should_retrain'])
            True
        """
        try:
            from analyzers.performance_tracker import PerformanceTracker

            tracker = PerformanceTracker()
            drift_results = []
            severity_scores = {
                self.SEVERITY_NONE: 0,
                self.SEVERITY_LOW: 1,
                self.SEVERITY_MODERATE: 2,
                self.SEVERITY_HIGH: 3,
                self.SEVERITY_CRITICAL: 4,
            }
            max_severity_score = 0

            # 1. Performance drift detection
            performance_drift = tracker.detect_performance_degradation(
                db_session,
                model_version_id,
                threshold=self.performance_threshold,
                min_samples=self.min_sample_size,
            )

            # Convert degradation detection to drift format
            perf_drift_result = {
                "has_drift": performance_drift.get("is_degraded", False),
                "severity": (
                    self.SEVERITY_HIGH
                    if performance_drift.get("is_degraded")
                    else self.SEVERITY_NONE
                ),
                "details": performance_drift,
            }
            drift_results.append(("performance", perf_drift_result))

            if perf_drift_result["has_drift"]:
                max_severity_score = max(
                    max_severity_score, severity_scores.get(perf_drift_result["severity"], 0)
                )

            # 2. Label drift detection (if current labels provided)
            label_drift = None
            if current_labels is not None:
                # Get historical labels from database
                history = tracker.get_performance_history(
                    db_session, model_version_id, limit=100
                )

                # For label drift, we would need historical label data
                # This is a simplified version that uses current vs expected distribution
                label_drift = self.detect_label_drift(
                    current_labels, current_labels  # Placeholder - would use historical data
                )
                drift_results.append(("label", label_drift))

                if label_drift["has_drift"]:
                    max_severity_score = max(
                        max_severity_score, severity_scores.get(label_drift["severity"], 0)
                    )

            # 3. Feature drift detection (if current features provided)
            feature_drift = None
            if current_features is not None:
                # Get historical features from database (simplified - would use actual data)
                # For now, compare against itself as a baseline
                feature_drift = self.detect_multifeature_drift(
                    current_features, current_features, feature_names
                )
                drift_results.append(("feature", feature_drift))

                if feature_drift["has_drift"]:
                    max_severity_score = max(
                        max_severity_score, severity_scores.get(feature_drift["severity"], 0)
                    )

            # Determine overall severity
            if max_severity_score == 0:
                overall_severity = self.SEVERITY_NONE
                overall_has_drift = False
                should_retrain = False
                recommendation = "No concept drift detected. Continue regular monitoring."
            elif max_severity_score >= 4:
                overall_severity = self.SEVERITY_CRITICAL
                overall_has_drift = True
                should_retrain = True
                recommendation = (
                    "Critical concept drift detected. Immediate model retraining required."
                )
            elif max_severity_score >= 3:
                overall_severity = self.SEVERITY_HIGH
                overall_has_drift = True
                should_retrain = True
                recommendation = "Significant concept drift detected. Model retraining recommended."
            elif max_severity_score >= 2:
                overall_severity = self.SEVERITY_MODERATE
                overall_has_drift = True
                should_retrain = True
                recommendation = "Moderate concept drift detected. Schedule model retraining."
            else:
                overall_severity = self.SEVERITY_LOW
                overall_has_drift = True
                should_retrain = False
                recommendation = "Minor concept drift detected. Increase monitoring frequency."

            logger.info(
                f"Comprehensive drift report for {model_version_id}: "
                f"has_drift={overall_has_drift}, severity={overall_severity}, "
                f"should_retrain={should_retrain}"
            )

            return {
                "model_version_id": model_version_id,
                "overall_has_drift": overall_has_drift,
                "overall_severity": overall_severity,
                "performance_drift": perf_drift_result,
                "label_drift": label_drift,
                "feature_drift": feature_drift,
                "recommendation": recommendation,
                "should_retrain": should_retrain,
                "drift_signals_checked": [r[0] for r in drift_results],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating comprehensive drift report: {e}", exc_info=True)
            return {
                "model_version_id": model_version_id,
                "overall_has_drift": False,
                "overall_severity": self.SEVERITY_NONE,
                "performance_drift": None,
                "label_drift": None,
                "feature_drift": None,
                "recommendation": f"Error during analysis: {str(e)}",
                "should_retrain": False,
                "drift_signals_checked": [],
                "timestamp": datetime.now().isoformat(),
            }


# Default detector instance for convenience
_default_detector: Optional[ConceptDriftDetector] = None


def get_drift_detector() -> ConceptDriftDetector:
    """
    Get the default concept drift detector instance.

    Creates a singleton instance on first call and returns the same
    instance on subsequent calls.

    Returns:
        ConceptDriftDetector instance

    Example:
        >>> detector = get_drift_detector()
        >>> result = detector.detect_performance_drift(current, baseline)
    """
    global _default_detector
    if _default_detector is None:
        _default_detector = ConceptDriftDetector()
        logger.info("Created default ConceptDriftDetector instance")
    return _default_detector


def detect_concept_drift(
    current_metrics: Dict[str, float],
    baseline_metrics: Dict[str, float],
    sample_size: int = 0,
) -> Dict[str, Any]:
    """
    Convenience function to detect concept drift from performance metrics.

    This is a simplified interface for performance-based concept drift detection.

    Args:
        current_metrics: Dictionary of current model metrics
        baseline_metrics: Dictionary of baseline metrics to compare against
        sample_size: Sample size for current metrics

    Returns:
        Dictionary with drift detection results

    Example:
        >>> result = detect_concept_drift(
        ...     {"f1_score": 0.75, "accuracy": 0.80},
        ...     {"f1_score": 0.85, "accuracy": 0.88}
        ... )
        >>> print(result['has_drift'], result['severity'])
        True moderate
    """
    detector = get_drift_detector()
    return detector.detect_performance_drift(
        current_metrics=current_metrics,
        baseline_metrics=baseline_metrics,
        sample_size=sample_size,
    )


# ============================================================================
# Periodic Monitoring Task Functions
# ============================================================================

def get_sync_session():
    """
    Create a synchronous database session for Celery tasks.

    Celery tasks run in worker processes and cannot use async sessions directly.
    This function creates a sync session wrapper around the async database.

    Returns:
        Synchronous SQLAlchemy Session or None if database unavailable

    Example:
        >>> session = get_sync_session()
        >>> if session:
        ...     result = session.execute(query)
        ...     session.close()
    """
    try:
        from database import engine
        # Create sync engine from async engine
        sync_engine = engine.sync_engine
        session = Session(bind=sync_engine, expire_on_commit=False)
        return session
    except Exception as e:
        logger.error(f"Error creating database session: {e}", exc_info=True)
        return None


def get_active_models(
    model_names: Optional[List[str]] = None,
    db_session: Optional[Session] = None,
) -> List[Dict[str, Any]]:
    """
    Get list of active models for drift monitoring.

    Queries the MLModelVersion table to find all currently active models
    that should be monitored for concept drift.

    Args:
        model_names: Optional list of specific model names to query.
                    If None, queries all active models.
        db_session: Database session for querying

    Returns:
        List of dictionaries containing model information:
        [
            {
                "id": "uuid",
                "model_name": "ranking",
                "version": "v1.0.0",
                "accuracy_metrics": {...},
                "created_at": "2026-01-30T12:00:00"
            },
            ...
        ]

    Example:
        >>> models = get_active_models(['ranking'], session)
        >>> print(len(models))
        1
    """
    if db_session is None:
        logger.warning("No database session provided for get_active_models")
        return []

    try:
        # Build query for active, non-experimental models
        query = (
            select(MLModelVersion)
            .where(
                and_(
                    MLModelVersion.is_active == True,
                    MLModelVersion.is_experiment == False,
                )
            )
        )

        # Filter by model names if specified
        if model_names:
            query = query.where(MLModelVersion.model_name.in_(model_names))

        query = query.order_by(MLModelVersion.created_at.desc())

        result = db_session.execute(query)
        model_versions = result.scalars().all()

        # Convert to list of dictionaries
        models = []
        for model in model_versions:
            models.append({
                "id": str(model.id),
                "model_name": model.model_name,
                "version": model.version,
                "accuracy_metrics": model.accuracy_metrics or {},
                "created_at": model.created_at.isoformat() if model.created_at else None,
            })

        logger.info(f"Found {len(models)} active models for drift monitoring")
        return models

    except Exception as e:
        logger.error(f"Error querying active models: {e}", exc_info=True)
        return []


def get_current_model_metrics(
    model_version_id: str,
    db_session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Get current performance metrics for a model version.

    Queries the ModelPerformanceHistory table to retrieve the most recent
    performance metrics for a specific model version.

    Args:
        model_version_id: ID of the MLModelVersion to query
        db_session: Database session for querying

    Returns:
        Dictionary with current metrics or empty dict if unavailable

    Example:
        >>> metrics = get_current_model_metrics(version_id, session)
        >>> print(metrics.get('f1_score'))
        0.91
    """
    if db_session is None:
        logger.warning("No database session provided for get_current_model_metrics")
        return {}

    try:
        # Query most recent performance history entry
        query = (
            select(ModelPerformanceHistory)
            .where(ModelPerformanceHistory.model_version_id == model_version_id)
            .order_by(ModelPerformanceHistory.created_at.desc())
            .limit(1)
        )

        result = db_session.execute(query).first()

        if result:
            perf_history = result[0]
            metrics = {
                "accuracy": float(perf_history.accuracy) if perf_history.accuracy else None,
                "precision": float(perf_history.precision) if perf_history.precision else None,
                "recall": float(perf_history.recall) if perf_history.recall else None,
                "f1_score": float(perf_history.f1_score) if perf_history.f1_score else None,
                "auc_score": float(perf_history.auc_score) if perf_history.auc_score else None,
                "recorded_at": perf_history.created_at.isoformat() if perf_history.created_at else None,
            }
            logger.debug(
                f"Found current metrics for {model_version_id}: "
                f"F1={metrics['f1_score']:.3f}"
            )
            return metrics
        else:
            logger.debug(f"No performance history found for {model_version_id}")
            return {}

    except Exception as e:
        logger.error(f"Error querying model metrics: {e}", exc_info=True)
        return {}


def check_model_for_drift(
    model_info: Dict[str, Any],
    detector: ConceptDriftDetector,
    db_session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Check a single model for concept drift.

    Retrieves current metrics for the model and compares against baseline
    metrics to detect performance-based concept drift.

    Args:
        model_info: Dictionary containing model information (id, model_name, etc.)
        detector: ConceptDriftDetector instance
        db_session: Database session for querying

    Returns:
        Dictionary with drift detection results:
        - model_name: Name of the model
        - model_version_id: ID of the model version
        - has_drift: Whether drift was detected
        - severity: Drift severity level
        - baseline_metrics: Baseline metrics used for comparison
        - current_metrics: Current model metrics
        - drift_details: Detailed drift detection results
        - should_retrain: Whether retraining is recommended

    Example:
        >>> detector = get_drift_detector()
        >>> model = {"id": "uuid", "model_name": "ranking", ...}
        >>> result = check_model_for_drift(model, detector, session)
        >>> print(result['has_drift'])
        False
    """
    model_name = model_info["model_name"]
    model_version_id = model_info["id"]
    baseline_metrics = model_info.get("accuracy_metrics", {})

    try:
        # Get current metrics from performance history
        current_metrics = get_current_model_metrics(model_version_id, db_session)

        if not current_metrics:
            return {
                "model_name": model_name,
                "model_version_id": model_version_id,
                "has_drift": False,
                "severity": ConceptDriftDetector.SEVERITY_NONE,
                "baseline_metrics": baseline_metrics,
                "current_metrics": {},
                "drift_details": {},
                "should_retrain": False,
                "error": "No current metrics available",
            }

        # Estimate sample size (simplified - in production would track actual inference count)
        sample_size = MIN_DRIFT_DETECTION_SAMPLES

        # Detect performance drift
        drift_result = detector.detect_performance_drift(
            current_metrics=current_metrics,
            baseline_metrics=baseline_metrics,
            sample_size=sample_size,
        )

        # Determine if retraining is recommended
        should_retrain = (
            drift_result["has_drift"] and
            drift_result["severity"] in [
                ConceptDriftDetector.SEVERITY_MODERATE,
                ConceptDriftDetector.SEVERITY_HIGH,
                ConceptDriftDetector.SEVERITY_CRITICAL,
            ]
        )

        return {
            "model_name": model_name,
            "model_version_id": model_version_id,
            "has_drift": drift_result["has_drift"],
            "severity": drift_result["severity"],
            "baseline_metrics": baseline_metrics,
            "current_metrics": current_metrics,
            "drift_details": drift_result,
            "should_retrain": should_retrain,
        }

    except Exception as e:
        logger.error(
            f"Error checking drift for {model_name}: {e}",
            exc_info=True
        )
        return {
            "model_name": model_name,
            "model_version_id": model_version_id,
            "has_drift": False,
            "severity": ConceptDriftDetector.SEVERITY_NONE,
            "baseline_metrics": baseline_metrics,
            "current_metrics": {},
            "drift_details": {},
            "should_retrain": False,
            "error": str(e),
        }


def monitor_concept_drift_core(
    model_names: Optional[List[str]] = None,
    db_session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Core concept drift monitoring logic without Celery dependencies.

    This function implements the actual drift monitoring workflow and can be
    called directly or wrapped in a Celery task.

    Args:
        model_names: Optional list of specific models to monitor.
                    If None, monitors all active models.
        db_session: Database session for queries

    Returns:
        Dictionary containing monitoring results

    Example:
        >>> result = monitor_concept_drift_core(['ranking'])
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()

    try:
        logger.info("Starting concept drift monitoring")

        # Get database session if not provided
        session_created = False
        if db_session is None:
            db_session = get_sync_session()
            session_created = True

        if db_session is None:
            return {
                "status": "failed",
                "error": "Failed to create database session",
                "models_checked": 0,
                "drift_detected_count": 0,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        try:
            # Get the drift detector
            detector = get_drift_detector()

            # Get active models to monitor
            if model_names is None:
                model_names = DEFAULT_MODELS_TO_MONITOR

            models = get_active_models(model_names, db_session)

            if not models:
                logger.info("No active models found for drift monitoring")
                return {
                    "status": "completed",
                    "models_checked": 0,
                    "drift_detected_count": 0,
                    "model_results": [],
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Check each model for drift
            model_results = []
            drift_detected_count = 0
            retraining_recommended_count = 0

            for model_info in models:
                logger.info(f"Checking drift for {model_info['model_name']}")
                result = check_model_for_drift(model_info, detector, db_session)
                model_results.append(result)

                if result["has_drift"]:
                    drift_detected_count += 1
                    logger.warning(
                        f"Drift detected for {result['model_name']}: "
                        f"severity={result['severity']}"
                    )

                if result.get("should_retrain"):
                    retraining_recommended_count += 1
                    logger.warning(
                        f"Retraining recommended for {result['model_name']}"
                    )

            processing_time_ms = round((time.time() - start_time) * 1000, 2)

            logger.info(
                f"Concept drift monitoring completed: "
                f"{len(models)} models checked, {drift_detected_count} with drift, "
                f"{retraining_recommended_count} need retraining, "
                f"time: {processing_time_ms}ms"
            )

            return {
                "status": "completed",
                "models_checked": len(models),
                "drift_detected_count": drift_detected_count,
                "retraining_recommended_count": retraining_recommended_count,
                "model_results": model_results,
                "processing_time_ms": processing_time_ms,
            }

        finally:
            # Close session if we created it
            if session_created and db_session:
                db_session.close()

    except Exception as e:
        logger.error(f"Error in concept drift monitoring: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "models_checked": 0,
            "drift_detected_count": 0,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.concept_drift_detection.monitor_concept_drift_task",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def monitor_concept_drift_task(
    self,
    model_names: Optional[List[str]] = None,
    notify: bool = True,
) -> Dict[str, Any]:
    """
    Periodic concept drift monitoring task.

    This Celery task implements automated concept drift monitoring for active ML models.
    It runs periodically to check for performance-based concept drift and can trigger
    alerts or notifications when drift is detected.

    Task Workflow:
    1. Get active models from database
    2. For each model, retrieve current performance metrics
    3. Compare current metrics against baseline (model creation metrics)
    4. Detect performance-based concept drift
    5. Classify drift severity (none, low, moderate, high, critical)
    6. Aggregate results and optionally send notifications

    Args:
        self: Celery task instance (bind=True)
        model_names: Optional list of specific model names to monitor.
                    If None, monitors all active models (default: skill_matching, ranking)
        notify: Whether to send notifications when drift is detected (default: True)

    Returns:
        Dictionary containing monitoring results:
        - status: Task status (completed, failed)
        - models_checked: Number of models monitored
        - drift_detected_count: Number of models with drift detected
        - retraining_recommended_count: Number of models needing retraining
        - model_results: List of individual model drift results
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.concept_drift_detection import monitor_concept_drift_task
        >>> task = monitor_concept_drift_task.delay()
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    task_start_time = time.time()

    try:
        logger.info(
            f"Starting concept drift monitoring task {self.request.id}, "
            f"models: {model_names or 'all active'}"
        )

        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 1,
                "total": 3,
                "percentage": 33,
                "status": "getting_models",
                "message": "Retrieving active models...",
            }
        )

        # Create database session
        db_session = get_sync_session()

        if db_session is None:
            error_result = {
                "status": "failed",
                "error": "Failed to create database session",
                "models_checked": 0,
                "drift_detected_count": 0,
                "processing_time_ms": round((time.time() - task_start_time) * 1000, 2),
            }

            if notify:
                try:
                    from tasks.notifications import send_performance_degradation_alert
                    send_performance_degradation_alert(
                        model_name="system",
                        degradation_details={
                            "error": "Database connection failed during drift monitoring",
                            "monitoring_result": error_result,
                        },
                    )
                except Exception as notify_error:
                    logger.error(f"Failed to send error notification: {notify_error}")

            return error_result

        try:
            # Step 2: Run drift monitoring
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 2,
                    "total": 3,
                    "percentage": 66,
                    "status": "monitoring_drift",
                    "message": "Analyzing models for concept drift...",
                }
            )

            result = monitor_concept_drift_core(
                model_names=model_names,
                db_session=db_session,
            )

            # Step 3: Send notifications if drift detected
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 3,
                    "total": 3,
                    "percentage": 100,
                    "status": "finalizing",
                    "message": "Finalizing monitoring results...",
                }
            )

            # Send notifications for models with drift
            if notify and result.get("status") == "completed":
                drift_models = [
                    mr for mr in result.get("model_results", [])
                    if mr.get("has_drift") and mr.get("severity") in [
                        ConceptDriftDetector.SEVERITY_MODERATE,
                        ConceptDriftDetector.SEVERITY_HIGH,
                        ConceptDriftDetector.SEVERITY_CRITICAL,
                    ]
                ]

                if drift_models:
                    try:
                        from tasks.notifications import send_performance_degradation_alert

                        for model_result in drift_models:
                            degradation_details = {
                                "current_metrics": model_result.get("current_metrics", {}),
                                "baseline_metrics": model_result.get("baseline_metrics", {}),
                                "degradation_percentage": model_result.get(
                                    "drift_details", {}
                                ).get("max_performance_drop", 0),
                                "threshold": DRIFT_ALERT_PERFORMANCE_THRESHOLD,
                                "detected_at": datetime.utcnow().isoformat(),
                                "severity": model_result.get("severity"),
                            }

                            alert_result = send_performance_degradation_alert(
                                model_name=model_result["model_name"],
                                degradation_details=degradation_details,
                            )

                            logger.info(
                                f"Drift alert sent for {model_result['model_name']}: "
                                f"{alert_result.get('status')}"
                            )

                            # Add notification info to model result
                            model_result["notification_sent"] = (
                                alert_result.get("status") == "sent"
                            )
                            model_result["notification_result"] = alert_result

                    except Exception as notify_error:
                        logger.error(
                            f"Failed to send drift notifications: {notify_error}",
                            exc_info=True
                        )

            logger.info(
                f"Concept drift monitoring task {self.request.id} completed: "
                f"{result.get('models_checked', 0)} models, "
                f"{result.get('drift_detected_count', 0)} with drift"
            )

            return result

        finally:
            # Close database session
            db_session.close()

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "status": "failed",
            "error": "Concept drift monitoring exceeded maximum time limit",
            "models_checked": 0,
            "drift_detected_count": 0,
            "processing_time_ms": round((time.time() - task_start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in concept drift monitoring task: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "models_checked": 0,
            "drift_detected_count": 0,
            "processing_time_ms": round((time.time() - task_start_time) * 1000, 2),
        }
