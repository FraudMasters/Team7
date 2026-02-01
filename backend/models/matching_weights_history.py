"""
MatchingWeightsHistory model for audit trail of weight profile changes
"""
from typing import Optional

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MatchingWeightsHistory(Base, UUIDMixin, TimestampMixin):
    """
    MatchingWeightsHistory model for tracking all changes to weight profiles

    This model maintains an audit trail of all modifications to matching weight profiles,
    allowing administrators to review historical changes and revert if necessary.

    Attributes:
        id: UUID primary key
        profile_id: UUID of the profile that was changed
        organization_id: Organization that owns the profile
        change_type: Type of change (create, update, delete)
        changed_by: User ID who made the change
        old_name: Previous profile name (before update)
        new_name: New profile name (after update/create)
        old_description: Previous description (before update)
        new_description: New description (after update/create)
        old_keyword_weight: Previous keyword weight (before update)
        new_keyword_weight: New keyword weight (after update/create)
        old_tfidf_weight: Previous TF-IDF weight (before update)
        new_tfidf_weight: New TF-IDF weight (after update/create)
        old_vector_weight: Previous vector weight (before update)
        new_vector_weight: New vector weight (after update/create)
        old_is_default: Previous is_default value (before update)
        new_is_default: New is_default value (after update/create)
        created_at: Timestamp when the change was recorded (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "matching_weights_history"

    profile_id: Mapped[str] = mapped_column(nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # create, update, delete
    changed_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Old values (before change)
    old_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    old_description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    old_keyword_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    old_tfidf_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    old_vector_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    old_is_default: Mapped[Optional[bool]] = mapped_column(nullable=True)

    # New values (after change)
    new_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    new_description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    new_keyword_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_tfidf_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_vector_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_is_default: Mapped[Optional[bool]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<MatchingWeightsHistory(id={self.id}, profile_id={self.profile_id}, "
            f"change_type={self.change_type}, changed_by={self.changed_by})>"
        )
