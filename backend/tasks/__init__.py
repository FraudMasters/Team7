"""
Celery tasks module for async processing.

This module provides Celery task definitions for long-running operations
like resume analysis, job matching, batch processing, and ML learning tasks.
"""
from .analysis_task import analyze_resume_async
from .learning_tasks import (
    aggregate_feedback_and_generate_synonyms,
    review_and_activate_synonyms,
    periodic_feedback_aggregation,
    retrain_skill_matching_model,
)

__all__ = [
    "analyze_resume_async",
    "aggregate_feedback_and_generate_synonyms",
    "review_and_activate_synonyms",
    "periodic_feedback_aggregation",
    "retrain_skill_matching_model",
]
