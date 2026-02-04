"""
IPBlocklist model for storing blocked IPs and networks
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class IPBlocklist(Base, UUIDMixin, TimestampMixin):
    """
    IPBlocklist model for storing blocked IP addresses and networks for DDoS protection

    Attributes:
        id: UUID primary key
        ip_address: Individual IP address to block (IPv4 or IPv6)
        cidr: CIDR notation for blocking a range of IPs (e.g., 192.168.1.0/24)
        block_reason: Reason why this IP/network was blocked
        is_active: Whether this block is currently active
        expires_at: Optional timestamp when the block should expire
        created_by: User ID or system identifier that created this block
        created_at: Timestamp when block was created (inherited from TimestampMixin)
        updated_at: Timestamp when block was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "ip_blocklist"

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    cidr: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    block_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        target = self.ip_address or self.cidr
        return f"<IPBlocklist(id={self.id}, target={target}, active={self.is_active})>"
