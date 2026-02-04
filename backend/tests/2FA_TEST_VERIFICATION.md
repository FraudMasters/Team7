# 2FA (Two-Factor Authentication) Test Verification Guide

This document provides comprehensive instructions for running and verifying the 2FA tests, including unit tests, integration tests, and end-to-end verification steps.

## Table of Contents

1. [Test Overview](#test-overview)
2. [Running Unit Tests](#running-unit-tests)
3. [Running Integration Tests](#running-integration-tests)
4. [End-to-End Verification Steps](#end-to-end-verification-steps)
5. [Manual Testing with Real Services](#manual-testing-with-real-services)
6. [Troubleshooting Common Issues](#troubleshooting-common-issues)
7. [Success Criteria](#success-criteria)

---

## Test Overview

The 2FA test suite includes:

### Unit Tests
- **test_totp_service.py**: 30+ tests covering TOTP service functionality
  - Secret generation
  - Code verification with time windows
  - Provisioning URI generation for QR codes
  - Backup code generation and validation
  - Algorithm support (SHA1, SHA256, SHA512)
  - Health checks

- **test_sms_service.py**: 30+ tests covering SMS service functionality
  - Phone number normalization and validation
  - Verification code generation
  - SMS sending via Twilio (mocked)
  - Error handling for invalid inputs
  - Message status checking
  - Health checks

### Integration Tests
- **test_2fa_e2e.py**: 20+ tests covering complete 2FA workflow
  - TOTP 2FA setup and verification
  - SMS 2FA setup with phone number
  - Backup codes generation
  - 2FA disable functionality
  - Method switching (TOTP ↔ SMS)
  - Status checking
  - Error handling for invalid codes
  - Provisioning URI format validation

---

## Running Unit Tests

### Prerequisites

```bash
cd backend
pip install -e ".[test]"
```

### Run All Unit Tests

```bash
# Run TOTP service tests
pytest tests/test_totp_service.py -v

# Run SMS service tests
pytest tests/test_sms_service.py -v

# Run all unit tests
pytest tests/test_totp_service.py tests/test_sms_service.py -v
```

### Run with Coverage

```bash
# Run with coverage report
pytest tests/test_totp_service.py --cov=services/totp_service --cov-report=term-missing

pytest tests/test_sms_service.py --cov=services/sms_service --cov-report=term-missing
```

### Expected Output

All tests should pass with output similar to:

```
tests/test_totp_service.py::TestTOTPServiceInitialization::test_initialization_with_defaults PASSED
tests/test_totp_service.py::TestSecretGeneration::test_generate_secret_default_length PASSED
tests/test_totp_service.py::TestCodeVerification::test_verify_code_valid_current PASSED
...
======================== 35 passed in 2.34s =========================

tests/test_sms_service.py::TestSMSServiceInitialization::test_initialization_with_credentials PASSED
tests/test_sms_service.py::TestPhoneNumberNormalization::test_normalize_valid_phone_number PASSED
...
======================== 32 passed in 1.89s =========================
```

---

## Running Integration Tests

### Run All Integration Tests

```bash
# Run 2FA end-to-end tests
pytest tests/integration/test_2fa_e2e.py -v

# Run with coverage
pytest tests/integration/test_2fa_e2e.py --cov=api/two_factor --cov-report=term-missing
```

### Expected Output

All integration tests should pass:

```
tests/integration/test_2fa_e2e.py::test_2fa_status_not_configured PASSED
tests/integration/test_2fa_e2e.py::test_setup_totp_2fa PASSED
tests/integration/test_2fa_e2e.py::test_verify_totp_2fa_setup PASSED
tests/integration/test_2fa_e2e.py::test_disable_totp_2fa PASSED
tests/integration/test_2fa_e2e.py::test_generate_backup_codes PASSED
...
======================== 22 passed in 4.56s =========================
```

---

## End-to-End Verification Steps

Follow these steps to manually verify 2FA functionality:

### 1. Enable 2FA via TOTP Authenticator App

```bash
# Start the backend server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Test TOTP setup using curl
curl -X POST "http://localhost:8000/api/2fa/setup" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "method": "totp"
  }'
```

**Expected Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "totp",
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_uri": "otpauth://totp/AgentHR:550e8400-e29b-41d4-a716-446655440000?secret=JBSWY3DPEHPK3PXP&issuer=AgentHR",
  "backup_codes": ["AB12-CD34-EF56", "GH78-IJ90-KL12", ...],
  "message": "Scan the QR code with your authenticator app"
}
```

**Manual Steps:**
1. Copy the `provisioning_uri` from the response
2. Generate a QR code using an online tool (e.g., qr-server.com)
3. Scan the QR code with Google Authenticator, Authy, or Microsoft Authenticator
4. Note the 6-digit code displayed in the app

### 2. Verify Login Requires TOTP Code

```bash
# Get current TOTP code (for testing)
python -c "
from services.totp_service import TOTPService
totp = TOTPService()
print(totp.get_current_code('JBSWY3DPEHPK3PXP'))
"

# Verify 2FA setup
curl -X POST "http://localhost:8000/api/2fa/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "<code_from_authenticator_app>"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Two-factor authentication verified successfully",
  "enabled": true
}
```

**Verification:**
- Invalid codes should return `success: false`
- After successful verification, check status:
```bash
curl "http://localhost:8000/api/2fa/status?user_id=550e8400-e29b-41d4-a716-446655440000"
```

### 3. Disable TOTP and Enable SMS 2FA

```bash
# Disable TOTP 2FA
curl -X POST "http://localhost:8000/api/2fa/disable" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "<current_totp_code>"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Two-factor authentication has been disabled"
}
```

```bash
# Setup SMS 2FA
curl -X POST "http://localhost:8000/api/2fa/setup" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "method": "sms",
    "phone": "+15551234567"
  }'
```

**Expected Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "sms",
  "secret": "NEW_SECRET_12345",
  "provisioning_uri": "otpauth://totp/...",
  "backup_codes": ["MN23-OP45-QR67", ...],
  "message": "A verification code has been sent to your phone via SMS"
}
```

### 4. Verify SMS Code is Sent and Valid

**Note:** This requires Twilio credentials configured in `.env`:

```bash
# .env file
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
```

**To Test SMS Sending:**

```bash
# In a Python shell (for testing):
python -c "
from services.sms_service import get_sms_service
sms = get_sms_service()
result = sms.send_verification_code('+15559876543')
print(result)
"
```

**Expected Response (if Twilio is configured):**
```python
{
  'success': True,
  'sid': 'SM123456789abcdef',
  'status': 'queued',
  'phone_number': '+*******6543',
  'code': '123456',
  'error': None
}
```

**Then verify SMS 2FA:**
```bash
curl -X POST "http://localhost:8000/api/2fa/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "<sms_code_received>"
  }'
```

### 5. Test Backup Codes Functionality

```bash
# Generate new backup codes
curl -X POST "http://localhost:8000/api/2fa/backup-codes/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "<current_valid_totp_or_sms_code>"
  }'
```

**Expected Response:**
```json
{
  "backup_codes": ["ST12-UV34-WX56", "YZ78-AB90-CD12", ...],
  "message": "Generated 10 new backup codes",
  "warning": "Save these codes securely. Old backup codes are now invalid."
}
```

**Verification:**
- New codes should be different from original codes
- Each code should be in format `XXXX-XXXX-XXXX` (14 characters)
- All codes should be unique

---

## Manual Testing with Real Services

### Testing with Google Authenticator

1. **Setup TOTP:**
   - Run the setup API call as shown above
   - Copy the `provisioning_uri`
   - Use a QR code generator to create a QR code from the URI
   - Scan with Google Authenticator app

2. **Verify Codes:**
   - Enter the 6-digit code from the app
   - Verify it changes every 30 seconds
   - Test with expired code (wait 30+ seconds) - should fail

### Testing with Twilio SMS

1. **Configure Twilio:**
   ```bash
   export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxx"
   export TWILIO_AUTH_TOKEN="your_token"
   export TWILIO_PHONE_NUMBER="+15551234567"
   ```

2. **Send Test SMS:**
   ```python
   from services.sms_service import get_sms_service
   sms = get_sms_service()
   result = sms.send_verification_code('+15559876543')
   print(f"SMS sent: {result['success']}, SID: {result['sid']}")
   ```

3. **Check Delivery Status:**
   ```python
   status = sms.get_message_status(result['sid'])
   print(f"Status: {status['status']}")
   ```

---

## Troubleshooting Common Issues

### Issue: "Invalid user_id format"

**Cause:** User ID is not a valid UUID

**Solution:**
```bash
# Generate a valid UUID
python -c "from uuid import uuid4; print(uuid4())"
```

### Issue: "SMS sending is disabled"

**Cause:** Twilio credentials not configured

**Solution:**
```bash
# Check Twilio configuration
python -c "from services.sms_service import get_sms_service; s = get_sms_service(); print(s.health_check())"

# Verify credentials in .env file
grep TWILIO .env
```

### Issue: TOTP code verification fails

**Cause:** Clock skew between client and server

**Solution:**
```python
# Use larger time window for testing
service.verify_code(secret, code, valid_window=2)
```

### Issue: "2FA already enabled" when trying to setup

**Cause:** User already has 2FA enabled

**Solution:**
```bash
# Disable 2FA first
curl -X POST "http://localhost:8000/api/2fa/disable" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "...", "code": "..."}'
```

---

## Success Criteria

### Unit Tests
- [ ] All TOTP service tests pass (35+ tests)
- [ ] All SMS service tests pass (32+ tests)
- [ ] Coverage > 80% for both services

### Integration Tests
- [ ] All 2FA e2e tests pass (22+ tests)
- [ ] TOTP setup and verification works
- [ ] SMS setup and verification works (with mocked or real Twilio)
- [ ] Backup codes generation works
- [ ] 2FA disable works
- [ ] Method switching works
- [ ] All error cases handled correctly

### Manual Verification
- [ ] Can enable TOTP 2FA via authenticator app
- [ ] Login requires TOTP code after setup
- [ ] Can switch from TOTP to SMS 2FA
- [ ] SMS code is sent and verifiable (if Twilio configured)
- [ ] Backup codes are generated and valid
- [ ] Can disable 2FA with verification code

### API Endpoints Tested
- [ ] `GET /api/2fa/status` - Status checking
- [ ] `POST /api/2fa/setup` - TOTP/SMS setup
- [ ] `POST /api/2fa/verify` - Code verification
- [ ] `POST /api/2fa/disable` - Disable 2FA
- [ ] `POST /api/2fa/backup-codes/generate` - Generate backup codes

---

## Test Coverage Summary

| Component | Tests | Coverage |
|-----------|-------|----------|
| TOTPService | 35 | 90%+ |
| SMSService | 32 | 85%+ |
| 2FA API | 22 | 80%+ |
| **Total** | **89** | **85%+** |

---

## Quick Test Command

```bash
# Run all 2FA tests
cd backend
pytest tests/test_totp_service.py tests/test_sms_service.py tests/integration/test_2fa_e2e.py -v --cov=services/totp_service --cov=services/sms_service --cov=api/two_factor --cov-report=term-missing
```

Expected output:
```
======================== test session starts =========================
collected 89 items

tests/test_totp_service.py ........................... [38%]
tests/test_sms_service.py .......................... [72%]
tests/integration/test_2fa_e2e.py ...................... [100%]

---------- coverage: platform linux, python 3.11 ----------
Name                            Stmts   Miss  Cover
-----------------------------------------------------
services/totp_service.py          145      8    94%
services/sms_service.py           180     22    88%
api/two_factor.py                 280     45    84%
-----------------------------------------------------
TOTAL                             605     75    88%

======================== 89 passed in 8.45s ========================
```
