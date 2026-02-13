"""
Agent Schemas - Pydantic models for agent CRUD, configuration, and execution
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


# ─── Agent Definition Schemas ──────────────────────────────────────────────

class AgentCreate(BaseModel):
    """Create a new agent definition"""
    name: str
    description: Optional[str] = None
    agent_type: str = "custom"
    backend_provider: str = "azure"
    backend_config: Optional[dict] = None
    capabilities: Optional[dict] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    organization_id: Optional[UUID] = None


class AgentUpdate(BaseModel):
    """Update an agent definition"""
    name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    backend_provider: Optional[str] = None
    backend_config: Optional[dict] = None
    capabilities: Optional[dict] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent definition response"""
    id: UUID
    name: str
    description: Optional[str] = None
    agent_type: str
    backend_provider: str
    backend_config: Optional[dict] = None
    capabilities: Optional[dict] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    status: str
    is_system: bool
    organization_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Workflow Task Agent (Template Level) ──────────────────────────────────

class WorkflowTaskAgentCreate(BaseModel):
    """Attach an agent to a workflow template task"""
    agent_id: UUID
    position: int = 0
    is_required: bool = False
    task_config: Optional[dict] = None
    instructions: Optional[str] = None


class WorkflowTaskAgentUpdate(BaseModel):
    """Update agent configuration on a workflow template task"""
    position: Optional[int] = None
    is_required: Optional[bool] = None
    task_config: Optional[dict] = None
    instructions: Optional[str] = None


class WorkflowTaskAgentResponse(BaseModel):
    """Workflow task agent response"""
    id: UUID
    task_id: UUID
    agent_id: UUID
    position: int
    is_required: bool
    task_config: Optional[dict] = None
    instructions: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Assignment Task Agent (Instance Level) ────────────────────────────────

class AssignmentTaskAgentCreate(BaseModel):
    """Assign an agent to an assignment task"""
    agent_id: UUID
    order: int = 0
    is_required: bool = False
    task_config: Optional[dict] = None
    instructions: Optional[str] = None


class AssignmentTaskAgentUpdate(BaseModel):
    """Update agent assignment on an assignment task"""
    order: Optional[int] = None
    is_required: Optional[bool] = None
    task_config: Optional[dict] = None
    instructions: Optional[str] = None
    status: Optional[str] = None


class AssignmentTaskAgentResponse(BaseModel):
    """Assignment task agent response"""
    id: UUID
    task_id: UUID
    agent_id: UUID
    template_agent_id: Optional[UUID] = None
    order: int
    status: str
    is_required: bool
    task_config: Optional[dict] = None
    instructions: Optional[str] = None
    assigned_by: Optional[UUID] = None
    last_execution_id: Optional[UUID] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Agent Execution Schemas ───────────────────────────────────────────────

class AgentExecutionCreate(BaseModel):
    """Trigger an agent execution"""
    input_data: Optional[dict] = None


class AgentExecutionResponse(BaseModel):
    """Agent execution result"""
    id: UUID
    assignment_task_agent_id: UUID
    agent_id: UUID
    task_id: UUID
    triggered_by: UUID
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    error_details: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    backend_provider: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
