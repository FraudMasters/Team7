# Alert Rules Testing Guide

**Subtask 10-4**: Test alert rules trigger appropriately

## Overview

This guide provides comprehensive instructions for testing Grafana alert rules to ensure they trigger appropriately when thresholds are exceeded, and verify that notification channels deliver alerts as expected.

## Quick Verification

Run the automated verification script:

```bash
./monitoring/verify-alert-rules.sh
```

This script will:
- ✓ Verify alert rules configuration file exists
- ✓ Check alert rules are loaded in Grafana
- ✓ Verify all alert groups and individual rules
- ✓ Check notification channel configuration
- ✓ Display current alert states
- ✓ Provide manual testing guidance

## Alert Rules Summary

### Total Alerts: 16 rules across 5 groups

#### 1. API Performance Alerts (4 rules)
- **HighAPIErrorRate**: Error rate > 5% (warning, 2min for)
- **CriticalAPIErrorRate**: Error rate > 15% (critical, 1min for)
- **HighAPILatency**: P95 latency > 2s (warning, 5min for)
- **CriticalAPILatency**: P95 latency > 5s (critical, 2min for)

#### 2. Celery Task Alerts (6 rules)
- **CeleryQueueBackup**: Queue depth > 100 tasks (warning, 5min for)
- **CriticalCeleryQueueBackup**: Queue depth > 500 tasks (critical, 2min for)
- **HighCeleryTaskFailureRate**: Failure rate > 10% (warning, 5min for)
- **CriticalCeleryTaskFailureRate**: Failure rate > 25% (critical, 2min for)
- **CeleryWorkersDown**: No workers running (critical, 2min for)
- **SlowCeleryTasks**: P95 runtime > 300s (warning, 10min for)

#### 3. ML Inference Alerts (2 rules)
- **SlowMLInference**: P95 inference time > 30s (warning, 5min for)
- **CriticalMLInference**: P95 inference time > 60s (critical, 2min for)

#### 4. Database Alerts (2 rules)
- **SlowDatabaseQueries**: P95 query duration > 1s (warning, 5min for)
- **CriticalDatabaseQueries**: P95 query duration > 3s (critical, 2min for)

#### 5. System Alerts (2 rules)
- **ServiceDown**: Service unreachable (critical, 1min for)
- **HighMemoryUsage**: Memory usage > 90% (warning, 5min for)

## Manual Testing Procedures

### Prerequisites

1. **Ensure services are running:**
   ```bash
   docker-compose ps
   ```

2. **Configure notification channels** (see [README.md](./README.md)):
   - Email: Set SMTP credentials in `.env`
   - Webhook: Set webhook URL in `.env`

3. **Access Grafana:**
   - URL: http://localhost:3001
   - Default credentials: `admin` / `admin`

### Test 1: Verify Alert Rules Are Loaded

**Objective**: Confirm all alert rules are properly loaded in Grafana

**Steps:**
1. Navigate to http://localhost:3001/alerting/rules
2. Verify all 5 alert groups are visible
3. Verify each group contains the expected alerts
4. Check that all alerts show "Normal" state initially

**Expected Result:**
- ✓ All 16 alert rules listed
- ✓ All alerts in "Normal" state
- ✓ No rule validation errors

**If Test Fails:**
- Check Grafana logs: `docker-compose logs grafana`
- Verify alert rules file: `monitoring/grafana/provisioning/alerts/alert_rules.yml`
- Restart Grafana: `docker-compose restart grafana`

### Test 2: Notification Channel Delivery

**Objective**: Verify notification channels can deliver alerts

#### 2A. Test Email Notifications

**Steps:**
1. Ensure SMTP is configured in `.env`:
   ```bash
   GRAFANA_SMTP_HOST=smtp.gmail.com:587
   GRAFANA_SMTP_USER=your_email@gmail.com
   GRAFANA_SMTP_PASSWORD=your_app_password
   ALERT_EMAIL_ADDRESS=your_email@example.com
   ```

2. Restart Grafana to apply config:
   ```bash
   docker-compose restart grafana
   ```

3. Navigate to http://localhost:3001/alerting/notifications

4. Click on "email-alerts" contact point

5. Click "Send test notification"

6. Check email inbox for test alert

**Expected Result:**
- ✓ Test email received within 30 seconds
- ✓ Email contains alert details (alert name, severity, description)

**If Test Fails:**
- Check SMTP credentials are correct
- For Gmail: Use App Password, not account password
- Check firewall allows SMTP port 587
- Review Grafana logs: `docker-compose logs grafana | grep -i smtp`

#### 2B. Test Webhook Notifications

**Steps:**
1. Configure webhook URL in `.env`:
   ```bash
   ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

2. Restart Grafana:
   ```bash
   docker-compose restart grafana
   ```

3. Navigate to http://localhost:3001/alerting/notifications

4. Click on "webhook-alerts" contact point

5. Click "Send test notification"

6. Check Slack/Teams/Discord for test message

**Expected Result:**
- ✓ Test message received in webhook target
- ✓ Message formatted correctly with alert details

**If Test Fails:**
- Verify webhook URL is correct
- Check webhook is accessible from Docker container
- Review Grafana logs: `docker-compose logs grafana | grep -i webhook`

### Test 3: Service Down Alert

**Objective**: Verify service down detection and alerting

**Difficulty**: Easy (safe to test in development)

**Steps:**
1. Navigate to http://localhost:3001/alerting/rules
2. Note current state of "ServiceDown" alert (should be Normal)
3. Stop the backend service:
   ```bash
   docker-compose stop backend
   ```
4. Wait 1-2 minutes
5. Refresh the alert rules page
6. Verify "ServiceDown" alert state changes:
   - After ~1min: State = Pending
   - After another ~1min: State = Firing
7. Check for notification (if configured)
8. Restart backend:
   ```bash
   docker-compose start backend
   ```
9. Wait 1-2 minutes
10. Verify alert returns to "Normal" state
11. Verify "resolved" notification received (if enabled)

**Expected Result:**
- ✓ Alert transitions: Normal → Pending → Firing → Normal
- ✓ Notification sent when alert fires
- ✓ Notification sent when alert resolves

**If Test Fails:**
- Check Prometheus is scraping backend target: http://localhost:9090/targets
- Verify alert rule expression: `up == 0`
- Check `for` duration (1 minute)

### Test 4: High API Error Rate Alert

**Objective**: Verify error rate alert triggers appropriately

**Difficulty**: Easy (safe to test in development)

**Steps:**
1. Open Grafana alert rules page: http://localhost:3001/alerting/rules
2. Generate API errors (non-existent endpoints):
   ```bash
   for i in {1..200}; do
     curl -s http://localhost:8000/api/nonexistent-endpoint-$i
   done
   ```
3. Monitor the "HighAPIErrorRate" alert
4. After 2 minutes, check if alert state changes:
   - Error rate should exceed 5% threshold
   - Alert should transition: Normal → Pending → Firing (warning)
5. Generate more errors to trigger critical:
   ```bash
   for i in {1..500}; do
     curl -s http://localhost:8000/api/nonexistent-endpoint-$i
   done
   ```
6. Wait 1-2 minutes
7. Check if "CriticalAPIErrorRate" alert fires (> 15% threshold)
8. Let alerts resolve (wait 5-10 minutes without errors)
9. Verify alerts return to "Normal" state

**Expected Result:**
- ✓ Warning alert fires when error rate > 5%
- ✓ Critical alert fires when error rate > 15%
- ✓ Alerts resolve when error rate drops
- ✓ Notifications sent for firing and resolving

**If Test Fails:**
- Verify `http_requests_total` metrics are being recorded
- Check Prometheus query: `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))`
- Ensure enough requests are made to exceed threshold
- Check alert `for` duration (2min warning, 1min critical)

### Test 5: Celery Queue Backup Alert

**Objective**: Verify queue depth monitoring

**Difficulty**: Medium (requires pausing workers)

**Steps:**
1. Ensure Celery workers are running:
   ```bash
   docker-compose ps celery_worker
   ```
2. Pause workers to stop processing:
   ```bash
   docker-compose pause celery_worker celery_exporter
   ```
3. Submit tasks to build queue (you'll need a task submission endpoint)
4. Monitor queue depth in Prometheus:
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=celery_queue_length' | jq
   ```
5. Wait until queue depth exceeds 100
6. After 5 minutes, verify "CeleryQueueBackup" warning alert fires
7. Continue until queue exceeds 500 (or simulate with more tasks)
8. Verify "CriticalCeleryQueueBackup" alert fires after 2 minutes
9. Resume workers:
   ```bash
   docker-compose unpause celery_worker celery_exporter
   ```
10. Monitor as queue drains
11. Verify alerts return to "Normal" state

**Expected Result:**
- ✓ Warning alert fires when queue > 100 tasks
- ✓ Critical alert fires when queue > 500 tasks
- ✓ Alerts resolve as queue drains
- ✓ Notifications sent appropriately

**If Test Fails:**
- Verify celery-exporter is running: `docker-compose ps celery_exporter`
- Check metrics: http://localhost:9540/metrics
- Verify `celery_queue_length` metric is present
- Ensure tasks are being queued while workers are paused

### Test 6: High Memory Usage Alert

**Objective**: Verify memory monitoring

**Difficulty**: Advanced (requires memory pressure simulation)

**Steps:**
1. Check current memory usage in Grafana dashboard
2. Simulate memory pressure (this is container-specific):
   - You may need to run memory-intensive workloads
   - Or temporarily lower container memory limit in docker-compose.yml
3. Monitor "HighMemoryUsage" alert
4. When memory usage exceeds 90%, verify alert fires after 5 minutes
5. Reduce memory pressure
6. Verify alert resolves

**Expected Result:**
- ✓ Alert fires when memory usage > 90%
- ✓ Alert resolves when usage drops

**Note**: This test is difficult to safely perform in development. Consider:
- Temporarily reducing container memory limit: `mem_limit: 256M`
- Running a memory stress test: `stress --vm 1 --vm-bytes 200M --vm-hang 0`

### Test 7: ML Inference Performance Alert

**Objective**: Verify ML model performance monitoring

**Difficulty**: Advanced (requires actual inference)

**Steps:**
1. Ensure ML models are loaded
2. Submit resume analysis requests
3. Monitor "SlowMLInference" and "CriticalMLInference" alerts
4. Under normal conditions, P95 should be < 30s (no alert)
5. To simulate slow inference:
   - You could intentionally slow down the inference process
   - Or test with very large resumes
6. Verify warning alert fires if P95 > 30s for 5 minutes
7. Verify critical alert fires if P95 > 60s for 2 minutes
8. After normal performance resumes, verify alerts resolve

**Expected Result:**
- ✓ Warning alerts if P95 > 30s
- ✓ Critical alerts if P95 > 60s
- ✓ Alerts resolve when performance improves

**Note**: This requires actual ML model inference and may be difficult to test without slowdown simulation.

### Test 8: Database Query Performance Alert

**Objective**: Verify database query monitoring

**Difficulty**: Advanced (requires slow queries)

**Steps:**
1. Under normal conditions, queries should be fast (< 1s)
2. Monitor "SlowDatabaseQueries" and "CriticalDatabaseQueries" alerts
3. To simulate slow queries:
   - Create complex queries
   - Or temporarily load the database with large datasets
4. Verify warning alert fires if P95 > 1s for 5 minutes
5. Verify critical alert fires if P95 > 3s for 2 minutes
6. After query performance improves, verify alerts resolve

**Expected Result:**
- ✓ Warning alerts if P95 query time > 1s
- ✓ Critical alerts if P95 query time > 3s
- ✓ Alerts resolve when performance improves

**Note**: This requires generating slow database queries, which may impact application performance.

## Alert State Transitions

### Normal State
- Alert condition is NOT met
- Metrics are below thresholds
- No action required

### Pending State
- Alert condition IS met
- Waiting for `for` duration to elapse
- Prevents alerts from flapping (transient spikes)

### Firing State
- Alert condition met for entire `for` duration
- Notifications are sent
- Action required

### Resolution
- Alert condition no longer met
- Returns to "Normal" state
- "Resolved" notifications sent (if enabled)

## Troubleshooting

### Alerts Not Firing When Expected

1. **Check metrics are being collected:**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=up' | jq
   ```

2. **Verify alert rule expression in Prometheus:**
   - Go to http://localhost:9090/alerts
   - Find the alert
   - Check if it shows "Inactive", "Pending", or "Firing"

3. **Check alert rule syntax:**
   - Ensure PromQL expressions are valid
   - Check for correct label matchers
   - Verify time windows are appropriate

4. **Verify `for` duration:**
   - Alert must be true for entire duration
   - Try reducing `for` duration for testing

5. **Check evaluation interval:**
   - Default is 30 seconds
   - Alert may not evaluate immediately

### Notifications Not Being Sent

1. **Verify notification channel is linked to alert:**
   - Go to http://localhost:3001/alerting/rules
   - Click alert rule
   - Check "Contact point" is set

2. **Check notification policies:**
   - Go to http://localhost:3001/alerting/routes
   - Verify default route matches your alerts

3. **Test notification channel directly:**
   - Go to http://localhost:3001/alerting/notifications
   - Click contact point
   - Send test notification

4. **Review Grafana logs:**
   ```bash
   docker-compose logs grafana | grep -i alert
   docker-compose logs grafana | grep -i notify
   ```

### Alerts Firing Too Frequently

1. **Adjust thresholds:**
   - Edit `monitoring/grafana/provisioning/alerts/alert_rules.yml`
   - Increase threshold values

2. **Increase `for` duration:**
   - Requires alert to be true for longer
   - Prevents alerts from transient spikes

3. **Use mute time intervals:**
   - Configure quiet hours in `contactpoints.yml`
   - Prevents after-hours alerts

4. **Add hysteresis:**
   - Use different thresholds for warning vs critical
   - Or use separate rules with different thresholds

## Automated Testing Script

The verification script (`verify-alert-rules.sh`) performs automated checks:

```bash
./monitoring/verify-alert-rules.sh
```

**What it checks:**
- ✓ Alert rules configuration file exists and is valid
- ✓ All alert groups and rules are loaded in Grafana
- ✓ Notification channels are configured
- ✓ Current alert states (Normal/Pending/Firing)
- ✓ Alert rule structure and syntax

**Manual Testing:** Use the procedures above to test specific alert conditions.

## Best Practices

### Testing in Development
1. Start with warning thresholds before testing critical
2. Use shorter `for` durations for faster testing
3. Test notification channels BEFORE relying on alerts
4. Document expected alert behavior in runbooks

### Production Readiness
1. All alert thresholds tuned to your environment
2. Notification channels verified and working
3. On-call rotation established
4. Alert response procedures documented
5. Mute time intervals configured for after-hours
6. Alert fatigue monitored and addressed

### Maintenance
1. Regularly review alert effectiveness
2. Adjust thresholds based on baseline metrics
3. Add new alerts as needed
4. Remove or tune noisy alerts
5. Keep runbooks up to date
6. Test notification channels periodically

## Additional Resources

- [Grafana Alerting Documentation](https://grafana.com/docs/grafana/latest/alerting/)
- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [PromQL Query Examples](https://promlabs.com/promql-cheat-sheet/)
- [Monitoring README](./README.md) - Setup and configuration

## Summary Checklist

Before considering alert testing complete:

- [ ] Verification script runs successfully
- [ ] All 16 alert rules loaded in Grafana
- [ ] Notification channels configured (email and/or webhook)
- [ ] Test notifications sent successfully
- [ ] Service down alert tested (easy)
- [ ] Error rate alert tested (easy)
- [ ] At least one threshold exceeded alert tested
- [ ] Alert state transitions observed (Normal → Pending → Firing → Normal)
- [ ] Alert resolution verified
- [ ] Documentation reviewed and understood

---

**Last Updated:** 2026-02-01
**Subtask:** 10-4 - Test alert rules trigger appropriately
