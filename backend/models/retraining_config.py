"""
RetrainingConfig model for storing automated model retraining configuration

This model stores runtime-configurable settings for the automated
model retraining pipeline, such as pause/resume state.
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RetrainingConfig(Base, UUIDMixin, TimestampMixin):
    """
    RetrainingConfig model for automated retraining pipeline configuration

    This model stores configuration for the automated model retraining system,
    allowing runtime control of the pipeline without requiring environment
    variable changes or server restarts.

    Attributes:
        id: UUID primary key
        model_name: Name of the model this config applies to (or 'global' for all models)
        paused: Whether automated retraining is paused for this model
        pause_reason: Optional reason for pausing
        paused_by: User or system that initiated the pause
    """

    __tablename__ = "retraining_config"

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="global",
        index=True,
    )
    paused: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    pause_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    paused_by: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    def __repr__(self) -> str:
        status = "paused" if self.paused else "active"
        return f"<RetrainingConfig(model={self.model_name}, status={status})>"
