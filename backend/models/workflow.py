"""
Workflow models for no-code/low-code automation system
"""
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, JSON, String, Boolean, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class WorkflowTriggerType(str, enum.Enum):
    """Types of triggers that can start a workflow"""

    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"


class WorkflowStatus(str, enum.Enum):
    """Status of a workflow"""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, enum.Enum):
    """Status of a workflow execution"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(str, enum.Enum):
    """Types of actions that can be executed in a workflow"""

    # Notification actions
    SEND_EMAIL = "send_email"
    SEND_WEBHOOK = "send_webhook"
    SEND_SLACK = "send_slack"

    # Candidate actions
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    ADD_NOTE = "add_note"
    MOVE_STAGE = "move_stage"
    ASSIGN_RECRUITER = "assign_recruiter"

    # Data actions
    UPDATE_FIELD = "update_field"
    CREATE_ENTITY = "create_entity"
    DELETE_ENTITY = "delete_entity"

    # Analytics actions
    TRACK_EVENT = "track_event"
    GENERATE_REPORT = "generate_report"

    # Custom actions
    EXECUTE_FUNCTION = "execute_function"
    RUN_PLUGIN = "run_plugin"
    LOG = "log"
    CONDITIONAL = "conditional"
    DELAY = "delay"


class Workflow(Base, UUIDMixin, TimestampMixin):
    """
    Workflow model for no-code/low-code automation

    This model enables users to create custom automations using a visual
    builder with "if X then Y" logic. Workflows can be triggered by webhooks,
    schedules, or manual execution, and can perform various actions like
    sending notifications, updating candidates, or calling external APIs.

    Attributes:
        id: UUID primary key
        name: Human-readable name for the workflow
        description: Optional description of what the workflow does
        trigger_type: Type of trigger (webhook, schedule, manual)
        trigger_config: JSON object with trigger-specific configuration
        actions: JSON array of actions to execute when triggered
        status: Current status of the workflow (draft, active, paused, archived)
        version: Version number for tracking workflow changes
        is_active: Whether the workflow is currently active
        api_key_id: Optional foreign key to API key that owns this workflow
        last_executed_at: Timestamp of last successful execution
        execution_count: Total number of times this workflow has been executed
        success_count: Number of successful executions
        failure_count: Number of failed executions
        created_at: Timestamp when workflow was created (inherited)
        updated_at: Timestamp when workflow was last updated (inherited)
    """

    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[WorkflowTriggerType] = mapped_column(
        String(50), nullable=False, index=True
    )
    trigger_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    actions: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[WorkflowStatus] = mapped_column(
        String(50), nullable=False, default=WorkflowStatus.DRAFT, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    api_key_id: Mapped[Optional["UUID"]] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=True, index=True
    )
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    execution_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"

    def activate(self) -> None:
        """Activate the workflow"""
        self.is_active = True
        self.status = WorkflowStatus.ACTIVE

    def pause(self) -> None:
        """Pause the workflow"""
        self.is_active = False
        self.status = WorkflowStatus.PAUSED

    def archive(self) -> None:
        """Archive the workflow"""
        self.is_active = False
        self.status = WorkflowStatus.ARCHIVED

    def record_execution(self, success: bool) -> None:
        """Record an execution attempt"""
        self.execution_count += 1
        if success:
            self.success_count += 1
            self.last_executed_at = datetime.utcnow()
        else:
            self.failure_count += 1

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100


class WorkflowExecution(Base, UUIDMixin, TimestampMixin):
    """
    WorkflowExecution model for tracking workflow execution history

    This model maintains a detailed log of all workflow executions,
    including input data, action results, and error information.
    Enables monitoring and debugging of workflow automations.

    Attributes:
        id: UUID primary key
        workflow_id: Foreign key to Workflow
        status: Current execution status (pending, running, completed, failed, cancelled)
        trigger_type: Type of trigger that initiated this execution
        trigger_data: JSON object with data that triggered the execution
        input_data: JSON object with input data passed to the workflow
        output_data: JSON object with output data from the workflow
        action_results: JSON array of results from each action
        error_message: Error message if execution failed
        started_at: Timestamp when execution started
        completed_at: Timestamp when execution completed
        duration_seconds: Duration of execution in seconds
        created_at: Timestamp when execution record was created (inherited)
        updated_at: Timestamp when execution record was last updated (inherited)
    """

    __tablename__ = "workflow_executions"

    workflow_id: Mapped["UUID"] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        String(50), nullable=False, default=ExecutionStatus.PENDING, index=True
    )
    trigger_type: Mapped[WorkflowTriggerType] = mapped_column(
        String(50), nullable=False
    )
    trigger_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    action_results: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Integer, nullable=True
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"

    def start(self) -> None:
        """Mark the execution as started"""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, output_data: Optional[dict] = None) -> None:
        """Mark the execution as completed"""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if output_data:
            self.output_data = output_data
        if self.started_at:
            self.duration_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )

    def fail(self, error_message: str) -> None:
        """Mark the execution as failed"""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        if self.started_at:
            self.duration_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )

    def cancel(self) -> None:
        """Mark the execution as cancelled"""
        self.status = ExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )

    def is_successful(self) -> bool:
        """Check if the execution was successful"""
        return self.status == ExecutionStatus.COMPLETED

    def is_terminal(self) -> bool:
        """Check if the execution is in a terminal state"""
        return self.status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        }
