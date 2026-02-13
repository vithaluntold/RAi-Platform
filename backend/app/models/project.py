"""
Project Models - Kanban board containers for task management
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, ARRAY, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectVisibility(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"


class ProjectPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Project(Base):
    """
    Projects serve as Kanban boards for task management within an organization.
    Can be linked to a client and contains multiple collaborators.
    """
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Organization context
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Project details
    name = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=True)
    
    # Optional client link
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True, index=True)
    
    # Status and priority
    status = Column(
        SQLEnum(ProjectStatus),
        default=ProjectStatus.PLANNING,
        nullable=False,
        index=True
    )
    priority = Column(
        SQLEnum(ProjectPriority),
        default=ProjectPriority.MEDIUM,
        nullable=False
    )
    
    # Ownership and access control
    owner_id = Column(UUID(as_uuid=True), nullable=False)  # user.id - project lead
    manager_ids = Column(ARRAY(UUID), nullable=True, default=[])  # Array of user IDs with manage access
    
    # Folder organization
    resource_folder_id = Column(UUID(as_uuid=True), nullable=True)  # Input folder
    output_folder_id = Column(UUID(as_uuid=True), nullable=True)  # Output folder
    
    # Timeline
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # Access control
    visibility = Column(
        SQLEnum(ProjectVisibility),
        default=ProjectVisibility.TEAM,
        nullable=False
    )
    
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
        Index('idx_projects_org_status', 'organization_id', 'status'),
        Index('idx_projects_client', 'client_id'),
        Index('idx_projects_owner', 'owner_id'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"
