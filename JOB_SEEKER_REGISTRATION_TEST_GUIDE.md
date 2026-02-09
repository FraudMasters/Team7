# Job Seeker Registration Flow Testing Guide

## Overview
This guide provides step-by-step instructions for testing the job seeker registration flow with email verification.

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

### Backend Integration Test
We've provided a comprehensive Python test suite that tests the complete job seeker registration flow:

```bash
cd backend
pytest tests/integration/test_job_seeker_registration_flow.py -v -s
```

This test suite covers:
1. ✅ Job seeker registration with explicit role
2. ✅ Job seeker registration with default role
3. ✅ Duplicate registration rejection
4. ✅ Invalid role validation
5. ✅ Password validation requirements
6. ✅ Job seeker role uniqueness
7. ✅ Multiple job seeker registrations

### Expected Output
```
=========================== test session starts ============================
tests/integration/test_job_seeker_registration_flow.py::test_job_seeker_registration_with_role PASSED
tests/integration/test_job_seeker_registration_flow.py::test_job_seeker_registration_default_role PASSED
tests/integration/test_job_seeker_registration_flow.py::test_job_seeker_duplicate_registration PASSED
tests/integration/test_job_seeker_registration_flow.py::test_job_seeker_invalid_role PASSED
tests/integration/test_job_seeker_registration_flow.py::test_job_seeker_password_validation PASSED
tests/integration/test_job_seeker_registration_flow.py::test_job_seeker_role_uniqueness PASSED
tests/integration/test_job_seeker_registration_flow.py::test_multiple_job_seekers_can_register PASSED
============================ 7 passed in 2.34s =============================
```

### E2E Flow Test
For complete end-to-end testing including email verification:

```bash
cd backend
pytest tests/integration/test_job_seeker_e2e_complete_flow.py -v -s
```

This script tests:
1. ✅ Job seeker registration via API
2. ✅ User created with job_seeker role
3. ✅ Email verification token generation
4. ✅ Email verification confirmation
5. ✅ User login with credentials
6. ✅ JWT token generation
7. ✅ Protected endpoint access
8. ✅ Token refresh functionality
9. ✅ Logout and token revocation

## Manual Browser Testing

### Test Case 1: Job Seeker Registration Flow

**Steps:**
1. Open browser to `http://localhost:5173/job-seeker/register`
2. Fill in the registration form:
   - **First Name**: John
   - **Last Name**: Doe
   - **Email**: john.doe@example.com
   - **Password**: TestPass123!
   - **Confirm Password**: TestPass123!
3. Click "Create Job Seeker Account" button
4. Verify success message appears
5. Verify redirect to login page

**Expected Results:**
- ✅ Page displays with green color theme (job seeker branding)
- ✅ Form validation works (all fields required)
- ✅ Email format validation (must contain @)
- ✅ Password strength validation (minimum 8 characters, uppercase, lowercase, number, special character)
- ✅ Password match validation (both passwords must match)
- ✅ Loading state shown during registration
- ✅ Success message displayed after registration
- ✅ Redirect to login page occurs
- ✅ No console errors

### Test Case 2: Login After Registration

**Steps:**
1. After registration, you should be on the login page
2. Enter credentials:
   - **Email**: john.doe@example.com
   - **Password**: TestPass123!
3. Click "Sign In" button

**Expected Results:**
- ✅ Login is successful
- ✅ JWT access token is stored in localStorage
- ✅ JWT refresh token is stored in localStorage
- ✅ User data is stored in localStorage with role: "job_seeker"
- ✅ Redirect to dashboard or appropriate page
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
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "is_superuser": false
  }
}
```

### Test Case 4: Email Verification Flow

**Steps:**
1. After registration, request email verification:
   ```bash
   curl -X POST http://localhost:8000/api/auth/request-email-verification \
     -H "Content-Type: application/json" \
     -d '{"email": "john.doe@example.com"}'
   ```
2. Get verification token from backend logs or database
3. Navigate to: `http://localhost:5173/verify-email?token=<YOUR_TOKEN>`
4. Or verify via API:
   ```bash
   curl -X POST http://localhost:8000/api/auth/verify-email \
     -H "Content-Type: application/json" \
     -d '{"token": "<YOUR_TOKEN>"}'
   ```

**Expected Results:**
- ✅ Email verification request succeeds
- ✅ Token is generated and stored in database
- ✅ Verification page loads and validates token
- ✅ Success message displayed after verification
- ✅ User's `is_verified` status updated to `true` in database
- ✅ Verification token is revoked after use

### Test Case 5: Navigation Links

**Steps:**
1. On the job seeker registration page, click "Already have an account? Sign in"
2. Click "Register as an employer" link

**Expected Results:**
- ✅ "Sign in" link navigates to login page
- ✅ "Register as an employer" link navigates to recruiter registration page
- ✅ All navigation works correctly
- ✅ No broken links or 404 errors

### Test Case 6: Password Validation

**Steps:**
1. Try entering passwords that don't meet requirements:
   - Too short: `Pass1!`
   - No uppercase: `password123!`
   - No lowercase: `PASSWORD123!`
   - No number: `Password!`
   - No special character: `Password123`

**Expected Results:**
- ✅ Each invalid password shows appropriate error message
- ✅ Submit button is disabled until password is valid
- ✅ Visual feedback indicates password strength
- ✅ Confirm password matching is validated

## API Endpoint Testing with cURL

### Test Job Seeker Registration Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jobseeker@example.com",
    "password": "TestPass123!",
    "full_name": "Jane JobSeeker",
    "role": "job_seeker"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "jobseeker@example.com",
  "full_name": "Jane JobSeeker",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "message": "User registered successfully"
}
```

### Test Registration with Default Role

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "defaultseeker@example.com",
    "password": "TestPass123!",
    "full_name": "Default Seeker"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "defaultseeker@example.com",
  "full_name": "Default Seeker",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "message": "User registered successfully"
}
```
Note: When no role is specified, it defaults to `job_seeker`.

### Test Invalid Role

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "invalid_role"
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "detail": "Invalid role. Must be one of: admin, hiring_manager, job_seeker, recruiter, viewer"
}
```

### Test Duplicate Registration

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jobseeker@example.com",
    "password": "AnotherPass123!",
    "full_name": "Another Name",
    "role": "job_seeker"
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "detail": "Email already registered"
}
```

### Test Email Verification Request

```bash
curl -X POST http://localhost:8000/api/auth/request-email-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "jobseeker@example.com"}'
```

**Expected Response (200 OK):**
```json
{
  "message": "If the email exists, a verification link has been sent"
}
```

### Test Email Verification

```bash
# Get token from database or logs
curl -X POST http://localhost:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "your_verification_token_here"}'
```

**Expected Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

### Test Login Endpoint

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jobseeker@example.com",
    "password": "TestPass123!"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "jobseeker@example.com",
    "full_name": "Jane JobSeeker",
    "is_active": true,
    "is_verified": true,
    "is_superuser": false
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
  "email": "jobseeker@example.com",
  "full_name": "Jane JobSeeker",
  "is_active": true,
  "is_verified": true,
  "is_superuser": false
}
```

## Verification Checklist

### Backend Verification
- [ ] Registration endpoint creates user with job_seeker role in database
- [ ] Password is hashed with bcrypt (not stored as plaintext)
- [ ] Default role is job_seeker when no role is specified
- [ ] Invalid role values are rejected with appropriate error message
- [ ] JWT access token is generated with correct expiration
- [ ] JWT refresh token is generated and stored in database
- [ ] Login validates credentials correctly
- [ ] Protected endpoints return 401 without token
- [ ] Protected endpoints return 200 with valid token
- [ ] Email verification tokens are generated on request
- [ ] Email verification tokens expire after 24 hours
- [ ] Email verification tokens are revoked after use

### Frontend Verification
- [ ] Job seeker registration page renders without errors at /job-seeker/register
- [ ] Green color theme is applied for job seeker branding
- [ ] Form validation prevents invalid submissions
- [ ] Loading state shown during API calls
- [ ] Success message displayed on successful registration
- [ ] Error message displayed on registration failure
- [ ] Redirect to login page after successful registration
- [ ] Navigation links to login and employer registration work
- [ ] Email verification page renders and validates token
- [ ] Login page stores tokens in localStorage
- [ ] User menu shows logged-in user information
- [ ] Logout clears tokens from localStorage
- [ ] Protected routes work with valid tokens
- [ ] Protected routes redirect to login without tokens

### Database Verification
- [ ] User record created in users table
- [ ] Password stored as bcrypt hash (starts with $2b$)
- [ ] job_seeker role assigned in roles table
- [ ] is_active = true by default
- [ ] is_verified = false by default
- [ ] Email verification token stored in refresh_tokens table
- [ ] is_verified = true after verification
- [ ] Verification token revoked after use

### Security Verification
- [ ] Passwords meet requirements (min 8 chars, uppercase, lowercase, number, special character)
- [ ] Passwords are hashed with bcrypt
- [ ] JWT tokens are signed correctly
- [ ] Access tokens expire (default 30 minutes)
- [ ] Refresh tokens expire (default 7 days)
- [ ] Tokens are validated on protected endpoints
- [ ] Invalid tokens are rejected with 401
- [ ] Email verification tokens expire after 24 hours
- [ ] Duplicate email registration is prevented
- [ ] Invalid role values are rejected

## Troubleshooting

### Issue: Registration fails with validation error
**Solution:** Ensure password meets all requirements:
- Minimum 8 characters
- Contains uppercase letter
- Contains lowercase letter
- Contains number
- Contains special character

Example valid password: `TestPass123!`

### Issue: "Email already registered" error
**Solution:** Use a different email address or delete the existing user from the database:
```sql
DELETE FROM roles WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com');
DELETE FROM users WHERE email = 'test@example.com';
```

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

### Issue: Email verification token not found
**Solution:**
- Check backend logs for the generated token
- Query the database directly:
  ```sql
  SELECT token, expires_at, is_revoked
  FROM refresh_tokens
  WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com')
  ORDER BY created_at DESC
  LIMIT 1;
  ```
- Request a new verification token via API

### Issue: "Invalid or expired verification token"
**Solution:**
- Ensure the token is copied correctly (no extra spaces)
- Check that the token hasn't expired (24-hour limit)
- Verify the token hasn't been revoked already
- Request a new verification token

## Test Data Cleanup

After testing, you can clean up test users:

### Option 1: Via Database
```sql
-- Delete test job seekers and related records
DELETE FROM refresh_tokens WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE '%@example.com' AND id IN (
    SELECT user_id FROM roles WHERE role = 'job_seeker'
  )
);
DELETE FROM roles WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE '%@example.com'
);
DELETE FROM users WHERE email LIKE '%@example.com';
```

### Option 2: Specific User Cleanup
```sql
-- Delete specific test user
DELETE FROM refresh_tokens WHERE user_id = (
  SELECT id FROM users WHERE email = 'jobseeker@example.com'
);
DELETE FROM roles WHERE user_id = (
  SELECT id FROM users WHERE email = 'jobseeker@example.com'
);
DELETE FROM users WHERE email = 'jobseeker@example.com';
```

## Success Criteria

The job seeker registration flow is considered working correctly when:

1. ✅ Job seeker can register with valid email/password/name
2. ✅ Default role is job_seeker when no role is specified
3. ✅ Invalid role values are rejected with helpful error messages
4. ✅ Password is hashed and stored securely with bcrypt
5. ✅ Duplicate email registration is prevented
6. ✅ Email verification token is generated on request
7. ✅ Email can be verified using the token
8. ✅ User can log in with registered credentials
9. ✅ JWT tokens are generated and returned
10. ✅ Tokens are stored correctly in localStorage
11. ✅ Tokens are sent with subsequent API requests
12. ✅ Protected endpoints are accessible with valid tokens
13. ✅ Protected endpoints reject invalid/expired tokens
14. ✅ User can logout and tokens are cleared
15. ✅ Frontend redirects correctly based on auth state
16. ✅ Green color theme is applied for job seeker branding
17. ✅ Navigation links work correctly

## Key Differences from Recruiter Registration

| Feature | Job Seeker Registration | Recruiter Registration |
|---------|------------------------|------------------------|
| URL Path | `/job-seeker/register` | `/register` |
| Color Theme | Green (growth/jobs) | Purple (professional) |
| Form Fields | First Name, Last Name, Email, Password | Name, Email, Password |
| Default Role | `job_seeker` | `recruiter` |
| Welcome Email | Job seeker specific template | Recruiter specific template |
| Navigation | Links to employer registration | Links to job seeker registration |

## Notes

- Email verification is implemented for job seekers
- The default role for job seeker registration is "job_seeker"
- JWT secrets should be configured in production using environment variables
- Refresh tokens are stored in the database and can be revoked
- Access tokens are short-lived (30 minutes) by default
- The system supports token refresh without requiring re-login
- Email verification tokens expire after 24 hours
- Password requirements are enforced for security
- Duplicate email registration is prevented
