"""
Integration model for storing HRIS/ATS platform integration configurations
"""
import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class IntegrationPlatform(str, enum.Enum):
    """Supported HRIS/ATS platforms"""

    # ATS platforms
    WORKDAY = "WORKDAY"
    GREENHOUSE = "GREENHOUSE"
    LEVER = "LEVER"

    # HRIS platforms
    BAMBOOHR = "BAMBOOHR"
    ASHBY = "ASHBY"


class IntegrationStatus(str, enum.Enum):
    """Status of integration configuration"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    PENDING = "PENDING"


class Integration(Base, UUIDMixin, TimestampMixin):
    """
    Integration model for storing external HRIS/ATS platform connections

    Attributes:
        id: UUID primary key
        name: Human-readable name for this integration
        platform: Platform type (WORKDAY, GREENHOUSE, LEVER, BAMBOOHR, ASHBY)
        status: Integration status (ACTIVE, INACTIVE, ERROR, PENDING)
        credentials: Encrypted credentials for API access (JSON)
        organization_config: Platform-specific organization settings (JSON)
        webhook_url: URL for receiving webhooks from this platform
        sync_enabled: Whether automatic sync is enabled
        sync_interval_minutes: Interval for automatic sync (in minutes)
        last_sync_at: Timestamp of last successful sync
        last_sync_status: Status of the last sync operation
        error_message: Error details if last sync failed
        created_at: Timestamp when integration was created (inherited)
        updated_at: Timestamp when integration was last updated (inherited)
    """

    __tablename__ = "integrations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[IntegrationPlatform] = mapped_column(
        Enum(IntegrationPlatform), nullable=False, index=True
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus), default=IntegrationStatus.PENDING, nullable=False, index=True
    )
    credentials: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    organization_config: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None
    )
    webhook_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sync_interval_minutes: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=None
    )
    last_sync_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, name={self.name}, platform={self.platform.value}, status={self.status.value})>"
