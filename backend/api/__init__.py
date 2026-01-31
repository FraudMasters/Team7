"""
API router module for resume analysis endpoints.

This module provides FastAPI routers for various API endpoints including
resume upload, analysis, and job matching.
"""
from . import ats_simulation

__all__ = ["ats_simulation"]
