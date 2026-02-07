"""
Add retraining_config table for pause/resume control

Adds the retraining_config table which stores runtime-configurable settings
for the automated model retraining pipeline, including pause/resume state.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260202_add_retraining_config"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retraining_config",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("model_name", sa.String(100), nullable=False, default="global", index=True),
        sa.Column("paused", sa.Boolean(), nullable=False, default=False),
        sa.Column("pause_reason", sa.String(500), nullable=True),
        sa.Column("paused_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=True),
        comment="Runtime configuration for automated model retraining pipeline",
    )


def downgrade() -> None:
    op.drop_table("retraining_config")
