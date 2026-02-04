"""
IntegrationMapping model for configurable field mappings between systems
"""
import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class FieldMappingType(str, enum.Enum):
    """Types of field mappings"""

    DIRECT = "DIRECT"  # Simple 1:1 field mapping
    TRANSFORMED = "TRANSFORMED"  # Value transformation required
    COMPUTED = "COMPUTED"  # Value computed from multiple fields
    LOOKUP = "LOOKUP"  # Value from lookup table/mapping


class IntegrationMapping(Base, UUIDMixin, TimestampMixin):
    """
    IntegrationMapping model for configurable field mappings between systems

    This model enables configurable field mappings between the internal system
    and external HRIS/ATS platforms (Workday, Greenhouse, Lever, BambooHR, Ashby, etc.).
    Each integration can have multiple field mappings that define how data is
    synchronized between systems.

    Attributes:
        id: UUID primary key
        integration_id: Integration this mapping belongs to
        source_field: Field name in internal system (e.g., "first_name", "salary")
        target_field: Field name in external system (e.g., "firstName", "compensation")
        mapping_type: Type of mapping (DIRECT, TRANSFORMED, COMPUTED, LOOKUP)
        field_type: Data type of field (string, number, boolean, date, etc.)
        is_required: Whether this field is required for synchronization
        is_active: Whether this mapping is currently active and used in sync
        transform_config: JSON configuration for value transformation rules
        default_value: Optional default value if source field is empty/null
        priority: Processing order for mappings (lower numbers processed first)
        validation_rule: Optional validation pattern or rule (regex, range, etc.)
        description: Optional description of what this mapping does
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "integration_mappings"

    integration_id: Mapped[str] = mapped_column(
        ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_field: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_field: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mapping_type: Mapped[FieldMappingType] = mapped_column(
        Enum(FieldMappingType), default=FieldMappingType.DIRECT, nullable=False, index=True
    )
    field_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # string, number, boolean, date, etc.
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    transform_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=None)
    default_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    validation_rule: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<IntegrationMapping(id={self.id}, integration_id={self.integration_id}, source={self.source_field}, target={self.target_field})>"
