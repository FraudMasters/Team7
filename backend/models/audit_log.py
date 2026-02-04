"""
AuditLog model for tracking system-wide user actions and changes
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class AuditActionType(str, enum.Enum):
    """Types of audit actions that can be tracked"""

    # Resume operations
    RESUME_CREATED = "resume_created"
    RESUME_UPDATED = "resume_updated"
    RESUME_DELETED = "resume_deleted"
    RESUME_VIEWED = "resume_viewed"
    RESUME_UPLOADED = "resume_uploaded"

    # Vacancy operations
    VACANCY_CREATED = "vacancy_created"
    VACANCY_UPDATED = "vacancy_updated"
    VACANCY_DELETED = "vacancy_deleted"
    VACANCY_VIEWED = "vacancy_viewed"

    # User operations
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_INVITED = "user_invited"
    USER_ROLE_CHANGED = "user_role_changed"

    # Candidate operations
    CANDIDATE_RANKED = "candidate_ranked"
    CANDIDATE_TAGGED = "candidate_tagged"
    CANDIDATE_NOTE_ADDED = "candidate_note_added"
    CANDIDATE_STAGE_CHANGED = "candidate_stage_changed"

    # Matching operations
    MATCH_CREATED = "match_created"
    MATCH_UPDATED = "match_updated"
    MATCH_DELETED = "match_deleted"

    # Data export operations
    DATA_EXPORTED = "data_exported"
    REPORT_GENERATED = "report_generated"

    # Integration operations
    INTEGRATION_CREATED = "integration_created"
    INTEGRATION_UPDATED = "integration_updated"
    INTEGRATION_DELETED = "integration_deleted"
    INTEGRATION_VIEWED = "integration_viewed"
    INTEGRATION_TESTED = "integration_tested"
    INTEGRATION_SYNCED = "integration_synced"

    # System operations
    SETTINGS_UPDATED = "settings_updated"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"

    # Authentication operations
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """
    AuditLog model for tracking system-wide user actions and changes

    This model provides a comprehensive audit trail of all user actions across the system,
    enabling compliance monitoring, security auditing, and accountability tracking. It records
    who did what, when, and on which entities, with optional before/after values for sensitive
    operations like deletions and role changes.

    Attributes:
        id: UUID primary key
        action_type: Type of action that occurred
        entity_type: Type of entity that was affected (resume, vacancy, user, etc.)
        entity_id: ID of the affected entity
        user_id: Foreign key to User who performed the action
        organization_id: Foreign key to Organization where the action occurred
        ip_address: IP address from which the action was performed
        user_agent: User agent string of the client
        action_data: JSON object with action-specific additional data
        before_value: JSON object with entity state before the action (for sensitive actions)
        after_value: JSON object with entity state after the action (for sensitive actions)
        reason: Optional text explanation for the action
        created_at: Timestamp when the action was recorded (inherited)
        updated_at: Timestamp when the record was last updated (inherited)
    """

    __tablename__ = "audit_logs"

    action_type: Mapped[AuditActionType] = mapped_column(
        String(50), nullable=False, index=True
    )
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    organization_id: Mapped[Optional[UUID]] = mapped_column(nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    before_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action_type}, entity={self.entity_type})>"
