"""
Pydantic Schemas for Workflow Assignments
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class AssignmentCreate(BaseModel):
    """Schema for creating a new assignment"""
    workflow_id: UUID
    client_id: UUID
    organization_id: Optional[UUID] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    notes: Optional[str] = None


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment"""
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task within assignment"""
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    actual_hours: Optional[float] = None
    completed_date: Optional[datetime] = None


class StepUpdate(BaseModel):
    """Schema for updating a step within assignment"""
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None


class StageUpdate(BaseModel):
    """Schema for updating a stage within assignment"""
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None


class AssignmentTaskResponse(BaseModel):
    """Response schema for assignment task"""
    id: UUID
    name: str
    description: Optional[str]
    order: int
    status: str
    assigned_to: Optional[UUID]
    due_date: Optional[datetime]
    completed_date: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]

    class Config:
        from_attributes = True


class AssignmentStepResponse(BaseModel):
    """Response schema for assignment step with tasks"""
    id: UUID
    name: str
    description: Optional[str]
    order: int
    status: str
    assigned_to: Optional[UUID]
    due_date: Optional[datetime]
    completed_date: Optional[datetime]
    tasks: List[AssignmentTaskResponse] = []

    class Config:
        from_attributes = True


class AssignmentStageResponse(BaseModel):
    """Response schema for assignment stage with steps"""
    id: UUID
    name: str
    description: Optional[str]
    order: int
    status: str
    assigned_to: Optional[UUID]
    start_date: Optional[datetime]
    completed_date: Optional[datetime]
    steps: List[AssignmentStepResponse] = []

    class Config:
        from_attributes = True


class AssignmentResponse(BaseModel):
    """Response schema for assignment with full hierarchy"""
    id: UUID
    workflow_id: UUID
    client_id: UUID
    client_name: Optional[str] = None
    organization_id: UUID
    status: str
    priority: str
    assigned_by: UUID
    notes: Optional[str]
    due_date: Optional[datetime]
    start_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    stages: List[AssignmentStageResponse] = []

    class Config:
        from_attributes = True


class AssignmentListItem(BaseModel):
    """Schema for assignment list item (with counts, no full hierarchy)"""
    id: UUID
    workflow_id: UUID
    client_id: UUID
    client_name: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[datetime]
    start_date: Optional[datetime]
    progress: int = 0  # Calculated percentage
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentListResponse(BaseModel):
    """Schema for paginated assignment list"""
    data: List[AssignmentListItem]
    pagination: dict = Field(default_factory=dict)
