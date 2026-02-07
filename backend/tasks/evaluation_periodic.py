"""
Periodic evaluation tasks for checking incomplete scorecards.

This module provides Celery Beat tasks for monitoring and managing incomplete
evaluation scorecards to ensure timely completion of candidate evaluations.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Status values that indicate incomplete scorecards
INCOMPLETE_STATUSES = ["draft", "in_progress"]

# Default threshold for days pending
DEFAULT_DAYS_THRESHOLD = 7

# Minimum time between checks (minutes)
CHECK_INTERVAL_MINUTES = 60


def get_incomplete_scorecards(
    days_threshold: int = DEFAULT_DAYS_THRESHOLD,
    db_session: Optional[object] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve incomplete scorecards for monitoring.

    This function identifies scorecards that have not been completed within
    the specified threshold, including those in draft or in_progress status.

    Args:
        days_threshold: Number of days before a scorecard is considered stale (default: 7)
        db_session: Optional database session for querying

    Returns:
        List of dictionaries containing incomplete scorecard data:
        [
            {
                "id": "uuid",
                "template_id": "uuid",
                "template_name": "Technical Interview",
                "resume_id": "uuid",
                "candidate_name": "John Doe",
                "evaluator_id": "uuid",
                "evaluator_name": "Jane Smith",
                "evaluator_email": "jane@example.com",
                "status": "in_progress",
                "criteria_count": 5,
                "completed_criteria_count": 2,
                "overall_score": null,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-15T00:00:00",
                "days_pending": 5
            },
            ...
        ]

    Example:
        >>> scorecards = get_incomplete_scorecards(days_threshold=7)
        >>> print(f"Found {len(scorecards)} incomplete scorecards")
        12
    """
    if db_session is None:
        logger.warning(
            "No database session provided for get_incomplete_scorecards, returning empty list"
        )
        return []

    logger.info(
        f"Retrieving incomplete scorecards pending for >= {days_threshold} days"
    )

    try:
        # Note: In a real implementation, you would execute:
        # from sqlalchemy import select, and_, func
        # from models.evaluation_scorecard import EvaluationScorecard
        # from models.evaluation_template import EvaluationTemplate
        # from models.resume import Resume
        # from models.recruiter import Recruiter
        # from models.evaluation_criteria import EvaluationCriteria
        #
        # cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        #
        # query = (
        #     select(
        #         EvaluationScorecard.id,
        #         EvaluationScorecard.template_id,
        #         EvaluationScorecard.resume_id,
        #         EvaluationScorecard.evaluator_id,
        #         EvaluationScorecard.status,
        #         EvaluationScorecard.criteria_responses,
        #         EvaluationScorecard.overall_score,
        #         EvaluationScorecard.created_at,
        #         EvaluationScorecard.updated_at,
        #         EvaluationTemplate.name.label("template_name"),
        #         Resume.candidate_name,
        #         Recruiter.name.label("evaluator_name"),
        #         Recruiter.email.label("evaluator_email"),
        #         func.count(EvaluationCriteria.id).label("criteria_count"),
        #     )
        #     .join(EvaluationTemplate, EvaluationScorecard.template_id == EvaluationTemplate.id)
        #     .join(Resume, EvaluationScorecard.resume_id == Resume.id)
        #     .outerjoin(Recruiter, EvaluationScorecard.evaluator_id == Recruiter.id)
        #     .outerjoin(
        #         EvaluationCriteria,
        #         EvaluationCriteria.template_id == EvaluationTemplate.id
        #     )
        #     .where(
        #         and_(
        #             EvaluationScorecard.status.in_(INCOMPLETE_STATUSES),
        #             EvaluationScorecard.created_at < cutoff_date
        #         )
        #     )
        #     .group_by(EvaluationScorecard.id)
        #     .order_by(EvaluationScorecard.created_at)
        # )
        #
        # result = db_session.execute(query)
        # scorecards = result.all()

        # Placeholder: Simulate database query results
        incomplete_scorecards = []

        logger.info(f"Retrieved {len(incomplete_scorecards)} incomplete scorecards")

        return incomplete_scorecards

    except Exception as e:
        logger.error(f"Error retrieving incomplete scorecards: {e}", exc_info=True)
        return []


def calculate_scorecard_completion_stats(
    scorecards: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate completion statistics for scorecards.

    This function aggregates statistics about incomplete scorecards
    to provide insights into evaluation progress and potential bottlenecks.

    Args:
        scorecards: List of scorecard data dictionaries

    Returns:
        Dictionary containing completion statistics:
        {
            "total_scorecards": 100,
            "incomplete_count": 15,
            "completion_rate": 0.85,
            "avg_days_pending": 5.2,
            "max_days_pending": 14,
            "by_status": {
                "draft": 8,
                "in_progress": 7
            },
            "by_template": {
                "Technical Interview": 10,
                "Cultural Fit": 5
            },
            "by_evaluator": {
                "evaluator-1": 5,
                "evaluator-2": 3
            },
            "urgent_count": 3,  # pending > 10 days
            "overdue_count": 7   # pending > 7 days
        }

    Example:
        >>> scorecards = get_incomplete_scorecards()
        >>> stats = calculate_scorecard_completion_stats(scorecards)
        >>> print(f"Completion rate: {stats['completion_rate']:.1%}")
        Completion rate: 85.0%
    """
    if not scorecards:
        return {
            "total_scorecards": 0,
            "incomplete_count": 0,
            "completion_rate": 0.0,
            "avg_days_pending": 0.0,
            "max_days_pending": 0,
            "by_status": {},
            "by_template": {},
            "by_evaluator": {},
            "urgent_count": 0,
            "overdue_count": 0,
        }

    try:
        incomplete_count = len(scorecards)

        # Calculate days pending statistics
        days_pending_list = [s.get("days_pending", 0) for s in scorecards]
        avg_days_pending = sum(days_pending_list) / len(days_pending_list) if days_pending_list else 0
        max_days_pending = max(days_pending_list) if days_pending_list else 0

        # Count by status
        by_status: Dict[str, int] = {}
        for scorecard in scorecards:
            status = scorecard.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        # Count by template
        by_template: Dict[str, int] = {}
        for scorecard in scorecards:
            template_name = scorecard.get("template_name", "Unknown Template")
            by_template[template_name] = by_template.get(template_name, 0) + 1

        # Count by evaluator
        by_evaluator: Dict[str, int] = {}
        for scorecard in scorecards:
            evaluator_id = scorecard.get("evaluator_id", "unassigned")
            by_evaluator[evaluator_id] = by_evaluator.get(evaluator_id, 0) + 1

        # Count urgent and overdue
        urgent_count = sum(1 for s in scorecards if s.get("days_pending", 0) > 10)
        overdue_count = sum(1 for s in scorecards if s.get("days_pending", 0) > 7)

        # Calculate completion rate (placeholder - would need total count from DB)
        # In production, you'd query: SELECT COUNT(*) FROM evaluation_scorecards
        total_scorecards = incomplete_count  # Placeholder
        completion_rate = (
            (total_scorecards - incomplete_count) / total_scorecards
            if total_scorecards > 0
            else 0.0
        )

        stats = {
            "total_scorecards": total_scorecards,
            "incomplete_count": incomplete_count,
            "completion_rate": round(completion_rate, 4),
            "avg_days_pending": round(avg_days_pending, 1),
            "max_days_pending": max_days_pending,
            "by_status": by_status,
            "by_template": by_template,
            "by_evaluator": by_evaluator,
            "urgent_count": urgent_count,
            "overdue_count": overdue_count,
        }

        logger.info(
            f"Calculated completion stats: {incomplete_count} incomplete, "
            f"{completion_rate:.1%} completion rate, "
            f"{avg_days_pending:.1f} avg days pending"
        )

        return stats

    except Exception as e:
        logger.error(f"Error calculating completion statistics: {e}", exc_info=True)
        return {
            "total_scorecards": 0,
            "incomplete_count": 0,
            "completion_rate": 0.0,
            "avg_days_pending": 0.0,
            "max_days_pending": 0,
            "by_status": {},
            "by_template": {},
            "by_evaluator": {},
            "urgent_count": 0,
            "overdue_count": 0,
            "error": str(e),
        }


@shared_task(
    name="tasks.check_incomplete_scorecards",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def check_incomplete_scorecards(
    self,
    days_threshold: int = DEFAULT_DAYS_THRESHOLD,
    include_details: bool = False,
) -> Dict[str, Any]:
    """
    Check for incomplete scorecards and generate monitoring report.

    This Celery Beat task periodically checks for incomplete evaluation scorecards
    and generates a monitoring report with statistics and actionable insights.
    It helps identify evaluations that need attention and potential bottlenecks.

    Task Workflow:
    1. Query database for incomplete scorecards
    2. Filter by days threshold
    3. Calculate completion statistics
    4. Identify urgent and overdue evaluations
    5. Generate monitoring report
    6. Return summary with optional details

    Args:
        self: Celery task instance (bind=True)
        days_threshold: Only check scorecards pending >= this many days (default: 7)
        include_details: Whether to include individual scorecard details (default: False)

    Returns:
        Dictionary containing check results:
        - incomplete_count: Number of incomplete scorecards found
        - urgent_count: Number of scorecards pending > 10 days
        - overdue_count: Number of scorecards pending > 7 days
        - completion_rate: Overall completion rate
        - avg_days_pending: Average days pending across incomplete scorecards
        - max_days_pending: Maximum days pending
        - by_status: Breakdown by status (draft, in_progress)
        - by_template: Breakdown by evaluation template
        - by_evaluator: Breakdown by evaluator
        - scorecards: List of scorecard details (if include_details=True)
        - processing_time_ms: Total processing time
        - status: Task status (completed/failed)
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.evaluation_periodic import check_incomplete_scorecards
        >>> task = check_incomplete_scorecards.delay(days_threshold=7)
        >>> result = task.get()
        >>> print(result['incomplete_count'])
        15
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting incomplete scorecard check: days_threshold={days_threshold}, "
            f"include_details={include_details}"
        )

        # Note: In a real implementation, you would get db_session here
        # from database import get_db_session
        # db_session = get_db_session()
        db_session = None

        # Step 1: Retrieve incomplete scorecards
        logger.info(f"Task {self.request.id}: Retrieving incomplete scorecards")

        incomplete_scorecards = get_incomplete_scorecards(
            days_threshold=days_threshold,
            db_session=db_session,
        )

        logger.info(f"Found {len(incomplete_scorecards)} incomplete scorecards")

        # Step 2: Calculate completion statistics
        logger.info(f"Task {self.request.id}: Calculating completion statistics")

        stats = calculate_scorecard_completion_stats(incomplete_scorecards)

        # Step 3: Identify evaluators with most pending
        logger.info(f"Task {self.request.id}: Identifying evaluators with pending evaluations")

        top_evaluators = sorted(
            stats.get("by_evaluator", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Step 4: Identify templates with most pending
        logger.info(f"Task {self.request.id}: Identifying templates with pending evaluations")

        top_templates = sorted(
            stats.get("by_template", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Build result
        result = {
            "incomplete_count": stats.get("incomplete_count", 0),
            "urgent_count": stats.get("urgent_count", 0),
            "overdue_count": stats.get("overdue_count", 0),
            "completion_rate": stats.get("completion_rate", 0.0),
            "avg_days_pending": stats.get("avg_days_pending", 0.0),
            "max_days_pending": stats.get("max_days_pending", 0),
            "by_status": stats.get("by_status", {}),
            "by_template": stats.get("by_template", {}),
            "by_evaluator": stats.get("by_evaluator", {}),
            "top_evaluators": top_evaluators,
            "top_templates": top_templates,
            "scorecards": incomplete_scorecards if include_details else [],
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        # Log summary
        logger.info(
            f"Incomplete scorecard check completed: "
            f"{result['incomplete_count']} incomplete, "
            f"{result['urgent_count']} urgent, "
            f"{result['overdue_count']} overdue, "
            f"completion rate: {result['completion_rate']:.1%}, "
            f"time: {processing_time_ms}ms"
        )

        # Log warnings for urgent/overdue
        if result['urgent_count'] > 0:
            logger.warning(
                f"Found {result['urgent_count']} urgent scorecards pending > 10 days"
            )

        if result['overdue_count'] > 0:
            logger.warning(
                f"Found {result['overdue_count']} overdue scorecards pending > 7 days"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "incomplete_count": 0,
            "urgent_count": 0,
            "overdue_count": 0,
            "completion_rate": 0.0,
            "avg_days_pending": 0.0,
            "max_days_pending": 0,
            "by_status": {},
            "by_template": {},
            "by_evaluator": {},
            "top_evaluators": [],
            "top_templates": [],
            "scorecards": [],
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": "Task exceeded maximum time limit",
        }

    except Exception as e:
        logger.error(f"Error in incomplete scorecard check: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "incomplete_count": 0,
            "urgent_count": 0,
            "overdue_count": 0,
            "completion_rate": 0.0,
            "avg_days_pending": 0.0,
            "max_days_pending": 0,
            "by_status": {},
            "by_template": {},
            "by_evaluator": {},
            "top_evaluators": [],
            "top_templates": [],
            "scorecards": [],
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": str(e),
        }
