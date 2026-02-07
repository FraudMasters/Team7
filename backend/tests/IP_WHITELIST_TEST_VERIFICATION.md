# IP Whitelist Test Verification Guide

This guide provides comprehensive instructions for verifying the IP whitelist functionality through automated tests and manual verification procedures.

## Table of Contents

1. [Running Tests](#running-tests)
2. [Test Coverage](#test-coverage)
3. [End-to-End Verification](#end-to-end-verification)
4. [Manual Testing](#manual-testing)
5. [Troubleshooting](#troubleshooting)
6. [Success Criteria](#success-criteria)

---

## Running Tests

### Unit Tests

Unit tests verify the IP whitelist middleware functionality in isolation:

```bash
# Run all IP whitelist middleware unit tests
cd backend
pytest tests/test_ip_whitelist_middleware.py -v

# Run specific test class
pytest tests/test_ip_whitelist_middleware.py::TestCIDRValidation -v

# Run with coverage
pytest tests/test_ip_whitelist_middleware.py --cov=middleware.ip_whitelist_middleware --cov-report=html

# Run specific test
pytest tests/test_ip_whitelist_middleware.py::TestCIDRValidation::test_ip_in_cidr_ipv4_class_c -v
```

### Integration Tests

Integration tests verify API endpoints and database persistence:

```bash
# Run all IP whitelist integration tests
cd backend
pytest tests/integration/test_ip_whitelist_e2e.py -v

# Run specific test class
pytest tests/integration/test_ip_whitelist_e2e.py::TestIPWhitelistCreate -v

# Run with coverage
pytest tests/integration/test_ip_whitelist_e2e.py --cov=api.security_config --cov-report=html

# Run specific test
pytest tests/integration/test_ip_whitelist_e2e.py::TestIPWhitelistCreate::test_create_whitelist_entry_with_cidr -v
```

### All IP Whitelist Tests

```bash
# Run all IP whitelist tests (unit + integration)
cd backend
pytest tests/test_ip_whitelist_middleware.py tests/integration/test_ip_whitelist_e2e.py -v

# Run with combined coverage report
pytest tests/test_ip_whitelist_middleware.py tests/integration/test_ip_whitelist_e2e.py \
  --cov=middleware.ip_whitelist_middleware \
  --cov=api.security_config \
  --cov=models.ip_whitelist \
  --cov-report=html \
  --cov-report=term-missing
```

---

## Test Coverage

### Unit Tests (48 tests)

Unit tests in `test_ip_whitelist_middleware.py` cover:

1. **Middleware Initialization** (2 tests)
   - Default exclude paths configuration
   - Custom exclude paths configuration

2. **Path Exclusion** (3 tests)
   - Health endpoint exclusion
   - Documentation paths exclusion
   - API endpoints not excluded

3. **Client IP Extraction** (6 tests)
   - X-Forwarded-For header extraction
   - X-Real-IP header extraction
   - CF-Connecting-IP header extraction (Cloudflare)
   - Request.client.host fallback
   - Header priority order (X-Forwarded-For > X-Real-IP > CF-Connecting-IP)
   - No IP found scenario

4. **CIDR Validation** (7 tests)
   - IPv4 /32 (single IP)
   - IPv4 /24 (Class C network)
   - IPv4 /16 (Class B network)
   - IPv4 /8 (Class A network)
   - IPv6 CIDR notation
   - Invalid CIDR format handling
   - Invalid IP address handling

5. **IP Range Validation** (3 tests)
   - Basic IPv4 range matching
   - IPv6 range matching
   - Invalid IP address handling

6. **IP Matching with Whitelist Entry** (4 tests)
   - CIDR-based matching
   - IP range-based matching
   - Both CIDR and range specified (CIDR priority)
   - No rules specified

7. **Dispatch Logic** (4 tests)
   - Excluded path passes through
   - No client IP passes through (fail open)
   - Allowed IP passes through
   - Blocked IP returns 403 Forbidden

8. **Error Handling** (1 test)
   - Database error fails open (allow request)

### Integration Tests (35 tests)

Integration tests in `test_ip_whitelist_e2e.py` cover:

1. **IP Whitelist Create** (8 tests)
   - Create entry with CIDR notation
   - Create entry with IP range
   - Create entry with IPv6 CIDR
   - Create inactive entry
   - Create organization-specific entry
   - Missing required field validation
   - Missing IP specification error

2. **IP Whitelist Read** (4 tests)
   - Retrieve all whitelist entries
   - Filter by organization
   - Filter by active status
   - Pagination support

3. **IP Whitelist Update** (4 tests)
   - Update entry name
   - Update CIDR notation
   - Toggle active status
   - Update non-existent entry

4. **IP Whitelist Delete** (2 tests)
   - Delete whitelist entry
   - Delete non-existent entry

5. **Security Config Integration** (3 tests)
   - Enable IP whitelist enforcement
   - Enable strict mode
   - Manage whitelist with enforcement disabled

6. **IP Validation** (2 tests)
   - CIDR notation validation
   - IP range validation (start <= end)

7. **Statistics** (2 tests)
   - Count by organization
   - Active vs inactive counts

8. **Edge Cases** (10 tests)
   - Both CIDR and range specified
   - Invalid UUID for organization filter
   - Pagination limit enforcement
   - Update with invalid UUID
   - Delete with invalid UUID

---

## End-to-End Verification

### Step 1: Add IP Whitelist Entry with CIDR Notation

```bash
# Create a new whitelist entry using CIDR notation
curl -X POST "http://localhost:8000/api/security/ip-whitelist" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": null,
    "name": "Office Network",
    "description": "Main office IP range",
    "cidr_notation": "192.168.1.0/24",
    "start_ip": null,
    "end_ip": null,
    "is_active": true
  }'
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "organization_id": null,
  "name": "Office Network",
  "description": "Main office IP range",
  "cidr_notation": "192.168.1.0/24",
  "start_ip": null,
  "end_ip": null,
  "is_active": true,
  "created_by": null,
  "created_at": "2026-02-04T10:00:00Z",
  "updated_at": "2026-02-04T10:00:00Z"
}
```

### Step 2: Verify Access from Allowed IP

```bash
# Make request from IP in whitelist (192.168.1.100)
# Use X-Forwarded-For header to simulate client IP
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 192.168.1.100"
```

**Expected Response:** `200 OK` - Request allowed

### Step 3: Verify Access Blocked from Non-Whitelisted IP

First, enable IP whitelist enforcement and strict mode:

```bash
# Get security config ID
curl -X GET "http://localhost:8000/api/security/config" | jq '.id'

# Enable IP whitelist with strict mode
curl -X PUT "http://localhost:8000/api/security/config/{config_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "sso_enabled": false,
    "two_factor_required": false,
    "ip_whitelist_enabled": true,
    "ip_whitelist_strict": true,
    "session_timeout_minutes": 60
  }'
```

Now test access from non-whitelisted IP:

```bash
# Make request from IP NOT in whitelist (10.0.0.1)
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 10.0.0.1"
```

**Expected Response:**
```json
{
  "error": "Access denied",
  "detail": "IP address 10.0.0.1 is not in the allowed whitelist",
  "type": "ip_not_allowed"
}
```

### Step 4: Test IP Range Validation

Create whitelist entry with IP range (not CIDR):

```bash
curl -X POST "http://localhost:8000/api/security/ip-whitelist" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": null,
    "name": "VPN Range",
    "description": "VPN client IP range",
    "cidr_notation": null,
    "start_ip": "10.8.0.1",
    "end_ip": "10.8.0.255",
    "is_active": true
  }'
```

Test access from within range:

```bash
# Should allow (within range)
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 10.8.0.100"
```

**Expected Response:** `200 OK`

Test access from outside range:

```bash
# Should block (outside range)
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 10.8.1.1"
```

**Expected Response:** `403 Forbidden`

### Step 5: Test Whitelist Disable Functionality

Disable IP whitelist enforcement:

```bash
curl -X PUT "http://localhost:8000/api/security/config/{config_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "sso_enabled": false,
    "two_factor_required": false,
    "ip_whitelist_enabled": false,
    "ip_whitelist_strict": false,
    "session_timeout_minutes": 60
  }'
```

Verify access is now allowed from any IP:

```bash
# Previously blocked IP should now work
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 10.0.0.1"
```

**Expected Response:** `200 OK` - IP whitelist disabled, access allowed

---

## Manual Testing

### Using the Frontend UI

1. **Navigate to IP Whitelist Page**
   - Login to the application
   - Go to `/recruiter/security/ip-whitelist`

2. **Create Whitelist Entry**
   - Click "Add New Entry"
   - Enter name: "Office Network"
   - Enter CIDR notation: `192.168.1.0/24`
   - Set active: true
   - Click "Save"

3. **Verify Entry Created**
   - Check that entry appears in the list
   - Verify CIDR notation is displayed correctly
   - Check that "Active" badge is shown

4. **Edit Whitelist Entry**
   - Click edit icon on the entry
   - Change CIDR to `10.0.0.0/24`
   - Click "Update"

5. **Toggle Active Status**
   - Click the toggle switch to deactivate
   - Verify entry shows as "Inactive"
   - Click again to activate

6. **Delete Whitelist Entry**
   - Click delete icon
   - Confirm deletion
   - Verify entry is removed from list

### Using Postman

1. **Import Collection**
   - Create a new collection for IP Whitelist tests
   - Add requests for each endpoint (Create, Read, Update, Delete)

2. **Set Up Environment**
   - Create environment variable `base_url` = `http://localhost:8000`
   - Create variable `config_id` for security config ID

3. **Run Tests**
   - Execute requests in order:
     1. GET `/api/security/config` - Get security config
     2. POST `/api/security/ip-whitelist` - Create entry
     3. GET `/api/security/ip-whitelist` - List entries
     4. PUT `/api/security/ip-whitelist/{id}` - Update entry
     5. PUT `/api/security/config/{id}` - Enable IP whitelist
     6. Test with different `X-Forwarded-For` headers
     7. DELETE `/api/security/ip-whitelist/{id}` - Delete entry

---

## Troubleshooting

### Tests Fail with "Database Error"

**Problem:** Tests cannot connect to database

**Solution:**
```bash
# Ensure test database URL is correctly set
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Run tests with verbose output
pytest tests/test_ip_whitelist_middleware.py -v -s
```

### IP Not Blocked Even With Strict Mode

**Problem:** Requests from non-whitelisted IPs are not blocked

**Solution:**
1. Verify IP whitelist is enabled in security config:
```bash
curl -X GET "http://localhost:8000/api/security/config" | jq '.ip_whitelist_enabled'
```

2. Check that middleware is registered in `main.py`:
```python
app.add_middleware(IPWhitelistMiddleware)
```

3. Verify client IP is correctly extracted:
   - Check `X-Forwarded-For`, `X-Real-IP`, `CF-Connecting-IP` headers
   - If behind proxy, ensure proxy forwards client IP

4. Check logs for middleware activity:
```bash
# Look for IP allow/block log messages
tail -f backend/logs/app.log | grep "IP"
```

### CIDR Notation Not Working

**Problem:** CIDR ranges not matching expected IPs

**Solution:**
1. Verify CIDR notation is valid:
```bash
# Python test
python3 -c "import ipaddress; print(ipaddress.ip_network('192.168.1.0/24'))"
```

2. Test specific IP matching:
```python
# Test in Python shell
import ipaddress
network = ipaddress.ip_network('192.168.1.0/24')
ip = ipaddress.ip_address('192.168.1.100')
print(ip in network)  # Should print True
```

3. Check whitelist entry in database:
```bash
# View entry
curl -X GET "http://localhost:8000/api/security/ip-whitelist" | jq '.entries[0]'
```

### Pagination Not Working

**Problem:** Pagination parameters not applied correctly

**Solution:**
1. Verify limit is within valid range (1-1000):
```bash
# Valid
curl "http://localhost:8000/api/security/ip-whitelist?limit=100&offset=0"

# Invalid (limit too high)
curl "http://localhost:8000/api/security/ip-whitelist?limit=2000"
# Should return 400 validation error
```

2. Check that default pagination is applied:
```bash
# Should default to limit=100, offset=0
curl "http://localhost:8000/api/security/ip-whitelist"
```

---

## Success Criteria

### Test Execution

- ✅ All 48 unit tests pass
- ✅ All 35 integration tests pass
- ✅ Code coverage > 80% for middleware
- ✅ Code coverage > 80% for API endpoints
- ✅ No critical bugs or errors

### Functional Requirements

- ✅ IP whitelist entries can be created with CIDR notation
- ✅ IP whitelist entries can be created with IP ranges
- ✅ IPv4 and IPv6 addresses are supported
- ✅ Whitelist entries can be filtered by organization and active status
- ✅ Whitelist entries can be updated and deleted
- ✅ Middleware blocks requests from non-whitelisted IPs when enforcement enabled
- ✅ Middleware allows requests from whitelisted IPs
- ✅ Middleware excludes health endpoints from IP checking
- ✅ Strict mode blocks all access when no whitelist is configured
- ✅ Client IP is correctly extracted from various headers

### Security Requirements

- ✅ IP whitelist enforcement can be toggled via security config
- ✅ Organization-specific and system-wide whitelists supported
- ✅ Active/inactive status for whitelist entries
- ✅ Blocked access attempts are logged
- ✅ Database errors fail open (allow access)

### Performance Requirements

- ✅ Middleware validation adds minimal overhead (< 10ms)
- ✅ Database queries are optimized with proper indexes
- ✅ Pagination support for large whitelist datasets

---

## Additional Verification Commands

### Check IP Whitelist Configuration

```bash
# Get security config
curl -X GET "http://localhost:8000/api/security/config" | jq '{
  ip_whitelist_enabled,
  ip_whitelist_strict
}'

# List all whitelist entries
curl -X GET "http://localhost:8000/api/security/ip-whitelist" | jq '{
  total_count,
  entries: [.entries[] | {
    name,
    cidr_notation,
    start_ip,
    end_ip,
    is_active
  }]
}'

# Get active entries only
curl -X GET "http://localhost:8000/api/security/ip-whitelist?is_active=true" | jq
```

### Test IP Matching

```bash
# Test from whitelisted IP (should succeed)
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 192.168.1.100" \
  -w "\nHTTP Status: %{http_code}\n"

# Test from non-whitelisted IP (should fail with strict mode)
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 10.0.0.1" \
  -w "\nHTTP Status: %{http_code}\n"

# Test from multiple IPs (X-Forwarded-For with chain)
curl -X GET "http://localhost:8000/api/security/config" \
  -H "X-Forwarded-For: 203.0.113.1, 192.168.1.100" \
  -w "\nHTTP Status: %{http_code}\n"
```

### Verify Logging

```bash
# Check for IP block logs
tail -f backend/logs/app.log | grep "IP blocked"

# Check for IP allow logs
tail -f backend/logs/app.log | grep "IP allowed"

# Check for IP validation errors
tail -f backend/logs/app.log | grep "Error validating IP"
```
