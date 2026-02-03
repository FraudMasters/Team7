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
    saved_searches,
    search,
    websocket,
)

__all__ = [
    "ats_simulation",
    "candidate_activities",
    "candidate_notes",
    "candidate_tags",
    "candidates",
    "saved_searches",
    "search",
    "websocket",
]
