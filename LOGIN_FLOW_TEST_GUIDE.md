# Login and Protected Route Access Testing Guide

## Overview
This guide provides step-by-step instructions for testing the login and protected route access flow (subtask-8-2).

## Prerequisites

### 1. Database Setup
Ensure PostgreSQL is running and the database schema is up to date:

```bash
# Check database migrations
cd backend
alembic current

# If migrations are not applied, run:
alembic upgrade head
```

### 2. Backend Service
Start the FastAPI backend server:

```bash
cd backend
python main.py
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Service
In a separate terminal, start the Vite frontend development server:

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Automated Testing

### Backend API Test
We've provided a comprehensive Python test script that tests the complete login flow:

```bash
cd backend
python test_login_flow.py
```

This script tests:
1. ✅ Backend health check
2. ✅ Test user setup (registration)
3. ✅ Login with valid credentials
4. ✅ Login with invalid credentials (should fail)
5. ✅ JWT token structure validation
6. ✅ Protected endpoint access (/api/auth/me)
7. ✅ Protected recruiter routes access
8. ✅ JWT token sent in Authorization header
9. ✅ Unauthorized access rejected (401)
10. ✅ Token refresh mechanism

### Expected Output
```
============================================================
  LOGIN AND PROTECTED ROUTE ACCESS - END-TO-END TEST
============================================================
ℹ Backend URL: http://localhost:8000
ℹ Test user: test_login@example.com

============================================================
  1. Backend Health Check
============================================================
✓ Backend is running: resume-analysis-api
ℹ Version: 1.0.0

============================================================
  2. Setup Test User
============================================================
✓ Test user created successfully!
✓ User ID: <uuid>

============================================================
  3. Login with Valid Credentials
============================================================
✓ Login successful!
✓ Access token received
✓ Refresh token received
✓ Authenticated user: Test Login User
✓ User role: Recruiter
✓ Is active: True

============================================================
  4. Login with Invalid Credentials
============================================================
✓ Invalid credentials correctly rejected (401)

============================================================
  5. JWT Token Structure Validation
============================================================
✓ JWT has valid structure (header.payload.signature)
✓ JWT header contains algorithm
✓ JWT payload contains user ID and expiration
✓ Role claim: Recruiter

============================================================
  6. Protected Endpoint - /api/auth/me
============================================================
✓ Protected endpoint accessible!
✓ Email matches authenticated user
✓ Name matches authenticated user

============================================================
  7. Protected Recruiter Routes
============================================================
✓ Candidates List: Accessible (200)
✓ Vacancies List: Accessible (200)
✓ Analytics Key Metrics: Accessible (200)
✓ Backups List: Accessible (200)

============================================================
  8. Verify JWT Token Sent in Requests
============================================================
✓ JWT token successfully sent in Authorization header
✓ Server accepted and validated the token

============================================================
  9. Unauthorized Access Without Token
============================================================
✓ Current User: Correctly rejected (401)
✓ Candidates List: Correctly rejected (401)
✓ Vacancies List: Correctly rejected (401)

============================================================
  10. Token Refresh Mechanism
============================================================
✓ Token refresh successful!
✓ New access token received

============================================================
  TEST SUMMARY
============================================================
✓ PASS: backend_health
✓ PASS: setup_test_user
✓ PASS: login_success
✓ PASS: login_invalid_credentials
✓ PASS: jwt_token_structure
✓ PASS: protected_endpoint_auth_me
✓ PASS: protected_recruiter_routes
✓ PASS: jwt_in_requests
✓ PASS: unauthorized_access
✓ PASS: token_refresh

============================================================
✓ ALL TESTS PASSED!
============================================================
```

## Manual Browser Testing

### Test Case 1: Navigate to Login Page

**Steps:**
1. Open browser to `http://localhost:5173/login`
2. Verify the login page loads correctly

**Expected Results:**
- ✅ Login form renders without errors
- ✅ Email input field is present and focused
- ✅ Password input field is present
- ✅ "Sign In" button is present
- ✅ Link to registration page is visible
- ✅ No console errors

### Test Case 2: Login with Valid Credentials

**Steps:**
1. On the login page (`http://localhost:5173/login`)
2. Enter valid credentials:
   - **Email**: test_login@example.com (or any registered user)
   - **Password**: TestPass123 (or the password you registered with)
3. Click "Sign In" button
4. Observe the loading state
5. Wait for successful login

**Expected Results:**
- ✅ Form validation works (all fields required)
- ✅ Email format validation (must contain @)
- ✅ Loading state shown during login (CircularProgress)
- ✅ No error messages displayed
- ✅ Successful login redirects to `/recruiter/dashboard`
- ✅ User menu appears in header with logged-in user's info
- ✅ No console errors
- ✅ JWT tokens stored in localStorage

### Test Case 3: Verify Redirect After Login

**Steps:**
1. Log in with valid credentials
2. Observe the redirect behavior
3. Check the URL after login

**Expected Results:**
- ✅ Default redirect to `/recruiter/dashboard` after successful login
- ✅ If `?return=` query param was present, redirect to that URL instead
- ✅ Dashboard page loads successfully
- ✅ User is authenticated in the application
- ✅ No redirect loops or errors

### Test Case 4: Access Protected Recruiter Routes

**Steps:**
1. Log in successfully
2. Navigate to various protected recruiter routes:
   - `http://localhost:5173/recruiter/dashboard`
   - `http://localhost:5173/recruiter/candidates`
   - `http://localhost:5173/recruiter/vacancies`
   - `http://localhost:5173/recruiter/analytics`
   - `http://localhost:5173/recruiter/backups`

**Expected Results:**
- ✅ All protected recruiter routes load successfully
- ✅ No redirect to login page
- ✅ User information displayed in header
- ✅ No authentication errors
- ✅ API requests include JWT token in Authorization header

### Test Case 5: Verify JWT Token Storage

**Steps:**
1. After logging in, open browser DevTools (F12)
2. Go to Application tab → Local Storage → http://localhost:5173
3. Check for the following keys:
   - `auth-access-token`
   - `auth-refresh-token`
   - `auth-user`

**Expected Results:**
```json
{
  "auth-access-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "auth-refresh-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "auth-user": {
    "id": "uuid",
    "email": "test_login@example.com",
    "name": "Test Login User",
    "role": "Recruiter",
    "is_active": true,
    "email_verified": false
  }
}
```

### Test Case 6: Verify JWT Sent in API Requests

**Steps:**
1. After logging in, open browser DevTools (F12)
2. Go to Network tab
3. Filter by XHR or Fetch requests
4. Navigate to a page that makes API requests (e.g., recruiter/candidates)
5. Click on an API request and check the Request Headers

**Expected Results:**
- ✅ API requests include `Authorization: Bearer <token>` header
- ✅ Token matches the `auth-access-token` from localStorage
- ✅ API responses return 200 (success) status
- ✅ Data is loaded correctly in the UI

### Test Case 7: Login with Invalid Credentials

**Steps:**
1. Go to `http://localhost:5173/login`
2. Enter invalid credentials:
   - **Email**: test_login@example.com
   - **Password**: WrongPassword123
3. Click "Sign In" button

**Expected Results:**
- ✅ Loading state shown during login attempt
- ✅ Error message displayed: "Invalid email or password"
- ✅ No redirect occurs
- ✅ User remains on login page
- ✅ Form is still accessible for retry
- ✅ No tokens stored in localStorage

### Test Case 8: Login Form Validation

**Steps:**
1. Go to `http://localhost:5173/login`
2. Test various validation scenarios:
   - Leave email empty, fill password, click Sign In
   - Leave password empty, fill email, click Sign In
   - Leave both empty, click Sign In
   - Enter email without @ symbol, click Sign In

**Expected Results:**
- ✅ "Please fill in all fields" error shown when any field is empty
- ✅ "Please enter a valid email address" error shown for invalid email
- ✅ Validation prevents form submission
- ✅ No API calls made for invalid forms
- ✅ Error messages disappear when user starts typing

### Test Case 9: Protected Route Redirect (Not Logged In)

**Steps:**
1. Open a new Incognito/Private window (or clear localStorage)
2. Navigate directly to a protected route:
   - `http://localhost:5173/recruiter/dashboard`
   - `http://localhost:5173/recruiter/candidates`

**Expected Results:**
- ✅ Redirected to `/login` page
- ✅ URL includes `?return=/recruiter/dashboard` query parameter
- ✅ Login page displays correctly
- ✅ After logging in, redirected back to original destination

### Test Case 10: Logout and Verify Protected Routes Inaccessible

**Steps:**
1. Log in successfully
2. Verify you can access protected routes
3. Click on user avatar in header
4. Click "Logout" from the dropdown menu
5. Try to access a protected route again (e.g., `/recruiter/dashboard`)

**Expected Results:**
- ✅ Logout API call succeeds
- ✅ All auth tokens removed from localStorage
- ✅ User data removed from localStorage
- ✅ Redirected to `/login` page
- ✅ Access to protected routes now redirects to login
- ✅ Cannot access recruiter routes without authentication

## API Endpoint Testing with cURL

### Test Login Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_login@example.com",
    "password": "TestPass123"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "test_login@example.com",
    "name": "Test Login User",
    "role": "Recruiter",
    "is_active": true,
    "email_verified": false
  }
}
```

### Test Login with Invalid Credentials

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_login@example.com",
    "password": "WrongPassword123"
  }'
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Invalid email or password"
}
```

### Test Protected Endpoint with Token

```bash
TOKEN="<access_token_from_login>"
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "test_login@example.com",
  "name": "Test Login User",
  "role": "Recruiter",
  "is_active": true,
  "email_verified": false
}
```

### Test Protected Recruiter Routes

```bash
TOKEN="<access_token_from_login>"

# Test candidates endpoint
curl -X GET http://localhost:8000/api/candidates/ \
  -H "Authorization: Bearer $TOKEN"

# Test vacancies endpoint
curl -X GET http://localhost:8000/api/vacancies/ \
  -H "Authorization: Bearer $TOKEN"

# Test analytics endpoint
curl -X GET http://localhost:8000/api/analytics/key-metrics \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

### Test Unauthorized Access

```bash
# Test without token
curl -X GET http://localhost:8000/api/auth/me

# Test with invalid token
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer invalid_token"
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

### Test Token Refresh

```bash
REFRESH_TOKEN="<refresh_token_from_login>"
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer $REFRESH_TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Verification Checklist

### Backend Verification
- [ ] Login endpoint validates credentials correctly
- [ ] Valid credentials return JWT tokens
- [ ] Invalid credentials return 401 error
- [ ] JWT access token is generated with correct expiration
- [ ] JWT refresh token is generated and stored in database
- [ ] JWT payload contains user ID, role, and expiration
- [ ] Protected endpoints return 401 without token
- [ ] Protected endpoints return 200 with valid token
- [ ] Token refresh mechanism works correctly
- [ ] Refresh tokens expire and are revoked

### Frontend Verification
- [ ] Login page renders without errors
- [ ] Form validation prevents invalid submissions
- [ ] Login API call is made correctly
- [ ] Loading state shown during authentication
- [ ] Success message displayed on successful login
- [ ] Error message displayed on login failure
- [ ] Redirect to /recruiter/dashboard after successful login
- [ ] Return URL query parameter is respected
- [ ] JWT access token stored in localStorage
- [ ] JWT refresh token stored in localStorage
- [ ] User data stored in localStorage
- [ ] JWT tokens sent with subsequent API requests
- [ ] Authorization header includes "Bearer <token>"
- [ ] Protected routes work with valid tokens
- [ ] Protected routes redirect to login without tokens

### Security Verification
- [ ] Passwords are never exposed in API responses
- [ ] JWT tokens are signed correctly
- [ ] Access tokens expire (default 15 minutes)
- [ ] Refresh tokens expire (default 7 days)
- [ ] Tokens are validated on protected endpoints
- [ ] Invalid/expired tokens are rejected with 401
- [ ] Brute force protection is in place (rate limiting)
- [ ] Password is not logged or exposed in errors

### Integration Verification
- [ ] Login page → Backend API integration works
- [ ] AuthContext state updates correctly after login
- [ ] ProtectedRoute component respects authentication state
- [ ] RecruiterLayout displays user menu after login
- [ ] API client includes JWT token in requests
- [ ] Token refresh happens automatically (if implemented)
- [ ] Full login-to-protected-route flow works end-to-end

## Troubleshooting

### Issue: Login fails with "Network Error"
**Solution:** Check that the backend is running and accessible:
```bash
# Check backend health
curl http://localhost:8000/health

# Or check in browser
# http://localhost:8000/docs
```

### Issue: Login succeeds but no redirect happens
**Solution:** Check browser console for errors:
- Verify AuthProvider is wrapping the app (check main.tsx)
- Check if navigate() function is working
- Look for React Router errors in console

### Issue: JWT tokens not storing in localStorage
**Solution:** Open browser DevTools Console and check for errors:
- Verify localStorage is enabled in browser
- Check for quota exceeded errors
- Verify AuthContext login function is working

### Issue: Protected routes still redirect to login after successful login
**Solution:**
- Check if tokens are actually stored in localStorage
- Verify ProtectedRoute component is checking authentication correctly
- Check if useAuth hook returns correct isAuthenticated state
- Look for JWT validation errors in network tab

### Issue: API requests don't include Authorization header
**Solution:**
- Check frontend/src/api/client.ts interceptor configuration
- Verify getAuthToken() function retrieves token from correct localStorage key
- Check browser Network tab to see if Authorization header is present

### Issue: 401 errors on protected routes even after login
**Solution:**
- Verify JWT token is valid (check expiration)
- Check backend JWT validation logic
- Ensure token format is correct (Bearer <token>)
- Verify backend CORS configuration

### Issue: Login with valid credentials fails
**Solution:**
- Verify user exists in database
- Check password is correct (passwords are case-sensitive)
- Ensure user.is_active is True in database
- Check backend logs for authentication errors

## Test Data Cleanup

After testing, you can clean up test users:

### Option 1: Via Database
```sql
DELETE FROM users WHERE email = 'test_login@example.com';
DELETE FROM refresh_tokens WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE 'test_%@example.com'
);
```

### Option 2: Via API (if admin endpoint exists)
```bash
# Requires admin authentication
TOKEN="<admin_token>"
USER_ID="<user_id_to_delete>"
curl -X DELETE http://localhost:8000/api/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN"
```

## Success Criteria

The login and protected route access flow is considered working correctly when:

1. ✅ User can navigate to login page
2. ✅ Login form validates input correctly
3. ✅ Valid credentials successfully authenticate
4. ✅ Invalid credentials are rejected with error message
5. ✅ JWT access and refresh tokens are generated
6. ✅ Tokens are stored correctly in localStorage
7. ✅ User is redirected to dashboard (or return URL) after login
8. ✅ Tokens are sent with API requests in Authorization header
9. ✅ Protected recruiter routes are accessible with valid token
10. ✅ Protected routes redirect to login without token
11. ✅ Invalid/expired tokens are rejected by protected routes
12. ✅ Logout clears tokens and prevents access to protected routes
13. ✅ Full end-to-end flow works: login → token storage → protected route access

## Next Steps

After completing login flow testing, proceed to:
1. **subtask-8-3**: Test logout and token invalidation flow
2. **subtask-8-4**: Test password reset flow via email
3. **subtask-8-5**: Test role-based access control (Admin vs Recruiter vs Viewer)

## Notes

- The default role for test users is "Recruiter"
- JWT access tokens expire in 15 minutes by default
- JWT refresh tokens expire in 7 days by default
- The system supports automatic token refresh (if implemented in AuthContext)
- Login page respects `?return=` query parameter for post-login redirect
- All protected routes require valid JWT authentication
- Admin endpoints require Admin role in addition to authentication
