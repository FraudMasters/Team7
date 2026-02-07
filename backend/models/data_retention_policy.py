"""
DataRetentionPolicy model for automatic data deletion and GDPR compliance
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RetentionEntityType(str, enum.Enum):
    """Types of entities that can have retention policies"""

    # Candidate and resume data
    RESUME = "resume"  # Resume files and parsed data
    CANDIDATE_DATA = "candidate_data"  # Candidate notes, tags, activities
    CANDIDATE_NOTES = "candidate_notes"  # Candidate notes specifically
    CANDIDATE_TAGS = "candidate_tags"  # Candidate tags specifically

    # Analytics and tracking
    ANALYTICS_EVENTS = "analytics_events"  # Analytics event tracking
    MATCH_RESULTS = "match_results"  # Resume-vacancy matching results
    ANALYSIS_RESULTS = "analysis_results"  # Resume analysis results

    # Audit and logging
    AUDIT_LOGS = "audit_logs"  # Audit log entries
    SEARCH_HISTORY = "search_history"  # User search history

    # Application data
    REPORTS = "reports"  # Generated reports
    BACKUPS = "backups"  # Backup files


class RetentionActionType(str, enum.Enum):
    """Types of actions to take when retention period expires"""

    DELETE = "delete"  # Permanently delete the data
    ANONYMIZE = "anonymize"  # Remove PII but keep aggregated data
    ARCHIVE = "archive"  # Move to cold storage/backup
    FLAG_REVIEW = "flag_review"  # Flag for manual review before deletion


class DataRetentionPolicy(Base, UUIDMixin, TimestampMixin):
    """
    DataRetentionPolicy model for automatic data deletion and GDPR compliance

    This model defines policies for automatically managing data lifecycle, ensuring GDPR compliance
    through storage limitation (data shouldn't be kept longer than necessary). Each policy specifies
    how long certain types of data should be retained and what action to take when the retention
    period expires. Policies can be organization-specific (custom settings) or global (default
    system-wide policies).

    GDPR Requirements Met:
    - Storage limitation: Automatic deletion of data after defined periods
    - Data minimization: Policies ensure only necessary data is retained
    - Right to erasure: Supports deletion through retention policies
    - Accountability: Complete audit trail of policy changes

    Background Task Integration:
    This model is used by the retention cleanup Celery task (tasks/retention_cleanup.py)
    which periodically scans for entities exceeding their retention periods and executes
    the specified action (delete, anonymize, archive, or flag for review).

    Attributes:
        id: UUID primary key
        policy_name: Human-readable name for the policy
        entity_type: Type of entity this policy applies to
        retention_days: Number of days to retain data before action
        action_type: Action to take when retention period expires
        organization_id: Foreign key to Organization (NULL for global policies)
        is_active: Whether the policy is currently active
        description: Optional description of the policy's purpose
        legal_basis: Legal basis for retention (e.g., "legitimate_interest", "contract")
        deletion_reason: Reason to record in audit logs when deleting data
        created_at: Timestamp when the policy was created
        updated_at: Timestamp when the policy was last updated
    """

    __tablename__ = "data_retention_policies"

    policy_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    entity_type: Mapped[RetentionEntityType] = mapped_column(
        String(50), nullable=False, index=True
    )
    retention_days: Mapped[int] = mapped_column(nullable=False, default=365)
    action_type: Mapped[RetentionActionType] = mapped_column(
        String(50), nullable=False, default=RetentionActionType.DELETE
    )
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    legal_basis: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    deletion_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return (
            f"<DataRetentionPolicy(id={self.id}, name={self.policy_name}, "
            f"entity={self.entity_type}, days={self.retention_days}, status={status})>"
        )

    def is_applicable_to(self, entity_type: str, organization_id: Optional[UUID] = None) -> bool:
        """
        Check if this policy applies to a specific entity and organization

        Args:
            entity_type: The type of entity to check
            organization_id: Optional organization ID (None checks for global policies)

        Returns:
            True if the policy is active and applies to the entity/org
        """
        if not self.is_active:
            return False

        # Check entity type matches
        if self.entity_type != entity_type:
            return False

        # If policy is organization-specific, check organization matches
        if self.organization_id is not None:
            return self.organization_id == organization_id

        # Global policy (organization_id is None) applies to all organizations
        # unless there's an org-specific policy that overrides it
        return True
