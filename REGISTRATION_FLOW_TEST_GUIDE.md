# User Registration Flow Testing Guide

## Overview
This guide provides step-by-step instructions for testing the user registration flow with email verification (subtask-8-1).

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
We've provided a comprehensive Python test script that tests the complete registration flow:

```bash
cd backend
python test_registration_flow.py
```

This script tests:
1. ✅ Backend health check
2. ✅ User registration via API
3. ✅ User login with credentials
4. ✅ JWT token generation
5. ✅ Protected endpoint access with token
6. ✅ JWT token structure validation
7. ✅ Unauthorized access rejection

### Expected Output
```
============================================================
  USER REGISTRATION FLOW - END-TO-END TEST
============================================================
ℹ Backend URL: http://localhost:8000
ℹ Test user: test_registration@example.com

============================================================
  1. Backend Health Check
============================================================
✓ Backend is running: resume-analysis-api
ℹ Version: 1.0.0

============================================================
  2. User Registration
============================================================
✓ Registration successful!
✓ User created with ID: <uuid>
✓ User name: Test Registration User
✓ User role: Recruiter
✓ Email verified: False

============================================================
  3. User Login
============================================================
✓ Login successful!
✓ Access token received
✓ Refresh token received
✓ Authenticated user: Test Registration User

============================================================
  4. Protected Endpoint Access
============================================================
✓ Protected endpoint accessible!
✓ Email matches registered user
✓ Name matches registered user

============================================================
  5. JWT Token Structure Validation
============================================================
✓ JWT has valid structure (header.payload.signature)
✓ JWT header contains algorithm
✓ JWT payload contains user ID and expiration

============================================================
  6. Unauthorized Access Test
============================================================
✓ Unauthorized request correctly rejected (401)

============================================================
  TEST SUMMARY
============================================================
✓ PASS: backend_health
✓ PASS: registration
✓ PASS: login
✓ PASS: protected_endpoint
✓ PASS: token_structure
✓ PASS: unauthorized_access

============================================================
✓ ALL TESTS PASSED!
============================================================
```

## Manual Browser Testing

### Test Case 1: User Registration Flow

**Steps:**
1. Open browser to `http://localhost:5173/register`
2. Fill in the registration form:
   - **Name**: Test User
   - **Email**: test@example.com
   - **Password**: TestPass123
   - **Confirm Password**: TestPass123
3. Click "Create Account" button
4. Verify success message appears
5. Verify redirect to login page after 2 seconds

**Expected Results:**
- ✅ Form validation works (all fields required)
- ✅ Email format validation (must contain @)
- ✅ Password length validation (minimum 8 characters)
- ✅ Password match validation (both passwords must match)
- ✅ Loading state shown during registration
- ✅ Success message displayed after registration
- ✅ Redirect to login page occurs
- ✅ No console errors

### Test Case 2: Login After Registration

**Steps:**
1. After registration, you should be on the login page
2. Enter credentials:
   - **Email**: test@example.com
   - **Password**: TestPass123
3. Click "Sign In" button

**Expected Results:**
- ✅ Login is successful
- ✅ JWT access token is stored in localStorage
- ✅ JWT refresh token is stored in localStorage
- ✅ User data is stored in localStorage
- ✅ Redirect to dashboard or jobs page
- ✅ User menu appears in header with logged-in user
- ✅ No console errors

### Test Case 3: Verify Token Storage

**Steps:**
1. After logging in, open browser DevTools (F12)
2. Go to Application tab → Local Storage
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
    "email": "test@example.com",
    "name": "Test User",
    "role": "Recruiter",
    "is_active": true,
    "email_verified": false
  }
}
```

### Test Case 4: Protected Route Access

**Steps:**
1. After logging in, try to access a protected route
2. Navigate to `http://localhost:5173/recruiter/dashboard`

**Expected Results:**
- ✅ Dashboard loads successfully
- ✅ No redirect to login page
- ✅ User information displayed in header
- ✅ No authentication errors

### Test Case 5: Logout and Token Cleanup

**Steps:**
1. Click on user avatar in header
2. Click "Logout" from the dropdown menu
3. Check localStorage in DevTools

**Expected Results:**
- ✅ Logout API call succeeds
- ✅ All auth tokens removed from localStorage
- ✅ User data removed from localStorage
- ✅ Redirect to login page
- ✅ Access to protected routes now redirects to login

## API Endpoint Testing with cURL

### Test Registration Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "apitest@example.com",
    "password": "TestPass123",
    "name": "API Test User"
  }'
```

**Expected Response (200 OK):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "apitest@example.com",
    "name": "API Test User",
    "role": "Recruiter",
    "is_active": true,
    "email_verified": false
  }
}
```

### Test Login Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "apitest@example.com",
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
    "email": "apitest@example.com",
    "name": "API Test User",
    "role": "Recruiter",
    "is_active": true,
    "email_verified": false
  }
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
  "email": "apitest@example.com",
  "name": "API Test User",
  "role": "Recruiter",
  "is_active": true,
  "email_verified": false
}
```

### Test Unauthorized Access

```bash
curl -X GET http://localhost:8000/api/auth/me
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

## Verification Checklist

### Backend Verification
- [ ] Registration endpoint creates user in database
- [ ] Password is hashed with bcrypt (not stored as plaintext)
- [ ] JWT access token is generated with correct expiration
- [ ] JWT refresh token is generated and stored in database
- [ ] Login validates credentials correctly
- [ ] Protected endpoints return 401 without token
- [ ] Protected endpoints return 200 with valid token
- [ ] Token contains correct user information in payload

### Frontend Verification
- [ ] Register page renders without errors
- [ ] Form validation prevents invalid submissions
- [ ] Loading state shown during API calls
- [ ] Success message displayed on successful registration
- [ ] Error message displayed on registration failure
- [ ] Redirect to login page after successful registration
- [ ] Login page stores tokens in localStorage
- [ ] User menu shows logged-in user information
- [ ] Logout clears tokens from localStorage
- [ ] Protected routes work with valid tokens
- [ ] Protected routes redirect to login without tokens

### Security Verification
- [ ] Passwords meet requirements (min 8 chars, mixed case, numbers)
- [ ] Passwords are hashed with bcrypt
- [ ] JWT tokens are signed correctly
- [ ] Access tokens expire (default 15 minutes)
- [ ] Refresh tokens expire (default 7 days)
- [ ] Tokens are validated on protected endpoints
- [ ] Invalid tokens are rejected with 401
- [ ] Email verification is required (optional, depending on config)

## Troubleshooting

### Issue: Backend connection refused
**Solution:** Ensure the backend service is running:
```bash
cd backend
python main.py
```

### Issue: Database connection error
**Solution:** Ensure PostgreSQL is running and migrations are applied:
```bash
cd backend
alembic upgrade head
```

### Issue: CORS errors in frontend
**Solution:** Check that `VITE_API_URL` in `frontend/.env` matches the backend URL:
```
VITE_API_URL=http://localhost:8000
```

### Issue: Tokens not storing in localStorage
**Solution:** Open browser DevTools Console and check for errors. Verify AuthProvider is wrapping the app.

### Issue: Registration fails with validation error
**Solution:** Ensure password meets requirements:
- Minimum 8 characters
- Contains uppercase letter
- Contains lowercase letter
- Contains number

Example valid password: `TestPass123`

## Test Data Cleanup

After testing, you can clean up test users:

### Option 1: Via Database
```sql
DELETE FROM users WHERE email LIKE 'test%@example.com' OR email LIKE 'apitest%@example.com';
```

### Option 2: Via API (if admin endpoint exists)
```bash
# Requires admin authentication
TOKEN="<admin_token>"
curl -X DELETE http://localhost:8000/api/users/<user_id> \
  -H "Authorization: Bearer $TOKEN"
```

## Success Criteria

The registration flow is considered working correctly when:

1. ✅ User can register with valid email/password/name
2. ✅ Password is hashed and stored securely
3. ✅ User can log in with registered credentials
4. ✅ JWT tokens are generated and returned
5. ✅ Tokens are stored correctly in localStorage
6. ✅ Tokens are sent with subsequent API requests
7. ✅ Protected endpoints are accessible with valid tokens
8. ✅ Protected endpoints reject invalid/expired tokens
9. ✅ User can logout and tokens are cleared
10. ✅ Frontend redirects correctly based on auth state

## Notes

- Email verification is implemented but optional for testing (you can skip email verification and still log in)
- The default role for new users is "Recruiter"
- JWT secrets should be configured in production using environment variables
- Refresh tokens are stored in the database and can be revoked
- Access tokens are short-lived (15 minutes) by default
- The system supports token refresh without requiring re-login
