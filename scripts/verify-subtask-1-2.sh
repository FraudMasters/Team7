#!/bin/bash
# Verification script for subtask-1-2: Create dedicated PostgreSQL database for Keycloak

echo "=== Verifying subtask-1-2: Keycloak Database Creation ==="
echo ""

# Check if keycloak_db exists
echo "1. Checking if keycloak_db database exists..."
docker exec -it postgres psql -U postgres -l | grep keycloak_db

if [ $? -eq 0 ]; then
    echo "✓ Database 'keycloak_db' found"
else
    echo "✗ Database 'keycloak_db' NOT found"
    echo ""
    echo "To create the database, you may need to:"
    echo "1. Restart PostgreSQL container to run initialization scripts:"
    echo "   docker-compose up -d postgres --force-recreate"
    echo ""
    echo "2. Or create manually:"
    echo "   docker exec -it postgres psql -U postgres -c 'CREATE DATABASE keycloak_db;'"
    exit 1
fi

echo ""
echo "2. Verifying keycloak user exists..."
docker exec -it postgres psql -U postgres -c "\du" | grep keycloak

if [ $? -eq 0 ]; then
    echo "✓ User 'keycloak' found"
else
    echo "⚠ User 'keycloak' NOT found (may not be created yet)"
fi

echo ""
echo "3. Checking database privileges..."
docker exec -it postgres psql -U postgres keycloak_db -c "\l" | grep keycloak_db

echo ""
echo "=== Verification Complete ==="
