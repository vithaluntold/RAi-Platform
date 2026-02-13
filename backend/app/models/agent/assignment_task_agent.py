"""
Assignment Task Agent - instance-level agent assignment
Cloned from WorkflowTaskAgent when an assignment is activated.
Similar to how users are assigned to tasks at the assignment level.
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class AgentAssignmentStatus(str, Enum):
    """Status of an agent assignment on a task"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AssignmentTaskAgent(Base):
    """
    Deep clone of WorkflowTaskAgent for a specific assignment task.
    Each assignment task gets its own agent config that can be
    independently configured, run, and tracked.

    This is the INSTANCE level — defines what agents ARE assigned.
    """
    __tablename__ = "assignment_task_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to the assignment-level task (assignment_workflow_tasks.id)
    task_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Reference to the agent definition
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Reference to the template config (for audit/traceability)
    template_agent_id = Column(UUID(as_uuid=True), nullable=True)

    # Ordering (like user assignment order)
    order = Column(Integer, nullable=False, default=0)

    # Status tracking
    status = Column(
        SQLEnum(AgentAssignmentStatus),
        default=AgentAssignmentStatus.PENDING,
        nullable=False
    )

    # Whether this agent is required or optional
    is_required = Column(Boolean, default=False, nullable=False)

    # Agent-specific config for this task instance
    task_config = Column(JSON, nullable=True)

    # Instructions for this specific run
    instructions = Column(String(2000), nullable=True)

    # Who configured/assigned this agent
    assigned_by = Column(UUID(as_uuid=True), nullable=True)

    # Last execution reference
    last_execution_id = Column(UUID(as_uuid=True), nullable=True)
    last_run_at = Column(DateTime, nullable=True)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index('idx_assign_task_agents_task', 'task_id'),
        Index('idx_assign_task_agents_agent', 'agent_id'),
        Index('idx_assign_task_agents_status', 'status'),
        Index('idx_assign_task_agents_order', 'task_id', 'order'),
    )

    def __repr__(self):
        return f"<AssignmentTaskAgent(id={self.id}, task_id={self.task_id}, agent_id={self.agent_id}, status={self.status})>"
