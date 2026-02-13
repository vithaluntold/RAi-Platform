"""
Project Collaborator Models - Multi-user project access
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class CollaboratorRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
    COMMENTER = "commenter"


class ProjectCollaborator(Base):
    """
    Enables multiple users to collaborate on the same project with role-based access.
    Each user has a unique role (owner, editor, viewer, commenter).
    """
    __tablename__ = "project_collaborators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to project
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Reference to user
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Role for this user in this project
    role = Column(
        SQLEnum(CollaboratorRole),
        default=CollaboratorRole.VIEWER,
        nullable=False
    )
    
    # When user joined the project
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # Ensure each user has only one role per project
        UniqueConstraint('project_id', 'user_id', name='unique_project_user'),
        Index('idx_project_collaborators_user', 'user_id'),
    )

    def __repr__(self):
        return f"<ProjectCollaborator(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"
