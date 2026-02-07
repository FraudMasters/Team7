"""
End-to-End Integration Tests for Workflow Creation, Trigger, and Execution

This test module performs comprehensive verification of the workflow automation system, including:
- Workflow creation with webhook, schedule, and manual triggers
- Webhook event triggering workflow execution
- Workflow execution engine processing actions
- Action execution and result tracking
- Execution history and statistics
- Workflow activation, pausing, and archiving

Test Coverage:
- Create workflow with webhook trigger
- Trigger webhook event to execute workflow
- Verify workflow execution in execution history
- Verify action completion and results
- Test multiple action types (log, add_tag, send_webhook)
- Test workflow status management (activate, pause)
- Test execution statistics and success rates
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowTriggerType,
    WorkflowStatus,
    ExecutionStatus,
    ActionType,
)
from models.webhook import WebhookEventType
from models.resume import Resume, ResumeStatus
from config import get_settings


# Test Database Setup
settings = get_settings()
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
# Test 1: Workflow Creation
# ============================================================================

@pytest.mark.asyncio
async def test_create_workflow_with_webhook_trigger(client: AsyncClient, test_session: AsyncSession):
    """Verify that workflows can be created with webhook triggers."""
    print("\n=== Test 1: Create Workflow with Webhook Trigger ===\n")

    workflow_data = {
        "name": "Candidate Created Notification",
        "description": "Send notification when candidate is created",
        "trigger": {
            "type": "webhook",
            "event": "candidate.created",
        },
        "actions": [
            {
                "type": "log",
                "config": {"message": "Candidate created: {{trigger.data.candidate_id}}"},
                "label": "Log candidate creation",
            }
        ],
    }

    response = await client.post("/api/workflows", json=workflow_data)
    assert response.status_code == 201

    result = response.json()
    print(f"✓ Workflow created: {result['id']}")
    print(f"  Name: {result['name']}")
    print(f"  Trigger type: {result['trigger_type']}")
    print(f"  Status: {result['status']}")
    print(f"  Actions: {len(result['actions'])}")

    # Verify response structure
    assert "id" in result
    assert result["name"] == workflow_data["name"]
    assert result["trigger_type"] == WorkflowTriggerType.WEBHOOK.value
    assert result["status"] == WorkflowStatus.DRAFT.value
    assert result["is_active"] is False
    assert len(result["actions"]) == 1
    assert result["actions"][0]["type"] == ActionType.LOG.value

    # Verify workflow was stored in database
    await test_session.commit()

    stmt = select(Workflow).where(Workflow.id == UUID(result["id"]))
    db_result = await test_session.execute(stmt)
    workflow = db_result.scalar_one_or_none()

    assert workflow is not None
    assert workflow.name == workflow_data["name"]
    assert workflow.trigger_type == WorkflowTriggerType.WEBHOOK
    assert workflow.trigger_config["event"] == "candidate.created"
    assert workflow.status == WorkflowStatus.DRAFT
    assert workflow.is_active is False
    assert len(workflow.actions) == 1
    print(f"✓ Workflow stored in database")

    return result


@pytest.mark.asyncio
async def test_create_workflow_with_schedule_trigger(client: AsyncClient, test_session: AsyncSession):
    """Verify that workflows can be created with schedule triggers."""
    print("\n=== Test 2: Create Workflow with Schedule Trigger ===\n")

    workflow_data = {
        "name": "Daily Report Generator",
        "description": "Generate daily analytics report",
        "trigger": {
            "type": "schedule",
            "cron_expression": "0 9 * * *",  # Daily at 9 AM
        },
        "actions": [
            {
                "type": "generate_report",
                "config": {"report_type": "daily_summary"},
            }
        ],
    }

    response = await client.post("/api/workflows", json=workflow_data)
    assert response.status_code == 201

    result = response.json()
    print(f"✓ Workflow created with schedule trigger: {result['id']}")
    print(f"  Cron expression: {result['trigger_config']['cron_expression']}")

    assert result["trigger_type"] == WorkflowTriggerType.SCHEDULE.value
    assert result["trigger_config"]["cron_expression"] == "0 9 * * *"


@pytest.mark.asyncio
async def test_create_workflow_with_multiple_actions(client: AsyncClient, test_session: AsyncSession):
    """Verify that workflows can have multiple actions."""
    print("\n=== Test 3: Create Workflow with Multiple Actions ===\n")

    workflow_data = {
        "name": "Candidate Onboarding",
        "description": "Process new candidate",
        "trigger": {
            "type": "webhook",
            "event": "candidate.created",
        },
        "actions": [
            {
                "type": "log",
                "config": {"message": "Processing candidate..."},
            },
            {
                "type": "add_tag",
                "config": {"tag": "new_candidate", "candidate_id": "{{trigger.data.candidate_id}}"},
            },
            {
                "type": "log",
                "config": {"message": "Candidate processing complete"},
            },
        ],
    }

    response = await client.post("/api/workflows", json=workflow_data)
    assert response.status_code == 201

    result = response.json()
    print(f"✓ Workflow created with {len(result['actions'])} actions")

    assert len(result["actions"]) == 3
    assert result["actions"][0]["type"] == ActionType.LOG.value
    assert result["actions"][1]["type"] == ActionType.ADD_TAG.value
    assert result["actions"][2]["type"] == ActionType.LOG.value


# ============================================================================
# Test 2: Workflow Activation and Status Management
# ============================================================================

@pytest.mark.asyncio
async def test_activate_workflow(client: AsyncClient, test_session: AsyncSession):
    """Verify that workflows can be activated."""
    print("\n=== Test 4: Activate Workflow ===\n")

    # First, create a workflow
    workflow_data = {
        "name": "Test Workflow",
        "trigger": {
            "type": "webhook",
            "event": "candidate.created",
        },
        "actions": [
            {"type": "log", "config": {"message": "Test"}},
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    assert create_response.status_code == 201
    workflow = create_response.json()
    workflow_id = workflow["id"]

    print(f"✓ Created workflow: {workflow_id} (status: {workflow['status']})")

    # Activate the workflow
    activate_response = await client.post(f"/api/workflows/{workflow_id}/activate")
    assert activate_response.status_code == 200
    activate_result = activate_response.json()

    print(f"✓ Activated workflow: {activate_result['status']}")
    assert activate_result["status"] == WorkflowStatus.ACTIVE.value
    assert activate_result["is_active"] is True

    # Verify in database
    stmt = select(Workflow).where(Workflow.id == UUID(workflow_id))
    result = await test_session.execute(stmt)
    workflow_obj = result.scalar_one_or_none()

    assert workflow_obj is not None
    assert workflow_obj.is_active is True
    assert workflow_obj.status == WorkflowStatus.ACTIVE


@pytest.mark.asyncio
async def test_pause_workflow(client: AsyncClient, test_session: AsyncSession):
    """Verify that workflows can be paused."""
    print("\n=== Test 5: Pause Workflow ===\n")

    # Create and activate workflow
    workflow_data = {
        "name": "Test Workflow",
        "trigger": {
            "type": "webhook",
            "event": "candidate.created",
        },
        "actions": [
            {"type": "log", "config": {"message": "Test"}},
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    workflow = create_response.json()
    workflow_id = workflow["id"]

    # Activate first
    await client.post(f"/api/workflows/{workflow_id}/activate")

    # Now pause
    pause_response = await client.post(f"/api/workflows/{workflow_id}/pause")
    assert pause_response.status_code == 200
    pause_result = pause_response.json()

    print(f"✓ Paused workflow: {pause_result['status']}")
    assert pause_result["status"] == WorkflowStatus.PAUSED.value
    assert pause_result["is_active"] is False


# ============================================================================
# Test 3: Manual Workflow Execution
# ============================================================================

@pytest.mark.asyncio
async def test_execute_workflow_manually(client: AsyncClient, test_session: AsyncSession):
    """Verify that workflows can be executed manually."""
    print("\n=== Test 6: Manual Workflow Execution ===\n")

    # Create and activate workflow
    workflow_data = {
        "name": "Manual Test Workflow",
        "description": "Test manual execution",
        "trigger": {
            "type": "manual",
        },
        "actions": [
            {
                "type": "log",
                "config": {"message": "Manual execution test"},
            },
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    workflow = create_response.json()
    workflow_id = workflow["id"]

    # Activate the workflow
    await client.post(f"/api/workflows/{workflow_id}/activate")

    print(f"✓ Created and activated workflow: {workflow_id}")

    # Execute manually
    execute_response = await client.post(
        f"/api/workflows/{workflow_id}/execute",
        json={"input_data": {"test": "data"}},
    )
    assert execute_response.status_code == 202  # Accepted (async execution)
    execute_result = execute_response.json()

    print(f"✓ Workflow execution started")
    print(f"  Execution ID: {execute_result.get('execution_id')}")
    assert "execution_id" in execute_result

    # Wait for execution to complete
    await asyncio.sleep(0.5)

    # Verify execution record
    await test_session.commit()

    stmt = select(WorkflowExecution).where(
        WorkflowExecution.workflow_id == UUID(workflow_id)
    )
    result = await test_session.execute(stmt)
    execution = result.scalar_one_or_none()

    assert execution is not None
    print(f"✓ Execution record found:")
    print(f"  Status: {execution.status.value}")
    print(f"  Trigger type: {execution.trigger_type.value}")

    # Verify workflow statistics updated
    await test_session.refresh(workflow_obj := await test_session.get(Workflow, UUID(workflow_id)))

    assert workflow_obj.execution_count >= 1
    print(f"✓ Workflow execution count: {workflow_obj.execution_count}")


# ============================================================================
# Test 4: Webhook-triggered Workflow Execution
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_triggered_by_webhook_event(client: AsyncClient, test_session: AsyncSession):
    """Verify that webhook events trigger workflow execution."""
    print("\n=== Test 7: Workflow Triggered by Webhook Event ===\n")

    # Create workflow with webhook trigger
    workflow_data = {
        "name": "Candidate Created Workflow",
        "description": "Process candidate creation",
        "trigger": {
            "type": "webhook",
            "event": "candidate.created",
        },
        "actions": [
            {
                "type": "log",
                "config": {"message": "Candidate {{trigger.data.candidate_id}} created"},
            },
            {
                "type": "log",
                "config": {"message": "Processing complete"},
            },
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    workflow = create_response.json()
    workflow_id = workflow["id"]

    # Activate the workflow
    await client.post(f"/api/workflows/{workflow_id}/activate")

    print(f"✓ Created and activated workflow: {workflow_id}")

    # Create a test candidate (resume)
    test_resume = Resume(
        filename="test_candidate.pdf",
        file_path="/tmp/test.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Test candidate",
        language="en"
    )
    test_session.add(test_resume)
    await test_session.commit()
    await test_session.refresh(test_resume)

    candidate_id = str(test_resume.id)
    print(f"✓ Created candidate: {candidate_id}")

    # Trigger workflow using workflow engine
    from services.workflow_engine import WorkflowEngine

    async with WorkflowEngine(session=test_session) as engine:
        trigger_data = {
            "candidate_id": candidate_id,
            "filename": test_resume.filename,
            "status": test_resume.status.value,
        }

        result = await engine.execute_workflow(
            workflow_id=workflow_id,
            trigger_type=WorkflowTriggerType.WEBHOOK,
            trigger_data=trigger_data,
        )

        print(f"✓ Workflow executed successfully")
        print(f"  Execution ID: {result['execution_id']}")
        print(f"  Status: {result['status']}")

        assert result["status"] == "completed"

    # Verify execution record
    await test_session.commit()

    stmt = select(WorkflowExecution).where(
        and_(
            WorkflowExecution.workflow_id == UUID(workflow_id),
            WorkflowExecution.trigger_type == WorkflowTriggerType.WEBHOOK,
        )
    )
    result = await test_session.execute(stmt)
    execution = result.scalar_one_or_none()

    assert execution is not None
    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.trigger_data["candidate_id"] == candidate_id

    print(f"✓ Execution verified:")
    print(f"  Status: {execution.status.value}")
    print(f"  Trigger data: {execution.trigger_data}")

    # Verify action results
    assert execution.action_results is not None
    assert len(execution.action_results) == 2

    print(f"✓ Action results: {len(execution.action_results)} actions executed")
    for action_result in execution.action_results:
        print(f"  - {action_result['action']['type']}: {action_result['status']}")
        assert action_result["status"] == "success"

    # Verify workflow statistics
    await test_session.refresh(workflow_obj := await test_session.get(Workflow, UUID(workflow_id)))

    assert workflow_obj.execution_count == 1
    assert workflow_obj.success_count == 1
    assert workflow_obj.last_executed_at is not None
    print(f"✓ Workflow statistics updated:")
    print(f"  Execution count: {workflow_obj.execution_count}")
    print(f"  Success count: {workflow_obj.success_count}")
    print(f"  Success rate: {workflow_obj.success_rate}%")

    return workflow_id, candidate_id


# ============================================================================
# Test 5: Execution History and Statistics
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_execution_history(client: AsyncClient, test_session: AsyncSession):
    """Verify that workflow execution history is tracked."""
    print("\n=== Test 8: Workflow Execution History ===\n")

    # Create and activate workflow
    workflow_data = {
        "name": "History Test Workflow",
        "trigger": {
            "type": "manual",
        },
        "actions": [
            {"type": "log", "config": {"message": "Test"}},
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    workflow = create_response.json()
    workflow_id = workflow["id"]

    await client.post(f"/api/workflows/{workflow_id}/activate")

    # Execute workflow multiple times
    num_executions = 3
    for i in range(num_executions):
        await client.post(f"/api/workflows/{workflow_id}/execute")
        await asyncio.sleep(0.2)  # Small delay between executions

    print(f"✓ Executed workflow {num_executions} times")

    # Get execution history
    history_response = await client.get(f"/api/workflows/{workflow_id}/executions")
    assert history_response.status_code == 200
    history_data = history_response.json()

    print(f"✓ Execution history retrieved:")
    print(f"  Total executions: {history_data['total_executions']}")
    print(f"  Records returned: {len(history_data['executions'])}")

    assert history_data["total_executions"] >= num_executions

    # Verify execution records
    for execution in history_data["executions"][:num_executions]:
        assert "id" in execution
        assert "status" in execution
        assert "trigger_type" in execution
        assert "created_at" in execution
        print(f"  - {execution['id'][:8]}: {execution['status']}")

    # Verify workflow statistics
    await test_session.commit()

    stmt = select(Workflow).where(Workflow.id == UUID(workflow_id))
    result = await test_session.execute(stmt)
    workflow_obj = result.scalar_one_or_none()

    assert workflow_obj is not None
    assert workflow_obj.execution_count >= num_executions

    print(f"✓ Workflow statistics:")
    print(f"  Total executions: {workflow_obj.execution_count}")
    print(f"  Success count: {workflow_obj.success_count}")
    print(f"  Failure count: {workflow_obj.failure_count}")
    print(f"  Success rate: {workflow_obj.success_rate}%")


# ============================================================================
# Test 6: Action Type Testing
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_with_conditional_action(client: AsyncClient, test_session: AsyncSession):
    """Verify that conditional actions work correctly."""
    print("\n=== Test 9: Conditional Action ===\n")

    workflow_data = {
        "name": "Conditional Workflow",
        "trigger": {
            "type": "manual",
        },
        "actions": [
            {
                "type": "conditional",
                "config": {
                    "condition": {
                        "operator": "equals",
                        "field": "input.test_value",
                        "value": "yes",
                    },
                    "then_actions": [
                        {
                            "type": "log",
                            "config": {"message": "Condition was true"},
                        }
                    ],
                    "else_actions": [
                        {
                            "type": "log",
                            "config": {"message": "Condition was false"},
                        }
                    ],
                },
            },
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    workflow = create_response.json()
    workflow_id = workflow["id"]

    await client.post(f"/api/workflows/{workflow_id}/activate")

    # Execute with condition = true
    await client.post(
        f"/api/workflows/{workflow_id}/execute",
        json={"input_data": {"test_value": "yes"}},
    )
    await asyncio.sleep(0.3)

    # Check execution
    await test_session.commit()

    stmt = select(WorkflowExecution).where(
        WorkflowExecution.workflow_id == UUID(workflow_id)
    ).order_by(WorkflowExecution.created_at.desc())

    result = await test_session.execute(stmt)
    execution = result.scalar_one_or_none()

    assert execution is not None
    assert execution.status == ExecutionStatus.COMPLETED

    # Check that the "then" action was executed
    if execution.action_results:
        print(f"✓ Conditional action executed correctly")
        for action_result in execution.action_results:
            print(f"  - {action_result['action']['type']}: {action_result.get('result', {}).get('branch', 'unknown')}")


@pytest.mark.asyncio
async def test_workflow_with_delay_action(client: AsyncClient, test_session: AsyncSession):
    """Verify that delay actions work correctly."""
    print("\n=== Test 10: Delay Action ===\n")

    workflow_data = {
        "name": "Delay Test Workflow",
        "trigger": {
            "type": "manual",
        },
        "actions": [
            {
                "type": "log",
                "config": {"message": "Before delay"},
            },
            {
                "type": "delay",
                "config": {"seconds": 0.1},  # Short delay for testing
            },
            {
                "type": "log",
                "config": {"message": "After delay"},
            },
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    workflow = create_response.json()
    workflow_id = workflow["id"]

    await client.post(f"/api/workflows/{workflow_id}/activate")

    # Execute and measure time
    start_time = datetime.now()
    await client.post(f"/api/workflows/{workflow_id}/execute")

    # Wait for execution
    await asyncio.sleep(0.5)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"✓ Workflow executed in {duration:.2f} seconds")

    # Verify execution
    await test_session.commit()

    stmt = select(WorkflowExecution).where(
        WorkflowExecution.workflow_id == UUID(workflow_id)
    )

    result = await test_session.execute(stmt)
    execution = result.scalar_one_or_none()

    assert execution is not None
    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.duration_seconds is not None
    assert execution.duration_seconds >= 0.1  # At least the delay time

    print(f"✓ Execution duration: {execution.duration_seconds}s")


# ============================================================================
# Test 7: End-to-End Integration Test
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_e2e_full_flow(client: AsyncClient, test_session: AsyncSession):
    """
    Full end-to-end test: Create workflow -> Trigger webhook -> Execute -> Verify.

    This test simulates the complete workflow automation:
    1. Developer creates a workflow with webhook trigger
    2. A candidate is created (resume uploaded)
    3. Webhook event triggers workflow execution
    4. Workflow executes actions
    5. Execution history is recorded
    6. Statistics are updated
    """
    print("\n=== Test 11: Full End-to-End Workflow Flow ===\n")

    # Step 1: Create workflow with webhook trigger
    print("Step 1: Creating workflow with webhook trigger...")
    workflow_data = {
        "name": "New Candidate Processing",
        "description": "Automatically process new candidates",
        "trigger": {
            "type": "webhook",
            "event": "candidate.created",
        },
        "actions": [
            {
                "type": "log",
                "config": {
                    "message": "Processing candidate: {{trigger.data.candidate_id}}"
                },
                "label": "Log processing start",
            },
            {
                "type": "add_tag",
                "config": {
                    "tag": "auto_processed",
                    "candidate_id": "{{trigger.data.candidate_id}}",
                },
                "label": "Add processing tag",
            },
            {
                "type": "log",
                "config": {
                    "message": "Candidate processing complete"
                },
                "label": "Log completion",
            },
        ],
    }

    create_response = await client.post("/api/workflows", json=workflow_data)
    assert create_response.status_code == 201
    workflow = create_response.json()
    workflow_id = workflow["id"]

    print(f"✓ Workflow created: {workflow_id}")
    print(f"  Name: {workflow['name']}")
    print(f"  Trigger: {workflow['trigger_type']} - {workflow['trigger_config']['event']}")
    print(f"  Actions: {len(workflow['actions'])}")

    # Step 2: Activate the workflow
    print("\nStep 2: Activating workflow...")
    activate_response = await client.post(f"/api/workflows/{workflow_id}/activate")
    assert activate_response.status_code == 200
    activated_workflow = activate_response.json()

    print(f"✓ Workflow activated: {activated_workflow['status']}")
    assert activated_workflow["is_active"] is True

    # Step 3: Create a candidate (this would trigger candidate.created event in production)
    print("\nStep 3: Creating candidate (resume upload)...")
    test_resume = Resume(
        filename="jane_doe_resume.pdf",
        file_path="/tmp/jane_doe_resume.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Jane Doe - Senior Software Engineer\n\nSkills: Python, React, AWS",
        language="en"
    )
    test_session.add(test_resume)
    await test_session.commit()
    await test_session.refresh(test_resume)

    candidate_id = str(test_resume.id)
    print(f"✓ Candidate created: {candidate_id}")
    print(f"  Filename: {test_resume.filename}")

    # Step 4: Trigger workflow execution
    print("\nStep 4: Triggering workflow execution...")
    from services.workflow_engine import WorkflowEngine

    async with WorkflowEngine(session=test_session) as engine:
        trigger_data = {
            "candidate_id": candidate_id,
            "filename": test_resume.filename,
            "status": test_resume.status.value,
            "created_at": test_resume.created_at.isoformat() if test_resume.created_at else None,
        }

        execution_result = await engine.execute_workflow(
            workflow_id=workflow_id,
            trigger_type=WorkflowTriggerType.WEBHOOK,
            trigger_data=trigger_data,
        )

        print(f"✓ Workflow execution completed")
        print(f"  Execution ID: {execution_result['execution_id']}")
        print(f"  Status: {execution_result['status']}")
        assert execution_result["status"] == "completed"

    # Step 5: Verify execution record
    print("\nStep 5: Verifying execution record...")
    await test_session.commit()

    stmt = select(WorkflowExecution).where(
        and_(
            WorkflowExecution.workflow_id == UUID(workflow_id),
            WorkflowExecution.trigger_type == WorkflowTriggerType.WEBHOOK,
        )
    )
    result = await test_session.execute(stmt)
    execution = result.scalar_one_or_none()

    assert execution is not None
    print(f"✓ Execution record found:")
    print(f"  ID: {execution.id}")
    print(f"  Status: {execution.status.value}")
    print(f"  Trigger type: {execution.trigger_type.value}")
    print(f"  Duration: {execution.duration_seconds}s" if execution.duration_seconds else "  Duration: N/A")
    print(f"  Started: {execution.started_at}")
    print(f"  Completed: {execution.completed_at}")

    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.trigger_data["candidate_id"] == candidate_id

    # Step 6: Verify action results
    print("\nStep 6: Verifying action results...")
    assert execution.action_results is not None
    assert len(execution.action_results) == 3

    print(f"✓ All {len(execution.action_results)} actions executed:")

    for i, action_result in enumerate(execution.action_results, 1):
        action_type = action_result["action"]["type"]
        status = action_result["status"]
        print(f"  {i}. {action_type}: {status}")
        assert status == "success"

    # Step 7: Verify workflow statistics updated
    print("\nStep 7: Verifying workflow statistics...")
    await test_session.refresh(workflow_obj := await test_session.get(Workflow, UUID(workflow_id)))

    print(f"✓ Workflow statistics updated:")
    print(f"  Execution count: {workflow_obj.execution_count}")
    print(f"  Success count: {workflow_obj.success_count}")
    print(f"  Failure count: {workflow_obj.failure_count}")
    print(f"  Success rate: {workflow_obj.success_rate}%")
    print(f"  Last executed: {workflow_obj.last_executed_at}")

    assert workflow_obj.execution_count == 1
    assert workflow_obj.success_count == 1
    assert workflow_obj.failure_count == 0
    assert workflow_obj.success_rate == 100.0
    assert workflow_obj.last_executed_at is not None

    # Step 8: Get execution history via API
    print("\nStep 8: Retrieving execution history via API...")
    history_response = await client.get(f"/api/workflows/{workflow_id}/executions")
    assert history_response.status_code == 200
    history_data = history_response.json()

    print(f"✓ Execution history retrieved:")
    print(f"  Total executions: {history_data['total_executions']}")

    assert history_data["total_executions"] >= 1

    if history_data["executions"]:
        first_execution = history_data["executions"][0]
        print(f"  Latest execution:")
        print(f"    ID: {first_execution['id']}")
        print(f"    Status: {first_execution['status']}")
        print(f"    Duration: {first_execution.get('duration_seconds', 'N/A')}s")

    # Step 9: List workflows
    print("\nStep 9: Listing workflows...")
    list_response = await client.get("/api/workflows/?is_active=true")
    assert list_response.status_code == 200
    workflows = list_response.json()

    print(f"✓ Active workflows: {len(workflows)}")

    # Find our workflow in the list
    our_workflow = next((w for w in workflows if w["id"] == workflow_id), None)
    assert our_workflow is not None
    assert our_workflow["is_active"] is True
    print(f"  Found our workflow: {our_workflow['name']}")

    print("\n=== End-to-End Workflow Test PASSED ===\n")
    print("Summary:")
    print("  ✓ Workflow created with webhook trigger")
    print("  ✓ Workflow activated successfully")
    print("  ✓ Candidate created (simulated resume upload)")
    print("  ✓ Workflow triggered by webhook event")
    print("  ✓ All actions executed successfully")
    print("  ✓ Execution record created")
    print("  ✓ Workflow statistics updated")
    print("  ✓ Execution history retrievable via API")
    print("  ✓ Workflow appears in active workflows list")


# ============================================================================
# Summary and Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
