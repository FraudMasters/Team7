"""
OrganizationUser model for many-to-many relationship between organizations and users
"""
from enum import Enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID as PyUUID

from .base import Base, TimestampMixin, UUIDMixin


class OrganizationUserRole(str, Enum):
    """User roles within an organization"""

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationUser(Base, UUIDMixin, TimestampMixin):
    """
    OrganizationUser model for many-to-many relationship

    This model represents the relationship between organizations and users,
    including the user's role within that organization. A user can belong to
    multiple organizations with different roles in each.

    Attributes:
        id: UUID primary key
        organization_id: Foreign key to the organization
        user_id: Foreign key to the user
        role: User's role in the organization (admin, member, viewer)
        created_at: Timestamp when the relationship was created (inherited)
        updated_at: Timestamp when the relationship was last updated (inherited)

    Roles:
        - admin: Full access to organization settings, can invite/manage users
        - member: Can access and modify organization data, but not settings
        - viewer: Read-only access to organization data
    """

    __tablename__ = "organization_users"

    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
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
        String(50), nullable=False, default=OrganizationUserRole.MEMBER
    )

    def __repr__(self) -> str:
        return f"<OrganizationUser(id={self.id}, organization_id={self.organization_id}, user_id={self.user_id}, role={self.role})>"
