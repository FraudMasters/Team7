"""
ABTest model for A/B testing framework
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ABTestStatus(str, enum.Enum):
    """Status of an A/B test"""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"


class ABTest(Base, UUIDMixin, TimestampMixin):
    """
    ABTest model for managing A/B testing experiments on matching weight configurations

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this A/B test
        name: Human-readable name for the experiment (e.g., "Technical Roles Q1 2026")
        description: Optional description of the experiment goals and hypothesis
        variant_a_profile_id: Foreign key to MatchingWeightsProfile for variant A
        variant_b_profile_id: Foreign key to MatchingWeightsProfile for variant B
        status: Current status of the test (draft/running/completed/paused)
        start_date: When the test started running
        end_date: When the test ended or was stopped
        created_by: User ID who created this test
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "ab_tests"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variant_a_profile_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("matching_weights_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_b_profile_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("matching_weights_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ABTestStatus] = mapped_column(
        Enum(ABTestStatus), default=ABTestStatus.DRAFT, nullable=False, index=True
    )
    start_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ABTest(id={self.id}, org={self.organization_id}, "
            f"name={self.name}, status={self.status})>"
        )
