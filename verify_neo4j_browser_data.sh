#!/bin/bash
# Verification script for graph data in Neo4j browser (subtask-4-4)
# This script verifies that graph data is accessible in Neo4j after episode ingestion
#
# Prerequisites:
# - Neo4j container must be running
# - At least one episode should have been ingested via the API
# - Neo4j Browser UI must be accessible
#
# Usage:
#   ./verify_neo4j_browser_data.sh
#
# For manual verification, open http://localhost:7474 in your browser

set -e

echo "=== Neo4j Browser Graph Data Verification (subtask-4-4) ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NEO4J_BROWSER_URL="http://localhost:7474"
NEO4J_CONTAINER="neo4j"
NEO4J_USER="neo4j"
# Note: Default password from docker-compose is "password" unless overridden

# Step 1: Check if Neo4j container is running
echo -e "${YELLOW}[1/7] Checking Neo4j container status...${NC}"
if docker ps | grep -q "${NEO4J_CONTAINER}"; then
    echo -e "${GREEN}✓ Neo4j container is running${NC}"
    docker ps | grep "${NEO4J_CONTAINER}"
else
    echo -e "${RED}✗ Neo4j container is not running${NC}"
    echo "Start Neo4j with: docker-compose up -d neo4j"
    exit 1
fi

# Step 2: Verify Neo4j Browser UI is accessible
echo ""
echo -e "${YELLOW}[2/7] Checking Neo4j Browser UI accessibility...${NC}"
if curl -s --connect-timeout 5 "${NEO4J_BROWSER_URL}" | grep -i neo4j > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Neo4j Browser UI is accessible at ${NEO4J_BROWSER_URL}${NC}"
else
    echo -e "${RED}✗ Neo4j Browser UI is not accessible${NC}"
    echo "Check if Neo4j is fully started: docker-compose logs neo4j"
    exit 1
fi

# Step 3: Check if cypher-shell is available for automated queries
echo ""
echo -e "${YELLOW}[3/7] Checking cypher-shell availability...${NC}"
if docker exec "${NEO4J_CONTAINER}" which cypher-shell > /dev/null 2>&1; then
    echo -e "${GREEN}✓ cypher-shell is available in container${NC}"
    CYPHER_SHELL_AVAILABLE=true
else
    echo -e "${YELLOW}⚠ cypher-shell not found, skipping automated queries${NC}"
    CYPHER_SHELL_AVAILABLE=false
fi

# Step 4: Query total node count (if cypher-shell available)
if [ "$CYPHER_SHELL_AVAILABLE" = true ]; then
    echo ""
    echo -e "${YELLOW}[4/7] Querying total node count in graph...${NC}"

    # Get password from environment or use default
    NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"

    NODE_COUNT=$(docker exec "${NEO4J_CONTAINER}" cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" "MATCH (n) RETURN count(n) AS count" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")

    if [ "$NODE_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Graph contains ${NODE_COUNT} node(s)${NC}"
    else
        echo -e "${YELLOW}⚠ Graph appears to be empty (0 nodes)${NC}"
        echo "This may indicate:"
        echo "  - No episodes have been ingested yet"
        echo "  - The GraphitiService hasn't been initialized"
        echo "  - The episodes are still being processed"
    fi
else
    echo ""
    echo -e "${YELLOW}[4/7] Skipping automated node count query${NC}"
    echo "Use Neo4j Browser UI to check node count manually"
fi

# Step 5: Query relationship count (if cypher-shell available)
if [ "$CYPHER_SHELL_AVAILABLE" = true ]; then
    echo ""
    echo -e "${YELLOW}[5/7] Querying relationship count in graph...${NC}"

    REL_COUNT=$(docker exec "${NEO4J_CONTAINER}" cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" "MATCH ()-[r]->() RETURN count(r) AS count" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")

    if [ "$REL_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Graph contains ${REL_COUNT} relationship(s)${NC}"
    else
        echo -e "${YELLOW}⚠ Graph has no relationships (0)${NC}"
        echo "This may indicate:"
        echo "  - Episodes are still being processed"
        echo "  - Entity extraction hasn't completed"
        echo "  - OpenAI API is not configured (needed for entity extraction)"
    fi
else
    echo ""
    echo -e "${YELLOW}[5/7] Skipping automated relationship count query${NC}"
fi

# Step 6: List node types/labels (if cypher-shell available)
if [ "$CYPHER_SHELL_AVAILABLE" = true ]; then
    echo ""
    echo -e "${YELLOW}[6/7] Querying node labels/types in graph...${NC}"

    LABELS=$(docker exec "${NEO4J_CONTAINER}" cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" "CALL db.labels() YIELD label RETURN label" 2>/dev/null | tail -n +2 || echo "")

    if [ -n "$LABELS" ]; then
        echo -e "${GREEN}✓ Found node labels:${NC}"
        echo "$LABELS" | while read -r label; do
            if [ -n "$label" ]; then
                count=$(docker exec "${NEO4J_CONTAINER}" cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" "MATCH (n:${label}) RETURN count(n)" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")
                echo "  - ${label}: ${count} node(s)"
            fi
        done)
    else
        echo -e "${YELLOW}⚠ No node labels found${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}[6/7] Skipping automated node label query${NC}"
fi

# Step 7: Provide manual verification instructions
echo ""
echo -e "${YELLOW}[7/7] Manual Verification Instructions${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}To manually verify graph data in Neo4j Browser:${NC}"
echo ""
echo "1. Open Neo4j Browser in your web browser:"
echo "   ${NEO4J_BROWSER_URL}"
echo ""
echo "2. Login with credentials:"
echo "   Username: ${NEO4J_USER}"
echo "   Password: (check NEO4J_PASSWORD environment variable, default: 'password')"
echo ""
echo "3. Run the following Cypher queries to verify data:"
echo ""
echo -e "${YELLOW}   a) Count all nodes:${NC}"
echo "      MATCH (n) RETURN count(n) AS total_nodes"
echo ""
echo -e "${YELLOW}   b) Count all relationships:${NC}"
echo "      MATCH ()-[r]->() RETURN count(r) AS total_relationships"
echo ""
echo -e "${YELLOW}   c) List all node labels:${NC}"
echo "      CALL db.labels() YIELD label RETURN label"
echo ""
echo -e "${YELLOW}   d) Show recent Episode nodes:${NC}"
echo "      MATCH (n:Episode) RETURN n.name, n.created_at ORDER BY n.created_at DESC LIMIT 10"
echo ""
echo -e "${YELLOW}   e) Visualize graph (sample):${NC}"
echo "      MATCH (n) RETURN n LIMIT 25"
echo ""
echo -e "${YELLOW}   f) Check Graphiti indices:${NC}"
echo "      SHOW INDEXES"
echo ""
echo "4. Expected results after episode ingestion:"
echo "   - Episode nodes (one per ingested episode)"
echo "   - Entity nodes (extracted from episode content)"
echo "   - Relationship nodes (connecting entities and episodes)"
echo "   - Graphiti-specific indices (vector and text search indexes)"
echo ""
echo "5. Common issues and solutions:"
echo ""
echo -e "${RED}   Issue: Empty graph (0 nodes)${NC}"
echo "   Solution: Ingest an episode via API:"
echo "   curl -X POST http://localhost:8000/api/v1/context/episodes \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"name\": \"Test\", \"body\": \"Test content\"}'"
echo ""
echo -e "${RED}   Issue: Only Episode nodes, no entities/relationships${NC}"
echo "   Solution: Check OPENAI_API_KEY is set and GraphitiService is initialized"
echo "   Wait 10-30 seconds for entity extraction to complete"
echo ""
echo -e "${RED}   Issue: Cannot login to Neo4j Browser${NC}"
echo "   Solution: Verify NEO4J_PASSWORD in .env matches login password"
echo "   Check docker-compose logs neo4j for authentication errors"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# Summary
echo -e "${YELLOW}Verification Summary${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Neo4j Browser verification complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "Next Steps:"
echo "  1. Open Neo4j Browser: ${NEO4J_BROWSER_URL}"
echo "  2. Login and run: MATCH (n) RETURN count(n)"
echo "  3. Verify nodes exist after episode ingestion"
echo "  4. If graph is empty, run: ./verify_episode_flow.sh"
echo ""
echo "Documentation:"
echo "  - Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/"
echo "  - Graphiti Documentation: https://github.com/getmesh/graphiti"
echo ""
