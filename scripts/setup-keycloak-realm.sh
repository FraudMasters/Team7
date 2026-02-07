#!/bin/bash
# Setup Keycloak realm, clients, and roles for subtask-1-4
# This script automates the creation of the agenthr realm and all required configuration

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
FRONTEND_REDIRECT_URI="http://localhost:5173/*"
BACKEND_REDIRECT_URI="http://localhost:8000/*"

echo "========================================"
echo "Keycloak Realm Setup"
echo "Subtask 1-4"
echo "========================================"
echo ""

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

# Function to check if realm exists
realm_exists() {
    local token=$1
    local response=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms" \
        -H "Authorization: Bearer $token")

    if echo "$response" | jq -e ".[] | select(.realm == \"$REALM_NAME\")" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to create realm
create_realm() {
    local token=$1

    echo "Creating realm: $REALM_NAME"

    local response=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{
            \"realm\": \"$REALM_NAME\",
            \"enabled\": true,
            \"displayName\": \"AgentHR\",
            \"registrationAllowed\": true,
            \"loginWithEmailAllowed\": true,
            \"duplicateEmailsAllowed\": false,
            \"resetPasswordAllowed\": true,
            \"editUsernameAllowed\": false,
            \"bruteForceProtected\": true,
            \"sslRequired\": \"external\",
            \"roles\": {
                \"realm\": {
                    \"Admin\": {},
                    \"Recruiter\": {},
                    \"Viewer\": {}
                }
            }
        }")

    if [ -z "$response" ]; then
        echo -e "${GREEN}✓ Realm created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create realm${NC}"
        echo "Response: $response"
        exit 1
    fi
}

# Function to create frontend client
create_frontend_client() {
    local token=$1

    echo "Creating frontend client: $FRONTEND_CLIENT_ID"

    local response=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{
            \"clientId\": \"$FRONTEND_CLIENT_ID\",
            \"name\": \"AgentHR Frontend\",
            \"description\": \"AgentHR Frontend Application\",
            \"enabled\": true,
            \"clientAuthenticatorType\": \"public-client\",
            \"redirectUris\": [\"$FRONTEND_REDIRECT_URI\"],
            \"webOrigins\": [\"http://localhost:5173\"],
            \"bearerOnly\": false,
            \"consentRequired\": false,
            \"standardFlowEnabled\": true,
            \"implicitFlowEnabled\": false,
            \"directAccessGrantsEnabled\": false,
            \"serviceAccountsEnabled\": false,
            \"publicClient\": true,
            \"protocol\": \"openid-connect\",
            \"attributes\": {
                \"access.token.lifespan\": \"300\"
            },
            \"fullScopeAllowed\": true,
            \"protocolMappers\": [
                {
                    \"name\": \"realm roles\",
                    \"protocol\": \"openid-connect\",
                    \"protocolMapper\": \"oidc-usermodel-realm-role-mapper\",
                    \"consentRequired\": false,
                    \"config\": {
                        \"multivalued\": \"true\",
                        \"userinfo.token.claim\": \"true\",
                        \"id.token.claim\": \"true\",
                        \"access.token.claim\": \"true\",
                        \"claim.name\": \"roles\",
                        \"jsonType.label\": \"String\"
                    }
                }
            ]
        }")

    if [ -z "$response" ]; then
        echo -e "${GREEN}✓ Frontend client created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create frontend client${NC}"
        echo "Response: $response"
        exit 1
    fi
}

# Function to create backend client
create_backend_client() {
    local token=$1

    echo "Creating backend client: $BACKEND_CLIENT_ID"

    local response=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{
            \"clientId\": \"$BACKEND_CLIENT_ID\",
            \"name\": \"AgentHR Backend\",
            \"description\": \"AgentHR Backend API\",
            \"enabled\": true,
            \"clientAuthenticatorType\": \"client-secret\",
            \"secret\": \"changeme-in-production\",
            \"redirectUris\": [\"$BACKEND_REDIRECT_URI\"],
            \"webOrigins\": [\"http://localhost:8000\"],
            \"bearerOnly\": false,
            \"consentRequired\": false,
            \"standardFlowEnabled\": false,
            \"implicitFlowEnabled\": false,
            \"directAccessGrantsEnabled\": true,
            \"serviceAccountsEnabled\": true,
            \"publicClient\": false,
            \"protocol\": \"openid-connect\",
            \"attributes\": {
                \"access.token.lifespan\": \"60\"
            },
            \"fullScopeAllowed\": true,
            \"authorizationServicesEnabled\": true
        }")

    if [ -z "$response" ]; then
        echo -e "${GREEN}✓ Backend client created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create backend client${NC}"
        echo "Response: $response"
        exit 1
    fi
}

# Function to get client ID by client_id
get_client_id() {
    local token=$1
    local client_id=$2

    local response=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients?clientId=$client_id" \
        -H "Authorization: Bearer $token")

    echo "$response" | jq -r '.[0].id'
}

# Function to create realm roles
create_realm_roles() {
    local token=$1

    echo "Creating realm roles: Admin, Recruiter, Viewer"

    for role in "Admin" "Recruiter" "Viewer"; do
        local response=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"$role\",
                \"description\": \"$role role for AgentHR\",
                \"composite\": false,
                \"clientRole\": false,
                \"containerId\": \"$REALM_NAME\"
            }")

        if [ -z "$response" ]; then
            echo -e "${GREEN}✓ Role '$role' created successfully${NC}"
        else
            echo -e "${YELLOW}⚠ Role '$role' may already exist or creation failed${NC}"
            echo "Response: $response"
        fi
    done
}

# Function to create default admin user
create_admin_user() {
    local token=$1

    echo "Creating default admin user (admin@agenthr.com)"

    # Check if user already exists
    local users=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=admin" \
        -H "Authorization: Bearer $token")

    if echo "$users" | jq -e '. | length > 0' > /dev/null; then
        echo -e "${YELLOW}⚠ Admin user already exists${NC}"
        return
    fi

    local response=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"admin\",
            \"email\": \"admin@agenthr.com\",
            \"firstName\": \"Admin\",
            \"lastName\": \"User\",
            \"enabled\": true,
            \"emailVerified\": true,
            \"credentials\": [{
                \"type\": \"password\",
                \"value\": \"admin123\",
                \"temporary\": false
            }]
        }")

    if [ -z "$response" ]; then
        echo -e "${GREEN}✓ Admin user created successfully${NC}"

        # Get user ID
        sleep 1
        local user_id=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=admin" \
            -H "Authorization: Bearer $token" | jq -r '.[0].id')

        # Assign Admin role
        local admin_role_id=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles/Admin" \
            -H "Authorization: Bearer $token" | jq -r '.id')

        curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users/$user_id/role-mappings/realm" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "[{
                \"id\": \"$admin_role_id\",
                \"name\": \"Admin\"
            }]" > /dev/null

        echo -e "${GREEN}✓ Admin role assigned to admin user${NC}"
    else
        echo -e "${RED}✗ Failed to create admin user${NC}"
        echo "Response: $response"
    fi
}

# Main execution
echo "Checking Keycloak availability..."
if ! curl -f -s "$KEYCLOAK_URL/health/ready" > /dev/null 2>&1; then
    echo -e "${RED}✗ Keycloak is not available at $KEYCLOAK_URL${NC}"
    echo "Please ensure Keycloak is running:"
    echo "  bash scripts/start-keycloak.sh"
    exit 1
fi

echo -e "${GREEN}✓ Keycloak is available${NC}"
echo ""

# Check for required tools
echo "Checking dependencies..."
if ! command -v jq &> /dev/null; then
    echo -e "${RED}✗ jq is required but not installed${NC}"
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi
echo -e "${GREEN}✓ All dependencies met${NC}"
echo ""

# Get admin token
echo "Authenticating as admin..."
ADMIN_TOKEN=$(get_admin_token)
echo -e "${GREEN}✓ Authenticated successfully${NC}"
echo ""

# Check if realm exists
echo "Checking if realm '$REALM_NAME' exists..."
if realm_exists "$ADMIN_TOKEN"; then
    echo -e "${YELLOW}⚠ Realm '$REALM_NAME' already exists${NC}"
    echo ""
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing realm..."
        curl -s -X DELETE "$KEYCLOAK_URL/admin/realms/$REALM_NAME" \
            -H "Authorization: Bearer $ADMIN_TOKEN"
        echo -e "${GREEN}✓ Realm deleted${NC}"
        echo ""
    else
        echo "Exiting without making changes."
        exit 0
    fi
fi

# Create realm
echo ""
echo "========================================"
echo "Creating Realm and Configuration"
echo "========================================"
echo ""
create_realm "$ADMIN_TOKEN"
sleep 1

# Create clients
echo ""
create_frontend_client "$ADMIN_TOKEN"
sleep 1

create_backend_client "$ADMIN_TOKEN"
sleep 1

# Create roles
echo ""
create_realm_roles "$ADMIN_TOKEN"
sleep 1

# Create default admin user
echo ""
create_admin_user "$ADMIN_TOKEN"

# Get backend client secret
echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Backend Client Secret:"
BACKEND_CLIENT_ID_UUID=$(get_client_id "$ADMIN_TOKEN" "$BACKEND_CLIENT_ID")
BACKEND_CLIENT_SECRET=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients/$BACKEND_CLIENT_ID_UUID/client-secret" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.value')

echo -e "${YELLOW}$BACKEND_CLIENT_SECRET${NC}"
echo ""
echo "⚠️  IMPORTANT: Save this secret and update your .env file:"
echo "   KEYCLOAK_CLIENT_SECRET=$BACKEND_CLIENT_SECRET"
echo ""
echo "========================================"
echo "Configuration Summary"
echo "========================================"
echo ""
echo "Realm: $REALM_NAME"
echo "Frontend Client: $FRONTEND_CLIENT_ID (Public)"
echo "Backend Client: $BACKEND_CLIENT_ID (Confidential)"
echo "Roles: Admin, Recruiter, Viewer"
echo ""
echo "Default Admin User:"
echo "  Username: admin"
echo "  Password: admin123"
echo "  Email: admin@agenthr.com"
echo ""
echo "Admin Console: $KEYCLOAK_URL/admin"
echo "Realm Console: $KEYCLOAK_URL/admin/master/console/#/realms/$REALM_NAME"
echo ""
echo "⚠️  SECURITY REMINDERS:"
echo "  1. Change the default admin password"
echo "  2. Update the backend client secret in .env"
echo "  3. Configure SMTP for email verification"
echo "  4. Enable SSL for production"
echo ""
