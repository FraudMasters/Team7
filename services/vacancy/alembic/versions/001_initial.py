"""
Начальная схема базы данных для Vacancy Service

Создает таблицу:
- vacancies: Хранение описаний вакансий и требований к кандидатам
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vacancies table / Создаем таблицу vacancies
    op.create_table(
        "vacancies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", postgresql.JSON(), nullable=False, default=list),
        sa.Column("min_experience_months", sa.Integer(), nullable=True),
        sa.Column("additional_requirements", postgresql.JSON(), nullable=True, default=list),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("work_format", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("english_level", sa.String(50), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
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
        comment="Store job vacancy descriptions and candidate requirements",
    )
    op.create_index("ix_vacancies_external_id", "vacancies", ["external_id"])
    op.create_index("ix_vacancies_created_at", "vacancies", ["created_at"])


def downgrade() -> None:
    # Drop vacancies table / Удаляем таблицу vacancies
    op.drop_index("ix_vacancies_created_at", table_name="vacancies")
    op.drop_index("ix_vacancies_external_id", table_name="vacancies")
    op.drop_table("vacancies")
