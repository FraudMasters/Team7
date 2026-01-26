"""
Celery tasks module for async processing.

This module provides Celery task definitions for long-running operations
like resume analysis, job matching, batch processing, ML learning tasks,
report generation, email notifications, and search alerts.
"""
from .analysis_task import analyze_resume_async, batch_analyze_resumes
from .learning_tasks import (
    aggregate_feedback_and_generate_synonyms,
    review_and_activate_synonyms,
    periodic_feedback_aggregation,
    retrain_skill_matching_model,
)
from .report_generation import (
    get_report_data,
    format_report_as_pdf,
    format_report_as_csv,
    send_report_via_email,
    generate_scheduled_reports,
    process_all_pending_reports,
)
from .email_task import (
    send_feedback_notification,
    send_batch_notification,
)
from .search_alerts_task import (
    check_resume_against_saved_searches,
    send_search_alert_notification,
    process_pending_alerts,
)

__all__ = [
    "analyze_resume_async",
    "batch_analyze_resumes",
    "aggregate_feedback_and_generate_synonyms",
    "review_and_activate_synonyms",
    "periodic_feedback_aggregation",
    "retrain_skill_matching_model",
    "get_report_data",
    "format_report_as_pdf",
    "format_report_as_csv",
    "send_report_via_email",
    "generate_scheduled_reports",
    "process_all_pending_reports",
    "send_feedback_notification",
    "send_batch_notification",
    "check_resume_against_saved_searches",
    "send_search_alert_notification",
    "process_pending_alerts",
]
