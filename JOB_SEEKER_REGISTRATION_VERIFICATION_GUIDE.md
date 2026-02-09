# Job Seeker Registration - End-to-End Verification Guide

This guide provides step-by-step instructions for manually verifying the complete job seeker registration flow.

## Prerequisites

1. Backend server running on `http://localhost:8000`
2. Frontend server running on `http://localhost:5173`
3. PostgreSQL database with migrations applied
4. Email service configured (or check logs for verification tokens)

## Automated E2E Test

The fastest way to verify the complete flow is to run the automated E2E test:

```bash
cd backend
pytest tests/integration/test_job_seeker_e2e_complete_flow.py -v -s
```

This test will verify all 10 steps of the registration flow automatically.

## Manual Verification Steps

### Step 1: Navigate to Job Seeker Registration Page

1. Open browser to: `http://localhost:5173/job-seeker/register`
2. **Expected:** Page loads with job seeker registration form
3. **Verify:**
   - Green color theme (job seeker branding)
   - Form fields: First Name, Last Name, Email, Password, Confirm Password
   - "Create Job Seeker Account" button
   - Link to sign in page
   - Link to employer registration page

### Step 2: Fill Registration Form

1. Enter the following test data:
   - **First Name:** `Test`
   - **Last Name:** `JobSeeker`
   - **Email:** `testjobseeker@example.com`
   - **Password:** `TestPass123!`
   - **Confirm Password:** `TestPass123!`

2. **Expected:** Form accepts valid input
3. **Verify:** No validation errors shown

### Step 3: Submit Registration

1. Click "Create Job Seeker Account" button
2. **Expected:** Loading spinner appears, then redirect to login
3. **Verify:**
   - Success message displayed: "Registration successful! Please sign in."
   - Redirected to `http://localhost:5173/login`

### Step 4: Verify User Created in Database

1. Connect to PostgreSQL database
2. Run query:
   ```sql
   SELECT id, email, full_name, is_active, is_verified, created_at
   FROM users
   WHERE email = 'testjobseeker@example.com';
   ```

3. **Expected Results:**
   - User record exists with provided email
   - `is_active` = `true`
   - `is_verified` = `false` (not verified yet)
   - `password_hash` is bcrypt hash (starts with `$2b$`)

4. Verify job seeker role:
   ```sql
   SELECT r.role
   FROM roles r
   JOIN users u ON u.id = r.user_id
   WHERE u.email = 'testjobseeker@example.com';
   ```

5. **Expected:** Role = `job_seeker`

### Step 5: Verify Email Verification Token Generated

**Option A: Check Backend Logs**

1. Check backend console/logs for message:
   ```
   Email verification token generated for testjobseeker@example.com: <token>
   ```

2. Copy the verification token from logs

**Option B: Check Database**

```sql
SELECT token, expires_at, is_revoked
FROM refresh_tokens
WHERE user_id = (SELECT id FROM users WHERE email = 'testjobseeker@example.com')
ORDER BY created_at DESC
LIMIT 1;
```

3. **Expected:**
   - Token exists
   - `is_revoked` = `false`
   - `expires_at` is 24 hours in the future

**Option C: Request New Token**

If no token found, request via API:

```bash
curl -X POST http://localhost:8000/api/auth/request-email-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "testjobseeker@example.com"}'
```

### Step 6: Click Email Verification Link

1. Construct verification URL:
   ```
   http://localhost:5173/verify-email?token=<YOUR_TOKEN_HERE>
   ```

2. Open URL in browser OR use API:

```bash
curl -X POST http://localhost:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "<YOUR_TOKEN_HERE>"}'
```

3. **Expected:** Success response
```json
{
  "message": "Email verified successfully"
}
```

### Step 7: Verify Email is Verified

1. Check database:
   ```sql
   SELECT is_verified
   FROM users
   WHERE email = 'testjobseeker@example.com';
   ```

2. **Expected:** `is_verified` = `true`

3. Verify token revoked:
   ```sql
   SELECT is_revoked, revoked_at
   FROM refresh_tokens
   WHERE token = '<YOUR_TOKEN_HERE>';
   ```

4. **Expected:** `is_revoked` = `true`

### Step 8: Login with Credentials

**Option A: Via Frontend**

1. Navigate to: `http://localhost:5173/login`
2. Enter credentials:
   - Email: `testjobseeker@example.com`
   - Password: `TestPass123!`
3. Click "Sign In"

**Option B: Via API**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testjobseeker@example.com",
    "password": "TestPass123!"
  }'
```

4. **Expected:** Success response with tokens

### Step 9: Verify JWT Tokens Received

Expected response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "...",
    "email": "testjobseeker@example.com",
    "full_name": "Test JobSeeker",
    "is_active": true,
    "is_verified": true,
    "is_superuser": false
  }
}
```

**Verify:**
- `access_token` is present (JWT, ~200+ chars)
- `refresh_token` is present (JWT, ~200+ chars)
- `token_type` = "bearer"
- `expires_in` = 1800 (30 minutes)
- `user.email` matches registered email
- `user.is_verified` = `true`
- `user.is_active` = `true`

### Step 10: Verify Job Seeker Can Access Protected Endpoints

**Test Token Refresh:**

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<YOUR_REFRESH_TOKEN>"
  }'
```

**Expected:** New access token returned

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Test Protected Endpoint:**

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

**Expected:** User information returned (or 401/403 if endpoint not implemented)

**Test Logout:**

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<YOUR_REFRESH_TOKEN>"
  }'
```

**Expected:** Success message

```json
{
  "message": "Logged out successfully"
}
```

**Verify Token Revoked:**

```bash
# Try to use the refresh token again
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<YOUR_REFRESH_TOKEN>"
  }'
```

**Expected:** 401 Unauthorized (token revoked)

## Quick API Verification Script

Save this as `verify_job_seeker_flow.sh`:

```bash
#!/bin/bash

API_URL="http://localhost:8000/api/auth"
EMAIL="verifyjobseeker$(date +%s)@example.com"
PASSWORD="VerifyPass123!"

echo "Step 1: Register job seeker"
REGISTER=$(curl -s -X POST $API_URL/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Verify JobSeeker\",\"role\":\"job_seeker\"}")
echo $REGISTER | jq .

echo -e "\nStep 2: Request email verification"
VERIFY_REQUEST=$(curl -s -X POST $API_URL/request-email-verification \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}")
echo $VERIFY_REQUEST | jq .

# Note: You'll need to extract token from database/logs for actual verification
echo -e "\nNote: Get verification token from backend logs or database"

echo -e "\nStep 3: Login"
LOGIN=$(curl -s -X POST $API_URL/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
echo $LOGIN | jq .

ACCESS_TOKEN=$(echo $LOGIN | jq -r .access_token)
REFRESH_TOKEN=$(echo $LOGIN | jq -r .refresh_token)

echo -e "\nStep 4: Test token refresh"
REFRESH=$(curl -s -X POST $API_URL/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")
echo $REFRESH | jq .

echo -e "\nStep 5: Test logout"
LOGOUT=$(curl -s -X POST $API_URL/logout \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")
echo $LOGOUT | jq .

echo -e "\n✓ Flow verification complete"
```

## Troubleshooting

### Registration Fails

- **Error:** "Email is already registered"
  - **Solution:** Use a different email address or delete existing user

- **Error:** "Password does not meet requirements"
  - **Solution:** Ensure password has: 8+ chars, uppercase, lowercase, number, special char

### Email Verification Fails

- **Error:** "Invalid or expired verification token"
  - **Solution:** Request new verification token
  - **Solution:** Check token is copied correctly (no extra spaces)

### Login Fails

- **Error:** "Invalid email or password"
  - **Solution:** Verify user exists in database
  - **Solution:** Check password is correct
  - **Solution:** Ensure email was verified

### Token Errors

- **Error:** "Invalid or expired refresh token"
  - **Solution:** Login again to get new tokens
  - **Solution:** Check token hasn't been revoked

## Cleanup

To clean up test data:

```sql
-- Delete test user and related records
DELETE FROM refresh_tokens WHERE user_id = (
  SELECT id FROM users WHERE email LIKE 'testjobseeker@example.com'
);
DELETE FROM roles WHERE user_id = (
  SELECT id FROM users WHERE email LIKE 'testjobseeker@example.com'
);
DELETE FROM users WHERE email LIKE 'testjobseeker@example.com';
```

## Acceptance Criteria

The job seeker registration flow is verified when:

- [ ] Job seeker can register with email/password
- [ ] User is created with `job_seeker` role in database
- [ ] Email verification token is generated and stored
- [ ] Email can be verified using the token
- [ ] User can login with registered credentials
- [ ] JWT access and refresh tokens are received
- [ ] Tokens can be used to access protected endpoints
- [ ] Logout revokes refresh tokens
- [ ] Revoked tokens cannot be reused

## Additional Tests

### Test Password Validation

Verify weak passwords are rejected:

```bash
# Too short
curl -X POST $API_URL/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"short1A!","role":"job_seeker"}'
# Expected: 400 Bad Request

# Missing uppercase
curl -X POST $API_URL/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test2@example.com","password":"lowercase123!","role":"job_seeker"}'
# Expected: 400 Bad Request

# Missing number
curl -X POST $API_URL/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test3@example.com","password":"NoNumber!","role":"job_seeker"}'
# Expected: 400 Bad Request
```

### Test Duplicate Registration

```bash
# Register same email twice
curl -X POST $API_URL/register \
  -H "Content-Type: application/json" \
  -d '{"email":"duplicate@example.com","password":"Test123!","role":"job_seeker"}'

curl -X POST $API_URL/register \
  -H "Content-Type: application/json" \
  -d '{"email":"duplicate@example.com","password":"Test123!","role":"job_seeker"}'

# Expected: Second request returns 400 Bad Request
```

### Test Invalid Role

```bash
curl -X POST $API_URL/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","role":"invalid_role"}'

# Expected: 400 Bad Request with "Invalid role" message
```
