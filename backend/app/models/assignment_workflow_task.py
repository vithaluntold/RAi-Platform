"""
Assignment Workflow Task Models - cloned from workflow tasks
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class AssignmentWorkflowTask(Base):
    """
    Deep clone of workflow tasks within steps, customizable and trackable per assignment.
    Created when assignment is activated.
    """
    __tablename__ = "assignment_workflow_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to parent step
    step_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Reference to original template task (for audit/history)
    template_task_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Task details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Ordering within step
    order = Column(Integer, nullable=False)
    
    # Status tracking
    status = Column(
        SQLEnum(TaskStatus),
        default=TaskStatus.NOT_STARTED,
        nullable=False
    )
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), nullable=True)  # user.id
    
    # Timeline
    due_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Time tracking
    estimated_hours = Column(Numeric(precision=10, scale=2), nullable=True)
    actual_hours = Column(Numeric(precision=10, scale=2), nullable=True)
    
    # Additional data
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
        Index('idx_assignment_workflow_tasks_step', 'step_id'),
        Index('idx_assignment_workflow_tasks_order', 'step_id', 'order'),
        Index('idx_assignment_workflow_tasks_status', 'status'),
    )

    def __repr__(self):
        return f"<AssignmentWorkflowTask(id={self.id}, name={self.name}, status={self.status})>"
