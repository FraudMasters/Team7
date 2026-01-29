"""
Celery tasks module for async processing.

This module provides Celery task definitions for long-running operations
like resume analysis, job matching, batch processing, ML learning tasks,
and report generation.
"""
from .analysis_task import analyze_resume_async, batch_analyze_resumes
from .learning_tasks import (
    aggregate_feedback_and_generate_synonyms,
    review_and_activate_synonyms,
    periodic_feedback_aggregation,
    retrain_skill_matching_model,
)
from .report_generation import (
    generate_scheduled_reports,
    process_all_pending_reports,
)

__all__ = [
    "analyze_resume_async",
    "batch_analyze_resumes",
    "aggregate_feedback_and_generate_synonyms",
    "review_and_activate_synonyms",
    "periodic_feedback_aggregation",
    "retrain_skill_matching_model",
    "generate_scheduled_reports",
    "process_all_pending_reports",
]
