#!/bin/bash
# Comprehensive verification script for Keycloak health (subtask-1-3)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "Keycloak Health Verification"
echo "Subtask 1-3"
echo "========================================"
echo ""

# Track overall status
ALL_CHECKS_PASSED=true

# Check 1: Container running
echo -e "${BLUE}[Check 1/5]${NC} Checking if Keycloak container is running..."
if docker ps | grep -q "keycloak"; then
    CONTAINER_STATUS=$(docker ps --format "{{.Status}}" | grep keycloak)
    echo -e "${GREEN}✓ PASS${NC} - Keycloak container is running ($CONTAINER_STATUS)"
else
    echo -e "${RED}✗ FAIL${NC} - Keycloak container is not running"
    ALL_CHECKS_PASSED=false

    if docker ps -a | grep -q "keycloak"; then
        echo ""
        echo "Keycloak container exists but is not running. Starting it..."
        docker-compose start keycloak
        sleep 5
    else
        echo ""
        echo "Keycloak container does not exist. Please run:"
        echo "  bash scripts/start-keycloak.sh"
        echo ""
        exit 1
    fi
fi
echo ""

# Check 2: Port accessible
echo -e "${BLUE}[Check 2/5]${NC} Checking if port 8080 is accessible..."
if nc -z localhost 8080 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC} - Port 8080 is accessible"
else
    echo -e "${RED}✗ FAIL${NC} - Port 8080 is not accessible"
    ALL_CHECKS_PASSED=false
    echo ""
    echo "Possible issues:"
    echo "  - Keycloak is still starting up"
    echo "  - Another service is using port 8080"
    echo "  - Firewall is blocking the port"
fi
echo ""

# Check 3: Health endpoint responds
echo -e "${BLUE}[Check 3/5]${NC} Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8080/health/ready 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Health endpoint returned HTTP 200"
else
    echo -e "${RED}✗ FAIL${NC} - Health endpoint returned HTTP $HTTP_CODE"
    ALL_CHECKS_PASSED=false
    echo ""
    echo "Response:"
    echo "$HEALTH_RESPONSE" | head -n-1
fi
echo ""

# Check 4: Database connectivity (from Keycloak's perspective)
echo -e "${BLUE}[Check 4/5]${NC} Checking Keycloak database connectivity..."
DB_EXISTS=$(docker exec resume_analysis_db psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='keycloak_db'" 2>/dev/null || echo "")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Keycloak database exists"

    # Check if tables are created (sign of successful startup)
    TABLE_COUNT=$(docker exec resume_analysis_db psql -U postgres keycloak_db -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")

    if [ "$TABLE_COUNT" -gt "0" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Database tables initialized ($TABLE_COUNT tables)"
    else
        echo -e "${YELLOW}⚠ WARN${NC} - Database tables not yet created (Keycloak may still be initializing)"
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Keycloak database does not exist"
    ALL_CHECKS_PASSED=false
fi
echo ""

# Check 5: Container health status
echo -e "${BLUE}[Check 5/5]${NC} Checking Docker health status..."
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' resume_analysis_keycloak 2>/dev/null || echo "unknown")

case "$HEALTH_STATUS" in
    "healthy")
        echo -e "${GREEN}✓ PASS${NC} - Docker health check: healthy"
        ;;
    "starting")
        echo -e "${YELLOW}⚠ WARN${NC} - Docker health check: starting (container is initializing)"
        ;;
    "unhealthy")
        echo -e "${RED}✗ FAIL${NC} - Docker health check: unhealthy"
        ALL_CHECKS_PASSED=false
        ;;
    *)
        echo -e "${YELLOW}⚠ INFO${NC} - Docker health check: $HEALTH_STATUS"
        ;;
esac
echo ""

# Final summary
echo "========================================"
if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo -e "${GREEN}All Critical Checks Passed${NC}"
    echo "========================================"
    echo ""
    echo "✓ Keycloak is running and healthy"
    echo ""
    echo "Access Keycloak at:"
    echo "  - Admin Console:  http://localhost:8080/admin"
    echo "  - Health:         http://localhost:8080/health/ready"
    echo "  - Metrics:        http://localhost:8080/metrics"
    echo ""
    echo "Default credentials:"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    echo "⚠️  IMPORTANT: Change admin password in production!"
    echo ""
    exit 0
else
    echo -e "${RED}Some Checks Failed${NC}"
    echo "========================================"
    echo ""
    echo "Troubleshooting steps:"
    echo ""
    echo "1. Check Keycloak logs:"
    echo "   docker logs -f --tail 50 resume_analysis_keycloak"
    echo ""
    echo "2. Restart Keycloak:"
    echo "   docker-compose restart keycloak"
    echo ""
    echo "3. Verify PostgreSQL:"
    echo "   docker exec -it resume_analysis_db psql -U postgres -l"
    echo ""
    echo "4. Check port conflicts:"
    echo "   lsof -i :8080"
    echo ""
    echo "5. Recreate Keycloak container (WARNING: loses config):"
    echo "   docker-compose down keycloak"
    echo "   docker rm -f resume_analysis_keycloak"
    echo "   docker-compose up -d keycloak"
    echo ""
    exit 1
fi
