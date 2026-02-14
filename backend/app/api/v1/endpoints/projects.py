"""
Projects API Endpoints
Routes for managing projects (Kanban boards) and tasks
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models import (
    Project,
    ProjectTask,
    ProjectCollaborator,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    ProjectTaskMove,
    ProjectCollaboratorAdd,
    ProjectListResponse,
    ProjectWithStatsResponse,
)
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    organization_id: str = Query(None, description="Organization ID (optional)"),
    status: str = Query(None, description="Filter by status"),
    owner_id: str = Query(None, description="Filter by owner"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """
    List projects with optional filters and statistics.
    
    - **organization_id**: Optional - filter by organization
    - **status**: Optional - filter by status (planning, active, review, completed, archived)
    - **owner_id**: Optional - filter by project owner
    """
    try:
        # Parse UUIDs safely
        org_uuid = None
        owner_uuid = None
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
            except ValueError:
                pass
        if owner_id:
            try:
                owner_uuid = UUID(owner_id)
            except ValueError:
                pass

        projects, total = ProjectService.get_projects_paginated(
            organization_id=org_uuid,
            status=status,
            owner_id=owner_uuid,
            page=page,
            limit=limit,
            db=db,
        )

        data = []
        for p in projects:
            stats = ProjectService.get_project_stats(p.id, db)
            data.append({
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
                "priority": p.priority.value if hasattr(p.priority, 'value') else str(p.priority),
                "owner_id": str(p.owner_id),
                "due_date": p.due_date,
                "task_count": stats["total"],
                "completed_count": stats["completed"],
                "in_progress_count": stats["in_progress"],
                "created_at": p.created_at,
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
async def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Create a new project (Kanban board).
    """
    try:
        project = Project(
            organization_id=payload.organization_id,
            name=payload.name,
            description=payload.description,
            client_id=payload.client_id,
            owner_id=payload.owner_id,
            manager_ids=payload.manager_ids or [],
            priority=payload.priority,
            status="planning",
            start_date=payload.start_date,
            due_date=payload.due_date,
            visibility=payload.visibility,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        # Add creator as owner collaborator
        collaborator = ProjectCollaborator(
            project_id=project.id,
            user_id=current_user.id,
            role="owner",
        )
        db.add(collaborator)
        db.commit()

        return {
            "id": str(project.id),
            "status": project.status.value,
            "created_at": project.created_at,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/kanban", response_model=dict)
async def get_project_kanban(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """
    Get project with Kanban board: tasks grouped by status columns.
    
    Returns columns: todo, in_progress, review, completed
    """
    try:
        project = db.query(Project).filter(
            Project.id == UUID(project_id)
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get grouped tasks
        columns = ProjectService.get_project_tasks_grouped(UUID(project_id), db)
        stats = ProjectService.get_project_stats(UUID(project_id), db)

        return {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "status": project.status.value,
                "owner_id": str(project.owner_id),
            },
            "columns": columns,
            "stats": stats,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/tasks", response_model=dict)
async def create_task(
    project_id: str,
    payload: ProjectTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """
    Create a new task in project (in todo column).
    """
    try:
        # Get max position in todo column
        max_pos = db.query(ProjectTask).filter(
            ProjectTask.project_id == UUID(project_id),
            ProjectTask.status == "todo",
        ).count()

        task = ProjectTask(
            project_id=UUID(project_id),
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            assignee_id=payload.assignee_id,
            status="todo",
            position=max_pos,
            due_date=payload.due_date,
            estimated_hours=payload.estimated_hours,
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "id": str(task.id),
            "title": task.title,
            "status": task.status.value,
            "position": task.position,
            "created_at": task.created_at,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}", response_model=dict)
async def update_task(
    task_id: str,
    payload: ProjectTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """
    Update task properties (title, description, status, priority, etc).
    
    Does NOT change position in column - use /move endpoint for that.
    """
    try:
        task = db.query(ProjectTask).filter(
            ProjectTask.id == UUID(task_id)
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description
        if payload.priority is not None:
            task.priority = payload.priority
        if payload.assignee_id is not None:
            task.assignee_id = payload.assignee_id
        if payload.due_date is not None:
            task.due_date = payload.due_date
        if payload.actual_hours is not None:
            task.actual_hours = payload.actual_hours

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        return {
            "id": str(task.id),
            "title": task.title,
            "status": task.status.value,
            "updated_at": task.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}/move", response_model=dict)
async def move_task(
    task_id: str,
    payload: ProjectTaskMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """
    Move task to different Kanban column and position.
    
    Handles reordering of affected tasks automatically.
    - **status**: Destination column (todo, in_progress, review, completed)
    - **position**: Position in the column (0-based)
    """
    try:
        result = ProjectService.move_task(
            task_id=UUID(task_id),
            new_status=payload.status,
            new_position=payload.position,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/tasks/{task_id}", response_model=dict)
async def delete_task(
    project_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """
    Delete a task from project.
    """
    try:
        task = db.query(ProjectTask).filter(
            ProjectTask.id == UUID(task_id),
            ProjectTask.project_id == UUID(project_id),
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Reorder remaining tasks
        affected = db.query(ProjectTask).filter(
            ProjectTask.project_id == UUID(project_id),
            ProjectTask.status == task.status,
            ProjectTask.position > task.position,
        ).all()

        for t in affected:
            t.position -= 1

        db.delete(task)
        db.commit()

        return {"deleted": str(task_id)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/collaborators", response_model=dict)
async def add_collaborator(
    project_id: str,
    payload: ProjectCollaboratorAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Add collaborator to project with specified role.
    
    Roles: owner, editor, viewer, commenter
    """
    try:
        result = ProjectService.add_collaborator(
            project_id=UUID(project_id),
            user_id=payload.user_id,
            role=payload.role,
            db=db,
        )
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
