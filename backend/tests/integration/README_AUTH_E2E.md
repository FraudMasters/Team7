# End-to-End Authentication Flow Test

## Overview

This comprehensive E2E test (`test_auth_flow_e2e.py`) verifies the complete authentication system integration across all components of the production-ready authentication implementation.

## Test Coverage

The test suite covers all 10 critical authentication requirements:

### 1. User Registration
- Register new user with email/password
- Verify user record created in database
- Verify session created
- Validate password strength requirements

### 2. Login Flow
- Login with valid credentials
- JWT tokens issued (access + refresh)
- Login attempts logged in database
- User information included in token payload

### 3. Protected Endpoint Access
- Access protected resources with valid access token
- Token validation and authorization
- User context extraction from JWT

### 4. Token Refresh Mechanism
- Use refresh token to obtain new access token
- Verify new token is different from old token
- Verify new token works for authentication
- Refresh token stored and validated in database

### 5. Account Lockout Protection
- Track failed login attempts
- Lock account after configured number of failures
- Failed attempts logged in database
- Lockout enforced at API level

### 6. OAuth Authentication
- OAuth provider infrastructure verified
- OAuth authorization endpoint available
- OAuth callback handling (requires live provider for full test)
- Account linking functionality

### 7. Session Management
- List active sessions for authenticated user
- Session details include device, location, timestamps
- Multiple concurrent sessions supported

### 8. Session Revocation
- Revoke individual sessions
- Verify revoked session no longer active
- Session cleanup in database

### 9. Session Analytics
- Track session events (login, logout, activity)
- Analytics endpoints accessible
- Session metrics calculated correctly
- Event logging in database

### 10. Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)
- CORS configuration

## Security Boundaries Test

The suite includes an additional test for security boundaries:

- Missing authentication header rejection
- Invalid token format rejection
- SQL injection protection
- XSS protection in user inputs
- Weak password rejection
- Token expiration handling

## Running the Tests

### Quick Run

```bash
cd backend
./tests/integration/run_auth_e2e_tests.sh
```

### Manual Run

```bash
cd backend
source .venv/bin/activate
pytest tests/integration/test_auth_flow_e2e.py -v -s
```

### Run Specific Test

```bash
# Main authentication flow
pytest tests/integration/test_auth_flow_e2e.py::test_complete_authentication_flow -v -s

# Security boundaries
pytest tests/integration/test_auth_flow_e2e.py::test_authentication_security_boundaries -v -s
```

### Run with Coverage

```bash
pytest tests/integration/test_auth_flow_e2e.py --cov=api.auth --cov=services --cov-report=html
```

## Test Database

The tests use an isolated SQLite database (`test_auth_e2e.db`) that is:
- Created fresh for each test run
- Populated with all necessary tables
- Cleaned up after test completion
- Independent from development/production databases

## Dependencies

The test requires:
- FastAPI application with authentication endpoints
- SQLAlchemy models (User, RefreshToken, LoginAttempt, Session, SessionEvent)
- JWT utilities for token creation/validation
- Session service and analytics service
- OAuth service (for infrastructure verification)

## Expected Outputs

### Successful Run

```
COMPLETE AUTHENTICATION FLOW E2E TEST
================================================================================

[Step 1] Register new user with email/password
--------------------------------------------------------------------------------
✓ User registered successfully with ID: abc-123
✓ User is active: True
✓ User record created in database

[Step 2] Login with password credentials
--------------------------------------------------------------------------------
✓ JWT tokens issued successfully
✓ Access token validated
✓ Refresh token stored in database
✓ Login attempt logged

[... continues through all 10 steps ...]

AUTHENTICATION FLOW E2E TEST COMPLETED SUCCESSFULLY
================================================================================

✓ All 10 verification steps completed
```

## Integration with CI/CD

This test should be run:
- Before merging authentication-related pull requests
- As part of the integration test suite in CI/CD
- Before deploying to staging/production
- After any changes to authentication services

## Troubleshooting

### Common Issues

**Issue**: Tests fail with database connection errors
**Solution**: Ensure PostgreSQL/SQLite is running and accessible

**Issue**: OAuth tests fail
**Solution**: OAuth tests verify infrastructure only; full OAuth flow requires live provider credentials

**Issue**: Session tests fail
**Solution**: Ensure Redis is running for session storage

**Issue**: Security header tests fail
**Solution**: Check middleware configuration in FastAPI application

## Maintenance

When updating authentication features:
1. Update corresponding test cases in this file
2. Add new verification steps if new features are added
3. Update this README with new requirements
4. Ensure backwards compatibility with existing tests

## Related Tests

- `test_jwt_refresh.py` - Detailed JWT refresh flow tests
- `test_oauth_flow.py` - OAuth provider integration tests
- `test_login_protection.py` - Account lockout and login tracking tests
- `test_session_analytics.py` - Session analytics service tests
- `test_sessions_e2e.py` - Session management E2E tests

## Test Markers

The tests use pytest markers:
- `@pytest.mark.asyncio` - Async test execution
- `@pytest.mark.e2e` - End-to-end test classification

Run only E2E tests:
```bash
pytest -m e2e
```

## Performance

Typical test execution time: 5-15 seconds
- Registration: ~500ms
- Login: ~500ms
- Token operations: ~200ms each
- Session operations: ~300ms each
- Analytics queries: ~500ms

## Success Criteria

All tests must pass with:
- 100% of assertions passing
- No database errors
- No authentication bypasses
- All security headers present
- All session events logged
- All login attempts tracked
