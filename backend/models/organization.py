"""
Organization model for multi-tenant support
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    """
    Organization model for multi-tenant support

    This model enables organizations to have customized hiring workflows,
    branding, email templates, and skill taxonomies. Each organization
    operates independently with their own configuration.

    Attributes:
        id: String primary key (UUID or custom identifier)
        name: Organization name (e.g., "Acme Corporation")
        slug: URL-friendly identifier (e.g., "acme-corp")
        domain: Optional domain for organization (e.g., "example.com")
        logo_url: Optional URL to organization logo
        is_active: Whether organization is active
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"
