"""
Agent Execution - tracks each time an agent runs on a task
Stores inputs, outputs, status, duration, and error details.
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class ExecutionStatus(str, Enum):
    """Status of an agent execution"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class AgentExecution(Base):
    """
    Tracks individual executions of an agent on a task.
    Each time a user runs an agent, a new execution record is created.
    """
    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which assignment-task-agent was executed
    assignment_task_agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which agent ran (denormalized for faster queries)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which task it ran on (denormalized)
    task_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Who triggered the execution
    triggered_by = Column(UUID(as_uuid=True), nullable=False)

    # Execution status
    status = Column(
        SQLEnum(ExecutionStatus),
        default=ExecutionStatus.QUEUED,
        nullable=False
    )

    # Input provided to the agent
    input_data = Column(JSON, nullable=True)

    # Output from the agent
    output_data = Column(JSON, nullable=True)

    # Error details if failed
    error_message = Column(String(2000), nullable=True)
    error_details = Column(JSON, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Numeric(precision=10, scale=2), nullable=True)

    # Backend used (azure, cyloid, etc.)
    backend_provider = Column(String(100), nullable=True)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index('idx_agent_exec_ata', 'assignment_task_agent_id'),
        Index('idx_agent_exec_agent', 'agent_id'),
        Index('idx_agent_exec_task', 'task_id'),
        Index('idx_agent_exec_status', 'status'),
        Index('idx_agent_exec_triggered', 'triggered_by'),
    )

    def __repr__(self):
        return f"<AgentExecution(id={self.id}, agent_id={self.agent_id}, status={self.status})>"
