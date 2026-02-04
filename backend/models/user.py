"""
User model for authentication and authorization
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    User model for authentication and authorization

    This model represents users in the system with authentication credentials,
    profile information, and role-based access control.

    Attributes:
        id: UUID primary key
        email: User's email address (unique, used for authentication)
        name: User's full name
        role: User's role for authorization (e.g., 'admin', 'recruiter', 'hiring_manager')
        is_active: Whether the user account is currently active
        created_at: Timestamp when user was created (inherited from TimestampMixin)
        updated_at: Timestamp when user was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name}, role={self.role})>"
