"""
Workflow Template CRUD Endpoints
Supports full hierarchy: Workflow → Stages → Steps → Tasks
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    StageCreate,
    StageUpdate,
    StepCreate,
    StepUpdate,
    TaskCreate,
    TaskUpdate,
)
from typing import Optional, List
from uuid import UUID

router = APIRouter()


# ── Workflow CRUD ───────────────────────────────────────────────────

@router.post("")
def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new workflow template."""
    try:
        workflow = WorkflowService.create_workflow(
            name=payload.name,
            description=payload.description,
            organization_id=payload.organization_id,
            created_by=current_user.id,
            db=db,
        )
        return {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value,
            "organization_id": str(workflow.organization_id),
            "created_by": str(workflow.created_by),
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def get_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all workflow templates."""
    workflows = WorkflowService.list_workflows(db=db, status=status)
    return [
        {
            "id": str(w.id),
            "name": w.name,
            "description": w.description,
            "status": w.status.value if hasattr(w.status, "value") else str(w.status),
            "organization_id": str(w.organization_id),
            "created_by": str(w.created_by),
            "created_at": w.created_at,
            "updated_at": w.updated_at,
        }
        for w in workflows
    ]


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get workflow with full hierarchy (stages → steps → tasks + agents)."""
    result = WorkflowService.get_workflow_hierarchy(workflow_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.patch("/{workflow_id}")
def update_workflow(
    workflow_id: UUID,
    payload: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update a workflow template."""
    workflow = WorkflowService.update_workflow(
        workflow_id=workflow_id,
        db=db,
        name=payload.name,
        description=payload.description,
        status=payload.status,
    )
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status.value,
        "organization_id": str(workflow.organization_id),
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
    }


@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a workflow template and all its children."""
    if not WorkflowService.delete_workflow(workflow_id, db):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"detail": "Workflow deleted"}


# ── Stage CRUD ──────────────────────────────────────────────────────

@router.post("/{workflow_id}/stages")
def create_stage(
    workflow_id: UUID,
    payload: StageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Add a stage to a workflow."""
    workflow = WorkflowService.get_workflow(workflow_id, db)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    stage = WorkflowService.create_stage(
        workflow_id=workflow_id,
        name=payload.name,
        description=payload.description,
        position=payload.position,
        execution_mode=payload.execution_mode,
        db=db,
    )
    return {
        "id": str(stage.id),
        "workflow_id": str(stage.workflow_id),
        "name": stage.name,
        "description": stage.description,
        "position": stage.position,
        "execution_mode": stage.execution_mode or "sequential",
        "created_at": stage.created_at,
        "updated_at": stage.updated_at,
    }


@router.get("/{workflow_id}/stages")
def get_stages(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List stages for a workflow."""
    stages = WorkflowService.list_stages(workflow_id, db)
    return [
        {
            "id": str(s.id),
            "workflow_id": str(s.workflow_id),
            "name": s.name,
            "description": s.description,
            "position": s.position,
            "execution_mode": s.execution_mode or "sequential",
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in stages
    ]


@router.patch("/stages/{stage_id}")
def update_stage(
    stage_id: UUID,
    payload: StageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update a stage."""
    stage = WorkflowService.update_stage(
        stage_id=stage_id,
        db=db,
        name=payload.name,
        description=payload.description,
        position=payload.position,
        execution_mode=payload.execution_mode,
    )
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    return {
        "id": str(stage.id),
        "workflow_id": str(stage.workflow_id),
        "name": stage.name,
        "description": stage.description,
        "position": stage.position,
        "execution_mode": stage.execution_mode or "sequential",
    }


@router.delete("/stages/{stage_id}")
def delete_stage(
    stage_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a stage and all its children."""
    if not WorkflowService.delete_stage(stage_id, db):
        raise HTTPException(status_code=404, detail="Stage not found")
    return {"detail": "Stage deleted"}


@router.put("/{workflow_id}/stages/reorder")
def reorder_stages(
    workflow_id: UUID,
    stage_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Reorder stages by providing ordered list of stage IDs."""
    WorkflowService.reorder_stages(workflow_id, stage_ids, db)
    return {"detail": "Stages reordered"}


# ── Step CRUD ───────────────────────────────────────────────────────

@router.post("/stages/{stage_id}/steps")
def create_step(
    stage_id: UUID,
    payload: StepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Add a step to a stage."""
    step = WorkflowService.create_step(
        stage_id=stage_id,
        name=payload.name,
        description=payload.description,
        position=payload.position,
        execution_mode=payload.execution_mode,
        db=db,
    )
    return {
        "id": str(step.id),
        "stage_id": str(step.stage_id),
        "name": step.name,
        "description": step.description,
        "position": step.position,
        "execution_mode": step.execution_mode or "sequential",
        "created_at": step.created_at,
        "updated_at": step.updated_at,
    }


@router.get("/stages/{stage_id}/steps")
def get_steps(
    stage_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List steps for a stage."""
    steps = WorkflowService.list_steps(stage_id, db)
    return [
        {
            "id": str(s.id),
            "stage_id": str(s.stage_id),
            "name": s.name,
            "description": s.description,
            "position": s.position,
            "execution_mode": s.execution_mode or "sequential",
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in steps
    ]


@router.patch("/steps/{step_id}")
def update_step(
    step_id: UUID,
    payload: StepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update a step."""
    step = WorkflowService.update_step(
        step_id=step_id,
        db=db,
        name=payload.name,
        description=payload.description,
        position=payload.position,
        execution_mode=payload.execution_mode,
    )
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return {
        "id": str(step.id),
        "stage_id": str(step.stage_id),
        "name": step.name,
        "description": step.description,
        "position": step.position,
        "execution_mode": step.execution_mode or "sequential",
    }


@router.delete("/steps/{step_id}")
def delete_step(
    step_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a step and all its tasks."""
    if not WorkflowService.delete_step(step_id, db):
        raise HTTPException(status_code=404, detail="Step not found")
    return {"detail": "Step deleted"}


# ── Task CRUD ───────────────────────────────────────────────────────

@router.post("/steps/{step_id}/tasks")
def create_task(
    step_id: UUID,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Add a task to a step."""
    task = WorkflowService.create_task(
        step_id=step_id,
        name=payload.name,
        description=payload.description,
        position=payload.position,
        db=db,
    )
    return {
        "id": str(task.id),
        "step_id": str(task.step_id),
        "name": task.name,
        "description": task.description,
        "position": task.position,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


@router.get("/steps/{step_id}/tasks")
def get_tasks(
    step_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List tasks for a step."""
    tasks = WorkflowService.list_tasks(step_id, db)
    return [
        {
            "id": str(t.id),
            "step_id": str(t.step_id),
            "name": t.name,
            "description": t.description,
            "position": t.position,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in tasks
    ]


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update a task."""
    task = WorkflowService.update_task(
        task_id=task_id,
        db=db,
        name=payload.name,
        description=payload.description,
        position=payload.position,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": str(task.id),
        "step_id": str(task.step_id),
        "name": task.name,
        "description": task.description,
        "position": task.position,
    }


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a task and its agent links."""
    if not WorkflowService.delete_task(task_id, db):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"detail": "Task deleted"}