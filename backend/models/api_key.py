"""
APIKey model for developer API authentication and rate limiting
"""
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import JSON, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class APIKeyScope(str, enum.Enum):
    """Scopes available for API key permissions"""

    # Candidate operations
    READ_CANDIDATES = "read:candidates"
    WRITE_CANDIDATES = "write:candidates"
    DELETE_CANDIDATES = "delete:candidates"

    # Resume operations
    READ_RESUMES = "read:resumes"
    WRITE_RESUMES = "write:resumes"
    DELETE_RESUMES = "delete:resumes"

    # Vacancy operations
    READ_VACANCIES = "read:vacancies"
    WRITE_VACANCIES = "write:vacancies"
    DELETE_VACANCIES = "delete:vacancies"

    # Analytics operations
    READ_ANALYTICS = "read:analytics"

    # Webhook operations
    READ_WEBHOOKS = "read:webhooks"
    WRITE_WEBHOOKS = "write:webhooks"
    DELETE_WEBHOOKS = "delete:webhooks"

    # Workflow operations
    READ_WORKFLOWS = "read:workflows"
    WRITE_WORKFLOWS = "write:workflows"
    DELETE_WORKFLOWS = "delete:workflows"

    # Plugin operations
    READ_PLUGINS = "read:plugins"
    WRITE_PLUGINS = "write:plugins"
    DELETE_PLUGINS = "delete:plugins"

    # API key management
    READ_API_KEYS = "read:api_keys"
    WRITE_API_KEYS = "write:api_keys"
    DELETE_API_KEYS = "delete:api_keys"


class APIKey(Base, UUIDMixin, TimestampMixin):
    """
    APIKey model for developer API authentication and rate limiting

    This model enables secure API access for developers by storing
    hashed API keys with configurable scopes and rate limits.

    Attributes:
        id: UUID primary key
        key_hash: SHA-256 hash of the API key for secure storage
        key_prefix: First 8 characters of the key for identification
        name: User-friendly name for the API key
        scopes: JSON array of permitted scopes/permissions
        rate_limit: JSON object with rate limit configuration
                  (requests_per_minute, requests_per_hour, requests_per_day)
        is_active: Whether the key is currently active
        expires_at: Optional expiration timestamp
        last_used_at: Timestamp of last API usage
        created_at: Timestamp when key was created (inherited)
        updated_at: Timestamp when key was last updated (inherited)
    """

    __tablename__ = "api_keys"

    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    rate_limit: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=lambda: {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000,
        },
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, prefix={self.key_prefix}, name={self.name}, active={self.is_active})>"

    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def has_scope(self, scope: str) -> bool:
        """Check if the API key has a specific scope"""
        return scope in self.scopes
