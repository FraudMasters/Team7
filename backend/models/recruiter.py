"""
Recruiter model for tracking recruiter attribution and performance
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class Recruiter(Base, UUIDMixin, TimestampMixin):
    """
    Recruiter model for tracking recruiter attribution and performance

    This model enables recruiter performance analytics by tracking individual
    recruiters and their associated metrics such as time-to-hire, placement rates,
    and activity levels.

    Attributes:
        id: UUID primary key
        name: Recruiter's full name
        email: Recruiter's contact email (unique)
        department: Optional department or team name
        is_active: Whether the recruiter is currently active
        created_at: Timestamp when recruiter was created (inherited from TimestampMixin)
        updated_at: Timestamp when recruiter was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "recruiters"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Recruiter(id={self.id}, name={self.name}, email={self.email})>"
