"""
Workflow Step Models - workflow template steps
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class WorkflowStep(Base):
    """
    Template step within a workflow stage.
    Steps break down each stage into more granular units of work.
    Supports parallel execution mode for concurrent steps.
    """
    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to parent stage
    stage_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Step details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Ordering within stage
    position = Column(Integer, nullable=False)

    # Execution mode: sequential (default) or parallel
    execution_mode = Column(String(50), default="sequential", nullable=False)

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
        Index('idx_workflow_steps_stage', 'stage_id'),
        Index('idx_workflow_steps_position', 'stage_id', 'position'),
    )

    def __repr__(self):
        return f"<WorkflowStep(id={self.id}, name={self.name})>"
