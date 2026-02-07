# Audit Logs Comprehensive Verification Guide

This document provides comprehensive instructions for verifying the audit logs functionality, including security event logging, filtering, export capabilities, and data completeness.

## Table of Contents

1. [Running Tests](#running-tests)
2. [Test Coverage Summary](#test-coverage-summary)
3. [End-to-End Verification Steps](#end-to-end-verification-steps)
4. [Manual Testing Procedures](#manual-testing-procedures)
5. [Troubleshooting Common Issues](#troubleshooting-common-issues)
6. [Success Criteria](#success-criteria)

---

## Running Tests

### Prerequisites

- Python 3.10+ installed
- Virtual environment activated
- Test dependencies installed: `pytest`, `pytest-asyncio`, `httpx`, `aiosqlite`

### Unit Tests

Run the audit logs API unit tests:

```bash
cd backend
pytest tests/test_audit_logs_api.py -v
```

Run with coverage:

```bash
pytest tests/test_audit_logs_api.py -v --cov=api.audit_logs --cov-report=term-missing
```

### Integration Tests

Run the security event integration tests:

```bash
cd backend
pytest tests/integration/test_audit_logs_security_e2e.py -v
```

Run the existing audit logs integration tests:

```bash
cd backend
pytest tests/integration/test_audit_logs_e2e.py -v
```

### All Audit Logs Tests

Run all audit logs tests together:

```bash
cd backend
pytest tests/test_audit_logs_api.py tests/integration/test_audit_logs_e2e.py tests/integration/test_audit_logs_security_e2e.py -v
```

### Test Output

Expected test count:
- `test_audit_logs_api.py`: 45+ unit tests
- `test_audit_logs_security_e2e.py`: 20+ integration tests
- `test_audit_logs_e2e.py`: 12+ existing integration tests

**Total: 77+ tests**

---

## Test Coverage Summary

### Unit Tests (test_audit_logs_api.py)

#### API Endpoint Testing
- ✅ Get audit logs - empty state
- ✅ Get audit logs - with data
- ✅ Action type filtering (valid and invalid)
- ✅ Security action type filtering (SSO_LOGIN, TFA_ENABLED, TFA_DISABLED, SESSION_REVOKED, IP_BLOCKED)
- ✅ Entity type filtering
- ✅ Entity ID filtering (valid and invalid UUID)
- ✅ User ID filtering (valid and invalid UUID)
- ✅ Organization ID filtering (valid and invalid UUID)
- ✅ Date range filtering (start_date, end_date, combined)
- ✅ Date format validation (ISO 8601, with Z suffix)
- ✅ Pagination (limit, offset, max enforcement)
- ✅ Log ordering (created_at descending)
- ✅ Combined filters (action + user, date range + action)
- ✅ Response structure validation
- ✅ Timestamp format validation (ISO 8601)
- ✅ Get action types endpoint
- ✅ Get entity types endpoint
- ✅ All security events are loggable

#### Validation Testing
- ✅ Invalid action type returns 400
- ✅ Invalid UUID formats return 400
- ✅ Invalid date formats return 400
- ✅ Pagination limits enforced (min 1, max 1000)
- ✅ All security action types are valid

### Integration Tests (test_audit_logs_security_e2e.py)

#### Security Event Logging
- ✅ SSO login event logging
- ✅ SSO login includes timestamp
- ✅ 2FA enabled event logging
- ✅ 2FA disabled with before_value
- ✅ 2FA method switch logging
- ✅ Session revocation event logging
- ✅ Revoke all sessions creates multiple logs
- ✅ IP blocked event logging
- ✅ IP blocked with whitelist reference

#### Security Event Filtering
- ✅ Filter by SSO_LOGIN events
- ✅ Filter by all security event types
- ✅ Date range filtering for security events
- ✅ Combined filters work correctly

#### CSV Export
- ✅ CSV export includes all fields
- ✅ CSV export respects filtering

#### Data Completeness
- ✅ All security events include user, action, timestamp
- ✅ Security event metadata completeness (IP, user agent, organization)
- ✅ Before/after values for sensitive operations

#### Statistics
- ✅ Security event statistics by user
- ✅ Security event statistics by organization

### Existing Integration Tests (test_audit_logs_e2e.py)

- ✅ Resume operations generate audit logs
- ✅ Vacancy operations generate audit logs
- ✅ Audit log filtering by various criteria
- ✅ CSV export functionality
- ✅ Cleanup task functionality
- ✅ API endpoints validation
- ✅ Pagination

---

## End-to-End Verification Steps

### 1. Verify All Security Events Are Logged

#### Step 1.1: Test SSO Login Event

```bash
# Use curl to simulate SSO login event
curl -X POST http://localhost:8000/api/audit-logs/ \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "sso_login",
    "entity_type": "sso_config",
    "user_id": "'$USER_ID'",
    "organization_id": "'$ORG_ID'",
    "ip_address": "192.168.1.100",
    "action_data": {"provider": "okta", "email": "user@example.com"}
  }'
```

Expected response:
```json
{
  "id": "...",
  "action_type": "sso_login",
  "user_id": "...",
  "created_at": "2026-02-04T10:30:00"
}
```

#### Step 1.2: Test 2FA Events

```bash
# Test 2FA enabled
curl -X POST http://localhost:8000/api/2fa/setup \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Test 2FA disabled
curl -X POST http://localhost:8000/api/2fa/disable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

#### Step 1.3: Test Session Revocation

```bash
# Revoke a session
curl -X DELETE http://localhost:8000/api/sessions/$SESSION_ID \
  -H "Authorization: Bearer $TOKEN"

# Revoke all sessions
curl -X POST http://localhost:8000/api/sessions/revoke-all \
  -H "Authorization: Bearer $TOKEN"
```

#### Step 1.4: Verify Events in Audit Logs

```bash
# Get all security events for a user
curl "http://localhost:8000/api/audit-logs/?user_id=$USER_ID&limit=100"
```

Verify response includes:
- `sso_login` events
- `2fa_enabled` events
- `2fa_disabled` events
- `session_revoked` events
- Each event has `user_id`, `action_type`, `created_at`

### 2. Test Audit Log Filtering by Event Type

#### Step 2.1: Filter by Individual Security Event Types

```bash
# Filter SSO login events
curl "http://localhost:8000/api/audit-logs/?action_type=sso_login"

# Filter 2FA enabled events
curl "http://localhost:8000/api/audit-logs/?action_type=2fa_enabled"

# Filter session revocation events
curl "http://localhost:8000/api/audit-logs/?action_type=session_revoked"

# Filter IP blocked events
curl "http://localhost:8000/api/audit-logs/?action_type=ip_blocked"
```

Expected: Each request returns only logs matching the specified `action_type`.

#### Step 2.2: Verify Invalid Action Type Returns Error

```bash
curl "http://localhost:8000/api/audit-logs/?action_type=invalid_event"
```

Expected response:
```json
{
  "detail": "Invalid action_type: invalid_event. Valid types are: sso_login, 2fa_enabled, ..."
}
```

Status code: 400

### 3. Test Audit Log Date Range Filtering

#### Step 3.1: Filter by Start Date

```bash
# Get logs from the last 24 hours
START_DATE=$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S)
curl "http://localhost:8000/api/audit-logs/?start_date=$START_DATE"
```

#### Step 3.2: Filter by End Date

```bash
# Get logs before a specific date
END_DATE=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)
curl "http://localhost:8000/api/audit-logs/?end_date=$END_DATE"
```

#### Step 3.3: Filter by Date Range

```bash
# Get logs within a specific range
START_DATE=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)
END_DATE=$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S)
curl "http://localhost:8000/api/audit-logs/?start_date=$START_DATE&end_date=$END_DATE"
```

#### Step 3.4: Verify Invalid Date Format Returns Error

```bash
curl "http://localhost:8000/api/audit-logs/?start_date=invalid-date"
```

Expected response:
```json
{
  "detail": "Invalid start_date format: invalid-date. Use ISO 8601 format."
}
```

Status code: 400

### 4. Export Audit Logs as CSV

#### Step 4.1: Get All Logs for Export

```bash
# Fetch logs with maximum limit
curl "http://localhost:8000/api/audit-logs/?limit=1000" > audit_logs.json
```

#### Step 4.2: Convert to CSV (Python Example)

```python
import json
import csv
import sys

# Load JSON data
with open('audit_logs.json', 'r') as f:
    data = json.load(f)

# Convert to CSV
with open('audit_logs.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    # Header
    writer.writerow([
        'Timestamp', 'Action', 'Entity Type', 'Entity ID',
        'User ID', 'Organization ID', 'IP Address', 'User Agent', 'Reason'
    ])

    # Rows
    for log in data['logs']:
        writer.writerow([
            log['created_at'],
            log['action_type'],
            log['entity_type'] or '',
            log['entity_id'] or '',
            log['user_id'] or '',
            log['organization_id'] or '',
            log['ip_address'] or '',
            log['user_agent'] or '',
            log['reason'] or '',
        ])

print(f"Exported {len(data['logs'])} audit logs to audit_logs.csv")
```

#### Step 4.3: Export Security Events Only

```bash
# Get only security events
curl "http://localhost:8000/api/audit-logs/?action_type=sso_login&limit=1000" > sso_logs.json
curl "http://localhost:8000/api/audit-logs/?action_type=2fa_enabled&limit=1000" > 2fa_enabled.json
curl "http://localhost:8000/api/audit-logs/?action_type=2fa_disabled&limit=1000" > 2fa_disabled.json
curl "http://localhost:8000/api/audit-logs/?action_type=session_revoked&limit=1000" > sessions.json
curl "http://localhost:8000/api/audit-logs/?action_type=ip_blocked&limit=1000" > ip_blocked.json
```

#### Step 4.4: Verify CSV Format

```bash
# Check CSV file
head -n 5 audit_logs.csv

# Verify row count
wc -l audit_logs.csv
```

Expected output:
- First row contains headers
- Subsequent rows contain log data
- Total rows = log count + 1 (header)

### 5. Verify Audit Log Includes User, Action, Timestamp

#### Step 5.1: Check User Field

```bash
# Get logs and verify user_id field
curl "http://localhost:8000/api/audit-logs/?limit=10" | jq '.logs[] | .user_id'
```

Expected:
- All logs have a `user_id` field (UUID or null for system actions like IP_BLOCKED)

#### Step 5.2: Check Action Field

```bash
# Get logs and verify action_type field
curl "http://localhost:8000/api/audit-logs/?limit=10" | jq '.logs[] | .action_type'
```

Expected:
- All logs have a non-null `action_type` field
- Action type is one of the valid types (e.g., `sso_login`, `2fa_enabled`, etc.)

#### Step 5.3: Check Timestamp Field

```bash
# Get logs and verify created_at field
curl "http://localhost:8000/api/audit-logs/?limit=10" | jq '.logs[] | .created_at'
```

Expected:
- All logs have a `created_at` field
- Timestamp is in ISO 8601 format (e.g., `2026-02-04T10:30:00`)
- Timestamp can be parsed with `date -d`

#### Step 5.4: Verify Complete Security Event Log Entry

```bash
# Get a specific security event log
curl "http://localhost:8000/api/audit-logs/?action_type=sso_login&limit=1" | jq '.logs[0]'
```

Expected structure:
```json
{
  "id": "uuid",
  "action_type": "sso_login",
  "entity_type": "sso_config",
  "entity_id": "uuid",
  "user_id": "uuid",
  "organization_id": "uuid",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "action_data": {...},
  "before_value": null,
  "after_value": null,
  "reason": null,
  "created_at": "2026-02-04T10:30:00"
}
```

---

## Manual Testing Procedures

### Frontend Testing

#### Test 1: Access Audit Logs Page

1. Navigate to `http://localhost:5173/recruiter/audit-logs`
2. Verify page loads without errors
3. Verify stats cards display (Total Logs, Security Events, etc.)
4. Verify filter controls are visible

#### Test 2: Filter Security Events

1. Toggle "Security Events Only" switch
2. Verify only security events are displayed
3. Verify security icon appears in action column
4. Verify Security Events count updates

#### Test 3: Filter by Action Type

1. Select "SSO Login" from Action Type dropdown
2. Verify only SSO_LOGIN events are shown
3. Try selecting different action types
4. Clear filters and verify all logs return

#### Test 4: Filter by Date Range

1. Set Start Date to 7 days ago
2. Set End Date to today
3. Verify only logs within date range are shown
4. Clear date filters

#### Test 5: Export to CSV

1. Apply a filter (e.g., Security Events Only)
2. Click "Export" button
3. Verify CSV file downloads
4. Open CSV and verify:
   - Headers are correct
   - Filtered logs are included
   - Timestamps are readable
   - All fields are present

#### Test 6: View Log Details

1. Click on "View Details" icon for a security event
2. Verify dialog opens with complete log information
3. Verify all fields are displayed:
   - Log ID
   - Timestamp
   - Action Type
   - Entity
   - User
   - Organization
   - IP Address
   - User Agent
   - Action Data (if present)
   - Before/After Values (if present)

### Backend API Testing

#### Test 1: Create Audit Log via API

```python
import requests
import json
from uuid import uuid4

# Create a test audit log
url = "http://localhost:8000/api/audit-logs/"
headers = {"Content-Type": "application/json"}
data = {
    "action_type": "sso_login",
    "entity_type": "sso_config",
    "user_id": str(uuid4()),
    "organization_id": str(uuid4()),
    "ip_address": "192.168.1.100",
    "action_data": {"provider": "okta", "email": "test@example.com"}
}

response = requests.post(url, headers=headers, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

#### Test 2: Verify Audit Log Retrieval

```python
import requests

# Get audit logs
url = "http://localhost:8000/api/audit-logs/"
params = {
    "limit": 10,
    "offset": 0
}

response = requests.get(url, params=params)
data = response.json()

print(f"Total logs: {data['total_count']}")
for log in data['logs']:
    print(f"- {log['created_at']}: {log['action_type']} (User: {log['user_id']})")
```

#### Test 3: Test All Filter Combinations

```python
import requests
from datetime import datetime, timedelta

base_url = "http://localhost:8000/api/audit-logs/"

# Test 1: Action type filter
response = requests.get(base_url, params={"action_type": "sso_login"})
print(f"SSO logs count: {response.json()['total_count']}")

# Test 2: Date range filter
start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
end_date = datetime.utcnow().isoformat()
response = requests.get(base_url, params={"start_date": start_date, "end_date": end_date})
print(f"Logs in date range: {response.json()['total_count']}")

# Test 3: Combined filters
user_id = "some-uuid-here"
response = requests.get(base_url, params={
    "action_type": "2fa_enabled",
    "user_id": user_id,
    "limit": 10
})
print(f"Filtered logs count: {response.json()['total_count']}")
```

---

## Troubleshooting Common Issues

### Issue 1: Tests Fail with "Invalid action_type"

**Problem**: Action type not recognized by the API.

**Solution**:
1. Check that the action type is defined in `AuditActionType` enum in `backend/models/audit_log.py`
2. Verify the action type uses lowercase and underscores (e.g., `sso_login`, not `SSO_Login`)
3. Run `GET /api/audit-logs/types` to see all valid action types

### Issue 2: Date Filtering Returns No Results

**Problem**: Date range filters exclude expected logs.

**Solution**:
1. Verify date format is ISO 8601: `2026-02-04T10:30:00`
2. For UTC times, append `Z`: `2026-02-04T10:30:00Z`
3. Check that dates are not timezone-confused (local vs UTC)
4. Use broader date ranges for testing

### Issue 3: CSV Export Missing Data

**Problem**: Exported CSV doesn't contain all expected fields.

**Solution**:
1. Verify the API response includes all fields
2. Check that the CSV conversion logic includes all required columns
3. Ensure `action_data`, `before_value`, and `after_value` JSON is properly serialized
4. Verify special characters are properly escaped in CSV

### Issue 4: Security Events Not Being Logged

**Problem**: Security actions don't create audit logs.

**Solution**:
1. Verify audit logging code exists in the security feature endpoints:
   - `backend/api/sso.py` (SSO login)
   - `backend/api/two_factor.py` (2FA enable/disable)
   - `backend/api/sessions.py` (session revocation)
   - `backend/middleware/ip_whitelist_middleware.py` (IP blocking)
2. Check that `create_audit_log()` is called with correct parameters
3. Verify database session is committed after creating audit log
4. Check for exceptions being caught and swallowed

### Issue 5: Missing User or Organization ID

**Problem**: Audit logs have null `user_id` or `organization_id`.

**Solution**:
1. Verify the authenticated user context is available in the endpoint
2. Check that `user_id` and `organization_id` are passed to audit log creation
3. For system actions (like IP blocking), `user_id` may legitimately be null
4. Ensure authentication middleware is working correctly

### Issue 6: Timestamp Inconsistencies

**Problem**: `created_at` timestamps are inconsistent or missing.

**Solution**:
1. Verify the `TimestampMixin` is applied to `AuditLog` model
2. Check that `datetime.utcnow()` is used for consistent UTC timestamps
3. Verify database stores timestamps in UTC
4. Check for timezone conversion issues when displaying timestamps

---

## Success Criteria

All verification steps should pass with the following results:

### Test Execution
- ✅ All 77+ tests pass
- ✅ No test failures or errors
- ✅ Code coverage > 80% for audit logs API
- ✅ Integration tests cover all security event types

### Security Event Logging
- ✅ SSO_LOGIN events logged with provider and email
- ✅ TFA_ENABLED events logged with method
- ✅ TFA_DISABLED events logged with before_value
- ✅ SESSION_REVOKED events logged with session details
- ✅ IP_BLOCKED events logged with IP address

### Filtering
- ✅ Action type filtering works for all security events
- ✅ Invalid action types return 400 error
- ✅ Date range filtering works (start, end, combined)
- ✅ Invalid date formats return 400 error
- ✅ Combined filters work correctly (action + date + user)
- ✅ User ID filtering works
- ✅ Organization ID filtering works

### CSV Export
- ✅ All fields exported (user, action, timestamp, IP, user agent, etc.)
- ✅ CSV format is valid and parseable
- ✅ Export respects filters (security events only, date range, etc.)
- ✅ Special characters properly escaped
- ✅ Large exports work (up to 1000 records)

### Data Completeness
- ✅ All logs include `user_id` (or null for system actions)
- ✅ All logs include `action_type` (non-null)
- ✅ All logs include `created_at` (valid ISO 8601 timestamp)
- ✅ Security events include `ip_address` and `user_agent`
- ✅ Sensitive operations include `before_value` and `after_value`
- ✅ Security events include `organization_id`

### Frontend Functionality
- ✅ Audit logs page loads without errors
- ✅ Security events toggle works
- ✅ All filter controls work (action type, date range, user ID)
- ✅ Export button downloads CSV file
- ✅ Details dialog shows complete log information
- ✅ Stats cards display accurate counts

### API Endpoints
- ✅ `GET /api/audit-logs/` returns logs with filters
- ✅ `GET /api/audit-logs/types` returns all action types
- ✅ `GET /api/audit-logs/entity-types` returns common entity types
- ✅ 400 errors for invalid input (action type, UUID, date format)
- ✅ Pagination works (limit, offset)
- ✅ Logs ordered by `created_at` descending

---

## Additional Verification Commands

### Count Security Events by Type

```bash
# Count SSO login events
curl "http://localhost:8000/api/audit-logs/?action_type=sso_login" | jq '.total_count'

# Count 2FA enabled events
curl "http://localhost:8000/api/audit-logs/?action_type=2fa_enabled" | jq '.total_count'

# Count session revocation events
curl "http://localhost:8000/api/audit-logs/?action_type=session_revoked" | jq '.total_count'
```

### Get Recent Security Events

```bash
# Get last 10 security events (any type)
curl "http://localhost:8000/api/audit-logs/?limit=10" | \
  jq '.logs[] | select(.action_type == "sso_login" or .action_type == "2fa_enabled" or .action_type == "2fa_disabled" or .action_type == "session_revoked" or .action_type == "ip_blocked")'
```

### Verify All Security Event Types Are Defined

```bash
# Get all action types
curl "http://localhost:8000/api/audit-logs/types" | jq '.action_types'

# Verify security types are present
curl "http://localhost:8000/api/audit-logs/types" | \
  jq '.action_types | contains(["sso_login", "2fa_enabled", "2fa_disabled", "session_revoked", "ip_blocked", "login_success", "login_failed", "logout", "password_changed"])'
```

### Check Audit Log Schema

```bash
# Get a sample log and verify its structure
curl "http://localhost:8000/api/audit-logs/?limit=1" | \
  jq '.logs[0] | keys'
```

Expected keys:
```json
[
  "id",
  "action_type",
  "entity_type",
  "entity_id",
  "user_id",
  "organization_id",
  "ip_address",
  "user_agent",
  "action_data",
  "before_value",
  "after_value",
  "reason",
  "created_at"
]
```

---

## Summary

This verification guide covers:

1. **77+ automated tests** for audit logs functionality
2. **All 9 security event types** verified
3. **Comprehensive filtering** by action, date, user, organization
4. **CSV export** with all fields
5. **Data completeness** verification (user, action, timestamp)
6. **Frontend integration** testing procedures
7. **Troubleshooting guide** for common issues

When all tests pass and manual verification steps succeed, the audit logs feature is fully verified and ready for production use.
