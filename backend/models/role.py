"""
Role model for user role-based access control
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    """User role definitions for access control"""

    ADMIN = "admin"
    HIRING_MANAGER = "hiring_manager"
    JOB_SEEKER = "job_seeker"
    RECRUITER = "recruiter"
    VIEWER = "viewer"


class Role(Base, UUIDMixin, TimestampMixin):
    """
    Role model for user role-based access control

    This model manages user permissions and access levels within the system.
    Each user can have one or more roles, and roles can be assigned to specific
    vacancies or organizations.

    Attributes:
        id: UUID primary key
        user_id: Foreign key to User
        role: User role (admin, hiring_manager, job_seeker, recruiter, viewer)
        vacancy_id: Optional foreign key to JobVacancy for scoped permissions
        notes: Optional notes about this role assignment
        created_at: Timestamp when role was assigned (inherited)
        updated_at: Timestamp when role was last updated (inherited)
    """

    __tablename__ = "roles"

    user_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.VIEWER, nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUIDMixin]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, user_id={self.user_id}, role={self.role})>"
