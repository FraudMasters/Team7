"""
DashboardConfiguration model for user-customizable analytics dashboards
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class DashboardConfiguration(Base, UUIDMixin, TimestampMixin):
    """
    DashboardConfiguration model for storing user-customizable dashboard layouts

    This model enables recruiters to customize their analytics dashboards by saving
    preferred widgets, layouts, and filters. Each recruiter can have multiple dashboard
    configurations with one marked as default.

    Attributes:
        id: UUID primary key
        recruiter_id: Foreign key to Recruiter who owns this dashboard
        name: Human-readable name for this dashboard configuration
        config: JSON object containing widgets, layout, and filter settings
        is_default: Whether this is the default dashboard for the recruiter
        created_at: Timestamp when configuration was created (inherited)
        updated_at: Timestamp when configuration was last updated (inherited)
    """

    __tablename__ = "dashboard_configurations"

    recruiter_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("recruiters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Recruiter who owns this dashboard configuration"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable name for this dashboard"
    )
    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Dashboard configuration including widgets, layout, and filters"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this is the default dashboard for the recruiter"
    )

    def __repr__(self) -> str:
        return f"<DashboardConfiguration(id={self.id}, name='{self.name}', recruiter_id={self.recruiter_id}, is_default={self.is_default})>"
