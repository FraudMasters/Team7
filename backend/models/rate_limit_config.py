"""
RateLimitConfig model for storing organization-specific rate limit policies
"""
from typing import Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RateLimitConfig(Base, UUIDMixin, TimestampMixin):
    """
    RateLimitConfig model for storing organization-specific rate limit policies

    Attributes:
        id: UUID primary key
        organization_id: Organization this rate limit config applies to
        endpoint_pattern: Optional pattern to match specific endpoints (e.g., /api/v1/*)
        requests_per_window: Maximum number of requests allowed within the time window
        window_size_seconds: Time window size in seconds (e.g., 60 for per-minute limits)
        role_type: Optional user role for role-based limits (admin, org_admin, user, anonymous)
        is_enabled: Whether this rate limit config is currently active
        created_at: Timestamp when config was created (inherited from TimestampMixin)
        updated_at: Timestamp when config was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "rate_limit_configs"

    organization_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    endpoint_pattern: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    requests_per_window: Mapped[int] = mapped_column(Integer, nullable=False)
    window_size_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    role_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<RateLimitConfig(id={self.id}, org={self.organization_id}, requests={self.requests_per_window}/{self.window_size_seconds}s, enabled={self.is_enabled})>"
