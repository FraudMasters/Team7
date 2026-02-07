# Password Reset Flow Testing Guide

This guide provides comprehensive testing instructions for the password reset flow via email feature.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Automated Testing](#automated-testing)
3. [Manual Browser Testing](#manual-browser-testing)
4. [API Endpoint Testing](#api-endpoint-testing)
5. [Verification Checklist](#verification-checklist)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Database Setup

Ensure your PostgreSQL database is running and migrations are applied:

```bash
cd backend
alembic upgrade head
```

### 2. Backend Service

Start the backend API server:

```bash
cd backend
python main.py
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "service": "agenthr-api",
  "status": "healthy",
  "version": "0.1.0"
}
```

### 3. Frontend Service

Start the frontend development server:

```bash
cd frontend
npm run dev
```

Access the application at: http://localhost:5173

### 4. Test User (Optional)

If you want to test with an existing user, create one first:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testreset@example.com",
    "password": "OldPass123",
    "name": "Test Reset User"
  }'
```

---

## Automated Testing

### Run the Automated Test Script

The automated test script verifies most of the password reset flow:

```bash
cd backend
python test_password_reset_flow.py
```

**Note**: The automated script cannot test the complete end-to-end flow because:
- Password reset tokens are sent via email in production
- For testing, you need to capture the token from backend logs or use a test email service
- The script will guide you to manual testing for the complete flow

### What the Automated Script Tests

✓ Backend health check
✓ Test user setup
✓ Login with old password (before reset)
✓ Request password reset API
✓ Reset request for non-existent email (security)
✓ Reset with invalid token (error handling)
✓ Token expiration handling (documentation)

---

## Manual Browser Testing

### Test Case 1: Complete Password Reset Flow

**Objective**: Verify a user can successfully reset their password via email

**Steps**:

1. **Navigate to Forgot Password Page**
   - Go to: http://localhost:5173/forgot-password
   - Verify the page loads with title "Forgot Password"
   - Verify email input field is present
   - Verify form helper text explains the process

2. **Submit Password Reset Request**
   - Enter email: `testreset@example.com` (or your test email)
   - Click "Send Reset Link" button
   - Verify success message appears: "Password reset email sent! Check your inbox for further instructions."
   - Verify loading spinner shows during submission
   - Verify form is hidden after successful submission

3. **Check Backend Logs for Reset Token**
   - Check backend console output for password reset log
   - Look for the generated reset token (UUID format)
   - Example log: `Password reset requested for email: testreset@example.com, token: abc123-def456-...`

4. **Navigate to Reset Password Page**
   - Construct the reset link manually (in production, this comes from email)
   - Format: `http://localhost:5173/reset-password?token=<TOKEN_FROM_LOGS>`
   - Example: `http://localhost:5173/reset-password?token=abc123-def456-789`
   - Navigate to this URL

5. **Reset Password**
   - Verify the page loads with title "Reset Password"
   - Verify new password field is present
   - Verify confirm password field is present
   - Enter new password: `NewPass456`
   - Enter confirm password: `NewPass456`
   - Click "Reset Password" button
   - Verify success message appears: "Password reset successfully!"
   - Verify page redirects to /login after 2 seconds

6. **Verify Login with New Password**
   - On the login page, enter email: `testreset@example.com`
   - Enter new password: `NewPass456`
   - Click "Sign In" button
   - Verify successful login (redirects to dashboard or jobs page)

7. **Verify Old Password No Longer Works**
   - Logout from the application
   - Navigate to: http://localhost:5173/login
   - Enter email: `testreset@example.com`
   - Enter old password: `OldPass123`
   - Click "Sign In" button
   - Verify error message: "Could not validate credentials" or similar
   - Verify login fails with 401 status

**Expected Result**: User successfully resets password and can log in with new password, but not with old password

---

### Test Case 2: Forgot Password Form Validation

**Objective**: Verify form validation on forgot password page

**Steps**:

1. **Empty Email Field**
   - Navigate to: http://localhost:5173/forgot-password
   - Leave email field empty
   - Click "Send Reset Link" button
   - Verify error message: "Please enter your email address"

2. **Invalid Email Format**
   - Enter email: `notanemail`
   - Click "Send Reset Link" button
   - Verify error message: "Please enter a valid email address"

3. **Email Without @ Symbol**
   - Enter email: `userexample.com`
   - Click "Send Reset Link" button
   - Verify error message: "Please enter a valid email address"

4. **Valid Email Format**
   - Enter email: `valid@example.com`
   - Click "Send Reset Link" button
   - Verify no validation errors
   - Verify API call is made to backend

**Expected Result**: Form validation prevents submission of invalid email addresses

---

### Test Case 3: Reset Password Form Validation

**Objective**: Verify form validation on reset password page

**Steps**:

1. **Missing Token**
   - Navigate to: http://localhost:5173/reset-password (without token parameter)
   - Verify error message: "Invalid or missing reset token. Please request a new password reset link."

2. **Empty Password Fields**
   - Navigate to: http://localhost:5173/reset-password?token=test123
   - Leave both password fields empty
   - Click "Reset Password" button
   - Verify error message: "Please fill in all fields"

3. **Password Too Short**
   - Enter new password: `Short1`
   - Enter confirm password: `Short1`
   - Click "Reset Password" button
   - Verify error message: "Password must be at least 8 characters long"

4. **Passwords Do Not Match**
   - Enter new password: `Password123`
   - Enter confirm password: `Different456`
   - Click "Reset Password" button
   - Verify error message: "Passwords do not match"

5. **Valid Password Reset**
   - Enter new password: `ValidPass123`
   - Enter confirm password: `ValidPass123`
   - Click "Reset Password" button
   - Verify no validation errors
   - Verify API call is made to backend

**Expected Result**: Form validation prevents submission of invalid passwords

---

### Test Case 4: Password Reset for Non-existent Email

**Objective**: Verify security behavior when requesting reset for non-existent email

**Steps**:

1. **Navigate to Forgot Password Page**
   - Go to: http://localhost:5173/forgot-password

2. **Submit Non-existent Email**
   - Enter email: `nonexistent@example.com`
   - Click "Send Reset Link" button

3. **Verify Response**
   - Verify success message appears (not error)
   - Message: "Password reset email sent! Check your inbox for further instructions."
   - This prevents email enumeration attacks

**Expected Result**: Returns success regardless of email existence (security best practice)

---

### Test Case 5: Invalid Reset Token

**Objective**: Verify error handling for invalid reset tokens

**Steps**:

1. **Navigate with Invalid Token**
   - Go to: http://localhost:5173/reset-password?token=invalid_token
   - Verify page loads (form validation happens on submit)

2. **Submit with Invalid Token**
   - Enter new password: `NewPass123`
   - Enter confirm password: `NewPass123`
   - Click "Reset Password" button
   - Verify error message: "Failed to reset password. Please try again or request a new reset link."
   - Verify user stays on reset page

**Expected Result**: Invalid token is rejected with user-friendly error message

---

### Test Case 6: Link Back to Login Page

**Objective**: Verify navigation links between auth pages

**Steps**:

1. **Forgot Password Page**
   - Navigate to: http://localhost:5173/forgot-password
   - Verify link text: "Remember your password? Sign in"
   - Click "Sign in" link
   - Verify redirects to: http://localhost:5173/login

2. **Reset Password Page**
   - Navigate to: http://localhost:5173/reset-password?token=test123
   - Verify link text: "Remember your password? Sign in"
   - Click "Sign in" link
   - Verify redirects to: http://localhost:5173/login

**Expected Result**: Navigation links work correctly between auth pages

---

### Test Case 7: Loading States During API Calls

**Objective**: Verify UI shows loading indicators during API requests

**Steps**:

1. **Forgot Password Loading State**
   - Navigate to: http://localhost:5173/forgot-password
   - Enter email: `test@example.com`
   - Click "Send Reset Link" button
   - Verify button shows loading spinner (CircularProgress)
   - Verify button is disabled during loading
   - Verify button text changes to "Send Reset Link" after completion

2. **Reset Password Loading State**
   - Navigate to: http://localhost:5173/reset-password?token=test123
   - Enter passwords: `NewPass123` / `NewPass123`
   - Click "Reset Password" button
   - Verify button shows loading spinner
   - Verify button is disabled during loading
   - Verify button text changes to "Reset Password" after completion

**Expected Result**: Loading states provide visual feedback during API calls

---

### Test Case 8: Browser Back Button After Reset

**Objective**: Verify navigation behavior after password reset

**Steps**:

1. **Reset Password Successfully**
   - Complete a password reset flow (see Test Case 1)
   - Wait for redirect to /login

2. **Use Browser Back Button**
   - Click browser back button
   - Verify redirects to login (or stays on login)
   - Verify user cannot go back to reset page after successful reset

**Expected Result**: Browser back button does not return to reset page after successful reset

---

### Test Case 9: Multiple Reset Requests

**Objective**: Verify handling of multiple password reset requests

**Steps**:

1. **First Reset Request**
   - Navigate to: http://localhost:5173/forgot-password
   - Enter email: `testreset@example.com`
   - Click "Send Reset Link"
   - Note the success message

2. **Second Reset Request**
   - Click "Sign in" link
   - Click "Forgot password?" link
   - Enter same email: `testreset@example.com`
   - Click "Send Reset Link"
   - Verify success message appears again

3. **Verify Tokens**
   - Check backend logs
   - Each request should generate a new reset token
   - Only the latest token should be valid (implementation-dependent)

**Expected Result**: Multiple reset requests are handled gracefully

---

### Test Case 10: Password Requirements Enforcement

**Objective**: Verify password requirements are enforced during reset

**Password Requirements**:
- Minimum 8 characters
- Must contain uppercase letter
- Must contain lowercase letter
- Must contain number

**Steps**:

1. **Test Too Short Password**
   - Navigate to reset page with valid token
   - Enter password: `Short1`
   - Verify error: "Password must be at least 8 characters long"

2. **Test No Uppercase**
   - Enter password: `nouppercase123`
   - Submit to backend
   - Verify error from backend about uppercase requirement

3. **Test No Lowercase**
   - Enter password: `NOLOWERCASE123`
   - Submit to backend
   - Verify error from backend about lowercase requirement

4. **Test No Number**
   - Enter password: `NoNumberPass`
   - Submit to backend
   - Verify error from backend about number requirement

5. **Test Valid Password**
   - Enter password: `ValidPass123`
   - Submit to backend
   - Verify success

**Expected Result**: Password requirements are enforced by both frontend and backend

---

## API Endpoint Testing

### Test 1: Request Password Reset

```bash
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testreset@example.com"
  }'
```

**Expected Response** (200 OK):
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

**Note**: Returns 200 even if email doesn't exist (security)

---

### Test 2: Reset Password with Valid Token

First, get a reset token from backend logs or database, then:

```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN_HERE",
    "new_password": "NewSecurePass123"
  }'
```

**Expected Response** (200 OK):
```json
{
  "message": "Password reset successfully"
}
```

---

### Test 3: Reset Password with Invalid Token

```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "invalid_token_xyz",
    "new_password": "NewSecurePass123"
  }'
```

**Expected Response** (400 Bad Request or 401 Unauthorized):
```json
{
  "detail": "Invalid or expired reset token"
}
```

---

### Test 4: Reset Password - Token Too Short

```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "short",
    "new_password": "NewSecurePass123"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "detail": "Token must be at least 10 characters"
}
```

---

### Test 5: Reset Password - Password Too Short

```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "valid_token_here",
    "new_password": "Short1"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "detail": "Password must be at least 8 characters"
}
```

---

### Test 6: Reset Password - Password Requirements Not Met

```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "valid_token_here",
    "new_password": "lowercaseonly"
  }'
```

**Expected Response** (400 Bad Request):
```json
{
  "detail": "Password must contain uppercase, lowercase, and numbers"
}
```

---

### Test 7: Verify Login After Password Reset

```bash
# Login with new password
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testreset@example.com",
    "password": "NewSecurePass123"
  }'
```

**Expected Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "testreset@example.com",
    "name": "Test Reset User",
    "role": "Recruiter",
    "is_active": true,
    "email_verified": false
  }
}
```

---

### Test 8: Verify Old Password No Longer Works

```bash
# Try to login with old password
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testreset@example.com",
    "password": "OldPass123"
  }'
```

**Expected Response** (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

---

## Verification Checklist

### Backend Verification

- [ ] POST `/api/auth/forgot-password` endpoint exists
- [ ] POST `/api/auth/reset-password` endpoint exists
- [ ] Password reset tokens are generated correctly
- [ ] Tokens expire after 24 hours
- [ ] Reset request returns 200 even for non-existent emails (security)
- [ ] Invalid tokens are rejected with 400/401
- [ ] Expired tokens are rejected with 400/401
- [ ] Password requirements are enforced (min 8 chars, mixed case, numbers)
- [ ] Old password no longer works after reset
- [ ] New password works after reset
- [ ] All existing refresh tokens are revoked after password reset
- [ ] Proper logging for audit trail

### Frontend Verification

- [ ] `/forgot-password` route exists and renders
- [ ] `/reset-password` route exists and renders
- [ ] Forgot password form has email validation
- [ ] Reset password form has password validation (length, matching)
- [ ] Token parameter is extracted from URL query params
- [ ] Loading states show during API calls
- [ ] Success messages display correctly
- [ ] Error messages display correctly
- [ ] Navigation links work (back to login)
- [ ] Auto-redirect to login after successful reset
- [ ] Forms have proper autocomplete attributes
- [ ] No console errors during flow

### Security Verification

- [ ] Password reset tokens are secure (UUID, random)
- [ ] Tokens have expiration time (24 hours)
- [ ] Email enumeration is prevented (200 response for non-existent emails)
- [ ] Password requirements enforced by backend
- [ ] Old passwords are rejected after reset
- [ ] All refresh tokens revoked after password reset
- [ ] Reset tokens are single-use (consumed after reset)
- [ ] Proper error messages (no information leakage)

### Integration Verification

- [ ] ForgotPasswordPage integrates with authClient.forgotPassword()
- [ ] ResetPasswordPage integrates with authClient.resetPassword()
- [ ] Backend logs password reset requests for debugging
- [ ] Frontend handles API errors gracefully
- [ ] Token from email link is properly passed to reset page
- [ ] User can complete entire flow in browser without errors

---

## Troubleshooting

### Issue: Backend returns 500 error on forgot-password

**Possible Causes**:
1. Database connection issue
2. AuthService not properly initialized
3. Email service configuration missing

**Solutions**:
- Check backend logs for detailed error
- Verify database is running: `alembic current`
- Check AuthService configuration in backend/services/auth_service.py
- Note: Email sending may be mocked in development

---

### Issue: "Invalid or missing reset token" error

**Possible Causes**:
1. Token not included in URL query params
2. Token expired (> 24 hours)
3. Token already used (single-use)
4. Token malformed

**Solutions**:
- Verify URL format: `/reset-password?token=<TOKEN>`
- Check backend logs for generated token
- Generate new reset request
- Copy token carefully from logs/email

---

### Issue: "Password does not meet requirements" error

**Possible Causes**:
1. Password too short (< 8 characters)
2. Missing uppercase letter
3. Missing lowercase letter
4. Missing number

**Solutions**:
- Use password with mixed case and numbers: `SecurePass123`
- Verify password meets all requirements
- Check backend logs for specific requirement that failed

---

### Issue: Can still log in with old password after reset

**Possible Causes**:
1. Password reset didn't complete successfully
2. Database transaction not committed
3. Wrong user account

**Solutions**:
- Verify reset returned 200 status
- Check backend logs for reset confirmation
- Verify you're using the correct email
- Check database for password_hash update

---

### Issue: Frontend shows loading spinner forever

**Possible Causes**:
1. Backend not responding
2. CORS error
3. Network connectivity issue

**Solutions**:
- Check backend is running: `curl http://localhost:8000/health`
- Check browser console for CORS errors
- Verify API URL in frontend (.env file)
- Check browser Network tab for failed requests

---

### Issue: Reset token not found in backend logs

**Possible Causes**:
1. Logging level too high
2. Token not being logged (security)
3. Forgot-password request failed

**Solutions**:
- Check backend logging configuration
- Look for "Password reset requested" in logs
- Verify forgot-password request returned 200
- Use database query to find token in users table

---

### Issue: "Email already exists" error during test setup

**Possible Causes**:
1. Test user from previous run
2. Manual testing created same user

**Solutions**:
- Delete test user from database
- Use unique email for each test
- Check `test_password_reset_flow.py` handles existing users

---

## Test Data Cleanup

After testing, clean up test data from the database:

```sql
-- Connect to PostgreSQL database
psql agenthr

-- Delete test user
DELETE FROM users WHERE email LIKE 'test_%@example.com';

-- Delete reset tokens
DELETE FROM password_reset_tokens WHERE created_at < NOW() - INTERVAL '1 day';

-- Verify deletion
SELECT email FROM users WHERE email LIKE 'test_%@example.com';
```

---

## Next Steps

After completing the password reset flow testing:

1. ✅ Mark subtask-8-4 as completed
2. ✅ Move to subtask-8-5: Test role-based access control
3. ✅ Complete all integration tests in phase 8
4. ✅ Run comprehensive QA sign-off
5. ✅ Update implementation plan with test results

---

## Additional Resources

- Backend API Documentation: http://localhost:8000/docs
- Frontend Application: http://localhost:5173
- Implementation Plan: `.auto-claude/specs/050-user-authentication-authorization-system/implementation_plan.json`
- Automated Test Script: `backend/test_password_reset_flow.py`

---

**Last Updated**: 2026-02-03
**Test Suite Version**: 1.0
**Status**: Ready for Testing
