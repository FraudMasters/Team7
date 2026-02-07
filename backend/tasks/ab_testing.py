"""
A/B testing tasks for automated model comparison.

This module provides Celery tasks for A/B testing model versions to compare
their performance before deploying new models to production. It includes
statistical significance testing, metrics comparison, and automated
decision-making for model rollout.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
from math import sqrt

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from models.ml_model_version import MLModelVersion
from models.model_performance_history import ModelPerformanceHistory
from models.skill_feedback import SkillFeedback
from analyzers.performance_tracker import PerformanceTracker
from analyzers.model_versioning import ModelVersionManager
from config import get_settings
from tasks.model_retraining import get_sync_session

logger = logging.getLogger(__name__)
settings = get_settings()

# Minimum sample size for A/B testing
MIN_AB_TEST_SAMPLE_SIZE = 100

# Statistical significance threshold (p-value)
STATISTICAL_SIGNIFICANCE_THRESHOLD = 0.05

# Minimum improvement threshold to consider new model better
MIN_IMPROVEMENT_THRESHOLD = 0.02  # 2% improvement

# Default confidence interval for A/B tests (95%)
DEFAULT_CONFIDENCE_LEVEL = 0.95

# Maximum time window for A/B test data (days)
MAX_AB_TEST_DATA_WINDOW_DAYS = 30


def calculate_two_sample_z_test(
    control_mean: float,
    treatment_mean: float,
    control_std: float,
    treatment_std: float,
    control_size: int,
    treatment_size: int,
) -> Tuple[float, float, bool]:
    """
    Calculate two-sample z-test for comparing model performance.

    This function performs a two-sample z-test to determine if there is a
    statistically significant difference between the control (current) and
    treatment (new) model performance metrics.

    Args:
        control_mean: Mean performance metric for control model
        treatment_mean: Mean performance metric for treatment model
        control_std: Standard deviation of control model metrics
        treatment_std: Standard deviation of treatment model metrics
        control_size: Sample size for control model
        treatment_size: Sample size for treatment model

    Returns:
        Tuple of (z_score, p_value, is_significant):
        - z_score: Calculated z-score
        - p_value: Two-tailed p-value
        - is_significant: True if p-value < threshold (0.05)

    Example:
        >>> z, p, sig = calculate_two_sample_z_test(0.85, 0.88, 0.12, 0.11, 500, 500)
        >>> print(f"Z-score: {z:.2f}, P-value: {p:.4f}, Significant: {sig}")
        Z-score: 4.11, P-value: 0.0000, Significant: True
    """
    try:
        # Calculate pooled standard error
        if control_size == 0 or treatment_size == 0:
            return 0.0, 1.0, False

        # Standard error of the difference between means
        se_control = control_std / sqrt(control_size) if control_size > 0 else 0
        se_treatment = treatment_std / sqrt(treatment_size) if treatment_size > 0 else 0
        se_diff = sqrt(se_control ** 2 + se_treatment ** 2)

        if se_diff == 0:
            return 0.0, 1.0, False

        # Calculate z-score
        z_score = (treatment_mean - control_mean) / se_diff

        # Calculate two-tailed p-value using error function approximation
        # For a more accurate implementation, scipy.stats would be used
        # This is a simplified approximation for z-score to p-value
        abs_z = abs(z_score)
        # Approximate p-value using complementary error function
        # p-value ≈ 2 * (1 - Φ(|z|)) where Φ is the standard normal CDF
        # Using a simple approximation for Φ
        if abs_z < 0.1:
            p_value = 1.0
        elif abs_z > 10:
            p_value = 0.0
        else:
            # Abramowitz and Stegun approximation for standard normal CDF
            t = 1.0 / (1.0 + 0.2316419 * abs_z)
            phi = 1.0 - 0.5 * t * (
                0.319381530
                + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429)))
            )
            p_value = 2.0 * (1.0 - phi)

        # Check if statistically significant
        is_significant = p_value < STATISTICAL_SIGNIFICANCE_THRESHOLD

        logger.debug(
            f"Z-test: control={control_mean:.4f}±{control_std:.4f} (n={control_size}), "
            f"treatment={treatment_mean:.4f}±{treatment_std:.4f} (n={treatment_size}), "
            f"z={z_score:.2f}, p={p_value:.4f}, significant={is_significant}"
        )

        return round(z_score, 4), round(p_value, 4), is_significant

    except Exception as e:
        logger.error(f"Error calculating z-test: {e}", exc_info=True)
        return 0.0, 1.0, False


def calculate_confidence_interval(
    sample_mean: float,
    sample_std: float,
    sample_size: int,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> Tuple[float, float]:
    """
    Calculate confidence interval for a sample mean.

    Args:
        sample_mean: Sample mean
        sample_std: Sample standard deviation
        sample_size: Sample size
        confidence_level: Confidence level (default: 0.95 for 95%)

    Returns:
        Tuple of (lower_bound, upper_bound) for the confidence interval

    Example:
        >>> lower, upper = calculate_confidence_interval(0.85, 0.12, 500)
        >>> print(f"95% CI: [{lower:.4f}, {upper:.4f}]")
        95% CI: [0.8395, 0.8605]
    """
    try:
        if sample_size == 0 or sample_std == 0:
            return sample_mean, sample_mean

        # Z-score for common confidence levels
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z_score = z_scores.get(confidence_level, 1.96)

        # Standard error
        se = sample_std / sqrt(sample_size)

        # Margin of error
        margin = z_score * se

        lower_bound = sample_mean - margin
        upper_bound = sample_mean + margin

        return round(lower_bound, 4), round(upper_bound, 4)

    except Exception as e:
        logger.error(f"Error calculating confidence interval: {e}", exc_info=True)
        return sample_mean, sample_mean


def calculate_effect_size(
    control_mean: float,
    treatment_mean: float,
    control_std: float,
    treatment_std: float,
) -> float:
    """
    Calculate Cohen's d effect size.

    Effect size measures the magnitude of difference between two groups,
    independent of sample size. Interpretation:
    - Small: ~0.2
    - Medium: ~0.5
    - Large: ~0.8+

    Args:
        control_mean: Mean of control group
        treatment_mean: Mean of treatment group
        control_std: Standard deviation of control group
        treatment_std: Standard deviation of treatment group

    Returns:
        Cohen's d effect size

    Example:
        >>> d = calculate_effect_size(0.85, 0.88, 0.12, 0.11)
        >>> print(f"Effect size (Cohen's d): {d:.2f}")
        Effect size (Cohen's d): 0.26
    """
    try:
        # Pooled standard deviation
        pooled_std = sqrt((control_std ** 2 + treatment_std ** 2) / 2)

        if pooled_std == 0:
            return 0.0

        # Cohen's d
        effect_size = (treatment_mean - control_mean) / pooled_std

        return round(effect_size, 4)

    except Exception as e:
        logger.error(f"Error calculating effect size: {e}", exc_info=True)
        return 0.0


def query_ab_test_feedback_data(
    control_version_id: str,
    treatment_version_id: str,
    db_session: Session,
    days_back: int = MAX_AB_TEST_DATA_WINDOW_DAYS,
) -> Dict[str, List[SkillFeedback]]:
    """
    Query feedback data for A/B testing.

    Retrieves feedback entries for both control and treatment model versions
    from the specified time period.

    Args:
        control_version_id: ID of the control (current) model version
        treatment_version_id: ID of the treatment (new) model version
        db_session: Database session
        days_back: Number of days to look back for feedback data

    Returns:
        Dictionary with control and treatment feedback lists:
        {
            "control": [SkillFeedback, ...],
            "treatment": [SkillFeedback, ...]
        }

    Example:
        >>> data = query_ab_test_feedback_data('v1', 'v2', session)
        >>> print(f"Control: {len(data['control'])}, Treatment: {len(data['treatment'])}")
        Control: 250, Treatment: 300
    """
    result = {"control": [], "treatment": []}

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Query control version feedback
        control_query = (
            select(SkillFeedback)
            .where(
                and_(
                    SkillFeedback.model_version_id == control_version_id,
                    SkillFeedback.created_at >= cutoff_date,
                    SkillFeedback.was_correct.isnot(None),
                )
            )
            .order_by(SkillFeedback.created_at.desc())
        )

        control_result = db_session.execute(control_query)
        result["control"] = control_result.scalars().all()

        # Query treatment version feedback
        treatment_query = (
            select(SkillFeedback)
            .where(
                and_(
                    SkillFeedback.model_version_id == treatment_version_id,
                    SkillFeedback.created_at >= cutoff_date,
                    SkillFeedback.was_correct.isnot(None),
                )
            )
            .order_by(SkillFeedback.created_at.desc())
        )

        treatment_result = db_session.execute(treatment_query)
        result["treatment"] = treatment_result.scalars().all()

        logger.info(
            f"Queried A/B test feedback: control={len(result['control'])}, "
            f"treatment={len(result['treatment'])} samples"
        )

        return result

    except Exception as e:
        logger.error(f"Error querying A/B test feedback data: {e}", exc_info=True)
        return result


def calculate_accuracy_metrics(
    feedback_entries: List[SkillFeedback],
) -> Dict[str, Any]:
    """
    Calculate accuracy metrics from feedback entries.

    Args:
        feedback_entries: List of SkillFeedback objects

    Returns:
        Dictionary with calculated metrics:
        {
            "accuracy": 0.85,
            "sample_size": 200,
            "correct_count": 170,
            "incorrect_count": 30,
            "std": 0.36  # Standard deviation (binary data)
        }

    Example:
        >>> metrics = calculate_accuracy_metrics(feedback_list)
        >>> print(f"Accuracy: {metrics['accuracy']:.2%}")
        Accuracy: 85.00%
    """
    try:
        if not feedback_entries:
            return {
                "accuracy": 0.0,
                "sample_size": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "std": 0.0,
            }

        sample_size = len(feedback_entries)
        correct_count = sum(1 for f in feedback_entries if f.was_correct)
        incorrect_count = sample_size - correct_count

        # Calculate accuracy
        accuracy = correct_count / sample_size if sample_size > 0 else 0.0

        # For binary accuracy data (0 or 1), std = sqrt(p * (1-p))
        # This is the standard deviation of a Bernoulli distribution
        std = sqrt(accuracy * (1 - accuracy)) if 0 < accuracy < 1 else 0.0

        return {
            "accuracy": accuracy,
            "sample_size": sample_size,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "std": std,
        }

    except Exception as e:
        logger.error(f"Error calculating accuracy metrics: {e}", exc_info=True)
        return {
            "accuracy": 0.0,
            "sample_size": 0,
            "correct_count": 0,
            "incorrect_count": 0,
            "std": 0.0,
        }


def compare_model_metrics(
    control_metrics: Dict[str, Any],
    treatment_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare metrics between control and treatment models.

    Performs statistical tests to determine if the treatment model
    significantly outperforms the control model.

    Args:
        control_metrics: Metrics dictionary for control model
        treatment_metrics: Metrics dictionary for treatment model

    Returns:
        Dictionary with comparison results:
        {
            "accuracy_improvement": 0.03,  # 3% improvement
            "relative_improvement": 0.035,  # 3.5% relative improvement
            "z_score": 2.45,
            "p_value": 0.0142,
            "is_statistically_significant": True,
            "is_better": True,
            "effect_size": 0.25,
            "control_ci": [0.82, 0.88],
            "treatment_ci": [0.85, 0.91],
            "recommendation": "deploy_treatment"
        }

    Example:
        >>> result = compare_model_metrics(control, treatment)
        >>> print(result['recommendation'])
        deploy_treatment
    """
    try:
        control_acc = control_metrics.get("accuracy", 0.0)
        treatment_acc = treatment_metrics.get("accuracy", 0.0)
        control_std = control_metrics.get("std", 0.0)
        treatment_std = treatment_metrics.get("std", 0.0)
        control_n = control_metrics.get("sample_size", 0)
        treatment_n = treatment_metrics.get("sample_size", 0)

        # Calculate improvement
        accuracy_improvement = treatment_acc - control_acc
        relative_improvement = (
            (accuracy_improvement / control_acc) if control_acc > 0 else 0.0
        )

        # Perform z-test
        z_score, p_value, is_significant = calculate_two_sample_z_test(
            control_mean=control_acc,
            treatment_mean=treatment_acc,
            control_std=control_std,
            treatment_std=treatment_std,
            control_size=control_n,
            treatment_size=treatment_n,
        )

        # Calculate effect size
        effect_size = calculate_effect_size(
            control_mean=control_acc,
            treatment_mean=treatment_acc,
            control_std=control_std,
            treatment_std=treatment_std,
        )

        # Calculate confidence intervals
        control_ci = calculate_confidence_interval(control_acc, control_std, control_n)
        treatment_ci = calculate_confidence_interval(
            treatment_acc, treatment_std, treatment_n
        )

        # Determine if treatment is better
        is_better = (
            is_significant
            and accuracy_improvement >= MIN_IMPROVEMENT_THRESHOLD
        )

        # Generate recommendation
        if is_better:
            recommendation = "deploy_treatment"
        elif is_significant and accuracy_improvement < -MIN_IMPROVEMENT_THRESHOLD:
            recommendation = "keep_control"
        else:
            recommendation = "insufficient_evidence"

        result = {
            "accuracy_improvement": round(accuracy_improvement, 4),
            "relative_improvement": round(relative_improvement, 4),
            "z_score": z_score,
            "p_value": p_value,
            "is_statistically_significant": is_significant,
            "is_better": is_better,
            "effect_size": effect_size,
            "control_ci": control_ci,
            "treatment_ci": treatment_ci,
            "recommendation": recommendation,
        }

        logger.info(
            f"A/B test comparison: improvement={accuracy_improvement:+.2%}, "
            f"p={p_value:.4f}, significant={is_significant}, "
            f"recommendation={recommendation}"
        )

        return result

    except Exception as e:
        logger.error(f"Error comparing model metrics: {e}", exc_info=True)
        return {
            "accuracy_improvement": 0.0,
            "relative_improvement": 0.0,
            "z_score": 0.0,
            "p_value": 1.0,
            "is_statistically_significant": False,
            "is_better": False,
            "effect_size": 0.0,
            "control_ci": [0.0, 0.0],
            "treatment_ci": [0.0, 0.0],
            "recommendation": "error",
        }


def evaluate_ab_test_core(
    control_version_id: str,
    treatment_version_id: str,
    db_session: Session,
    days_back: int = MAX_AB_TEST_DATA_WINDOW_DAYS,
) -> Dict[str, Any]:
    """
    Core A/B testing logic without Celery dependencies.

    This function implements the actual A/B test evaluation workflow and can be
    called directly or wrapped in a Celery task.

    Args:
        control_version_id: ID of the control (current) model version
        treatment_version_id: ID of the treatment (new) model version
        db_session: Database session
        days_back: Number of days of feedback to use for testing

    Returns:
        Dictionary containing A/B test results

    Example:
        >>> result = evaluate_ab_test_core('v1-id', 'v2-id', session)
        >>> print(result['recommendation'])
        deploy_treatment
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting A/B test evaluation: control={control_version_id}, "
            f"treatment={treatment_version_id}, days_back={days_back}"
        )

        # Query model versions
        control_model = (
            db_session.query(MLModelVersion)
            .filter(MLModelVersion.id == control_version_id)
            .first()
        )

        treatment_model = (
            db_session.query(MLModelVersion)
            .filter(MLModelVersion.id == treatment_version_id)
            .first()
        )

        if not control_model or not treatment_model:
            error_msg = "Model version not found"
            if not control_model:
                error_msg += f": control_version_id={control_version_id}"
            if not treatment_model:
                error_msg += f": treatment_version_id={treatment_version_id}"

            return {
                "status": "failed",
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Query feedback data
        feedback_data = query_ab_test_feedback_data(
            control_version_id, treatment_version_id, db_session, days_back
        )

        control_feedback = feedback_data.get("control", [])
        treatment_feedback = feedback_data.get("treatment", [])

        logger.info(
            f"Feedback samples: control={len(control_feedback)}, "
            f"treatment={len(treatment_feedback)}"
        )

        # Check minimum sample size
        if len(control_feedback) < MIN_AB_TEST_SAMPLE_SIZE:
            return {
                "status": "insufficient_data",
                "error": f"Insufficient control samples: {len(control_feedback)} < {MIN_AB_TEST_SAMPLE_SIZE}",
                "control_sample_size": len(control_feedback),
                "treatment_sample_size": len(treatment_feedback),
                "min_required": MIN_AB_TEST_SAMPLE_SIZE,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        if len(treatment_feedback) < MIN_AB_TEST_SAMPLE_SIZE:
            return {
                "status": "insufficient_data",
                "error": f"Insufficient treatment samples: {len(treatment_feedback)} < {MIN_AB_TEST_SAMPLE_SIZE}",
                "control_sample_size": len(control_feedback),
                "treatment_sample_size": len(treatment_feedback),
                "min_required": MIN_AB_TEST_SAMPLE_SIZE,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Calculate metrics for both models
        control_metrics = calculate_accuracy_metrics(control_feedback)
        treatment_metrics = calculate_accuracy_metrics(treatment_feedback)

        logger.info(
            f"Metrics: control_accuracy={control_metrics['accuracy']:.3f}, "
            f"treatment_accuracy={treatment_metrics['accuracy']:.3f}"
        )

        # Compare metrics
        comparison = compare_model_metrics(control_metrics, treatment_metrics)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "status": "completed",
            "control_version_id": control_version_id,
            "control_version": control_model.version,
            "treatment_version_id": treatment_version_id,
            "treatment_version": treatment_model.version,
            "control_metrics": control_metrics,
            "treatment_metrics": treatment_metrics,
            "comparison": comparison,
            "recommendation": comparison.get("recommendation"),
            "control_sample_size": len(control_feedback),
            "treatment_sample_size": len(treatment_feedback),
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"A/B test completed: {result['recommendation']}, "
            f"improvement={comparison['accuracy_improvement']:+.2%}, "
            f"p={comparison['p_value']:.4f}"
        )

        return result

    except Exception as e:
        logger.error(f"Error in core A/B test evaluation: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.ab_testing.evaluate_ab_test",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def evaluate_ab_test(
    self,
    control_version_id: str,
    treatment_version_id: str,
    days_back: int = MAX_AB_TEST_DATA_WINDOW_DAYS,
    auto_activate_if_better: bool = False,
) -> Dict[str, Any]:
    """
    A/B testing task for comparing model versions.

    This Celery task performs A/B testing between a control (current production)
    model and a treatment (newly trained) model to determine if the new model
    should be deployed to production.

    Task Workflow:
    1. Query feedback data for both model versions
    2. Calculate accuracy metrics for each model
    3. Perform statistical significance testing (z-test)
    4. Calculate effect size and confidence intervals
    5. Generate deployment recommendation
    6. Optionally activate treatment model if it's significantly better

    Args:
        self: Celery task instance (bind=True)
        control_version_id: ID of the control (current) model version
        treatment_version_id: ID of the treatment (new) model version
        days_back: Number of days of feedback to use for testing (default: 30)
        auto_activate_if_better: Whether to auto-activate if treatment wins (default: False)

    Returns:
        Dictionary containing A/B test results:
        - status: Test status (completed, insufficient_data, failed)
        - control_version_id: ID of control model
        - control_version: Version string of control model
        - treatment_version_id: ID of treatment model
        - treatment_version: Version string of treatment model
        - control_metrics: Metrics for control model
        - treatment_metrics: Metrics for treatment model
        - comparison: Statistical comparison results
        - recommendation: Deployment recommendation (deploy_treatment, keep_control, insufficient_evidence)
        - activated: Whether treatment was activated (if auto_activate_if_better=True)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.ab_testing import evaluate_ab_test
        >>> task = evaluate_ab_test.delay(
        ...     control_version_id='control-id',
        ...     treatment_version_id='treatment-id',
        ...     auto_activate_if_better=True
        ... )
        >>> result = task.get()
        >>> print(result['recommendation'])
        deploy_treatment
    """
    start_time = time.time()
    total_steps = 4
    current_step = 0

    db_session = None

    try:
        logger.info(
            f"Starting A/B test task: control={control_version_id}, "
            f"treatment={treatment_version_id}, auto_activate={auto_activate_if_better}"
        )

        # Step 1: Create database session and query versions
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "querying_versions",
            "message": "Querying model versions...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Querying versions")

        db_session = get_sync_session()

        if db_session is None:
            return {
                "status": "failed",
                "error": "Failed to create database session",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 2: Query feedback data
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "querying_feedback",
            "message": "Querying feedback data...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Querying feedback")

        # Step 3: Calculate metrics and perform comparison
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "calculating_metrics",
            "message": "Calculating metrics and performing comparison...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Calculating metrics")

        # Call the core evaluation function
        result = evaluate_ab_test_core(
            control_version_id=control_version_id,
            treatment_version_id=treatment_version_id,
            db_session=db_session,
            days_back=days_back,
        )

        if result["status"] != "completed":
            return result

        # Step 4: Auto-activate if requested and treatment is better
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "finalizing",
            "message": "Finalizing A/B test...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Finalizing")

        activated = False
        if auto_activate_if_better and result.get("recommendation") == "deploy_treatment":
            try:
                # Import here to avoid circular dependency
                from tasks.model_retraining import activate_model_version

                model_name = (
                    db_session.query(MLModelVersion)
                    .filter(MLModelVersion.id == treatment_version_id)
                    .first()
                )

                if model_name:
                    activation_success = activate_model_version(
                        model_name=model_name.model_name,
                        model_version_id=treatment_version_id,
                        db_session=db_session,
                    )
                    activated = activation_success

                    if activated:
                        logger.info(
                            f"Treatment model {result['treatment_version']} activated automatically"
                        )
                    else:
                        logger.warning("Failed to activate treatment model")
            except Exception as e:
                logger.error(f"Error auto-activating treatment model: {e}", exc_info=True)

        result["activated"] = activated

        # Close database session
        db_session.close()

        logger.info(
            f"A/B test task completed: recommendation={result.get('recommendation')}, "
            f"activated={activated}, time={result.get('processing_time_ms')}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "status": "failed",
            "error": "A/B test evaluation exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in A/B test task: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    finally:
        # Ensure database session is closed
        if db_session:
            try:
                db_session.close()
            except Exception:
                pass


@shared_task(
    name="tasks.ab_testing.batch_ab_test_evaluation",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
)
def batch_ab_test_evaluation(
    self,
    model_name: str,
    days_back: int = MAX_AB_TEST_DATA_WINDOW_DAYS,
) -> Dict[str, Any]:
    """
    Batch A/B testing task for all experimental versions of a model.

    This task evaluates all experimental (non-active) versions of a model
    against the current production (active) version to identify candidates
    for deployment.

    Args:
        self: Celery task instance (bind=True)
        model_name: Name of the model to evaluate
        days_back: Number of days of feedback to use for testing

    Returns:
        Dictionary containing batch test results:
        - status: Batch status (completed, failed)
        - model_name: Name of the model tested
        - control_version_id: Active model version ID
        - evaluations: List of individual test results
        - best_candidate: Best performing experimental version
        - total_evaluations: Number of evaluations performed
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.ab_testing import batch_ab_test_evaluation
        >>> task = batch_ab_test_evaluation.delay('skill_matching')
        >>> result = task.get()
        >>> print(result['best_candidate']['treatment_version'])
        v2.1.0
    """
    start_time = time.time()

    db_session = None

    try:
        logger.info(f"Starting batch A/B test evaluation for model: {model_name}")

        db_session = get_sync_session()

        if db_session is None:
            return {
                "status": "failed",
                "error": "Failed to create database session",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Get active (production) model
        control_model = (
            db_session.query(MLModelVersion)
            .filter(
                and_(
                    MLModelVersion.model_name == model_name,
                    MLModelVersion.is_active == True,
                    MLModelVersion.is_experiment == False,
                )
            )
            .first()
        )

        if not control_model:
            return {
                "status": "failed",
                "error": f"No active production model found for: {model_name}",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Get all experimental versions
        experimental_models = (
            db_session.query(MLModelVersion)
            .filter(
                and_(
                    MLModelVersion.model_name == model_name,
                    MLModelVersion.is_experiment == True,
                )
            )
            .order_by(MLModelVersion.created_at.desc())
            .all()
        )

        if not experimental_models:
            return {
                "status": "completed",
                "model_name": model_name,
                "control_version_id": str(control_model.id),
                "control_version": control_model.version,
                "evaluations": [],
                "best_candidate": None,
                "total_evaluations": 0,
                "message": "No experimental versions found",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        logger.info(
            f"Found {len(experimental_models)} experimental versions to test against {control_model.version}"
        )

        # Evaluate each experimental version
        evaluations = []
        best_candidate = None
        best_score = -float("inf")

        for exp_model in experimental_models:
            logger.info(f"Evaluating {exp_model.version}...")

            result = evaluate_ab_test_core(
                control_version_id=str(control_model.id),
                treatment_version_id=str(exp_model.id),
                db_session=db_session,
                days_back=days_back,
            )

            result["treatment_is_experiment"] = exp_model.is_experiment
            evaluations.append(result)

            # Track best candidate
            if result.get("status") == "completed":
                comparison = result.get("comparison", {})
                if comparison.get("is_better"):
                    improvement = comparison.get("accuracy_improvement", 0)
                    if improvement > best_score:
                        best_score = improvement
                        best_candidate = result

        db_session.close()

        logger.info(
            f"Batch A/B test completed for {model_name}: "
            f"{len(evaluations)} evaluations, best_candidate={best_candidate.get('treatment_version') if best_candidate else None}"
        )

        return {
            "status": "completed",
            "model_name": model_name,
            "control_version_id": str(control_model.id),
            "control_version": control_model.version,
            "evaluations": evaluations,
            "best_candidate": best_candidate,
            "total_evaluations": len(evaluations),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in batch A/B test evaluation: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    finally:
        if db_session:
            try:
                db_session.close()
            except Exception:
                pass
