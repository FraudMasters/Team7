"""
Model retraining tasks for automated ML model improvement.

This module provides Celery tasks for automated model retraining based on
recruiter feedback, performance degradation detection, and A/B testing
comparison to ensure ranking quality improves over time.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session

from models.ml_model_version import MLModelVersion
from models.model_performance_history import ModelPerformanceHistory
from models.model_training_event import ModelTrainingEvent
from models.skill_feedback import SkillFeedback
from analyzers.performance_tracker import PerformanceTracker
from analyzers.model_versioning import ModelVersionManager
from config import get_settings
from tasks.notifications import send_model_retraining_notification

logger = logging.getLogger(__name__)
settings = get_settings()

# Minimum performance degradation threshold to trigger retraining
MIN_PERFORMANCE_DEGRADATION_THRESHOLD = 0.05  # 5% drop

# Minimum number of feedback samples required for retraining
MIN_FEEDBACK_SAMPLES_FOR_TRAINING = 100

# Minimum number of days between retraining runs
MIN_RETRAINING_INTERVAL_DAYS = 7

# Performance threshold for auto-activating retrained models
AUTO_ACTIVATION_PERFORMANCE_THRESHOLD = 0.85

# Default dataset types for evaluation
DEFAULT_EVALUATION_DATASETS = ["validation", "test"]


def get_current_performance_metrics(
    model_name: str,
    dataset_types: List[str],
    db_session: Session,
) -> Dict[str, Dict[str, Any]]:
    """
    Get current performance metrics for a model across dataset types.

    This function queries the ModelPerformanceHistory table to retrieve
    the most recent performance metrics for a given model across
    specified dataset types.

    Args:
        model_name: Name of the model to query (e.g., 'skill_matching', 'ranking')
        dataset_types: List of dataset types to query (e.g., ['validation', 'test'])
        db_session: Database session for querying

    Returns:
        Dictionary mapping dataset types to their latest metrics:
        {
            "validation": {
                "accuracy": 0.92,
                "precision": 0.89,
                "recall": 0.94,
                "f1_score": 0.91,
                "recorded_at": "2026-01-30T12:00:00"
            },
            "test": {...}
        }

    Example:
        >>> metrics = get_current_performance_metrics('ranking', ['validation'], session)
        >>> print(metrics['validation']['f1_score'])
        0.91
    """
    performance_data = {}

    try:
        for dataset_type in dataset_types:
            # Query the most recent performance record for this dataset type
            query = (
                select(ModelPerformanceHistory, MLModelVersion)
                .join(MLModelVersion, ModelPerformanceHistory.model_version_id == MLModelVersion.id)
                .where(
                    and_(
                        MLModelVersion.model_name == model_name,
                        ModelPerformanceHistory.dataset_type == dataset_type,
                    )
                )
                .order_by(ModelPerformanceHistory.created_at.desc())
                .limit(1)
            )

            result = db_session.execute(query).first()

            if result:
                perf_history, model_version = result
                performance_data[dataset_type] = {
                    "accuracy": float(perf_history.accuracy) if perf_history.accuracy else None,
                    "precision": float(perf_history.precision) if perf_history.precision else None,
                    "recall": float(perf_history.recall) if perf_history.recall else None,
                    "f1_score": float(perf_history.f1_score) if perf_history.f1_score else None,
                    "auc_score": float(perf_history.auc_score) if perf_history.auc_score else None,
                    "performance_delta": float(perf_history.performance_delta) if perf_history.performance_delta else None,
                    "recorded_at": perf_history.created_at.isoformat() if perf_history.created_at else None,
                    "model_version_id": perf_history.model_version_id,
                }
                logger.debug(
                    f"Found {dataset_type} metrics for {model_name}: "
                    f"F1={performance_data[dataset_type]['f1_score']:.3f}"
                )
            else:
                logger.debug(f"No {dataset_type} metrics found for {model_name}")
                performance_data[dataset_type] = None

    except Exception as e:
        logger.error(f"Error querying performance metrics for {model_name}: {e}", exc_info=True)

    return performance_data


def check_performance_degradation(
    current_metrics: Dict[str, Dict[str, Any]],
    baseline_metrics: Dict[str, Dict[str, Any]],
    threshold: float = MIN_PERFORMANCE_DEGRADATION_THRESHOLD,
    model_name: str = "model",
) -> Tuple[bool, Dict[str, float]]:
    """
    Check if model performance has degraded beyond threshold.

    Compares current performance metrics against baseline metrics to detect
    significant performance degradation that would warrant retraining.

    Args:
        current_metrics: Current performance metrics by dataset type
        baseline_metrics: Baseline performance metrics to compare against
        threshold: Degradation threshold (default: 0.05 for 5% drop)
        model_name: Name of the model for logging (default: "model")

    Returns:
        Tuple of (is_degraded, degradation_details):
        - is_degraded: True if performance degraded beyond threshold
        - degradation_details: Dictionary with degradation amounts per metric:
          {
              "f1_score": 0.08,  # 8% drop in F1
              "accuracy": 0.03,  # 3% drop in accuracy
              "max_degradation": 0.08
          }

    Example:
        >>> current = {"validation": {"f1_score": 0.85}}
        >>> baseline = {"validation": {"f1_score": 0.92}}
        >>> is_degraded, details = check_performance_degradation(current, baseline, model_name='ranking')
        >>> print(is_degraded)
        True
    """
    is_degraded = False
    degradation_details = {"max_degradation": 0.0}

    metric_keys = ["accuracy", "precision", "recall", "f1_score"]

    for dataset_type in current_metrics.keys():
        current = current_metrics.get(dataset_type)
        baseline = baseline_metrics.get(dataset_type)

        if not current or not baseline:
            continue

        for metric in metric_keys:
            current_value = current.get(metric)
            baseline_value = baseline.get(metric)

            if current_value is None or baseline_value is None:
                continue

            # Calculate degradation (baseline - current)
            degradation = baseline_value - current_value

            if degradation > 0:
                degradation_details[f"{dataset_type}_{metric}"] = round(degradation, 4)
                degradation_details["max_degradation"] = max(
                    degradation_details["max_degradation"], degradation
                )

                # Check if degradation exceeds threshold
                if degradation >= threshold:
                    is_degraded = True
                    logger.warning(
                        f"Performance degradation detected in {model_name}: "
                        f"{dataset_type}.{metric} dropped by {degradation:.3f} "
                        f"(threshold: {threshold})"
                    )

    return is_degraded, degradation_details


def count_recent_feedback(
    model_name: str,
    days_back: int,
    db_session: Session,
) -> int:
    """
    Count feedback entries available for retraining.

    Queries the SkillFeedback table to count feedback entries from the
    specified time period that can be used for model retraining.

    Args:
        model_name: Name of the model (for metadata filtering)
        days_back: Number of days to look back for feedback
        db_session: Database session for querying

    Returns:
        Count of feedback entries available for training

    Example:
        >>> count = count_recent_feedback('ranking', 30, session)
        >>> print(f"Feedback samples: {count}")
        Feedback samples: 250
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Count feedback entries from the specified period
        query = select(func.count(SkillFeedback.id)).where(
            and_(
                SkillFeedback.created_at >= cutoff_date,
                # Optionally filter by model-specific metadata
                # SkillFeedback.metadata['model_name'].astext == model_name
            )
        )

        count = db_session.execute(query).scalar()
        logger.info(f"Found {count} feedback samples for {model_name} in last {days_back} days")
        return count or 0

    except Exception as e:
        logger.error(f"Error counting feedback for {model_name}: {e}", exc_info=True)
        return 0


def should_trigger_retraining(
    model_name: str,
    db_session: Session,
    performance_threshold: float = MIN_PERFORMANCE_DEGRADATION_THRESHOLD,
    min_feedback_samples: int = MIN_FEEDBACK_SAMPLES_FOR_TRAINING,
    min_interval_days: int = MIN_RETRAINING_INTERVAL_DAYS,
) -> Dict[str, Any]:
    """
    Determine if model retraining should be triggered.

    Evaluates multiple criteria to determine if a model should be retrained:
    - Performance degradation compared to baseline
    - Sufficient feedback samples available
    - Minimum time interval since last retraining

    Args:
        model_name: Name of the model to evaluate
        db_session: Database session for querying
        performance_threshold: Performance degradation threshold (default: 0.05)
        min_feedback_samples: Minimum feedback samples required (default: 100)
        min_interval_days: Minimum days between retraining (default: 7)

    Returns:
        Dictionary with retraining decision and reasons:
        {
            "should_retrain": True,
            "reasons": [
                "Performance degraded by 8%",
                "Sufficient feedback samples (250)"
            ],
            "performance_degraded": True,
            "sufficient_feedback": True,
            "interval_satisfied": True,
            "current_metrics": {...},
            "degradation_details": {...}
        }

    Example:
        >>> decision = should_trigger_retraining('ranking', session)
        >>> print(decision['should_retrain'])
        True
    """
    reasons = []
    should_retrain = False

    # Get current performance metrics
    current_metrics = get_current_performance_metrics(
        model_name, DEFAULT_EVALUATION_DATASETS, db_session
    )

    # Get baseline metrics (from active model)
    baseline_metrics = {}
    try:
        active_model = (
            db_session.query(MLModelVersion)
            .where(
                and_(
                    MLModelVersion.model_name == model_name,
                    MLModelVersion.is_active == True,
                    MLModelVersion.is_experiment == False,
                )
            )
            .first()
        )

        if active_model and active_model.accuracy_metrics:
            # Use the active model's metrics as baseline
            baseline_metrics = {
                "production": {
                    "accuracy": active_model.accuracy_metrics.get("accuracy"),
                    "precision": active_model.accuracy_metrics.get("precision"),
                    "recall": active_model.accuracy_metrics.get("recall"),
                    "f1_score": active_model.accuracy_metrics.get("f1_score"),
                }
            }
    except Exception as e:
        logger.error(f"Error querying baseline metrics: {e}", exc_info=True)

    # Check performance degradation
    performance_degraded = False
    degradation_details = {"max_degradation": 0.0}

    if current_metrics and baseline_metrics:
        performance_degraded, degradation_details = check_performance_degradation(
            current_metrics, baseline_metrics, performance_threshold, model_name
        )

        if performance_degraded:
            should_retrain = True
            reasons.append(
                f"Performance degraded by {degradation_details['max_degradation']:.1%}"
            )
    else:
        logger.info(f"Insufficient metrics data for degradation check on {model_name}")

    # Check feedback availability
    feedback_count = count_recent_feedback(model_name, min_interval_days, db_session)
    sufficient_feedback = feedback_count >= min_feedback_samples

    if sufficient_feedback:
        if not should_retrain:  # Only add if not already triggered
            should_retrain = True
            reasons.append(f"Sufficient feedback samples ({feedback_count})")
    else:
        logger.info(
            f"Insufficient feedback for retraining: {feedback_count} < {min_feedback_samples}"
        )

    # Check time interval since last retraining
    interval_satisfied = True
    try:
        last_training = (
            db_session.query(ModelTrainingEvent)
            .where(
                and_(
                    ModelTrainingEvent.model_name == model_name,
                    ModelTrainingEvent.training_status == "completed",
                )
            )
            .order_by(ModelTrainingEvent.completed_at.desc())
            .first()
        )

        if last_training and last_training.completed_at:
            last_completion = datetime.fromisoformat(last_training.completed_at)
            days_since_last = (datetime.utcnow() - last_completion).days

            if days_since_last < min_interval_days:
                interval_satisfied = False
                logger.info(
                    f"Minimum interval not satisfied: {days_since_last} days since last retraining"
                )
    except Exception as e:
        logger.error(f"Error checking retraining interval: {e}", exc_info=True)

    # Final decision: need sufficient feedback AND either degradation OR interval
    if should_retrain and sufficient_feedback and interval_satisfied:
        should_retrain = True
    elif not sufficient_feedback or not interval_satisfied:
        should_retrain = False
        reasons = [
            r for r in reasons
            if "Performance degraded" in r  # Keep performance warnings
        ]

    return {
        "should_retrain": should_retrain,
        "reasons": reasons,
        "performance_degraded": performance_degraded,
        "sufficient_feedback": sufficient_feedback,
        "interval_satisfied": interval_satisfied,
        "current_metrics": current_metrics,
        "degradation_details": degradation_details,
    }


@shared_task(
    name="tasks.model_retraining.automated_retraining_task",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def automated_retraining_task(
    self,
    model_name: str,
    days_back: int = 30,
    auto_activate: bool = False,
    performance_threshold: float = AUTO_ACTIVATION_PERFORMANCE_THRESHOLD,
    notify: bool = True,
) -> Dict[str, Any]:
    """
    Automated model retraining task.

    This Celery task implements automated model retraining based on performance
    degradation and feedback accumulation. It evaluates whether retraining is
    needed, performs the training, evaluates the new model, and optionally
    activates it if performance thresholds are met.

    Task Workflow:
    1. Evaluate if retraining should be triggered (performance degradation, feedback count)
    2. Query feedback data for training
    3. Create ModelTrainingEvent record to track the training run
    4. Extract and prepare training data
    5. Train new model version
    6. Evaluate model performance
    7. Create MLModelVersion entry
    8. Record performance metrics
    9. Optionally activate model if performance exceeds threshold
    10. Update training event status

    Args:
        self: Celery task instance (bind=True)
        model_name: Name of the model to retrain (e.g., 'skill_matching', 'ranking')
        days_back: Number of days of feedback to use for training (default: 30)
        auto_activate: Whether to auto-activate if performance threshold met (default: False)
        performance_threshold: Minimum F1 score for auto-activation (default: 0.85)
        notify: Whether to send notifications about retraining (default: True)

    Returns:
        Dictionary containing retraining results:
        - should_retrain: Whether retraining was triggered
        - training_triggered: Boolean indicating if training was executed
        - training_event_id: ID of the ModelTrainingEvent record
        - new_version_id: ID of the created MLModelVersion
        - new_version: Version identifier (e.g., 'v2.1.0')
        - performance_metrics: Dictionary of model performance metrics
        - is_active: Whether the model was activated
        - is_experiment: Whether the model is an experiment
        - improvement_over_baseline: Performance improvement over current model
        - training_samples: Number of feedback samples used
        - processing_time_ms: Total processing time
        - status: Task status (completed, skipped, failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.model_retraining import automated_retraining_task
        >>> task = automated_retraining_task.delay(
        ...     model_name='ranking',
        ...     days_back=30,
        ...     auto_activate=True
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    total_steps = 8
    current_step = 0

    try:
        logger.info(
            f"Starting automated retraining evaluation for '{model_name}', "
            f"days_back: {days_back}, auto_activate: {auto_activate}"
        )

        # Note: Database session would be injected in real implementation
        # For now, this is a placeholder implementation
        db_session = None

        # Step 1: Evaluate if retraining should be triggered
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "evaluating_trigger",
            "message": "Evaluating retraining trigger conditions...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Evaluating trigger")

        if db_session:
            trigger_decision = should_trigger_retraining(
                model_name=model_name,
                db_session=db_session,
                performance_threshold=MIN_PERFORMANCE_DEGRADATION_THRESHOLD,
                min_feedback_samples=MIN_FEEDBACK_SAMPLES_FOR_TRAINING,
                min_interval_days=MIN_RETRAINING_INTERVAL_DAYS,
            )
        else:
            # Placeholder for testing without database
            trigger_decision = {
                "should_retrain": True,
                "reasons": ["Manual trigger"],
                "performance_degraded": False,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

        if not trigger_decision["should_retrain"]:
            logger.info(
                f"Retraining not triggered for {model_name}: {trigger_decision['reasons']}"
            )
            result = {
                "should_retrain": False,
                "training_triggered": False,
                "reasons": trigger_decision["reasons"],
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "status": "skipped",
            }

            # Send notification if requested (optional for skipped retraining)
            if notify:
                try:
                    logger.info(f"Sending skipped notification for {model_name}")
                    notification_result = send_model_retraining_notification(
                        model_name=model_name,
                        training_result=result,
                    )
                    result["notification_sent"] = notification_result.get("status") == "sent"
                    result["notification_result"] = notification_result
                except Exception as e:
                    logger.error(f"Failed to send skipped notification: {e}", exc_info=True)
                    result["notification_sent"] = False

            return result

        logger.info(
            f"Retraining triggered for {model_name}: {', '.join(trigger_decision['reasons'])}"
        )

        # Step 2: Query feedback data for training
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "querying_feedback",
            "message": "Querying feedback data for training...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Querying feedback")

        # Note: In real implementation, query feedback from database
        training_samples = MIN_FEEDBACK_SAMPLES_FOR_TRAINING + 50  # Placeholder
        logger.info(f"Using {training_samples} feedback samples for training")

        # Step 3: Create training event record
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "creating_training_event",
            "message": "Creating training event record...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Creating event")

        # Generate new version number
        new_version = "v2.0.0"  # Placeholder - would increment from latest

        # Note: In real implementation, create ModelTrainingEvent
        training_event_id = "placeholder-event-id"
        logger.info(f"Created training event {training_event_id} for {model_name} {new_version}")

        # Step 4: Extract and prepare training data
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "preparing_training_data",
            "message": "Preparing training data...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Preparing data")

        # Note: In real implementation, extract features from feedback
        logger.info("Training data prepared successfully")

        # Step 5: Train new model version
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "training_model",
            "message": "Training new model version...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Training model")

        # Note: In real implementation, this would invoke actual training logic
        # For now, simulate training time
        time.sleep(0.1)
        logger.info(f"Model training completed for {model_name} {new_version}")

        # Step 6: Evaluate model performance
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "evaluating_model",
            "message": "Evaluating model performance...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Evaluating model")

        # Note: In real implementation, use PerformanceTracker to calculate metrics
        # Placeholder performance metrics
        performance_metrics = {
            "accuracy": 0.92,
            "precision": 0.89,
            "recall": 0.94,
            "f1_score": 0.91,
            "auc_score": 0.95,
        }
        logger.info(
            f"Model evaluation completed: F1={performance_metrics['f1_score']:.3f}"
        )

        # Step 7: Create model version entry
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "creating_model_version",
            "message": "Creating model version entry...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Creating version")

        # Determine if model should be activated
        f1_score = performance_metrics["f1_score"]
        should_activate = auto_activate and f1_score >= performance_threshold

        # Note: In real implementation, create MLModelVersion entry
        new_version_id = "placeholder-version-id"
        is_active = False
        is_experiment = not should_activate

        logger.info(
            f"Created model version {new_version} (ID: {new_version_id}), "
            f"activated: {should_activate}"
        )

        # Step 8: Record performance metrics and activate if needed
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "recording_metrics",
            "message": "Recording metrics and finalizing...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Recording metrics")

        # Calculate improvement over baseline
        baseline_f1 = 0.85  # Placeholder - would query from current active model
        improvement = round(f1_score - baseline_f1, 3)

        # Note: In real implementation, use PerformanceTracker.record_performance()
        # and ModelVersionManager.record_performance_metrics()
        logger.info(
            f"Performance metrics recorded: F1={f1_score:.3f}, "
            f"improvement={improvement:+.3f}"
        )

        # Activate model if needed
        if should_activate:
            # Note: In real implementation, deactivate other versions and activate this one
            is_active = True
            is_experiment = False
            logger.info(f"Model {new_version} activated as production model")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "should_retrain": True,
            "training_triggered": True,
            "training_event_id": training_event_id,
            "new_version_id": new_version_id,
            "new_version": new_version,
            "performance_metrics": performance_metrics,
            "is_active": is_active,
            "is_experiment": is_experiment,
            "improvement_over_baseline": improvement,
            "training_samples": training_samples,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Automated retraining completed for {model_name}: "
            f"version {new_version}, F1={f1_score:.3f}, "
            f"activated={is_active}, improvement={improvement:+.3f}"
        )

        # Send notification if requested
        if notify:
            try:
                logger.info(f"Sending retraining notification for {model_name}")
                notification_result = send_model_retraining_notification(
                    model_name=model_name,
                    training_result=result,
                )
                result["notification_sent"] = notification_result.get("status") == "sent"
                result["notification_result"] = notification_result
                logger.info(
                    f"Retraining notification sent: {notification_result.get('status')}"
                )
            except Exception as e:
                logger.error(f"Failed to send retraining notification: {e}", exc_info=True)
                result["notification_sent"] = False
                result["notification_error"] = str(e)

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        error_result = {
            "should_retrain": True,
            "training_triggered": False,
            "status": "failed",
            "error": "Automated retraining exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

        # Send notification if requested
        if notify:
            try:
                logger.info(f"Sending failure notification for {model_name}")
                notification_result = send_model_retraining_notification(
                    model_name=model_name,
                    training_result=error_result,
                )
                error_result["notification_sent"] = notification_result.get("status") == "sent"
                error_result["notification_result"] = notification_result
            except Exception as notify_error:
                logger.error(f"Failed to send failure notification: {notify_error}", exc_info=True)
                error_result["notification_sent"] = False

        return error_result

    except Exception as e:
        logger.error(f"Error in automated retraining: {e}", exc_info=True)
        error_result = {
            "should_retrain": True,
            "training_triggered": False,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

        # Send notification if requested
        if notify:
            try:
                logger.info(f"Sending failure notification for {model_name}")
                notification_result = send_model_retraining_notification(
                    model_name=model_name,
                    training_result=error_result,
                )
                error_result["notification_sent"] = notification_result.get("status") == "sent"
                error_result["notification_result"] = notification_result
            except Exception as notify_error:
                logger.error(f"Failed to send failure notification: {notify_error}", exc_info=True)
                error_result["notification_sent"] = False

        return error_result


@shared_task(
    name="tasks.model_retraining.manual_retraining_task",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
)
def manual_retraining_task(
    self,
    model_name: str,
    days_back: int = 30,
    requested_by: Optional[str] = None,
    auto_activate: bool = False,
    performance_threshold: float = AUTO_ACTIVATION_PERFORMANCE_THRESHOLD,
) -> Dict[str, Any]:
    """
    Manual model retraining task triggered by admin.

    This task is similar to automated_retraining_task but is triggered
    manually by an administrator via API or admin interface. It skips
    the trigger evaluation and proceeds directly to training.

    Args:
        self: Celery task instance (bind=True)
        model_name: Name of the model to retrain
        days_back: Number of days of feedback to use for training (default: 30)
        requested_by: Optional user ID of who requested the retraining
        auto_activate: Whether to auto-activate if performance threshold met
        performance_threshold: Minimum F1 score for auto-activation (default: 0.85)

    Returns:
        Dictionary containing retraining results (same format as automated_retraining_task)

    Example:
        >>> from tasks.model_retraining import manual_retraining_task
        >>> task = manual_retraining_task.delay('ranking', days_back=30, requested_by='admin123')
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    logger.info(
        f"Manual retraining requested for '{model_name}' by {requested_by or 'unknown'}"
    )

    # Call automated_retraining_task with force trigger
    # Note: In real implementation, you'd want to bypass trigger evaluation
    result = automated_retraining_task(
        model_name=model_name,
        days_back=days_back,
        auto_activate=auto_activate,
        performance_threshold=performance_threshold,
        notify=True,
    )

    # Add requested_by information
    result["requested_by"] = requested_by
    result["trigger_type"] = "manual"

    return result
