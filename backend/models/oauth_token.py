"""
OAuthToken model for storing OAuth 2.0 tokens
"""
from typing import Optional
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class OAuthToken(Base, UUIDMixin, TimestampMixin):
    """
    OAuthToken model for storing OAuth 2.0 tokens

    This model stores OAuth 2.0 access and refresh tokens obtained during user
    authentication flows. These tokens enable the application to authenticate
    users via OAuth providers and make API calls on behalf of users.

    Attributes:
        id: UUID primary key
        user_id: User ID who owns this token
        provider_id: OAuth provider ID from oauth_providers table
        provider_type: Provider type (google, github, microsoft, etc.) for quick lookup
        access_token: OAuth access token (encrypted at rest)
        refresh_token: OAuth refresh token for obtaining new access tokens (encrypted at rest)
        token_type: Token type (usually "Bearer")
        expires_at: When the access token expires
        scope: Space-separated list of granted OAuth scopes
        id_token: OpenID Connect ID token if available (encrypted at rest)
        provider_user_id: User ID from the OAuth provider
        provider_email: Email from the OAuth provider
        provider_metadata: Additional metadata from the OAuth provider (user profile data)
        last_used_at: When this token was last used for authentication
        created_at: Timestamp when token was created (inherited from TimestampMixin)
        updated_at: Timestamp when token was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "oauth_tokens"

    # User and provider association
    user_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User ID who owns this token"
    )
    provider_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="OAuth provider ID from oauth_providers table"
    )
    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Provider type (google, github, microsoft, etc.) for quick lookup"
    )

    # OAuth tokens
    access_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="OAuth access token (encrypted at rest)"
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="OAuth refresh token for obtaining new access tokens (encrypted at rest)"
    )
    token_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Bearer",
        comment='Token type (usually "Bearer")'
    )

    # Token metadata
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When the access token expires"
    )
    scope: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Space-separated list of granted OAuth scopes"
    )
    id_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="OpenID Connect ID token if available (encrypted at rest)"
    )

    # Provider user information
    provider_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User ID from the OAuth provider"
    )
    provider_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Email from the OAuth provider"
    )
    provider_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata from the OAuth provider (user profile data)"
    )

    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this token was last used for authentication"
    )

    def __repr__(self) -> str:
        return f"<OAuthToken(id={self.id}, user_id={self.user_id}, provider_type={self.provider_type}, expires_at={self.expires_at})>"
