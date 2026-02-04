"""
BrandingSettings model for storing organization customization and branding preferences
"""
from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class BrandingSettings(Base, UUIDMixin, TimestampMixin):
    """
    BrandingSettings model for storing organization customization and branding preferences

    This model enables organizations to customize their hiring workflow experience
    with branded colors, fonts, logos, and custom styles. Each organization can have
    one active branding settings record.

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns these branding settings
        primary_color: Primary brand color in hex format (e.g., "#3B82F6")
        secondary_color: Secondary brand color in hex format (e.g., "#10B981")
        accent_color: Accent color for highlights and CTAs (e.g., "#F59E0B")
        background_color: Optional background color (e.g., "#FFFFFF")
        text_color: Optional text color (e.g., "#1F2937")
        font_family: Optional font family name (e.g., "Inter", "Roboto")
        custom_css: Optional custom CSS for advanced styling
        logo_url: Optional URL to override organization logo
        favicon_url: Optional URL to custom favicon
        is_active: Whether these branding settings are currently active
        created_by: User ID who created these branding settings
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "branding_settings"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")
    secondary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#10B981")
    accent_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#F59E0B")
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    text_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    font_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    custom_css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BrandingSettings(id={self.id}, org={self.organization_id}, "
            f"primary={self.primary_color}, secondary={self.secondary_color}, "
            f"accent={self.accent_color})>"
        )
