"""
Agent API Endpoints
Routes for managing agents, template-level configs, assignment-level assignments, and executions
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.agent import Agent, WorkflowTaskAgent, AssignmentTaskAgent
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse,
    WorkflowTaskAgentCreate, WorkflowTaskAgentUpdate, WorkflowTaskAgentResponse,
    AssignmentTaskAgentCreate, AssignmentTaskAgentUpdate, AssignmentTaskAgentResponse,
    AgentExecutionCreate, AgentExecutionResponse,
)
from app.services.agent_service import (
    AgentService, WorkflowTaskAgentService,
    AssignmentTaskAgentService, AgentExecutionService,
)

router = APIRouter()


# ─── Agent Definition CRUD ─────────────────────────────────────────────────

@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new agent definition"""
    agent = AgentService.create_agent(db, payload.model_dump(), current_user.id)
    return agent


@router.get("", response_model=list[AgentResponse])
def list_agents(
    agent_type: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all agents with optional filters"""
    return AgentService.list_agents(db, agent_type=agent_type, status=status)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get a single agent by ID"""
    agent = AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update an agent definition"""
    agent = AgentService.update_agent(
        db, agent_id, payload.model_dump(exclude_unset=True)
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Soft-delete an agent (marks inactive)"""
    if not AgentService.delete_agent(db, agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")


# ─── Workflow Task Agent (Template Level) ──────────────────────────────────

@router.post(
    "/workflow-tasks/{task_id}/agents",
    response_model=WorkflowTaskAgentResponse,
    status_code=201,
)
def attach_agent_to_workflow_task(
    task_id: UUID,
    payload: WorkflowTaskAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Attach an agent to a workflow template task"""
    wta = WorkflowTaskAgentService.attach_agent(db, task_id, payload.model_dump())
    agent = AgentService.get_agent(db, wta.agent_id)
    result = _build_wta_response(wta, agent)
    return result


@router.get(
    "/workflow-tasks/{task_id}/agents",
    response_model=list[WorkflowTaskAgentResponse],
)
def list_workflow_task_agents(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all agents attached to a workflow template task"""
    items = WorkflowTaskAgentService.list_task_agents(db, task_id)
    results = []
    for wta in items:
        agent = AgentService.get_agent(db, wta.agent_id)
        results.append(_build_wta_response(wta, agent))
    return results


@router.patch(
    "/workflow-task-agents/{wta_id}",
    response_model=WorkflowTaskAgentResponse,
)
def update_workflow_task_agent(
    wta_id: UUID,
    payload: WorkflowTaskAgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update agent config on a workflow template task"""
    wta = WorkflowTaskAgentService.update_task_agent(
        db, wta_id, payload.model_dump(exclude_unset=True)
    )
    if not wta:
        raise HTTPException(status_code=404, detail="Workflow task agent not found")
    agent = AgentService.get_agent(db, wta.agent_id)
    return _build_wta_response(wta, agent)


@router.delete("/workflow-task-agents/{wta_id}", status_code=204)
def remove_workflow_task_agent(
    wta_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Remove an agent from a workflow template task"""
    if not WorkflowTaskAgentService.remove_task_agent(db, wta_id):
        raise HTTPException(status_code=404, detail="Workflow task agent not found")


# ─── Assignment Task Agent (Instance Level) ────────────────────────────────

@router.post(
    "/assignment-tasks/{task_id}/agents",
    response_model=AssignmentTaskAgentResponse,
    status_code=201,
)
def assign_agent_to_assignment_task(
    task_id: UUID,
    payload: AssignmentTaskAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Manually assign an agent to an assignment task"""
    ata = AssignmentTaskAgentService.assign_agent(
        db, task_id, payload.model_dump(), current_user.id
    )
    agent = AgentService.get_agent(db, ata.agent_id)
    return _build_ata_response(ata, agent)


@router.get(
    "/assignment-tasks/{task_id}/agents",
    response_model=list[AssignmentTaskAgentResponse],
)
def list_assignment_task_agents(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all agents assigned to an assignment task"""
    items = AssignmentTaskAgentService.list_task_agents(db, task_id)
    results = []
    for ata in items:
        agent = AgentService.get_agent(db, ata.agent_id)
        results.append(_build_ata_response(ata, agent))
    return results


@router.patch(
    "/assignment-task-agents/{ata_id}",
    response_model=AssignmentTaskAgentResponse,
)
def update_assignment_task_agent(
    ata_id: UUID,
    payload: AssignmentTaskAgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update agent assignment on an assignment task"""
    ata = AssignmentTaskAgentService.update_task_agent(
        db, ata_id, payload.model_dump(exclude_unset=True)
    )
    if not ata:
        raise HTTPException(status_code=404, detail="Assignment task agent not found")
    agent = AgentService.get_agent(db, ata.agent_id)
    return _build_ata_response(ata, agent)


@router.delete("/assignment-task-agents/{ata_id}", status_code=204)
def remove_assignment_task_agent(
    ata_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Remove an agent from an assignment task"""
    if not AssignmentTaskAgentService.remove_task_agent(db, ata_id):
        raise HTTPException(status_code=404, detail="Assignment task agent not found")


# ─── Agent Execution ──────────────────────────────────────────────────────

@router.post(
    "/assignment-task-agents/{ata_id}/execute",
    response_model=AgentExecutionResponse,
    status_code=201,
)
def execute_agent(
    ata_id: UUID,
    payload: AgentExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Trigger an agent execution on an assignment task"""
    try:
        execution = AgentExecutionService.create_execution(
            db, ata_id, current_user.id, payload.input_data
        )
        return execution
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/assignment-task-agents/{ata_id}/executions",
    response_model=list[AgentExecutionResponse],
)
def list_agent_executions(
    ata_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all executions for an assignment task agent"""
    return AgentExecutionService.list_executions(db, ata_id)


@router.get(
    "/executions/{execution_id}",
    response_model=AgentExecutionResponse,
)
def get_agent_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get a single execution result"""
    execution = AgentExecutionService.get_execution(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


# ─── Response Builders ─────────────────────────────────────────────────────

def _build_wta_response(wta: WorkflowTaskAgent, agent: Agent | None) -> dict:
    """Build WorkflowTaskAgentResponse dict with agent name/type"""
    return {
        "id": wta.id,
        "task_id": wta.task_id,
        "agent_id": wta.agent_id,
        "position": wta.position,
        "is_required": wta.is_required,
        "task_config": wta.task_config,
        "instructions": wta.instructions,
        "created_at": wta.created_at,
        "updated_at": wta.updated_at,
        "agent_name": agent.name if agent else None,
        "agent_type": agent.agent_type.value if agent else None,
    }


def _build_ata_response(ata: AssignmentTaskAgent, agent: Agent | None) -> dict:
    """Build AssignmentTaskAgentResponse dict with agent name/type"""
    return {
        "id": ata.id,
        "task_id": ata.task_id,
        "agent_id": ata.agent_id,
        "template_agent_id": ata.template_agent_id,
        "order": ata.order,
        "status": ata.status.value if hasattr(ata.status, "value") else ata.status,
        "is_required": ata.is_required,
        "task_config": ata.task_config,
        "instructions": ata.instructions,
        "assigned_by": ata.assigned_by,
        "last_execution_id": ata.last_execution_id,
        "last_run_at": ata.last_run_at,
        "created_at": ata.created_at,
        "updated_at": ata.updated_at,
        "agent_name": agent.name if agent else None,
        "agent_type": agent.agent_type.value if agent else None,
    }
