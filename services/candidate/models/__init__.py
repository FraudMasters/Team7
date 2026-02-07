"""
Database models for Candidate Service.

Модели базы данных для сервиса управления кандидатами.
"""
from .base import Base, TimestampMixin, UUIDMixin
from .candidate import Candidate, CandidateStatus
from .candidate_note import CandidateNote
from .candidate_tag import CandidateTag
from .candidate_activity import CandidateActivity, CandidateActivityType

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "Candidate",
    "CandidateStatus",
    "CandidateNote",
    "CandidateTag",
    "CandidateActivity",
    "CandidateActivityType",
]
