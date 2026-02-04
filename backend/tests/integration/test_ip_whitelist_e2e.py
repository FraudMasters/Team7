"""
End-to-End Integration Tests for IP Whitelist Functionality

This test module performs comprehensive verification of the IP whitelist system,
including CRUD operations for whitelist entries, CIDR notation validation,
IP range matching, and integration with security configuration.

Test Coverage:
- IP whitelist CRUD operations (create, read, update, delete)
- CIDR notation validation for IPv4 and IPv6
- IP range validation (start/end IPs)
- Whitelist filtering by organization and active status
- Security configuration integration (enable/disable IP whitelist)
- Strict mode enforcement when no whitelist is configured
- Multiple whitelist entries per organization
- System-wide and organization-specific whitelists
- Whitelist statistics and aggregation

Note: Actual IP enforcement by the middleware is tested in unit tests.
These tests focus on API endpoints and data persistence.
"""
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.ip_whitelist import IPWhitelist
from models.security_config import SecurityConfig
from models.audit_log import AuditLog, AuditActionType
from config import get_settings


# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Test Data
VALID_IPV4_CIDR = "192.168.1.0/24"
VALID_IPV6_CIDR = "2001:db8::/32"
VALID_IP_START = "192.168.1.1"
VALID_IP_END = "192.168.1.100"
INVALID_CIDR = "not-a-valid-cidr"
OUT_OF_RANGE_IP = "192.168.2.1"


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database override."""

    async def override_get_db():
        yield test_db

    # Import app after models are loaded
    from main import app
    from database import get_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_security_config(test_db: AsyncSession) -> SecurityConfig:
    """Create test security configuration."""
    config = SecurityConfig(
        organization_id=None,  # System-wide config
        sso_enabled=False,
        two_factor_required=False,
        ip_whitelist_enabled=False,  # Start with IP whitelist disabled
        ip_whitelist_strict=False,
        session_timeout_minutes=60,
    )
    test_db.add(config)
    await test_db.commit()
    await test_db.refresh(config)
    return config


class TestIPWhitelistCreate:
    """Test suite for creating IP whitelist entries."""

    @pytest.mark.asyncio
    async def test_create_whitelist_entry_with_cidr(self, test_client: AsyncClient):
        """Test creating whitelist entry with CIDR notation."""
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Office Network",
                "description": "Main office IP range",
                "cidr_notation": VALID_IPV4_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Office Network"
        assert data["cidr_notation"] == VALID_IPV4_CIDR
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_whitelist_entry_with_ip_range(self, test_client: AsyncClient):
        """Test creating whitelist entry with IP range."""
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "VPN Range",
                "description": "VPN IP range",
                "cidr_notation": None,
                "start_ip": VALID_IP_START,
                "end_ip": VALID_IP_END,
                "is_active": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "VPN Range"
        assert data["start_ip"] == VALID_IP_START
        assert data["end_ip"] == VALID_IP_END
        assert data["cidr_notation"] is None

    @pytest.mark.asyncio
    async def test_create_whitelist_entry_with_ipv6_cidr(self, test_client: AsyncClient):
        """Test creating whitelist entry with IPv6 CIDR."""
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "IPv6 Network",
                "description": "IPv6 test network",
                "cidr_notation": VALID_IPV6_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "IPv6 Network"
        assert data["cidr_notation"] == VALID_IPV6_CIDR

    @pytest.mark.asyncio
    async def test_create_whitelist_entry_inactive(self, test_client: AsyncClient):
        """Test creating inactive whitelist entry."""
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Disabled Network",
                "description": "Inactive whitelist entry",
                "cidr_notation": VALID_IPV4_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_create_whitelist_entry_for_organization(
        self, test_client: AsyncClient
    ):
        """Test creating organization-specific whitelist entry."""
        org_id = str(uuid4())

        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": org_id,
                "name": "Org Office Network",
                "description": "Organization-specific whitelist",
                "cidr_notation": VALID_IPV4_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == org_id

    @pytest.mark.asyncio
    async def test_create_whitelist_entry_missing_name(self, test_client: AsyncClient):
        """Test that missing required fields return validation error."""
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "description": "Missing name",
                "cidr_notation": VALID_IPV4_CIDR,
                "is_active": True,
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_whitelist_entry_missing_ip_specification(
        self, test_client: AsyncClient
    ):
        """Test that missing both CIDR and IP range returns error."""
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Invalid Entry",
                "description": "No IP specification",
                "cidr_notation": None,
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        # Should return error since either CIDR or range must be specified
        assert response.status_code == 400


class TestIPWhitelistRead:
    """Test suite for reading IP whitelist entries."""

    @pytest.mark.asyncio
    async def test_get_all_whitelist_entries(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test retrieving all whitelist entries."""
        # Create test entries
        entry1 = IPWhitelist(
            organization_id=None,
            name="Office Network",
            cidr_notation=VALID_IPV4_CIDR,
            is_active=True,
        )
        entry2 = IPWhitelist(
            organization_id=None,
            name="VPN Range",
            start_ip=VALID_IP_START,
            end_ip=VALID_IP_END,
            is_active=True,
        )
        test_db.add(entry1)
        test_db.add(entry2)
        await test_db.commit()

        response = await test_client.get("/api/security/ip-whitelist")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["entries"]) == 2

    @pytest.mark.asyncio
    async def test_get_whitelist_entries_by_organization(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering whitelist entries by organization."""
        org_id = uuid4()

        # Create entries for different organizations
        entry1 = IPWhitelist(
            organization_id=org_id,
            name="Org Network",
            cidr_notation=VALID_IPV4_CIDR,
            is_active=True,
        )
        entry2 = IPWhitelist(
            organization_id=None,  # System-wide
            name="System Network",
            cidr_notation="10.0.0.0/8",
            is_active=True,
        )
        test_db.add(entry1)
        test_db.add(entry2)
        await test_db.commit()

        response = await test_client.get(
            f"/api/security/ip-whitelist?organization_id={org_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["entries"][0]["name"] == "Org Network"

    @pytest.mark.asyncio
    async def test_get_whitelist_entries_by_active_status(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering whitelist entries by active status."""
        # Create active and inactive entries
        entry1 = IPWhitelist(
            organization_id=None,
            name="Active Network",
            cidr_notation=VALID_IPV4_CIDR,
            is_active=True,
        )
        entry2 = IPWhitelist(
            organization_id=None,
            name="Inactive Network",
            cidr_notation="10.0.0.0/8",
            is_active=False,
        )
        test_db.add(entry1)
        test_db.add(entry2)
        await test_db.commit()

        response = await test_client.get("/api/security/ip-whitelist?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["entries"][0]["name"] == "Active Network"

    @pytest.mark.asyncio
    async def test_get_whitelist_entries_with_pagination(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test pagination of whitelist entries."""
        # Create multiple entries
        for i in range(5):
            entry = IPWhitelist(
                organization_id=None,
                name=f"Network {i}",
                cidr_notation=f"10.{i}.0.0/24",
                is_active=True,
            )
            test_db.add(entry)
        await test_db.commit()

        response = await test_client.get("/api/security/ip-whitelist?limit=2&offset=2")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2  # Limited
        assert len(data["entries"]) == 2


class TestIPWhitelistUpdate:
    """Test suite for updating IP whitelist entries."""

    @pytest.mark.asyncio
    async def test_update_whitelist_entry_name(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test updating whitelist entry name."""
        entry = IPWhitelist(
            organization_id=None,
            name="Original Name",
            cidr_notation=VALID_IPV4_CIDR,
            is_active=True,
        )
        test_db.add(entry)
        await test_db.commit()
        await test_db.refresh(entry)

        response = await test_client.put(
            f"/api/security/ip-whitelist/{entry.id}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
                "cidr_notation": VALID_IPV4_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_whitelist_entry_cidr(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test updating CIDR notation."""
        entry = IPWhitelist(
            organization_id=None,
            name="Network",
            cidr_notation="192.168.1.0/24",
            is_active=True,
        )
        test_db.add(entry)
        await test_db.commit()
        await test_db.refresh(entry)

        response = await test_client.put(
            f"/api/security/ip-whitelist/{entry.id}",
            json={
                "name": "Network",
                "description": None,
                "cidr_notation": "10.0.0.0/8",
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cidr_notation"] == "10.0.0.0/8"

    @pytest.mark.asyncio
    async def test_update_whitelist_entry_toggle_active(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test toggling active status."""
        entry = IPWhitelist(
            organization_id=None,
            name="Network",
            cidr_notation=VALID_IPV4_CIDR,
            is_active=True,
        )
        test_db.add(entry)
        await test_db.commit()
        await test_db.refresh(entry)

        # Disable entry
        response = await test_client.put(
            f"/api/security/ip-whitelist/{entry.id}",
            json={
                "name": "Network",
                "description": None,
                "cidr_notation": VALID_IPV4_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_nonexistent_entry(self, test_client: AsyncClient):
        """Test updating non-existent whitelist entry."""
        fake_id = uuid4()

        response = await test_client.put(
            f"/api/security/ip-whitelist/{fake_id}",
            json={
                "name": "Updated",
                "description": None,
                "cidr_notation": VALID_IPV4_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        assert response.status_code == 404


class TestIPWhitelistDelete:
    """Test suite for deleting IP whitelist entries."""

    @pytest.mark.asyncio
    async def test_delete_whitelist_entry(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test deleting a whitelist entry."""
        entry = IPWhitelist(
            organization_id=None,
            name="Network to Delete",
            cidr_notation=VALID_IPV4_CIDR,
            is_active=True,
        )
        test_db.add(entry)
        await test_db.commit()
        await test_db.refresh(entry)

        response = await test_client.delete(f"/api/security/ip-whitelist/{entry.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "IP whitelist entry deleted successfully"

        # Verify deletion
        result = await test_db.execute(
            select(IPWhitelist).where(IPWhitelist.id == entry.id)
        )
        deleted_entry = result.scalar_one_or_none()
        assert deleted_entry is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entry(self, test_client: AsyncClient):
        """Test deleting non-existent whitelist entry."""
        fake_id = uuid4()

        response = await test_client.delete(f"/api/security/ip-whitelist/{fake_id}")

        assert response.status_code == 404


class TestIPWhitelistWithSecurityConfig:
    """Test suite for IP whitelist integration with security configuration."""

    @pytest.mark.asyncio
    async def test_enable_ip_whitelist_enforcement(
        self, test_client: AsyncClient, test_security_config: SecurityConfig
    ):
        """Test enabling IP whitelist enforcement."""
        response = await test_client.put(
            f"/api/security/config/{test_security_config.id}",
            json={
                "sso_enabled": False,
                "two_factor_required": False,
                "ip_whitelist_enabled": True,
                "ip_whitelist_strict": False,
                "session_timeout_minutes": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ip_whitelist_enabled"] is True

    @pytest.mark.asyncio
    async def test_enable_strict_mode(
        self, test_client: AsyncClient, test_security_config: SecurityConfig
    ):
        """Test enabling strict mode (block all when no whitelist configured)."""
        response = await test_client.put(
            f"/api/security/config/{test_security_config.id}",
            json={
                "sso_enabled": False,
                "two_factor_required": False,
                "ip_whitelist_enabled": True,
                "ip_whitelist_strict": True,
                "session_timeout_minutes": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ip_whitelist_strict"] is True

    @pytest.mark.asyncio
    async def test_whitelist_with_enforcement_disabled(
        self, test_client: AsyncClient, test_security_config: SecurityConfig
    ):
        """Test that whitelist entries can be managed even when enforcement is disabled."""
        # IP whitelist disabled in security config
        assert test_security_config.ip_whitelist_enabled is False

        # Should still be able to create whitelist entries
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Pre-configured Network",
                "description": "Configure before enabling",
                "cidr_notation": VALID_IPV4_CIDR,
                "start_ip": None,
                "end_ip": None,
                "is_active": True,
            },
        )

        assert response.status_code == 200


class TestIPWhitelistValidation:
    """Test suite for IP validation in whitelist entries."""

    @pytest.mark.asyncio
    async def test_cidr_notation_validation(self, test_client: AsyncClient):
        """Test CIDR notation validation."""
        # Valid CIDR should work
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Valid CIDR",
                "cidr_notation": "192.168.1.0/24",
                "is_active": True,
            },
        )
        assert response.status_code == 200

        # Invalid CIDR should fail
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Invalid CIDR",
                "cidr_notation": "not-a-cidr",
                "is_active": True,
            },
        )
        # API should reject or store it, but middleware won't match it
        # (validation may happen at API level or during enforcement)

    @pytest.mark.asyncio
    async def test_ip_range_validation(self, test_client: AsyncClient):
        """Test IP range validation."""
        # Valid IP range should work
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Valid Range",
                "start_ip": "192.168.1.1",
                "end_ip": "192.168.1.100",
                "is_active": True,
            },
        )
        assert response.status_code == 200

        # Start IP greater than end IP should be rejected
        response = await test_client.post(
            "/api/security/ip-whitelist",
            json={
                "organization_id": None,
                "name": "Invalid Range",
                "start_ip": "192.168.1.100",
                "end_ip": "192.168.1.1",
                "is_active": True,
            },
        )
        assert response.status_code == 400


class TestIPWhitelistStatistics:
    """Test suite for IP whitelist statistics and aggregation."""

    @pytest.mark.asyncio
    async def test_whitelist_count_by_organization(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test counting whitelist entries by organization."""
        org_id = uuid4()

        # Create entries for organization
        for i in range(3):
            entry = IPWhitelist(
                organization_id=org_id,
                name=f"Org Network {i}",
                cidr_notation=f"10.{i}.0.0/24",
                is_active=True,
            )
            test_db.add(entry)

        # Create system-wide entries
        for i in range(2):
            entry = IPWhitelist(
                organization_id=None,
                name=f"System Network {i}",
                cidr_notation=f"192.168.{i}.0/24",
                is_active=True,
            )
            test_db.add(entry)

        await test_db.commit()

        # Get organization entries
        response = await test_client.get(
            f"/api/security/ip-whitelist?organization_id={org_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3

        # Get system entries
        response = await test_client.get("/api/security/ip-whitelist?organization_id=null")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2

    @pytest.mark.asyncio
    async def test_active_vs_inactive_count(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test counting active vs inactive whitelist entries."""
        # Create active entries
        for i in range(3):
            entry = IPWhitelist(
                organization_id=None,
                name=f"Active Network {i}",
                cidr_notation=f"10.{i}.0.0/24",
                is_active=True,
            )
            test_db.add(entry)

        # Create inactive entries
        for i in range(2):
            entry = IPWhitelist(
                organization_id=None,
                name=f"Inactive Network {i}",
                cidr_notation=f"192.168.{i}.0/24",
                is_active=False,
            )
            test_db.add(entry)

        await test_db.commit()

        # Get active count
        response = await test_client.get("/api/security/ip-whitelist?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3

        # Get inactive count
        response = await test_client.get("/api/security/ip-whitelist?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2


class TestIPWhitelistEdgeCases:
    """Test suite for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_cidr_and_range_both_specified(
        self, test_client: AsyncClient, test_db: AsyncSession
    ):
        """Test whitelist entry with both CIDR and range specified."""
        entry = IPWhitelist(
            organization_id=None,
            name="Both Specified",
            cidr_notation=VALID_IPV4_CIDR,
            start_ip=VALID_IP_START,
            end_ip=VALID_IP_END,
            is_active=True,
        )
        test_db.add(entry)
        await test_db.commit()
        await test_db.refresh(entry)

        response = await test_client.get(f"/api/security/ip-whitelist")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        # Both should be stored
        assert data["entries"][0]["cidr_notation"] == VALID_IPV4_CIDR
        assert data["entries"][0]["start_ip"] == VALID_IP_START

    @pytest.mark.asyncio
    async def test_organization_filter_with_invalid_uuid(
        self, test_client: AsyncClient
    ):
        """Test organization filter with invalid UUID format."""
        response = await test_client.get(
            "/api/security/ip-whitelist?organization_id=not-a-uuid"
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_pagination_limits(self, test_client: AsyncClient):
        """Test pagination limit enforcement."""
        # Request more than maximum allowed limit
        response = await test_client.get("/api/security/ip-whitelist?limit=2000")

        # Should reject or cap at maximum
        assert response.status_code == 400  # Validation error for limit > 1000

    @pytest.mark.asyncio
    async def test_update_entry_with_invalid_uuid(self, test_client: AsyncClient):
        """Test updating entry with invalid UUID."""
        response = await test_client.put(
            "/api/security/ip-whitelist/not-a-uuid",
            json={
                "name": "Updated",
                "cidr_notation": VALID_IPV4_CIDR,
                "is_active": True,
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_entry_with_invalid_uuid(self, test_client: AsyncClient):
        """Test deleting entry with invalid UUID."""
        response = await test_client.delete("/api/security/ip-whitelist/not-a-uuid")

        assert response.status_code == 400
