"""
End-to-end integration test for user registration flow.

This test verifies the complete registration flow:
1. User submits registration data via API
2. User is created in database with hashed password
3. Default role (viewer) is assigned
4. Response contains correct user information
5. Duplicate email is rejected
"""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.user import User
from models.role import Role, UserRole


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_registration.db"


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


@pytest.mark.asyncio
async def test_complete_registration_flow(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end test: Complete user registration flow from API to database.

    Verification steps:
    1. Submit registration request with valid data
    2. Verify response contains user information
    3. Verify user created in database
    4. Verify password is hashed (not stored in plaintext)
    5. Verify default 'viewer' role is assigned
    6. Verify user is active but not verified
    7. Attempt duplicate registration (should fail)
    8. Verify error message for duplicate email
    """
    print("\n=== Starting Registration Flow E2E Test ===\n")

    # Step 1: Submit registration request
    print("Step 1: Submitting registration request...")
    registration_data = {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }

    response = await client.post("/api/auth/register", json=registration_data)
    print(f"Response status: {response.status_code}")

    # Step 2: Verify response
    print("\nStep 2: Verifying registration response...")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()
    print(f"Response data: {data}")

    assert "id" in data, "Response should contain user ID"
    assert data["email"] == registration_data["email"], "Email should match"
    assert data["full_name"] == registration_data["full_name"], "Full name should match"
    assert data["is_active"] is True, "User should be active by default"
    assert data["is_verified"] is False, "User should not be verified by default"
    assert data["is_superuser"] is False, "User should not be superuser by default"
    assert "message" in data, "Response should contain success message"
    print("✓ Registration response valid")

    # Step 3: Verify user created in database
    print("\nStep 3: Verifying user created in database...")
    result = await test_db.execute(
        select(User).where(User.email == registration_data["email"])
    )
    user = result.scalar_one_or_none()

    assert user is not None, "User should be created in database"
    assert user.email == registration_data["email"], "Email in database should match"
    assert user.full_name == registration_data["full_name"], "Full name in database should match"
    assert user.is_active is True, "User should be active in database"
    assert user.is_verified is False, "User should not be verified in database"
    assert user.is_superuser is False, "User should not be superuser in database"
    print(f"✓ User found in database with ID: {user.id}")

    # Step 4: Verify password is hashed
    print("\nStep 4: Verifying password is hashed...")
    assert user.password_hash is not None, "Password hash should exist"
    assert user.password_hash != registration_data["password"], "Password should NOT be stored in plaintext"
    assert user.password_hash.startswith("$2b$"), "Password should be bcrypt hashed (starts with $2b$)"
    assert len(user.password_hash) == 60, "Bcrypt hash should be 60 characters"
    print(f"✓ Password properly hashed: {user.password_hash[:10]}...")

    # Step 5: Verify default role assigned
    print("\nStep 5: Verifying default role assigned...")
    result = await test_db.execute(
        select(Role).where(Role.user_id == user.id)
    )
    roles = result.scalars().all()

    assert len(roles) == 1, "User should have exactly 1 role"
    assert roles[0].role == UserRole.VIEWER, "Default role should be VIEWER"
    print(f"✓ Default role assigned: {roles[0].role.value}")

    # Step 6: Attempt duplicate registration
    print("\nStep 6: Attempting duplicate registration...")
    duplicate_response = await client.post("/api/auth/register", json=registration_data)
    print(f"Duplicate response status: {duplicate_response.status_code}")

    assert duplicate_response.status_code == 400, f"Expected 400 for duplicate, got {duplicate_response.status_code}"
    duplicate_data = duplicate_response.json()
    assert "detail" in duplicate_data, "Error response should contain detail"
    assert "email" in duplicate_data["detail"].lower() or "already" in duplicate_data["detail"].lower(), \
        "Error message should mention email already exists"
    print(f"✓ Duplicate registration rejected: {duplicate_data['detail']}")

    print("\n=== Registration Flow E2E Test PASSED ===\n")


@pytest.mark.asyncio
async def test_registration_password_validation(client: AsyncClient):
    """
    Test registration password validation.

    Verifies that weak passwords are rejected:
    1. Password too short
    2. Missing uppercase
    3. Missing lowercase
    4. Missing digit
    """
    print("\n=== Testing Password Validation ===\n")

    weak_passwords = [
        ("short", "Short1!", "Password too short"),
        ("nouppercase", "nouppercase1!", "Missing uppercase"),
        ("NOLOWERCASE", "NOLOWERCASE1!", "Missing lowercase"),
        ("NoDigits!", "NoDigits!", "Missing digit"),
    ]

    for email, password, description in weak_passwords:
        print(f"Testing: {description} ('{password}')")

        response = await client.post("/api/auth/register", json={
            "email": f"{email}@example.com",
            "password": password,
            "full_name": "Test User"
        })

        assert response.status_code == 400, f"Expected 400 for {description}, got {response.status_code}"
        print(f"✓ Rejected: {description}")

    print("\n=== Password Validation Test PASSED ===\n")


@pytest.mark.asyncio
async def test_registration_email_validation(client: AsyncClient):
    """
    Test registration email validation.

    Verifies that invalid emails are rejected.
    """
    print("\n=== Testing Email Validation ===\n")

    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user @example.com",
    ]

    for email in invalid_emails:
        print(f"Testing invalid email: '{email}'")

        response = await client.post("/api/auth/register", json={
            "email": email,
            "password": "ValidPass123!",
            "full_name": "Test User"
        })

        # Should return 422 (validation error) for invalid email format
        assert response.status_code == 422, f"Expected 422 for '{email}', got {response.status_code}"
        print(f"✓ Rejected invalid email: '{email}'")

    print("\n=== Email Validation Test PASSED ===\n")


if __name__ == "__main__":
    print("Running registration flow tests...")
    pytest.main([__file__, "-v", "-s"])
