"""
User model for authentication and authorization
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    User model for authentication and authorization

    This model manages user accounts and authentication credentials.
    It supports user login, account status tracking, and basic profile information.

    Attributes:
        id: UUID primary key
        email: User's email address (unique, used for login)
        password_hash: Hashed password (bcrypt/argon2)
        full_name: User's full name
        is_active: Whether the user account is active
        is_verified: Whether the user's email has been verified
        is_superuser: Whether the user has superuser/admin privileges
        created_at: Timestamp when user was created (inherited from TimestampMixin)
        updated_at: Timestamp when user was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    job_applications: Mapped[list["JobApplication"]] = relationship(
        "JobApplication",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    saved_jobs: Mapped[list["SavedJob"]] = relationship(
        "SavedJob",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    candidate_documents: Mapped[list["CandidateDocument"]] = relationship(
        "CandidateDocument",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"
