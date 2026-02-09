#!/bin/bash
# Apply migration for adding JOB_SEEKER role
# This script applies the 20260209_add_job_seeker_role migration

set -e

echo "=========================================="
echo "Applying JOB_SEEKER role migration"
echo "=========================================="
echo

cd backend

echo "Current migration version:"
python -m alembic current 2>/dev/null || echo "Unable to determine current version"
echo

echo "Applying migration to head..."
python -m alembic upgrade head

echo
echo "=========================================="
echo "Migration applied successfully!"
echo "=========================================="
echo
echo "Verifying..."
python -m alembic current

echo
echo "Expected: Current revision should be 20260209_add_job_seeker_role"
