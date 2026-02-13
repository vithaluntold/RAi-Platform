"""
Assignment API Endpoints
Routes for managing workflow assignments: CRUD, status updates, task tracking
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import uuid
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models import WorkflowAssignment, Client
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    TaskUpdate,
    StepUpdate,
    StageUpdate,
    AssignmentListResponse,
)
from app.services.assignment_service import AssignmentService

router = APIRouter()


@router.get("/", response_model=AssignmentListResponse)
async def list_assignments(
    organization_id: str = Query(None, description="Organization ID (optional)"),
    client_id: str = Query(None, description="Filter by client"),
    status: str = Query(None, description="Filter by assignment status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List assignments with optional filters.
    
    - **organization_id**: Optional - filter by organization
    - **client_id**: Optional - filter by client
    - **status**: Optional - filter by status (draft, active, in_progress, completed, on_hold, cancelled)
    """
    try:
        # Parse UUIDs safely
        org_uuid = None
        client_uuid = None
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
            except ValueError:
                pass
        if client_id:
            try:
                client_uuid = UUID(client_id)
            except ValueError:
                pass

        assignments, total = AssignmentService.get_assignments_paginated(
            organization_id=org_uuid,
            client_id=client_uuid,
            status=status,
            page=page,
            limit=limit,
            db=db,
        )

        # Collect unique client_ids for batch lookup
        client_ids = list(set(a.client_id for a in assignments if a.client_id))
        client_map = {}
        if client_ids:
            clients = db.query(Client).filter(Client.id.in_(client_ids)).all()
            client_map = {c.id: c.name for c in clients}

        # Add progress for each assignment
        data = []
        for a in assignments:
            progress = AssignmentService.calculate_progress(a.id, db)
            data.append({
                "id": str(a.id),
                "workflow_id": str(a.workflow_id),
                "client_id": str(a.client_id),
                "client_name": client_map.get(a.client_id),
                "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                "priority": a.priority.value if hasattr(a.priority, 'value') else str(a.priority),
                "due_date": a.due_date,
                "start_date": a.start_date,
                "progress": progress,
                "created_at": a.created_at,
            })

        return {
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": max(1, (total + limit - 1) // limit),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
async def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new workflow assignment in draft status.
    When activated (status=active), will clone workflow structure.
    """
    try:
        # Use provided organization_id or generate a default one
        org_id = payload.organization_id or uuid.uuid4()

        # Create assignment
        assignment = WorkflowAssignment(
            workflow_id=payload.workflow_id,
            client_id=payload.client_id,
            organization_id=org_id,
            assigned_by=current_user.id,
            status="draft",
            priority=payload.priority,
            due_date=payload.due_date,
            start_date=payload.start_date,
            notes=payload.notes,
        )

        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        return {
            "id": str(assignment.id),
            "status": assignment.status.value,
            "created_at": assignment.created_at,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assignment_id}", response_model=dict)
async def get_assignment_detail(
    assignment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get assignment with full hierarchy: stages -> steps -> tasks.
    Shows all cloned workflow structure if assignment is active.
    """
    try:
        hierarchy = AssignmentService.get_assignment_hierarchy(
            UUID(assignment_id), db
        )
        return hierarchy
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{assignment_id}", response_model=dict)
async def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update assignment properties.
    
    When transitioning status to "active":
    - Clones entire workflow structure (stages, steps, tasks)
    - Setup becomes customizable per assignment
    """
    try:
        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == UUID(assignment_id)
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # If transitioning to active, clone workflow
        if payload.status == "active" and assignment.status != "active":
            AssignmentService.activate_assignment(UUID(assignment_id), db)

        # Update fields
        if payload.status:
            assignment.status = payload.status
        if payload.priority:
            assignment.priority = payload.priority
        if payload.notes is not None:
            assignment.notes = payload.notes
        if payload.due_date:
            assignment.due_date = payload.due_date
        if payload.start_date:
            assignment.start_date = payload.start_date

        assignment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(assignment)

        return {
            "id": str(assignment.id),
            "status": assignment.status.value,
            "priority": assignment.priority.value,
            "updated_at": assignment.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{assignment_id}/tasks/{task_id}", response_model=dict)
async def update_assignment_task(
    assignment_id: str,
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update task status, assignment, and time tracking.
    
    - **status**: not_started, in_progress, completed, blocked
    - **assigned_to**: User ID to assign task to
    - **actual_hours**: Log actual hours spent
    """
    try:
        from datetime import datetime

        result = AssignmentService.update_task_status(
            task_id=UUID(task_id),
            new_status=payload.status,
            assigned_to=payload.assigned_to,
            actual_hours=payload.actual_hours,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{assignment_id}/steps/{step_id}", response_model=dict)
async def update_assignment_step(
    assignment_id: str,
    step_id: str,
    payload: StepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update step status with auto-progression.
    If step is marked completed, all child tasks are also completed.
    """
    try:
        result = AssignmentService.update_step_status(
            step_id=UUID(step_id),
            new_status=payload.status,
            assigned_to=payload.assigned_to,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{assignment_id}/stages/{stage_id}", response_model=dict)
async def update_assignment_stage(
    assignment_id: str,
    stage_id: str,
    payload: StageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update stage status with auto-progression.
    If stage is marked completed, all child steps and tasks are also completed.
    """
    try:
        result = AssignmentService.update_stage_status(
            stage_id=UUID(stage_id),
            new_status=payload.status,
            assigned_to=payload.assigned_to,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Import datetime for endpoint use
from datetime import datetime
