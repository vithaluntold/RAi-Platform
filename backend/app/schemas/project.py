"""
Pydantic Schemas for Projects
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class ProjectTaskCreate(BaseModel):
    """Schema for creating a task in project"""
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None


class ProjectTaskUpdate(BaseModel):
    """Schema for updating a project task"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    actual_hours: Optional[float] = None


class ProjectTaskMove(BaseModel):
    """Schema for moving task between Kanban columns"""
    status: str
    position: int


class ProjectTaskResponse(BaseModel):
    """Response schema for project task"""
    id: UUID
    title: str
    description: Optional[str]
    status: str
    priority: str
    assignee_id: Optional[UUID]
    due_date: Optional[datetime]
    position: int
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    organization_id: UUID
    name: str
    description: Optional[str] = None
    client_id: Optional[UUID] = None
    owner_id: UUID
    manager_ids: Optional[List[UUID]] = []
    priority: Optional[str] = "medium"
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    visibility: Optional[str] = "team"


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    manager_ids: Optional[List[UUID]] = None


class ProjectCollaboratorAdd(BaseModel):
    """Schema for adding collaborator to project"""
    user_id: UUID
    role: str = "viewer"  # owner, editor, viewer, commenter


class ProjectResponse(BaseModel):
    """Response schema for project"""
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    client_id: Optional[UUID]
    status: str
    priority: str
    owner_id: UUID
    manager_ids: Optional[List[UUID]]
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    visibility: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectWithStatsResponse(BaseModel):
    """Response schema for project with task statistics"""
    id: UUID
    name: str
    description: Optional[str]
    status: str
    priority: str
    owner_id: UUID
    due_date: Optional[datetime]
    task_count: int = 0
    completed_count: int = 0
    in_progress_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectKanbanResponse(BaseModel):
    """Response schema for project Kanban board"""
    project: ProjectResponse
    columns: dict = Field(default_factory=lambda: {
        "todo": [],
        "in_progress": [],
        "review": [],
        "completed": []
    })
    stats: dict = Field(default_factory=dict)


class ProjectListResponse(BaseModel):
    """Schema for paginated project list"""
    data: List[ProjectWithStatsResponse]
    pagination: dict = Field(default_factory=dict)
