"""
Celery tasks module for async processing.

This module provides Celery task definitions for long-running operations
like resume analysis, job matching, and batch processing.
"""
from .analysis_task import analyze_resume_async

__all__ = ["analyze_resume_async"]
