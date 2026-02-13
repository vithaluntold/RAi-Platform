"""
Canvas API Endpoints
Routes for workflow visualization and assignment canvas operations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models import Workflow, WorkflowStage, WorkflowStep, WorkflowTask, WorkflowAssignment
from app.services.assignment_service import AssignmentService

router = APIRouter()


class CanvasNodeUpdate(BaseModel):
    """Schema for updating a node's status from canvas view"""
    node_type: str  # "stage", "step", or "task"
    node_id: str
    status: str  # "not_started", "in_progress", "completed", "blocked"


@router.get("/workflows/{workflow_id}", response_model=dict)
async def get_workflow_canvas(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get workflow template visualization as nodes and edges for canvas rendering.
    
    Returns:
    - nodes: Array of stage nodes with positions
    - edges: Array of connections between stages
    - metadata: Workflow info and statistics
    """
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == UUID(workflow_id)
        ).first()

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Fetch all stages with their steps and tasks
        stages = db.query(WorkflowStage).filter(
            WorkflowStage.workflow_id == UUID(workflow_id)
        ).order_by(WorkflowStage.position).all()

        nodes = []
        edges = []
        x_offset = 0
        prev_stage_id = None

        for idx, stage in enumerate(stages):
            # Get tasks in this stage
            steps = db.query(WorkflowStep).filter(
                WorkflowStep.stage_id == stage.id
            ).all()

            task_count = sum(
                db.query(WorkflowTask).filter(
                    WorkflowTask.step_id == step.id
                ).count()
                for step in steps
            )

            node = {
                "id": str(stage.id),
                "type": "stage",
                "data": {
                    "label": stage.name,
                    "description": stage.description,
                    "stepCount": len(steps),
                    "taskCount": task_count,
                },
                "position": {
                    "x": x_offset,
                    "y": 0,
                },
            }
            nodes.append(node)

            # Create edge from previous stage
            if prev_stage_id:
                edge = {
                    "id": f"edge-{prev_stage_id}-{stage.id}",
                    "source": str(prev_stage_id),
                    "target": str(stage.id),
                    "animated": True,
                }
                edges.append(edge)

            x_offset += 300  # Space nodes horizontally
            prev_stage_id = stage.id

        return {
            "workflow": {
                "id": str(workflow.id),
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status.value if hasattr(workflow.status, 'value') else workflow.status,
            },
            "nodes": nodes,
            "edges": edges,
            "viewport": {
                "x": 0,
                "y": 0,
                "zoom": 1.0,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/{assignment_id}", response_model=dict)
async def get_assignment_canvas(
    assignment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get assignment visualization: cloned workflow with status overlay.
    
    Shows the template workflow structure with each stage/step/task's current status.
    Allows interactive navigation and status updates directly on canvas.
    
    Returns:
    - nodes: Stage nodes with status colors and progress
    - edges: Connections between stages
    - entityMap: Map of node IDs to database records for status updates
    """
    try:
        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == UUID(assignment_id)
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Use service to get hierarchy
        hierarchy = AssignmentService.get_assignment_hierarchy(UUID(assignment_id), db)

        # Transform to canvas format
        nodes = []
        edges = []
        entity_map = {}
        x_offset = 0
        prev_stage_id = None

        for stage_idx, stage in enumerate(hierarchy.get("stages", [])):
            stage_status = stage["status"]
            stage_id = stage["id"]

            # Determine status color
            status_color = {
                "NOT_STARTED": "#e0e0e0",
                "IN_PROGRESS": "#ffeb3b",
                "COMPLETED": "#4caf50",
            }.get(stage_status, "#e0e0e0")

            # Build nested steps with tasks for frontend hierarchy
            steps_data = []
            for step in stage.get("steps", []):
                tasks_data = [
                    {
                        "id": t.get("id", ""),
                        "name": t.get("name", ""),
                        "status": t.get("status", "NOT_STARTED"),
                        "assigned_to": t.get("assigned_to"),
                        "order": t.get("order", 0),
                        "agents": t.get("agents", []),
                    }
                    for t in step.get("tasks", [])
                ]
                steps_data.append({
                    "id": step["id"],
                    "name": step["name"],
                    "status": step.get("status", "NOT_STARTED"),
                    "tasks": tasks_data,
                    "order": step.get("order", 0),
                })

            task_count = sum(
                len(step.get("tasks", [])) for step in stage.get("steps", [])
            )
            completed_count = sum(
                1 for step in stage.get("steps", [])
                for task in step.get("tasks", [])
                if task.get("status") == "COMPLETED"
            )

            node = {
                "id": stage_id,
                "type": "stage",
                "data": {
                    "label": stage["name"],
                    "status": stage_status,
                    "progress": f"{(completed_count / task_count * 100):.0f}%" if task_count > 0 else "0%",
                    "taskCount": task_count,
                    "completedCount": completed_count,
                    "stepCount": len(steps_data),
                    "steps": steps_data,
                },
                "position": {
                    "x": x_offset,
                    "y": 0,
                },
                "style": {
                    "backgroundColor": status_color,
                    "borderColor": "#333",
                    "borderWidth": 2,
                },
            }
            nodes.append(node)
            entity_map[stage_id] = {
                "type": "stage",
                "dbId": stage_id,
            }

            # Create edge from previous stage
            if prev_stage_id:
                edge = {
                    "id": f"edge-{prev_stage_id}-{stage_id}",
                    "source": str(prev_stage_id),
                    "target": str(stage_id),
                    "animated": stage_status == "IN_PROGRESS",
                }
                edges.append(edge)

            # Add step and task entity mappings for status updates
            for step in stage.get("steps", []):
                entity_map[step["id"]] = {
                    "type": "step",
                    "dbId": step["id"],
                }
                for task in step.get("tasks", []):
                    entity_map[task.get("id", "")] = {
                        "type": "task",
                        "dbId": task.get("id", ""),
                    }

            x_offset += 300
            prev_stage_id = stage_id

        progress = AssignmentService.calculate_progress(UUID(assignment_id), db)

        return {
            "assignment": {
                "id": str(assignment.id),
                "status": assignment.status.value if hasattr(assignment.status, 'value') else assignment.status,
                "priority": assignment.priority.value if hasattr(assignment.priority, 'value') else assignment.priority,
                "client_id": str(assignment.client_id),
                "progress": progress,
                "due_date": assignment.due_date,
            },
            "nodes": nodes,
            "edges": edges,
            "entityMap": entity_map,
            "viewport": {
                "x": 0,
                "y": 0,
                "zoom": 0.8,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/stats", response_model=dict)
async def get_workflow_stats(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get workflow template statistics: stage count, typical duration, etc.
    """
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == UUID(workflow_id)
        ).first()

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        stages = db.query(WorkflowStage).filter(
            WorkflowStage.workflow_id == UUID(workflow_id)
        ).all()

        total_steps = sum(
            db.query(WorkflowStep).filter(
                WorkflowStep.stage_id == stage.id
            ).count()
            for stage in stages
        )

        total_tasks = sum(
            db.query(WorkflowTask).filter(
                WorkflowTask.step_id == step.id
            ).count()
            for stage in stages
            for step in db.query(WorkflowStep).filter(
                WorkflowStep.stage_id == stage.id
            ).all()
        )

        return {
            "workflow_id": str(workflow.id),
            "stage_count": len(stages),
            "step_count": total_steps,
            "task_count": total_tasks,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/assignments/{assignment_id}/nodes", response_model=dict)
async def update_canvas_node_status(
    assignment_id: str,
    payload: CanvasNodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a node's status directly from canvas view.
    Supports stages, steps, and tasks with auto-progression.
    
    - **node_type**: "stage", "step", or "task"
    - **node_id**: UUID of the entity
    - **status**: New status value
    """
    try:
        # Verify assignment exists
        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == UUID(assignment_id)
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        node_id = UUID(payload.node_id)

        if payload.node_type == "task":
            result = AssignmentService.update_task_status(
                task_id=node_id,
                new_status=payload.status,
                db=db,
            )
        elif payload.node_type == "step":
            result = AssignmentService.update_step_status(
                step_id=node_id,
                new_status=payload.status,
                db=db,
            )
        elif payload.node_type == "stage":
            result = AssignmentService.update_stage_status(
                stage_id=node_id,
                new_status=payload.status,
                db=db,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid node_type: {payload.node_type}")

        # Return updated canvas data
        updated_canvas = await get_assignment_canvas(assignment_id, db, current_user)
        return {
            "update_result": result,
            "canvas": updated_canvas,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
