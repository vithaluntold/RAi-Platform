"""
Assignment Workflow Step Models - cloned from workflow steps
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from .assignment_workflow_stage import StageStatus


class AssignmentWorkflowStep(Base):
    """
    Deep clone of workflow steps within stages, customizable per assignment.
    Created when assignment is activated.
    """
    __tablename__ = "assignment_workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to parent stage
    stage_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Reference to original template step (for audit/history)
    template_step_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Step details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Ordering within stage
    order = Column(Integer, nullable=False)
    
    # Execution mode: sequential (default) or parallel
    execution_mode = Column(String(50), default="sequential", nullable=False)
    
    # Status tracking (reuse StageStatus for consistency)
    status = Column(
        SQLEnum(StageStatus),
        default=StageStatus.NOT_STARTED,
        nullable=False
    )
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), nullable=True)  # user.id
    
    # Timeline
    due_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
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
        Index('idx_assignment_workflow_steps_stage', 'stage_id'),
        Index('idx_assignment_workflow_steps_order', 'stage_id', 'order'),
    )

    def __repr__(self):
        return f"<AssignmentWorkflowStep(id={self.id}, name={self.name}, status={self.status})>"
