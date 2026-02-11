"""
Model Performance Monitor Service for Comprehensive Metrics Tracking

This module provides comprehensive performance monitoring for machine learning models,
including real-time metrics tracking, trend analysis, alerting thresholds, and
performance snapshots. The system supports:
- Standard classification metrics (accuracy, precision, recall, F1, AUC)
- Ranking quality metrics (NDCG, MRR)
- Performance trend analysis and anomaly detection
- Alerting for performance degradation
- Historical performance snapshots
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy import typing as npt

from models.ml_model_version import MLModelVersion
from models.model_performance_history import ModelPerformanceHistory
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


class ModelPerformanceMonitor:
    """
    Comprehensive performance monitoring service for ML models.

    This class provides methods to monitor, track, and analyze model performance
    metrics over time, detect anomalies, and trigger alerts for degradation.

    Attributes:
        degradation_threshold: Threshold for performance degradation alerts
        warning_threshold: Threshold for performance warnings
        min_samples_for_alert: Minimum samples required before alerting

    Example:
        >>> monitor = ModelPerformanceMonitor()
        >>> monitor.record_observation('model-123', 'skill_matching',
        ...     actual=True, predicted=True, score=0.95)
        >>> snapshot = monitor.get_performance_snapshot('model-123')
        >>> print(f"Current accuracy: {snapshot['accuracy']:.2%}")
    """

    # Default thresholds
    DEFAULT_DEGRADATION_THRESHOLD = 0.10  # 10% drop triggers degradation alert
    DEFAULT_WARNING_THRESHOLD = 0.05  # 5% drop triggers warning
    DEFAULT_MIN_SAMPLES = 100  # Minimum samples before alerting

    # Metric types
    METRIC_ACCURACY = "accuracy"
    METRIC_PRECISION = "precision"
    METRIC_RECALL = "recall"
    METRIC_F1 = "f1_score"
    METRIC_AUC = "auc_score"
    METRIC_NDCG = "ndcg_score"
    METRIC_MRR = "mrr_score"

    # Alert severity levels
    ALERT_LEVEL_INFO = "info"
    ALERT_LEVEL_WARNING = "warning"
    ALERT_LEVEL_CRITICAL = "critical"

    def __init__(
        self,
        degradation_threshold: float = DEFAULT_DEGRADATION_THRESHOLD,
        warning_threshold: float = DEFAULT_WARNING_THRESHOLD,
        min_samples_for_alert: int = DEFAULT_MIN_SAMPLES,
    ) -> None:
        """
        Initialize the model performance monitor.

        Args:
            degradation_threshold: Performance drop threshold for critical alerts (0-1)
            warning_threshold: Performance drop threshold for warning alerts (0-1)
            min_samples_for_alert: Minimum observations before generating alerts
        """
        self.degradation_threshold = degradation_threshold
        self.warning_threshold = warning_threshold
        self.min_samples_for_alert = min_samples_for_alert

        # In-memory buffers for real-time tracking
        self._observation_buffers: Dict[str, Dict[str, List]] = {}
        self._baselines: Dict[str, Dict[str, float]] = {}

    def record_observation(
        self,
        model_version_id: str,
        model_name: str,
        actual: Any,
        predicted: Any,
        score: Optional[float] = None,
        ranking_position: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record a single observation for real-time performance tracking.

        Args:
            model_version_id: UUID of the model version
            model_name: Name of the model
            actual: Ground truth value
            predicted: Predicted value
            score: Optional prediction confidence score
            ranking_position: Position in ranking (for ranking models)
            metadata: Optional additional metadata

        Returns:
            Dictionary with updated metrics for the model

        Example:
            >>> monitor = ModelPerformanceMonitor()
            >>> result = monitor.record_observation(
            ...     'model-123', 'skill_matching',
            ...     actual=True, predicted=True, score=0.95
            ... )
        """
        start_time = time.time()

        try:
            # Initialize buffer if needed
            buffer_key = f"{model_name}:{model_version_id}"
            if buffer_key not in self._observation_buffers:
                self._observation_buffers[buffer_key] = {
                    "actuals": [],
                    "predictions": [],
                    "scores": [],
                    "ranking_positions": [],
                    "timestamps": [],
                    "metadata": [],
                }

            buffer = self._observation_buffers[buffer_key]

            # Add observation
            buffer["actuals"].append(actual)
            buffer["predictions"].append(predicted)
            buffer["scores"].append(score)
            buffer["ranking_positions"].append(ranking_position)
            buffer["timestamps"].append(datetime.utcnow())
            buffer["metadata"].append(metadata or {})

            # Calculate current metrics
            metrics = self._calculate_buffer_metrics(buffer)

            # Record metrics timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name=model_name,
                    operation="record_observation",
                    duration=duration,
                    prediction_type="monitoring",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            return {
                "model_version_id": model_version_id,
                "model_name": model_name,
                "observation_count": len(buffer["actuals"]),
                "current_metrics": metrics,
            }

        except Exception as e:
            logger.error(
                f"Error recording observation for {model_name}:{model_version_id}: {e}",
                exc_info=True,
            )
            return {
                "model_version_id": model_version_id,
                "model_name": model_name,
                "observation_count": 0,
                "current_metrics": {},
                "error": str(e),
            }

    def _calculate_buffer_metrics(
        self, buffer: Dict[str, List]
    ) -> Dict[str, float]:
        """
        Calculate metrics from observation buffer.

        Args:
            buffer: Observation buffer containing actuals, predictions, etc.

        Returns:
            Dictionary with calculated metrics
        """
        if not buffer["actuals"]:
            return {}

        try:
            actuals = np.array(buffer["actuals"])
            predictions = np.array(buffer["predictions"])

            # Basic classification metrics
            correct = np.sum(actuals == predictions)
            total = len(actuals)
            accuracy = correct / total if total > 0 else 0.0

            # True positives, false positives, etc. (for binary)
            if set(np.unique(np.concatenate([actuals, predictions]))) <= {True, False, 1, 0, "True", "False"}:
                # Convert to boolean for comparison
                actuals_bool = np.array([bool(a) for a in actuals])
                predictions_bool = np.array([bool(p) for p in predictions])

                tp = np.sum(actuals_bool & predictions_bool)
                tn = np.sum(~actuals_bool & ~predictions_bool)
                fp = np.sum(~actuals_bool & predictions_bool)
                fn = np.sum(actuals_bool & ~predictions_bool)

                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = (
                    2 * precision * recall / (precision + recall)
                    if (precision + recall) > 0
                    else 0.0
                )
            else:
                precision = accuracy  # For multiclass, use accuracy as proxy
                recall = accuracy
                f1 = accuracy

            metrics = {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "sample_size": total,
            }

            # Calculate ranking metrics if positions are available
            positions = [p for p in buffer["ranking_positions"] if p is not None]
            if positions:
                metrics["mrr_score"] = self._calculate_mrr(positions)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating buffer metrics: {e}", exc_info=True)
            return {}

    def _calculate_mrr(self, positions: List[int]) -> float:
        """
        Calculate Mean Reciprocal Rank for ranking metrics.

        Args:
            positions: List of ranking positions (1-indexed)

        Returns:
            MRR score (0-1)
        """
        if not positions:
            return 0.0

        reciprocal_ranks = [1.0 / pos for pos in positions if pos > 0]
        return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

    def get_performance_snapshot(
        self,
        model_version_id: str,
        model_name: str,
        include_trends: bool = True,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get a comprehensive performance snapshot for a model.

        Combines real-time buffer metrics with historical database metrics
        to provide a complete view of model performance.

        Args:
            model_version_id: UUID of the model version
            model_name: Name of the model
            include_trends: Whether to include trend analysis
            db_session: Optional database session for historical data

        Returns:
            Dictionary with comprehensive performance snapshot

        Example:
            >>> monitor = ModelPerformanceMonitor()
            >>> snapshot = monitor.get_performance_snapshot('uuid', 'skill_matching')
            >>> print(f"Accuracy: {snapshot['current_metrics']['accuracy']:.2%}")
        """
        start_time = time.time()

        try:
            snapshot = {
                "model_version_id": model_version_id,
                "model_name": model_name,
                "snapshot_time": datetime.utcnow().isoformat(),
                "current_metrics": {},
                "historical_metrics": {},
                "trends": {},
                "alerts": [],
            }

            # Get current metrics from buffer
            buffer_key = f"{model_name}:{model_version_id}"
            if buffer_key in self._observation_buffers:
                snapshot["current_metrics"] = self._calculate_buffer_metrics(
                    self._observation_buffers[buffer_key]
                )

            # Get historical metrics from database
            if db_session is not None:
                snapshot["historical_metrics"] = self._get_historical_metrics(
                    db_session, model_version_id
                )

                if include_trends:
                    snapshot["trends"] = self._calculate_trends(
                        db_session, model_version_id
                    )

            # Check for alerts
            snapshot["alerts"] = self._check_performance_alerts(
                snapshot["current_metrics"],
                snapshot.get("historical_metrics", {}),
                model_version_id,
            )

            # Record snapshot timing
            duration = time.time() - start_time
            logger.info(
                f"Generated performance snapshot for {model_name}:{model_version_id} "
                f"in {duration:.3f}s"
            )

            return snapshot

        except Exception as e:
            logger.error(
                f"Error getting performance snapshot for {model_name}:{model_version_id}: {e}",
                exc_info=True,
            )
            return {
                "model_version_id": model_version_id,
                "model_name": model_name,
                "snapshot_time": datetime.utcnow().isoformat(),
                "error": str(e),
            }

    def _get_historical_metrics(
        self, db_session: Any, model_version_id: str
    ) -> Dict[str, Any]:
        """
        Get historical metrics from database.

        Args:
            db_session: Database session
            model_version_id: UUID of the model version

        Returns:
            Dictionary with historical metrics
        """
        try:
            # Get latest performance record
            latest = (
                db_session.query(ModelPerformanceHistory)
                .filter(ModelPerformanceHistory.model_version_id == model_version_id)
                .order_by(ModelPerformanceHistory.created_at.desc())
                .first()
            )

            if not latest:
                return {}

            # Get aggregate statistics
            records = (
                db_session.query(ModelPerformanceHistory)
                .filter(ModelPerformanceHistory.model_version_id == model_version_id)
                .order_by(ModelPerformanceHistory.created_at.desc())
                .limit(100)
                .all()
            )

            f1_scores = [
                float(r.f1_score) for r in records if r.f1_score is not None
            ]
            accuracies = [
                float(r.accuracy) for r in records if r.accuracy is not None
            ]

            return {
                "latest": {
                    "accuracy": float(latest.accuracy) if latest.accuracy else None,
                    "precision": float(latest.precision) if latest.precision else None,
                    "recall": float(latest.recall) if latest.recall else None,
                    "f1_score": float(latest.f1_score) if latest.f1_score else None,
                    "auc_score": float(latest.auc_score) if latest.auc_score else None,
                    "sample_size": latest.sample_size,
                    "recorded_at": latest.created_at.isoformat() if latest.created_at else None,
                },
                "aggregates": {
                    "record_count": len(records),
                    "avg_f1_score": sum(f1_scores) / len(f1_scores) if f1_scores else None,
                    "avg_accuracy": sum(accuracies) / len(accuracies) if accuracies else None,
                    "best_f1_score": max(f1_scores) if f1_scores else None,
                    "worst_f1_score": min(f1_scores) if f1_scores else None,
                },
            }

        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}", exc_info=True)
            return {}

    def _calculate_trends(
        self, db_session: Any, model_version_id: str
    ) -> Dict[str, Any]:
        """
        Calculate performance trends over time.

        Args:
            db_session: Database session
            model_version_id: UUID of the model version

        Returns:
            Dictionary with trend analysis
        """
        try:
            # Get recent performance records
            records = (
                db_session.query(ModelPerformanceHistory)
                .filter(ModelPerformanceHistory.model_version_id == model_version_id)
                .order_by(ModelPerformanceHistory.created_at.desc())
                .limit(30)
                .all()
            )

            if len(records) < 2:
                return {"trend": "insufficient_data", "records": len(records)}

            # Calculate trend direction
            f1_scores = [
                float(r.f1_score) for r in reversed(records) if r.f1_score is not None
            ]

            if len(f1_scores) < 2:
                return {"trend": "insufficient_data", "records": len(records)}

            # Simple trend: compare recent average to older average
            mid = len(f1_scores) // 2
            older_avg = sum(f1_scores[:mid]) / mid if mid > 0 else f1_scores[0]
            recent_avg = sum(f1_scores[mid:]) / (len(f1_scores) - mid)

            change = recent_avg - older_avg
            change_pct = (change / older_avg * 100) if older_avg > 0 else 0

            if change_pct > 1:
                trend_direction = "improving"
            elif change_pct < -1:
                trend_direction = "declining"
            else:
                trend_direction = "stable"

            return {
                "trend": trend_direction,
                "change": change,
                "change_pct": change_pct,
                "recent_avg_f1": recent_avg,
                "older_avg_f1": older_avg,
                "data_points": len(f1_scores),
            }

        except Exception as e:
            logger.error(f"Error calculating trends: {e}", exc_info=True)
            return {"trend": "error", "error": str(e)}

    def _check_performance_alerts(
        self,
        current_metrics: Dict[str, float],
        historical_metrics: Dict[str, Any],
        model_version_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Check for performance alerts based on thresholds.

        Args:
            current_metrics: Current performance metrics
            historical_metrics: Historical metrics for comparison
            model_version_id: Model version ID for alert context

        Returns:
            List of alert dictionaries
        """
        alerts = []

        try:
            if not current_metrics or not historical_metrics:
                return alerts

            # Get baseline F1 score
            baseline = historical_metrics.get("aggregates", {}).get("avg_f1_score")
            current_f1 = current_metrics.get("f1_score")

            if baseline is None or current_f1 is None:
                return alerts

            sample_size = current_metrics.get("sample_size", 0)
            if sample_size < self.min_samples_for_alert:
                return alerts

            # Calculate performance drop
            drop = baseline - current_f1
            drop_pct = drop / baseline if baseline > 0 else 0

            if drop_pct >= self.degradation_threshold:
                alerts.append({
                    "level": self.ALERT_LEVEL_CRITICAL,
                    "type": "performance_degradation",
                    "model_version_id": model_version_id,
                    "message": f"Performance degraded by {drop_pct:.1%} (threshold: {self.degradation_threshold:.1%})",
                    "current_f1": current_f1,
                    "baseline_f1": baseline,
                    "drop": drop,
                    "drop_pct": drop_pct,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            elif drop_pct >= self.warning_threshold:
                alerts.append({
                    "level": self.ALERT_LEVEL_WARNING,
                    "type": "performance_warning",
                    "model_version_id": model_version_id,
                    "message": f"Performance warning: dropped by {drop_pct:.1%}",
                    "current_f1": current_f1,
                    "baseline_f1": baseline,
                    "drop": drop,
                    "drop_pct": drop_pct,
                    "timestamp": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}", exc_info=True)

        return alerts

    def set_baseline(
        self,
        model_version_id: str,
        model_name: str,
        metrics: Dict[str, float],
    ) -> None:
        """
        Set baseline metrics for a model for comparison.

        Args:
            model_version_id: UUID of the model version
            model_name: Name of the model
            metrics: Baseline metrics to set
        """
        key = f"{model_name}:{model_version_id}"
        self._baselines[key] = metrics
        logger.info(
            f"Set baseline for {model_name}:{model_version_id}: "
            f"F1={metrics.get('f1_score', 'N/A')}"
        )

    def get_baseline(
        self, model_version_id: str, model_name: str
    ) -> Optional[Dict[str, float]]:
        """
        Get baseline metrics for a model.

        Args:
            model_version_id: UUID of the model version
            model_name: Name of the model

        Returns:
            Baseline metrics dictionary or None if not set
        """
        key = f"{model_name}:{model_version_id}"
        return self._baselines.get(key)

    def clear_buffer(
        self, model_version_id: str, model_name: str
    ) -> int:
        """
        Clear the observation buffer for a model.

        Args:
            model_version_id: UUID of the model version
            model_name: Name of the model

        Returns:
            Number of observations cleared
        """
        key = f"{model_name}:{model_version_id}"
        if key in self._observation_buffers:
            count = len(self._observation_buffers[key]["actuals"])
            del self._observation_buffers[key]
            logger.info(f"Cleared {count} observations for {key}")
            return count
        return 0

    def flush_to_database(
        self,
        model_version_id: str,
        model_name: str,
        dataset_type: str,
        db_session: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Flush buffered observations to database as a performance record.

        Args:
            model_version_id: UUID of the model version
            model_name: Name of the model
            dataset_type: Type of dataset (training, validation, test, production)
            db_session: Database session

        Returns:
            Dictionary with flush results or None if failed

        Example:
            >>> monitor = ModelPerformanceMonitor()
            >>> # ... record observations ...
            >>> result = monitor.flush_to_database(
            ...     'uuid', 'skill_matching', 'production', db
            ... )
        """
        if db_session is None:
            logger.warning("No database session provided, skipping flush")
            return None

        try:
            buffer_key = f"{model_name}:{model_version_id}"
            if buffer_key not in self._observation_buffers:
                logger.debug(f"No observations to flush for {buffer_key}")
                return None

            buffer = self._observation_buffers[buffer_key]
            metrics = self._calculate_buffer_metrics(buffer)

            if not metrics or metrics.get("sample_size", 0) == 0:
                logger.debug(f"No valid metrics to flush for {buffer_key}")
                return None

            # Get previous performance for delta calculation
            previous = (
                db_session.query(ModelPerformanceHistory)
                .filter(
                    ModelPerformanceHistory.model_version_id == model_version_id,
                    ModelPerformanceHistory.dataset_type == dataset_type,
                )
                .order_by(ModelPerformanceHistory.created_at.desc())
                .first()
            )

            previous_f1 = (
                float(previous.f1_score)
                if previous and previous.f1_score
                else None
            )

            # Calculate performance delta
            current_f1 = metrics.get("f1_score", 0)
            performance_delta = None
            if previous_f1 is not None:
                performance_delta = current_f1 - previous_f1

            # Create performance history record
            performance_record = ModelPerformanceHistory(
                model_version_id=model_version_id,
                dataset_type=dataset_type,
                accuracy=metrics.get("accuracy"),
                precision=metrics.get("precision"),
                recall=metrics.get("recall"),
                f1_score=current_f1,
                auc_score=metrics.get("auc_score"),
                sample_size=metrics.get("sample_size"),
                confusion_matrix=metrics.get("confusion_matrix"),
                custom_metrics={
                    "mrr_score": metrics.get("mrr_score"),
                    "flush_time": datetime.utcnow().isoformat(),
                },
                performance_delta=performance_delta,
                evaluation_metadata={
                    "source": "model_performance_monitor",
                    "buffer_flush": True,
                },
            )

            db_session.add(performance_record)
            db_session.flush()

            # Clear the buffer after successful flush
            observation_count = len(buffer["actuals"])
            del self._observation_buffers[buffer_key]

            logger.info(
                f"Flushed {observation_count} observations to database for "
                f"{model_name}:{model_version_id} (F1: {current_f1:.4f})"
            )

            return {
                "id": str(performance_record.id),
                "model_version_id": model_version_id,
                "dataset_type": dataset_type,
                "observations_flushed": observation_count,
                "metrics": metrics,
                "performance_delta": performance_delta,
            }

        except Exception as e:
            logger.error(
                f"Error flushing to database for {model_name}:{model_version_id}: {e}",
                exc_info=True,
            )
            if db_session:
                db_session.rollback()
            return None

    def compare_models(
        self,
        model_a_id: str,
        model_b_id: str,
        model_name: str,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Compare performance between two model versions.

        Args:
            model_a_id: UUID of first model version
            model_b_id: UUID of second model version
            model_name: Name of the model
            db_session: Optional database session

        Returns:
            Dictionary with comparison results

        Example:
            >>> monitor = ModelPerformanceMonitor()
            >>> comparison = monitor.compare_models(
            ...     'uuid-a', 'uuid-b', 'skill_matching', db
            ... )
            >>> print(f"Winner: {comparison['winner']}")
        """
        try:
            comparison = {
                "model_a_id": model_a_id,
                "model_b_id": model_b_id,
                "model_name": model_name,
                "model_a_metrics": {},
                "model_b_metrics": {},
                "comparison": {},
                "winner": None,
                "confidence": None,
            }

            # Get metrics from buffers
            buffer_a_key = f"{model_name}:{model_a_id}"
            buffer_b_key = f"{model_name}:{model_b_id}"

            if buffer_a_key in self._observation_buffers:
                comparison["model_a_metrics"] = self._calculate_buffer_metrics(
                    self._observation_buffers[buffer_a_key]
                )

            if buffer_b_key in self._observation_buffers:
                comparison["model_b_metrics"] = self._calculate_buffer_metrics(
                    self._observation_buffers[buffer_b_key]
                )

            # Get historical metrics if database available
            if db_session is not None:
                if not comparison["model_a_metrics"]:
                    comparison["model_a_metrics"] = self._get_historical_metrics(
                        db_session, model_a_id
                    ).get("latest", {})
                if not comparison["model_b_metrics"]:
                    comparison["model_b_metrics"] = self._get_historical_metrics(
                        db_session, model_b_id
                    ).get("latest", {})

            # Compare metrics
            metrics_a = comparison["model_a_metrics"]
            metrics_b = comparison["model_b_metrics"]

            if metrics_a and metrics_b:
                f1_a = metrics_a.get("f1_score", 0) or 0
                f1_b = metrics_b.get("f1_score", 0) or 0

                comparison["comparison"] = {
                    "f1_diff": f1_a - f1_b,
                    "accuracy_diff": (metrics_a.get("accuracy", 0) or 0) - (metrics_b.get("accuracy", 0) or 0),
                    "precision_diff": (metrics_a.get("precision", 0) or 0) - (metrics_b.get("precision", 0) or 0),
                    "recall_diff": (metrics_a.get("recall", 0) or 0) - (metrics_b.get("recall", 0) or 0),
                }

                # Determine winner
                if f1_a > f1_b:
                    comparison["winner"] = "model_a"
                    comparison["confidence"] = (f1_a - f1_b) / f1_a if f1_a > 0 else 0
                elif f1_b > f1_a:
                    comparison["winner"] = "model_b"
                    comparison["confidence"] = (f1_b - f1_a) / f1_b if f1_b > 0 else 0
                else:
                    comparison["winner"] = "tie"
                    comparison["confidence"] = 0

            return comparison

        except Exception as e:
            logger.error(
                f"Error comparing models {model_a_id} vs {model_b_id}: {e}",
                exc_info=True,
            )
            return {
                "model_a_id": model_a_id,
                "model_b_id": model_b_id,
                "model_name": model_name,
                "error": str(e),
            }

    def get_model_health_status(
        self,
        model_version_id: str,
        model_name: str,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get overall health status for a model.

        Combines performance metrics, trends, and alerts into a health score.

        Args:
            model_version_id: UUID of the model version
            model_name: Name of the model
            db_session: Optional database session

        Returns:
            Dictionary with health status information

        Example:
            >>> monitor = ModelPerformanceMonitor()
            >>> health = monitor.get_model_health_status('uuid', 'skill_matching')
            >>> print(f"Health score: {health['health_score']}")
        """
        try:
            snapshot = self.get_performance_snapshot(
                model_version_id, model_name, include_trends=True, db_session=db_session
            )

            # Calculate health score (0-100)
            health_score = 100.0
            health_factors = []

            # Factor 1: Current performance vs baseline
            current_f1 = snapshot.get("current_metrics", {}).get("f1_score")
            baseline_f1 = snapshot.get("historical_metrics", {}).get("aggregates", {}).get("avg_f1_score")

            if current_f1 is not None and baseline_f1 is not None:
                performance_ratio = current_f1 / baseline_f1 if baseline_f1 > 0 else 1.0
                if performance_ratio < 1:
                    penalty = (1 - performance_ratio) * 100
                    health_score -= penalty
                    health_factors.append({
                        "factor": "performance_vs_baseline",
                        "impact": -penalty,
                        "details": f"Current F1 {current_f1:.3f} vs baseline {baseline_f1:.3f}",
                    })

            # Factor 2: Trend direction
            trend = snapshot.get("trends", {}).get("trend")
            if trend == "declining":
                health_score -= 10
                health_factors.append({
                    "factor": "performance_trend",
                    "impact": -10,
                    "details": "Performance is declining",
                })
            elif trend == "improving":
                health_score += 5
                health_factors.append({
                    "factor": "performance_trend",
                    "impact": 5,
                    "details": "Performance is improving",
                })

            # Factor 3: Active alerts
            alerts = snapshot.get("alerts", [])
            for alert in alerts:
                if alert.get("level") == self.ALERT_LEVEL_CRITICAL:
                    health_score -= 20
                elif alert.get("level") == self.ALERT_LEVEL_WARNING:
                    health_score -= 10

            if alerts:
                health_factors.append({
                    "factor": "active_alerts",
                    "impact": -len(alerts) * 10,
                    "details": f"{len(alerts)} active alert(s)",
                })

            # Clamp health score
            health_score = max(0, min(100, health_score))

            # Determine status
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 60:
                status = "warning"
            elif health_score >= 40:
                status = "degraded"
            else:
                status = "critical"

            return {
                "model_version_id": model_version_id,
                "model_name": model_name,
                "health_score": round(health_score, 1),
                "status": status,
                "health_factors": health_factors,
                "alerts": alerts,
                "current_metrics": snapshot.get("current_metrics", {}),
                "trend": trend,
                "snapshot_time": snapshot.get("snapshot_time"),
            }

        except Exception as e:
            logger.error(
                f"Error getting health status for {model_name}:{model_version_id}: {e}",
                exc_info=True,
            )
            return {
                "model_version_id": model_version_id,
                "model_name": model_name,
                "health_score": 0,
                "status": "unknown",
                "error": str(e),
            }
