"""Add candidate documents table

Creates table for:
- candidate_documents: Store additional documents uploaded by candidates (portfolios, certifications, etc.)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260321_add_candidate_documents"
down_revision: Union[str, None] = "20260221_add_skill_hierarchy_and_relationships"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create documenttype enum type
    documenttype_enum = sa.Enum(
        "PORTFOLIO",
        "CERTIFICATION",
        "COVER_LETTER",
        "TRANSCRIPT",
        "REFERENCE",
        "OTHER",
        name="documenttype",
    )
    documenttype_enum.create(op.get_bind(), checkfirst=True)

    # Create candidate_documents table
    op.create_table(
        "candidate_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_type",
            documenttype_enum,
            nullable=False,
            server_default="OTHER",
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Store additional documents uploaded by candidates (portfolios, certifications, etc.)",
    )
    op.create_index(op.f("ix_candidate_documents_user_id"), "candidate_documents", ["user_id"])
    op.create_index(op.f("ix_candidate_documents_application_id"), "candidate_documents", ["application_id"])
    op.create_index(op.f("ix_candidate_documents_document_type"), "candidate_documents", ["document_type"])


def downgrade() -> None:
    # Drop candidate_documents table
    op.drop_index(op.f("ix_candidate_documents_document_type"), table_name="candidate_documents")
    op.drop_index(op.f("ix_candidate_documents_application_id"), table_name="candidate_documents")
    op.drop_index(op.f("ix_candidate_documents_user_id"), table_name="candidate_documents")
    op.drop_table("candidate_documents")

    # Drop enum type
    sa.Enum(name="documenttype").drop(op.get_bind(), checkfirst=True)
