"""
End-to-end integration test for role-based access control (RBAC) enforcement.

This test verifies that role-based access control is properly enforced:
1. Users with different roles (Admin, Recruiter, Hiring Manager, Viewer) can be created
2. Each role has appropriate access levels to protected endpoints
3. Restricted endpoints return 403 for unauthorized roles
4. Role hierarchy works correctly (Admin > Hiring Manager > Recruiter > Viewer)
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
from utils.security import get_password_hash

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_rbac.db"


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
async def admin_user(client: AsyncClient, test_db: AsyncSession):
    """Create an admin user for testing."""
    user_data = {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin User"
    }

    # Register user
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201

    # Get user from database
    result = await test_db.execute(select(User).where(User.email == user_data["email"]))
    user = result.scalar_one()

    # Assign admin role
    admin_role = Role(
        user_id=user.id,
        role=UserRole.ADMIN
    )
    test_db.add(admin_role)
    await test_db.commit()

    # Login to get tokens
    login_response = await client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200

    tokens = login_response.json()
    return {
        "user": user_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }


@pytest.fixture
async def recruiter_user(client: AsyncClient, test_db: AsyncSession):
    """Create a recruiter user for testing."""
    user_data = {
        "email": "recruiter@example.com",
        "password": "RecruiterPass123!",
        "full_name": "Recruiter User"
    }

    # Register user
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201

    # Get user from database
    result = await test_db.execute(select(User).where(User.email == user_data["email"]))
    user = result.scalar_one()

    # Assign recruiter role
    recruiter_role = Role(
        user_id=user.id,
        role=UserRole.RECRUITER
    )
    test_db.add(recruiter_role)
    await test_db.commit()

    # Login to get tokens
    login_response = await client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200

    tokens = login_response.json()
    return {
        "user": user_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }


@pytest.fixture
async def hiring_manager_user(client: AsyncClient, test_db: AsyncSession):
    """Create a hiring manager user for testing."""
    user_data = {
        "email": "hiringmanager@example.com",
        "password": "HiringManagerPass123!",
        "full_name": "Hiring Manager User"
    }

    # Register user
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201

    # Get user from database
    result = await test_db.execute(select(User).where(User.email == user_data["email"]))
    user = result.scalar_one()

    # Assign hiring manager role
    hm_role = Role(
        user_id=user.id,
        role=UserRole.HIRING_MANAGER
    )
    test_db.add(hm_role)
    await test_db.commit()

    # Login to get tokens
    login_response = await client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200

    tokens = login_response.json()
    return {
        "user": user_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }


@pytest.fixture
async def viewer_user(client: AsyncClient, test_db: AsyncSession):
    """Create a viewer user for testing (default role)."""
    user_data = {
        "email": "viewer@example.com",
        "password": "ViewerPass123!",
        "full_name": "Viewer User"
    }

    # Register user (automatically gets viewer role)
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201

    # Verify user has viewer role
    result = await test_db.execute(select(User).where(User.email == user_data["email"]))
    user = result.scalar_one()

    role_result = await test_db.execute(
        select(Role).where(Role.user_id == user.id)
    )
    user_role = role_result.scalar_one()
    assert user_role.role == UserRole.VIEWER

    # Login to get tokens
    login_response = await client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200

    tokens = login_response.json()
    return {
        "user": user_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }


@pytest.mark.asyncio
async def test_users_have_correct_roles(client: AsyncClient, test_db: AsyncSession):
    """
    Test that users are created with correct role assignments in the database.
    """
    print("\n=== Testing User Role Assignments ===\n")

    # Create users with different roles
    users_data = []

    # Admin user
    admin_data = {
        "email": "admin_test@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin Test User"
    }
    await client.post("/api/auth/register", json=admin_data)
    result = await test_db.execute(select(User).where(User.email == admin_data["email"]))
    admin_user = result.scalar_one()
    admin_role = Role(user_id=admin_user.id, role=UserRole.ADMIN)
    test_db.add(admin_role)
    await test_db.commit()
    users_data.append(("admin", admin_data["email"], UserRole.ADMIN))

    # Recruiter user
    recruiter_data = {
        "email": "recruiter_test@example.com",
        "password": "RecruiterPass123!",
        "full_name": "Recruiter Test User"
    }
    await client.post("/api/auth/register", json=recruiter_data)
    result = await test_db.execute(select(User).where(User.email == recruiter_data["email"]))
    recruiter_user = result.scalar_one()
    recruiter_role = Role(user_id=recruiter_user.id, role=UserRole.RECRUITER)
    test_db.add(recruiter_role)
    await test_db.commit()
    users_data.append(("recruiter", recruiter_data["email"], UserRole.RECRUITER))

    # Hiring Manager user
    hm_data = {
        "email": "hm_test@example.com",
        "password": "HiringManagerPass123!",
        "full_name": "Hiring Manager Test User"
    }
    await client.post("/api/auth/register", json=hm_data)
    result = await test_db.execute(select(User).where(User.email == hm_data["email"]))
    hm_user = result.scalar_one()
    hm_role = Role(user_id=hm_user.id, role=UserRole.HIRING_MANAGER)
    test_db.add(hm_role)
    await test_db.commit()
    users_data.append(("hiring_manager", hm_data["email"], UserRole.HIRING_MANAGER))

    # Viewer user (default role)
    viewer_data = {
        "email": "viewer_test@example.com",
        "password": "ViewerPass123!",
        "full_name": "Viewer Test User"
    }
    await client.post("/api/auth/register", json=viewer_data)
    users_data.append(("viewer", viewer_data["email"], UserRole.VIEWER))

    # Verify all users have correct roles
    print("Verifying role assignments in database...")
    for role_name, email, expected_role in users_data:
        result = await test_db.execute(select(User).where(User.email == email))
        user = result.scalar_one()

        role_result = await test_db.execute(
            select(Role).where(Role.user_id == user.id, Role.role == expected_role)
        )
        user_role = role_result.scalar_one_or_none()

        assert user_role is not None, f"{role_name} user should have {expected_role.value} role"
        assert user_role.role == expected_role, f"{role_name} should have {expected_role.value} role"
        print(f"✓ {email} has role: {expected_role.value}")

    print("\n✓ All users have correct role assignments\n")


@pytest.mark.asyncio
async def test_viewer_cannot_access_recruiter_endpoints(
    client: AsyncClient,
    viewer_user: dict
):
    """
    Test that Viewer role cannot access recruiter-only endpoints.
    Viewer should receive 403 Forbidden for restricted operations.
    """
    print("\n=== Testing Viewer Access to Recruiter Endpoints ===\n")

    headers = {
        "Authorization": f"Bearer {viewer_user['access_token']}"
    }

    # Test 1: Try to move candidate to different stage (PUT /api/candidates/{id}/stage)
    print("Test 1: Viewer attempting to move candidate to different stage...")
    response = await client.put(
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage",
        json={"stage_id": "interview"},
        headers=headers
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    print(f"✓ Correctly returned 403 Forbidden")

    # Test 2: Try to bulk move candidates (POST /api/candidates/bulk-move)
    print("\nTest 2: Viewer attempting to bulk move candidates...")
    response = await client.post(
        "/api/candidates/bulk-move",
        json={
            "resume_ids": ["00000000-0000-0000-0000-000000000001"],
            "stage_id": "interview"
        },
        headers=headers
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    print(f"✓ Correctly returned 403 Forbidden")

    # Test 3: Try to perform bulk actions (POST /api/candidates/bulk-action)
    print("\nTest 3: Viewer attempting to perform bulk actions...")
    response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "export",
            "resume_ids": ["00000000-0000-0000-0000-000000000001"]
        },
        headers=headers
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    print(f"✓ Correctly returned 403 Forbidden")

    print("\n✓ Viewer correctly blocked from all recruiter-only endpoints\n")


@pytest.mark.asyncio
async def test_recruiter_can_access_recruiter_endpoints(
    client: AsyncClient,
    recruiter_user: dict
):
    """
    Test that Recruiter role can access recruiter-only endpoints.
    Recruiter should receive 200 OK or appropriate success response.
    """
    print("\n=== Testing Recruiter Access to Recruiter Endpoints ===\n")

    headers = {
        "Authorization": f"Bearer {recruiter_user['access_token']}"
    }

    # Test 1: Try to move candidate to different stage (PUT /api/candidates/{id}/stage)
    print("Test 1: Recruiter attempting to move candidate to different stage...")
    # Note: This may return 404 if candidate doesn't exist, but should NOT return 403
    response = await client.put(
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage",
        json={"stage_id": "interview"},
        headers=headers
    )
    assert response.status_code != 403, f"Recruiter should not get 403, got {response.status_code}"
    print(f"✓ Recruiter authorized (status: {response.status_code})")

    # Test 2: Try to bulk move candidates (POST /api/candidates/bulk-move)
    print("\nTest 2: Recruiter attempting to bulk move candidates...")
    response = await client.post(
        "/api/candidates/bulk-move",
        json={
            "resume_ids": ["00000000-0000-0000-0000-000000000001"],
            "stage_id": "interview"
        },
        headers=headers
    )
    assert response.status_code != 403, f"Recruiter should not get 403, got {response.status_code}"
    print(f"✓ Recruiter authorized (status: {response.status_code})")

    # Test 3: Try to perform bulk actions (POST /api/candidates/bulk-action)
    print("\nTest 3: Recruiter attempting to perform bulk actions...")
    response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "export",
            "resume_ids": ["00000000-0000-0000-0000-000000000001"]
        },
        headers=headers
    )
    assert response.status_code != 403, f"Recruiter should not get 403, got {response.status_code}"
    print(f"✓ Recruiter authorized (status: {response.status_code})")

    print("\n✓ Recruiter has access to all recruiter-only endpoints\n")


@pytest.mark.asyncio
async def test_hiring_manager_can_access_recruiter_endpoints(
    client: AsyncClient,
    hiring_manager_user: dict
):
    """
    Test that Hiring Manager role can access recruiter endpoints.
    Hiring Managers have higher privileges than Recruiters.
    """
    print("\n=== Testing Hiring Manager Access to Recruiter Endpoints ===\n")

    headers = {
        "Authorization": f"Bearer {hiring_manager_user['access_token']}"
    }

    # Test 1: Try to move candidate to different stage
    print("Test 1: Hiring Manager attempting to move candidate to different stage...")
    response = await client.put(
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage",
        json={"stage_id": "interview"},
        headers=headers
    )
    assert response.status_code != 403, f"Hiring Manager should not get 403, got {response.status_code}"
    print(f"✓ Hiring Manager authorized (status: {response.status_code})")

    # Test 2: Try to bulk move candidates
    print("\nTest 2: Hiring Manager attempting to bulk move candidates...")
    response = await client.post(
        "/api/candidates/bulk-move",
        json={
            "resume_ids": ["00000000-0000-0000-0000-000000000001"],
            "stage_id": "interview"
        },
        headers=headers
    )
    assert response.status_code != 403, f"Hiring Manager should not get 403, got {response.status_code}"
    print(f"✓ Hiring Manager authorized (status: {response.status_code})")

    print("\n✓ Hiring Manager has access to recruiter endpoints\n")


@pytest.mark.asyncio
async def test_admin_can_access_recruiter_endpoints(
    client: AsyncClient,
    admin_user: dict
):
    """
    Test that Admin role can access recruiter endpoints.
    Admins have the highest privileges and can access all endpoints.
    """
    print("\n=== Testing Admin Access to Recruiter Endpoints ===\n")

    headers = {
        "Authorization": f"Bearer {admin_user['access_token']}"
    }

    # Test 1: Try to move candidate to different stage
    print("Test 1: Admin attempting to move candidate to different stage...")
    response = await client.put(
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage",
        json={"stage_id": "interview"},
        headers=headers
    )
    assert response.status_code != 403, f"Admin should not get 403, got {response.status_code}"
    print(f"✓ Admin authorized (status: {response.status_code})")

    # Test 2: Try to bulk move candidates
    print("\nTest 2: Admin attempting to bulk move candidates...")
    response = await client.post(
        "/api/candidates/bulk-move",
        json={
            "resume_ids": ["00000000-0000-0000-0000-000000000001"],
            "stage_id": "interview"
        },
        headers=headers
    )
    assert response.status_code != 403, f"Admin should not get 403, got {response.status_code}"
    print(f"✓ Admin authorized (status: {response.status_code})")

    print("\n✓ Admin has access to all recruiter endpoints\n")


@pytest.mark.asyncio
async def test_all_roles_can_access_read_only_endpoints(
    client: AsyncClient,
    viewer_user: dict,
    recruiter_user: dict,
    admin_user: dict
):
    """
    Test that all authenticated roles can access read-only endpoints.
    Read-only endpoints only require authentication, not specific roles.
    """
    print("\n=== Testing All Roles Access to Read-Only Endpoints ===\n")

    # Test viewer access
    print("Test 1: Viewer accessing read-only endpoint (list candidates)...")
    headers = {"Authorization": f"Bearer {viewer_user['access_token']}"}
    response = await client.get("/api/candidates/", headers=headers)
    assert response.status_code == 200, f"Viewer should access read-only endpoint, got {response.status_code}"
    print(f"✓ Viewer can access read-only endpoint (status: {response.status_code})")

    # Test recruiter access
    print("\nTest 2: Recruiter accessing read-only endpoint (list candidates)...")
    headers = {"Authorization": f"Bearer {recruiter_user['access_token']}"}
    response = await client.get("/api/candidates/", headers=headers)
    assert response.status_code == 200, f"Recruiter should access read-only endpoint, got {response.status_code}"
    print(f"✓ Recruiter can access read-only endpoint (status: {response.status_code})")

    # Test admin access
    print("\nTest 3: Admin accessing read-only endpoint (list candidates)...")
    headers = {"Authorization": f"Bearer {admin_user['access_token']}"}
    response = await client.get("/api/candidates/", headers=headers)
    assert response.status_code == 200, f"Admin should access read-only endpoint, got {response.status_code}"
    print(f"✓ Admin can access read-only endpoint (status: {response.status_code})")

    print("\n✓ All roles can access read-only endpoints\n")


@pytest.mark.asyncio
async def test_unauthenticated_access_denied(client: AsyncClient):
    """
    Test that unauthenticated requests are denied with 401.
    All protected endpoints should require authentication.
    """
    print("\n=== Testing Unauthenticated Access ===\n")

    # Test 1: Try to access candidates list without authentication
    print("Test 1: Unauthenticated request to list candidates...")
    response = await client.get("/api/candidates/")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print(f"✓ Correctly returned 401 Unauthorized")

    # Test 2: Try to move candidate without authentication
    print("\nTest 2: Unauthenticated request to move candidate...")
    response = await client.put(
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage",
        json={"stage_id": "interview"}
    )
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print(f"✓ Correctly returned 401 Unauthorized")

    # Test 3: Try to bulk move candidates without authentication
    print("\nTest 3: Unauthenticated request to bulk move candidates...")
    response = await client.post(
        "/api/candidates/bulk-move",
        json={
            "resume_ids": ["00000000-0000-0000-0000-000000000001"],
            "stage_id": "interview"
        }
    )
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print(f"✓ Correctly returned 401 Unauthorized")

    print("\n✓ All unauthenticated requests correctly denied\n")


@pytest.mark.asyncio
async def test_role_enforcement_with_invalid_token(client: AsyncClient):
    """
    Test that invalid tokens are rejected with 401.
    """
    print("\n=== Testing Invalid Token Handling ===\n")

    headers = {
        "Authorization": "Bearer invalid.token.here"
    }

    print("Test: Requesting with invalid JWT token...")
    response = await client.get("/api/candidates/", headers=headers)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print(f"✓ Correctly returned 401 Unauthorized")

    print("\n✓ Invalid tokens correctly rejected\n")


@pytest.mark.asyncio
async def test_rbac_error_messages(client: AsyncClient, viewer_user: dict):
    """
    Test that RBAC errors return appropriate error messages.
    Error messages should be descriptive but not leak sensitive information.
    """
    print("\n=== Testing RBAC Error Messages ===\n")

    headers = {
        "Authorization": f"Bearer {viewer_user['access_token']}"
    }

    print("Test: Checking 403 error message for insufficient role...")
    response = await client.put(
        "/api/candidates/00000000-0000-0000-0000-000000000001/stage",
        json={"stage_id": "interview"},
        headers=headers
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    error_data = response.json()
    assert "detail" in error_data, "Error response should have 'detail' field"
    print(f"✓ Error message: {error_data['detail']}")

    # Verify error message mentions role requirement
    assert "role" in error_data["detail"].lower() or "recruiter" in error_data["detail"].lower() or "permission" in error_data["detail"].lower()
    print("✓ Error message is descriptive and mentions role/permission")

    print("\n✓ RBAC error messages are appropriate\n")
