"""
ClientUsage model for tracking per-client resource usage
"""
import enum
from uuid import UUID
from typing import Optional
from datetime import datetime

from sqlalchemy import ForeignKey, JSON, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ResourceType(str, enum.Enum):
    """Types of resources that can be tracked for billing"""

    RESUME_UPLOAD = "resume_upload"
    JOB_POSTING = "job_posting"
    CANDIDATE_MATCH = "candidate_match"
    API_CALL = "api_call"
    STORAGE_GB = "storage_gb"
    USER_SEAT = "user_seat"
    EMAIL_SENT = "email_sent"
    SMS_SENT = "sms_sent"
    REPORT_GENERATED = "report_generated"


class ClientUsage(Base, UUIDMixin, TimestampMixin):
    """
    ClientUsage model for tracking per-client resource usage

    This model enables unified billing by recording resource consumption
    for each client tenant, allowing agencies to track usage across all
    clients and generate accurate billing reports.

    Attributes:
        id: UUID primary key
        client_tenant_id: Foreign key to ClientTenant being tracked
        resource_type: Type of resource consumed (resume_upload, job_posting, etc.)
        usage_count: Number of units consumed in this period
        period_start: Start of the billing/tracking period
        period_end: End of the billing/tracking period
        metadata: JSON object with usage-specific data (file sizes, durations, etc.)
        cost_cents: Optional cost in cents for this usage
        notes: Optional human-readable notes about this usage record
        created_at: Timestamp when usage was recorded (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "client_usage"

    client_tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("client_tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_type: Mapped[ResourceType] = mapped_column(String(50), nullable=False, index=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cost_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    def __repr__(self) -> str:
        return f"<ClientUsage(id={self.id}, client_tenant_id={self.client_tenant_id}, resource_type={self.resource_type}, usage_count={self.usage_count})>"
