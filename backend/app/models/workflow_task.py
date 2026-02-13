"""
Workflow Task Models - workflow template tasks
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class WorkflowTask(Base):
    """
    Template task within a workflow step.
    Tasks are the finest-grained units of work in the workflow.
    """
    __tablename__ = "workflow_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to parent step
    step_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Task details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Ordering within step
    position = Column(Integer, nullable=False)

    # Custom metadata
    custom_metadata = Column(JSON, nullable=True)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index('idx_workflow_tasks_step', 'step_id'),
        Index('idx_workflow_tasks_position', 'step_id', 'position'),
    )

    def __repr__(self):
        return f"<WorkflowTask(id={self.id}, name={self.name})>"
