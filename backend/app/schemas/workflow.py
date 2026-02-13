"""
Pydantic Schemas for Workflow Templates (Stages, Steps, Tasks)
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


# ── Workflow ────────────────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    organization_id: Optional[UUID] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Stage ───────────────────────────────────────────────────────────

class StageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    position: Optional[int] = None  # auto-calculated if omitted


class StageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    position: Optional[int] = None


class StageResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    name: str
    description: Optional[str]
    position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Step ────────────────────────────────────────────────────────────

class StepCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    position: Optional[int] = None


class StepUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    position: Optional[int] = None


class StepResponse(BaseModel):
    id: UUID
    stage_id: UUID
    name: str
    description: Optional[str]
    position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Task ────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    position: Optional[int] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    position: Optional[int] = None


class TaskResponse(BaseModel):
    id: UUID
    step_id: UUID
    name: str
    description: Optional[str]
    position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Nested hierarchy response ───────────────────────────────────────

class TaskWithAgents(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    position: int
    agents: List[dict] = []

    class Config:
        from_attributes = True


class StepWithTasks(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    position: int
    tasks: List[TaskWithAgents] = []

    class Config:
        from_attributes = True


class StageWithSteps(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    position: int
    steps: List[StepWithTasks] = []

    class Config:
        from_attributes = True


class WorkflowWithHierarchy(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    stages: List[StageWithSteps] = []

    class Config:
        from_attributes = True
