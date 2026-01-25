"""
Report and ScheduledReport models for custom report configurations
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class Report(Base, UUIDMixin, TimestampMixin):
    """
    Report model for storing custom report configurations

    Attributes:
        id: UUID primary key
        organization_id: Foreign key or reference to organization
        name: Human-readable name for the report
        description: Optional description of the report's purpose
        report_type: Type of report (hiring_pipeline, skill_demand, source_effectiveness, diversity_metrics, custom)
        configuration: JSON object containing filters, dimensions, metrics, and visualization settings
        created_by: User ID who created this report configuration
        is_active: Whether this report configuration is currently active
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "reports"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    report_type: Mapped[str] = mapped_column(nullable=False, index=True)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, org={self.organization_id}, name={self.name}, type={self.report_type})>"


class ScheduledReport(Base, UUIDMixin, TimestampMixin):
    """
    ScheduledReport model for scheduling automated report generation and delivery

    Attributes:
        id: UUID primary key
        organization_id: Foreign key or reference to organization
        report_id: Reference to the Report configuration to use
        name: Human-readable name for the scheduled report
        schedule_config: JSON object containing frequency, timezone, and schedule settings
        delivery_config: JSON object containing delivery method (email, Slack, etc.) and settings
        recipients: JSON array of user IDs or email addresses to receive the report
        created_by: User ID who created this scheduled report
        is_active: Whether this scheduled report is currently active
        next_run_at: Timestamp for when the next report generation should occur
        last_run_at: Timestamp for when the report was last generated
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "scheduled_reports"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    schedule_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    delivery_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    recipients: Mapped[list] = mapped_column(JSON, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<ScheduledReport(id={self.id}, org={self.organization_id}, name={self.name}, report_id={self.report_id})>"
