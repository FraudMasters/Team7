"""
End-to-end integration test for login protection and account lockout.

This test verifies the complete login protection flow:
1. Track successful login attempts
2. Track failed login attempts
3. Account lockout after multiple failed attempts
4. Lockout expiration and reset
5. Successful login resets failed attempts counter
6. IP-based tracking of login attempts
"""
import pytest
import time
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.user import User
from models.login_attempt import LoginAttempt
from services.auth_service import AuthService


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_login_protection.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(client: AsyncClient):
    """Create a test user for login protection tests."""
    user_data = {
        "email": "loginprotection@example.com",
        "password": "TestPass123!",
        "full_name": "Login Protection Test User"
    }

    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest.fixture
def auth_service():
    """Create auth service instance for testing."""
    return AuthService()


@pytest.mark.asyncio
async def test_successful_login_tracking(
    client: AsyncClient,
    test_db: AsyncSession,
    test_user: dict
):
    """
    Test that successful login attempts are tracked correctly.

    Verification steps:
    1. Login with valid credentials
    2. Verify LoginAttempt record created
    3. Verify success flag is True
    4. Verify user_id is set
    5. Verify IP and user agent are captured
    """
    print("\n=== Testing Successful Login Tracking ===\n")

    # Step 1: Login with valid credentials
    print("Step 1: Logging in with valid credentials...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200, f"Login should succeed: {response.text}"
    print("✓ Login successful")

    # Step 2: Verify LoginAttempt record was created
    print("\nStep 2: Verifying login attempt was tracked...")
    result = await test_db.execute(
        select(LoginAttempt)
        .where(LoginAttempt.email == test_user["email"])
        .order_by(LoginAttempt.created_at.desc())
    )
    attempts = result.scalars().all()

    assert len(attempts) > 0, "At least one login attempt should be tracked"
    latest_attempt = attempts[0]
    print(f"✓ Found {len(attempts)} login attempt(s)")

    # Step 3: Verify success flag
    assert latest_attempt.success is True, "Login attempt should be marked as successful"
    print("✓ Login attempt marked as successful")

    # Step 4: Verify user_id is set
    assert latest_attempt.user_id is not None, "User ID should be set for successful login"
    print(f"✓ User ID tracked: {latest_attempt.user_id}")

    # Step 5: Verify IP address is captured
    assert latest_attempt.ip_address is not None, "IP address should be captured"
    assert len(latest_attempt.ip_address) > 0, "IP address should not be empty"
    print(f"✓ IP address tracked: {latest_attempt.ip_address}")

    # Step 6: Verify failure_reason is None for successful login
    assert latest_attempt.failure_reason is None, "Failure reason should be None for successful login"
    print("✓ No failure reason for successful login")

    print("\n=== Successful Login Tracking Test PASSED ===\n")


@pytest.mark.asyncio
async def test_failed_login_tracking(client: AsyncClient, test_db: AsyncSession, test_user: dict):
    """
    Test that failed login attempts are tracked correctly.

    Verification steps:
    1. Login with invalid password
    2. Verify LoginAttempt record created
    3. Verify success flag is False
    4. Verify failure_reason is set
    """
    print("\n=== Testing Failed Login Tracking ===\n")

    # Step 1: Login with invalid password
    print("Step 1: Attempting login with invalid password...")
    login_data = {
        "email": test_user["email"],
        "password": "WrongPassword123!"
    }

    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401, f"Login should fail with 401: {response.text}"
    print("✓ Login correctly rejected")

    # Step 2: Verify LoginAttempt record was created
    print("\nStep 2: Verifying failed attempt was tracked...")
    result = await test_db.execute(
        select(LoginAttempt)
        .where(
            LoginAttempt.email == test_user["email"],
            LoginAttempt.success == False
        )
        .order_by(LoginAttempt.created_at.desc())
    )
    attempts = result.scalars().all()

    assert len(attempts) > 0, "Failed login attempt should be tracked"
    latest_attempt = attempts[0]
    print(f"✓ Failed attempt tracked (ID: {latest_attempt.id})")

    # Step 3: Verify success flag is False
    assert latest_attempt.success is False, "Login attempt should be marked as failed"
    print("✓ Login attempt marked as failed")

    # Step 4: Verify failure_reason is set
    assert latest_attempt.failure_reason is not None, "Failure reason should be set"
    assert len(latest_attempt.failure_reason) > 0, "Failure reason should not be empty"
    print(f"✓ Failure reason tracked: {latest_attempt.failure_reason}")

    print("\n=== Failed Login Tracking Test PASSED ===\n")


@pytest.mark.asyncio
async def test_account_lockout_after_max_attempts(
    client: AsyncClient,
    test_db: AsyncSession,
    auth_service: AuthService
):
    """
    Test account lockout after exceeding MAX_LOGIN_ATTEMPTS.

    Verification steps:
    1. Create a test user
    2. Make MAX_LOGIN_ATTEMPTS failed login attempts
    3. Verify account is locked
    4. Verify lockout message contains time remaining
    5. Verify all failed attempts are tracked in database
    """
    print("\n=== Testing Account Lockout After Max Attempts ===\n")

    # Step 1: Create a test user
    print("Step 1: Creating test user for lockout test...")
    user_data = {
        "email": "lockout@example.com",
        "password": "TestPass123!",
        "full_name": "Lockout Test User"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    print(f"✓ User created: {user_data['email']}")

    # Step 2: Make MAX_LOGIN_ATTEMPTS failed attempts
    max_attempts = auth_service.MAX_LOGIN_ATTEMPTS
    print(f"\nStep 2: Making {max_attempts} failed login attempts...")

    for i in range(max_attempts):
        login_data = {
            "email": user_data["email"],
            "password": "WrongPassword123!"
        }
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401, f"Attempt {i+1} should be rejected with 401"
        print(f"  Attempt {i+1}/{max_attempts}: Failed (as expected)")

    print(f"✓ Made {max_attempts} failed login attempts")

    # Step 3: Verify account is now locked
    print("\nStep 3: Verifying account is locked...")
    is_locked, locked_until = await auth_service.is_account_locked(test_db, user_data["email"])
    assert is_locked is True, "Account should be locked after max attempts"
    assert locked_until is not None, "Locked until timestamp should be set"
    print(f"✓ Account is locked until {locked_until}")

    # Step 4: Attempt login and verify lockout message
    print("\nStep 4: Attempting login on locked account...")
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]  # Even with correct password
    }
    response = await client.post("/api/auth/login", json=login_data)

    # Should be rejected with 403 or 429 (depending on implementation)
    assert response.status_code in [401, 403, 429], \
        f"Locked account should be rejected: {response.status_code}"

    data = response.json()
    assert "detail" in data or "message" in data, "Error message should be present"
    error_msg = data.get("detail") or data.get("message", "")
    assert "locked" in error_msg.lower() or "too many" in error_msg.lower(), \
        "Error should mention account lockout"
    print(f"✓ Lockout message: {error_msg}")

    # Step 5: Verify all failed attempts are in database
    print("\nStep 5: Verifying failed attempts in database...")
    result = await test_db.execute(
        select(LoginAttempt)
        .where(
            LoginAttempt.email == user_data["email"],
            LoginAttempt.success == False
        )
        .order_by(LoginAttempt.created_at.desc())
    )
    failed_attempts = result.scalars().all()

    assert len(failed_attempts) >= max_attempts, \
        f"Should have at least {max_attempts} failed attempts tracked"
    print(f"✓ Found {len(failed_attempts)} failed attempts in database")

    print("\n=== Account Lockout Test PASSED ===\n")


@pytest.mark.asyncio
async def test_successful_login_resets_failed_attempts(
    client: AsyncClient,
    test_db: AsyncSession,
    auth_service: AuthService
):
    """
    Test that successful login resets the failed attempts counter.

    Verification steps:
    1. Create test user
    2. Make some failed attempts (less than max)
    3. Make successful login
    4. Verify account is not locked
    5. Make more failed attempts
    6. Verify they start counting from zero
    """
    print("\n=== Testing Successful Login Resets Failed Attempts ===\n")

    # Step 1: Create test user
    print("Step 1: Creating test user...")
    user_data = {
        "email": "reset@example.com",
        "password": "TestPass123!",
        "full_name": "Reset Test User"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    print(f"✓ User created: {user_data['email']}")

    # Step 2: Make some failed attempts
    failed_attempts_count = 3
    print(f"\nStep 2: Making {failed_attempts_count} failed attempts...")
    for i in range(failed_attempts_count):
        response = await client.post("/api/auth/login", json={
            "email": user_data["email"],
            "password": "WrongPassword!"
        })
        assert response.status_code == 401
        print(f"  Attempt {i+1}: Failed")

    print(f"✓ Made {failed_attempts_count} failed attempts")

    # Step 3: Make successful login
    print("\nStep 3: Making successful login...")
    response = await client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert response.status_code == 200, "Login should succeed"
    print("✓ Successful login")

    # Step 4: Verify account is not locked
    print("\nStep 4: Verifying account is not locked...")
    is_locked, _ = await auth_service.is_account_locked(test_db, user_data["email"])
    assert is_locked is False, "Account should not be locked after successful login"
    print("✓ Account is not locked")

    # Step 5: Make MAX_LOGIN_ATTEMPTS more failed attempts
    max_attempts = auth_service.MAX_LOGIN_ATTEMPTS
    print(f"\nStep 5: Making {max_attempts} more failed attempts...")
    for i in range(max_attempts):
        response = await client.post("/api/auth/login", json={
            "email": user_data["email"],
            "password": "WrongPassword!"
        })
        assert response.status_code == 401
        print(f"  Attempt {i+1}: Failed")

    # Step 6: Verify account is now locked (counter was reset)
    print("\nStep 6: Verifying account is locked after new failed attempts...")
    is_locked, locked_until = await auth_service.is_account_locked(test_db, user_data["email"])
    assert is_locked is True, "Account should be locked after new max attempts"
    print(f"✓ Account locked after counter reset: {locked_until}")

    print("\n=== Successful Login Reset Test PASSED ===\n")


@pytest.mark.asyncio
async def test_nonexistent_user_login_tracking(
    client: AsyncClient,
    test_db: AsyncSession
):
    """
    Test that login attempts for non-existent users are tracked.

    Verification steps:
    1. Attempt login with non-existent email
    2. Verify attempt is tracked
    3. Verify user_id is None
    4. Verify failure_reason indicates user not found
    """
    print("\n=== Testing Non-Existent User Login Tracking ===\n")

    # Step 1: Attempt login with non-existent email
    print("Step 1: Attempting login with non-existent user...")
    nonexistent_email = "nonexistent@example.com"
    response = await client.post("/api/auth/login", json={
        "email": nonexistent_email,
        "password": "SomePassword123!"
    })
    assert response.status_code == 401, "Login should fail"
    print("✓ Login correctly rejected")

    # Step 2: Verify attempt is tracked
    print("\nStep 2: Verifying attempt was tracked...")
    result = await test_db.execute(
        select(LoginAttempt)
        .where(LoginAttempt.email == nonexistent_email)
        .order_by(LoginAttempt.created_at.desc())
    )
    attempts = result.scalars().all()

    assert len(attempts) > 0, "Login attempt should be tracked even for non-existent user"
    latest_attempt = attempts[0]
    print(f"✓ Attempt tracked (ID: {latest_attempt.id})")

    # Step 3: Verify user_id is None
    assert latest_attempt.user_id is None, \
        "User ID should be None for non-existent user"
    print("✓ User ID is None (user doesn't exist)")

    # Step 4: Verify failure reason
    assert latest_attempt.success is False, "Attempt should be marked as failed"
    assert latest_attempt.failure_reason is not None, "Failure reason should be set"
    print(f"✓ Failure reason: {latest_attempt.failure_reason}")

    print("\n=== Non-Existent User Tracking Test PASSED ===\n")


@pytest.mark.asyncio
async def test_ip_address_tracking(client: AsyncClient, test_db: AsyncSession, test_user: dict):
    """
    Test that IP addresses are correctly tracked in login attempts.

    Verification steps:
    1. Make login attempt
    2. Verify IP address is captured
    3. Verify IP address format
    """
    print("\n=== Testing IP Address Tracking ===\n")

    # Step 1: Make login attempt
    print("Step 1: Making login attempt...")
    response = await client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    print("✓ Login successful")

    # Step 2: Verify IP address is captured
    print("\nStep 2: Verifying IP address tracking...")
    result = await test_db.execute(
        select(LoginAttempt)
        .where(LoginAttempt.email == test_user["email"])
        .order_by(LoginAttempt.created_at.desc())
    )
    latest_attempt = result.scalar_one()

    assert latest_attempt.ip_address is not None, "IP address should be captured"
    assert len(latest_attempt.ip_address) > 0, "IP address should not be empty"
    print(f"✓ IP address captured: {latest_attempt.ip_address}")

    # Step 3: Verify IP address format (basic validation)
    ip = latest_attempt.ip_address
    # Should be a valid IP (IPv4 or IPv6) or localhost
    assert any([
        ip == "127.0.0.1",
        ip == "::1",
        ip == "testclient",
        "." in ip,  # IPv4
        ":" in ip,  # IPv6
    ]), f"IP address should be valid format: {ip}"
    print(f"✓ IP address format valid: {ip}")

    print("\n=== IP Address Tracking Test PASSED ===\n")


@pytest.mark.asyncio
async def test_lockout_duration_and_expiration(
    client: AsyncClient,
    test_db: AsyncSession,
    auth_service: AuthService
):
    """
    Test that account lockout expires after ACCOUNT_LOCKOUT_DURATION_MINUTES.

    Note: This test is simplified for integration testing and doesn't actually wait
    for the full lockout duration. It verifies the lockout timestamp calculation.

    Verification steps:
    1. Create user and trigger lockout
    2. Verify lockout timestamp is in the future
    3. Verify lockout duration is approximately correct
    """
    print("\n=== Testing Lockout Duration ===\n")

    # Step 1: Create user and trigger lockout
    print("Step 1: Creating user and triggering lockout...")
    user_data = {
        "email": "lockoutduration@example.com",
        "password": "TestPass123!",
        "full_name": "Lockout Duration Test"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201

    # Make MAX_LOGIN_ATTEMPTS failed attempts
    for i in range(auth_service.MAX_LOGIN_ATTEMPTS):
        await client.post("/api/auth/login", json={
            "email": user_data["email"],
            "password": "WrongPassword!"
        })
    print("✓ Account locked")

    # Step 2: Verify lockout timestamp
    print("\nStep 2: Verifying lockout timestamp...")
    is_locked, locked_until = await auth_service.is_account_locked(
        test_db, user_data["email"]
    )
    assert is_locked is True
    assert locked_until is not None
    print(f"✓ Locked until: {locked_until}")

    # Step 3: Verify lockout duration
    print("\nStep 3: Verifying lockout duration...")
    now = datetime.utcnow()
    time_until_unlock = (locked_until - now).total_seconds()
    expected_duration = auth_service.ACCOUNT_LOCKOUT_DURATION_MINUTES * 60

    # Allow some tolerance (within 60 seconds)
    assert abs(time_until_unlock - expected_duration) < 60, \
        f"Lockout duration should be ~{expected_duration}s, got {time_until_unlock}s"
    print(f"✓ Lockout duration: {time_until_unlock:.0f}s (~{time_until_unlock/60:.1f} minutes)")

    print("\n=== Lockout Duration Test PASSED ===\n")


@pytest.mark.asyncio
async def test_inactive_account_login_protection(
    client: AsyncClient,
    test_db: AsyncSession
):
    """
    Test that inactive accounts cannot login even with correct credentials.

    Verification steps:
    1. Create user and deactivate
    2. Attempt login with correct password
    3. Verify login is rejected with 403
    4. Verify attempt is tracked
    """
    print("\n=== Testing Inactive Account Protection ===\n")

    # Step 1: Create and deactivate user
    print("Step 1: Creating and deactivating user...")
    user_data = {
        "email": "inactive@example.com",
        "password": "TestPass123!",
        "full_name": "Inactive User"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201

    # Deactivate user
    result = await test_db.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_active = False
    await test_db.commit()
    print(f"✓ User deactivated: {user.email}")

    # Step 2: Attempt login
    print("\nStep 2: Attempting login with inactive account...")
    response = await client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert response.status_code == 403, "Inactive account should be rejected with 403"
    print("✓ Login correctly rejected")

    # Step 3: Verify error message
    data = response.json()
    assert "detail" in data or "message" in data
    error_msg = data.get("detail") or data.get("message", "")
    assert "inactive" in error_msg.lower() or "deactivated" in error_msg.lower(), \
        "Error should mention inactive account"
    print(f"✓ Error message: {error_msg}")

    # Step 4: Verify attempt is tracked
    print("\nStep 3: Verifying attempt was tracked...")
    result = await test_db.execute(
        select(LoginAttempt)
        .where(LoginAttempt.email == user_data["email"])
        .order_by(LoginAttempt.created_at.desc())
    )
    attempts = result.scalars().all()

    # Should have the failed login attempt (but not the initial successful registration login)
    failed_attempts = [a for a in attempts if not a.success]
    assert len(failed_attempts) > 0, "Failed attempt should be tracked"
    print(f"✓ Attempt tracked with failure reason: {failed_attempts[0].failure_reason}")

    print("\n=== Inactive Account Protection Test PASSED ===\n")


if __name__ == "__main__":
    print("Running login protection tests...")
    pytest.main([__file__, "-v", "-s"])
