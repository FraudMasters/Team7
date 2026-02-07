"""
Script to run Alembic migration programmatically
"""
import sys
from alembic.config import Config
from alembic import command

# Create Alembic configuration
alembic_cfg = Config("alembic.ini")

try:
    # Upgrade to head
    command.upgrade(alembic_cfg, "head")
    print("Migration completed successfully!")
    sys.exit(0)
except Exception as e:
    print(f"Migration failed: {e}")
    sys.exit(1)
