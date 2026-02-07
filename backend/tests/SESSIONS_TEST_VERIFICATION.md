# Session Management Testing Guide

This guide provides comprehensive instructions for verifying the session management functionality including automated tests, end-to-end verification steps, and manual testing procedures.

## Table of Contents

1. [Running Tests](#running-tests)
2. [End-to-End Verification](#end-to-end-verification)
3. [Manual Testing](#manual-testing)
4. [Troubleshooting](#troubleshooting)
5. [Success Criteria](#success-criteria)

---

## Running Tests

### Prerequisites

Ensure you have the test dependencies installed:

```bash
cd backend
pip install -e ".[test]"
```

### Unit Tests

Run the unit tests for SessionService:

```bash
cd backend
pytest tests/test_session_service.py -v
```

Run with coverage:

```bash
cd backend
pytest tests/test_session_service.py -v --cov=services/session_service --cov-report=html
```

### Integration Tests

Run the end-to-end integration tests:

```bash
cd backend
pytest tests/integration/test_sessions_e2e.py -v
```

### All Session Tests

Run all session-related tests:

```bash
cd backend
pytest tests/test_session_service.py tests/integration/test_sessions_e2e.py -v
```

### Run Specific Test

Run a specific test case:

```bash
cd backend
pytest tests/test_session_service.py::TestTokenGeneration::test_generate_token -v
```

### Run with Verbose Output

```bash
cd backend
pytest tests/ -v -s --tb=short -k "session"
```

---

## End-to-End Verification

### Verification Steps

Follow these steps to verify session management functionality end-to-end:

#### 1. Login from Multiple Devices

**Objective:** Verify users can have multiple concurrent sessions.

**Steps:**

1. **Login from Desktop:**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "password123"
     }' \
     -c cookies-desktop.txt
   ```

2. **Login from Mobile (different user-agent):**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)" \
     -d '{
       "email": "test@example.com",
       "password": "password123"
     }' \
     -c cookies-mobile.txt
   ```

3. **Login from Tablet:**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -H "User-Agent: Mozilla/5.0 (iPad; CPU OS 16_0)" \
     -d '{
       "email": "test@example.com",
       "password": "password123"
     }' \
     -c cookies-tablet.txt
   ```

**Expected Result:**
- All logins succeed
- Three separate sessions are created
- Each session has unique token and device fingerprint

#### 2. View Active Sessions in UI

**Objective:** Verify users can view all active sessions.

**Steps:**

1. **Get active sessions:**
   ```bash
   curl -X GET "http://localhost:8000/api/sessions/" \
     -H "Authorization: Bearer <token-from-desktop-login>" \
     -b cookies-desktop.txt
   ```

**Expected Result:**
- Response contains array of 3 sessions
- Each session shows:
  - `id`: Unique session ID
  - `device_name`: e.g., "Chrome on Windows", "Safari on iOS"
  - `device_type`: "desktop", "mobile", "tablet"
  - `ip_address`: IP where session was created
  - `location`: Location derived from IP
  - `is_active`: true
  - `last_activity_at`: Recent timestamp
  - `created_at`: Session creation timestamp

2. **Filter by device type:**
   ```bash
   curl -X GET "http://localhost:8000/api/sessions/?device_type=mobile" \
     -H "Authorization: Bearer <token>" \
     -b cookies-desktop.txt
   ```

**Expected Result:**
- Returns only mobile sessions

#### 3. Revoke Individual Session

**Objective:** Verify users can revoke a specific session.

**Steps:**

1. **List sessions and get session_id to revoke:**
   ```bash
   SESSION_ID=$(curl -s -X GET "http://localhost:8000/api/sessions/" \
     -H "Authorization: Bearer <token>" \
     -b cookies-desktop.txt \
     | jq -r '.sessions[1].id')
   ```

2. **Revoke the session:**
   ```bash
   curl -X DELETE "http://localhost:8000/api/sessions/$SESSION_ID?reason=user_logout" \
     -H "Authorization: Bearer <token>" \
     -b cookies-desktop.txt
   ```

**Expected Result:**
- Response: `{"message": "Session revoked successfully", "session_id": "..."}`
- Session is marked as inactive (`is_active: false`)
- `revoked_at` timestamp is set
- `revoke_reason` is "user_logout"

3. **Verify session is revoked:**
   ```bash
   curl -X GET "http://localhost:8000/api/sessions/" \
     -H "Authorization: Bearer <token>" \
     -b cookies-desktop.txt \
     | jq ".sessions[] | select(.id == \"$SESSION_ID\")"
   ```

**Expected Result:**
- Revoked session shows `is_active: false`

#### 4. Revoke All Sessions

**Objective:** Verify users can revoke all other sessions except current.

**Steps:**

1. **Get user_id:**
   ```bash
   USER_ID=$(curl -s -X GET "http://localhost:8000/api/sessions/" \
     -H "Authorization: Bearer <token>" \
     -b cookies-desktop.txt \
     | jq -r '.sessions[0].user_id')
   ```

2. **Revoke all other sessions:**
   ```bash
   curl -X DELETE "http://localhost:8000/api/sessions/revoke-all?user_id=$USER_ID&exclude_current=true&reason=security_reset" \
     -H "Authorization: Bearer <token>" \
     -b cookies-desktop.txt
   ```

**Expected Result:**
- Response: `{"message": "All sessions revoked successfully", "revoked_count": 2}`
- 2 other sessions are revoked (mobile and tablet)
- Current session (desktop) remains active

3. **Verify only current session remains:**
   ```bash
   curl -s -X GET "http://localhost:8000/api/sessions/?is_active=true" \
     -H "Authorization: Bearer <token>" \
     -b cookies-desktop.txt \
     | jq '.total_count'
   ```

**Expected Result:**
- Returns `1` (only current session)

#### 5. Verify Revoked Sessions Cannot Access API

**Objective:** Verify revoked sessions are denied access.

**Steps:**

1. **Try to use revoked session token:**
   ```bash
   # Get revoked session token from earlier step
   REVOKED_TOKEN="<revoked-session-token>"

   curl -X GET "http://localhost:8000/api/sessions/" \
     -H "Authorization: Bearer $REVOKED_TOKEN"
   ```

**Expected Result:**
- Response: `401 Unauthorized` or `403 Forbidden`
- Error message: "Authentication required" or "Session invalid"

2. **Verify active session still works:**
   ```bash
   curl -X GET "http://localhost:8000/api/sessions/" \
     -H "Authorization: Bearer <valid-token>" \
     -b cookies-desktop.txt
   ```

**Expected Result:**
- Response: `200 OK`
- Session data is returned

---

## Manual Testing

### Test Case 1: Multiple Device Login

**Scenario:** User logs in from different devices simultaneously.

**Steps:**
1. Open browser on desktop (Chrome on Windows)
2. Login with test credentials
3. Open browser on mobile (Safari on iPhone)
4. Login with same credentials
5. Open browser on tablet (Firefox on iPad)
6. Login with same credentials

**Verification:**
- All three logins succeed
- User is authenticated on all devices
- Each device has its own session record

### Test Case 2: View Sessions in UI

**Scenario:** User views active sessions in security settings.

**Steps:**
1. Navigate to `/recruiter/security/sessions`
2. View session list

**Verification:**
- All active sessions are displayed
- Device names are user-friendly (e.g., "Chrome on Windows")
- Device type icons are correct (desktop/mobile/tablet)
- Current session is highlighted
- IP addresses and locations are shown
- Last activity timestamps are recent

### Test Case 3: Revoke Session from UI

**Scenario:** User revokes a specific session.

**Steps:**
1. Navigate to `/recruiter/security/sessions`
2. Find session to revoke (e.g., mobile session)
3. Click "Revoke" button
4. Confirm revocation in dialog

**Verification:**
- Confirmation dialog appears
- After confirmation, session is removed from list
- Success message is displayed
- Revoked session's device is logged out

### Test Case 4: Revoke All Other Sessions

**Scenario:** User revokes all other sessions except current.

**Steps:**
1. Navigate to `/recruiter/security/sessions`
2. Click "Revoke All Other Sessions" button
3. Confirm action

**Verification:**
- Confirmation shows count of sessions to be revoked
- After confirmation, only current session remains
- Success message shows number of sessions revoked
- Other devices are logged out

### Test Case 5: Session Expiration

**Scenario:** Session expires after TTL.

**Steps:**
1. Set session TTL to 1 minute for testing
2. Login and get session token
3. Wait for 1 minute
4. Try to access API with expired token

**Verification:**
- API request is denied
- User is redirected to login
- Session is marked as expired (not revoked)

### Test Case 6: Max Sessions Limit

**Scenario:** User exceeds maximum allowed sessions.

**Steps:**
1. Set max_sessions_per_user to 3
2. Login from 5 different devices

**Verification:**
- Only 3 most recent sessions are active
- Oldest sessions are automatically revoked
- Revoke reason is "timeout"

### Test Case 7: Device Type Detection

**Scenario:** Verify device type detection accuracy.

**Steps:**
1. Login from various devices with different user agents:
   - Desktop: Chrome on Windows
   - Desktop: Firefox on Linux
   - Desktop: Safari on macOS
   - Mobile: Chrome on Android
   - Mobile: Safari on iOS
   - Tablet: Chrome on iPad
   - Tablet: Firefox on Kindle

**Verification:**
- Device types are correctly detected
- Device names are user-friendly
- Icons match device types

---

## Troubleshooting

### Tests Fail to Run

**Problem:** `ImportError: No module named 'services.session_service'`

**Solution:**
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/test_session_service.py
```

### Database Errors in Tests

**Problem:** Tests fail with database connection errors.

**Solution:**
- Ensure SQLite is installed
- Verify aiosqlite is installed: `pip install aiosqlite`
- Check that test database URL is correct: `sqlite+aiosqlite:///:memory:`

### Session Not Found

**Problem:** Session lookup fails even after creation.

**Solution:**
- Check that session is being committed to database
- Verify token hashing is consistent
- Ensure session ID is correctly converted to UUID

### Revoked Session Still Valid

**Problem:** Revoked session passes validation.

**Solution:**
- Check that `is_active` flag is being set to False
- Verify `revoked_at` timestamp is being set
- Ensure database commit is successful

### All Tests Pass But Manual Verification Fails

**Problem:** Automated tests pass but API returns 401.

**Solution:**
- API endpoints currently return 401 with "Authentication required" message
- This is expected behavior - authentication integration is pending
- Tests verify service layer logic directly
- Manual verification requires valid JWT token in production

---

## Success Criteria

The session management testing is considered successful when:

### Automated Tests

- ✅ All unit tests pass (40+ tests)
- ✅ All integration tests pass (30+ tests)
- ✅ Code coverage ≥ 80% for SessionService
- ✅ No test failures or errors

### End-to-End Verification

- ✅ Login from multiple devices works
- ✅ Active sessions are viewable in UI
- ✅ Individual session revocation works
- ✅ Revoke all sessions works correctly
- ✅ Revoked sessions cannot access API
- ✅ Current session is excluded when requested

### Manual Testing

- ✅ Session list displays correctly with device info
- ✅ Revoke buttons work with confirmation dialogs
- ✅ Success/error messages are user-friendly
- ✅ Device type detection is accurate
- ✅ Session expiration is enforced
- ✅ Max sessions limit is enforced

### Security

- ✅ Tokens are securely generated (cryptographically random)
- ✅ Tokens are hashed before storage
- ✅ Revoked sessions cannot be reused
- ✅ Session isolation between users
- ✅ IP addresses are tracked
- ✅ Device fingerprinting works

---

## Test Coverage Summary

### Unit Tests (test_session_service.py)

| Category | Tests | Description |
|----------|-------|-------------|
| Initialization | 3 | Default/custom config, unlimited sessions |
| Token Generation | 4 | Generation, uniqueness, hashing |
| Device Parsing | 8 | Desktop, mobile, tablet, unknown detection |
| Device Name | 7 | Browser/OS detection, user-friendly names |
| Session Creation | 4 | Creation, auto-token, max sessions |
| Session Validation | 4 | Valid, not found, revoked, expired |
| Session Retrieval | 2 | Get by token, not found |
| Session Revocation | 4 | Revoke single, not found, already revoked, revoke all |
| Active Sessions | 2 | Get all, empty list |
| Activity Update | 2 | Update success, not found |
| Cleanup | 2 | Cleanup expired, no sessions |
| Health Check | 2 | Healthy, with error |
| Global Instance | 2 | Singleton pattern |

**Total: 46 unit tests**

### Integration Tests (test_sessions_e2e.py)

| Category | Tests | Description |
|----------|-------|-------------|
| Basic Operations | 7 | Create, validate, revoke, get active, revoke all, exclude current |
| Expiration | 2 | Expired validation, cleanup |
| Device Types | 1 | Desktop, mobile, tablet detection |
| Multiple Sessions | 2 | Concurrent sessions, max limit |
| Health Check | 1 | Service health |
| Activity Updates | 1 | Activity timestamp update |
| Error Handling | 4 | Revoke nonexistent, validate nonexistent, already revoked, invalid user_id |
| Token Generation | 2 | Unique tokens, consistent hashing |
| Global Service | 1 | Global instance |
| Complete Lifecycle | 1 | Create → validate → update → revoke |
| No Expiration | 1 | Session without TTL |
| Edge Cases | 2 | Unknown browser, None user agent |
| Multiple Users | 1 | Session isolation |
| Revocation Reasons | 1 | All reason types |

**Total: 30 integration tests**

### Combined: 76 tests

---

## Additional Notes

### Current Limitations

The session API endpoints (`/api/sessions/`) currently return 401 Unauthorized with a placeholder message. This is by design as full authentication middleware integration is pending. The tests verify the service layer logic directly, which handles all session operations correctly.

### Future Enhancements

When authentication is fully integrated:

1. API endpoints will extract `user_id` from JWT token
2. Authorization checks will prevent cross-user access
3. Current session detection will work properly
4. Audit logs will track session management events
5. Real-time notifications will alert users of new logins

### Performance Considerations

- Session validation updates activity timestamp on each request
- Cleanup should be run periodically (e.g., Celery task)
- Consider indexing on `token_hash`, `user_id`, `is_active`
- Max sessions limit prevents unlimited session growth
