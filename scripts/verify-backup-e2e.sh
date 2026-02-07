#!/bin/bash
# End-to-End Verification Script for Backup and Disaster Recovery System
# This script verifies: Metrics → Dashboard → Alerts → Notifications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
ADMIN_USER="${GRAFANA_USER:-admin}"
ADMIN_PASSWORD="${GRAFANA_PASSWORD:-admin}"

# Test results tracking
PASSED=0
FAILED=0
SKIPPED=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((SKIPPED++))
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=${3:-30}
    local attempt=1

    log_info "Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$name is ready"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo ""
    log_error "$name failed to start"
    return 1
}

# ============================================================================
# Step 1: Verify All Services are Running
# ============================================================================
echo ""
echo "=========================================="
echo "Step 1: Verifying Services"
echo "=========================================="

check_service() {
    local url=$1
    local name=$2
    log_info "Checking $name at $url"

    if curl -s -f "$url" > /dev/null 2>&1; then
        log_success "$name is running"
        return 0
    else
        log_error "$name is not accessible"
        return 1
    fi
}

check_service "$BACKEND_URL/health" "Backend API"
check_service "$PROMETHEUS_URL/-/healthy" "Prometheus"
check_service "$GRAFANA_URL/api/health" "Grafana"

# ============================================================================
# Step 2: Trigger Manual Backup
# ============================================================================
echo ""
echo "=========================================="
echo "Step 2: Triggering Manual Backup"
echo "=========================================="

log_info "Triggering manual database backup..."

BACKUP_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/backups/create" \
    -H "Content-Type: application/json" \
    -d '{"backup_type": "database"}' 2>&1)

if echo "$BACKUP_RESPONSE" | grep -q "task_id\|backup_id\|id"; then
    log_success "Backup task initiated successfully"
    BACKUP_ID=$(echo "$BACKUP_RESPONSE" | grep -o '"task_id":"[^"]*' | cut -d'"' -f4 || echo "$BACKUP_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    log_info "Backup ID: $BACKUP_ID"
else
    log_error "Failed to trigger backup"
    log_info "Response: $BACKUP_RESPONSE"
fi

# Wait for backup to complete
log_info "Waiting for backup to complete (30 seconds)..."
sleep 30

# ============================================================================
# Step 3: Verify Backup Metrics in Prometheus
# ============================================================================
echo ""
echo "=========================================="
echo "Step 3: Verifying Backup Metrics"
echo "=========================================="

log_info "Fetching metrics from backend..."

METRICS=$(curl -s "$BACKEND_URL/metrics" 2>&1)

# Check for specific backup metrics
check_metric() {
    local metric_name=$1
    local description=$2

    if echo "$METRICS" | grep -q "^$metric_name"; then
        log_success "$description ($metric_name)"
        echo "$METRICS" | grep "^$metric_name" | head -3
        return 0
    else
        log_error "$description not found ($metric_name)"
        return 1
    fi
}

check_metric "backup_operations_total" "Backup operations counter"
check_metric "backup_failures_total" "Backup failures counter"
check_metric "backup_size_bytes" "Backup size gauge"
check_metric "backup_duration_seconds" "Backup duration histogram"
check_metric "backup_last_success_timestamp" "Last successful backup"
check_metric "s3_sync_operations_total" "S3 sync operations"
check_metric "backup_disk_usage_bytes" "Disk usage metrics"
check_metric "backup_integrity_checks_total" "Integrity check counter"
check_metric "restore_operations_total" "Restore operations counter"

# Verify metrics are being scraped by Prometheus
log_info "Verifying metrics in Prometheus..."
PROM_METRICS=$(curl -s "$PROMETHEUS_URL/api/v1/targets" 2>&1)

if echo "$PROM_METRICS" | grep -q "job=\"backend\""; then
    log_success "Backend target found in Prometheus"
else
    log_warning "Backend target not found in Prometheus (may still be scraping)"
fi

# ============================================================================
# Step 4: Verify Grafana Dashboard
# ============================================================================
echo ""
echo "=========================================="
echo "Step 4: Verifying Grafana Dashboard"
echo "=========================================="

# Check if dashboard provisioning file exists
if [ -f "monitoring/grafana/dashboards/backup-status.json" ]; then
    log_success "Backup dashboard JSON file exists"
else
    log_error "Backup dashboard JSON file not found"
fi

# Try to access dashboard via API
log_info "Checking dashboard via Grafana API..."

DASHBOARDS=$(curl -s "$GRAFANA_URL/api/search?query=backup" \
    -u "$ADMIN_USER:$ADMIN_PASSWORD" 2>&1)

if echo "$DASHBOARDS" | grep -q "backup"; then
    log_success "Backup dashboard found in Grafana"
    DASHBOARD_UID=$(echo "$DASHBOARDS" | grep -o '"uid":"[^"]*' | head -1 | cut -d'"' -f4)
    log_info "Dashboard UID: $DASHBOARD_UID"
else
    log_warning "Backup dashboard not found in Grafana API (may need to reload)"
fi

# Check dashboard provisioning config
if [ -f "monitoring/grafana/provisioning/dashboards/dashboards.yml" ]; then
    if grep -q "backup-status" monitoring/grafana/provisioning/dashboards/dashboards.yml; then
        log_success "Dashboard registered in provisioning config"
    else
        log_error "Dashboard not registered in provisioning config"
    fi
fi

# ============================================================================
# Step 5: Verify Backup Status Visibility
# ============================================================================
echo ""
echo "=========================================="
echo "Step 5: Verifying Backup Status Visibility"
echo "=========================================="

log_info "Fetching backup list from API..."

BACKUPS=$(curl -s "$BACKEND_URL/api/backups" 2>&1)

if echo "$BACKUPS" | grep -q "\[\]\|backups"; then
    log_success "Backup status endpoint accessible"

    # Count backups
    BACKUP_COUNT=$(echo "$BACKUPS" | grep -o '"id"' | wc -l || echo "0")
    log_info "Found $BACKUP_COUNT backup(s) in system"

    if [ "$BACKUP_COUNT" -gt 0 ]; then
        log_success "Backups are tracked in the system"
    else
        log_warning "No backups found yet (new system)"
    fi
else
    log_error "Failed to fetch backup status"
fi

# ============================================================================
# Step 6: Verify Alert Rules
# ============================================================================
echo ""
echo "=========================================="
echo "Step 6: Verifying Alert Rules"
echo "=========================================="

# Check alert rules file exists
if [ -f "monitoring/grafana/provisioning/alerts/backup_alert_rules.yml" ]; then
    log_success "Backup alert rules file exists"
else
    log_error "Backup alert rules file not found"
fi

# Check if rules are in Prometheus config
if grep -q "backup_alert_rules" monitoring/prometheus/prometheus.yml; then
    log_success "Alert rules included in Prometheus config"
else
    log_error "Alert rules not in Prometheus config"
fi

# Try to fetch rules from Prometheus API
log_info "Fetching rules from Prometheus API..."

RULES=$(curl -s "$PROMETHEUS_URL/api/v1/rules" 2>&1)

# Check for specific backup alerts
check_alert() {
    local alert_name=$1
    local description=$2

    if echo "$RULES" | grep -q "$alert_name"; then
        log_success "$description alert loaded ($alert_name)"
        return 0
    else
        log_warning "$description alert not found in Prometheus ($alert_name)"
        return 1
    fi
}

check_alert "BackupFailure" "Backup failure"
check_alert "BackupMissed" "Missed backup"
check_alert "S3SyncFailure" "S3 sync failure"
check_alert "LowBackupDiskSpace" "Low disk space"
check_alert "BackupIntegrityCheckFailed" "Integrity check failure"

# ============================================================================
# Step 7: Verify Email Notification Configuration
# ============================================================================
echo ""
echo "=========================================="
echo "Step 7: Verifying Email Notifications"
echo "=========================================="

# Check if email service file exists
if [ -f "backend/services/email_notification_service.py" ]; then
    log_success "Email notification service file exists"
else
    log_error "Email notification service file not found"
fi

# Check if email is integrated in backup tasks
if grep -q "send_backup_notification" backend/tasks/backup_tasks.py; then
    log_success "Email notifications integrated in backup tasks"
else
    log_error "Email notifications not integrated in backup tasks"
fi

# Check environment variables
if [ -f ".env.example" ]; then
    if grep -q "SMTP" .env.example; then
        log_success "Email configuration in .env.example"
    else
        log_error "Email configuration not in .env.example"
    fi
fi

# ============================================================================
# Step 8: Verify Documentation
# ============================================================================
echo ""
echo "=========================================="
echo "Step 8: Verifying Documentation"
echo "=========================================="

check_doc() {
    local file=$1
    local name=$2

    if [ -f "$file" ]; then
        log_success "$name documentation exists ($file)"

        # Check for key sections
        case "$file" in
            *DISASTER_RECOVERY.md)
                if grep -q "restore" "$file" && grep -q "backup" "$file"; then
                    log_success "  - Contains restore procedures"
                fi
                ;;
            *BACKUP_RTO_RPO.md)
                if grep -q "RTO" "$file" && grep -q "RPO" "$file"; then
                    log_success "  - Contains RTO/RPO documentation"
                fi
                ;;
        esac
        return 0
    else
        log_error "$name documentation not found ($file)"
        return 1
    fi
}

check_doc "docs/DISASTER_RECOVERY.md" "Disaster Recovery"
check_doc "docs/BACKUP_RTO_RPO.md" "RTO/RPO"

# Check if README references DR docs
if [ -f "README.md" ]; then
    if grep -q "DISASTER_RECOVERY" README.md; then
        log_success "README references disaster recovery documentation"
    else
        log_error "README does not reference disaster recovery documentation"
    fi
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
echo -e "${YELLOW}Skipped:${NC} $SKIPPED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Visit Grafana at $GRAFANA_URL (admin/admin)"
    echo "2. Open the Backup Status dashboard"
    echo "3. Verify metrics are displaying correctly"
    echo "4. Check alert rules in Prometheus: $PROMETHEUS_URL/rules"
    echo "5. Test manual backup via frontend: $BACKEND_URL/docs"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the errors above.${NC}"
    exit 1
fi
