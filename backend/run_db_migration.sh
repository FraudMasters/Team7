#!/bin/bash
# Run database migration
set -e

cd "$(dirname "$0")"

echo "Running Alembic migration..."

# Try to find and use alembic
if command -v alembic &> /dev/null; then
    alembic upgrade head
elif [ -f ".venv/bin/alembic" ]; then
    .venv/bin/alembic upgrade head
elif [ -f "venv/bin/alembic" ]; then
    venv/bin/alembic upgrade head
else
    # Fallback to running the Python script directly
    python3 run_migration.py
fi

echo "✓ Migration applied"
