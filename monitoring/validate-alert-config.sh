#!/bin/bash

# Alert Rules Configuration Validation Script
# Validates alert rules configuration without requiring running services

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Alert Rules Configuration Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ALERT_RULES_FILE="monitoring/grafana/provisioning/alerts/alert_rules.yml"
CONTACTPOINTS_FILE="monitoring/grafana/provisioning/alerting/contactpoints.yml"

# Expected counts
EXPECTED_GROUPS=5
EXPECTED_RULES=16

echo -e "${BLUE}[1/6] Checking alert rules file exists...${NC}"
if [ -f "$ALERT_RULES_FILE" ]; then
    echo -e "${GREEN}✓ File exists: $ALERT_RULES_FILE${NC}"
else
    echo -e "${RED}✗ File not found: $ALERT_RULES_FILE${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[2/6] Validating alert groups...${NC}"
GROUP_COUNT=$(grep -c "^  - name:" "$ALERT_RULES_FILE" || echo "0")
echo -e "Found ${GREEN}$GROUP_COUNT${NC} alert groups (expected: $EXPECTED_GROUPS)"

if [ "$GROUP_COUNT" -eq "$EXPECTED_GROUPS" ]; then
    echo -e "${GREEN}✓ Correct number of alert groups${NC}"
else
    echo -e "${YELLOW}⚠ Expected $EXPECTED_GROUPS groups, found $GROUP_COUNT${NC}"
fi

# List groups
echo ""
echo "Alert groups:"
grep "^  - name:" "$ALERT_RULES_FILE" | sed 's/^  - name: /  - /'
echo ""

echo -e "${BLUE}[3/6] Validating alert rules...${NC}"
RULE_COUNT=$(grep -c "^      - alert:" "$ALERT_RULES_FILE" || echo "0")
echo -e "Found ${GREEN}$RULE_COUNT${NC} alert rules (expected: $EXPECTED_RULES)"

if [ "$RULE_COUNT" -eq "$EXPECTED_RULES" ]; then
    echo -e "${GREEN}✓ Correct number of alert rules${NC}"
else
    echo -e "${YELLOW}⚠ Expected $EXPECTED_RULES rules, found $RULE_COUNT${NC}"
fi

# List all alerts
echo ""
echo "Alert rules:"
grep "^      - alert:" "$ALERT_RULES_FILE" | sed 's/^      - alert: /  - /'
echo ""

echo -e "${BLUE}[4/6] Validating alert rule structure...${NC}"
VALIDATION_ERRORS=0

# Check that each alert has required fields
while IFS= read -r line; do
    if [[ $line =~ ^[[:space:]]*- alert:[[:space:]]*(.+)$ ]]; then
        alert_name="${BASH_REMATCH[1]}"
        echo -n "  Checking '$alert_name'... "

        # Extract the alert block (next 20 lines)
        ALERT_BLOCK=$(grep -A 20 "^      - alert: $alert_name$" "$ALERT_RULES_FILE")

        # Check for required fields
        if echo "$ALERT_BLOCK" | grep -q "expr:"; then
            if echo "$ALERT_BLOCK" | grep -q "for:"; then
                if echo "$ALERT_BLOCK" | grep -q "labels:"; then
                    if echo "$ALERT_BLOCK" | grep -q "annotations:"; then
                        echo -e "${GREEN}✓${NC}"
                    else
                        echo -e "${RED}✗ Missing annotations${NC}"
                        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
                    fi
                else
                    echo -e "${RED}✗ Missing labels${NC}"
                    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
                fi
            else
                echo -e "${RED}✗ Missing 'for' duration${NC}"
                VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
            fi
        else
            echo -e "${RED}✗ Missing expression${NC}"
            VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
        fi
    fi
done < "$ALERT_RULES_FILE"

if [ $VALIDATION_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All alert rules have valid structure${NC}"
else
    echo -e "${RED}✗ Found $VALIDATION_ERRORS validation errors${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[5/6] Checking contact points configuration...${NC}"
if [ -f "$CONTACTPOINTS_FILE" ]; then
    echo -e "${GREEN}✓ Contact points file exists${NC}"

    CONTACT_COUNT=$(grep -c "^  - name:" "$CONTACTPOINTS_FILE" || echo "0")
    echo -e "Found ${GREEN}$CONTACT_COUNT${NC} notification channels"

    # List notification channels
    echo ""
    echo "Notification channels:"
    grep "^  - name:" "$CONTACTPOINTS_FILE" | sed 's/^  - name: /  - /'
    echo ""

    # Check for email configuration
    if grep -q "type: email" "$CONTACTPOINTS_FILE"; then
        echo -e "${GREEN}✓ Email channel configured${NC}"
    else
        echo -e "${YELLOW}⚠ Email channel not found${NC}"
    fi

    # Check for webhook configuration
    if grep -q "type: webhook" "$CONTACTPOINTS_FILE"; then
        echo -e "${GREEN}✓ Webhook channel configured${NC}"
    else
        echo -e "${YELLOW}⚠ Webhook channel not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Contact points file not found: $CONTACTPOINTS_FILE${NC}"
fi
echo ""

echo -e "${BLUE}[6/6] Checking alert rule categories...${NC}"
# Count alerts by severity
WARNING_COUNT=$(grep -A 5 "^      - alert:" "$ALERT_RULES_FILE" | grep -c "severity: warning" || echo "0")
CRITICAL_COUNT=$(grep -A 5 "^      - alert:" "$ALERT_RULES_FILE" | grep -c "severity: critical" || echo "0")

echo -e "Warning alerts: ${GREEN}${WARNING_COUNT}${NC}"
echo -e "Critical alerts: ${RED}${CRITICAL_COUNT}${NC}"
echo -e "Total: $((WARNING_COUNT + CRITICAL_COUNT))"

# Count by category
echo ""
echo "Alerts by category:"
for category in api celery ml database system; do
    COUNT=$(grep -A 5 "^      - alert:" "$ALERT_RULES_FILE" | grep "category: $category" | wc -l | tr -d ' ')
    if [ "$COUNT" -gt 0 ]; then
        echo -e "  $category: ${GREEN}${COUNT}${NC}"
    fi
done
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $VALIDATION_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Configuration validation PASSED${NC}"
    echo ""
    echo "Configuration is valid and ready for deployment."
    echo ""
    echo "Next Steps:"
    echo "  1. Start services: docker-compose up -d"
    echo "  2. Run verification: ./monitoring/verify-alert-rules.sh"
    echo "  3. Test notifications in Grafana UI"
    echo "  4. Follow testing guide: ALERT_RULES_TESTING_GUIDE.md"
    echo ""
else
    echo -e "${RED}✗ Configuration validation FAILED${NC}"
    echo ""
    echo "Please fix the validation errors above."
    exit 1
fi
