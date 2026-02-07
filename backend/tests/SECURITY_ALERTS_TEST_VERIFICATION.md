# Security Alerts Test Verification Guide

This document provides comprehensive instructions for running and verifying the security alerts tests, including unit tests, integration tests, and end-to-end verification steps.

## Table of Contents

1. [Test Overview](#test-overview)
2. [Prerequisites](#prerequisites)
3. [Running Unit Tests](#running-unit-tests)
4. [Running Integration Tests](#running-integration-tests)
5. [End-to-End Verification Steps](#end-to-end-verification-steps)
6. [Manual Testing with Real Services](#manual-testing-with-real-services)
7. [Testing Organization-Specific Configuration](#testing-organization-specific-configuration)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Success Criteria](#success-criteria)

---

## Test Overview

The security alerts test suite includes:

### Unit Tests (`test_security_alerts.py`)
- **Suspicious Activity Detection**: 8+ tests
  - Default and custom threshold detection
  - Failed login alerts
  - Multiple IP access alerts
  - Time window filtering
  - Exception handling

- **Alert Notification Delivery**: 8+ tests
  - Email alert delivery
  - SMS alert delivery
  - Multi-channel delivery (email + SMS)
  - Failed logins message formatting
  - Multiple IPs message formatting
  - Account locked and password reset messages
  - Timeout handling

- **Webhook Alert Delivery**: 4+ tests
  - Successful webhook delivery
  - HMAC signature authentication
  - Invalid URL rejection
  - Non-200 response handling

- **Slack Alert Delivery**: 3+ tests
  - Successful Slack delivery
  - Invalid URL rejection
  - Channel override

- **Multi-Channel Delivery**: 3+ tests
  - All channels success
  - Partial failure handling
  - No channels configured error

- **Helper Functions**: 15+ tests
  - Message formatting for all alert types
  - Webhook payload formatting
  - Slack message formatting
  - Phone number masking
  - Webhook URL masking

- **Database Query Functions**: 4+ tests
  - Failed logins query
  - Multiple IP access query
  - Total failed logins count
  - Unique active users count

### Integration Tests (`test_security_alerts_e2e.py`)
- **Suspicious Activity Detection**: 6+ tests
  - No suspicious activity scenarios
  - Multiple failed logins detection
  - Multiple IP access detection
  - Both threat types detection
  - Time window filtering
  - User and IP grouping

- **Alert Notification Delivery**: 6+ tests
  - Email alert delivery
  - SMS alert delivery
  - Alert without recipient fails
  - Message content verification for all alert types

- **Webhook Alert Delivery**: 3+ tests
  - Successful webhook delivery
  - URL validation
  - Payload structure verification

- **Slack Alert Delivery**: 3+ tests
  - URL validation
  - Payload structure
  - Message blocks verification

- **Multi-Channel Delivery**: 2+ tests
  - Partial success scenarios
  - No channels configured error

- **Organization Configuration**: 4+ tests
  - Default security config values
  - Custom threshold per organization
  - Alerts disabled per organization
  - Multiple organization configs

- **Alert Audit Logging**: 3+ tests
  - Failed login audit logs
  - Multiple failed logins audit trail
  - Successful login audit logs

- **Comprehensive Workflow**: 2+ tests
  - Complete alert workflow (event → detection → notification)
  - Organization-specific alert workflow

---

## Prerequisites

### Required Services

1. **PostgreSQL Database** (for production testing)
2. **Redis** (for Celery broker)
3. **Celery Worker** (for background task execution)

### Python Dependencies

```bash
cd backend
pip install -e ".[test]"
```

### Environment Configuration

Create a `.env` file for testing:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security (optional - for real email/SMS testing)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+15551234567
```

---

## Running Unit Tests

### Run All Unit Tests

```bash
cd backend
pytest tests/test_security_alerts.py -v
```

### Run Specific Test Suites

```bash
# Suspicious activity detection tests
pytest tests/test_security_alerts.py::TestCheckSuspiciousActivity -v

# Alert notification delivery tests
pytest tests/test_security_alerts.py::TestSendSecurityAlert -v

# Webhook delivery tests
pytest tests/test_security_alerts.py::TestSendSecurityAlertWebhook -v

# Slack delivery tests
pytest tests/test_security_alerts.py::TestSendSecurityAlertSlack -v

# Multi-channel delivery tests
pytest tests/test_security_alerts.py::TestSendSecurityAlertMultiChannel -v

# Helper function tests
pytest tests/test_security_alerts.py::TestFormatSecurityAlertMessage -v
pytest tests/test_security_alerts.py::TestFormatWebhookPayload -v
pytest tests/test_security_alerts.py::TestFormatSlackMessage -v
pytest tests/test_security_alerts.py::TestMaskingFunctions -v

# Database query function tests
pytest tests/test_security_alerts.py::TestDatabaseQueryFunctions -v
```

### Run with Coverage

```bash
pytest tests/test_security_alerts.py \
  --cov=tasks/security_alerts \
  --cov-report=term-missing \
  --cov-report=html
```

### Expected Output

All tests should pass with output similar to:

```
tests/test_security_alerts.py::TestCheckSuspiciousActivity::test_check_suspicious_activity_with_default_threshold PASSED
tests/test_security_alerts.py::TestSendSecurityAlert::test_send_alert_with_email PASSED
tests/test_security_alerts.py::TestSendSecurityAlertWebhook::test_send_webhook_success PASSED
...
======================== 45+ passed in 5.23s =========================

---------- coverage: platform linux, python 3.11 ----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
tasks/security_alerts.py              800    120    85%
-------------------------------------------------------
TOTAL                                 800    120    85%
```

---

## Running Integration Tests

### Run All Integration Tests

```bash
cd backend
pytest tests/integration/test_security_alerts_e2e.py -v
```

### Run Specific Test Suites

```bash
# Suspicious activity detection
pytest tests/integration/test_security_alerts_e2e.py::TestSuspiciousActivityDetection -v

# Alert notification delivery
pytest tests/integration/test_security_alerts_e2e.py::TestAlertNotificationDelivery -v

# Organization configuration
pytest tests/integration/test_security_alerts_e2e.py::TestOrganizationAlertConfiguration -v

# Comprehensive workflow
pytest tests/integration/test_security_alerts_e2e.py::TestComprehensiveAlertWorkflow -v
```

### Run with Coverage

```bash
pytest tests/integration/test_security_alerts_e2e.py \
  --cov=tasks/security_alerts \
  --cov=api/security_config \
  --cov-report=term-missing
```

### Expected Output

```
tests/integration/test_security_alerts_e2e.py::TestSuspiciousActivityDetection::test_no_suspicious_activity PASSED
tests/integration/test_security_alerts_e2e.py::TestSuspiciousActivityDetection::test_detects_multiple_failed_logins PASSED
tests/integration/test_security_alerts_e2e.py::TestAlertNotificationDelivery::test_send_email_alert_success PASSED
...
======================== 32+ passed in 8.45s =========================
```

---

## End-to-End Verification Steps

### 1. Trigger Failed Login Event

#### Create Audit Log Entries

```bash
# Start Python shell
cd backend
python

# In Python shell:
import asyncio
from datetime import datetime
from database import async_session_maker
from models.audit_log import AuditLog, AuditActionType
from uuid import uuid4

async def create_failed_logins():
    user_id = uuid4()
    async with async_session_maker() as session:
        # Create 10 failed login attempts
        for i in range(10):
            log = AuditLog(
                user_id=user_id,
                action_type=AuditActionType.LOGIN_FAILED,
                ip_address="192.168.1.100",
                location="New York",
            )
            session.add(log)
        await session.commit()
        print(f"Created 10 failed logins for user {user_id}")

asyncio.run(create_failed_logins())
```

**Expected Output:**
```
Created 10 failed logins for user 550e8400-e29b-41d4-a716-446655440000
```

### 2. Verify Security Alert Celery Task Executes

#### Start Celery Worker

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
cd backend
celery -A celery_app worker --loglevel=info --concurrency=1
```

**Expected Output:**
```
-------------- celery@hostname v5.x.x
---- **** -----
--- * ***  * -- Linux-x.x.x
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         backend.tasks:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/1
- *** --- * --- .> concurrency: 1 (solo)
-- ******* ---- .> task events: OFF
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery
```

#### Trigger Security Check Task

```bash
# Terminal 3: Trigger the task
cd backend
python

# In Python shell:
from tasks.security_alerts import check_suspicious_activity
import json

# Trigger the task
result = check_suspicious_activity.delay(
    time_window_minutes=60,
    failed_login_threshold=5,
    alert_on_multiple_ips=True,
    ip_change_threshold=3,
)

# Wait for result
print(json.dumps(result.get(timeout=30), indent=2))
```

**Expected Output:**
```json
{
  "status": "success",
  "time_window_minutes": 60,
  "analyzed_period_start": "2026-02-04T11:00:00",
  "analyzed_period_end": "2026-02-04T12:00:00",
  "failed_login_alerts": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "ip_address": "192.168.1.100",
      "failed_count": 10
    }
  ],
  "multiple_ip_alerts": [],
  "total_failed_logins": 10,
  "total_unique_users": 1,
  "processing_time_ms": 45.23
}
```

**Celery Worker Log:**
```
[2026-02-04 12:00:00,123: INFO/MainProcess] Task tasks.security_alerts.check_suspicious_activity[abc-123] received
[2026-02-04 12:00:00,234: INFO/MainProcess] Starting suspicious activity check with 60min window, failed_login_threshold=5
[2026-02-04 12:00:00,345: WARNING/MainProcess] Detected 1 users with suspicious failed login attempts
[2026-02-04 12:00:00,346: WARNING/MainProcess] User 550e8400-e29b-41d4-a716-446655440000: 10 failed logins from IP 192.168.1.100
[2026-02-04 12:00:00,456: INFO/MainProcess] Security check completed: 1 failed login alerts, 0 multiple IP alerts, processing time: 45ms
[2026-02-04 12:00:00,457: INFO/MainProcess] Task tasks.security_alerts.check_suspicious_activity[abc-123] succeeded in 0.33s
```

### 3. Verify Alert Notification Delivered

#### Send Security Alert

```bash
# In Python shell:
from tasks.security_alerts import send_security_alert
from unittest.mock import MagicMock

# Create mock task
task = MagicMock()

# Alert data from previous step
alert_data = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "ip_address": "192.168.1.100",
    "failed_count": 10,
    "severity": "high",
    "timestamp": "2026-02-04T12:00:00Z",
}

# Send email alert
result = send_security_alert(
    task,
    alert_type="failed_logins",
    recipient_email="user@example.com",
    alert_data=alert_data,
)

print(json.dumps(result, indent=2))
```

**Expected Output:**
```json
{
  "alert_type": "failed_logins",
  "status": "sent",
  "email_sent": true,
  "sms_sent": false,
  "recipient_email": "user@example.com",
  "recipient_phone_masked": null,
  "processing_time_ms": 123.45
}
```

**Celery Worker Log:**
```
[2026-02-04 12:01:00,123: INFO/MainProcess] Task tasks.security_alerts.send_security_alert[def-456] received
[2026-02-04 12:01:00,234: INFO/MainProcess] Sending security alert: type=failed_logins, email=yes, sms=no
[2026-02-04 12:01:00,345: INFO/MainProcess] Alert formatted: subject='⚠️ Security Alert: Multiple Failed Login Attempts Detected', sms_length=145
[2026-02-04 12:01:00,456: INFO/MainProcess] Sending security alert email: subject='⚠️ Security Alert: Multiple Failed Login Attempts Detected', to=user@example.com
[2026-02-04 12:01:00,567: INFO/MainProcess] Security alert email sent successfully to user@example.com
[2026-02-04 12:01:00,578: INFO/MainProcess] Security alert sent successfully: type=failed_logins, email=True, sms=False, time=123ms
```

#### Verify Alert Content

The alert should include:
- **Email Subject**: `⚠️ Security Alert: Multiple Failed Login Attempts Detected`
- **Email Body**: Details about failed logins, IP address, recommended actions
- **SMS Message**: Short summary with failed count and IP address

### 4. Test Alert Configuration Per Organization

#### Create Organization-Specific Config

```bash
# In Python shell:
import asyncio
from database import async_session_maker
from models.security_config import SecurityConfig
from uuid import uuid4

async def create_org_config():
    org_id = uuid4()
    async with async_session_maker() as session:
        config = SecurityConfig(
            organization_id=org_id,
            failed_login_threshold=15,  # Higher threshold
            security_alerts_enabled=True,
        )
        session.add(config)
        await session.commit()
        print(f"Created security config for organization {org_id}")
        print(f"Failed login threshold: {config.failed_login_threshold}")

asyncio.run(create_org_config())
```

**Expected Output:**
```
Created security config for organization 550e8400-e29b-41d4-a716-446655440001
Failed login threshold: 15
```

#### Test with Different Thresholds

```bash
# Create 12 failed logins (below org threshold of 15, above default of 5)
python

import asyncio
from database import async_session_maker
from models.audit_log import AuditLog, AuditActionType
from tasks.security_alerts import check_suspicious_activity

async def test_threshold():
    user_id = uuid4()
    async with async_session_maker() as session:
        for i in range(12):
            log = AuditLog(
                user_id=user_id,
                action_type=AuditActionType.LOGIN_FAILED,
                ip_address="192.168.1.101",
                location="London",
            )
            session.add(log)
        await session.commit()

    # Check with default threshold (5)
    result_default = check_suspicious_activity.apply_async(
        args=(60, 5, False, 3)
    ).get(timeout=30)

    # Check with org threshold (15)
    result_org = check_suspicious_activity.apply_async(
        args=(60, 15, False, 3)
    ).get(timeout=30)

    print(f"With threshold 5: {len(result_default['failed_login_alerts'])} alerts")
    print(f"With threshold 15: {len(result_org['failed_login_alerts'])} alerts")

asyncio.run(test_threshold())
```

**Expected Output:**
```
With threshold 5: 1 alerts
With threshold 15: 0 alerts
```

---

## Manual Testing with Real Services

### Testing Email Delivery

#### Configure SMTP

```bash
# Add to .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

#### Send Test Email

```python
from tasks.security_alerts import send_security_alert
from unittest.mock import MagicMock

task = MagicMock()

alert_data = {
    "user_id": str(uuid4()),
    "ip_address": "192.168.1.100",
    "failed_count": 10,
    "severity": "high",
}

result = send_security_alert(
    task,
    alert_type="failed_logins",
    recipient_email="your_email@gmail.com",
    alert_data=alert_data,
)

print(result)
```

**Verification:**
- Check your email inbox
- Verify subject line and content
- Verify formatting and recommended actions

### Testing SMS Delivery (Twilio)

#### Configure Twilio

```bash
# Add to .env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+15551234567
```

#### Send Test SMS

```python
from tasks.security_alerts import send_security_alert
from unittest.mock import MagicMock

task = MagicMock()

alert_data = {
    "user_id": str(uuid4()),
    "ip_address": "192.168.1.100",
    "failed_count": 10,
}

result = send_security_alert(
    task,
    alert_type="failed_logins",
    recipient_phone="+15559876543",  # Your phone number
    alert_data=alert_data,
)

print(result)
```

**Verification:**
- Check your phone for SMS
- Verify message format
- Verify failed count and IP address

### Testing Webhook Delivery

#### Use httpbin for Testing

```python
from tasks.security_alerts import send_security_alert_webhook
from unittest.mock import MagicMock

task = MagicMock()
task.update_state = MagicMock()

alert_data = {
    "user_id": str(uuid4()),
    "ip_address": "192.168.1.100",
    "failed_count": 10,
    "severity": "high",
}

result = send_security_alert_webhook(
    task,
    alert_type="failed_logins",
    webhook_url="https://httpbin.org/post",
    webhook_secret="supersecretkey",
    alert_data=alert_data,
)

print(result)
```

**Verification:**
- Check httpbin response
- Verify payload structure
- Verify HMAC signature header (if secret provided)

### Testing Slack Delivery

#### Create Slack Webhook

1. Go to https://api.slack.com/apps
2. Create a new app → "Incoming Webhooks"
3. Activate Incoming Webhooks
4. Copy webhook URL

#### Send Test Slack Message

```python
from tasks.security_alerts import send_security_alert_slack
from unittest.mock import MagicMock

task = MagicMock()
task.update_state = MagicMock()

alert_data = {
    "user_id": str(uuid4()),
    "ip_address": "192.168.1.100",
    "failed_count": 10,
    "severity": "high",
}

result = send_security_alert_slack(
    task,
    alert_type="failed_logins",
    slack_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    alert_data=alert_data,
)

print(result)
```

**Verification:**
- Check Slack channel
- Verify message formatting
- Verify color based on severity
- Verify emoji and header

---

## Troubleshooting Common Issues

### Issue: "Celery worker not responding"

**Cause:** Celery worker not running or not connected to Redis

**Solution:**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check Celery worker
celery -A celery_app inspect active

# Restart worker
celery -A celery_app worker --loglevel=info --concurrency=1
```

### Issue: "No alerts detected despite failed logins"

**Cause:** Failed logins outside time window or below threshold

**Solution:**
```python
# Check audit logs directly
import asyncio
from database import async_session_maker
from models.audit_log import AuditLog, AuditActionType
from datetime import datetime, timedelta

async def check_logs():
    async with async_session_maker() as session:
        from sqlalchemy import select, func
        stmt = select(func.count(AuditLog.id)).where(
            AuditLog.action_type == AuditActionType.LOGIN_FAILED,
            AuditLog.created_at >= datetime.utcnow() - timedelta(minutes=60)
        )
        result = await session.execute(stmt)
        count = result.scalar()
        print(f"Failed logins in last 60 minutes: {count}")

asyncio.run(check_logs())
```

### Issue: "Webhook delivery fails"

**Cause:** Invalid URL, network issues, or endpoint not responding

**Solution:**
```bash
# Test webhook URL manually
curl -X POST "https://your-webhook-url.com" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Check network connectivity
ping your-webhook-url.com

# Use httpbin for testing
curl -X POST "https://httpbin.org/post" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Issue: "Slack webhook rejected"

**Cause:** Invalid Slack webhook URL format

**Solution:**
```python
# Verify Slack webhook URL format
url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
assert url.startswith("https://hooks.slack.com/"), "Invalid Slack webhook URL"

# Test with Slack's webhook validator
# https://api.slack.com/messaging/webhooks
```

### Issue: "Organization config not being used"

**Cause:** Security config not created or not properly linked

**Solution:**
```python
import asyncio
from database import async_session_maker
from models.security_config import SecurityConfig
from sqlalchemy import select

async def check_config():
    async with async_session_maker() as session:
        stmt = select(SecurityConfig).where(
            SecurityConfig.organization_id == your_org_id
        )
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            print(f"Config found: threshold={config.failed_login_threshold}")
        else:
            print("No config found for organization")

asyncio.run(check_config())
```

---

## Success Criteria

### Unit Tests
- [ ] All suspicious activity detection tests pass (8+ tests)
- [ ] All alert notification delivery tests pass (8+ tests)
- [ ] All webhook delivery tests pass (4+ tests)
- [ ] All Slack delivery tests pass (3+ tests)
- [ ] All multi-channel delivery tests pass (3+ tests)
- [ ] All helper function tests pass (15+ tests)
- [ ] All database query function tests pass (4+ tests)
- [ ] Coverage > 80% for security_alerts.py

### Integration Tests
- [ ] All suspicious activity detection tests pass (6+ tests)
- [ ] All alert notification delivery tests pass (6+ tests)
- [ ] All webhook delivery tests pass (3+ tests)
- [ ] All Slack delivery tests pass (3+ tests)
- [ ] All multi-channel delivery tests pass (2+ tests)
- [ ] All organization configuration tests pass (4+ tests)
- [ ] All audit logging tests pass (3+ tests)
- [ ] All comprehensive workflow tests pass (2+ tests)

### End-to-End Verification
- [ ] Failed login events trigger security check task
- [ ] Celery task executes successfully
- [ ] Alert notifications delivered (email/SMS/webhook/Slack)
- [ ] Organization-specific configurations respected
- [ ] Audit logs created for all security events

### Manual Verification
- [ ] Can trigger failed login event via audit logs
- [ ] Security check Celery task executes and detects threats
- [ ] Email alert received (with SMTP configured)
- [ ] SMS alert received (with Twilio configured)
- [ ] Webhook delivered successfully (tested with httpbin)
- [ ] Slack message received (with webhook configured)
- [ ] Can configure alert thresholds per organization
- [ ] Audit logs capture all security events

---

## Test Coverage Summary

| Component | Tests | Coverage |
|-----------|-------|----------|
| Suspicious Activity Detection | 14 | 85%+ |
| Alert Notification Delivery | 14 | 85%+ |
| Webhook Delivery | 7 | 85%+ |
| Slack Delivery | 6 | 85%+ |
| Multi-Channel Delivery | 5 | 85%+ |
| Helper Functions | 15 | 90%+ |
| Database Queries | 7 | 85%+ |
| Organization Config | 4 | 80%+ |
| Audit Logging | 3 | 85%+ |
| Comprehensive Workflow | 2 | 80%+ |
| **Total** | **77+** | **85%+** |

---

## Quick Test Command

```bash
# Run all security alerts tests
cd backend
pytest tests/test_security_alerts.py tests/integration/test_security_alerts_e2e.py -v \
  --cov=tasks/security_alerts \
  --cov-report=term-missing \
  --cov-report=html
```

**Expected output:**
```
======================== test session starts =========================
collected 77+ items

tests/test_security_alerts.py .................................... [58%]
tests/integration/test_security_alerts_e2e.py .................... [100%]

---------- coverage: platform linux, python 3.11 ----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
tasks/security_alerts.py              800    120    85%
-------------------------------------------------------
TOTAL                                 800    120    85%

======================== 77+ passed in 15.23s =========================
```

---

## Additional Verification Commands

### Check Celery Worker Status

```bash
# Check active workers
celery -A celery_app inspect active

# Check registered tasks
celery -A celery_app inspect registered

# Check worker statistics
celery -A celery_app inspect stats
```

### Verify Security Tasks Registered

```bash
celery -A celery_app inspect registered | grep security_alert
```

**Expected output:**
```
* tasks.security_alerts.check_suspicious_activity
* tasks.security_alerts.send_security_alert
* tasks.security_alerts.send_security_alert_webhook
* tasks.security_alerts.send_security_alert_slack
* tasks.security_alerts.send_security_alert_multi_channel
```

### Monitor Celery Logs

```bash
# Tail worker logs
celery -A celery_app worker --loglevel=info

# Monitor task execution
celery -A celery_app events
```

---

## Next Steps

After successful verification:

1. **Configure Production Settings**: Set up real SMTP and Twilio credentials
2. **Set Up Monitoring**: Configure alerts for Celery task failures
3. **Schedule Periodic Checks**: Use Celery Beat for regular security scans
4. **Configure Organization Policies**: Set organization-specific thresholds
5. **Test with Real Users**: Run pilot with actual users and organizations

---

## Document Version

- **Version**: 1.0
- **Last Updated**: 2026-02-04
- **Author**: Auto-Claude (Subtask 16-5)
- **Related Spec**: 073-advanced-security-features-sso-audit-logs-2fa
