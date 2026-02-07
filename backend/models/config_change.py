"""
ConfigChange model for tracking configuration modifications
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ConfigChangeAction(str, enum.Enum):
    """Types of configuration change actions"""

    # Configuration value changes
    VALUE_UPDATED = "value_updated"
    VALUE_RESET = "value_reset"

    # Environment changes
    ENVIRONMENT_CHANGED = "environment_changed"

    # Hot-reload operations
    CONFIG_RELOADED = "config_reloaded"
    CONFIG_VALIDATED = "config_validated"

    # Security operations
    ENCRYPTED_VALUE_UPDATED = "encrypted_value_updated"
    SECRET_ROTATED = "secret_rotated"

    # Batch operations
    BATCH_UPDATE = "batch_update"
    BATCH_ROLLBACK = "batch_rollback"

    # System operations
    CONFIG_FILE_LOADED = "config_file_loaded"
    CONFIG_OVERRIDE_APPLIED = "config_override_applied"
    CONFIG_VALIDATION_FAILED = "config_validation_failed"


class ConfigChange(Base, UUIDMixin, TimestampMixin):
    """
    ConfigChange model for tracking configuration modifications

    This model provides a comprehensive audit trail of all configuration changes
    across the system, enabling compliance monitoring, security auditing, and
    accountability tracking. It records who changed what configuration, when,
    and the before/after values for complete traceability.

    Attributes:
        id: UUID primary key
        action_type: Type of configuration action that occurred
        config_key: The configuration key that was changed (e.g., 'database_url')
        config_path: Dot-notation path for nested configs (e.g., 'backup.s3.enabled')
        environment: Environment where the change was made (development, staging, production)
        user_id: Foreign key to User who performed the change
        organization_id: Foreign key to Organization where the change occurred
        ip_address: IP address from which the change was made
        user_agent: User agent string of the client
        before_value: Configuration value before the change
        after_value: Configuration value after the change
        change_reason: Optional explanation for the change
        metadata: Additional metadata about the change (JSON)
        created_at: Timestamp when the change was recorded (inherited)
        updated_at: Timestamp when the record was last updated (inherited)
    """

    __tablename__ = "config_changes"

    action_type: Mapped[ConfigChangeAction] = mapped_column(
        String(50), nullable=False, index=True
    )
    config_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    config_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, index=True
    )
    environment: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    organization_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    before_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ConfigChange(id={self.id}, action={self.action_type}, "
            f"key={self.config_key}, env={self.environment})>"
        )
