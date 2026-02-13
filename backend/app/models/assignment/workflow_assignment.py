"""
Workflow Assignment Models - for assigning workflow templates to clients
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class AssignmentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class AssignmentPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class WorkflowAssignment(Base):
    """
    Core table for assigning workflow templates to clients.
    When activated, clones workflow structure into assignment-specific tables.
    """
    __tablename__ = "workflow_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Status tracking
    status = Column(
        SQLEnum(AssignmentStatus),
        default=AssignmentStatus.DRAFT,
        nullable=False,
        index=True
    )
    assigned_by = Column(UUID(as_uuid=True), nullable=False)  # user.id
    
    # Notes and metadata
    notes = Column(String(1000), nullable=True)
    
    # Timeline
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    
    # Priority
    priority = Column(
        SQLEnum(AssignmentPriority),
        default=AssignmentPriority.MEDIUM,
        nullable=False
    )
    
    # Flexible storage for custom fields per organization
    custom_metadata = Column(JSON, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Indexes for common queries
    __table_args__ = (
        Index('idx_workflow_assignments_org_status', 'organization_id', 'status'),
        Index('idx_workflow_assignments_client', 'client_id'),
        Index('idx_workflow_assignments_workflow', 'workflow_id'),
    )

    def __repr__(self):
        return f"<WorkflowAssignment(id={self.id}, status={self.status}, client_id={self.client_id})>"
