"""
ClientTenant model for many-to-many relationship between agencies and client organizations
"""
from enum import Enum

from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID as PyUUID

from .base import Base, TimestampMixin, UUIDMixin


class ClientTenantStatus(str, Enum):
    """Status of client tenant relationship"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ClientTenant(Base, UUIDMixin, TimestampMixin):
    """
    ClientTenant model for many-to-many relationship

    This model represents the relationship between recruitment agencies and their
    client organizations. An agency can manage multiple client organizations, and
    theoretically an organization could be serviced by multiple agencies (though
    typically it's one-to-many from agency to organizations).

    Attributes:
        id: UUID primary key
        agency_id: Foreign key to the agency
        organization_id: Foreign key to the client organization (tenant)
        status: Status of the client relationship (active, inactive, suspended)
        is_primary: Whether this is the primary agency for the organization
        created_at: Timestamp when the relationship was created (inherited)
        updated_at: Timestamp when the relationship was last updated (inherited)

    Status values:
        - active: Client relationship is active and operational
        - inactive: Client relationship is no longer active (contract ended)
        - suspended: Client relationship is temporarily suspended
    """

    __tablename__ = "client_tenants"

    agency_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ClientTenantStatus.ACTIVE
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    def __repr__(self) -> str:
        return f"<ClientTenant(id={self.id}, agency_id={self.agency_id}, organization_id={self.organization_id}, status={self.status})>"
