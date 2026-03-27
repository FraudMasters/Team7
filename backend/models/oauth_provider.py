"""
OAuthProvider model for OAuth 2.0 provider configurations
"""
from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class OAuthProvider(Base, UUIDMixin, TimestampMixin):
    """
    OAuthProvider model for OAuth 2.0 provider configurations

    This model enables organizations to configure OAuth 2.0 Single Sign-On (SSO)
    integration with identity providers such as Google, GitHub, Microsoft, and others.
    Each organization can configure multiple OAuth providers, allowing users to
    authenticate using their social or corporate credentials.

    Attributes:
        id: UUID primary key
        organization_id: Organization ID (null for system-wide config)
        provider_name: Human-readable name of the OAuth provider (e.g., "Google OAuth")
        provider_type: Provider type: google, github, microsoft, okta, or generic_oauth
        client_id: OAuth client ID from the identity provider
        client_secret: OAuth client secret (encrypted at rest)
        authorization_url: OAuth authorization endpoint URL
        token_url: OAuth token endpoint URL
        userinfo_url: OAuth userinfo endpoint URL to fetch user profile
        scopes: Space-separated list of OAuth scopes to request
        redirect_uri: OAuth redirect URI configured in the provider
        attribute_mapping_email: User profile attribute name for email
        attribute_mapping_name: User profile attribute name for display name
        attribute_mapping_first_name: User profile attribute name for first name
        attribute_mapping_last_name: User profile attribute name for last name
        attribute_mapping_picture: User profile attribute name for profile picture URL
        is_enabled: Whether this OAuth configuration is active
        is_default: Whether this is the default OAuth provider for the organization
        created_at: Timestamp when config was created (inherited from TimestampMixin)
        updated_at: Timestamp when config was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "oauth_providers"

    # Organization scope
    organization_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Organization ID (null for system-wide config)"
    )

    # Provider identification
    provider_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable name of the OAuth provider (e.g., 'Google OAuth')"
    )
    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Provider type: google, github, microsoft, okta, or generic_oauth"
    )

    # OAuth credentials
    client_id: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="OAuth client ID from the identity provider"
    )
    client_secret: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="OAuth client secret (encrypted at rest)"
    )

    # OAuth endpoints
    authorization_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="OAuth authorization endpoint URL"
    )
    token_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="OAuth token endpoint URL"
    )
    userinfo_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="OAuth userinfo endpoint URL to fetch user profile"
    )

    # OAuth configuration
    scopes: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="openid profile email",
        comment="Space-separated list of OAuth scopes to request"
    )
    redirect_uri: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="OAuth redirect URI configured in the provider"
    )

    # Attribute mappings for user provisioning
    attribute_mapping_email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="email",
        comment="User profile attribute name for email"
    )
    attribute_mapping_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="name",
        comment="User profile attribute name for display name"
    )
    attribute_mapping_first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="given_name",
        comment="User profile attribute name for first name"
    )
    attribute_mapping_last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="family_name",
        comment="User profile attribute name for last name"
    )
    attribute_mapping_picture: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="picture",
        comment="User profile attribute name for profile picture URL"
    )

    # Configuration flags
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this OAuth configuration is active"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this is the default OAuth provider for the organization"
    )

    def __repr__(self) -> str:
        return f"<OAuthProvider(id={self.id}, provider={self.provider_name}, type={self.provider_type}, enabled={self.is_enabled})>"
