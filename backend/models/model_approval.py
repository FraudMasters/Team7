"""
Model Approval Request models for managing model deployment workflows

This module provides data models for managing approval workflows when deploying
ML models. It supports a multi-stage approval process with status tracking,
reviewer assignments, and comments for governance and audit purposes.
"""
import enum
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ApprovalStatus(str, enum.Enum):
    """Status of a model approval request in its lifecycle"""

    PENDING = "pending"  # Awaiting review
    APPROVED = "approved"  # Approved for deployment
    REJECTED = "rejected"  # Rejected by reviewer
    DEPLOYED = "deployed"  # Successfully deployed to production
    CANCELLED = "cancelled"  # Cancelled by requester


class ModelApprovalRequest(Base, UUIDMixin, TimestampMixin):
    """
    ModelApprovalRequest model for managing model deployment approval workflows

    This model represents a request to deploy a specific ML model version.
    It tracks the approval status, reviewer information, and provides
    an audit trail for model deployments.

    Attributes:
        id: UUID primary key
        model_version_id: Foreign key to the MLModelVersion being requested for deployment
        status: Current approval status (pending, approved, rejected, deployed, cancelled)
        requested_by: User ID who submitted the deployment request
        reviewed_by: User ID who reviewed (approved/rejected) the request
        requested_at: Timestamp when the request was submitted
        reviewed_at: Timestamp when the request was reviewed
        justification: Text explaining why this model should be deployed
        review_notes: Text with reviewer's feedback or reasons for rejection
        target_environment: Target environment for deployment (staging, production)
        organization_id: Organization that owns this approval request
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "model_approval_requests"

    model_version_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True
    )
    requested_by: Mapped[str] = mapped_column(nullable=False, index=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    requested_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default="staging"
    )
    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<ModelApprovalRequest(id={self.id}, model_version_id={self.model_version_id}, "
            f"status={self.status}, requested_by={self.requested_by})>"
        )
