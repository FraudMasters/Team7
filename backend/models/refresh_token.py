"""
RefreshToken model for JWT refresh token management
"""
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    """
    RefreshToken model for JWT refresh token management

    This model stores refresh tokens used to obtain new access tokens without
    requiring re-authentication. Refresh tokens are more long-lived than access
    tokens and can be revoked independently.

    Attributes:
        id: UUID primary key
        user_id: Foreign key reference to the user who owns this token
        token: The refresh token string (hashed, unique)
        expires_at: Timestamp when this token expires
        revoked_at: Optional timestamp when token was revoked (NULL if active)
        created_at: Timestamp when token was created (inherited from TimestampMixin)
        updated_at: Timestamp when token was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_refresh_tokens_user_expires", "user_id", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
