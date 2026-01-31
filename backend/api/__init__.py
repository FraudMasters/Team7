"""
API router module for resume analysis endpoints.

This module provides FastAPI routers for various API endpoints including
resume upload, analysis, and job matching.
"""
from . import ats_simulation, candidate_notes, candidate_tags

__all__ = ["ats_simulation", "candidate_notes", "candidate_tags"]
