"""
AgencyUser model for many-to-many relationship between agencies and users
"""
from enum import Enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID as PyUUID

from .base import Base, TimestampMixin, UUIDMixin


class AgencyUserRole(str, Enum):
    """User roles within an agency"""

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class AgencyUser(Base, UUIDMixin, TimestampMixin):
    """
    AgencyUser model for many-to-many relationship

    This model represents the relationship between agencies and users,
    including the user's role within that agency. A user can belong to
    multiple agencies with different roles in each.

    Attributes:
        id: UUID primary key
        agency_id: Foreign key to the agency
        user_id: Foreign key to the user
        role: User's role in the agency (admin, member, viewer)
        created_at: Timestamp when the relationship was created (inherited)
        updated_at: Timestamp when the relationship was last updated (inherited)

    Roles:
        - admin: Full access to agency settings, can invite/manage users
        - member: Can access and modify agency data, but not settings
        - viewer: Read-only access to agency data
    """

    __tablename__ = "agency_users"

    agency_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AgencyUserRole.MEMBER
    )

    def __repr__(self) -> str:
        return f"<AgencyUser(id={self.id}, agency_id={self.agency_id}, user_id={self.user_id}, role={self.role})>"
