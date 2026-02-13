"""
Workflow Models - workflow templates
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Workflow(Base):
    """
    Workflow template that can be assigned to multiple clients.
    Non-destructive - clients get cloned copies when assigned.
    """
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Workflow details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Status
    status = Column(
        SQLEnum(WorkflowStatus),
        default=WorkflowStatus.DRAFT,
        nullable=False
    )

    # Custom metadata (flexible storage)
    custom_metadata = Column(JSON, nullable=True)

    # Audit trail
    created_by = Column(UUID(as_uuid=True), nullable=False)  # user.id
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index('idx_workflows_org_status', 'organization_id', 'status'),
    )

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"
