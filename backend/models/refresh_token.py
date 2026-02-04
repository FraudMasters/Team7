"""
RefreshToken model for JWT refresh token storage
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    """
    RefreshToken model for JWT refresh token storage

    This model manages refresh tokens for JWT-based authentication.
    Refresh tokens are used to obtain new access tokens without requiring
    the user to re-authenticate. Each token is associated with a user
    and has an expiration date.

    Attributes:
        id: UUID primary key
        user_id: Foreign key to User (token owner)
        token: The refresh token string (unique, hashed)
        expires_at: Token expiration timestamp
        revoked_at: When the token was revoked (null if active)
        is_revoked: Whether the token has been revoked
        created_at: Timestamp when token was created (inherited)
        updated_at: Timestamp when token was last updated (inherited)
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_refresh_tokens_user_expires", "user_id", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"
