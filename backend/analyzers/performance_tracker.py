"""
Performance Tracking Service for ML Models

This module provides comprehensive performance tracking for machine learning models,
including metrics calculation, historical performance recording, and degradation detection.
The system supports:
- Standard classification metrics (accuracy, precision, recall, F1, AUC)
- Performance history tracking over time
- Performance degradation detection
- A/B testing comparison support
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy import typing as npt
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_curve,
)

from models.model_performance_history import ModelPerformanceHistory

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Performance tracking service for ML model metrics.

    This class provides methods to calculate performance metrics for machine learning
    models, track historical performance data, and detect performance degradation.

    Attributes:
        default_metrics: Default set of metrics to calculate

    Example:
        >>> tracker = PerformanceTracker()
        >>> y_true = np.array([1, 0, 1, 1])
        >>> y_pred = np.array([1, 0, 0, 1])
        >>> metrics = tracker.calculate_metrics(y_true, y_pred)
        >>> print(f"Accuracy: {metrics['accuracy']:.3f}")
        Accuracy: 0.750
    """

    # Default metrics to calculate
    DEFAULT_METRICS = ["accuracy", "precision", "recall", "f1_score"]

    # Dataset types
    DATASET_TRAINING = "training"
    DATASET_VALIDATION = "validation"
    DATASET_TEST = "test"
    DATASET_PRODUCTION = "production"

    def __init__(self, default_metrics: Optional[List[str]] = None) -> None:
        """
        Initialize the performance tracker.

        Args:
            default_metrics: List of default metrics to calculate
                            (defaults to DEFAULT_METRICS)
        """
        self.default_metrics = default_metrics or self.DEFAULT_METRICS

    def calculate_metrics(
        self,
        y_true: npt.NDArray[np.int_],
        y_pred: npt.NDArray[np.int_],
        y_scores: Optional[npt.NDArray[np.float64]] = None,
        average: str = "binary",
        zero_division: str = "warn",
    ) -> Dict[str, float]:
        """
        Calculate performance metrics for classification predictions.

        Computes standard classification metrics including accuracy, precision,
        recall, and F1 score. Optionally computes AUC-ROC if probability scores
        are provided.

        Args:
            y_true: Ground truth labels (n_samples,)
            y_pred: Predicted labels (n_samples,)
            y_scores: Optional predicted probabilities for positive class (n_samples,)
            average: Averaging method for multiclass ('binary', 'micro', 'macro', 'weighted')
            zero_division: How to handle zero division ('warn' or 0/1)

        Returns:
            Dictionary with computed metrics (accuracy, precision, recall, f1_score, auc_score)

        Example:
            >>> tracker = PerformanceTracker()
            >>> y_true = np.array([1, 0, 1, 1])
            >>> y_pred = np.array([1, 0, 0, 1])
            >>> metrics = tracker.calculate_metrics(y_true, y_pred)
            >>> print(f"Accuracy: {metrics['accuracy']}")
            0.75
        """
        try:
            metrics: Dict[str, float] = {}

            # Calculate accuracy
            metrics["accuracy"] = float(accuracy_score(y_true, y_pred))

            # Calculate precision, recall, f1
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_true,
                y_pred,
                average=average,
                zero_division=0 if zero_division != "warn" else 0,
            )

            metrics["precision"] = float(precision)
            metrics["recall"] = float(recall)
            metrics["f1_score"] = float(f1)

            # Calculate AUC if scores provided and binary classification
            if y_scores is not None and len(np.unique(y_true)) == 2:
                try:
                    fpr, tpr, _ = roc_curve(y_true, y_scores)
                    metrics["auc_score"] = float(auc(fpr, tpr))
                except Exception as e:
                    logger.warning(f"Could not calculate AUC score: {e}")
                    metrics["auc_score"] = 0.0
            else:
                metrics["auc_score"] = None

            logger.info(
                f"Calculated metrics: accuracy={metrics['accuracy']:.4f}, "
                f"f1={metrics['f1_score']:.4f}, recall={metrics['recall']:.4f}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}", exc_info=True)
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "auc_score": None,
            }

    def calculate_confusion_matrix(
        self, y_true: npt.NDArray[np.int_], y_pred: npt.NDArray[np.int_]
    ) -> Dict[str, Any]:
        """
        Calculate confusion matrix for classification predictions.

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels

        Returns:
            Dictionary with confusion matrix data and metadata

        Example:
            >>> tracker = PerformanceTracker()
            >>> y_true = np.array([1, 0, 1, 1])
            >>> y_pred = np.array([1, 0, 0, 1])
            >>> cm = tracker.calculate_confusion_matrix(y_true, y_pred)
            >>> print(cm['matrix'])
            [[1, 0], [1, 2]]
        """
        try:
            cm = confusion_matrix(y_true, y_pred)

            # Format confusion matrix for JSON storage
            cm_dict = {
                "matrix": cm.tolist(),
                "shape": cm.shape,
                "labels": sorted(np.unique(np.concatenate([y_true, y_pred]))).tolist(),
            }

            # Add derived metrics
            if cm.shape == (2, 2):
                # Binary classification
                tn, fp, fn, tp = cm.ravel()
                cm_dict.update(
                    {
                        "true_negatives": int(tn),
                        "false_positives": int(fp),
                        "false_negatives": int(fn),
                        "true_positives": int(tp),
                    }
                )

            logger.debug(f"Calculated confusion matrix: {cm.shape}")
            return cm_dict

        except Exception as e:
            logger.error(f"Error calculating confusion matrix: {e}", exc_info=True)
            return {
                "matrix": [],
                "shape": (0, 0),
                "labels": [],
            }

    def record_performance(
        self,
        db_session: Any,
        model_version_id: str,
        y_true: npt.NDArray[np.int_],
        y_pred: npt.NDArray[np.int_],
        dataset_type: str,
        y_scores: Optional[npt.NDArray[np.float64]] = None,
        custom_metrics: Optional[Dict[str, Any]] = None,
        evaluation_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ModelPerformanceHistory]:
        """
        Record performance metrics to database.

        Calculates metrics and creates a new ModelPerformanceHistory record
        in the database for tracking model performance over time.

        Args:
            db_session: Database session
            model_version_id: ID of the MLModelVersion
            y_true: Ground truth labels
            y_pred: Predicted labels
            dataset_type: Type of dataset (training, validation, test, production)
            y_scores: Optional predicted probabilities
            custom_metrics: Optional custom metrics to store
            evaluation_metadata: Optional evaluation metadata

        Returns:
            Created ModelPerformanceHistory instance or None if failed

        Example:
            >>> tracker = PerformanceTracker()
            >>> history = tracker.record_performance(
            ...     db, model_id, y_true, y_pred, "test"
            ... )
            >>> print(f"Recorded F1: {history.f1_score}")
        """
        if db_session is None:
            logger.warning("No database session provided, skipping performance recording")
            return None

        try:
            # Calculate metrics
            metrics = self.calculate_metrics(y_true, y_pred, y_scores)
            cm_data = self.calculate_confusion_matrix(y_true, y_pred)

            # Get previous performance for delta calculation
            previous_performance = (
                db_session.query(ModelPerformanceHistory)
                .filter(
                    ModelPerformanceHistory.model_version_id == model_version_id,
                    ModelPerformanceHistory.dataset_type == dataset_type,
                )
                .order_by(ModelPerformanceHistory.created_at.desc())
                .first()
            )

            # Calculate performance delta
            performance_delta = None
            if previous_performance and previous_performance.f1_score is not None:
                performance_delta = (
                    metrics["f1_score"] - previous_performance.f1_score
                )

            # Create performance history record
            performance_record = ModelPerformanceHistory(
                model_version_id=model_version_id,
                dataset_type=dataset_type,
                accuracy=metrics.get("accuracy"),
                precision=metrics.get("precision"),
                recall=metrics.get("recall"),
                f1_score=metrics.get("f1_score"),
                auc_score=metrics.get("auc_score"),
                sample_size=len(y_true),
                confusion_matrix=cm_data,
                custom_metrics=custom_metrics or {},
                performance_delta=performance_delta,
                evaluation_metadata=evaluation_metadata or {},
            )

            db_session.add(performance_record)
            db_session.flush()

            logger.info(
                f"Recorded performance for model {model_version_id} "
                f"(dataset: {dataset_type}, f1: {metrics['f1_score']:.4f})"
            )

            return performance_record

        except Exception as e:
            logger.error(
                f"Error recording performance for model {model_version_id}: {e}",
                exc_info=True,
            )
            return None

    def get_performance_history(
        self,
        db_session: Any,
        model_version_id: str,
        dataset_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve performance history for a model version.

        Args:
            db_session: Database session
            model_version_id: ID of the MLModelVersion
            dataset_type: Optional filter by dataset type
            limit: Maximum number of records to retrieve

        Returns:
            List of performance history dictionaries

        Example:
            >>> tracker = PerformanceTracker()
            >>> history = tracker.get_performance_history(db, model_id, "test")
            >>> for record in history:
            ...     print(f"{record['created_at']}: {record['f1_score']}")
        """
        if db_session is None:
            logger.debug("No database session provided, returning empty history")
            return []

        try:
            query = db_session.query(ModelPerformanceHistory).filter(
                ModelPerformanceHistory.model_version_id == model_version_id
            )

            if dataset_type:
                query = query.filter(ModelPerformanceHistory.dataset_type == dataset_type)

            records = (
                query.order_by(ModelPerformanceHistory.created_at.desc())
                .limit(limit)
                .all()
            )

            history = []
            for record in records:
                history.append(
                    {
                        "id": str(record.id),
                        "dataset_type": record.dataset_type,
                        "accuracy": float(record.accuracy) if record.accuracy else None,
                        "precision": float(record.precision) if record.precision else None,
                        "recall": float(record.recall) if record.recall else None,
                        "f1_score": float(record.f1_score) if record.f1_score else None,
                        "auc_score": float(record.auc_score) if record.auc_score else None,
                        "sample_size": record.sample_size,
                        "performance_delta": (
                            float(record.performance_delta)
                            if record.performance_delta
                            else None
                        ),
                        "confusion_matrix": record.confusion_matrix,
                        "custom_metrics": record.custom_metrics or {},
                        "created_at": (
                            record.created_at.isoformat() if record.created_at else None
                        ),
                    }
                )

            logger.info(f"Retrieved {len(history)} performance records for {model_version_id}")
            return history

        except Exception as e:
            logger.error(
                f"Error getting performance history for {model_version_id}: {e}",
                exc_info=True,
            )
            return []

    def detect_performance_degradation(
        self,
        db_session: Any,
        model_version_id: str,
        dataset_type: str = "production",
        threshold: float = 0.05,
        min_samples: int = 100,
        window_size: int = 5,
    ) -> Dict[str, Any]:
        """
        Detect if model performance has degraded.

        Compares recent performance against historical baseline to detect
        significant degradation that may indicate the need for retraining.

        Args:
            db_session: Database session
            model_version_id: ID of the MLModelVersion
            dataset_type: Dataset type to check
            threshold: Performance drop threshold (e.g., 0.05 = 5% drop)
            min_samples: Minimum sample size for reliable measurement
            window_size: Number of recent records to average

        Returns:
            Dictionary with degradation detection results

        Example:
            >>> tracker = PerformanceTracker()
            >>> result = tracker.detect_performance_degradation(db, model_id)
            >>> if result['is_degraded']:
            ...     print(f"Performance dropped by {result['drop_amount']:.2%}")
        """
        try:
            # Get performance history
            history = self.get_performance_history(
                db_session, model_version_id, dataset_type, limit=window_size + 10
            )

            if len(history) < 2:
                return {
                    "is_degraded": False,
                    "reason": "Insufficient historical data",
                    "current_f1": None,
                    "baseline_f1": None,
                    "drop_amount": 0.0,
                }

            # Calculate baseline from older records (excluding most recent)
            baseline_records = history[1 : window_size + 1]
            if not baseline_records:
                baseline_f1 = history[0]["f1_score"]
            else:
                baseline_scores = [
                    r["f1_score"] for r in baseline_records if r["f1_score"] is not None
                ]
                baseline_f1 = sum(baseline_scores) / len(baseline_scores) if baseline_scores else None

            # Get current performance
            current_f1 = history[0]["f1_score"]
            current_sample_size = history[0].get("sample_size", 0)

            # Check if we have reliable measurements
            if current_f1 is None or baseline_f1 is None:
                return {
                    "is_degraded": False,
                    "reason": "Missing F1 score data",
                    "current_f1": current_f1,
                    "baseline_f1": baseline_f1,
                    "drop_amount": 0.0,
                }

            # Check sample size
            if current_sample_size < min_samples:
                return {
                    "is_degraded": False,
                    "reason": f"Insufficient sample size ({current_sample_size} < {min_samples})",
                    "current_f1": current_f1,
                    "baseline_f1": baseline_f1,
                    "drop_amount": 0.0,
                }

            # Calculate performance drop
            drop_amount = baseline_f1 - current_f1
            drop_percentage = (drop_amount / baseline_f1) if baseline_f1 > 0 else 0.0

            # Determine if degraded
            is_degraded = drop_amount > threshold

            result = {
                "is_degraded": is_degraded,
                "current_f1": current_f1,
                "baseline_f1": baseline_f1,
                "drop_amount": drop_amount,
                "drop_percentage": drop_percentage,
                "threshold": threshold,
                "sample_size": current_sample_size,
            }

            if is_degraded:
                logger.warning(
                    f"Performance degradation detected for {model_version_id}: "
                    f"{drop_percentage:.2%} drop (threshold: {threshold:.2%})"
                )
            else:
                logger.debug(
                    f"No performance degradation for {model_version_id}: "
                    f"current={current_f1:.4f}, baseline={baseline_f1:.4f}"
                )

            return result

        except Exception as e:
            logger.error(
                f"Error detecting performance degradation for {model_version_id}: {e}",
                exc_info=True,
            )
            return {
                "is_degraded": False,
                "reason": f"Error during detection: {str(e)}",
                "current_f1": None,
                "baseline_f1": None,
                "drop_amount": 0.0,
            }

    def calculate_aggregate_metrics(
        self, db_session: Any, model_version_id: str
    ) -> Dict[str, Any]:
        """
        Calculate aggregate performance metrics across all dataset types.

        Args:
            db_session: Database session
            model_version_id: ID of the MLModelVersion

        Returns:
            Dictionary with aggregate metrics by dataset type

        Example:
            >>> tracker = PerformanceTracker()
            >>> agg = tracker.calculate_aggregate_metrics(db, model_id)
            >>> print(agg['by_dataset_type']['test']['avg_accuracy'])
        """
        try:
            history = self.get_performance_history(
                db_session, model_version_id, limit=1000
            )

            if not history:
                return {
                    "model_version_id": model_version_id,
                    "total_records": 0,
                    "by_dataset_type": {},
                }

            # Group by dataset type
            by_dataset: Dict[str, List[Dict]] = {}
            for record in history:
                dataset = record["dataset_type"]
                if dataset not in by_dataset:
                    by_dataset[dataset] = []
                by_dataset[dataset].append(record)

            # Calculate aggregates for each dataset type
            aggregates = {}
            for dataset, records in by_dataset.items():
                # Filter out None values
                accuracies = [r["accuracy"] for r in records if r["accuracy"] is not None]
                f1_scores = [r["f1_score"] for r in records if r["f1_score"] is not None]
                recalls = [r["recall"] for r in records if r["recall"] is not None]
                precisions = [
                    r["precision"] for r in records if r["precision"] is not None
                ]

                aggregates[dataset] = {
                    "record_count": len(records),
                    "avg_accuracy": sum(accuracies) / len(accuracies) if accuracies else None,
                    "avg_f1_score": sum(f1_scores) / len(f1_scores) if f1_scores else None,
                    "avg_recall": sum(recalls) / len(recalls) if recalls else None,
                    "avg_precision": (
                        sum(precisions) / len(precisions) if precisions else None
                    ),
                    "latest_f1_score": f1_scores[0] if f1_scores else None,
                    "total_samples": sum(r.get("sample_size", 0) for r in records),
                }

            return {
                "model_version_id": model_version_id,
                "total_records": len(history),
                "by_dataset_type": aggregates,
            }

        except Exception as e:
            logger.error(
                f"Error calculating aggregate metrics for {model_version_id}: {e}",
                exc_info=True,
            )
            return {
                "model_version_id": model_version_id,
                "total_records": 0,
                "by_dataset_type": {},
            }
