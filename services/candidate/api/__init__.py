"""
API package for Candidate Service.

Пакет API для сервиса управления кандидатами.

Этот пакет содержит все эндпоинты API для сервиса управления кандидатами.

This package contains all API endpoints for the candidate management service.
"""
from .candidates import router as candidates_router
from .candidate_notes import router as candidate_notes_router
from .candidate_tags import router as candidate_tags_router
from .candidate_activities import router as candidate_activities_router

__all__ = [
    "candidates_router",
    "candidate_notes_router",
    "candidate_tags_router",
    "candidate_activities_router",
]
