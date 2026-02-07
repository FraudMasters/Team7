"""
A/B Testing models for experimenting with matching weight configurations

This module provides data models for running A/B tests on different matching
algorithm weight configurations. It supports random user assignment, performance
metric tracking, and statistical analysis to determine optimal weight settings.
"""
import enum
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ABTestStatus(str, enum.Enum):
    """Status of an A/B test in its lifecycle"""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"


class ABTest(Base, UUIDMixin, TimestampMixin):
    """
    ABTest model for managing A/B testing experiments

    This model represents a complete A/B testing experiment for comparing different
    matching weight configurations. It tracks the experiment's status, duration,
    and configuration throughout its lifecycle from draft to completion.

    Attributes:
        id: UUID primary key
        name: Human-readable name for the experiment (e.g., "Q1 2026 Weight Optimization")
        description: Detailed description of the experiment's goals and hypotheses
        status: Current status of the test (draft, running, completed, paused)
        start_date: When the test started actively running
        end_date: When the test was completed or stopped
        organization_id: Organization that owns this experiment
        created_by: User ID who created this experiment
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "ab_tests"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ABTestStatus] = mapped_column(
        Enum(ABTestStatus), default=ABTestStatus.DRAFT, nullable=False, index=True
    )
    start_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ABTest(id={self.id}, name={self.name}, "
            f"status={self.status}, org={self.organization_id})>"
        )


class ABTestAssignment(Base, UUIDMixin, TimestampMixin):
    """
    ABTestAssignment model for tracking user-to-profile assignments

    This model represents a user's assignment to a specific weight profile
    within an A/B test. Each user can be assigned to only one profile per test.
    The assignment is deterministic - the same user will always receive the
    same profile assignment for a given test.

    Attributes:
        id: UUID primary key
        test_id: Foreign key to the ABTest this assignment belongs to
        user_id: ID of the user being assigned
        profile_id: Foreign key to the MatchingWeightsProfile assigned to this user
        assigned_at: Timestamp when the assignment was made
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "ab_test_assignments"

    test_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ab_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(nullable=False, index=True)
    profile_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("matching_weights_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<ABTestAssignment(id={self.id}, test_id={self.test_id}, "
            f"user_id={self.user_id}, profile_id={self.profile_id})>"
        )
