"""
Add JOB_SEEKER role to UserRole enum

Extends the existing userrole enum to include job_seeker role:
- Adds 'job_seeker' as a new valid role value
- Enables registration and authentication for job seekers
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "013_add_job_seeker_role"
down_revision: Union[str, None] = "010_add_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add job_seeker to the userrole enum.

    PostgreSQL requires ALTER TYPE ... ADD VALUE to run outside a transaction.
    We use op.execute() to run the command in autocommit mode.
    """
    # Add job_seeker to the existing userrole enum
    # This must be done outside a transaction in PostgreSQL
    op.execute(
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'job_seeker' AFTER 'hiring_manager'"
    )


def downgrade() -> None:
    """
    Remove job_seeker from the userrole enum.

    Note: PostgreSQL doesn't support removing enum values directly.
    The typical workaround is:
    1. Create a new enum type without the value
    2. Update columns to use the new type
    3. Drop the old enum type

    However, this is a destructive operation and requires manual intervention
    if there are existing rows with the job_seeker role.
    """
    # PostgreSQL doesn't support dropping enum values
    # To properly rollback:
    # 1. Ensure no rows use job_seeker role
    # 2. Create new enum without job_seeker
    # 3. Alter column types to use new enum
    # 4. Drop old enum type

    # For safety, we raise an error to prevent accidental data loss
    raise NotImplementedError(
        "Removing enum values is not supported in PostgreSQL. "
        "Manual intervention required: "
        "1. Delete all rows with job_seeker role "
        "2. Create new userrole enum without job_seeker "
        "3. Update roles.role column to use new enum "
        "4. Drop old userrole type"
    )
