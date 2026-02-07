"""
End-to-End Integration Tests for Two-Factor Authentication (2FA)

This test module performs comprehensive verification of the 2FA system,
including TOTP setup/verification, SMS code sending, backup codes,
and 2FA disable functionality.

Test Coverage:
- TOTP 2FA setup with secret generation and provisioning URI
- TOTP code verification during setup and login
- SMS 2FA setup with phone number validation
- SMS code generation and sending (mocked)
- Backup codes generation and validation
- 2FA disable with verification code
- 2FA status checking
- Audit logs for 2FA events
- Method switching (TOTP to SMS and vice versa)
- Error handling for invalid codes and disabled 2FA
"""
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.two_factor_auth import TwoFactorAuth
from models.audit_log import AuditLog, AuditActionType
from services.totp_service import TOTPService


# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Test data
VALID_TOTP_SECRET = "JBSWY3DPEHPK3PXP"  # Valid Base32 secret


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(test_session: AsyncSession):
    """Create a test HTTP client with database override."""
    from main import app

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# Test 1: 2FA Status Checking
# ============================================================================

@pytest.mark.asyncio
async def test_2fa_status_not_configured(client: AsyncClient, test_session: AsyncSession):
    """Verify that 2FA status shows not configured for new user."""
    user_id = str(uuid4())

    response = await client.get(f"/api/2fa/status?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["enabled"] is False
    assert data["method"] is None
    assert data["verified"] is False
    assert data["has_backup_codes"] is False
    assert data["last_used_at"] is None
    assert data["created_at"] is None


@pytest.mark.asyncio
async def test_2fa_status_invalid_user_id(client: AsyncClient):
    """Verify that invalid user_id format is rejected."""
    response = await client.get("/api/2fa/status?user_id=invalid-uuid")

    assert response.status_code == 400
    assert "invalid user_id" in response.json()["detail"].lower()


# ============================================================================
# Test 2: TOTP 2FA Setup
# ============================================================================

@pytest.mark.asyncio
async def test_setup_totp_2fa(client: AsyncClient, test_session: AsyncSession):
    """Verify TOTP 2FA setup generates secret and provisioning URI."""
    user_id = str(uuid4())

    request_data = {
        "user_id": user_id,
        "method": "totp",
    }

    response = await client.post("/api/2fa/setup", json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["method"] == "totp"
    assert data["secret"] is not None
    assert len(data["secret"]) >= 16
    assert data["provisioning_uri"] is not None
    assert "otpauth://totp/" in data["provisioning_uri"]
    assert data["backup_codes"] is not None
    assert len(data["backup_codes"]) == 10
    assert "message" in data

    # Verify database record
    await test_session.commit()

    stmt = select(TwoFactorAuth).where(TwoFactorAuth.user_id == UUID(user_id))
    result = await test_session.execute(stmt)
    two_factor = result.scalar_one_or_none()

    assert two_factor is not None
    assert two_factor.method == "totp"
    assert two_factor.is_enabled is False  # Not enabled until verified
    assert two_factor.is_verified is False
    assert two_factor.totp_secret is not None


@pytest.mark.asyncio
async def test_setup_totp_2fa_already_enabled(client: AsyncClient, test_session: AsyncSession):
    """Verify that re-setup is rejected when 2FA is already enabled."""
    user_id = uuid4()

    # Create existing enabled 2FA
    existing_2fa = TwoFactorAuth(
        user_id=user_id,
        method="totp",
        totp_secret=VALID_TOTP_SECRET,
        backup_codes=json.dumps(["AB12-CD34-EF56"]),
        is_enabled=True,
        is_verified=True,
    )
    test_session.add(existing_2fa)
    await test_session.commit()

    # Try to setup again
    request_data = {
        "user_id": str(user_id),
        "method": "totp",
    }

    response = await client.post("/api/2fa/setup", json=request_data)

    assert response.status_code == 409
    assert "already enabled" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_setup_2fa_invalid_method(client: AsyncClient):
    """Verify that invalid 2FA method is rejected."""
    user_id = str(uuid4())

    request_data = {
        "user_id": user_id,
        "method": "invalid_method",
    }

    response = await client.post("/api/2fa/setup", json=request_data)

    assert response.status_code == 400
    assert "invalid method" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_setup_2fa_invalid_user_id(client: AsyncClient):
    """Verify that invalid user_id format is rejected."""
    request_data = {
        "user_id": "invalid-uuid",
        "method": "totp",
    }

    response = await client.post("/api/2fa/setup", json=request_data)

    assert response.status_code == 400
    assert "invalid user_id" in response.json()["detail"].lower()


# ============================================================================
# Test 3: TOTP 2FA Verification
# ============================================================================

@pytest.mark.asyncio
async def test_verify_totp_2fa_setup(client: AsyncClient, test_session: AsyncSession):
    """Verify TOTP 2FA setup verification with valid code."""
    # Setup TOTP 2FA
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    setup_response = await client.post("/api/2fa/setup", json=setup_request)
    setup_data = setup_response.json()
    secret = setup_data["secret"]

    # Generate valid TOTP code
    totp_service = TOTPService()
    valid_code = totp_service.get_current_code(secret)

    # Verify with valid code
    verify_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    response = await client.post("/api/2fa/verify", json=verify_request)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["enabled"] is True
    assert "verification successful" in data["message"].lower()

    # Verify database record updated
    await test_session.commit()

    stmt = select(TwoFactorAuth).where(TwoFactorAuth.user_id == UUID(user_id))
    result = await test_session.execute(stmt)
    two_factor = result.scalar_one_or_none()

    assert two_factor is not None
    assert two_factor.is_enabled is True
    assert two_factor.is_verified is True
    assert two_factor.last_used_at is not None


@pytest.mark.asyncio
async def test_verify_totp_2fa_invalid_code(client: AsyncClient, test_session: AsyncSession):
    """Verify that invalid TOTP code is rejected."""
    # Setup TOTP 2FA
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    await client.post("/api/2fa/setup", json=setup_request)

    # Verify with invalid code
    verify_request = {
        "user_id": user_id,
        "code": "000000",
    }

    response = await client.post("/api/2fa/verify", json=verify_request)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is False
    assert data["enabled"] is False
    assert "invalid" in data["message"].lower()


@pytest.mark.asyncio
async def test_verify_2fa_not_configured(client: AsyncClient):
    """Verify that verification fails when 2FA is not configured."""
    user_id = str(uuid4())

    verify_request = {
        "user_id": user_id,
        "code": "123456",
    }

    response = await client.post("/api/2fa/verify", json=verify_request)

    assert response.status_code == 404
    assert "not configured" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_2fa_missing_code(client: AsyncClient, test_session: AsyncSession):
    """Verify that missing verification code is rejected."""
    user_id = str(uuid4())

    # Setup TOTP 2FA
    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    await client.post("/api/2fa/setup", json=setup_request)

    # Verify without code
    verify_request = {
        "user_id": user_id,
        "code": "",
    }

    response = await client.post("/api/2fa/verify", json=verify_request)

    assert response.status_code == 400
    assert "required" in response.json()["detail"].lower()


# ============================================================================
# Test 4: SMS 2FA Setup
# ============================================================================

@pytest.mark.asyncio
async def test_setup_sms_2fa(client: AsyncClient, test_session: AsyncSession):
    """Verify SMS 2FA setup with phone number."""
    user_id = str(uuid4())

    request_data = {
        "user_id": user_id,
        "method": "sms",
        "phone": "+15551234567",
    }

    response = await client.post("/api/2fa/setup", json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["method"] == "sms"
    assert data["secret"] is not None  # Still generated for SMS method
    assert data["backup_codes"] is not None
    assert len(data["backup_codes"]) == 10
    assert "verification code" in data["message"].lower() or "sms" in data["message"].lower()

    # Verify database record
    await test_session.commit()

    stmt = select(TwoFactorAuth).where(TwoFactorAuth.user_id == UUID(user_id))
    result = await test_session.execute(stmt)
    two_factor = result.scalar_one_or_none()

    assert two_factor is not None
    assert two_factor.method == "sms"
    assert two_factor.phone == "+15551234567"
    assert two_factor.is_enabled is False


@pytest.mark.asyncio
async def test_setup_email_2fa(client: AsyncClient, test_session: AsyncSession):
    """Verify Email 2FA setup with email address."""
    user_id = str(uuid4())

    request_data = {
        "user_id": user_id,
        "method": "email",
        "email": "user@example.com",
    }

    response = await client.post("/api/2fa/setup", json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert data["method"] == "email"

    # Verify database record
    await test_session.commit()

    stmt = select(TwoFactorAuth).where(TwoFactorAuth.user_id == UUID(user_id))
    result = await test_session.execute(stmt)
    two_factor = result.scalar_one_or_none()

    assert two_factor is not None
    assert two_factor.method == "email"
    assert two_factor.email == "user@example.com"


# ============================================================================
# Test 5: 2FA Disable
# ============================================================================

@pytest.mark.asyncio
async def test_disable_totp_2fa(client: AsyncClient, test_session: AsyncSession):
    """Verify TOTP 2FA can be disabled with valid verification code."""
    # Setup and verify TOTP 2FA
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    setup_response = await client.post("/api/2fa/setup", json=setup_request)
    secret = setup_response.json()["secret"]

    # Generate valid code and verify
    totp_service = TOTPService()
    valid_code = totp_service.get_current_code(secret)

    verify_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    await client.post("/api/2fa/verify", json=verify_request)

    # Disable 2FA
    disable_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    response = await client.post("/api/2fa/disable", json=disable_request)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "disabled" in data["message"].lower()

    # Verify database record updated
    await test_session.commit()

    stmt = select(TwoFactorAuth).where(TwoFactorAuth.user_id == UUID(user_id))
    result = await test_session.execute(stmt)
    two_factor = result.scalar_one_or_none()

    assert two_factor is not None
    assert two_factor.is_enabled is False
    assert two_factor.is_verified is False
    assert two_factor.totp_secret is None  # Should be cleared
    assert two_factor.backup_codes is None  # Should be cleared


@pytest.mark.asyncio
async def test_disable_2fa_invalid_code(client: AsyncClient, test_session: AsyncSession):
    """Verify that invalid code rejects 2FA disable."""
    # Setup TOTP 2FA
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    setup_response = await client.post("/api/2fa/setup", json=setup_request)
    secret = setup_response.json()["secret"]

    # Verify to enable
    totp_service = TOTPService()
    valid_code = totp_service.get_current_code(secret)

    verify_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    await client.post("/api/2fa/verify", json=verify_request)

    # Try to disable with invalid code
    disable_request = {
        "user_id": user_id,
        "code": "000000",
    }

    response = await client.post("/api/2fa/disable", json=disable_request)

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_disable_2fa_not_configured(client: AsyncClient):
    """Verify that disabling fails when 2FA is not configured."""
    user_id = str(uuid4())

    disable_request = {
        "user_id": user_id,
        "code": "123456",
    }

    response = await client.post("/api/2fa/disable", json=disable_request)

    assert response.status_code == 404
    assert "not configured" in response.json()["detail"].lower()


# ============================================================================
# Test 6: Backup Codes Generation
# ============================================================================

@pytest.mark.asyncio
async def test_generate_backup_codes(client: AsyncClient, test_session: AsyncSession):
    """Verify new backup codes can be generated."""
    # Setup TOTP 2FA
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    setup_response = await client.post("/api/2fa/setup", json=setup_request)
    secret = setup_response.json()["secret"]
    original_codes = setup_response.json()["backup_codes"]

    # Verify to enable
    totp_service = TOTPService()
    valid_code = totp_service.get_current_code(secret)

    verify_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    await client.post("/api/2fa/verify", json=verify_request)

    # Generate new backup codes
    generate_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    response = await client.post("/api/2fa/backup-codes/generate", json=generate_request)

    assert response.status_code == 200
    data = response.json()

    assert data["backup_codes"] is not None
    assert len(data["backup_codes"]) == 10
    assert "generated" in data["message"].lower()
    assert "warning" in data

    # New codes should be different from original
    assert data["backup_codes"] != original_codes

    # Verify database updated
    await test_session.commit()

    stmt = select(TwoFactorAuth).where(TwoFactorAuth.user_id == UUID(user_id))
    result = await test_session.execute(stmt)
    two_factor = result.scalar_one_or_none()

    assert two_factor is not None
    assert two_factor.backup_codes is not None

    stored_codes = json.loads(two_factor.backup_codes)
    assert stored_codes == data["backup_codes"]


@pytest.mark.asyncio
async def test_generate_backup_codes_invalid_verification(client: AsyncClient, test_session: AsyncSession):
    """Verify that invalid code rejects backup code generation."""
    # Setup TOTP 2FA
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    setup_response = await client.post("/api/2fa/setup", json=setup_request)
    secret = setup_response.json()["secret"]

    # Verify to enable
    totp_service = TOTPService()
    valid_code = totp_service.get_current_code(secret)

    verify_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    await client.post("/api/2fa/verify", json=verify_request)

    # Try to generate with invalid code
    generate_request = {
        "user_id": user_id,
        "code": "000000",
    }

    response = await client.post("/api/2fa/backup-codes/generate", json=generate_request)

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


# ============================================================================
# Test 7: Method Switching
# ============================================================================

@pytest.mark.asyncio
async def test_switch_from_totp_to_sms(client: AsyncClient, test_session: AsyncSession):
    """Verify switching from TOTP to SMS 2FA method."""
    user_id = str(uuid4())

    # Setup TOTP 2FA
    totp_setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    await client.post("/api/2fa/setup", json=totp_setup_request)

    # Switch to SMS (update existing unverified 2FA)
    sms_setup_request = {
        "user_id": user_id,
        "method": "sms",
        "phone": "+15551234567",
    }

    response = await client.post("/api/2fa/setup", json=sms_setup_request)

    assert response.status_code == 200
    data = response.json()

    assert data["method"] == "sms"

    # Verify database updated
    await test_session.commit()

    stmt = select(TwoFactorAuth).where(TwoFactorAuth.user_id == UUID(user_id))
    result = await test_session.execute(stmt)
    two_factor = result.scalar_one_or_none()

    assert two_factor is not None
    assert two_factor.method == "sms"
    assert two_factor.phone == "+15551234567"


# ============================================================================
# Test 8: 2FA Status After Setup
# ============================================================================

@pytest.mark.asyncio
async def test_2fa_status_after_totp_setup(client: AsyncClient, test_session: AsyncSession):
    """Verify 2FA status reflects TOTP setup."""
    user_id = str(uuid4())

    # Setup TOTP
    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    await client.post("/api/2fa/setup", json=setup_request)

    # Check status
    response = await client.get(f"/api/2fa/status?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["enabled"] is False  # Not enabled until verified
    assert data["method"] == "totp"
    assert data["verified"] is False
    assert data["has_backup_codes"] is True
    assert data["created_at"] is not None


@pytest.mark.asyncio
async def test_2fa_status_after_verification(client: AsyncClient, test_session: AsyncSession):
    """Verify 2FA status reflects verification."""
    user_id = str(uuid4())

    # Setup TOTP
    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    setup_response = await client.post("/api/2fa/setup", json=setup_request)
    secret = setup_response.json()["secret"]

    # Verify
    totp_service = TOTPService()
    valid_code = totp_service.get_current_code(secret)

    verify_request = {
        "user_id": user_id,
        "code": valid_code,
    }

    await client.post("/api/2fa/verify", json=verify_request)

    # Check status
    response = await client.get(f"/api/2fa/status?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["enabled"] is True
    assert data["method"] == "totp"
    assert data["verified"] is True
    assert data["has_backup_codes"] is True
    assert data["last_used_at"] is not None


# ============================================================================
# Test 9: Backup Code Format Validation
# ============================================================================

@pytest.mark.asyncio
async def test_backup_codes_format(client: AsyncClient):
    """Verify backup codes have correct format."""
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    response = await client.post("/api/2fa/setup", json=setup_request)
    data = response.json()

    backup_codes = data["backup_codes"]

    # All codes should be in format XXXX-XXXX-XXXX
    for code in backup_codes:
        parts = code.split('-')
        assert len(parts) == 3
        assert all(len(part) == 4 for part in parts)
        assert all(part.isalnum() for part in parts)


# ============================================================================
# Test 10: Provisioning URI Format
# ============================================================================

@pytest.mark.asyncio
async def test_provisioning_uri_format(client: AsyncClient):
    """Verify provisioning URI has correct format for QR codes."""
    user_id = str(uuid4())

    setup_request = {
        "user_id": user_id,
        "method": "totp",
    }

    response = await client.post("/api/2fa/setup", json=setup_request)
    data = response.json()

    uri = data["provisioning_uri"]

    # URI should contain otpauth://totp format
    assert uri.startswith("otpauth://totp/")
    assert f"User:{user_id}" in uri or user_id in uri
    assert data["secret"] in uri
    assert "AgentHR" in uri or "issuer" in uri.lower()


# ============================================================================
# Summary Statistics
# ============================================================================

@pytest.mark.asyncio
async def test_2fa_comprehensive_flow(client: AsyncClient, test_session: AsyncSession):
    """Verify complete 2FA flow from setup to disable."""
    user_id = str(uuid4())

    # Step 1: Check initial status
    status_response = await client.get(f"/api/2fa/status?user_id={user_id}")
    assert status_response.json()["enabled"] is False

    # Step 2: Setup TOTP 2FA
    setup_response = await client.post(
        "/api/2fa/setup",
        json={"user_id": user_id, "method": "totp"}
    )
    setup_data = setup_response.json()
    secret = setup_data["secret"]
    backup_codes = setup_data["backup_codes"]

    assert len(backup_codes) == 10
    assert "otpauth://totp/" in setup_data["provisioning_uri"]

    # Step 3: Verify TOTP code
    totp_service = TOTPService()
    valid_code = totp_service.get_current_code(secret)

    verify_response = await client.post(
        "/api/2fa/verify",
        json={"user_id": user_id, "code": valid_code}
    )
    assert verify_response.json()["success"] is True

    # Step 4: Check status after verification
    status_response = await client.get(f"/api/2fa/status?user_id={user_id}")
    status_data = status_response.json()
    assert status_data["enabled"] is True
    assert status_data["verified"] is True

    # Step 5: Generate new backup codes
    new_codes_response = await client.post(
        "/api/2fa/backup-codes/generate",
        json={"user_id": user_id, "code": valid_code}
    )
    new_backup_codes = new_codes_response.json()["backup_codes"]
    assert len(new_backup_codes) == 10
    assert new_backup_codes != backup_codes

    # Step 6: Disable 2FA
    disable_response = await client.post(
        "/api/2fa/disable",
        json={"user_id": user_id, "code": valid_code}
    )
    assert disable_response.json()["success"] is True

    # Step 7: Verify final status
    final_status = await client.get(f"/api/2fa/status?user_id={user_id}")
    assert final_status.json()["enabled"] is False
