"""
Assignment Workflow Stage Models - cloned from workflow stages
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class StageStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AssignmentWorkflowStage(Base):
    """
    Deep clone of workflow stages, customizable per assignment.
    Created when assignment is activated.
    """
    __tablename__ = "assignment_workflow_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to parent assignment
    assignment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Reference to original template stage (for audit/history)
    template_stage_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Stage details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Ordering within assignment
    order = Column(Integer, nullable=False)
    
    # Execution mode: sequential (default) or parallel
    execution_mode = Column(String(50), default="sequential", nullable=False)
    
    # Status tracking
    status = Column(
        SQLEnum(StageStatus),
        default=StageStatus.NOT_STARTED,
        nullable=False
    )
    
    # Timeline
    start_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Assignment
    assigned_to = Column(UUID(as_uuid=True), nullable=True)  # user.id
    
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
        Index('idx_assignment_workflow_stages_assignment', 'assignment_id'),
        Index('idx_assignment_workflow_stages_order', 'assignment_id', 'order'),
    )

    def __repr__(self):
        return f"<AssignmentWorkflowStage(id={self.id}, name={self.name}, status={self.status})>"
