#!/bin/bash
# Start Keycloak service for subtask-1-3
# This script starts Keycloak and waits for it to be healthy

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "Starting Keycloak Service"
echo "========================================"
echo ""

# Function to wait for service
wait_for_keycloak() {
    local max_attempts=60
    local attempt=0

    echo "Waiting for Keycloak to be healthy..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s http://localhost:8080/health/ready > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Keycloak is healthy${NC}"
            return 0
        fi

        # Check if container is running
        if ! docker ps | grep -q "keycloak"; then
            echo -e "${RED}✗ Keycloak container is not running${NC}"
            echo "Check logs with: docker logs resume_analysis_keycloak"
            return 1
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    echo -e "${RED}✗ Timeout waiting for Keycloak${NC}"
    return 1
}

# Check if PostgreSQL is running
echo "Checking PostgreSQL..."
if ! docker ps | grep -q "postgres"; then
    echo -e "${YELLOW}PostgreSQL is not running. Starting it...${NC}"
    docker-compose up -d postgres

    echo "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec resume_analysis_db pg_isready -U postgres > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
            break
        fi
        sleep 1
    done
else
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
fi

echo ""

# Check if Keycloak database exists
echo "Checking Keycloak database..."
DB_EXISTS=$(docker exec resume_analysis_db psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='keycloak_db'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" != "1" ]; then
    echo -e "${YELLOW}Creating Keycloak database...${NC}"
    docker exec resume_analysis_db psql -U postgres -c "CREATE DATABASE keycloak_db;" 2>/dev/null || echo "Database creation failed or already exists"
    docker exec resume_analysis_db psql -U postgres -c "CREATE USER keycloak WITH PASSWORD 'keycloak_password';" 2>/dev/null || echo "User may already exist"
    docker exec resume_analysis_db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE keycloak_db TO keycloak;" 2>/dev/null
    echo -e "${GREEN}✓ Database setup complete${NC}"
else
    echo -e "${GREEN}✓ Keycloak database exists${NC}"
fi

echo ""

# Start Keycloak
echo "Starting Keycloak service..."
docker-compose up -d keycloak

echo ""

# Wait for Keycloak to be healthy
if wait_for_keycloak; then
    echo ""
    echo "========================================"
    echo -e "${GREEN}Keycloak Started Successfully${NC}"
    echo "========================================"
    echo ""
    echo "Keycloak is ready at:"
    echo "  - Health Endpoint: http://localhost:8080/health/ready"
    echo "  - Admin Console:  http://localhost:8080/admin"
    echo ""
    echo "Default credentials:"
    echo "  Username: admin"
    echo "  Password: admin (CHANGE IN PRODUCTION)"
    echo ""
    exit 0
else
    echo ""
    echo "========================================"
    echo -e "${RED}Failed to Start Keycloak${NC}"
    echo "========================================"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker logs resume_analysis_keycloak"
    echo "  2. Check status: docker ps -a | grep keycloak"
    echo "  3. Restart: docker-compose restart keycloak"
    echo ""
    exit 1
fi
