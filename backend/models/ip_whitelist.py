"""
IPWhitelist model for organization IP access restrictions
"""
from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class IPWhitelist(Base, UUIDMixin, TimestampMixin):
    """
    IPWhitelist model for managing organization IP access restrictions

    This model enables organizations to restrict access to approved IP addresses or ranges.
    Admins can configure multiple IP ranges using CIDR notation, and the IP whitelist
    middleware validates incoming requests against these rules. Each organization can
    have its own IP whitelist configuration.

    Attributes:
        id: UUID primary key
        organization_id: Organization ID (null for system-wide whitelist)
        name: Friendly name for this IP range (e.g., "Office Network", "VPN")
        description: Optional description with additional context
        cidr_notation: IP range in CIDR notation (e.g., "192.168.1.0/24", "10.0.0.0/16")
        start_ip: Starting IP address (for range-based whitelisting)
        end_ip: Ending IP address (for range-based whitelisting)
        is_active: Whether this IP range is currently enforced
        created_by: User ID who created this whitelist entry
        created_at: Timestamp when whitelist entry was created (inherited from TimestampMixin)
        updated_at: Timestamp when whitelist entry was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "ip_whitelists"

    # Organization scope
    organization_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Organization ID (null for system-wide whitelist)"
    )

    # Identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Friendly name for this IP range (e.g., 'Office Network')"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description with additional context"
    )

    # IP range specification
    cidr_notation: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="IP range in CIDR notation (e.g., '192.168.1.0/24')"
    )
    start_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Starting IP address (for range-based whitelisting, supports IPv6)"
    )
    end_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Ending IP address (for range-based whitelisting, supports IPv6)"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this IP range is currently enforced"
    )

    # Audit tracking
    created_by: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="User ID who created this whitelist entry"
    )

    def __repr__(self) -> str:
        org_id_str = f"org={self.organization_id}" if self.organization_id else "system-wide"
        status = "active" if self.is_active else "inactive"
        return f"<IPWhitelist(id={self.id}, {org_id_str}, name={self.name}, status={status})>"
