# Alert Rules Quick Reference

**Subtask 10-4**: Test alert rules trigger appropriately

## Configuration Status ✓

- **Alert Rules File**: `monitoring/grafana/provisioning/alerts/alert_rules.yml`
- **Contact Points File**: `monitoring/grafana/provisioning/alerting/contactpoints.yml`
- **Total Alert Groups**: 5
- **Total Alert Rules**: 16
- **Warning Alerts**: 7
- **Critical Alerts**: 9

## Alert Groups

### 1. API Performance (4 alerts)
- HighAPIErrorRate - Error rate > 5% (2min)
- CriticalAPIErrorRate - Error rate > 15% (1min)
- HighAPILatency - P95 > 2s (5min)
- CriticalAPILatency - P95 > 5s (2min)

### 2. Celery Tasks (6 alerts)
- CeleryQueueBackup - Queue > 100 (5min)
- CriticalCeleryQueueBackup - Queue > 500 (2min)
- HighCeleryTaskFailureRate - Failures > 10% (5min)
- CriticalCeleryTaskFailureRate - Failures > 25% (2min)
- CeleryWorkersDown - No workers (2min)
- SlowCeleryTasks - P95 > 300s (10min)

### 3. ML Inference (2 alerts)
- SlowMLInference - P95 > 30s (5min)
- CriticalMLInference - P95 > 60s (2min)

### 4. Database (2 alerts)
- SlowDatabaseQueries - P95 > 1s (5min)
- CriticalDatabaseQueries - P95 > 3s (2min)

### 5. System (2 alerts)
- ServiceDown - up == 0 (1min)
- HighMemoryUsage - Memory > 90% (5min)

## Quick Testing Commands

### Validate Configuration
```bash
# Check configuration files
test -f monitoring/grafana/provisioning/alerts/alert_rules.yml
test -f monitoring/grafana/provisioning/alerting/contactpoints.yml

# Count alerts
grep -c "^      - alert:" monitoring/grafana/provisioning/alerts/alert_rules.yml
# Expected: 16
```

### Runtime Testing (Requires Docker Running)

#### Test 1: Service Down Alert (Easy)
```bash
# Stop backend
docker-compose stop backend

# Wait 2 minutes, check alert state at:
# http://localhost:3001/alerting/rules

# Restart backend
docker-compose start backend
```

#### Test 2: High Error Rate Alert (Easy)
```bash
# Generate errors
for i in {1..500}; do
  curl -s http://localhost:8000/api/nonexistent-$i
done

# Wait 2 minutes, check "HighAPIErrorRate" alert at:
# http://localhost:3001/alerting/rules
```

#### Test 3: Celery Queue Backup (Medium)
```bash
# Pause workers
docker-compose pause celery_worker celery_exporter

# Submit tasks to build queue depth > 100

# Wait 5 minutes, check "CeleryQueueBackup" alert

# Resume workers
docker-compose unpause celery_worker celery_exporter
```

## Verification URLs

### Grafana
- Alert Rules: http://localhost:3001/alerting/rules
- Notifications: http://localhost:3001/alerting/notifications
- Alert History: http://localhost:3001/alerting/history

### Prometheus
- Targets: http://localhost:9090/targets
- Alerts: http://localhost:9090/alerts
- Graph: http://localhost:9090/graph

## Notification Testing

### Email Test
1. Configure SMTP in `.env`:
   ```bash
   GRAFANA_SMTP_HOST=smtp.gmail.com:587
   GRAFANA_SMTP_USER=your_email@gmail.com
   GRAFANA_SMTP_PASSWORD=your_app_password
   ALERT_EMAIL_ADDRESS=alerts@example.com
   ```

2. Restart Grafana: `docker-compose restart grafana`

3. Send test:
   - Go to http://localhost:3001/alerting/notifications
   - Click "email-alerts"
   - Click "Send test notification"

### Webhook Test
1. Configure webhook in `.env`:
   ```bash
   ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

2. Restart Grafana: `docker-compose restart grafana`

3. Send test:
   - Go to http://localhost:3001/alerting/notifications
   - Click "webhook-alerts"
   - Click "Send test notification"

## Alert State Lifecycle

```
Normal (condition not met)
    ↓ [condition becomes true]
Pending (waiting for 'for' duration)
    ↓ [for duration elapsed]
Firing (alert active, notifications sent)
    ↓ [condition becomes false]
Normal (alert resolved, resolved notifications sent)
```

## Troubleshooting

### Alert Not Firing
1. Check metric exists in Prometheus
2. Verify expression evaluates to true
3. Ensure `for` duration elapsed
4. Check alert evaluation interval (30s)

### No Notification Received
1. Verify notification channel linked to alert
2. Send test notification from Grafana UI
3. Check Grafana logs: `docker-compose logs grafana | grep -i alert`
4. Verify SMTP/webhook credentials

### Alert Flapping
1. Increase `for` duration
2. Adjust threshold slightly
3. Add hysteresis (separate warning/critical)

## Documentation

- **Testing Guide**: `ALERT_RULES_TESTING_GUIDE.md` - Comprehensive testing procedures
- **Checklist**: `ALERT_TESTING_CHECKLIST.md` - Step-by-step testing checklist
- **Verification Script**: `verify-alert-rules.sh` - Automated verification
- **Validation Script**: `validate-alert-config.sh` - Configuration validation
- **Monitoring README**: `README.md` - Setup and configuration details

## Verification Checklist

- [ ] Configuration files validated (16 rules, 5 groups)
- [ ] Alert rules loaded in Grafana UI
- [ ] Notification channels configured
- [ ] Test notifications sent successfully
- [ ] At least 2 alert types tested end-to-end
- [ ] Alert state transitions observed
- [ ] Alert resolution verified

## Support

For detailed testing procedures, see:
- `ALERT_RULES_TESTING_GUIDE.md` - Full testing documentation
- `ALERT_TESTING_CHECKLIST.md` - Testing checklist with sign-off

---

**Status**: Configuration verified ✓
**Ready for**: Runtime testing with Docker services running
**Last Updated**: 2026-02-01
