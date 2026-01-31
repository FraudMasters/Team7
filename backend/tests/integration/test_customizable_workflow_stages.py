"""
End-to-end integration test for customizable workflow stages functionality.

This test verifies:
1. Creating custom workflow stages
2. Updating workflow stages (renaming, reordering, changing colors)
3. Deleting workflow stages
4. Listing workflow stages with filters
5. Verifying stages appear correctly in candidate queries
6. Verifying stage customization is reflected throughout the system
"""
import pytest
import uuid
from datetime import datetime

from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.hiring_stage import HiringStage, HiringStageName
from models.workflow_stage_config import WorkflowStageConfig
from models.analytics_event import AnalyticsEvent, AnalyticsEventType


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_custom_stages.db"


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
async def test_create_custom_workflow_stage(client: AsyncClient, test_db: AsyncSession):
    """
    Test creating a custom workflow stage 'Phone Screen' between Applied and Screening.

    Verification steps:
    1. Create custom stage 'Phone Screen' with order 1.5 (between Applied=0 and Screening=2)
    2. Verify stage is created with correct attributes
    3. Verify stage appears in list endpoint
    4. Verify stage can be retrieved by ID
    """
    print("\n=== Test: Create Custom Workflow Stage ===\n")

    organization_id = "test-org-001"

    # Step 1: Create custom stage 'Phone Screen'
    print("Step 1: Creating custom stage 'Phone Screen'...")
    create_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Phone Screen",
            "stage_order": 1,
            "is_default": False,
            "is_active": True,
            "color": "#8B5CF6",
            "description": "Initial phone screening with recruiter"
        }
    )

    assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}: {create_response.text}"
    stage_data = create_response.json()

    print(f"✓ Created custom stage:")
    print(f"  ID: {stage_data['id']}")
    print(f"  Name: {stage_data['stage_name']}")
    print(f"  Order: {stage_data['stage_order']}")
    print(f"  Color: {stage_data['color']}")
    print(f"  Description: {stage_data['description']}")

    # Verify attributes
    assert stage_data['stage_name'] == "Phone Screen"
    assert stage_data['stage_order'] == 1
    assert stage_data['color'] == "#8B5CF6"
    assert stage_data['is_active'] == True
    assert stage_data['is_default'] == False
    assert stage_data['description'] == "Initial phone screening with recruiter"
    assert 'id' in stage_data

    stage_id = stage_data['id']

    # Step 2: Verify stage appears in list endpoint
    print("\nStep 2: Verifying stage appears in list endpoint...")
    list_response = await client.get(
        f"/api/workflow-stages/?organization_id={organization_id}"
    )

    assert list_response.status_code == 200
    list_data = list_response.json()

    print(f"✓ Retrieved {list_data['total_count']} stages for organization")

    # Find our custom stage
    phone_screen_stage = next(
        (s for s in list_data['stages'] if s['id'] == stage_id),
        None
    )
    assert phone_screen_stage is not None, "Custom stage not found in list"
    print(f"✓ Custom stage found in list: {phone_screen_stage['stage_name']}")

    # Step 3: Verify stage can be retrieved by ID
    print("\nStep 3: Verifying stage can be retrieved by ID...")
    get_response = await client.get(f"/api/workflow-stages/{stage_id}")

    assert get_response.status_code == 200
    get_data = get_response.json()

    assert get_data['id'] == stage_id
    assert get_data['stage_name'] == "Phone Screen"
    print(f"✓ Stage retrieved by ID: {get_data['stage_name']}")

    print("\n✅ Test PASSED: Custom workflow stage created successfully")


@pytest.mark.asyncio
async def test_update_workflow_stage_rename(client: AsyncClient, test_db: AsyncSession):
    """
    Test renaming a workflow stage from 'Technical' to 'Technical Interview'.

    Verification steps:
    1. Create a stage named 'Technical'
    2. Update the stage name to 'Technical Interview'
    3. Verify the rename is reflected in GET endpoints
    4. Verify the rename is reflected in database
    """
    print("\n=== Test: Update Workflow Stage (Rename) ===\n")

    organization_id = "test-org-002"

    # Step 1: Create stage named 'Technical'
    print("Step 1: Creating stage named 'Technical'...")
    create_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Technical",
            "stage_order": 3,
            "is_default": False,
            "is_active": True,
            "color": "#3B82F6",
            "description": "Technical assessment"
        }
    )

    assert create_response.status_code == 201
    stage_data = create_response.json()
    stage_id = stage_data['id']

    print(f"✓ Created stage: {stage_data['stage_name']}")

    # Step 2: Rename to 'Technical Interview'
    print("\nStep 2: Renaming stage to 'Technical Interview'...")
    update_response = await client.put(
        f"/api/workflow-stages/{stage_id}",
        json={
            "stage_name": "Technical Interview",
            "description": "Technical interview with engineering team"
        }
    )

    assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
    updated_data = update_response.json()

    print(f"✓ Renamed stage:")
    print(f"  Old name: Technical")
    print(f"  New name: {updated_data['stage_name']}")
    print(f"  New description: {updated_data['description']}")

    # Verify rename
    assert updated_data['stage_name'] == "Technical Interview"
    assert updated_data['description'] == "Technical interview with engineering team"
    assert updated_data['id'] == stage_id

    # Step 3: Verify rename reflected in GET endpoint
    print("\nStep 3: Verifying rename reflected in GET endpoint...")
    get_response = await client.get(f"/api/workflow-stages/{stage_id}")

    assert get_response.status_code == 200
    get_data = get_response.json()

    assert get_data['stage_name'] == "Technical Interview"
    print(f"✓ Rename confirmed via GET endpoint: {get_data['stage_name']}")

    # Step 4: Verify rename reflected in list
    print("\nStep 4: Verifying rename reflected in list endpoint...")
    list_response = await client.get(
        f"/api/workflow-stages/?organization_id={organization_id}"
    )

    assert list_response.status_code == 200
    list_data = list_response.json()

    technical_stage = next(
        (s for s in list_data['stages'] if s['id'] == stage_id),
        None
    )
    assert technical_stage is not None
    assert technical_stage['stage_name'] == "Technical Interview"
    print(f"✓ Rename confirmed in list: {technical_stage['stage_name']}")

    # Step 5: Verify rename reflected in database
    print("\nStep 5: Verifying rename reflected in database...")
    result = await test_db.execute(
        select(WorkflowStageConfig).where(WorkflowStageConfig.id == uuid.UUID(stage_id))
    )
    db_stage = result.scalar_one_or_none()

    assert db_stage is not None
    assert db_stage.stage_name == "Technical Interview"
    print(f"✓ Rename confirmed in database: {db_stage.stage_name}")

    print("\n✅ Test PASSED: Workflow stage renamed successfully")


@pytest.mark.asyncio
async def test_delete_workflow_stage(client: AsyncClient, test_db: AsyncSession):
    """
    Test deleting a workflow stage and verifying it's removed from the system.

    Verification steps:
    1. Create a custom stage
    2. Delete the stage
    3. Verify stage no longer appears in list endpoint
    4. Verify GET endpoint returns 404
    5. Verify stage removed from database
    """
    print("\n=== Test: Delete Workflow Stage ===\n")

    organization_id = "test-org-003"

    # Step 1: Create a custom stage
    print("Step 1: Creating custom stage to delete...")
    create_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Stage To Delete",
            "stage_order": 5,
            "is_default": False,
            "is_active": True,
            "color": "#EF4444",
            "description": "This stage will be deleted"
        }
    )

    assert create_response.status_code == 201
    stage_data = create_response.json()
    stage_id = stage_data['id']

    print(f"✓ Created stage: {stage_data['stage_name']} (ID: {stage_id})")

    # Verify it exists
    list_before = await client.get(f"/api/workflow-stages/?organization_id={organization_id}")
    assert list_before.status_code == 200
    count_before = list_before.json()['total_count']
    print(f"✓ Stage count before deletion: {count_before}")

    # Step 2: Delete the stage
    print("\nStep 2: Deleting stage...")
    delete_response = await client.delete(f"/api/workflow-stages/{stage_id}")

    assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
    delete_data = delete_response.json()

    print(f"✓ Stage deleted: {delete_data['message']}")

    # Step 3: Verify stage no longer appears in list
    print("\nStep 3: Verifying stage removed from list endpoint...")
    list_after = await client.get(f"/api/workflow-stages/?organization_id={organization_id}")

    assert list_after.status_code == 200
    list_data = list_after.json()

    deleted_stage = next(
        (s for s in list_data['stages'] if s['id'] == stage_id),
        None
    )
    assert deleted_stage is None, "Deleted stage still appears in list"
    count_after = list_data['total_count']
    print(f"✓ Stage count after deletion: {count_after}")
    assert count_after == count_before - 1, "Stage count didn't decrease"

    # Step 4: Verify GET endpoint returns 404
    print("\nStep 4: Verifying GET endpoint returns 404...")
    get_response = await client.get(f"/api/workflow-stages/{stage_id}")

    assert get_response.status_code == 404
    print(f"✓ GET endpoint correctly returns 404: {get_response.json()['detail']}")

    # Step 5: Verify stage removed from database
    print("\nStep 5: Verifying stage removed from database...")
    result = await test_db.execute(
        select(WorkflowStageConfig).where(WorkflowStageConfig.id == uuid.UUID(stage_id))
    )
    db_stage = result.scalar_one_or_none()

    assert db_stage is None, "Stage still exists in database"
    print(f"✓ Stage confirmed deleted from database")

    print("\n✅ Test PASSED: Workflow stage deleted successfully")


@pytest.mark.asyncio
async def test_workflow_stage_ordering_and_filters(client: AsyncClient, test_db: AsyncSession):
    """
    Test that workflow stages can be ordered and filtered correctly.

    Verification steps:
    1. Create multiple stages with different orders
    2. Verify stages are returned in correct order
    3. Test filtering by is_active
    4. Test filtering by is_default
    5. Verify ordering is preserved in database
    """
    print("\n=== Test: Workflow Stage Ordering and Filters ===\n")

    organization_id = "test-org-004"

    # Step 1: Create multiple stages
    print("Step 1: Creating multiple stages with different orders...")
    stages_to_create = [
        {"stage_name": "Stage A", "stage_order": 1, "is_active": True, "is_default": False, "color": "#3B82F6"},
        {"stage_name": "Stage B", "stage_order": 2, "is_active": True, "is_default": True, "color": "#10B981"},
        {"stage_name": "Stage C", "stage_order": 3, "is_active": False, "is_default": False, "color": "#F59E0B"},
        {"stage_name": "Stage D", "stage_order": 4, "is_active": True, "is_default": False, "color": "#EF4444"},
    ]

    stage_ids = []
    for stage_config in stages_to_create:
        response = await client.post(
            "/api/workflow-stages/",
            json={
                "organization_id": organization_id,
                **stage_config,
                "description": f"Description for {stage_config['stage_name']}"
            }
        )
        assert response.status_code == 201
        stage_data = response.json()
        stage_ids.append(stage_data['id'])
        print(f"  ✓ Created {stage_data['stage_name']} (order: {stage_data['stage_order']}, active: {stage_data['is_active']})")

    # Step 2: Verify stages are returned in correct order
    print("\nStep 2: Verifying stages are returned in order...")
    list_response = await client.get(f"/api/workflow-stages/?organization_id={organization_id}")

    assert list_response.status_code == 200
    list_data = list_response.json()

    stages = list_data['stages']
    print(f"✓ Retrieved {len(stages)} stages")

    # Verify ordering
    for i in range(len(stages) - 1):
        assert stages[i]['stage_order'] <= stages[i+1]['stage_order'], \
            f"Stages not in order: {stages[i]['stage_order']} > {stages[i+1]['stage_order']}"

    print(f"✓ Stages correctly ordered:")
    for stage in stages:
        print(f"  {stage['stage_order']}: {stage['stage_name']}")

    # Step 3: Test filtering by is_active
    print("\nStep 3: Testing filter by is_active=True...")
    active_response = await client.get(
        f"/api/workflow-stages/?organization_id={organization_id}&is_active=true"
    )

    assert active_response.status_code == 200
    active_data = active_response.json()

    print(f"✓ Active stages: {active_data['total_count']}")
    for stage in active_data['stages']:
        assert stage['is_active'] == True, "Inactive stage in active filter"
        print(f"  - {stage['stage_name']}")

    # Step 4: Test filtering by is_default
    print("\nStep 4: Testing filter by is_default=true...")
    default_response = await client.get(
        f"/api/workflow-stages/?organization_id={organization_id}&is_default=true"
    )

    assert default_response.status_code == 200
    default_data = default_response.json()

    print(f"✓ Default stages: {default_data['total_count']}")
    for stage in default_data['stages']:
        assert stage['is_default'] == True, "Non-default stage in default filter"
        print(f"  - {stage['stage_name']}")

    # Step 5: Verify combined filters
    print("\nStep 5: Testing combined filters (active + default)...")
    combined_response = await client.get(
        f"/api/workflow-stages/?organization_id={organization_id}&is_active=true&is_default=true"
    )

    assert combined_response.status_code == 200
    combined_data = combined_response.json()

    print(f"✓ Active + Default stages: {combined_data['total_count']}")
    for stage in combined_data['stages']:
        assert stage['is_active'] == True and stage['is_default'] == True
        print(f"  - {stage['stage_name']}")

    print("\n✅ Test PASSED: Workflow stage ordering and filters working correctly")


@pytest.mark.asyncio
async def test_workflow_stage_update_all_fields(client: AsyncClient, test_db: AsyncSession):
    """
    Test updating all fields of a workflow stage.

    Verification steps:
    1. Create a stage with initial values
    2. Update all fields (name, order, color, description, active status)
    3. Verify all fields are updated correctly
    4. Verify updated_at timestamp changed
    """
    print("\n=== Test: Update All Workflow Stage Fields ===\n")

    organization_id = "test-org-005"

    # Step 1: Create initial stage
    print("Step 1: Creating initial stage...")
    create_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Original Name",
            "stage_order": 1,
            "is_default": False,
            "is_active": True,
            "color": "#3B82F6",
            "description": "Original description"
        }
    )

    assert create_response.status_code == 201
    stage_data = create_response.json()
    stage_id = stage_data['id']
    original_updated_at = stage_data['updated_at']

    print(f"✓ Created stage: {stage_data['stage_name']}")
    print(f"  Updated at: {original_updated_at}")

    # Small delay to ensure updated_at timestamp differs
    import asyncio
    await asyncio.sleep(0.1)

    # Step 2: Update all fields
    print("\nStep 2: Updating all fields...")
    update_response = await client.put(
        f"/api/workflow-stages/{stage_id}",
        json={
            "stage_name": "Updated Name",
            "stage_order": 5,
            "is_default": True,
            "is_active": False,
            "color": "#F59E0B",
            "description": "Updated description"
        }
    )

    assert update_response.status_code == 200
    updated_data = update_response.json()

    print(f"✓ Updated all fields:")
    print(f"  Name: {stage_data['stage_name']} → {updated_data['stage_name']}")
    print(f"  Order: {stage_data['stage_order']} → {updated_data['stage_order']}")
    print(f"  Default: {stage_data['is_default']} → {updated_data['is_default']}")
    print(f"  Active: {stage_data['is_active']} → {updated_data['is_active']}")
    print(f"  Color: {stage_data['color']} → {updated_data['color']}")
    print(f"  Description: {stage_data['description']} → {updated_data['description']}")

    # Step 3: Verify all fields updated
    print("\nStep 3: Verifying all fields updated correctly...")
    assert updated_data['stage_name'] == "Updated Name"
    assert updated_data['stage_order'] == 5
    assert updated_data['is_default'] == True
    assert updated_data['is_active'] == False
    assert updated_data['color'] == "#F59E0B"
    assert updated_data['description'] == "Updated description"
    assert updated_data['id'] == stage_id

    # Verify updated_at changed
    new_updated_at = updated_data['updated_at']
    assert new_updated_at != original_updated_at, "updated_at timestamp should change"
    print(f"✓ Updated at: {original_updated_at} → {new_updated_at}")

    # Step 4: Verify in database
    print("\nStep 4: Verifying updates in database...")
    result = await test_db.execute(
        select(WorkflowStageConfig).where(WorkflowStageConfig.id == uuid.UUID(stage_id))
    )
    db_stage = result.scalar_one_or_none()

    assert db_stage is not None
    assert db_stage.stage_name == "Updated Name"
    assert db_stage.stage_order == 5
    assert db_stage.is_default == True
    assert db_stage.is_active == False
    assert db_stage.color == "#F59E0B"
    assert db_stage.description == "Updated description"
    print(f"✓ All fields verified in database")

    print("\n✅ Test PASSED: All workflow stage fields updated successfully")


@pytest.mark.asyncio
async def test_duplicate_stage_name_prevention(client: AsyncClient, test_db: AsyncSession):
    """
    Test that duplicate stage names are prevented within an organization.

    Verification steps:
    1. Create a stage with name 'Unique Stage'
    2. Attempt to create another stage with same name
    3. Verify second creation fails with 409 Conflict
    4. Attempt to rename existing stage to duplicate name
    5. Verify rename fails with 409 Conflict
    """
    print("\n=== Test: Duplicate Stage Name Prevention ===\n")

    organization_id = "test-org-006"

    # Step 1: Create initial stage
    print("Step 1: Creating initial stage 'Unique Stage'...")
    create_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Unique Stage",
            "stage_order": 1,
            "is_active": True,
            "color": "#3B82F6"
        }
    )

    assert create_response.status_code == 201
    first_stage = create_response.json()
    print(f"✓ Created stage: {first_stage['stage_name']} (ID: {first_stage['id']})")

    # Step 2: Attempt to create duplicate
    print("\nStep 2: Attempting to create duplicate stage name...")
    duplicate_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Unique Stage",
            "stage_order": 2,
            "is_active": True,
            "color": "#10B981"
        }
    )

    assert duplicate_response.status_code == 409, f"Expected 409 Conflict, got {duplicate_response.status_code}"
    print(f"✓ Duplicate creation prevented: {duplicate_response.json()['detail']}")

    # Step 3: Create another stage
    print("\nStep 3: Creating second stage 'Another Stage'...")
    second_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Another Stage",
            "stage_order": 2,
            "is_active": True,
            "color": "#10B981"
        }
    )

    assert second_response.status_code == 201
    second_stage = second_response.json()
    print(f"✓ Created second stage: {second_stage['stage_name']}")

    # Step 4: Attempt to rename to duplicate
    print("\nStep 4: Attempting to rename second stage to 'Unique Stage'...")
    rename_response = await client.put(
        f"/api/workflow-stages/{second_stage['id']}",
        json={"stage_name": "Unique Stage"}
    )

    assert rename_response.status_code == 409, f"Expected 409 Conflict, got {rename_response.status_code}"
    print(f"✓ Rename to duplicate prevented: {rename_response.json()['detail']}")

    # Verify original stage unchanged
    get_response = await client.get(f"/api/workflow-stages/{second_stage['id']}")
    assert get_response.status_code == 200
    unchanged_stage = get_response.json()
    assert unchanged_stage['stage_name'] == "Another Stage"
    print(f"✓ Original stage unchanged: {unchanged_stage['stage_name']}")

    print("\n✅ Test PASSED: Duplicate stage names prevented correctly")


@pytest.mark.asyncio
async def test_custom_stage_with_candidates(client: AsyncClient, test_db: AsyncSession):
    """
    Test that custom stages work with candidate assignments.

    Verification steps:
    1. Create custom stage
    2. Create candidate (resume)
    3. Move candidate to custom stage
    4. Verify candidate appears in custom stage query
    5. Verify audit trail logged for custom stage movement
    """
    print("\n=== Test: Custom Stage with Candidates ===\n")

    organization_id = "test-org-007"

    # Step 1: Create custom stage
    print("Step 1: Creating custom stage 'Custom Interview'...")
    stage_response = await client.post(
        "/api/workflow-stages/",
        json={
            "organization_id": organization_id,
            "stage_name": "Custom Interview",
            "stage_order": 10,
            "is_active": True,
            "color": "#8B5CF6",
            "description": "Custom interview stage"
        }
    )

    assert stage_response.status_code == 201
    custom_stage = stage_response.json()
    custom_stage_id = custom_stage['id']
    print(f"✓ Created custom stage: {custom_stage['stage_name']} (ID: {custom_stage_id})")

    # Step 2: Create candidate
    print("\nStep 2: Creating candidate...")
    test_resume = Resume(
        filename="test_candidate_custom_stage.pdf",
        file_path="/tmp/test_candidate_custom_stage.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Test resume content",
        language="en"
    )
    test_db.add(test_resume)
    await test_db.commit()
    await test_db.refresh(test_resume)

    candidate_id = str(test_resume.id)
    print(f"✓ Created candidate: {candidate_id}")

    # Step 3: Move candidate to custom stage
    print("\nStep 3: Moving candidate to custom stage...")
    move_response = await client.put(
        f"/api/candidates/{candidate_id}/stage",
        json={
            "stage_id": custom_stage_id,
            "notes": "Moved to custom stage"
        }
    )

    assert move_response.status_code == 200
    move_data = move_response.json()
    print(f"✓ Moved candidate to custom stage:")
    print(f"  Previous stage: {move_data['previous_stage']}")
    print(f"  New stage: {move_data['new_stage']}")

    # Step 4: Verify candidate appears in custom stage query
    print("\nStep 4: Verifying candidate appears in custom stage query...")
    candidates_response = await client.get(
        f"/api/candidates/?stage_id={custom_stage_id}"
    )

    assert candidates_response.status_code == 200
    candidates_data = candidates_response.json()

    assert len(candidates_data) >= 1, "Expected at least one candidate in custom stage"
    candidate_in_custom = next(
        (c for c in candidates_data if c['id'] == candidate_id),
        None
    )
    assert candidate_in_custom is not None, "Candidate not found in custom stage"
    print(f"✓ Candidate found in custom stage: {candidate_in_custom['filename']}")

    # Step 5: Verify audit trail
    print("\nStep 5: Verifying audit trail logged...")
    analytics_query = select(AnalyticsEvent).where(
        and_(
            AnalyticsEvent.entity_id == test_resume.id,
            AnalyticsEvent.event_type == AnalyticsEventType.STAGE_CHANGED
        )
    ).order_by(AnalyticsEvent.created_at.desc())

    result = await test_db.execute(analytics_query)
    analytics_events = result.scalars().all()

    assert len(analytics_events) >= 1, "Expected analytics event for custom stage movement"
    latest_event = analytics_events[0]

    print(f"✓ Analytics event logged:")
    print(f"  Event type: {latest_event.event_type}")
    print(f"  New stage: {latest_event.event_data.get('new_stage')}")
    print(f"  Notes: {latest_event.event_data.get('notes')}")

    print("\n✅ Test PASSED: Custom stages work correctly with candidates")


if __name__ == "__main__":
    print("This test requires pytest with async support.")
    print("Run with: pytest backend/tests/integration/test_customizable_workflow_stages.py -v")
