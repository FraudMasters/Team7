"""
Agency model for multi-tenant recruitment agency support
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Agency(Base, TimestampMixin):
    """
    Agency model for recruitment agencies managing multiple client organizations

    This model represents recruitment agencies that manage multiple client tenants.
    Each agency can have multiple client organizations, track usage across clients,
    and provide cross-client analytics and billing.

    Attributes:
        id: String primary key (UUID or custom identifier)
        name: Agency name (e.g., "TechRecruit Partners")
        slug: URL-friendly identifier (e.g., "techrecruit-partners")
        domain: Optional domain for agency (e.g., "techrecruit.com")
        logo_url: Optional URL to agency logo
        contact_email: Optional contact email for agency
        contact_phone: Optional contact phone for agency
        is_active: Whether agency is active
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "agencies"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    def __repr__(self) -> str:
        return f"<Agency(id={self.id}, name={self.name}, slug={self.slug})>"
