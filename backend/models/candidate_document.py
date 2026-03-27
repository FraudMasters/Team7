"""
CandidateDocument model for storing additional candidate documents
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class DocumentType(str, enum.Enum):
    """Type of document uploaded by candidate"""

    PORTFOLIO = "PORTFOLIO"               # Portfolio or work samples
    CERTIFICATION = "CERTIFICATION"       # Professional certifications
    COVER_LETTER = "COVER_LETTER"        # Cover letter
    TRANSCRIPT = "TRANSCRIPT"            # Academic transcripts
    REFERENCE = "REFERENCE"              # Reference letters
    OTHER = "OTHER"                      # Other supporting documents


class CandidateDocument(Base, UUIDMixin, TimestampMixin):
    """
    CandidateDocument model for storing additional documents uploaded by candidates

    Attributes:
        id: UUID primary key
        user_id: Foreign key to User (the candidate who uploaded the document)
        application_id: Optional foreign key to JobApplication (if linked to specific application)
        document_type: Type of document (portfolio, certification, etc.)
        filename: Original filename of uploaded document
        file_path: Path to stored document file
        content_type: MIME type of the file (e.g., application/pdf, image/png)
        description: Optional user-provided description of the document
        created_at: Timestamp when document was uploaded (inherited)
        updated_at: Timestamp when document was last updated (inherited)
    """

    __tablename__ = "candidate_documents"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType), default=DocumentType.OTHER, nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="candidate_documents"
    )
    application: Mapped[Optional["JobApplication"]] = relationship(
        "JobApplication",
        back_populates="candidate_documents"
    )

    def __repr__(self) -> str:
        return f"<CandidateDocument(id={self.id}, user_id={self.user_id}, type={self.document_type.value}, filename={self.filename})>"
