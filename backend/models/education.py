"""
Education model for storing job seeker education history
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, Date
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class DegreeType(str, enum.Enum):
    """Type of degree"""

    HIGH_SCHOOL = "HIGH_SCHOOL"
    CERTIFICATE = "CERTIFICATE"
    ASSOCIATE = "ASSOCIATE"
    BACHELOR = "BACHELOR"
    MASTER = "MASTER"
    DOCTORATE = "DOCTORATE"
    POST_DOCTORAL = "POST_DOCTORAL"
    OTHER = "OTHER"


class Education(Base, UUIDMixin, TimestampMixin):
    """
    Education model for storing job seeker education entries

    Attributes:
        id: UUID primary key
        resume_id: Resume that this education belongs to
        institution_name: Name of the school, college or university
        degree: Degree obtained (e.g., Bachelor of Science, Master of Arts)
        field_of_study: Major or area of study (e.g., Computer Science, Mathematics)
        start_date: When the education program started
        end_date: When the education program ended or graduation date (null if current)
        description: Additional details about achievements, coursework, etc.
        location: City, state or country of the institution
        degree_type: Type of degree (high school, bachelor, master, PhD, etc.)
        created_at: Timestamp when record was created (inherited from TimestampMixin)
        updated_at: Timestamp when record was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "education"

    resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    field_of_study: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[object] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    degree_type: Mapped[DegreeType] = mapped_column(
        Enum(DegreeType), default=DegreeType.BACHELOR, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Education(id={self.id}, institution={self.institution_name}, degree={self.degree}, start={self.start_date})>"
