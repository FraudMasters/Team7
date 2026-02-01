#!/usr/bin/env python3
"""
Run Alembic migration programmatically.
This script executes alembic upgrade head without requiring the alembic CLI.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command

def run_upgrade():
    """Run alembic upgrade to head."""
    print("Running alembic upgrade head...")

    # Create alembic config
    alembic_cfg = Config("alembic.ini")

    try:
        # Run the upgrade
        command.upgrade(alembic_cfg, "head")
        print("✅ Migration completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_upgrade()
    sys.exit(0 if success else 1)
