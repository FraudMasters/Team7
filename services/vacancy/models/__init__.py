"""Models package for Vacancy Service."""
from .base import Base, TimestampMixin, UUIDMixin
from .vacancy import Vacancy

__all__ = ["Base", "TimestampMixin", "UUIDMixin", "Vacancy"]
