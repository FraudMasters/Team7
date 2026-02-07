#!/bin/bash
# Verification script for Keycloak realm, clients, and roles (subtask-1-4)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
REALM_NAME="agenthr"
FRONTEND_CLIENT_ID="agenthr-frontend"
BACKEND_CLIENT_ID="agenthr-backend"

echo "========================================"
echo "Keycloak Configuration Verification"
echo "Subtask 1-4"
echo "========================================"
echo ""

# Track overall status
ALL_CHECKS_PASSED=true

# Function to get admin token
get_admin_token() {
    local token=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$ADMIN_USER" \
        -d "password=$ADMIN_PASSWORD" \
        -d "grant_type=password" \
        -d "client_id=admin-cli" | jq -r '.access_token')

    if [ "$token" = "null" ] || [ -z "$token" ]; then
        echo -e "${RED}Failed to get admin token${NC}"
        exit 1
    fi

    echo "$token"
}

# Check 1: Keycloak is available
echo -e "${BLUE}[Check 1/6]${NC} Checking Keycloak availability..."
if curl -f -s "$KEYCLOAK_URL/health/ready" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Keycloak is available at $KEYCLOAK_URL"
else
    echo -e "${RED}✗ FAIL${NC} - Keycloak is not available"
    echo ""
    echo "Please ensure Keycloak is running:"
    echo "  bash scripts/start-keycloak.sh"
    exit 1
fi
echo ""

# Get admin token
ADMIN_TOKEN=$(get_admin_token)

# Check 2: Realm exists
echo -e "${BLUE}[Check 2/6]${NC} Checking if realm '$REALM_NAME' exists..."
REALM_EXISTS=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -e ".[] | select(.realm == \"$REALM_NAME\")" > /dev/null && echo "true" || echo "false")

if [ "$REALM_EXISTS" = "true" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Realm '$REALM_NAME' exists"

    # Get realm details
    REALM_ENABLED=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.enabled')

    if [ "$REALM_ENABLED" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Realm is enabled"
    else
        echo -e "${RED}✗ FAIL${NC} - Realm is disabled"
        ALL_CHECKS_PASSED=false
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Realm '$REALM_NAME' does not exist"
    ALL_CHECKS_PASSED=false
    echo ""
    echo "Run the setup script to create the realm:"
    echo "  bash scripts/setup-keycloak-realm.sh"
fi
echo ""

if [ "$REALM_EXISTS" != "true" ]; then
    echo "Skipping remaining checks as realm does not exist."
    exit 1
fi

# Check 3: Frontend client exists
echo -e "${BLUE}[Check 3/6]${NC} Checking if frontend client exists..."
FRONTEND_CLIENT=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients?clientId=$FRONTEND_CLIENT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

FRONTEND_CLIENT_EXISTS=$(echo "$FRONTEND_CLIENT" | jq -e '.[0]' > /dev/null && echo "true" || echo "false")

if [ "$FRONTEND_CLIENT_EXISTS" = "true" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Frontend client '$FRONTEND_CLIENT_ID' exists"

    # Check client configuration
    FRONTEND_ENABLED=$(echo "$FRONTEND_CLIENT" | jq -r '.[0].enabled')
    FRONTEND_PUBLIC=$(echo "$FRONTEND_CLIENT" | jq -r '.[0].publicClient')
    FRONTEND_REDIRECT=$(echo "$FRONTEND_CLIENT" | jq -r '.[0].redirectUris[0]')

    if [ "$FRONTEND_ENABLED" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Frontend client is enabled"
    else
        echo -e "${RED}✗ FAIL${NC} - Frontend client is disabled"
        ALL_CHECKS_PASSED=false
    fi

    if [ "$FRONTEND_PUBLIC" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Frontend client is public"
    else
        echo -e "${RED}✗ FAIL${NC} - Frontend client should be public"
        ALL_CHECKS_PASSED=false
    fi

    echo "  Redirect URI: $FRONTEND_REDIRECT"
else
    echo -e "${RED}✗ FAIL${NC} - Frontend client '$FRONTEND_CLIENT_ID' does not exist"
    ALL_CHECKS_PASSED=false
fi
echo ""

# Check 4: Backend client exists
echo -e "${BLUE}[Check 4/6]${NC} Checking if backend client exists..."
BACKEND_CLIENT=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients?clientId=$BACKEND_CLIENT_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN")

BACKEND_CLIENT_EXISTS=$(echo "$BACKEND_CLIENT" | jq -e '.[0]' > /dev/null && echo "true" || echo "false")

if [ "$BACKEND_CLIENT_EXISTS" = "true" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Backend client '$BACKEND_CLIENT_ID' exists"

    # Check client configuration
    BACKEND_ENABLED=$(echo "$BACKEND_CLIENT" | jq -r '.[0].enabled')
    BACKEND_PUBLIC=$(echo "$BACKEND_CLIENT" | jq -r '.[0].publicClient')
    BACKEND_SERVICE_ACCOUNT=$(echo "$BACKEND_CLIENT" | jq -r '.[0].serviceAccountsEnabled')

    if [ "$BACKEND_ENABLED" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Backend client is enabled"
    else
        echo -e "${RED}✗ FAIL${NC} - Backend client is disabled"
        ALL_CHECKS_PASSED=false
    fi

    if [ "$BACKEND_PUBLIC" = "false" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Backend client is confidential"
    else
        echo -e "${RED}✗ FAIL${NC} - Backend client should be confidential"
        ALL_CHECKS_PASSED=false
    fi

    if [ "$BACKEND_SERVICE_ACCOUNT" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Backend client has service accounts enabled"
    else
        echo -e "${YELLOW}⚠ WARN${NC} - Backend client should have service accounts enabled"
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Backend client '$BACKEND_CLIENT_ID' does not exist"
    ALL_CHECKS_PASSED=false
fi
echo ""

# Check 5: Roles exist
echo -e "${BLUE}[Check 5/6]${NC} Checking if required roles exist..."
REQUIRED_ROLES=("Admin" "Recruiter" "Viewer")
ALL_ROLES_EXIST=true

for role in "${REQUIRED_ROLES[@]}"; do
    ROLE_EXISTS=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles/$role" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -e '.name' > /dev/null && echo "true" || echo "false")

    if [ "$ROLE_EXISTS" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Role '$role' exists"
    else
        echo -e "${RED}✗ FAIL${NC} - Role '$role' does not exist"
        ALL_ROLES_EXIST=false
        ALL_CHECKS_PASSED=false
    fi
done
echo ""

# Check 6: Default admin user exists
echo -e "${BLUE}[Check 6/6]${NC} Checking if default admin user exists..."
ADMIN_USER_EXISTS=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=admin" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -e '.[0]' > /dev/null && echo "true" || echo "false")

if [ "$ADMIN_USER_EXISTS" = "true" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Admin user exists"

    # Check if user is enabled
    USER_ENABLED=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=admin" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].enabled')

    if [ "$USER_ENABLED" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Admin user is enabled"
    else
        echo -e "${RED}✗ FAIL${NC} - Admin user is disabled"
        ALL_CHECKS_PASSED=false
    fi

    # Check if user has Admin role
    USER_ID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=admin" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')

    USER_ROLES=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users/$USER_ID/role-mappings/realm" \
        -H "Authorization: Bearer $ADMIN_TOKEN")

    HAS_ADMIN_ROLE=$(echo "$USER_ROLES" | jq -e '.[] | select(.name == "Admin")' > /dev/null && echo "true" || echo "false")

    if [ "$HAS_ADMIN_ROLE" = "true" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Admin user has Admin role"
    else
        echo -e "${YELLOW}⚠ WARN${NC} - Admin user does not have Admin role"
    fi
else
    echo -e "${YELLOW}⚠ INFO${NC} - Admin user does not exist (optional)"
fi
echo ""

# Final summary
echo "========================================"
if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo -e "${GREEN}All Critical Checks Passed${NC}"
    echo "========================================"
    echo ""
    echo "✓ Realm: $REALM_NAME"
    echo "✓ Frontend Client: $FRONTEND_CLIENT_ID (Public)"
    echo "✓ Backend Client: $BACKEND_CLIENT_ID (Confidential)"
    echo "✓ Roles: Admin, Recruiter, Viewer"
    echo ""
    echo "Configuration is ready for:"
    echo "  - Backend integration (subtask 2-1 onwards)"
    echo "  - Frontend integration (subtask 3-1 onwards)"
    echo ""
    echo "Access Admin Console:"
    echo "  $KEYCLOAK_URL/admin"
    echo "  Realm: $REALM_NAME"
    echo ""
    echo "Default credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""
    exit 0
else
    echo -e "${RED}Some Checks Failed${NC}"
    echo "========================================"
    echo ""
    echo "To fix issues, run:"
    echo "  bash scripts/setup-keycloak-realm.sh"
    echo ""
    echo "Or manually configure in the Admin Console:"
    echo "  $KEYCLOAK_URL/admin"
    echo ""
    exit 1
fi
