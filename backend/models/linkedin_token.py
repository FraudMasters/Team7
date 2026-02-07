"""
LinkedIn OAuth Token model for secure token storage.

This module provides the LinkedInToken model for storing encrypted
LinkedIn OAuth access tokens and refresh tokens.

Features:
- Encrypted token storage (Fernet encryption)
- Token expiration tracking
- LinkedIn member ID association
- Recruiter/user linkage
- Automatic timestamp management
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

logger = logging.getLogger(__name__)


class LinkedInToken(Base, UUIDMixin, TimestampMixin):
    """
    LinkedIn OAuth token storage model.

    This model securely stores LinkedIn OAuth access tokens and refresh tokens
    for recruiters/users. Tokens are encrypted at rest using Fernet symmetric
    encryption.

    Attributes:
        id: UUID primary key
        recruiter_id: Foreign key to recruiters table (user who owns the token)
        access_token_encrypted: Encrypted access token (Fernet-encrypted)
        refresh_token_encrypted: Encrypted refresh token (optional, Fernet-encrypted)
        token_expires_at: Token expiration timestamp (optional)
        linkedin_member_id: LinkedIn member ID (optional, for profile linking)
        created_at: Timestamp when token was created
        updated_at: Timestamp when token was last updated

    Relationships:
        recruiter: Recruiter who owns this token

    Security:
        - Access tokens are encrypted using Fernet (AES-128-CBC with HMAC)
        - Encryption key is stored in LINKEDIN_TOKEN_ENCRYPTION_KEY environment variable
        - Never log plaintext tokens
        - Tokens should be refreshed before expiration

    Example:
        >>> from utils.token_encryption import encrypt_token
        >>> from models.linkedin_token import LinkedInToken
        >>>
        >>> # Create a new token record
        >>> token = LinkedInToken(
        ...     recruiter_id=recruiter_id,
        ...     access_token_encrypted=encrypt_token(access_token),
        ...     refresh_token_encrypted=encrypt_token(refresh_token),
        ...     token_expires_at=datetime.now() + timedelta(hours=2),
        ...     linkedin_member_id="abc123"
        ... )
        >>> session.add(token)
        >>> session.commit()
    """

    __tablename__ = "linkedin_tokens"

    # Foreign key to recruiters table
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the recruiter who owns this token",
    )

    # Encrypted access token (required)
    access_token_encrypted: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
        comment="Encrypted LinkedIn OAuth access token (Fernet-encrypted)",
    )

    # Encrypted refresh token (optional)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(
        Text(),
        nullable=True,
        comment="Encrypted LinkedIn OAuth refresh token (Fernet-encrypted)",
    )

    # Token expiration timestamp (optional)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Token expiration timestamp (if provided by LinkedIn)",
    )

    # LinkedIn member ID (optional, for linking to LinkedIn profiles)
    linkedin_member_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="LinkedIn member ID (for profile linking)",
    )

    # Relationship to recruiter
    recruiter = relationship("Recruiter", backref="linkedin_tokens")

    # Unique constraint: one active token per recruiter
    __table_args__ = (
        UniqueConstraint("recruiter_id", name="uq_linkedin_tokens_recruiter_id"),
    )

    # Relationship to recruiter
    recruiter = relationship("Recruiter", backref="linkedin_tokens")

    def __repr__(self) -> str:
        """String representation of LinkedInToken (without exposing sensitive data)."""
        return (
            f"<LinkedInToken("
            f"id={self.id}, "
            f"recruiter_id={self.recruiter_id}, "
            f"expires_at={self.token_expires_at}, "
            f"linkedin_member_id={self.linkedin_member_id}"
            f")>"
        )

    def is_expired(self) -> bool:
        """
        Check if the access token is expired.

        Returns:
            True if token is expired or expiration is unknown, False otherwise

        Example:
            >>> token = session.get(LinkedInToken, token_id)
            >>> if token.is_expired():
            ...     print("Token expired, refresh needed")
        """
        if self.token_expires_at is None:
            # If we don't know the expiration, assume it's expired
            return True

        # Add 5-minute buffer to refresh tokens before actual expiration
        return datetime.now(self.token_expires_at.tzinfo) >= (
            self.token_expires_at - timedelta(minutes=5)
        )

    def expires_soon(self, buffer_minutes: int = 15) -> bool:
        """
        Check if the access token will expire soon.

        Args:
            buffer_minutes: Minutes before expiration to consider as "soon" (default: 15)

        Returns:
            True if token expires within buffer minutes, False otherwise

        Example:
            >>> if token.expires_soon(buffer_minutes=30):
            ...     print("Token will expire soon, consider refreshing")
        """
        if self.token_expires_at is None:
            return True

        expires_in = self.token_expires_at - datetime.now(
            self.token_expires_at.tzinfo
        )
        return expires_in <= timedelta(minutes=buffer_minutes)

    def time_until_expiry(self) -> Optional[timedelta]:
        """
        Get time remaining until token expiration.

        Returns:
            Timedelta until expiration, or None if expiration is unknown

        Example:
            >>> time_left = token.time_until_expiry()
            >>> if time_left:
            ...     print(f"Token expires in {time_left}")
        """
        if self.token_expires_at is None:
            return None

        delta = self.token_expires_at - datetime.now(self.token_expires_at.tzinfo)
        return delta if delta.total_seconds() > 0 else timedelta(0)
