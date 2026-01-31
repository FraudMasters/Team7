"""
WorkflowStageConfig model for per-organization customizable hiring stages
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class WorkflowStageConfig(Base, UUIDMixin, TimestampMixin):
    """
    WorkflowStageConfig model for per-organization customizable hiring stages

    This model enables organizations to customize their hiring workflow stages
    to match their specific recruitment process. Each organization can define
    their own stage names, order, and configuration.

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this workflow stage configuration
        stage_name: Custom name for this stage (e.g., "Applied", "Screening", "Technical Interview")
        stage_order: Order in which this stage appears in the workflow (1, 2, 3, etc.)
        is_default: Whether this is a default stage (applied to new organizations)
        is_active: Whether this stage is currently active and visible
        color: Optional color code for UI display (e.g., "#3B82F6" for blue)
        description: Optional description of what happens in this stage
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "workflow_stage_configs"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color code
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<WorkflowStageConfig(id={self.id}, org={self.organization_id}, stage={self.stage_name})>"
