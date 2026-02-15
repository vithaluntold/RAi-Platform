"""
Workflow Stage Models - workflow template stages
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class WorkflowStage(Base):
    """
    Template stage within a workflow.
    Defines the sequential phases of a workflow process.
    Supports parallel execution mode for concurrent stages.
    """
    __tablename__ = "workflow_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to parent workflow
    workflow_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Stage details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Ordering within workflow
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
        Index('idx_workflow_stages_workflow', 'workflow_id'),
        Index('idx_workflow_stages_position', 'workflow_id', 'position'),
    )

    def __repr__(self):
        return f"<WorkflowStage(id={self.id}, name={self.name})>"
