"""
Project Task Models - Kanban cards within projects
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class ProjectTaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"


class ProjectTaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProjectTask(Base):
    """
    Individual task cards displayed in Kanban board columns.
    Supports drag-drop reordering via position field.
    """
    __tablename__ = "project_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to parent project
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Task details
    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=True)
    
    # Status and priority
    status = Column(
        SQLEnum(ProjectTaskStatus),
        default=ProjectTaskStatus.TODO,
        nullable=False,
        index=True
    )
    priority = Column(
        SQLEnum(ProjectTaskPriority),
        default=ProjectTaskPriority.MEDIUM,
        nullable=False
    )
    
    # Assignment
    assignee_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # user.id
    
    # Timeline
    due_date = Column(DateTime, nullable=True)
    
    # Position for drag-to-reorder within status column
    position = Column(Integer, nullable=False)
    
    # Time tracking
    estimated_hours = Column(Numeric(precision=10, scale=2), nullable=True)
    actual_hours = Column(Numeric(precision=10, scale=2), nullable=True)
    
    # Folder organization
    resource_folder_id = Column(UUID(as_uuid=True), nullable=True)
    output_folder_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Flexible storage for custom fields
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
        Index('idx_project_tasks_project', 'project_id'),
        Index('idx_project_tasks_status', 'status'),
        Index('idx_project_tasks_assignee', 'assignee_id'),
        Index('idx_project_tasks_position', 'project_id', 'status', 'position'),
    )

    def __repr__(self):
        return f"<ProjectTask(id={self.id}, title={self.title}, status={self.status})>"
