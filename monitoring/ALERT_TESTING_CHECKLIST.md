# Alert Rules Testing Checklist

**Subtask 10-4**: Test alert rules trigger appropriately

## Pre-Flight Verification

### Configuration File Validation ✓

Run these checks to verify alert rules are properly configured:

```bash
# 1. Verify alert rules file exists
test -f monitoring/grafana/provisioning/alerts/alert_rules.yml && echo "✓ Alert rules file exists"

# 2. Count alert groups
grep -c "^  - name:" monitoring/grafana/provisioning/alerts/alert_rules.yml
# Expected: 5 groups

# 3. Count alert rules
grep -c "^      - alert:" monitoring/grafana/provisioning/alerts/alert_rules.yml
# Expected: 16 rules

# 4. Verify notification channels file exists
test -f monitoring/grafana/provisioning/alerting/contactpoints.yml && echo "✓ Contact points file exists"

# 5. List all alert names
grep "^      - alert:" monitoring/grafana/provisioning/alerts/alert_rules.yml | sed 's/^      - alert: /  - /'
```

### Alert Inventory

**Expected Configuration:**

| Group | Alert Name | Threshold | Severity | For Duration |
|-------|-----------|-----------|----------|--------------|
| api_performance_alerts | HighAPIErrorRate | > 5% | warning | 2m |
| api_performance_alerts | CriticalAPIErrorRate | > 15% | critical | 1m |
| api_performance_alerts | HighAPILatency | P95 > 2s | warning | 5m |
| api_performance_alerts | CriticalAPILatency | P95 > 5s | critical | 2m |
| celery_alerts | CeleryQueueBackup | > 100 tasks | warning | 5m |
| celery_alerts | CriticalCeleryQueueBackup | > 500 tasks | critical | 2m |
| celery_alerts | HighCeleryTaskFailureRate | > 10% | warning | 5m |
| celery_alerts | CriticalCeleryTaskFailureRate | > 25% | critical | 2m |
| celery_alerts | CeleryWorkersDown | < 1 worker | critical | 2m |
| celery_alerts | SlowCeleryTasks | P95 > 300s | warning | 10m |
| ml_inference_alerts | SlowMLInference | P95 > 30s | warning | 5m |
| ml_inference_alerts | CriticalMLInference | P95 > 60s | critical | 2m |
| database_alerts | SlowDatabaseQueries | P95 > 1s | warning | 5m |
| database_alerts | CriticalDatabaseQueries | P95 > 3s | critical | 2m |
| system_alerts | ServiceDown | up == 0 | critical | 1m |
| system_alerts | HighMemoryUsage | > 90% | warning | 5m |

**Total:** 16 alert rules across 5 groups

## Runtime Testing Checklist

These tests require Docker services to be running.

### 1. Service Availability Check

- [ ] Prometheus is accessible at http://localhost:9090
- [ ] Grafana is accessible at http://localhost:3001
- [ ] All Prometheus targets are UP (check http://localhost:9090/targets)
- [ ] Alert rules are loaded in Grafana (check http://localhost:3001/alerting/rules)

### 2. Alert Rules Loaded Verification

- [ ] Navigate to http://localhost:3001/alerting/rules
- [ ] Verify 5 alert groups are visible
- [ ] Verify all 16 alert rules are listed
- [ ] All alerts show "Normal" state initially
- [ ] No rule validation errors visible

### 3. Notification Channel Configuration

#### Email Alerts
- [ ] SMTP credentials configured in `.env` file
- [ ] Grafana restarted after configuration
- [ ] Email contact point shows as "healthy" in Grafana
- [ ] Test notification sent successfully
- [ ] Test email received in inbox

#### Webhook Alerts (if configured)
- [ ] Webhook URL configured in `.env` file
- [ ] Webhook contact point shows configured in Grafana
- [ ] Test notification sent successfully
- [ ] Test message received in Slack/Teams/Discord

### 4. Alert State Transition Tests

#### Test 4A: Service Down Alert (Easy - Safe to Test)

- [ ] Note current "ServiceDown" alert state (should be Normal)
- [ ] Stop backend service: `docker-compose stop backend`
- [ ] Wait 1 minute
- [ ] Verify alert state changes to "Pending"
- [ ] Wait another minute
- [ ] Verify alert state changes to "Firing"
- [ ] Check for notification (if configured)
- [ ] Start backend: `docker-compose start backend`
- [ ] Wait 1-2 minutes
- [ ] Verify alert returns to "Normal" state
- [ ] Check for "resolved" notification

**Result:** Service down detection working ✓

#### Test 4B: High Error Rate Alert (Easy - Safe to Test)

- [ ] Note "HighAPIErrorRate" alert state (should be Normal)
- [ ] Generate 500+ 5xx errors:
  ```bash
  for i in {1..500}; do
    curl -s http://localhost:8000/api/nonexistent-$i
  done
  ```
- [ ] Wait 2 minutes
- [ ] Verify alert transitions: Normal → Pending → Firing (warning)
- [ ] Check for notification
- [ ] Wait 5-10 minutes (stop generating errors)
- [ ] Verify alert returns to "Normal"

**Result:** Error rate alert working ✓

#### Test 4C: Celery Queue Backup (Medium - Requires Worker Pause)

- [ ] Verify Celery workers running: `docker-compose ps celery_worker`
- [ ] Pause workers: `docker-compose pause celery_worker celery_exporter`
- [ ] Submit tasks to build queue depth > 100
- [ ] Monitor queue metric: `curl -s 'http://localhost:9090/api/v1/query?query=celery_queue_length'`
- [ ] Wait 5 minutes after queue exceeds 100
- [ ] Verify "CeleryQueueBackup" alert fires (warning)
- [ ] Build queue > 500 (or test critical threshold separately)
- [ ] Wait 2 minutes
- [ ] Verify "CriticalCeleryQueueBackup" alert fires
- [ ] Resume workers: `docker-compose unpause celery_worker celery_exporter`
- [ ] Monitor queue drain
- [ ] Verify alerts return to "Normal"

**Result:** Celery queue monitoring working ✓

#### Test 4D: Alert Resolution (All Alerts)

- [ ] For any firing alert, fix the underlying condition
- [ ] Wait for evaluation interval + `for` duration
- [ ] Verify alert state changes: Firing → Normal
- [ ] Verify "resolved" notification sent (if enabled)
- [ ] Check alert history for state transition

**Result:** Alert resolution working ✓

### 5. Alert Notification Tests

- [ ] Trigger "ServiceDown" alert (stop backend)
- [ ] Verify notification received within 1-2 minutes
- [ ] Check notification contains:
  - [ ] Alert name
  - [ ] Severity level
  - [ ] Summary
  - [ ] Description with actual value
  - [ ] Labels (category, severity, etc.)
- [ ] Restart backend
- [ ] Verify "resolved" notification received

**Result:** Alert notifications working ✓

### 6. Alert Dashboard Verification

- [ ] Navigate to http://localhost:3001/alerting/rules
- [ ] Filter alerts by severity (warning/critical)
- [ ] Sort alerts by state
- [ ] Click on individual alert to view details
- [ ] Verify alert graph shows metric history
- [ ] Check alert annotations are populated correctly

### 7. Integration Tests

#### Test 7A: End-to-End Alert Flow

- [ ] Generate condition that triggers warning alert
- [ ] Verify warning alert fires after `for` duration
- [ ] Verify warning notification sent
- [ ] Escalate condition to trigger critical alert
- [ ] Verify critical alert fires
- [ ] Verify critical notification sent
- [ ] Resolve condition
- [ ] Verify both alerts resolve
- [ ] Verify resolved notifications sent

**Result:** Full alert lifecycle working ✓

#### Test 7B: Multiple Alert Scenarios

- [ ] Trigger multiple different alerts simultaneously
- [ ] Verify all notifications sent
- [ ] Verify alert grouping works correctly
- [ ] Check notification rate limiting (if configured)
- [ ] Resolve all alerts
- [ ] Verify all resolved correctly

**Result:** Multiple alert handling working ✓

## Post-Testing Verification

### Configuration Validation

- [ ] All 16 alert rules present in Grafana
- [ ] All alert rules evaluate without errors
- [ ] No "No Data" errors on alerts
- [ ] Notification channels linked to alerts
- [ ] Alert routing policy configured correctly

### Performance Validation

- [ ] Alert evaluation time < 5 seconds
- [ ] No alert evaluation failures
- [ ] Prometheus query performance acceptable
- [ ] No high memory usage from alert evaluation

### Documentation Validation

- [ ] Alert thresholds documented
- [ ] Alert response procedures documented
- [ ] Notification channel settings documented
- [ ] On-call procedures established

## Test Summary

### Automated Tests
- [ ] `./monitoring/verify-alert-rules.sh` runs successfully
- [ ] All configuration file checks pass
- [ ] No syntax errors in alert rules

### Manual Tests
- [ ] At least 2 alert types tested end-to-end
- [ ] Notification channels verified working
- [ ] Alert state transitions observed
- [ ] Alert resolution verified

### Production Readiness
- [ ] All alerts tuned to appropriate thresholds
- [ ] Notification channels verified
- [ ] On-call rotation defined
- [ ] Runbooks created
- [ ] Mute time intervals configured (if needed)

## Common Issues and Solutions

### Issue: Alert Not Firing

**Checks:**
1. Verify metric exists in Prometheus: http://localhost:9090/graph
2. Check alert expression evaluates to true
3. Verify `for` duration has elapsed
4. Check alert evaluation interval (default 30s)

**Solution:**
- Reduce `for` duration temporarily for testing
- Verify metric labels match alert expression
- Check alert rule syntax

### Issue: Notification Not Received

**Checks:**
1. Notification channel linked to alert in routing policy
2. Contact point marked as "healthy"
3. Test notification works
4. Check Grafana logs for errors

**Solution:**
- Verify SMTP/webhook credentials
- Check notification routing rules
- Review Grafana logs: `docker-compose logs grafana`

### Issue: Alert Flapping (Firing/Resolving Repeatedly)

**Checks:**
1. Metric hovering near threshold
2. `for` duration too short
3. Query time window too short

**Solution:**
- Increase `for` duration
- Adjust threshold slightly
- Add hysteresis (separate warning/critical thresholds)

## Sign-off

**Tester:** ______________________
**Date:** ______________________
**Environment:** Development / Staging / Production

**Tests Completed:**
- Configuration validation: ✓ / ✗
- Runtime testing: ✓ / ✗
- Notification testing: ✓ / ✗
- End-to-end testing: ✓ / ✗

**Overall Result:** PASS / FAIL

**Notes:**
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________

---

**Document Version:** 1.0
**Last Updated:** 2026-02-01
**Subtask:** 10-4 - Test alert rules trigger appropriately
