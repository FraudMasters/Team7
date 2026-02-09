"""
Skill model for storing job seeker skills
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ProficiencyLevel(str, enum.Enum):
    """Proficiency level for a skill"""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class Skill(Base, UUIDMixin, TimestampMixin):
    """
    Skill model for storing job seeker skills and competencies

    Attributes:
        id: UUID primary key
        resume_id: Resume that this skill belongs to
        name: Name of the skill (e.g., Python, Java, Project Management)
        category: Category of the skill (e.g., Technical, Soft Skills, Languages)
        proficiency_level: Level of proficiency in this skill
        years_of_experience: Number of years of experience with this skill
        description: Additional details about the skill or its application
        created_at: Timestamp when record was created (inherited from TimestampMixin)
        updated_at: Timestamp when record was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "skills"

    resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    proficiency_level: Mapped[ProficiencyLevel] = mapped_column(
        Enum(ProficiencyLevel), default=ProficiencyLevel.INTERMEDIATE, nullable=False
    )
    years_of_experience: Mapped[Optional[float]] = mapped_column(nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name}, level={self.proficiency_level.value})>"
