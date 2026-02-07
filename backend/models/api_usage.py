"""
APIUsage model for tracking API usage analytics
"""
import enum
from uuid import UUID
from typing import Optional

from sqlalchemy import ForeignKey, JSON, String, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class APIRequestStatus(str, enum.Enum):
    """Status of API requests that can be tracked"""

    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    VALIDATION_ERROR = "validation_error"


class APIUsage(Base, UUIDMixin, TimestampMixin):
    """
    APIUsage model for tracking API usage analytics

    This model enables comprehensive API analytics by recording all API requests,
    allowing for usage metrics, rate limit monitoring, endpoint analysis,
    and developer API performance tracking.

    Attributes:
        id: UUID primary key
        api_key_id: Foreign key to APIKey that made the request
        endpoint: API endpoint that was called (e.g., /api/v1/candidates)
        method: HTTP method used (GET, POST, PUT, DELETE, etc.)
        status: Status of the request (success, rate_limited, etc.)
        status_code: HTTP status code returned
        response_time_ms: Response time in milliseconds
        rate_limit_remaining: Number of requests remaining in rate limit window
        request_data: JSON object with request-specific data (query params, etc.)
        response_data: JSON object with response-specific data (error messages, etc.)
        ip_address: Optional IP address of the requester
        user_agent: Optional user agent string
        created_at: Timestamp when usage was recorded (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "api_usage"

    api_key_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    status: Mapped[APIRequestStatus] = mapped_column(String(50), nullable=False, index=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<APIUsage(id={self.id}, endpoint={self.endpoint}, method={self.method}, status={self.status_code})>"
