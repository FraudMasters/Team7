"""
Create user preferences table for language and locale settings

Creates table for:
- user_preferences: Store user language and timezone preferences
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_create_user_preferences"
down_revision: Union[str, None] = "002_add_advanced_matching"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("timezone", sa.String(50), nullable=True),
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
        comment="Store user language and timezone preferences",
    )
    op.create_index(op.f("ix_user_preferences_language"), "user_preferences", ["language"])


def downgrade() -> None:
    # Drop user_preferences table
    op.drop_index(op.f("ix_user_preferences_language"), table_name="user_preferences")
    op.drop_table("user_preferences")
