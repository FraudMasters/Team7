# SSO End-to-End Test Verification Guide

This document provides the verification steps for end-to-end SSO testing with Okta/Azure AD.

## Test Files Created

### 1. Unit Tests: `backend/tests/test_saml_service.py`
Comprehensive unit tests for the SAMLService class covering:
- Service initialization and configuration
- Certificate validation
- Health check functionality
- SAML config building
- Login redirect URL generation
- SAML response processing
- Metadata generation
- Attribute mapping
- Edge cases and error conditions
- Provider-specific scenarios (Okta, Azure AD, Google Workspace)

### 2. Integration Tests: `backend/tests/integration/test_sso_e2e.py`
End-to-end integration tests covering:
- SSO provider CRUD operations (create, read, update, delete)
- Certificate validation for X.509 certificates
- Provider type validation
- SP metadata generation
- SAML login initiation
- SAML ACS callback processing with mock responses
- Audit log verification for SSO_LOGIN events
- Multiple provider support
- Custom attribute mapping
- All supported provider types (okta, azure_ad, google_workspace, generic_saml)
- Provider statistics and filtering

## Running the Tests

### Unit Tests
```bash
cd backend
pytest tests/test_saml_service.py -v
```

### Integration Tests
```bash
cd backend
pytest tests/integration/test_sso_e2e.py -v
```

### All SSO Tests
```bash
cd backend
pytest tests/test_saml_service.py tests/integration/test_sso_e2e.py -v
```

### With Coverage
```bash
cd backend
pytest tests/test_saml_service.py tests/integration/test_sso_e2e.py --cov=services.saml_service --cov=api.sso --cov-report=html
```

## End-to-End Verification Steps

### Prerequisites
1. Backend server running with SAML configuration
2. PostgreSQL database available
3. Valid IdP credentials (Okta/Azure AD test account)

### Step 1: Initiate SAML Login from Frontend
**Verification:**
- Call `POST /api/sso/login` with provider_id
- Should receive 200 status with redirect_url
- Redirect URL should contain the IdP's SSO URL

**Expected Result:**
```json
{
  "redirect_url": "https://okta.com/sso?SAMLRequest=...",
  "provider_id": "sso-provider-uuid"
}
```

### Step 2: Complete IdP Authentication
**Verification:**
- User is redirected to IdP login page
- User enters credentials
- IdP authenticates user
- IdP generates SAML response

**Note:** This step happens on the IdP side (Okta/Azure AD) and cannot be automated without real IdP credentials.

### Step 3: Verify ACS Callback Processes Correctly
**Verification:**
- IdP POSTs SAML response to `POST /api/sso/acs`
- Backend validates SAML response signature
- Backend extracts user attributes
- Backend returns user data

**Expected Result:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "department": "Engineering",
  "name_id": "john.doe@example.com",
  "session_index": "session123",
  "provider_id": "sso-provider-uuid"
}
```

### Step 4: Confirm User Logged In with SSO
**Verification:**
- Frontend receives user data from ACS callback
- Frontend creates session with JWT token
- User is redirected to dashboard
- User can access protected routes

**API Calls:**
- Session creation via authentication endpoints
- JWT token stored in localStorage
- Protected routes return 200 (not 401)

### Step 5: Verify SSO_LOGIN Audit Event Created
**Verification:**
- Query audit logs: `GET /api/audit-logs?action_type=SSO_LOGIN`
- Should find entry with:
  - action: `SSO_LOGIN`
  - entity_type: `sso`
  - user_email: authenticated user's email
  - details: provider information

**Expected Result:**
```json
{
  "logs": [
    {
      "id": "audit-log-uuid",
      "action": "SSO_LOGIN",
      "entity_type": "sso",
      "entity_id": "provider-uuid",
      "recruiter_id": "user-uuid",
      "details": {
        "provider": "okta",
        "email": "user@example.com"
      },
      "created_at": "2026-02-04T10:00:00Z"
    }
  ]
}
```

## Test Coverage Summary

### Unit Test Coverage (test_saml_service.py)
- ✅ Service initialization
- ✅ Certificate validation (valid and invalid)
- ✅ Health checks (enabled, disabled, incomplete config)
- ✅ SAML config building
- ✅ Login redirect URL generation
- ✅ SAML response processing
- ✅ Metadata generation
- ✅ Attribute mapping (default and custom)
- ✅ Provider-specific configurations (Okta, Azure AD, Google)
- ✅ Edge cases (list attributes, missing attributes)

### Integration Test Coverage (test_sso_e2e.py)
- ✅ Create SSO provider
- ✅ List SSO providers (with filters)
- ✅ Update SSO provider
- ✅ Delete SSO provider
- ✅ Certificate validation (reject invalid certificates)
- ✅ Provider type validation (reject invalid types)
- ✅ SP metadata generation
- ✅ SAML login initiation
- ✅ Disabled provider rejection
- ✅ Non-existent provider rejection
- ✅ SAML ACS callback processing (with mock response)
- ✅ Audit log creation for SSO events
- ✅ Multiple providers per organization
- ✅ Custom attribute mapping
- ✅ All provider types (okta, azure_ad, google_workspace, generic_saml)
- ✅ Provider statistics

## Manual Testing with Real IdP

For actual end-to-end testing with a real IdP (Okta/Azure AD), follow these steps:

### 1. Configure Test IdP
**Okta Setup:**
1. Create a new Okta developer account (free)
2. Create a new SAML application in Okta
3. Upload the SP metadata from `GET /api/sso/metadata`
4. Configure the application with callback URL: `http://localhost:8000/api/sso/acs`
5. Copy the IdP metadata: entity_id, sso_url, x509_certificate

**Azure AD Setup:**
1. Create Azure AD tenant (free trial available)
2. Register a new enterprise application
3. Configure SAML-based SSO
4. Upload SP metadata
5. Copy IdP metadata from Azure AD

### 2. Create Test SSO Provider
```bash
curl -X POST http://localhost:8000/api/sso/providers \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "Test Okta",
    "provider_type": "okta",
    "entity_id": "https://dev-123456.okta.com/entityid",
    "sso_url": "https://dev-123456.okta.com/sso",
    "x509_certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
    "is_enabled": true
  }'
```

### 3. Initiate Login Flow
```bash
curl -X POST http://localhost:8000/api/sso/login \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "provider-uuid",
    "relay_state": "/dashboard"
  }'
```

### 4. Complete Authentication
- Open the redirect_url in a browser
- Login with test Okta/Azure AD credentials
- Verify SAML response is posted to ACS endpoint

### 5. Verify Results
- Check user is logged in
- Verify audit log entry exists
- Check session is created

## Troubleshooting

### Common Issues

**1. "SAML SSO is not configured"**
- Ensure SAML settings are configured in backend/.env
- Check SAML_SP_ENTITY_ID and SAML_SP_ACS_URL are set

**2. "Invalid X.509 certificate"**
- Verify certificate is in PEM format
- Certificate must include `-----BEGIN CERTIFICATE-----` header
- Certificate must include `-----END CERTIFICATE-----` footer

**3. "SSO provider not enabled"**
- Check provider's `is_enabled` field is true
- Ensure provider is active before using for login

**4. SAML signature validation fails**
- Verify the IdP certificate matches what's configured
- Check certificate hasn't expired
- Ensure certificate is from the correct IdP

**5. Audit log not created**
- Verify audit logging is enabled
- Check database connection
- Ensure SSO_LOGIN is in AuditActionType enum

## Security Considerations

### Test Data Security
- Use test/dev environments only
- Never use production credentials in tests
- Rotate test certificates regularly
- Don't commit real certificates to repository

### IdP Configuration
- Use separate test applications in Okta/Azure AD
- Limit test application to specific test users
- Disable test applications when not in use
- Monitor for unauthorized access attempts

### Certificate Management
- Generate self-signed certificates for testing
- Keep test certificates separate from production
- Document certificate expiration dates
- Use different certificates for each environment

## Success Criteria

The SSO end-to-end testing is considered successful when:

✅ All unit tests pass (test_saml_service.py)
✅ All integration tests pass (test_sso_e2e.py)
✅ SSO provider can be created and configured
✅ Login initiation returns valid redirect URL
✅ SAML response is processed successfully
✅ User attributes are extracted correctly
✅ Audit log entry is created with SSO_LOGIN event
✅ User can authenticate via SSO and access protected routes
✅ Multiple providers can be configured simultaneously
✅ Custom attribute mappings work correctly
✅ All supported provider types (Okta, Azure AD, Google Workspace) function correctly

## Next Steps

After successful testing:
1. Document any issues or edge cases found
2. Update SSO configuration documentation
3. Create user guide for SSO setup
4. Add monitoring for SSO authentication failures
5. Set up alerts for unusual SSO activity
6. Plan production deployment with real IdP integration
