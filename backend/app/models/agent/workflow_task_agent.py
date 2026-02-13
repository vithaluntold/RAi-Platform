"""
Workflow Task Agent - template-level agent configuration
Configures which agents are available on a workflow template task,
similar to how checklists are defined at the template level.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class WorkflowTaskAgent(Base):
    """
    Links an agent to a workflow template task.
    When a workflow is cloned into an assignment, these become
    AssignmentTaskAgent records that can be individually configured.

    This is the TEMPLATE level — defines what agents CAN be used.
    """
    __tablename__ = "workflow_task_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which task this agent is attached to
    task_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which agent
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Ordering (like checklist position)
    position = Column(Integer, nullable=False, default=0)

    # Whether this agent is required or optional for the task
    is_required = Column(Boolean, default=False, nullable=False)

    # Agent-specific config for this task (prompts, params, etc.)
    task_config = Column(JSON, nullable=True)

    # Instructions for the agent in context of this task
    instructions = Column(String(2000), nullable=True)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index('idx_wf_task_agents_task', 'task_id'),
        Index('idx_wf_task_agents_agent', 'agent_id'),
        Index('idx_wf_task_agents_position', 'task_id', 'position'),
    )

    def __repr__(self):
        return f"<WorkflowTaskAgent(id={self.id}, task_id={self.task_id}, agent_id={self.agent_id})>"
