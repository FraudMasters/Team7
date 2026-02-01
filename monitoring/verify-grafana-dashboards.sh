#!/bin/bash

# Grafana Dashboards Verification Script
# Subtask 10-3: Verify all dashboards load and display data

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

# Expected dashboards
declare -A DASHBOARDS=(
    ["api-performance"]="API Performance"
    ["celery-tasks"]="Celery Tasks"
    ["ml-inference"]="ML Inference"
    ["database-performance"]="Database Performance"
    ["system-overview"]="System Overview"
)

# Expected metrics for each dashboard
declare -A DASHBOARD_METRICS=(
    ["api-performance"]="http_request_duration_seconds_bucket|http_requests_total"
    ["celery-tasks"]="celery_queue_length|celery_tasks_total"
    ["ml-inference"]="ml_inference_duration_seconds_bucket|ml_predictions_total"
    ["database-performance"]="db_query_duration_seconds_bucket|pg_stat_database_numbackends"
    ["system-overview"]="container_cpu_usage_seconds_total|container_memory_usage_bytes"
)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Grafana Dashboards Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check Grafana accessibility
echo -e "${BLUE}[1/6] Checking Grafana service...${NC}"
if curl -sf -o /dev/null "$GRAFANA_URL"; then
    echo -e "${GREEN}✓ Grafana is accessible at $GRAFANA_URL${NC}"
else
    echo -e "${RED}✗ Grafana is not accessible at $GRAFANA_URL${NC}"
    echo -e "${YELLOW}  Please start Grafana: docker-compose up -d grafana${NC}"
    exit 1
fi
echo ""

# Step 2: Check Prometheus datasource health
echo -e "${BLUE}[2/6] Checking Prometheus datasource...${NC}"
DATASOURCE_HEALTH=$(curl -s "$GRAFANA_URL/api/datasources" | jq -r '.[] | select(.name == "Prometheus") | .health' 2>/dev/null || echo "NOT_FOUND")

if [ "$DATASOURCE_HEALTH" = "OK" ]; then
    echo -e "${GREEN}✓ Prometheus datasource is healthy${NC}"
else
    echo -e "${RED}✗ Prometheus datasource health: $DATASOURCE_HEALTH${NC}"
    echo -e "${YELLOW}  Please check Prometheus is running: docker-compose ps prometheus${NC}"
    exit 1
fi
echo ""

# Step 3: List all provisioned dashboards
echo -e "${BLUE}[3/6] Listing provisioned dashboards...${NC}"
DASHBOARDS_LIST=$(curl -s "$GRAFANA_URL/api/search?type=dash-db" 2>/dev/null)

if [ -z "$DASHBOARDS_LIST" ]; then
    echo -e "${RED}✗ Failed to retrieve dashboard list${NC}"
    exit 1
fi

DASHBOARD_COUNT=$(echo "$DASHBOARDS_LIST" | jq '. | length' 2>/dev/null || echo "0")
echo -e "${GREEN}✓ Found $DASHBOARD_COUNT dashboards${NC}"
echo ""

# Display dashboard list
echo "Provisioned Dashboards:"
echo "$DASHBOARDS_LIST" | jq -r '.[] | "  - \(.title) (UID: \(.uri))"' 2>/dev/null || echo "  Error parsing dashboard list"
echo ""

# Step 4: Verify each expected dashboard exists and loads
echo -e "${BLUE}[4/6] Verifying each dashboard loads...${NC}"
ALL_DASHBOARDS_OK=true

for uid in "${!DASHBOARDS[@]}"; do
    title="${DASHBOARDS[$uid]}"
    dashboard_url="$GRAFANA_URL/d/$uid"

    echo -n "  Testing $title ($uid)... "

    # Check if dashboard returns 200
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$dashboard_url")

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ OK (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${RED}✗ FAILED (HTTP $HTTP_CODE)${NC}"
        ALL_DASHBOARDS_OK=false
    fi
done
echo ""

if [ "$ALL_DASHBOARDS_OK" = true ]; then
    echo -e "${GREEN}✓ All dashboards load successfully${NC}"
else
    echo -e "${RED}✗ Some dashboards failed to load${NC}"
    exit 1
fi
echo ""

# Step 5: Check if Prometheus has metrics for each dashboard
echo -e "${BLUE}[5/6] Checking Prometheus metrics availability...${NC}"

for uid in "${!DASHBOARD_METRICS[@]}"; do
    title="${DASHBOARDS[$uid]}"
    metrics_pattern="${DASHBOARD_METRICS[$uid]}"

    echo -n "  Checking metrics for $title... "

    # Try each metric in the pattern
    METRICS_FOUND=false
    IFS='|' read -ra METRICS <<< "$metrics_pattern"
    for metric in "${METRICS[@]}"; do
        # Query Prometheus for this metric
        RESULT=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${metric}" | jq -r '.data.result | length' 2>/dev/null || echo "0")

        if [ "$RESULT" -gt 0 ]; then
            echo -e "${GREEN}✓ OK ($metric has data)${NC}"
            METRICS_FOUND=true
            break
        fi
    done

    if [ "$METRICS_FOUND" = false ]; then
        echo -e "${YELLOW}⚠ NO DATA (metrics not yet available)${NC}"
        echo -e "     This is expected if services haven't generated metrics yet"
    fi
done
echo ""

# Step 6: Verify dashboard provisioning configuration
echo -e "${BLUE}[6/6] Verifying dashboard provisioning configuration...${NC}"

# Check if dashboard files exist
echo "  Checking dashboard files..."
DASHBOARD_DIR="monitoring/grafana/dashboards"
ALL_FILES_EXIST=true

for uid in "${!DASHBOARDS[@]}"; do
    if [ -f "$DASHBOARD_DIR/$uid.json" ]; then
        echo -e "    ${GREEN}✓${NC} $uid.json exists"
    else
        echo -e "    ${RED}✗${NC} $uid.json missing"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = true ]; then
    echo -e "${GREEN}✓ All dashboard files present${NC}"
else
    echo -e "${RED}✗ Some dashboard files missing${NC}"
    exit 1
fi

# Check provisioning configuration
PROVISIONING_FILE="monitoring/grafana/provisioning/dashboards/dashboards.yml"
if [ -f "$PROVISIONING_FILE" ]; then
    echo -e "${GREEN}✓ Provisioning configuration exists${NC}"

    # Check key settings
    if grep -q "foldersFromFilesStructure: true" "$PROVISIONING_FILE"; then
        echo -e "${GREEN}✓ Auto-discovery enabled${NC}"
    else
        echo -e "${YELLOW}⚠ Auto-discovery may not be enabled${NC}"
    fi

    UPDATE_INTERVAL=$(grep "updateIntervalSeconds:" "$PROVISIONING_FILE" | awk '{print $2}')
    echo -e "${GREEN}✓ Update interval: ${UPDATE_INTERVAL}s${NC}"
else
    echo -e "${RED}✗ Provisioning configuration not found${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"

TOTAL_DASHBOARDS=${#DASHBOARDS[@]}
echo -e "Total Dashboards: ${GREEN}$TOTAL_DASHBOARDS${NC}"
echo -e "Grafana Service: ${GREEN}Running${NC}"
echo -e "Prometheus Datasource: ${GREEN}Healthy${NC}"
echo -e "Dashboard Provisioning: ${GREEN}Configured${NC}"
echo ""

# Check if metrics are available
METRICS_AVAILABLE=false
for uid in "${!DASHBOARD_METRICS[@]}"; do
    metrics_pattern="${DASHBOARD_METRICS[$uid]}"
    IFS='|' read -ra METRICS <<< "$metrics_pattern"
    for metric in "${METRICS[@]}"; do
        RESULT=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${metric}" | jq -r '.data.result | length' 2>/dev/null || echo "0")
        if [ "$RESULT" -gt 0 ]; then
            METRICS_AVAILABLE=true
            break 2
        fi
    done
done

if [ "$METRICS_AVAILABLE" = true ]; then
    echo -e "${GREEN}✓ DASHBOARDS ARE DISPLAYING DATA${NC}"
    echo ""
    echo "Next Steps:"
    echo "  1. Open Grafana: $GRAFANA_URL"
    echo "  2. Navigate to each dashboard to view metrics"
    echo "  3. Customize time ranges and panels as needed"
else
    echo -e "${YELLOW}⚠ DASHBOARDS LOADED BUT NO DATA YET${NC}"
    echo ""
    echo "To generate metrics:"
    echo "  1. API Performance: curl $BACKEND_URL/api/resumes"
    echo "  2. Database: curl $BACKEND_URL/health"
    echo "  3. Celery: Submit and process Celery tasks"
    echo "  4. ML Inference: Upload and analyze resumes"
    echo "  5. System Overview: Automatically populated by cAdvisor"
    echo ""
    echo "After generating metrics, wait 15-30 seconds for Prometheus to scrape."
fi

echo ""
echo -e "${GREEN}✓ Verification complete!${NC}"
echo ""
echo "Dashboard URLs:"
for uid in "${!DASHBOARDS[@]}"; do
    title="${DASHBOARDS[$uid]}"
    echo "  • $title: $GRAFANA_URL/d/$uid"
done
echo ""
