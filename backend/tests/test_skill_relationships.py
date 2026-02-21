"""
Unit Tests for SkillRelationship Model and API

Tests cover:
- RelationshipType enum values
- SkillRelationship model instantiation and defaults
- Create skill relationships (batch)
- List skill relationships with filters
- Get single skill relationship
- Update skill relationship
- Delete skill relationship
- Delete relationships by skill
- Get relationship types
- Validation (UUIDs, relationship types, weights)
- Error handling
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from database import get_db, Base
from models.skill_relationship import SkillRelationship, RelationshipType
from models.skill_taxonomy import SkillTaxonomy
from api.skill_relationships import (
    validate_relationship_type,
    get_skill_name,
    create_skill_relationships,
    list_skill_relationships,
    get_skill_relationship,
    update_skill_relationship,
    delete_skill_relationship,
    delete_skill_relationships_by_skill,
    list_relationship_types,
)


# ============================================================================
# Test Database Setup
# ============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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
async def test_session(test_engine) -> AsyncSession:
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


# Helper function to create test skill taxonomy
async def create_test_skill(session: AsyncSession, **kwargs) -> SkillTaxonomy:
    """Create a test skill taxonomy with default or provided values."""
    defaults = {
        "skill_name": f"test_skill_{uuid4().hex[:8]}",
        "variants": [],
        "industry": "Technology",
        "context": "general",
        "organization_id": uuid4(),
    }
    defaults.update(kwargs)

    skill = SkillTaxonomy(**defaults)
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return skill


# Helper function to create test skill relationship
async def create_test_relationship(session: AsyncSession, **kwargs) -> SkillRelationship:
    """Create a test skill relationship with default or provided values."""
    org_id = kwargs.get("organization_id", uuid4())

    # Create default skills if not provided
    if "source_skill_id" not in kwargs:
        source = await create_test_skill(session, organization_id=org_id)
        kwargs["source_skill_id"] = source.id

    if "target_skill_id" not in kwargs:
        target = await create_test_skill(session, organization_id=org_id)
        kwargs["target_skill_id"] = target.id

    defaults = {
        "relationship_type": RelationshipType.RELATED.value,
        "weight": 0.5,
        "extra_metadata": {"test": "data"},
        "is_active": True,
        "organization_id": org_id,
    }
    defaults.update(kwargs)

    rel = SkillRelationship(**defaults)
    session.add(rel)
    await session.commit()
    await session.refresh(rel)
    return rel


# ============================================================================
# Test RelationshipType Enum
# ============================================================================

class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_relationship_type_values(self):
        """Test that all relationship types have correct values."""
        assert RelationshipType.PARENT_CHILD.value == "parent_child"
        assert RelationshipType.SIMILAR.value == "similar"
        assert RelationshipType.PREREQUISITE.value == "prerequisite"
        assert RelationshipType.RELATED.value == "related"

    def test_relationship_type_count(self):
        """Test that there are exactly 4 relationship types."""
        assert len(RelationshipType) == 4

    def test_relationship_type_is_string_enum(self):
        """Test that RelationshipType is a string enum."""
        assert isinstance(RelationshipType.PARENT_CHILD.value, str)
        assert isinstance(RelationshipType.SIMILAR.value, str)


# ============================================================================
# Test SkillRelationship Model
# ============================================================================

class TestSkillRelationshipModel:
    """Tests for SkillRelationship model."""

    def test_model_instantiation(self):
        """Test basic model instantiation."""
        org_id = uuid4()
        source_id = uuid4()
        target_id = uuid4()

        rel = SkillRelationship(
            source_skill_id=source_id,
            target_skill_id=target_id,
            relationship_type=RelationshipType.SIMILAR.value,
            weight=0.75,
            extra_metadata={"context": "frontend"},
            is_active=True,
            organization_id=org_id,
        )

        assert rel.source_skill_id == source_id
        assert rel.target_skill_id == target_id
        assert rel.relationship_type == "similar"
        assert rel.weight == 0.75
        assert rel.extra_metadata == {"context": "frontend"}
        assert rel.is_active is True
        assert rel.organization_id == org_id

    def test_model_default_values(self):
        """Test model default values."""
        org_id = uuid4()
        rel = SkillRelationship(
            source_skill_id=uuid4(),
            target_skill_id=uuid4(),
            relationship_type=RelationshipType.RELATED.value,
            organization_id=org_id,
        )

        assert rel.is_active is True  # Default value
        assert rel.weight is None  # Optional field
        assert rel.extra_metadata is None  # Optional field

    def test_model_repr(self):
        """Test model string representation."""
        rel = SkillRelationship(
            source_skill_id=uuid4(),
            target_skill_id=uuid4(),
            relationship_type=RelationshipType.PARENT_CHILD.value,
            organization_id=uuid4(),
        )

        repr_str = repr(rel)
        assert "SkillRelationship" in repr_str
        assert "parent_child" in repr_str


# ============================================================================
# Test Validate Relationship Type Function
# ============================================================================

class TestValidateRelationshipType:
    """Tests for validate_relationship_type function."""

    def test_validate_valid_types(self):
        """Test validation of all valid relationship types."""
        valid_types = ["parent_child", "similar", "prerequisite", "related"]
        for rel_type in valid_types:
            result = validate_relationship_type(rel_type)
            assert result == rel_type

    def test_validate_invalid_type(self):
        """Test validation raises exception for invalid type."""
        with pytest.raises(HTTPException) as exc_info:
            validate_relationship_type("invalid_type")

        assert exc_info.value.status_code == 422
        assert "Invalid relationship type" in exc_info.value.detail

    def test_validate_type_case_sensitive(self):
        """Test that type validation is case-sensitive."""
        with pytest.raises(HTTPException):
            validate_relationship_type("SIMILAR")


# ============================================================================
# Test Create Skill Relationships
# ============================================================================

@pytest.mark.asyncio
class TestCreateSkillRelationships:
    """Tests for creating skill relationships."""

    async def test_create_single_relationship(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating a single skill relationship."""
        org_id = uuid4()
        source = await create_test_skill(test_session, organization_id=org_id)
        target = await create_test_skill(test_session, organization_id=org_id)

        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(source.id),
                        "target_skill_id": str(target.id),
                        "relationship_type": "similar",
                        "weight": 0.8,
                        "is_active": True,
                    }
                ]
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["relationships"]) == 1

        rel = data["relationships"][0]
        assert rel["source_skill_id"] == str(source.id)
        assert rel["target_skill_id"] == str(target.id)
        assert rel["relationship_type"] == "similar"
        assert rel["weight"] == 0.8
        assert rel["is_active"] is True

    async def test_create_batch_relationships(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating multiple skill relationships at once."""
        org_id = uuid4()
        skill1 = await create_test_skill(test_session, organization_id=org_id)
        skill2 = await create_test_skill(test_session, organization_id=org_id)
        skill3 = await create_test_skill(test_session, organization_id=org_id)

        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(skill1.id),
                        "target_skill_id": str(skill2.id),
                        "relationship_type": "similar",
                    },
                    {
                        "source_skill_id": str(skill1.id),
                        "target_skill_id": str(skill3.id),
                        "relationship_type": "related",
                    },
                ]
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["total_count"] == 2

    async def test_create_relationship_invalid_type(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating relationship with invalid type."""
        org_id = uuid4()
        source = await create_test_skill(test_session, organization_id=org_id)
        target = await create_test_skill(test_session, organization_id=org_id)

        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(source.id),
                        "target_skill_id": str(target.id),
                        "relationship_type": "invalid_type",
                    }
                ]
            },
        )

        assert response.status_code == 422

    async def test_create_relationship_invalid_uuid(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating relationship with invalid UUID format."""
        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": "not-a-uuid",
                        "target_skill_id": "also-not-a-uuid",
                        "relationship_type": "similar",
                    }
                ]
            },
        )

        # Should skip invalid relationships, resulting in 0 created
        assert response.status_code == 201
        data = response.json()
        assert data["total_count"] == 0

    async def test_create_relationship_weight_out_of_range(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating relationship with weight outside valid range."""
        org_id = uuid4()
        source = await create_test_skill(test_session, organization_id=org_id)
        target = await create_test_skill(test_session, organization_id=org_id)

        # Weight > 1.0
        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(source.id),
                        "target_skill_id": str(target.id),
                        "relationship_type": "similar",
                        "weight": 1.5,  # Invalid: > 1.0
                    }
                ]
            },
        )

        assert response.status_code == 422

    async def test_create_empty_relationships_list(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating with empty relationships list."""
        response = await client.post(
            "/api/skill-relationships/",
            json={"relationships": []},
        )

        assert response.status_code == 422


# ============================================================================
# Test List Skill Relationships
# ============================================================================

@pytest.mark.asyncio
class TestListSkillRelationships:
    """Tests for listing skill relationships."""

    async def test_list_empty_relationships(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test listing when no relationships exist."""
        response = await client.get("/api/skill-relationships/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["relationships"]) == 0

    async def test_list_relationships_returns_all(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test listing returns all relationships."""
        await create_test_relationship(test_session)
        await create_test_relationship(test_session)

        response = await client.get("/api/skill-relationships/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["relationships"]) == 2

    async def test_filter_by_source_skill_id(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test filtering by source skill ID."""
        rel1 = await create_test_relationship(test_session)
        await create_test_relationship(test_session)  # Different relationship

        response = await client.get(
            f"/api/skill-relationships/?source_skill_id={rel1.source_skill_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["relationships"][0]["source_skill_id"] == str(rel1.source_skill_id)

    async def test_filter_by_target_skill_id(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test filtering by target skill ID."""
        rel1 = await create_test_relationship(test_session)
        await create_test_relationship(test_session)  # Different relationship

        response = await client.get(
            f"/api/skill-relationships/?target_skill_id={rel1.target_skill_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["relationships"][0]["target_skill_id"] == str(rel1.target_skill_id)

    async def test_filter_by_relationship_type(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test filtering by relationship type."""
        await create_test_relationship(
            test_session, relationship_type=RelationshipType.SIMILAR.value
        )
        await create_test_relationship(
            test_session, relationship_type=RelationshipType.RELATED.value
        )

        response = await client.get(
            "/api/skill-relationships/?relationship_type=similar"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["relationships"][0]["relationship_type"] == "similar"

    async def test_filter_by_active_status(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test filtering by active status."""
        await create_test_relationship(test_session, is_active=True)
        await create_test_relationship(test_session, is_active=False)

        response = await client.get("/api/skill-relationships/?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["relationships"][0]["is_active"] is True

    async def test_filter_by_invalid_source_skill_id(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test filtering with invalid source_skill_id format."""
        response = await client.get(
            "/api/skill-relationships/?source_skill_id=invalid-uuid"
        )

        assert response.status_code == 422
        data = response.json()
        assert "Invalid source_skill_id format" in data["detail"]

    async def test_filter_by_invalid_relationship_type(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test filtering with invalid relationship type."""
        response = await client.get(
            "/api/skill-relationships/?relationship_type=invalid"
        )

        assert response.status_code == 422

    async def test_response_includes_skill_names(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test that response includes skill names."""
        source = await create_test_skill(test_session, skill_name="React")
        target = await create_test_skill(test_session, skill_name="Vue.js")
        await create_test_relationship(
            test_session,
            source_skill_id=source.id,
            target_skill_id=target.id,
        )

        response = await client.get("/api/skill-relationships/")

        assert response.status_code == 200
        data = response.json()
        rel = data["relationships"][0]
        assert rel["source_skill_name"] == "React"
        assert rel["target_skill_name"] == "Vue.js"


# ============================================================================
# Test Get Single Skill Relationship
# ============================================================================

@pytest.mark.asyncio
class TestGetSkillRelationship:
    """Tests for getting a single skill relationship."""

    async def test_get_relationship_by_id(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test getting a relationship by ID."""
        rel = await create_test_relationship(test_session)

        response = await client.get(f"/api/skill-relationships/{rel.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(rel.id)
        assert data["relationship_type"] == rel.relationship_type

    async def test_get_relationship_not_found(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test getting a non-existent relationship."""
        fake_id = uuid4()
        response = await client.get(f"/api/skill-relationships/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_relationship_invalid_id(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test getting a relationship with invalid ID format."""
        response = await client.get("/api/skill-relationships/invalid-id")

        assert response.status_code == 422
        data = response.json()
        assert "Invalid relationship ID format" in data["detail"]


# ============================================================================
# Test Update Skill Relationship
# ============================================================================

@pytest.mark.asyncio
class TestUpdateSkillRelationship:
    """Tests for updating skill relationships."""

    async def test_update_relationship_type(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test updating relationship type."""
        rel = await create_test_relationship(
            test_session, relationship_type=RelationshipType.RELATED.value
        )

        response = await client.put(
            f"/api/skill-relationships/{rel.id}",
            json={"relationship_type": "similar"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["relationship_type"] == "similar"

    async def test_update_weight(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test updating relationship weight."""
        rel = await create_test_relationship(test_session, weight=0.5)

        response = await client.put(
            f"/api/skill-relationships/{rel.id}",
            json={"weight": 0.9},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weight"] == 0.9

    async def test_update_active_status(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test updating active status."""
        rel = await create_test_relationship(test_session, is_active=True)

        response = await client.put(
            f"/api/skill-relationships/{rel.id}",
            json={"is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_update_metadata(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test updating extra metadata."""
        rel = await create_test_relationship(test_session, extra_metadata={"old": "data"})

        response = await client.put(
            f"/api/skill-relationships/{rel.id}",
            json={"extra_metadata": {"new": "data", "complex": {"nested": True}}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["extra_metadata"]["new"] == "data"
        assert data["extra_metadata"]["complex"]["nested"] is True

    async def test_update_relationship_not_found(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test updating a non-existent relationship."""
        fake_id = uuid4()
        response = await client.put(
            f"/api/skill-relationships/{fake_id}",
            json={"weight": 0.5},
        )

        assert response.status_code == 404

    async def test_update_invalid_relationship_type(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test updating with invalid relationship type."""
        rel = await create_test_relationship(test_session)

        response = await client.put(
            f"/api/skill-relationships/{rel.id}",
            json={"relationship_type": "invalid"},
        )

        assert response.status_code == 422

    async def test_update_weight_out_of_range(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test updating with weight out of valid range."""
        rel = await create_test_relationship(test_session)

        response = await client.put(
            f"/api/skill-relationships/{rel.id}",
            json={"weight": 1.5},
        )

        assert response.status_code == 422


# ============================================================================
# Test Delete Skill Relationship
# ============================================================================

@pytest.mark.asyncio
class TestDeleteSkillRelationship:
    """Tests for deleting skill relationships."""

    async def test_delete_relationship(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test deleting a relationship."""
        rel = await create_test_relationship(test_session)

        response = await client.delete(f"/api/skill-relationships/{rel.id}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

        # Verify it's actually deleted
        get_response = await client.get(f"/api/skill-relationships/{rel.id}")
        assert get_response.status_code == 404

    async def test_delete_relationship_not_found(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test deleting a non-existent relationship."""
        fake_id = uuid4()
        response = await client.delete(f"/api/skill-relationships/{fake_id}")

        assert response.status_code == 404

    async def test_delete_relationship_invalid_id(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test deleting with invalid ID format."""
        response = await client.delete("/api/skill-relationships/invalid-id")

        assert response.status_code == 422


# ============================================================================
# Test Delete Relationships By Skill
# ============================================================================

@pytest.mark.asyncio
class TestDeleteRelationshipsBySkill:
    """Tests for deleting all relationships for a specific skill."""

    async def test_delete_relationships_by_skill_as_source(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test deleting relationships where skill is source."""
        skill = await create_test_skill(test_session)
        other_skill = await create_test_skill(test_session)

        # Create relationships with skill as source
        await create_test_relationship(
            test_session, source_skill_id=skill.id, target_skill_id=other_skill.id
        )
        await create_test_relationship(
            test_session, source_skill_id=skill.id, target_skill_id=other_skill.id,
            relationship_type=RelationshipType.SIMILAR.value
        )

        response = await client.delete(f"/api/skill-relationships/skill/{skill.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 2

    async def test_delete_relationships_by_skill_as_target(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test deleting relationships where skill is target."""
        skill = await create_test_skill(test_session)
        other_skill = await create_test_skill(test_session)

        # Create relationship with skill as target
        await create_test_relationship(
            test_session, source_skill_id=other_skill.id, target_skill_id=skill.id
        )

        response = await client.delete(f"/api/skill-relationships/skill/{skill.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 1

    async def test_delete_relationships_by_skill_invalid_id(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test deleting relationships with invalid skill ID."""
        response = await client.delete("/api/skill-relationships/skill/invalid-id")

        assert response.status_code == 422


# ============================================================================
# Test List Relationship Types
# ============================================================================

@pytest.mark.asyncio
class TestListRelationshipTypes:
    """Tests for listing relationship types."""

    async def test_list_relationship_types(self, client: AsyncClient):
        """Test listing all relationship types."""
        response = await client.get("/api/skill-relationships/types/")

        assert response.status_code == 200
        data = response.json()
        assert "relationship_types" in data
        assert data["total_count"] == 4

        type_values = [t["value"] for t in data["relationship_types"]]
        assert "parent_child" in type_values
        assert "similar" in type_values
        assert "prerequisite" in type_values
        assert "related" in type_values

    async def test_relationship_types_include_descriptions(
        self, client: AsyncClient
    ):
        """Test that relationship types include descriptions."""
        response = await client.get("/api/skill-relationships/types/")

        assert response.status_code == 200
        data = response.json()

        for rel_type in data["relationship_types"]:
            assert "value" in rel_type
            assert "label" in rel_type
            assert "description" in rel_type
            assert isinstance(rel_type["description"], str)


# ============================================================================
# Test Response Structure
# ============================================================================

@pytest.mark.asyncio
class TestResponseStructure:
    """Tests for response structure."""

    async def test_relationship_response_includes_all_fields(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test that relationship response includes all required fields."""
        source = await create_test_skill(test_session, skill_name="Python")
        target = await create_test_skill(test_session, skill_name="Python3")
        rel = await create_test_relationship(
            test_session,
            source_skill_id=source.id,
            target_skill_id=target.id,
            relationship_type=RelationshipType.SIMILAR.value,
            weight=0.9,
            extra_metadata={"reason": "version variants"},
            is_active=True,
        )

        response = await client.get(f"/api/skill-relationships/{rel.id}")

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        assert "id" in data
        assert "source_skill_id" in data
        assert "target_skill_id" in data
        assert "source_skill_name" in data
        assert "target_skill_name" in data
        assert "relationship_type" in data
        assert "weight" in data
        assert "extra_metadata" in data
        assert "is_active" in data
        assert "organization_id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Check values
        assert data["source_skill_name"] == "Python"
        assert data["target_skill_name"] == "Python3"
        assert data["relationship_type"] == "similar"
        assert data["weight"] == 0.9
        assert data["extra_metadata"]["reason"] == "version variants"
        assert data["is_active"] is True

    async def test_timestamp_format(self, client: AsyncClient, test_session: AsyncSession):
        """Test that timestamps are in ISO 8601 format."""
        rel = await create_test_relationship(test_session)

        response = await client.get(f"/api/skill-relationships/{rel.id}")

        assert response.status_code == 200
        data = response.json()

        # Verify timestamps can be parsed
        created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))

        assert isinstance(created_at, datetime)
        assert isinstance(updated_at, datetime)


# ============================================================================
# Test Edge Cases
# ============================================================================

@pytest.mark.asyncio
class TestEdgeCases:
    """Tests for edge cases."""

    async def test_create_relationship_same_source_and_target(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating relationship with same source and target skill."""
        skill = await create_test_skill(test_session)

        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(skill.id),
                        "target_skill_id": str(skill.id),
                        "relationship_type": "similar",
                    }
                ]
            },
        )

        # This should be allowed (self-referential for some use cases)
        # or rejected depending on business rules
        assert response.status_code in [201, 422]

    async def test_create_duplicate_relationship(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test creating duplicate relationship is handled."""
        org_id = uuid4()
        source = await create_test_skill(test_session, organization_id=org_id)
        target = await create_test_skill(test_session, organization_id=org_id)

        # First creation
        await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(source.id),
                        "target_skill_id": str(target.id),
                        "relationship_type": "similar",
                    }
                ]
            },
        )

        # Duplicate creation
        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(source.id),
                        "target_skill_id": str(target.id),
                        "relationship_type": "similar",
                    }
                ]
            },
        )

        # Should skip duplicate, resulting in 0 new relationships
        assert response.status_code == 201
        data = response.json()
        assert data["total_count"] == 0

    async def test_weight_boundary_values(
        self, client: AsyncClient, test_session: AsyncSession
    ):
        """Test weight at boundary values (0.0 and 1.0)."""
        org_id = uuid4()
        source = await create_test_skill(test_session, organization_id=org_id)
        target = await create_test_skill(test_session, organization_id=org_id)

        # Weight 0.0
        response = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(source.id),
                        "target_skill_id": str(target.id),
                        "relationship_type": "similar",
                        "weight": 0.0,
                    }
                ]
            },
        )
        assert response.status_code == 201
        assert response.json()["relationships"][0]["weight"] == 0.0

        # Weight 1.0
        response2 = await client.post(
            "/api/skill-relationships/",
            json={
                "relationships": [
                    {
                        "source_skill_id": str(source.id),
                        "target_skill_id": str(target.id),
                        "relationship_type": "related",
                        "weight": 1.0,
                    }
                ]
            },
        )
        assert response2.status_code == 201
        assert response2.json()["relationships"][0]["weight"] == 1.0


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
