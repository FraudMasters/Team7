"""
JobBoardIntegration model for storing job board API configurations
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class JobBoardIntegration(Base, UUIDMixin, TimestampMixin):
    """
    JobBoardIntegration model for storing job board API configurations

    Attributes:
        id: UUID primary key
        name: Job board name (e.g., LinkedIn, Indeed, etc.)
        api_endpoint: API endpoint URL for the job board
        api_key: API key for authentication
        enabled: Whether the integration is active
        config: Additional configuration as JSON (e.g., filters, sync settings)
        last_sync_at: Timestamp of last successful sync
        created_at: Timestamp when integration was created (inherited)
        updated_at: Timestamp when integration was last updated (inherited)
    """

    __tablename__ = "job_board_integrations"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    api_endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=dict
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return f"<JobBoardIntegration(id={self.id}, name={self.name}, enabled={self.enabled})>"
