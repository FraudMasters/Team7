"""Add skill hierarchy and relationships tables

Revision ID: 20260221_add_skill_hierarchy_and_relationships
Revises: 20260212_add_parsing_correction_tables
Create Date: 2026-02-21

Adds:
- parent_skill_id column to skill_taxonomies for hierarchical categories
- category_path column to skill_taxonomies for category path storage
- skill_relationships table for skill relationships (parent/child, similar, prerequisite, related)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260221_add_skill_hierarchy_and_relationships"
down_revision: Union[str, None] = "20260212_add_parsing_correction_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add hierarchy columns to skill_taxonomies and create skill_relationships table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Add hierarchy columns to skill_taxonomies if they don't exist
    if "skill_taxonomies" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("skill_taxonomies")]

        # Add parent_skill_id for hierarchical categories
        if "parent_skill_id" not in columns:
            op.add_column(
                "skill_taxonomies",
                sa.Column(
                    "parent_skill_id",
                    postgresql.UUID(as_uuid=True),
                    nullable=True,
                ),
            )
            op.create_foreign_key(
                "fk_skill_taxonomies_parent_skill",
                "skill_taxonomies",
                "skill_taxonomies",
                ["parent_skill_id"],
                ["id"],
            )
            op.create_index(
                "ix_skill_taxonomies_parent_skill_id",
                "skill_taxonomies",
                ["parent_skill_id"],
            )

        # Add category_path for storing the full path from root to this skill
        if "category_path" not in columns:
            op.add_column(
                "skill_taxonomies",
                sa.Column("category_path", sa.JSON(), nullable=True),
            )

    # Create skill_relationships table
    if "skill_relationships" not in inspector.get_table_names():
        op.create_table(
            "skill_relationships",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "source_skill_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "target_skill_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column("relationship_type", sa.String(50), nullable=False),
            sa.Column("weight", sa.Float(), nullable=True),
            sa.Column("extra_metadata", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("organization_id", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(
                ["source_skill_id"],
                ["skill_taxonomies.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["target_skill_id"],
                ["skill_taxonomies.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["organization_id"],
                ["organizations.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_skill_relationships_source_skill_id",
            "skill_relationships",
            ["source_skill_id"],
        )
        op.create_index(
            "ix_skill_relationships_target_skill_id",
            "skill_relationships",
            ["target_skill_id"],
        )
        op.create_index(
            "ix_skill_relationships_relationship_type",
            "skill_relationships",
            ["relationship_type"],
        )
        op.create_index(
            "ix_skill_relationships_organization_id",
            "skill_relationships",
            ["organization_id"],
        )


def downgrade() -> None:
    """Remove hierarchy columns from skill_taxonomies and drop skill_relationships table."""
    # Drop skill_relationships table
    op.drop_index("ix_skill_relationships_organization_id", table_name="skill_relationships")
    op.drop_index("ix_skill_relationships_relationship_type", table_name="skill_relationships")
    op.drop_index("ix_skill_relationships_target_skill_id", table_name="skill_relationships")
    op.drop_index("ix_skill_relationships_source_skill_id", table_name="skill_relationships")
    op.drop_table("skill_relationships")

    # Drop hierarchy columns from skill_taxonomies
    op.drop_index("ix_skill_taxonomies_parent_skill_id", table_name="skill_taxonomies")
    op.drop_constraint("fk_skill_taxonomies_parent_skill", "skill_taxonomies", type_="foreignkey")
    op.drop_column("skill_taxonomies", "category_path")
    op.drop_column("skill_taxonomies", "parent_skill_id")
