"""
TokenBlacklist model for tracking revoked/invalidated JWT tokens
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, String, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class TokenBlacklist(Base, UUIDMixin, TimestampMixin):
    """
    TokenBlacklist model for tracking revoked/invalidated JWT tokens

    This model stores tokens that have been explicitly revoked or invalidated
    before their natural expiration. It prevents reuse of old tokens during
    token rotation and enables immediate revocation for security purposes.

    Attributes:
        id: UUID primary key
        token: The JWT token string (unique, indexed for fast lookups)
        token_type: Type of token ("access" or "refresh")
        user_id: Optional user ID associated with the token
        expires_at: Original expiration time of the token
        revoked_at: When the token was blacklisted
        reason: Optional reason for blacklisting (e.g., "rotation", "logout", "security")
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "token_blacklist"

    token: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    token_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    __table_args__ = (
        Index("ix_token_blacklist_token_expires", "token", "expires_at"),
        Index("ix_token_blacklist_user_revoked", "user_id", "revoked_at"),
    )

    def __repr__(self) -> str:
        return f"<TokenBlacklist(id={self.id}, token_type={self.token_type}, user_id={self.user_id}, reason={self.reason})>"
