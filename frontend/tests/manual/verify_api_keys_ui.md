# API Keys Manager UI Verification

## Purpose

Manual verification test for the API Keys Manager UI integrated with the backend API key authentication system.

## Prerequisites

1. **Backend Services Running:**
   ```bash
   # Start PostgreSQL, Redis, and FastAPI backend
   cd backend
   docker-compose up -d postgres redis
   source .venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```

2. **Frontend Development Server Running:**
   ```bash
   # In a separate terminal
   cd frontend
   npm install  # If dependencies not installed
   npm run dev  # Starts Vite dev server on port 5173
   ```

3. **User Account:**
   - Must be logged in as an authenticated user
   - Any user role (JobSeeker, Recruiter, HiringManager, Admin) can access the developer portal

## Test Location

**URL:** http://localhost:5173/developer/api-keys

**Navigation Path:**
1. Log in to the application
2. Navigate to `/developer` (Developer Portal)
3. Click on "API Keys" in the sidebar or "Manage Keys" button
4. You should see the API Keys management page

## Verification Checklist

### 1. Page Renders Correctly

**Expected:**
- ✅ Page title: "API Keys"
- ✅ Description: "Manage API keys for authenticating requests to AgentHR"
- ✅ "Create API Key" button visible in header
- ✅ API keys list section displays

**How to Test:**
1. Navigate to http://localhost:5173/developer/api-keys
2. Verify all elements are visible and properly styled
3. Check for any console errors in browser DevTools

**Screenshot Location (if taking):** `screenshots/api-keys-page-render.png`

---

### 2. Generate New API Key

**Expected:**
- ✅ Click "Create API Key" button opens a dialog
- ✅ Dialog contains:
  - Name field (required)
  - Scopes multi-select (required)
  - Rate limit configuration (optional)
  - Expiration date picker (optional)
- ✅ "Create" button disabled until name and at least one scope are selected
- ✅ Successful creation shows the full API key (only shown once)
- ✅ Key can be copied to clipboard
- ✅ Warning message to save the key securely

**How to Test:**
1. Click "Create API Key" button
2. Fill in the form:
   - **Name:** "Test Integration Key"
   - **Scopes:** Select `read:candidates`, `read:vacancies`
   - **Rate Limit:** 100 requests/minute (optional)
   - **Expires:** Leave blank or set a future date
3. Click "Create" button
4. Verify success dialog appears with the full API key
5. Copy the key using the copy button
6. Save the key somewhere for later tests
7. Close the dialog

**API Request (Behind the Scenes):**
```bash
POST http://localhost:8000/api/api-keys/generate
Content-Type: application/json

{
  "name": "Test Integration Key",
  "scopes": ["read:candidates", "read:vacancies"],
  "rate_limit": {
    "requests_per_minute": 100
  }
}

# Expected Response: 201 Created
{
  "id": "uuid-here",
  "key": "64-character-hex-string",
  "key_prefix": "ak_test1234",
  "name": "Test Integration Key",
  "scopes": ["read:candidates", "read:vacancies"],
  "rate_limit": {"requests_per_minute": 100},
  "expires_at": null,
  "created_at": "2026-03-21T...",
  "message": "API key created successfully. Save this key securely - it won't be shown again."
}
```

**Screenshot Location:** `screenshots/api-key-created-dialog.png`

---

### 3. View API Key List

**Expected:**
- ✅ All API keys displayed in a table/list
- ✅ Each key shows:
  - Key prefix (e.g., `ak_test1234...`)
  - Name
  - Scopes (as chips/badges)
  - Status (Active/Revoked)
  - Rate limit
  - Created date
  - Last used date (if applicable)
  - Expiration date (if set)
- ✅ Active keys highlighted differently from revoked keys
- ✅ Full key is masked (not visible)

**How to Test:**
1. After creating a key, verify it appears in the list
2. Create a second key with different scopes
3. Verify both keys are displayed
4. Check that all metadata is correct
5. Verify full key value is not visible

**API Request (Behind the Scenes):**
```bash
GET http://localhost:8000/api/api-keys/?skip=0&limit=100

# Expected Response: 200 OK
[
  {
    "id": "uuid-1",
    "key_prefix": "ak_test1234",
    "name": "Test Integration Key",
    "scopes": ["read:candidates", "read:vacancies"],
    "rate_limit": {"requests_per_minute": 100},
    "is_active": true,
    "expires_at": null,
    "last_used_at": null,
    "created_at": "2026-03-21T...",
    "updated_at": "2026-03-21T..."
  },
  ...
]
```

**Screenshot Location:** `screenshots/api-keys-list.png`

---

### 4. Revoke API Key

**Expected:**
- ✅ Each active key has a "Revoke" button or action menu
- ✅ Clicking "Revoke" shows a confirmation dialog
- ✅ Confirmation dialog warns about consequences
- ✅ After confirmation, key status changes to "Revoked"
- ✅ Revoked keys are visually distinct (grayed out, strikethrough, etc.)
- ✅ Revoked keys no longer work for authentication

**How to Test:**
1. Find an API key in the list
2. Click "Revoke" button
3. Verify confirmation dialog appears
4. Confirm the revocation
5. Verify key status changes to "Revoked" or "Inactive"
6. Verify visual changes (color, icon, etc.)
7. Try using the revoked key (should get 401/403 error)

**API Request (Behind the Scenes):**
```bash
POST http://localhost:8000/api/api-keys/{key_id}/revoke

# Expected Response: 200 OK
{
  "id": "uuid-1",
  "key_prefix": "ak_test1234",
  "name": "Test Integration Key",
  "is_active": false,
  "message": "API key revoked successfully"
}
```

**Test Revoked Key Authentication:**
```bash
curl -X GET http://localhost:8000/api/candidates \
  -H "X-API-Key: <revoked-key>"

# Expected: 403 Forbidden
{
  "detail": "API key is not active"
}
```

**Screenshot Location:** `screenshots/api-key-revoked.png`

---

### 5. Filter and Search

**Expected (if implemented):**
- ✅ Can filter by status (Active/Revoked/All)
- ✅ Can search by name or key prefix
- ✅ Filters update the list in real-time

**How to Test:**
1. Create multiple API keys (some active, some revoked)
2. Use filter dropdown to show only active keys
3. Use filter dropdown to show only revoked keys
4. Search for a specific key by name
5. Verify list updates correctly

**Screenshot Location:** `screenshots/api-keys-filtered.png`

---

### 6. View API Key Details

**Expected (if detail view exists):**
- ✅ Clicking on a key shows detailed information
- ✅ Details include:
  - Full metadata
  - Usage statistics (if available)
  - Recent API calls
  - Rate limit status
- ✅ Can edit key metadata (name, rate limits) if allowed

**How to Test:**
1. Click on an API key in the list
2. Verify detail view/modal opens
3. Check all information is displayed correctly
4. Close the detail view

**Screenshot Location:** `screenshots/api-key-details.png`

---

### 7. Rate Limit Headers

**Expected:**
- ✅ API responses include rate limit headers:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

**How to Test:**
1. Use one of your API keys to make a request
2. Check response headers in browser DevTools or curl

```bash
curl -X GET http://localhost:8000/api/candidates \
  -H "X-API-Key: <your-key>" \
  -i

# Expected headers:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1710123456
```

---

### 8. Error Handling

**Expected:**
- ✅ Invalid API key returns 401 Unauthorized
- ✅ Expired API key returns 403 Forbidden
- ✅ Revoked API key returns 403 Forbidden
- ✅ Rate limit exceeded returns 429 Too Many Requests with `Retry-After` header
- ✅ Missing required scopes returns 403 Forbidden with scope error message

**How to Test:**

**Test 1: Invalid Key**
```bash
curl -X GET http://localhost:8000/api/candidates \
  -H "X-API-Key: invalid-key-12345" \
  -i

# Expected: 401 Unauthorized
```

**Test 2: Rate Limit Exceeded**
```bash
# Make requests until rate limit is hit
for i in {1..101}; do
  curl -X GET http://localhost:8000/api/candidates \
    -H "X-API-Key: <your-key-with-100-limit>" \
    -s -o /dev/null -w "%{http_code}\n"
done

# First 100: 200 OK
# Request 101: 429 Too Many Requests
```

---

### 9. UI/UX Quality

**Expected:**
- ✅ Responsive design (works on mobile, tablet, desktop)
- ✅ Loading states shown during API calls
- ✅ Error messages are clear and actionable
- ✅ Success messages are shown
- ✅ Icons and colors are consistent
- ✅ Tooltips/help text for complex fields
- ✅ Keyboard navigation works
- ✅ Accessibility: proper ARIA labels, focus indicators

**How to Test:**
1. Resize browser window to test responsive design
2. Test all interactions and verify loading states
3. Trigger errors (invalid input, network errors) and check messages
4. Use keyboard to navigate (Tab, Enter, Escape)
5. Check with screen reader if available

---

## Integration Points Verified

By completing these tests, you verify the following Phase 1 integrations:

- ✅ **API Keys Endpoint** (`/api/api-keys/`) - Generate, list, revoke operations
- ✅ **API Key Authentication Middleware** - X-API-Key header validation
- ✅ **Rate Limiting Middleware** - Per-key rate limits enforced
- ✅ **Usage Analytics** - Last used timestamp updates
- ✅ **Frontend-Backend Communication** - API client working correctly
- ✅ **Developer Routes** - `/developer/api-keys` route registered
- ✅ **Protected Routes** - Authentication required to access

## Troubleshooting

### Issue: Page not found (404)

**Solution:**
- Verify frontend dev server is running on port 5173
- Verify routes are registered in `frontend/src/App.tsx`
- Check browser console for routing errors

### Issue: API errors (401, 403, 500)

**Solution:**
- Verify backend is running on port 8000
- Check backend logs for errors
- Verify database migrations are applied
- Check user is authenticated (has valid session cookie)

### Issue: Keys not appearing in list

**Solution:**
- Check backend API is responding: `curl http://localhost:8000/api/api-keys/`
- Verify user is authenticated
- Check browser console for JavaScript errors
- Check Network tab in DevTools for failed requests

### Issue: Cannot create API key

**Solution:**
- Verify all required fields are filled
- Check backend validation errors in response
- Verify database connection is working
- Check for constraint violations (unique names, etc.)

### Issue: Rate limiting not working

**Solution:**
- Verify Redis is running (rate limit tracking requires Redis)
- Check backend configuration for `RATE_LIMIT_PER_MINUTE`
- Verify RateLimitMiddleware is registered in main.py
- Check backend logs for rate limit events

## Expected Results Summary

After completing all verification steps:

✅ **Create API Key:** Successfully generates new API key with scopes and rate limits
✅ **View API Keys:** All keys displayed with correct metadata
✅ **Revoke API Key:** Keys can be revoked and become inactive
✅ **Filter/Search:** List can be filtered and searched (if implemented)
✅ **Rate Limiting:** Rate limit headers present, 429 errors when exceeded
✅ **Error Handling:** Proper error responses for invalid/revoked/expired keys
✅ **UI/UX:** Responsive, accessible, and user-friendly interface

## Test Report

**Tester:** _________________
**Date:** _________________
**Frontend Version:** _________________
**Backend Version:** _________________

**Overall Result:** ☐ Pass  ☐ Fail  ☐ Pass with Issues

**Issues Found:**
-
-
-

**Notes:**
