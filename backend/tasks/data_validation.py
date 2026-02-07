"""
Data Validation Module for ML Model Retraining

This module provides comprehensive data validation for feedback quality checks
in the automated model retraining pipeline. The system supports:
- Skill feedback validation (correctness, confidence scores)
- Candidate feedback quality checks
- Data completeness and consistency validation
- Duplicate feedback detection
- Temporal validation (feedback age, recency)
- Label quality assessment for training data
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy import typing as npt

from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


class FeedbackValidator:
    """
    Data validation service for feedback quality checks.

    This class provides methods to validate feedback data for use in
    machine learning model training. It ensures data quality by checking
    completeness, consistency, and various quality metrics.

    Attributes:
        min_confidence_score: Minimum confidence score for valid feedback
        max_feedback_age_days: Maximum age of feedback to consider valid
        require_explicit_labels: Whether explicit labels are required

    Example:
        >>> validator = FeedbackValidator()
        >>> feedback_data = {"skill": "python", "was_correct": True, "confidence_score": 0.9}
        >>> result = validator.validate_skill_feedback(feedback_data)
        >>> print(f"Valid: {result['is_valid']}")
        Valid: True
    """

    # Default validation thresholds
    DEFAULT_MIN_CONFIDENCE = 0.3
    DEFAULT_MAX_FEEDBACK_AGE_DAYS = 90
    DEFAULT_MIN_SAMPLE_SIZE = 50

    # Validation result codes
    VALID = "valid"
    INVALID_LOW_CONFIDENCE = "invalid_low_confidence"
    INVALID_MISSING_FIELDS = "invalid_missing_fields"
    INVALID_TOO_OLD = "invalid_too_old"
    INVALID_DUPLICATE = "invalid_duplicate"
    INVALID_INCONSISTENT = "invalid_inconsistent"

    # Feedback types
    FEEDBACK_TYPE_SKILL = "skill_feedback"
    FEEDBACK_TYPE_CANDIDATE = "candidate_feedback"
    FEEDBACK_TYPE_MATCH = "match_feedback"

    def __init__(
        self,
        min_confidence_score: Optional[float] = None,
        max_feedback_age_days: Optional[int] = None,
        require_explicit_labels: bool = True,
    ) -> None:
        """
        Initialize the feedback validator.

        Args:
            min_confidence_score: Minimum confidence score for valid feedback
                                (defaults to DEFAULT_MIN_CONFIDENCE)
            max_feedback_age_days: Maximum age of feedback in days
                                  (defaults to DEFAULT_MAX_FEEDBACK_AGE_DAYS)
            require_explicit_labels: Whether explicit labels are required
        """
        self.min_confidence_score = min_confidence_score or self.DEFAULT_MIN_CONFIDENCE
        self.max_feedback_age_days = max_feedback_age_days or self.DEFAULT_MAX_FEEDBACK_AGE_DAYS
        self.require_explicit_labels = require_explicit_labels

    def validate_skill_feedback(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a single skill feedback entry.

        Checks if the feedback has all required fields, meets confidence
        threshold, and is within acceptable age range.

        Args:
            feedback_data: Dictionary containing feedback data with keys:
                          - skill: str (required)
                          - was_correct: bool (required)
                          - confidence_score: float (optional)
                          - created_at: datetime or str (optional)
                          - actual_skill: str (optional)

        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - reason: str (validation result code)
            - score: float (validation score 0-1)
            - issues: List[str] (list of validation issues)

        Example:
            >>> validator = FeedbackValidator()
            >>> feedback = {"skill": "python", "was_correct": True, "confidence_score": 0.9}
            >>> result = validator.validate_skill_feedback(feedback)
            >>> print(result['is_valid'])
            True
        """
        start_time = time.time()

        try:
            issues: List[str] = []
            score = 1.0

            # Check required fields
            required_fields = ["skill", "was_correct"]
            missing_fields = [
                field for field in required_fields if field not in feedback_data
            ]

            if missing_fields:
                issues.append(f"Missing required fields: {', '.join(missing_fields)}")
                score -= 0.5
                return {
                    "is_valid": False,
                    "reason": self.INVALID_MISSING_FIELDS,
                    "score": max(0.0, score),
                    "issues": issues,
                }

            # Validate skill field
            skill = feedback_data.get("skill", "")
            if not isinstance(skill, str) or not skill.strip():
                issues.append("Skill must be a non-empty string")
                score -= 0.3

            # Validate was_correct field
            was_correct = feedback_data.get("was_correct")
            if not isinstance(was_correct, bool):
                issues.append("was_correct must be a boolean")
                score -= 0.2

            # Validate confidence score if present
            confidence_score = feedback_data.get("confidence_score")
            if confidence_score is not None:
                if not isinstance(confidence_score, (int, float)):
                    issues.append("confidence_score must be numeric")
                    score -= 0.1
                elif confidence_score < self.min_confidence_score:
                    issues.append(
                        f"Confidence score {confidence_score} below threshold "
                        f"{self.min_confidence_score}"
                    )
                    score -= 0.2

            # Validate feedback age if timestamp provided
            created_at = feedback_data.get("created_at")
            if created_at is not None:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except ValueError:
                        issues.append(f"Invalid datetime format: {created_at}")
                        score -= 0.1
                        created_at = None

                if isinstance(created_at, datetime):
                    age = datetime.now(created_at.tzinfo) - created_at
                    if age > timedelta(days=self.max_feedback_age_days):
                        issues.append(
                            f"Feedback too old: {age.days} days "
                            f"(max: {self.max_feedback_age_days})"
                        )
                        score -= 0.3

            # Record validation timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="feedback_validator",
                    operation="validate_skill_feedback",
                    duration=duration,
                    prediction_type="validation",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            is_valid = score >= 0.7 and len(issues) == 0
            reason = self.VALID if is_valid else issues[0] if issues else self.VALID

            logger.debug(
                f"Validated skill feedback: skill={skill}, "
                f"valid={is_valid}, score={score:.2f}"
            )

            return {
                "is_valid": is_valid,
                "reason": reason,
                "score": max(0.0, score),
                "issues": issues,
            }

        except Exception as e:
            logger.error(f"Error validating skill feedback: {e}", exc_info=True)
            return {
                "is_valid": False,
                "reason": self.INVALID_INCONSISTENT,
                "score": 0.0,
                "issues": [f"Validation error: {str(e)}"],
            }

    def validate_feedback_batch(
        self, feedback_list: List[Dict[str, Any]], feedback_type: str = FEEDBACK_TYPE_SKILL
    ) -> Dict[str, Any]:
        """
        Validate a batch of feedback entries.

        Validates multiple feedback entries and provides aggregate statistics
        about the batch quality.

        Args:
            feedback_list: List of feedback dictionaries to validate
            feedback_type: Type of feedback (skill_feedback, candidate_feedback, match_feedback)

        Returns:
            Dictionary with batch validation results:
            - total_count: int
            - valid_count: int
            - invalid_count: int
            - validity_rate: float
            - average_score: float
            - results: List[Dict] (individual validation results)
            - quality_issues: Dict[str, int] (count of each issue type)

        Example:
            >>> validator = FeedbackValidator()
            >>> batch = [
            ...     {"skill": "python", "was_correct": True, "confidence_score": 0.9},
            ...     {"skill": "java", "was_correct": False, "confidence_score": 0.8}
            ... ]
            >>> result = validator.validate_feedback_batch(batch)
            >>> print(f"Valid: {result['valid_count']}/{result['total_count']}")
            Valid: 2/2
        """
        start_time = time.time()

        try:
            results = []
            valid_count = 0
            total_score = 0.0
            quality_issues: Dict[str, int] = {}

            for feedback_data in feedback_list:
                # Validate based on feedback type
                if feedback_type == self.FEEDBACK_TYPE_SKILL:
                    validation_result = self.validate_skill_feedback(feedback_data)
                else:
                    # Default to skill feedback validation for other types
                    validation_result = self.validate_skill_feedback(feedback_data)

                results.append(validation_result)

                if validation_result["is_valid"]:
                    valid_count += 1
                else:
                    reason = validation_result.get("reason", "unknown")
                    quality_issues[reason] = quality_issues.get(reason, 0) + 1

                total_score += validation_result["score"]

            total_count = len(feedback_list)
            invalid_count = total_count - valid_count
            validity_rate = valid_count / total_count if total_count > 0 else 0.0
            average_score = total_score / total_count if total_count > 0 else 0.0

            # Record batch validation timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="feedback_validator",
                    operation="validate_feedback_batch",
                    duration=duration,
                    prediction_type="batch_validation",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            logger.info(
                f"Validated feedback batch: {valid_count}/{total_count} valid "
                f"({validity_rate:.2%}), avg_score={average_score:.3f}"
            )

            return {
                "total_count": total_count,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "validity_rate": validity_rate,
                "average_score": average_score,
                "results": results,
                "quality_issues": quality_issues,
            }

        except Exception as e:
            logger.error(f"Error validating feedback batch: {e}", exc_info=True)
            return {
                "total_count": len(feedback_list),
                "valid_count": 0,
                "invalid_count": len(feedback_list),
                "validity_rate": 0.0,
                "average_score": 0.0,
                "results": [],
                "quality_issues": {self.INVALID_INCONSISTENT: len(feedback_list)},
            }

    def filter_valid_feedback(
        self, feedback_list: List[Dict[str, Any]], feedback_type: str = FEEDBACK_TYPE_SKILL
    ) -> List[Dict[str, Any]]:
        """
        Filter out invalid feedback entries.

        Returns only the feedback entries that pass validation checks.

        Args:
            feedback_list: List of feedback dictionaries
            feedback_type: Type of feedback to validate

        Returns:
            List of valid feedback dictionaries

        Example:
            >>> validator = FeedbackValidator()
            >>> batch = [{"skill": "python", "was_correct": True}]
            >>> valid = validator.filter_valid_feedback(batch)
            >>> len(valid)
            1
        """
        try:
            batch_result = self.validate_feedback_batch(feedback_list, feedback_type)
            valid_indices = [
                i for i, result in enumerate(batch_result["results"]) if result["is_valid"]
            ]
            return [feedback_list[i] for i in valid_indices]
        except Exception as e:
            logger.error(f"Error filtering valid feedback: {e}", exc_info=True)
            return []

    def check_label_distribution(
        self, labels: npt.NDArray[np.int_]
    ) -> Dict[str, Any]:
        """
        Check if label distribution is balanced enough for training.

        Analyzes the distribution of labels to detect class imbalance
        that could affect model training.

        Args:
            labels: Array of class labels

        Returns:
            Dictionary with distribution analysis:
            - is_balanced: bool
            - class_counts: Dict[int, int] (count per class)
            - class_proportions: Dict[int, float] (proportion per class)
            - imbalance_ratio: float (ratio of minority to majority class)
            - min_samples_per_class: int
            - recommendation: str

        Example:
            >>> validator = FeedbackValidator()
            >>> labels = np.array([1, 0, 1, 1, 0, 1])
            >>> dist = validator.check_label_distribution(labels)
            >>> print(dist['is_balanced'])
            True
        """
        try:
            unique_labels, counts = np.unique(labels, return_counts=True)
            total_samples = len(labels)

            class_counts = dict(zip(unique_labels.tolist(), counts.tolist()))
            class_proportions = {
                label: count / total_samples for label, count in class_counts.items()
            }

            if len(unique_labels) < 2:
                return {
                    "is_balanced": False,
                    "class_counts": class_counts,
                    "class_proportions": class_proportions,
                    "imbalance_ratio": 0.0,
                    "min_samples_per_class": min(counts.tolist()) if len(counts) > 0 else 0,
                    "recommendation": "Need at least 2 classes for training",
                }

            # Calculate imbalance ratio (minority / majority)
            min_count = min(counts)
            max_count = max(counts)
            imbalance_ratio = min_count / max_count if max_count > 0 else 0.0

            # Determine if balanced (ratio >= 0.3 is reasonably balanced)
            is_balanced = imbalance_ratio >= 0.3 and min_count >= self.DEFAULT_MIN_SAMPLE_SIZE

            if imbalance_ratio < 0.1:
                recommendation = "Severe class imbalance - consider oversampling or collecting more data"
            elif imbalance_ratio < 0.3:
                recommendation = "Moderate class imbalance - consider class weighting"
            elif min_count < self.DEFAULT_MIN_SAMPLE_SIZE:
                recommendation = f"Minority class has < {self.DEFAULT_MIN_SAMPLE_SIZE} samples"
            else:
                recommendation = "Label distribution is acceptable for training"

            logger.info(
                f"Label distribution check: balanced={is_balanced}, "
                f"imbalance_ratio={imbalance_ratio:.3f}"
            )

            return {
                "is_balanced": is_balanced,
                "class_counts": class_counts,
                "class_proportions": class_proportions,
                "imbalance_ratio": float(imbalance_ratio),
                "min_samples_per_class": int(min_count),
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error checking label distribution: {e}", exc_info=True)
            return {
                "is_balanced": False,
                "class_counts": {},
                "class_proportions": {},
                "imbalance_ratio": 0.0,
                "min_samples_per_class": 0,
                "recommendation": f"Error during analysis: {str(e)}",
            }

    def check_data_sufficiency(
        self,
        feedback_count: int,
        feature_count: int,
        min_samples_ratio: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Check if there's sufficient data for model training.

        Evaluates whether the dataset has enough samples relative to
        the number of features for reliable model training.

        Args:
            feedback_count: Number of feedback samples available
            feature_count: Number of features in the feature space
            min_samples_ratio: Minimum ratio of samples to features (default: 10)

        Returns:
            Dictionary with sufficiency analysis:
            - is_sufficient: bool
            - sample_count: int
            - feature_count: int
            - ratio: float
            - required_samples: int
            - recommendation: str

        Example:
            >>> validator = FeedbackValidator()
            >>> result = validator.check_data_sufficiency(1000, 50)
            >>> print(result['is_sufficient'])
            True
        """
        try:
            ratio = feedback_count / feature_count if feature_count > 0 else 0.0
            required_samples = int(feature_count * min_samples_ratio)

            if feedback_count < self.DEFAULT_MIN_SAMPLE_SIZE:
                is_sufficient = False
                recommendation = (
                    f"Insufficient data: {feedback_count} samples "
                    f"(minimum {self.DEFAULT_MIN_SAMPLE_SIZE} required)"
                )
            elif ratio < min_samples_ratio:
                is_sufficient = False
                recommendation = (
                    f"Insufficient data for {feature_count} features: "
                    f"need at least {required_samples} samples (ratio: {ratio:.1f})"
                )
            else:
                is_sufficient = True
                recommendation = (
                    f"Sufficient data: {feedback_count} samples for {feature_count} features"
                )

            logger.info(
                f"Data sufficiency check: sufficient={is_sufficient}, "
                f"ratio={ratio:.1f}, samples={feedback_count}"
            )

            return {
                "is_sufficient": is_sufficient,
                "sample_count": feedback_count,
                "feature_count": feature_count,
                "ratio": float(ratio),
                "required_samples": required_samples,
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error checking data sufficiency: {e}", exc_info=True)
            return {
                "is_sufficient": False,
                "sample_count": feedback_count,
                "feature_count": feature_count,
                "ratio": 0.0,
                "required_samples": int(feature_count * min_samples_ratio) if feature_count > 0 else 0,
                "recommendation": f"Error during analysis: {str(e)}",
            }

    def detect_duplicate_feedback(
        self, feedback_list: List[Dict[str, Any]], keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect potential duplicate feedback entries.

        Identifies feedback entries that may be duplicates based on
        specified key fields.

        Args:
            feedback_list: List of feedback dictionaries
            keys: Fields to use for duplicate detection (default: ["skill", "vacancy_id", "resume_id"])

        Returns:
            Dictionary with duplicate detection results:
            - duplicate_count: int
            - duplicate_indices: List[Tuple[int, int]] (pairs of duplicate indices)
            - unique_count: int
            - duplicate_rate: float

        Example:
            >>> validator = FeedbackValidator()
            >>> feedback = [
            ...     {"skill": "python", "resume_id": "1", "vacancy_id": "2", "was_correct": True},
            ...     {"skill": "python", "resume_id": "1", "vacancy_id": "2", "was_correct": False}
            ... ]
            >>> result = validator.detect_duplicate_feedback(feedback)
            >>> print(result['duplicate_count'])
            1
        """
        try:
            if keys is None:
                keys = ["skill", "resume_id", "vacancy_id"]

            # Create signature for each feedback entry
            signatures = []
            for i, feedback in enumerate(feedback_list):
                signature_parts = []
                for key in keys:
                    value = feedback.get(key, "")
                    signature_parts.append(str(value))
                signature = "|".join(signature_parts)
                signatures.append((i, signature))

            # Find duplicates
            seen = {}
            duplicate_indices = []
            for i, signature in signatures:
                if signature in seen:
                    duplicate_indices.append((seen[signature], i))
                else:
                    seen[signature] = i

            unique_count = len(feedback_list) - len(duplicate_indices)
            duplicate_count = len(duplicate_indices)
            duplicate_rate = duplicate_count / len(feedback_list) if feedback_list else 0.0

            logger.info(
                f"Duplicate detection: found {duplicate_count} duplicates "
                f"({duplicate_rate:.2%}) out of {len(feedback_list)} entries"
            )

            return {
                "duplicate_count": duplicate_count,
                "duplicate_indices": duplicate_indices,
                "unique_count": unique_count,
                "duplicate_rate": duplicate_rate,
            }

        except Exception as e:
            logger.error(f"Error detecting duplicates: {e}", exc_info=True)
            return {
                "duplicate_count": 0,
                "duplicate_indices": [],
                "unique_count": len(feedback_list),
                "duplicate_rate": 0.0,
            }

    def get_validation_summary(
        self, feedback_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get a comprehensive validation summary for feedback data.

        Combines multiple validation checks into a single summary report.

        Args:
            feedback_list: List of feedback dictionaries to analyze

        Returns:
            Dictionary with comprehensive validation summary:
            - batch_validation: Dict (batch validation results)
            - label_distribution: Dict (label distribution analysis)
            - data_sufficiency: Dict (data sufficiency check)
            - duplicate_analysis: Dict (duplicate detection results)
            - overall_quality_score: float
            - ready_for_training: bool

        Example:
            >>> validator = FeedbackValidator()
            >>> batch = [{"skill": "python", "was_correct": True}]
            >>> summary = validator.get_validation_summary(batch)
            >>> print(summary['ready_for_training'])
            False
        """
        try:
            # Batch validation
            batch_validation = self.validate_feedback_batch(feedback_list)

            # Label distribution
            labels = np.array([
                1 if f.get("was_correct", True) else 0 for f in feedback_list
            ])
            label_distribution = self.check_label_distribution(labels)

            # Data sufficiency (estimate feature count as 10 for skill feedback)
            estimated_features = 10
            valid_count = batch_validation["valid_count"]
            data_sufficiency = self.check_data_sufficiency(
                valid_count, estimated_features
            )

            # Duplicate detection
            duplicate_analysis = self.detect_duplicate_feedback(feedback_list)

            # Calculate overall quality score (0-1)
            validity_score = batch_validation["validity_rate"]
            balance_score = label_distribution["imbalance_ratio"]
            duplicate_penalty = duplicate_analysis["duplicate_rate"]
            sufficiency_score = 1.0 if data_sufficiency["is_sufficient"] else 0.0

            overall_quality_score = (
                (validity_score * 0.4) +
                (balance_score * 0.2) +
                (sufficiency_score * 0.3) +
                ((1 - duplicate_penalty) * 0.1)
            )

            # Determine if ready for training
            ready_for_training = (
                batch_validation["validity_rate"] >= 0.8 and
                label_distribution["is_balanced"] and
                data_sufficiency["is_sufficient"] and
                duplicate_analysis["duplicate_rate"] < 0.1
            )

            logger.info(
                f"Validation summary: quality_score={overall_quality_score:.3f}, "
                f"ready_for_training={ready_for_training}"
            )

            return {
                "batch_validation": batch_validation,
                "label_distribution": label_distribution,
                "data_sufficiency": data_sufficiency,
                "duplicate_analysis": duplicate_analysis,
                "overall_quality_score": float(overall_quality_score),
                "ready_for_training": ready_for_training,
            }

        except Exception as e:
            logger.error(f"Error generating validation summary: {e}", exc_info=True)
            return {
                "batch_validation": {"total_count": 0, "validity_rate": 0.0},
                "label_distribution": {"is_balanced": False},
                "data_sufficiency": {"is_sufficient": False},
                "duplicate_analysis": {"duplicate_rate": 0.0},
                "overall_quality_score": 0.0,
                "ready_for_training": False,
            }
