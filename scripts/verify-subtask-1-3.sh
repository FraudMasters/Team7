#!/bin/bash
# Verification script for subtask-1-3: Start Keycloak service and verify health

set -e

echo "=== Verifying Keycloak Service Health ==="
echo ""

# Check if Keycloak is running
echo "1. Checking if Keycloak container is running..."
if docker ps | grep -q "keycloak"; then
    echo "✓ Keycloak container is running"
else
    echo "✗ Keycloak container is not running"
    echo ""
    echo "To start Keycloak, run:"
    echo "  docker-compose up -d keycloak"
    echo ""
    exit 1
fi

echo ""
echo "2. Testing Keycloak health endpoint..."
# Wait a moment for the service to be ready
sleep 2

# Test health endpoint
HEALTH_STATUS=$(curl -f -s -o /dev/null -w "%{http_code}" http://localhost:8080/health/ready || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✓ Keycloak health check passed (HTTP 200)"
    echo ""
    echo "Keycloak is ready at:"
    echo "  - Admin Console: http://localhost:8080/admin"
    echo "  - Health: http://localhost:8080/health/ready"
    echo ""
    echo "Default admin credentials:"
    echo "  Username: admin"
    echo "  Password: admin (CHANGE IN PRODUCTION)"
    exit 0
else
    echo "✗ Keycloak health check failed (HTTP $HEALTH_STATUS)"
    echo ""
    echo "Checking Keycloak logs..."
    docker logs --tail 20 resume_analysis_keycloak
    exit 1
fi
