# Logout and Token Invalidation Flow - Testing Guide

This guide provides comprehensive testing instructions for the logout and token invalidation functionality.

## Overview

The logout flow ensures that:
1. Users can log out securely
2. Refresh tokens are invalidated on the backend
3. Local storage is cleared on the frontend
4. Users are redirected to the login page
5. Protected routes become inaccessible after logout

## Prerequisites

### 1. Database Setup

Ensure PostgreSQL is running and the database is initialized:

```bash
cd backend
python -c "from database import engine; import asyncio; asyncio.run(engine.connect())"
```

### 2. Backend Setup

Start the backend server:

```bash
cd backend
python main.py
```

Verify backend is running:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "agenthr-backend",
  "version": "0.1.0"
}
```

### 3. Frontend Setup

Start the frontend development server:

```bash
cd frontend
npm run dev
```

Verify frontend is running at `http://localhost:5173`

## Automated Testing

### Running the Logout Flow Test Script

The automated test script verifies:

1. Backend health check
2. Test user setup (login)
3. Login with valid credentials
4. Access protected route before logout
5. Logout with refresh token
6. Access protected route after logout
7. Token refresh rejection after logout
8. Multiple protected routes after logout
9. Login again after logout
10. Logout with invalid token

**Run the test script:**

```bash
cd backend
python test_logout_flow.py
```

**Expected output:**

```
============================================================
  LOGOUT AND TOKEN INVALIDATION - END-TO-END TEST
============================================================
ℹ Backend URL: http://localhost:8000
ℹ Test user: test_logout@example.com

============================================================
  1. Backend Health Check
============================================================
✓ Backend is running: agenthr-backend
ℹ Version: 0.1.0

============================================================
  2. Setup Test User
============================================================
ℹ POST http://localhost:8000/api/auth/register
ℹ Creating test user: test_logout@example.com
✓ Test user already exists (from previous test)

============================================================
  3. Login with Valid Credentials
============================================================
ℹ POST http://localhost:8000/api/auth/login
ℹ Email: test_logout@example.com
✓ Login successful!
ℹ Token type: bearer
✓ Access token received
ℹ Access token length: 123 chars
✓ Refresh token received
ℹ Refresh token length: 256 chars
✓ Authenticated user: Test Logout User
✓ User email: test_logout@example.com
✓ User role: Recruiter

... (additional tests)

============================================================
  TEST SUMMARY
============================================================
✓ PASS: backend_health
✓ PASS: setup_test_user
✓ PASS: login_success
✓ PASS: access_protected_before_logout
✓ PASS: logout
✓ PASS: access_protected_after_logout
✓ PASS: token_refresh_after_logout
✓ PASS: multiple_protected_routes
✓ PASS: login_after_logout
✓ PASS: logout_with_invalid_token

============================================================
✓ ALL TESTS PASSED!
ℹ The logout and token invalidation flow is working correctly.
```

## Manual Browser Testing

### Test Case 1: Complete Logout Flow

**Steps:**

1. Navigate to `http://localhost:5173/login`
2. Log in with valid credentials:
   - Email: `test_logout@example.com`
   - Password: `TestPass123`
3. Verify redirect to dashboard at `/recruiter/dashboard`
4. Verify user menu appears in header (avatar with user initial)
5. Click on user avatar to open menu
6. Verify user info displays (name and email)
7. Click "Logout" button
8. Verify redirect to `/login` page
9. Open browser DevTools → Application → Local Storage
10. Verify localStorage is cleared:
    - `auth-access-token` should be removed
    - `auth-refresh-token` should be removed
    - `auth-user` should be removed
11. Try to navigate to `/recruiter/dashboard`
12. Verify redirect back to `/login` page

**Expected Result:** ✅ User is logged out, tokens are cleared, and protected routes redirect to login

---

### Test Case 2: Token Invalidation

**Steps:**

1. Log in as test user
2. Open browser DevTools → Application → Local Storage
3. Copy the `auth-refresh-token` value
4. Click logout button
5. Open a new tab and navigate to `http://localhost:8000/docs`
6. Find the `/api/auth/refresh` endpoint
7. Try to refresh with the copied token:
   ```json
   {
     "refresh_token": "<copied_refresh_token>"
   }
   ```
8. Verify request fails with 401 or 400 status
9. Try the same refresh request again
10. Verify it continues to fail

**Expected Result:** ✅ Refresh token is invalidated after logout and cannot be reused

---

### Test Case 3: Protected Routes After Logout

**Steps:**

1. Log in as test user
2. Access a protected route (e.g., `/recruiter/candidates`)
3. Verify page loads successfully
4. Click logout button
5. Try to directly access protected routes:
   - `/recruiter/dashboard`
   - `/recruiter/candidates`
   - `/recruiter/vacancies`
   - `/recruiter/analytics`
   - `/recruiter/backups`
6. Verify each redirects to `/login` page

**Expected Result:** ✅ All protected routes redirect to login after logout

---

### Test Case 4: Re-login After Logout

**Steps:**

1. Log in as test user
2. Click logout button
3. Verify redirect to `/login` page
4. Log in again with same credentials
5. Verify successful login
6. Verify new tokens are issued (check localStorage)
7. Verify access to protected routes

**Expected Result:** ✅ User can successfully log in again after logout

---

### Test Case 5: Logout from Multiple Sessions

**Steps:**

1. Open browser in normal mode
2. Log in as test user (Session A)
3. Open incognito/private window
4. Log in as same user (Session B)
5. In Session A, click logout button
6. Verify Session A redirects to login
7. In Session B, try to access a protected route
8. **Expected:** Session B should still work (logout only affects current session)

**Expected Result:** ✅ Logout only invalidates the current session's refresh token

---

### Test Case 6: Logout with Invalid Token

**Steps:**

1. Log in as test user
2. Open browser DevTools → Console
3. Manually corrupt the refresh token in localStorage:
   ```javascript
   localStorage.setItem('auth-refresh-token', 'invalid_token_123');
   ```
4. Click logout button
5. Verify user is still logged out (local storage cleared)
6. Verify redirect to login page

**Expected Result:** ✅ Logout succeeds even with invalid token (graceful degradation)

---

### Test Case 7: JWT Token Expiry vs Logout

**Steps:**

1. Log in as test user
2. Copy the access token from localStorage
3. Click logout button
4. Open new tab and test the copied access token:
   ```bash
   curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/api/auth/me
   ```
5. **Expected:** May still work (JWT is stateless)
6. Try to refresh with the old refresh token:
   ```bash
   curl -X POST http://localhost:8000/api/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "<old_refresh_token>"}'
   ```
7. Verify refresh fails with 401/400

**Expected Result:** ✅ Access token may work until expiry, but refresh is blocked

---

### Test Case 8: Browser Back Button After Logout

**Steps:**

1. Log in as test user
2. Navigate to `/recruiter/candidates`
3. Click logout button
4. Verify redirect to `/login`
5. Click browser back button
6. Verify page redirects back to `/login`

**Expected Result:** ✅ Browser back button doesn't bypass authentication

---

### Test Case 9: localStorage Persistence

**Steps:**

1. Log in as test user
2. Open DevTools → Application → Local Storage
3. Verify tokens are stored:
   - `auth-access-token`: <JWT string>
   - `auth-refresh-token`: <JWT string>
   - `auth-user`: <JSON string>
4. Click logout button
5. Verify all three keys are removed
6. Refresh the page
7. Verify no authentication state remains

**Expected Result:** ✅ localStorage is completely cleared after logout

---

### Test Case 10: Network Tab Verification

**Steps:**

1. Log in as test user
2. Open DevTools → Network tab
3. Filter by "fetch" and "XHR"
4. Click logout button
5. Verify POST request to `/api/auth/logout`
6. Verify request payload contains refresh_token
7. Verify response status is 200
8. Verify subsequent requests to protected routes fail

**Expected Result:** ✅ Logout API call is made and backend processes it correctly

---

## API Endpoint Testing

### Test Logout Endpoint

**Request:**

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

**Success Response (200):**

```json
{
  "message": "Logged out successfully"
}
```

**Error Response (401/400):**

```json
{
  "detail": "Invalid or expired refresh token"
}
```

### Test Refresh Token After Logout

**Request:**

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "revoked_refresh_token"
  }'
```

**Expected Response (401/400):**

```json
{
  "detail": "Invalid or expired refresh token"
}
```

---

## Verification Checklist

### Backend Verification

- [ ] Logout endpoint exists at `POST /api/auth/logout`
- [ ] Logout endpoint accepts `refresh_token` in request body
- [ ] Refresh token is marked as revoked in database
- [ ] Revoked refresh token cannot be used for refresh
- [ ] Logout endpoint returns 200 status on success
- [ ] Logout endpoint handles invalid tokens gracefully

### Frontend Verification

- [ ] Logout button visible in user menu
- [ ] Clicking logout calls `AuthContext.logout()` function
- [ ] `AuthContext.logout()` clears all auth state
- [ ] `AuthContext.logout()` calls backend logout endpoint
- [ ] `AuthContext.logout()` clears localStorage
- [ ] User is redirected to `/login` after logout
- [ ] Protected routes redirect unauthenticated users to login

### Security Verification

- [ ] Refresh tokens are invalidated on logout
- [ ] Invalidated refresh tokens cannot be refreshed
- [ ] Access tokens expire naturally (JWT stateless)
- [ ] localStorage is cleared completely
- [ ] No sensitive data remains after logout
- [ ] Browser back button doesn't bypass auth
- [ ] Multiple sessions are handled correctly

### Integration Verification

- [ ] Login → Access Protected → Logout flow works
- [ ] Re-login after logout works
- [ ] Tokens are properly stored after login
- [ ] Tokens are properly cleared after logout
- [ ] API client handles logout correctly
- [ ] ProtectedRoute component redirects after logout

---

## Troubleshooting

### Issue: Logout doesn't clear localStorage

**Solution:** Check that `AuthContext.logout()` is being called and contains:

```typescript
const logout = useCallback(() => {
  setUser(null);
  setAccessToken(null);
  setRefreshToken(null);
  setError(null);
  clearAuthData(); // This should clear localStorage
  // ... backend logout call
}, [clearAuthData]);
```

### Issue: Protected routes still accessible after logout

**Solution:** Verify that:
1. localStorage is cleared (check DevTools)
2. `ProtectedRoute` component checks `isAuthenticated` state
3. `isAuthenticated` is derived from `user && accessToken`

### Issue: Refresh token still works after logout

**Solution:** Check backend logs to verify:
1. Logout endpoint is called
2. Refresh token is found in database
3. `revoked_at` field is set to current time
4. Refresh endpoint checks `revoked_at` is null

### Issue: User not redirected to login after logout

**Solution:** Verify `RecruiterLayout.handleLogout()`:

```typescript
const handleLogout = () => {
  handleUserMenuClose();
  logout();
  navigate('/login'); // This should be present
};
```

### Issue: Logout button not visible

**Solution:** Verify user is authenticated and user data exists:
1. Check `useAuth().user` is not null
2. Check RecruiterLayout renders user menu
3. Check console for authentication errors

---

## Test Data Cleanup

To clean up test data after testing:

```sql
-- Connect to database
psql agenthr

-- Delete test user (this will cascade delete refresh tokens)
DELETE FROM users WHERE email = 'test_logout@example.com';

-- Verify cleanup
SELECT * FROM refresh_tokens WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE 'test_%'
);
```

Or via Python:

```bash
cd backend
python -c "
from database import get_session
from models.user import User
import asyncio

async def cleanup():
    async with get_session() as db:
        result = await db.execute(
            select(User).where(User.email.like('test_%'))
        )
        for user in result.scalars():
            await db.delete(user)
        await db.commit()
        print('Test users deleted')

asyncio.run(cleanup())
"
```

---

## Conclusion

After completing all tests:

1. ✅ Automated tests should all pass
2. ✅ Manual browser tests should verify user experience
3. ✅ API endpoint tests should verify backend behavior
4. ✅ Security verification should ensure proper token invalidation

If all tests pass, the logout and token invalidation flow is working correctly and ready for production use.
