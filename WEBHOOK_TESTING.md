# Webhook Testing Documentation

## Overview

This document describes the webhook reception and processing flow testing for HRIS/ATS integrations.

## Test Files

### 1. `test_webhook_flow.py` - Comprehensive Python Test Script

A comprehensive async Python script that tests the complete webhook flow for all platforms.

**Features:**
- Creates test integrations with webhook secrets
- Sends webhook payloads with HMAC-SHA256 signature verification
- Verifies webhook reception and validation
- Checks sync log entry creation in database
- Tests all 5 platforms (Greenhouse, Lever, Workday, BambooHR, Ashby)
- Provides detailed test results and error reporting
- Includes cleanup functionality

**Requirements:**
```bash
pip install httpx sqlalchemy
```

**Usage:**
```bash
# Run all webhook flow tests
python test_webhook_flow.py

# Clean up test integrations only
python test_webhook_flow.py --cleanup

# With custom API URL
API_BASE_URL=http://localhost:8000 python test_webhook_flow.py
```

**What it tests:**
1. ✓ Send test webhook payload to webhook endpoint
2. ✓ Verify webhook is received and validated
3. ✓ Check that data is processed and stored
4. ✓ Verify sync log entry created

### 2. `test_webhooks.sh` - Shell Script Test

A bash script that uses curl to test webhook endpoints without requiring Python dependencies.

**Requirements:**
- `curl` - HTTP client
- `jq` - JSON processor (optional, for pretty output)
- `openssl` - For HMAC signature generation

**Usage:**
```bash
# Make executable
chmod +x test_webhooks.sh

# Run tests
./test_webhooks.sh

# With custom API URL
API_BASE_URL=http://localhost:8000 ./test_webhooks.sh

# With custom webhook secret
WEBHOOK_SECRET=my_secret ./test_webhooks.sh
```

**Test cases:**
1. Greenhouse candidate.created webhook
2. Greenhouse candidate.updated webhook
3. Lever candidate.created webhook
4. Lever opportunity.updated webhook
5. Workday employee.created webhook
6. BambooHR employee_added webhook
7. Ashby candidate.created webhook
8. Invalid signature (should fail with 401)
9. Invalid platform (should fail with 400)
10. List webhook endpoints

## Verification Steps

### Step 1: Send Test Webhook Payload

The test scripts send POST requests to webhook endpoints:

```bash
POST /api/webhooks/{platform}
Headers:
  Content-Type: application/json
  X-Webhook-Signature: sha256=<hmac_signature>
Body:
  {
    "event": "candidate.created",
    "data": { ... }
  }
```

### Step 2: Verify Webhook is Received and Validated

Expected response:
```json
{
  "success": true,
  "message": "Webhook received and processed for greenhouse",
  "event_id": "<sync_log_uuid>"
}
```

Validation checks:
- ✓ Platform is valid (workday, greenhouse, lever, bamboohr, ashby)
- ✓ JSON payload is well-formed
- ✓ Signature matches webhook secret (HMAC-SHA256)
- ✓ Active integration exists for platform
- ✓ Event type is recognized

### Step 3: Check Data Processing and Storage

The webhook endpoint processes the event:

1. **Event parsing**: Event type and data extracted
2. **Sync decision**: Determines if sync should be triggered based on event type
3. **Duplicate check**: Verifies no sync is already in progress
4. **Sync log creation**: Creates `SyncLog` entry with PENDING status
5. **Audit logging**: Logs webhook receipt for audit trail

Event types that trigger syncs:
- `candidate.created`, `candidate.updated`, `candidate.deleted`
- `employee.created`, `employee.updated`, `employee.terminated`
- `vacancy.created`, `vacancy.updated`, `vacancy.closed`
- `job.created`, `job.updated`, `job.closed`

### Step 4: Verify Sync Log Entry Created

Query the database to verify sync log:

```sql
SELECT
    id,
    integration_id,
    sync_type,
    status,
    records_processed,
    sync_metadata
FROM sync_logs
WHERE sync_metadata->>'triggered_by' = 'webhook'
ORDER BY created_at DESC
LIMIT 10;
```

Expected sync log entry:
```json
{
  "id": "<uuid>",
  "integration_id": "<uuid>",
  "sync_type": "incremental_sync",
  "status": "pending",
  "records_processed": 0,
  "records_successful": 0,
  "records_failed": 0,
  "sync_metadata": {
    "triggered_by": "webhook",
    "webhook_event": "candidate.created",
    "webhook_data": { ... }
  }
}
```

## Manual Testing with curl

### Test a webhook manually:

```bash
# Set variables
WEBHOOK_URL="http://localhost:8000/api/webhooks/greenhouse"
WEBHOOK_SECRET="test_webhook_secret_12345"
PAYLOAD='{"event":"candidate.created","data":{"candidate_id":12345,"first_name":"John","last_name":"Doe","email":"john.doe@example.com"}}'

# Generate signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print "sha256="$2}')

# Send webhook
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -d "$PAYLOAD" \
  "$WEBHOOK_URL"
```

### Test webhook validation endpoint:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "greenhouse",
    "payload": {"event": "candidate.created", "data": {}},
    "signature": "sha256=..."
  }' \
  "http://localhost:8000/api/webhooks/validate"
```

### List webhook endpoints:

```bash
curl "http://localhost:8000/api/webhooks/"
```

## Platform-Specific Webhook Formats

### Greenhouse

**Events:** `candidate.created`, `candidate.updated`, `application.created`, `application.updated`, `job.created`, `job.updated`

**Signature Header:** `X-Webhook-Signature: sha256=<hmac>`

**Example Payload:**
```json
{
  "event": "candidate.created",
  "data": {
    "candidate_id": 12345,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "application_id": 98765
  }
}
```

### Lever

**Events:** `candidate.created`, `candidate.updated`, `opportunity.created`, `opportunity.updated`, `posting.created`, `posting.updated`

**Signature Header:** `X-Webhook-Signature: sha256=<hmac>`

**Example Payload:**
```json
{
  "event": "candidate.created",
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "name": "Jane Doe",
    "email": "jane.doe@example.com"
  }
}
```

### Workday

**Events:** `employee.created`, `employee.updated`, `candidate.created`, `candidate.updated`

**Signature Header:** `X-Webhook-Signature: sha256=<hmac>`

**Example Payload:**
```json
{
  "event": "employee.created",
  "data": {
    "worker_id": "ABC123",
    "name": "Bob Johnson",
    "email": "bob.johnson@company.com",
    "position": "Software Engineer"
  }
}
```

### BambooHR

**Events:** `employee_added`, `employee_updated`, `time_off_requested`

**Signature Header:** `X-Webhook-Signature: sha256=<hmac>`

**Example Payload:**
```json
{
  "event": "employee_added",
  "data": {
    "id": "101",
    "firstName": "Charlie",
    "lastName": "Brown",
    "email": "charlie.brown@company.com",
    "jobTitle": "Product Manager"
  }
}
```

### Ashby

**Events:** `candidate.created`, `candidate.updated`, `application.created`, `application.updated`, `job.posting.created`, `job.posting.updated`

**Signature Header:** `X-Webhook-Signature: sha256=<hmac>`

**Example Payload:**
```json
{
  "event": "candidate.created",
  "data": {
    "id": "ashby_candidate_123",
    "name": "Diana Prince",
    "email": "diana.prince@example.com"
  }
}
```

## Common Issues and Troubleshooting

### Issue: "No active integration found"

**Cause:** No integration with status=ACTIVE exists for the platform.

**Solution:** Create a test integration:
```sql
INSERT INTO integrations (name, platform, status, credentials, sync_enabled)
VALUES (
  'Test Greenhouse',
  'GREENHOUSE',
  'ACTIVE',
  '{"api_key": "test", "webhook_secret": "test_webhook_secret_12345"}',
  true
);
```

### Issue: "Invalid webhook signature"

**Cause:** Signature doesn't match webhook secret.

**Solution:** Ensure you're using the same secret to generate the signature:
```python
import hmac, hashlib
signature = f"sha256={hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()}"
```

### Issue: Webhook received but no sync triggered

**Cause:** Event type may not require sync, or sync is already in progress.

**Solution:** Check the webhook event type against the sync trigger logic in `webhooks.py`. Only events indicating data changes trigger syncs.

### Issue: Sync log created but status is stuck at PENDING

**Cause:** Celery worker may not be running to process the sync task.

**Solution:** Start the Celery worker:
```bash
cd backend
celery -A celery_app worker -l info
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Webhook Tests

on: [push, pull_request]

jobs:
  test-webhooks:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: agenthr_test
          POSTGRES_USER: agenthr
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run migrations
        run: |
          cd backend
          alembic upgrade head

      - name: Start backend server
        run: |
          cd backend
          uvicorn main:app &
          sleep 5

      - name: Run webhook flow tests
        run: |
          python test_webhook_flow.py
```

## Security Considerations

### Webhook Signature Verification

All webhooks should include HMAC-SHA256 signature verification:

```python
# Server-side verification
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
    return hmac.compare_digest(signature, expected)
```

### Best Practices

1. **Always use HTTPS in production**
2. **Rotate webhook secrets regularly**
3. **Store secrets securely (encrypted at rest)**
4. **Log all webhook events for audit trail**
5. **Implement rate limiting on webhook endpoints**
6. **Return 200 OK immediately, process asynchronously**
7. **Validate all webhook payloads before processing**

## Monitoring and Observability

### Key Metrics to Track

- Webhook reception rate (per platform)
- Webhook processing latency
- Signature verification failures
- Sync trigger rate from webhooks
- Webhook processing errors

### Example Prometheus Queries

```promql
# Webhook reception rate
rate(webhook_received_total[5m])

# Webhook errors by platform
rate(webhook_errors_total{platform="greenhouse"}[5m])

# Syncs triggered from webhooks
rate(syncs_triggered_total{trigger="webhook"}[5m])
```

### Logging

The webhook endpoint logs the following events:

- Webhook received (INFO)
- Signature verification success/failure (WARNING)
- Sync triggered from webhook (INFO)
- Webhook processing errors (ERROR)

Example log entries:
```
INFO:api.webhooks:Webhook processed successfully: greenhouse - candidate.created (integration: 123e4567-e89b-12d3-a456-426614174000)
INFO:api.webhooks:Triggered incremental_sync sync from webhook event candidate.created (sync_id: 987fcdeb-51a2-43f1-a456-426614174000)
WARNING:api.webhooks:Invalid webhook signature for platform greenhouse (integration: 123e4567-e89b-12d3-a456-426614174000)
```

## Next Steps

After webhook testing:

1. ✓ Verify webhooks are received and validated
2. ✓ Confirm sync logs are created
3. ✓ Test Celery worker processing of webhook-triggered syncs
4. ✓ Verify actual data sync with external platforms
5. ✓ Set up monitoring and alerting
6. ✓ Document webhook setup process for end users
