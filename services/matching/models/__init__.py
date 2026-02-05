"""
Models package for matching service.
"""
from .base import Base, TimestampMixin, UUIDMixin
from .match_result import MatchResult

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "MatchResult",
]
