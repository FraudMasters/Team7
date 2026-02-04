"""
Role model for role-based access control (RBAC)
"""
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class Role(Base, UUIDMixin, TimestampMixin):
    """
    Role model for role-based access control (RBAC)

    This model defines user roles with hierarchical permissions and capabilities.
    Roles determine what actions users can perform within the application.

    Role Hierarchy (higher level = more permissions):
        - Admin (level 1): Full system access, user management, settings, analytics
        - Recruiter (level 2): Candidate management, job postings, screening, interviews
        - Viewer (level 3): Read-only access to candidates and job postings

    Attributes:
        id: UUID primary key
        name: Unique role name (Admin, Recruiter, Viewer)
        description: Human-readable description of the role
        level: Hierarchy level (1=highest, 3=lowest)
        permissions: JSON object defining specific permissions for this role
        created_at: Timestamp when role was created (inherited from TimestampMixin)
        updated_at: Timestamp when role was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[int] = mapped_column(nullable=False, index=True)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name}, level={self.level})>"

    def has_permission(self, permission: str) -> bool:
        """
        Check if this role has a specific permission

        Args:
            permission: Permission key to check (e.g., "users.create", "candidates.read")

        Returns:
            True if the role has this permission, False otherwise
        """
        # Admin has all permissions
        if self.name == "Admin":
            return True

        # Check specific permission in the permissions dict
        permission_parts = permission.split(".")
        current = self.permissions

        for part in permission_parts:
            if isinstance(current, dict):
                if part not in current:
                    return False
                current = current[part]
            else:
                return False

        return bool(current)

    @classmethod
    def get_default_roles(cls) -> list[dict]:
        """
        Get the default role definitions for system initialization

        Returns:
            List of role dictionaries with default permissions
        """
        return [
            {
                "name": "Admin",
                "description": "Full system access including user management, settings, and all features",
                "level": 1,
                "permissions": {
                    "users": {"create": True, "read": True, "update": True, "delete": True},
                    "candidates": {"create": True, "read": True, "update": True, "delete": True},
                    "vacancies": {"create": True, "read": True, "update": True, "delete": True},
                    "analytics": {"read": True, "export": True},
                    "reports": {"create": True, "read": True, "update": True, "delete": True},
                    "settings": {"read": True, "update": True},
                    "backups": {"create": True, "read": True, "restore": True},
                },
            },
            {
                "name": "Recruiter",
                "description": "Recruiting access for candidate management, job postings, and screening",
                "level": 2,
                "permissions": {
                    "users": {"create": False, "read": False, "update": False, "delete": False},
                    "candidates": {"create": True, "read": True, "update": True, "delete": True},
                    "vacancies": {"create": True, "read": True, "update": True, "delete": False},
                    "analytics": {"read": True, "export": False},
                    "reports": {"create": True, "read": True, "update": False, "delete": False},
                    "settings": {"read": False, "update": False},
                    "backups": {"create": False, "read": False, "restore": False},
                },
            },
            {
                "name": "Viewer",
                "description": "Read-only access to candidates and job postings for viewing and reporting",
                "level": 3,
                "permissions": {
                    "users": {"create": False, "read": False, "update": False, "delete": False},
                    "candidates": {"create": False, "read": True, "update": False, "delete": False},
                    "vacancies": {"create": False, "read": True, "update": False, "delete": False},
                    "analytics": {"read": True, "export": False},
                    "reports": {"create": False, "read": True, "update": False, "delete": False},
                    "settings": {"read": False, "update": False},
                    "backups": {"create": False, "read": False, "restore": False},
                },
            },
        ]
