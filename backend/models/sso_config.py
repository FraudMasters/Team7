"""
SSOConfig model for SAML SSO provider configurations
"""
from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SSOConfig(Base, UUIDMixin, TimestampMixin):
    """
    SSOConfig model for SAML SSO provider configurations

    This model enables organizations to configure SAML 2.0 Single Sign-On (SSO)
    integration with identity providers such as Okta, Azure AD, and Google Workspace.
    Each organization can configure multiple SSO providers, allowing users to
    authenticate using their corporate credentials.

    Attributes:
        id: UUID primary key
        organization_id: Organization ID (null for system-wide config)
        provider_name: Human-readable name of the SSO provider (e.g., "Company Okta")
        provider_type: Provider type: okta, azure_ad, google_workspace, or generic_saml
        entity_id: SAML Entity ID (IdP identifier) from the identity provider
        sso_url: SAML SSO URL where authentication requests are sent
        sls_url: SAML Single Logout Service URL for logout requests
        x509_certificate: X.509 certificate from IdP for verifying SAML responses
        metadata_url: Optional URL to fetch SAML metadata automatically
        attribute_mapping_email: SAML attribute name for user email
        attribute_mapping_name: SAML attribute name for user display name
        attribute_mapping_first_name: SAML attribute name for user first name
        attribute_mapping_last_name: SAML attribute name for user last name
        attribute_mapping_department: SAML attribute name for user department
        is_enabled: Whether this SSO configuration is active
        is_default: Whether this is the default SSO provider for the organization
        created_at: Timestamp when config was created (inherited from TimestampMixin)
        updated_at: Timestamp when config was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "sso_configs"

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
        comment="Human-readable name of the SSO provider (e.g., 'Company Okta')"
    )
    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Provider type: okta, azure_ad, google_workspace, or generic_saml"
    )

    # SAML configuration
    entity_id: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="SAML Entity ID (IdP identifier) from the identity provider"
    )
    sso_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="SAML SSO URL where authentication requests are sent"
    )
    sls_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="SAML Single Logout Service URL for logout requests"
    )
    x509_certificate: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="X.509 certificate from IdP for verifying SAML responses"
    )
    metadata_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional URL to fetch SAML metadata automatically"
    )

    # Attribute mappings for user provisioning
    attribute_mapping_email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="email",
        comment="SAML attribute name for user email"
    )
    attribute_mapping_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="displayName",
        comment="SAML attribute name for user display name"
    )
    attribute_mapping_first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="firstName",
        comment="SAML attribute name for user first name"
    )
    attribute_mapping_last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="lastName",
        comment="SAML attribute name for user last name"
    )
    attribute_mapping_department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="department",
        comment="SAML attribute name for user department"
    )

    # Configuration flags
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this SSO configuration is active"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this is the default SSO provider for the organization"
    )

    def __repr__(self) -> str:
        return f"<SSOConfig(id={self.id}, provider={self.provider_name}, type={self.provider_type}, enabled={self.is_enabled})>"
