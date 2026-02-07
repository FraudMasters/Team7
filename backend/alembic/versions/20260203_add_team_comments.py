"""
Add team comments and comment mentions tables

Creates tables for:
- team_comments: Enable collaborative threaded discussions on candidate profiles
- comment_mentions: Track @mentions in team comments for notifications
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_team_comments"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create team_comments table
    op.create_table(
        "team_comments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_comment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("edits_count", sa.Integer(), nullable=False, server_default="0"),
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
        comment="Enable collaborative threaded discussions on candidate profiles",
    )
    op.create_index(op.f("ix_team_comments_resume_id"), "team_comments", ["resume_id"])
    op.create_index(op.f("ix_team_comments_author_id"), "team_comments", ["author_id"])
    op.create_index(
        op.f("ix_team_comments_parent_comment_id"), "team_comments", ["parent_comment_id"]
    )
    op.create_index(op.f("ix_team_comments_is_resolved"), "team_comments", ["is_resolved"])
    op.create_index(op.f("ix_team_comments_is_deleted"), "team_comments", ["is_deleted"])

    # Create comment_mentions table
    op.create_table(
        "comment_mentions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "comment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("team_comments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mentioned_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
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
        comment="Track @mentions in team comments for notifications",
    )
    op.create_index(
        op.f("ix_comment_mentions_comment_id"), "comment_mentions", ["comment_id"]
    )
    op.create_index(
        op.f("ix_comment_mentions_mentioned_user_id"),
        "comment_mentions",
        ["mentioned_user_id"],
    )
    op.create_index(op.f("ix_comment_mentions_is_read"), "comment_mentions", ["is_read"])


def downgrade() -> None:
    # Drop comment_mentions table
    op.drop_index(op.f("ix_comment_mentions_is_read"), table_name="comment_mentions")
    op.drop_index(
        op.f("ix_comment_mentions_mentioned_user_id"), table_name="comment_mentions"
    )
    op.drop_index(op.f("ix_comment_mentions_comment_id"), table_name="comment_mentions")
    op.drop_table("comment_mentions")

    # Drop team_comments table
    op.drop_index(op.f("ix_team_comments_is_deleted"), table_name="team_comments")
    op.drop_index(op.f("ix_team_comments_is_resolved"), table_name="team_comments")
    op.drop_index(
        op.f("ix_team_comments_parent_comment_id"), table_name="team_comments"
    )
    op.drop_index(op.f("ix_team_comments_author_id"), table_name="team_comments")
    op.drop_index(op.f("ix_team_comments_resume_id"), table_name="team_comments")
    op.drop_table("team_comments")
