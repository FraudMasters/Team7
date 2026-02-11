"""
Feedback Accumulation Service for ML Models

This module provides comprehensive feedback tracking and accumulation for machine learning
models, including feedback counting per model version, threshold checking for retraining
triggers, and feedback statistics tracking.

The system supports:
- Feedback count tracking per model version
- Configurable feedback thresholds for retraining triggers
- Feedback accumulation statistics over time
- Multi-model feedback tracking
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


@dataclass
class FeedbackStats:
    """
    Statistics for feedback accumulation.

    Attributes:
        total_count: Total number of feedback items
        positive_count: Number of positive feedback items
        negative_count: Number of negative feedback items
        neutral_count: Number of neutral feedback items
        last_feedback_at: Timestamp of the most recent feedback
        first_feedback_at: Timestamp of the first feedback
    """

    total_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    last_feedback_at: Optional[datetime] = None
    first_feedback_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary representation."""
        return {
            "total_count": self.total_count,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "last_feedback_at": (
                self.last_feedback_at.isoformat() if self.last_feedback_at else None
            ),
            "first_feedback_at": (
                self.first_feedback_at.isoformat() if self.first_feedback_at else None
            ),
        }


@dataclass
class ModelFeedbackAccumulator:
    """
    Accumulator for tracking feedback for a single model version.

    Attributes:
        model_name: Name of the ML model
        model_version_id: Version ID of the model
        feedback_since_training: Feedback count since last training
        feedback_stats: Detailed feedback statistics
        threshold_reached_at: Timestamp when threshold was reached (if applicable)
    """

    model_name: str
    model_version_id: str
    feedback_since_training: int = 0
    feedback_stats: FeedbackStats = field(default_factory=FeedbackStats)
    threshold_reached_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert accumulator to dictionary representation."""
        return {
            "model_name": self.model_name,
            "model_version_id": self.model_version_id,
            "feedback_since_training": self.feedback_since_training,
            "feedback_stats": self.feedback_stats.to_dict(),
            "threshold_reached_at": (
                self.threshold_reached_at.isoformat() if self.threshold_reached_at else None
            ),
        }


class FeedbackAccumulator:
    """
    Feedback accumulation service for tracking feedback counts per ML model.

    This class provides methods to track, accumulate, and analyze feedback
    for machine learning models, supporting automatic retraining triggers
    based on feedback volume thresholds.

    Attributes:
        feedback_threshold: Number of feedbacks required to trigger retraining
        model_accumulators: Dictionary tracking feedback per model version

    Example:
        >>> accumulator = FeedbackAccumulator(feedback_threshold=1000)
        >>> accumulator.record_feedback("ranking_model", "v1.0.0", "positive")
        >>> accumulator.record_feedback("ranking_model", "v1.0.0", "negative")
        >>> if accumulator.should_trigger_retraining("ranking_model", "v1.0.0"):
        ...     print("Threshold reached!")
    """

    # Default feedback threshold for triggering retraining
    DEFAULT_FEEDBACK_THRESHOLD = 1000

    # Feedback type constants
    FEEDBACK_POSITIVE = "positive"
    FEEDBACK_NEGATIVE = "negative"
    FEEDBACK_NEUTRAL = "neutral"

    # Valid feedback types
    VALID_FEEDBACK_TYPES = {FEEDBACK_POSITIVE, FEEDBACK_NEGATIVE, FEEDBACK_NEUTRAL}

    def __init__(self, feedback_threshold: int = DEFAULT_FEEDBACK_THRESHOLD) -> None:
        """
        Initialize the feedback accumulator.

        Args:
            feedback_threshold: Number of feedbacks required to trigger retraining
                              (defaults to DEFAULT_FEEDBACK_THRESHOLD = 1000)
        """
        self.feedback_threshold = feedback_threshold
        self.model_accumulators: Dict[str, ModelFeedbackAccumulator] = {}
        logger.info(
            f"FeedbackAccumulator initialized with threshold={feedback_threshold}"
        )

    def _get_accumulator_key(self, model_name: str, model_version_id: str) -> str:
        """
        Generate unique key for model accumulator lookup.

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model

        Returns:
            Unique string key for the model version
        """
        return f"{model_name}:{model_version_id}"

    def _get_or_create_accumulator(
        self, model_name: str, model_version_id: str
    ) -> ModelFeedbackAccumulator:
        """
        Get existing accumulator or create new one for model version.

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model

        Returns:
            ModelFeedbackAccumulator instance for the model version
        """
        key = self._get_accumulator_key(model_name, model_version_id)
        if key not in self.model_accumulators:
            self.model_accumulators[key] = ModelFeedbackAccumulator(
                model_name=model_name,
                model_version_id=model_version_id,
            )
            logger.debug(f"Created new accumulator for {key}")
        return self.model_accumulators[key]

    def record_feedback(
        self,
        model_name: str,
        model_version_id: str,
        feedback_type: str = FEEDBACK_NEUTRAL,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Record a feedback item for a specific model version.

        Increments feedback counters and checks if threshold has been reached.

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model
            feedback_type: Type of feedback (positive, negative, neutral)
            timestamp: Optional timestamp for the feedback (defaults to now)

        Returns:
            Dictionary with updated feedback status including:
            - total_count: Updated total feedback count
            - threshold_reached: Whether threshold has been reached
            - threshold: The configured feedback threshold

        Example:
            >>> accumulator = FeedbackAccumulator(feedback_threshold=100)
            >>> result = accumulator.record_feedback("ranking", "v1.0", "positive")
            >>> print(result['total_count'])
            1
        """
        start_time = time.time()

        # Validate feedback type
        if feedback_type not in self.VALID_FEEDBACK_TYPES:
            logger.warning(
                f"Invalid feedback type '{feedback_type}', defaulting to neutral"
            )
            feedback_type = self.FEEDBACK_NEUTRAL

        try:
            # Get or create accumulator
            accumulator = self._get_or_create_accumulator(model_name, model_version_id)

            # Use current time if not provided
            if timestamp is None:
                timestamp = datetime.utcnow()

            # Update feedback counts
            accumulator.feedback_since_training += 1
            accumulator.feedback_stats.total_count += 1

            # Update type-specific counts
            if feedback_type == self.FEEDBACK_POSITIVE:
                accumulator.feedback_stats.positive_count += 1
            elif feedback_type == self.FEEDBACK_NEGATIVE:
                accumulator.feedback_stats.negative_count += 1
            else:
                accumulator.feedback_stats.neutral_count += 1

            # Update timestamps
            if accumulator.feedback_stats.first_feedback_at is None:
                accumulator.feedback_stats.first_feedback_at = timestamp
            accumulator.feedback_stats.last_feedback_at = timestamp

            # Check if threshold reached
            threshold_reached = (
                accumulator.feedback_since_training >= self.feedback_threshold
            )
            if threshold_reached and accumulator.threshold_reached_at is None:
                accumulator.threshold_reached_at = timestamp
                logger.info(
                    f"Feedback threshold reached for {model_name}:{model_version_id} "
                    f"({accumulator.feedback_since_training} feedbacks)"
                )

            # Record metrics
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="feedback_accumulator",
                    operation="record_feedback",
                    duration=duration,
                    prediction_type="feedback_tracking",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            result = {
                "model_name": model_name,
                "model_version_id": model_version_id,
                "total_count": accumulator.feedback_stats.total_count,
                "feedback_since_training": accumulator.feedback_since_training,
                "threshold_reached": threshold_reached,
                "threshold": self.feedback_threshold,
                "feedback_type": feedback_type,
            }

            logger.debug(
                f"Recorded {feedback_type} feedback for {model_name}:{model_version_id} "
                f"(total: {accumulator.feedback_stats.total_count}, "
                f"since training: {accumulator.feedback_since_training})"
            )

            return result

        except Exception as e:
            logger.error(f"Error recording feedback: {e}", exc_info=True)
            return {
                "model_name": model_name,
                "model_version_id": model_version_id,
                "total_count": 0,
                "feedback_since_training": 0,
                "threshold_reached": False,
                "threshold": self.feedback_threshold,
                "error": str(e),
            }

    def record_feedback_batch(
        self,
        model_name: str,
        model_version_id: str,
        feedback_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Record multiple feedback items in a batch.

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model
            feedback_items: List of feedback dictionaries with 'type' and optional 'timestamp'

        Returns:
            Dictionary with batch processing results

        Example:
            >>> accumulator = FeedbackAccumulator()
            >>> items = [{"type": "positive"}, {"type": "negative"}]
            >>> result = accumulator.record_feedback_batch("ranking", "v1.0", items)
            >>> print(result['processed_count'])
            2
        """
        start_time = time.time()

        try:
            processed_count = 0
            type_counts = {"positive": 0, "negative": 0, "neutral": 0}
            last_timestamp = None

            for item in feedback_items:
                feedback_type = item.get("type", self.FEEDBACK_NEUTRAL)
                timestamp = item.get("timestamp")

                # Convert string timestamp to datetime if needed
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except ValueError:
                        timestamp = None

                self.record_feedback(model_name, model_version_id, feedback_type, timestamp)
                processed_count += 1
                type_counts[feedback_type] = type_counts.get(feedback_type, 0) + 1
                last_timestamp = timestamp

            # Record batch metrics
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="feedback_accumulator",
                    operation="record_feedback_batch",
                    duration=duration,
                    prediction_type="batch_processing",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            accumulator = self._get_or_create_accumulator(model_name, model_version_id)

            logger.info(
                f"Processed batch of {processed_count} feedback items for "
                f"{model_name}:{model_version_id}"
            )

            return {
                "model_name": model_name,
                "model_version_id": model_version_id,
                "processed_count": processed_count,
                "type_counts": type_counts,
                "total_feedback_since_training": accumulator.feedback_since_training,
                "threshold_reached": accumulator.feedback_since_training >= self.feedback_threshold,
            }

        except Exception as e:
            logger.error(f"Error processing feedback batch: {e}", exc_info=True)
            return {
                "model_name": model_name,
                "model_version_id": model_version_id,
                "processed_count": 0,
                "error": str(e),
            }

    def should_trigger_retraining(
        self, model_name: str, model_version_id: str
    ) -> bool:
        """
        Check if retraining should be triggered based on feedback accumulation.

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model

        Returns:
            True if feedback threshold has been reached, False otherwise

        Example:
            >>> accumulator = FeedbackAccumulator(feedback_threshold=2)
            >>> accumulator.record_feedback("model", "v1", "positive")
            >>> accumulator.record_feedback("model", "v1", "positive")
            >>> accumulator.should_trigger_retraining("model", "v1")
            True
        """
        key = self._get_accumulator_key(model_name, model_version_id)
        accumulator = self.model_accumulators.get(key)

        if accumulator is None:
            logger.debug(
                f"No feedback recorded for {model_name}:{model_version_id}, "
                "retraining not triggered"
            )
            return False

        should_trigger = accumulator.feedback_since_training >= self.feedback_threshold

        if should_trigger:
            logger.info(
                f"Retraining trigger check: {model_name}:{model_version_id} "
                f"({accumulator.feedback_since_training}/{self.feedback_threshold}) - TRIGGER"
            )
        else:
            logger.debug(
                f"Retraining trigger check: {model_name}:{model_version_id} "
                f"({accumulator.feedback_since_training}/{self.feedback_threshold}) - NO TRIGGER"
            )

        return should_trigger

    def get_feedback_count(self, model_name: str, model_version_id: str) -> int:
        """
        Get the total feedback count for a model version.

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model

        Returns:
            Number of feedback items recorded since last training reset
        """
        key = self._get_accumulator_key(model_name, model_version_id)
        accumulator = self.model_accumulators.get(key)
        return accumulator.feedback_since_training if accumulator else 0

    def get_feedback_stats(
        self, model_name: str, model_version_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed feedback statistics for a model version.

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model

        Returns:
            Dictionary with feedback statistics

        Example:
            >>> accumulator = FeedbackAccumulator()
            >>> accumulator.record_feedback("model", "v1", "positive")
            >>> stats = accumulator.get_feedback_stats("model", "v1")
            >>> print(stats['total_count'])
            1
        """
        key = self._get_accumulator_key(model_name, model_version_id)
        accumulator = self.model_accumulators.get(key)

        if accumulator is None:
            return {
                "model_name": model_name,
                "model_version_id": model_version_id,
                "total_count": 0,
                "feedback_since_training": 0,
                "threshold": self.feedback_threshold,
                "threshold_reached": False,
                "stats": FeedbackStats().to_dict(),
            }

        return {
            "model_name": model_name,
            "model_version_id": model_version_id,
            "total_count": accumulator.feedback_stats.total_count,
            "feedback_since_training": accumulator.feedback_since_training,
            "threshold": self.feedback_threshold,
            "threshold_reached": accumulator.feedback_since_training >= self.feedback_threshold,
            "stats": accumulator.feedback_stats.to_dict(),
            "threshold_reached_at": (
                accumulator.threshold_reached_at.isoformat()
                if accumulator.threshold_reached_at
                else None
            ),
        }

    def reset_feedback_count(
        self, model_name: str, model_version_id: str
    ) -> Dict[str, Any]:
        """
        Reset the feedback count for a model version (typically after retraining).

        Args:
            model_name: Name of the ML model
            model_version_id: Version ID of the model

        Returns:
            Dictionary with reset status and previous count

        Example:
            >>> accumulator = FeedbackAccumulator(feedback_threshold=100)
            >>> accumulator.record_feedback("model", "v1", "positive")
            >>> result = accumulator.reset_feedback_count("model", "v1")
            >>> print(result['previous_count'])
            1
        """
        key = self._get_accumulator_key(model_name, model_version_id)
        accumulator = self.model_accumulators.get(key)

        previous_count = 0
        if accumulator:
            previous_count = accumulator.feedback_since_training
            accumulator.feedback_since_training = 0
            accumulator.threshold_reached_at = None
            logger.info(
                f"Reset feedback count for {model_name}:{model_version_id} "
                f"(was {previous_count})"
            )
        else:
            logger.debug(
                f"No accumulator found for {model_name}:{model_version_id}, "
                "nothing to reset"
            )

        return {
            "model_name": model_name,
            "model_version_id": model_version_id,
            "previous_count": previous_count,
            "new_count": 0,
            "reset_at": datetime.utcnow().isoformat(),
        }

    def get_all_model_stats(self) -> List[Dict[str, Any]]:
        """
        Get feedback statistics for all tracked models.

        Returns:
            List of dictionaries with feedback stats for each model version

        Example:
            >>> accumulator = FeedbackAccumulator()
            >>> accumulator.record_feedback("model1", "v1", "positive")
            >>> accumulator.record_feedback("model2", "v1", "negative")
            >>> all_stats = accumulator.get_all_model_stats()
            >>> len(all_stats)
            2
        """
        stats_list = []

        for key, accumulator in self.model_accumulators.items():
            stats_list.append(
                {
                    "model_name": accumulator.model_name,
                    "model_version_id": accumulator.model_version_id,
                    "feedback_since_training": accumulator.feedback_since_training,
                    "threshold": self.feedback_threshold,
                    "threshold_reached": (
                        accumulator.feedback_since_training >= self.feedback_threshold
                    ),
                    "stats": accumulator.feedback_stats.to_dict(),
                    "threshold_reached_at": (
                        accumulator.threshold_reached_at.isoformat()
                        if accumulator.threshold_reached_at
                        else None
                    ),
                }
            )

        logger.debug(f"Retrieved stats for {len(stats_list)} model versions")
        return stats_list

    def get_models_needing_retraining(self) -> List[Dict[str, Any]]:
        """
        Get list of model versions that have reached feedback threshold.

        Returns:
            List of dictionaries for model versions needing retraining

        Example:
            >>> accumulator = FeedbackAccumulator(feedback_threshold=1)
            >>> accumulator.record_feedback("model", "v1", "positive")
            >>> needs_retraining = accumulator.get_models_needing_retraining()
            >>> len(needs_retraining)
            1
        """
        needs_retraining = []

        for key, accumulator in self.model_accumulators.items():
            if accumulator.feedback_since_training >= self.feedback_threshold:
                needs_retraining.append(
                    {
                        "model_name": accumulator.model_name,
                        "model_version_id": accumulator.model_version_id,
                        "feedback_since_training": accumulator.feedback_since_training,
                        "threshold": self.feedback_threshold,
                        "excess_feedback": (
                            accumulator.feedback_since_training - self.feedback_threshold
                        ),
                        "threshold_reached_at": (
                            accumulator.threshold_reached_at.isoformat()
                            if accumulator.threshold_reached_at
                            else None
                        ),
                    }
                )

        if needs_retraining:
            logger.info(
                f"Found {len(needs_retraining)} model versions needing retraining"
            )

        return needs_retraining

    def set_feedback_threshold(self, threshold: int) -> None:
        """
        Update the feedback threshold for retraining triggers.

        Args:
            threshold: New feedback threshold value

        Example:
            >>> accumulator = FeedbackAccumulator()
            >>> accumulator.set_feedback_threshold(500)
            >>> accumulator.feedback_threshold
            500
        """
        if threshold < 1:
            raise ValueError("Feedback threshold must be at least 1")

        old_threshold = self.feedback_threshold
        self.feedback_threshold = threshold
        logger.info(f"Updated feedback threshold from {old_threshold} to {threshold}")
