"""
API router module for resume analysis endpoints.

This module provides FastAPI routers for various API endpoints including
resume upload, analysis, and job matching.
"""
from . import (
    ats_simulation,
    candidate_activities,
    candidate_notes,
    candidate_tags,
    candidates,
    job_integrations,
    saved_searches,
    search,
    webhooks,
)

__all__ = [
    "ats_simulation",
    "candidate_activities",
    "candidate_notes",
    "candidate_tags",
    "candidates",
    "job_integrations",
    "saved_searches",
    "search",
    "webhooks",
]
