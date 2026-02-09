"""
End-to-end integration test for job seeker registration flow.

This test verifies the complete job seeker registration flow:
1. Job seeker submits registration data via API
2. User is created in database with hashed password
3. Job seeker role is assigned (or defaults to job_seeker)
4. Response contains correct user information
5. Duplicate email is rejected
6. Role validation works correctly
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
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_job_seeker_registration.db"


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
async def test_job_seeker_registration_with_role(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end test: Job seeker registration with explicit role.

    Verification steps:
    1. Submit registration request with role='job_seeker'
    2. Verify response contains user information
    3. Verify user created in database
    4. Verify password is hashed (not stored in plaintext)
    5. Verify 'job_seeker' role is assigned
    6. Verify user is active but not verified
    """
    print("\n=== Starting Job Seeker Registration (Explicit Role) Test ===\n")

    # Step 1: Submit registration request with explicit role
    print("Step 1: Submitting registration request with role='job_seeker'...")
    registration_data = {
        "email": "jobseeker1@example.com",
        "password": "JobSeekerPass123!",
        "full_name": "Jane JobSeeker",
        "role": "job_seeker"
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

    # Step 5: Verify job_seeker role is assigned
    print("\nStep 5: Verifying job_seeker role assigned...")
    result = await test_db.execute(
        select(Role).where(Role.user_id == user.id)
    )
    roles = result.scalars().all()

    assert len(roles) == 1, "User should have exactly 1 role"
    assert roles[0].role == UserRole.JOB_SEEKER, "Role should be JOB_SEEKER"
    print(f"✓ Job seeker role assigned: {roles[0].role.value}")

    print("\n=== Job Seeker Registration (Explicit Role) Test PASSED ===\n")


@pytest.mark.asyncio
async def test_job_seeker_registration_default_role(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end test: Job seeker registration with default role.

    Verifies that when no role is specified, the system defaults to job_seeker.
    """
    print("\n=== Starting Job Seeker Registration (Default Role) Test ===\n")

    # Step 1: Submit registration request without role
    print("Step 1: Submitting registration request without role parameter...")
    registration_data = {
        "email": "jobseeker2@example.com",
        "password": "DefaultRole123!",
        "full_name": "John Default"
    }

    response = await client.post("/api/auth/register", json=registration_data)
    print(f"Response status: {response.status_code}")

    # Step 2: Verify response
    print("\nStep 2: Verifying registration response...")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()
    assert "id" in data, "Response should contain user ID"
    assert data["email"] == registration_data["email"], "Email should match"
    print("✓ Registration response valid")

    # Step 3: Verify user created in database
    print("\nStep 3: Verifying user created in database...")
    result = await test_db.execute(
        select(User).where(User.email == registration_data["email"])
    )
    user = result.scalar_one_or_none()

    assert user is not None, "User should be created in database"
    print(f"✓ User found in database with ID: {user.id}")

    # Step 4: Verify default role is job_seeker
    print("\nStep 4: Verifying default role is job_seeker...")
    result = await test_db.execute(
        select(Role).where(Role.user_id == user.id)
    )
    roles = result.scalars().all()

    assert len(roles) == 1, "User should have exactly 1 role"
    assert roles[0].role == UserRole.JOB_SEEKER, "Default role should be JOB_SEEKER"
    print(f"✓ Default role correctly assigned as job_seeker")

    print("\n=== Job Seeker Registration (Default Role) Test PASSED ===\n")


@pytest.mark.asyncio
async def test_job_seeker_duplicate_registration(client: AsyncClient, test_db: AsyncSession):
    """
    Test duplicate job seeker registration rejection.

    Verifies that registering with the same email twice is rejected.
    """
    print("\n=== Testing Duplicate Job Seeker Registration ===\n")

    registration_data = {
        "email": "duplicate@example.com",
        "password": "Duplicate123!",
        "full_name": "Duplicate User",
        "role": "job_seeker"
    }

    # First registration
    print("Step 1: Registering new job seeker...")
    response = await client.post("/api/auth/register", json=registration_data)
    assert response.status_code == 201, f"First registration should succeed, got {response.status_code}"
    print("✓ First registration successful")

    # Attempt duplicate registration
    print("\nStep 2: Attempting duplicate registration...")
    duplicate_response = await client.post("/api/auth/register", json=registration_data)
    print(f"Duplicate response status: {duplicate_response.status_code}")

    assert duplicate_response.status_code == 400, f"Expected 400 for duplicate, got {duplicate_response.status_code}"
    duplicate_data = duplicate_response.json()
    assert "detail" in duplicate_data, "Error response should contain detail"
    assert "email" in duplicate_data["detail"].lower() or "already" in duplicate_data["detail"].lower(), \
        "Error message should mention email already exists"
    print(f"✓ Duplicate registration rejected: {duplicate_data['detail']}")

    print("\n=== Duplicate Job Seeker Registration Test PASSED ===\n")


@pytest.mark.asyncio
async def test_job_seeker_invalid_role(client: AsyncClient):
    """
    Test job seeker registration with invalid role.

    Verifies that invalid role values are rejected.
    """
    print("\n=== Testing Invalid Role ===\n")

    invalid_roles = [
        "invalid_role",
        "admin123",
        "JOBSEEKER",  # Wrong case
        "",
    ]

    for role in invalid_roles:
        print(f"Testing invalid role: '{role}'")

        response = await client.post("/api/auth/register", json={
            "email": f"test_{role}@example.com",
            "password": "ValidPass123!",
            "full_name": "Test User",
            "role": role
        })

        # Should return 400 for invalid role
        assert response.status_code == 400, f"Expected 400 for role '{role}', got {response.status_code}"
        print(f"✓ Rejected invalid role: '{role}'")

    print("\n=== Invalid Role Test PASSED ===\n")


@pytest.mark.asyncio
async def test_job_seeker_password_validation(client: AsyncClient):
    """
    Test job seeker registration password validation.

    Verifies that weak passwords are rejected for job seeker registration.
    """
    print("\n=== Testing Job Seeker Password Validation ===\n")

    weak_passwords = [
        ("weak", "Weak1!", "Password too short"),
        ("nouppercase", "nouppercase1!", "Missing uppercase"),
        ("NOLOWERCASE", "NOLOWERCASE1!", "Missing lowercase"),
        ("NoDigits!", "NoDigits!", "Missing digit"),
    ]

    for email, password, description in weak_passwords:
        print(f"Testing: {description} ('{password}')")

        response = await client.post("/api/auth/register", json={
            "email": f"{email}@example.com",
            "password": password,
            "full_name": "Job Seeker",
            "role": "job_seeker"
        })

        assert response.status_code == 400, f"Expected 400 for {description}, got {response.status_code}"
        print(f"✓ Rejected: {description}")

    print("\n=== Job Seeker Password Validation Test PASSED ===\n")


@pytest.mark.asyncio
async def test_job_seeker_role_uniqueness(client: AsyncClient, test_db: AsyncSession):
    """
    Test that job seeker role is properly stored and can be queried.

    Verifies the role can be retrieved and matches the job_seeker enum value.
    """
    print("\n=== Testing Job Seeker Role Uniqueness ===\n")

    registration_data = {
        "email": "unique@example.com",
        "password": "UniquePass123!",
        "full_name": "Unique Seeker",
        "role": "job_seeker"
    }

    # Register job seeker
    response = await client.post("/api/auth/register", json=registration_data)
    assert response.status_code == 201, "Registration should succeed"

    # Get user from database
    result = await test_db.execute(
        select(User).where(User.email == registration_data["email"])
    )
    user = result.scalar_one_or_none()
    assert user is not None, "User should exist"

    # Verify role
    result = await test_db.execute(
        select(Role).where(Role.user_id == user.id)
    )
    roles = result.scalars().all()

    assert len(roles) == 1, "Should have exactly one role"
    role = roles[0]

    # Verify role enum value
    assert role.role == UserRole.JOB_SEEKER, "Role should be JOB_SEEKER"
    assert role.role.value == "job_seeker", "Role value should be 'job_seeker'"
    assert str(role.role) == "job_seeker", "Role string representation should be 'job_seeker'"

    print(f"✓ Job seeker role properly stored: {role.role.value}")
    print("\n=== Job Seeker Role Uniqueness Test PASSED ===\n")


@pytest.mark.asyncio
async def test_multiple_job_seekers_can_register(client: AsyncClient, test_db: AsyncSession):
    """
    Test that multiple job seekers can register with different emails.

    Verifies the system can handle multiple job seeker registrations.
    """
    print("\n=== Testing Multiple Job Seeker Registrations ===\n")

    job_seekers = [
        {
            "email": "seeker1@example.com",
            "password": "SeekerOne123!",
            "full_name": "First Seeker",
            "role": "job_seeker"
        },
        {
            "email": "seeker2@example.com",
            "password": "SeekerTwo123!",
            "full_name": "Second Seeker",
            "role": "job_seeker"
        },
        {
            "email": "seeker3@example.com",
            "password": "SeekerThree123!",
            "full_name": "Third Seeker",
            # No role specified - should default to job_seeker
        }
    ]

    registered_ids = []

    for i, seeker_data in enumerate(job_seekers, 1):
        print(f"Registering job seeker {i}: {seeker_data['email']}")

        response = await client.post("/api/auth/register", json=seeker_data)
        assert response.status_code == 201, f"Registration {i} should succeed"

        data = response.json()
        registered_ids.append(data["id"])
        print(f"✓ Job seeker {i} registered with ID: {data['id']}")

    # Verify all users exist in database
    print("\nVerifying all job seekers in database...")
    for seeker_data in job_seekers:
        result = await test_db.execute(
            select(User).where(User.email == seeker_data["email"])
        )
        user = result.scalar_one_or_none()
        assert user is not None, f"User {seeker_data['email']} should exist in database"

        # Verify role
        result = await test_db.execute(
            select(Role).where(Role.user_id == user.id)
        )
        roles = result.scalars().all()
        assert len(roles) == 1, "Should have exactly one role"
        assert roles[0].role == UserRole.JOB_SEEKER, "All should be job seekers"
        print(f"✓ {seeker_data['email']} has job_seeker role")

    assert len(registered_ids) == 3, "Should have 3 unique user IDs"
    assert len(set(registered_ids)) == 3, "All user IDs should be unique"

    print("\n=== Multiple Job Seeker Registrations Test PASSED ===\n")


if __name__ == "__main__":
    print("Running job seeker registration flow tests...")
    pytest.main([__file__, "-v", "-s"])
