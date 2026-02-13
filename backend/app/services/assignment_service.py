"""
Assignment Business Logic Service
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from uuid import UUID

from app.models import (
    WorkflowAssignment,
    AssignmentWorkflowStage,
    AssignmentWorkflowStep,
    AssignmentWorkflowTask,
    Client,
)
from app.models.agent import (
    WorkflowTaskAgent,
    AssignmentTaskAgent,
    AgentAssignmentStatus,
    Agent,
)
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType


class AssignmentService:
    """Service for managing workflow assignments"""

    @staticmethod
    def activate_assignment(assignment_id: UUID, db: Session) -> None:
        """
        Activate assignment by cloning entire workflow structure.
        Clones: workflow stages -> steps -> tasks
        """
        from app.models.workflow import Workflow, WorkflowStage, WorkflowStep, WorkflowTask

        # Get assignment with workflow
        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == assignment_id
        ).first()

        if not assignment:
            raise ValueError("Assignment not found")

        # Get workflow template
        workflow = db.query(Workflow).filter(
            Workflow.id == assignment.workflow_id
        ).first()

        if not workflow:
            raise ValueError("Workflow not found")

        # Get all stages ordered
        stages = db.query(WorkflowStage).filter(
            WorkflowStage.workflow_id == workflow.id
        ).order_by(WorkflowStage.position).all()

        # Clone each stage with its steps and tasks
        for stage in stages:
            cloned_stage = AssignmentWorkflowStage(
                assignment_id=assignment.id,
                template_stage_id=stage.id,
                name=stage.name,
                description=stage.description,
                order=stage.position,
                status="not_started",
            )
            db.add(cloned_stage)
            db.flush()  # Get ID for child inserts

            # Get steps in stage
            steps = db.query(WorkflowStep).filter(
                WorkflowStep.stage_id == stage.id
            ).order_by(WorkflowStep.position).all()

            for step in steps:
                cloned_step = AssignmentWorkflowStep(
                    stage_id=cloned_stage.id,
                    template_step_id=step.id,
                    name=step.name,
                    description=step.description,
                    order=step.position,
                    status="not_started",
                )
                db.add(cloned_step)
                db.flush()

                # Get tasks in step
                tasks = db.query(WorkflowTask).filter(
                    WorkflowTask.step_id == step.id
                ).order_by(WorkflowTask.position).all()

                for task in tasks:
                    cloned_task = AssignmentWorkflowTask(
                        step_id=cloned_step.id,
                        template_task_id=task.id,
                        name=task.name,
                        description=task.description,
                        order=task.position,
                        status="not_started",
                    )
                    db.add(cloned_task)
                    db.flush()

                    # Clone agents attached to this template task
                    template_agents = db.query(WorkflowTaskAgent).filter(
                        WorkflowTaskAgent.task_id == task.id
                    ).order_by(WorkflowTaskAgent.position).all()

                    for ta in template_agents:
                        cloned_agent = AssignmentTaskAgent(
                            task_id=cloned_task.id,
                            agent_id=ta.agent_id,
                            template_agent_id=ta.id,
                            order=ta.position,
                            status=AgentAssignmentStatus.PENDING,
                            is_required=ta.is_required,
                            task_config=ta.task_config,
                            instructions=ta.instructions,
                            assigned_by=assignment.assigned_by,
                        )
                        db.add(cloned_agent)

        db.commit()

    @staticmethod
    def get_assignment_hierarchy(assignment_id: UUID, db: Session) -> dict:
        """
        Get assignment with full hierarchy: stages -> steps -> tasks
        """
        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == assignment_id
        ).first()

        if not assignment:
            raise ValueError("Assignment not found")

        # Get all stages
        stages = db.query(AssignmentWorkflowStage).filter(
            AssignmentWorkflowStage.assignment_id == assignment_id
        ).order_by(AssignmentWorkflowStage.order).all()

        stages_data = []
        for stage in stages:
            # Get steps in stage
            steps = db.query(AssignmentWorkflowStep).filter(
                AssignmentWorkflowStep.stage_id == stage.id
            ).order_by(AssignmentWorkflowStep.order).all()

            steps_data = []
            for step in steps:
                # Get tasks in step
                tasks = db.query(AssignmentWorkflowTask).filter(
                    AssignmentWorkflowTask.step_id == step.id
                ).order_by(AssignmentWorkflowTask.order).all()

                tasks_list = []
                for task in tasks:
                    # Get agents assigned to this task
                    task_agents = db.query(AssignmentTaskAgent).filter(
                        AssignmentTaskAgent.task_id == task.id
                    ).order_by(AssignmentTaskAgent.order).all()

                    agents_list = []
                    for ta in task_agents:
                        agent = db.query(Agent).filter(Agent.id == ta.agent_id).first()
                        agents_list.append({
                            "id": str(ta.id),
                            "agent_id": str(ta.agent_id),
                            "agent_name": agent.name if agent else "Unknown",
                            "agent_type": agent.agent_type.value if agent else "custom",
                            "status": ta.status.value if ta.status else "pending",
                            "is_required": ta.is_required,
                            "order": ta.order,
                            "last_run_at": ta.last_run_at.isoformat() if ta.last_run_at else None,
                        })

                    tasks_list.append({
                        "id": str(task.id),
                        "name": task.name,
                        "description": task.description,
                        "status": task.status.value if task.status else "not_started",
                        "assigned_to": str(task.assigned_to) if task.assigned_to else None,
                        "order": task.order,
                        "due_date": task.due_date,
                        "completed_date": task.completed_date,
                        "estimated_hours": float(task.estimated_hours) if task.estimated_hours else None,
                        "actual_hours": float(task.actual_hours) if task.actual_hours else None,
                        "agents": agents_list,
                    })

                steps_data.append({
                    "id": str(step.id),
                    "name": step.name,
                    "description": step.description,
                    "status": step.status.value if step.status else "not_started",
                    "assigned_to": str(step.assigned_to) if step.assigned_to else None,
                    "order": step.order,
                    "due_date": step.due_date,
                    "completed_date": step.completed_date,
                    "tasks": tasks_list,
                })

            stages_data.append({
                "id": str(stage.id),
                "name": stage.name,
                "description": stage.description,
                "status": stage.status.value if stage.status else "not_started",
                "assigned_to": str(stage.assigned_to) if stage.assigned_to else None,
                "order": stage.order,
                "start_date": stage.start_date,
                "completed_date": stage.completed_date,
                "steps": steps_data,
            })

        # Look up client name
        client_name = None
        if assignment.client_id:
            client = db.query(Client).filter(Client.id == assignment.client_id).first()
            if client:
                client_name = client.name

        return {
            "id": str(assignment.id),
            "workflow_id": str(assignment.workflow_id),
            "client_id": str(assignment.client_id),
            "client_name": client_name,
            "organization_id": str(assignment.organization_id),
            "status": assignment.status.value if assignment.status else "draft",
            "priority": assignment.priority.value if assignment.priority else "medium",
            "assigned_by": str(assignment.assigned_by),
            "notes": assignment.notes,
            "due_date": assignment.due_date,
            "start_date": assignment.start_date,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at,
            "stages": stages_data,
        }

    @staticmethod
    def calculate_progress(assignment_id: UUID, db: Session) -> int:
        """
        Calculate completion percentage for assignment.
        Returns 0-100 based on completed tasks vs total tasks.
        """
        # Count total tasks
        total_tasks = db.query(AssignmentWorkflowTask).filter(
            AssignmentWorkflowTask.step_id.in_(
                db.query(AssignmentWorkflowStep.id).filter(
                    AssignmentWorkflowStep.stage_id.in_(
                        db.query(AssignmentWorkflowStage.id).filter(
                            AssignmentWorkflowStage.assignment_id == assignment_id
                        )
                    )
                )
            )
        ).count()

        if total_tasks == 0:
            return 0

        # Count completed tasks
        completed_tasks = db.query(AssignmentWorkflowTask).filter(
            AssignmentWorkflowTask.step_id.in_(
                db.query(AssignmentWorkflowStep.id).filter(
                    AssignmentWorkflowStep.stage_id.in_(
                        db.query(AssignmentWorkflowStage.id).filter(
                            AssignmentWorkflowStage.assignment_id == assignment_id
                        )
                    )
                )
            ),
            AssignmentWorkflowTask.status == "completed",
        ).count()

        return int((completed_tasks / total_tasks) * 100)

    @staticmethod
    def get_assignments_paginated(
        organization_id: UUID = None,
        db: Session = None,
        client_id: UUID = None,
        status: str = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple:
        """
        Get paginated list of assignments with optional filters.
        Returns (assignments, total_count)
        """
        query = db.query(WorkflowAssignment)

        if organization_id:
            query = query.filter(
                WorkflowAssignment.organization_id == organization_id
            )

        if client_id:
            query = query.filter(WorkflowAssignment.client_id == client_id)

        if status:
            query = query.filter(WorkflowAssignment.status == status)

        total_count = query.count()

        offset = (page - 1) * limit
        assignments = (
            query.order_by(desc(WorkflowAssignment.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return assignments, total_count

    @staticmethod
    def update_task_status(
        task_id: UUID,
        new_status: str,
        assigned_to: UUID = None,
        actual_hours: float = None,
        db: Session = None,
    ) -> dict:
        """Update task status and trigger auto-progression up the hierarchy."""
        task = db.query(AssignmentWorkflowTask).filter(
            AssignmentWorkflowTask.id == task_id
        ).first()

        if not task:
            raise ValueError("Task not found")

        old_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

        if new_status:
            task.status = new_status
            if new_status == "completed":
                task.completed_date = datetime.utcnow()
            elif new_status == "in_progress" and old_status == "not_started":
                task.completed_date = None

        if assigned_to:
            task.assigned_to = assigned_to

        if actual_hours is not None:
            task.actual_hours = actual_hours

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        # Auto-progression: propagate status upward through hierarchy
        propagation = AssignmentService._propagate_status_upward(task.step_id, db)

        # Notification: task completed
        if new_status == "completed":
            step = db.query(AssignmentWorkflowStep).filter(
                AssignmentWorkflowStep.id == task.step_id
            ).first()
            assignment_name = ""
            assignment_id = None
            if step:
                stage = db.query(AssignmentWorkflowStage).filter(
                    AssignmentWorkflowStage.id == step.stage_id
                ).first()
                if stage:
                    assignment = db.query(WorkflowAssignment).filter(
                        WorkflowAssignment.id == stage.assignment_id
                    ).first()
                    if assignment:
                        assignment_name = assignment.name
                        assignment_id = assignment.id
            notify_user = task.assigned_to or (assigned_to if assigned_to else None)
            if notify_user:
                NotificationService.notify_task_completed(
                    db=db,
                    task_name=task.name,
                    assignment_name=assignment_name,
                    assigned_to=notify_user,
                    assignment_id=assignment_id,
                )
                db.commit()

        return {
            "id": str(task.id),
            "name": task.name,
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            "assigned_to": str(task.assigned_to) if task.assigned_to else None,
            "actual_hours": float(task.actual_hours) if task.actual_hours else None,
            "propagation": propagation,
        }

    @staticmethod
    def _propagate_status_upward(step_id: UUID, db: Session) -> dict:
        """
        Auto-progression: when tasks complete, propagate status up the hierarchy.

        Rules:
        - All tasks in a step completed → step status = completed
        - Any task in a step in_progress (and step was not_started) → step = in_progress
        - All steps in a stage completed → stage status = completed
        - Any step in a stage in_progress → stage = in_progress
        - All stages in assignment completed → assignment = completed
        - Any stage in_progress → assignment = in_progress
        """
        result = {"step": None, "stage": None, "assignment": None}

        # --- Step level ---
        step = db.query(AssignmentWorkflowStep).filter(
            AssignmentWorkflowStep.id == step_id
        ).first()
        if not step:
            return result

        tasks = db.query(AssignmentWorkflowTask).filter(
            AssignmentWorkflowTask.step_id == step_id
        ).all()

        if tasks:
            task_statuses = [
                t.status.value if hasattr(t.status, 'value') else str(t.status)
                for t in tasks
            ]
            all_completed = all(s == "completed" for s in task_statuses)
            any_in_progress = any(s in ("in_progress", "completed") for s in task_statuses)
            any_blocked = any(s == "blocked" for s in task_statuses)

            if all_completed:
                step.status = "completed"
                step.completed_date = datetime.utcnow()
                result["step"] = "completed"

                # Notify step completed
                _stage = db.query(AssignmentWorkflowStage).filter(
                    AssignmentWorkflowStage.id == step.stage_id
                ).first()
                if _stage:
                    _assignment = db.query(WorkflowAssignment).filter(
                        WorkflowAssignment.id == _stage.assignment_id
                    ).first()
                    if _assignment and step.assigned_to:
                        NotificationService.notify_step_completed(
                            db=db,
                            step_name=step.name,
                            assignment_name=_assignment.name,
                            assigned_to=step.assigned_to,
                            assignment_id=_assignment.id,
                        )
            elif any_blocked:
                step.status = "in_progress"
                result["step"] = "in_progress"
            elif any_in_progress:
                step.status = "in_progress"
                step.completed_date = None
                result["step"] = "in_progress"
            else:
                step.status = "not_started"
                step.completed_date = None
                result["step"] = "not_started"

        step.updated_at = datetime.utcnow()
        db.flush()

        # --- Stage level ---
        stage = db.query(AssignmentWorkflowStage).filter(
            AssignmentWorkflowStage.id == step.stage_id
        ).first()
        if not stage:
            db.commit()
            return result

        steps = db.query(AssignmentWorkflowStep).filter(
            AssignmentWorkflowStep.stage_id == stage.id
        ).all()

        if steps:
            step_statuses = [
                s.status.value if hasattr(s.status, 'value') else str(s.status)
                for s in steps
            ]
            all_completed = all(s == "completed" for s in step_statuses)
            any_in_progress = any(s in ("in_progress", "completed") for s in step_statuses)

            if all_completed:
                stage.status = "completed"
                stage.completed_date = datetime.utcnow()
                result["stage"] = "completed"

                # Notify stage completed
                _assignment_for_stage = db.query(WorkflowAssignment).filter(
                    WorkflowAssignment.id == stage.assignment_id
                ).first()
                if _assignment_for_stage and stage.assigned_to:
                    NotificationService.notify_stage_completed(
                        db=db,
                        stage_name=stage.name,
                        assignment_name=_assignment_for_stage.name,
                        assigned_to=stage.assigned_to,
                        assignment_id=_assignment_for_stage.id,
                    )
            elif any_in_progress:
                stage.status = "in_progress"
                if not stage.start_date:
                    stage.start_date = datetime.utcnow()
                stage.completed_date = None
                result["stage"] = "in_progress"
            else:
                stage.status = "not_started"
                stage.completed_date = None
                result["stage"] = "not_started"

        stage.updated_at = datetime.utcnow()
        db.flush()

        # --- Assignment level ---
        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == stage.assignment_id
        ).first()
        if not assignment:
            db.commit()
            return result

        stages = db.query(AssignmentWorkflowStage).filter(
            AssignmentWorkflowStage.assignment_id == assignment.id
        ).all()

        if stages:
            stage_statuses = [
                s.status.value if hasattr(s.status, 'value') else str(s.status)
                for s in stages
            ]
            all_completed = all(s == "completed" for s in stage_statuses)
            any_in_progress = any(s in ("in_progress", "completed") for s in stage_statuses)

            if all_completed:
                assignment.status = "completed"
                result["assignment"] = "completed"

                # Notify assignment completed
                if assignment.assigned_to:
                    NotificationService.notify_assignment_completed(
                        db=db,
                        assignment_name=assignment.name,
                        assigned_to=assignment.assigned_to,
                        assignment_id=assignment.id,
                    )
            elif any_in_progress:
                assignment.status = "in_progress"
                if not assignment.start_date:
                    assignment.start_date = datetime.utcnow()
                result["assignment"] = "in_progress"

        assignment.updated_at = datetime.utcnow()
        db.commit()

        return result

    @staticmethod
    def update_step_status(
        step_id: UUID,
        new_status: str,
        assigned_to: UUID = None,
        db: Session = None,
    ) -> dict:
        """Update step status manually and propagate upward."""
        step = db.query(AssignmentWorkflowStep).filter(
            AssignmentWorkflowStep.id == step_id
        ).first()

        if not step:
            raise ValueError("Step not found")

        step.status = new_status
        if new_status == "completed":
            step.completed_date = datetime.utcnow()
        if assigned_to:
            step.assigned_to = assigned_to
        step.updated_at = datetime.utcnow()

        # If step marked completed, mark all its tasks completed too
        if new_status == "completed":
            tasks = db.query(AssignmentWorkflowTask).filter(
                AssignmentWorkflowTask.step_id == step_id
            ).all()
            for task in tasks:
                task_status = task.status.value if hasattr(task.status, 'value') else str(task.status)
                if task_status != "completed":
                    task.status = "completed"
                    task.completed_date = datetime.utcnow()
                    task.updated_at = datetime.utcnow()

            # Notify step completed
            _stage_for_step = db.query(AssignmentWorkflowStage).filter(
                AssignmentWorkflowStage.id == step.stage_id
            ).first()
            if _stage_for_step:
                _assgn = db.query(WorkflowAssignment).filter(
                    WorkflowAssignment.id == _stage_for_step.assignment_id
                ).first()
                notify_user = step.assigned_to or assigned_to
                if _assgn and notify_user:
                    NotificationService.notify_step_completed(
                        db=db,
                        step_name=step.name,
                        assignment_name=_assgn.name,
                        assigned_to=notify_user,
                        assignment_id=_assgn.id,
                    )

        db.flush()

        # Propagate upward from step's stage
        stage = db.query(AssignmentWorkflowStage).filter(
            AssignmentWorkflowStage.id == step.stage_id
        ).first()

        propagation = {"step": new_status, "stage": None, "assignment": None}

        if stage:
            steps = db.query(AssignmentWorkflowStep).filter(
                AssignmentWorkflowStep.stage_id == stage.id
            ).all()
            step_statuses = [
                s.status.value if hasattr(s.status, 'value') else str(s.status)
                for s in steps
            ]
            if all(s == "completed" for s in step_statuses):
                stage.status = "completed"
                stage.completed_date = datetime.utcnow()
                propagation["stage"] = "completed"
            elif any(s in ("in_progress", "completed") for s in step_statuses):
                stage.status = "in_progress"
                if not stage.start_date:
                    stage.start_date = datetime.utcnow()
                propagation["stage"] = "in_progress"
            stage.updated_at = datetime.utcnow()
            db.flush()

            # Assignment level
            assignment = db.query(WorkflowAssignment).filter(
                WorkflowAssignment.id == stage.assignment_id
            ).first()
            if assignment:
                all_stages = db.query(AssignmentWorkflowStage).filter(
                    AssignmentWorkflowStage.assignment_id == assignment.id
                ).all()
                stage_statuses = [
                    s.status.value if hasattr(s.status, 'value') else str(s.status)
                    for s in all_stages
                ]
                if all(s == "completed" for s in stage_statuses):
                    assignment.status = "completed"
                    propagation["assignment"] = "completed"
                elif any(s in ("in_progress", "completed") for s in stage_statuses):
                    assignment.status = "in_progress"
                    propagation["assignment"] = "in_progress"
                assignment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(step)

        return {
            "id": str(step.id),
            "name": step.name,
            "status": step.status.value if hasattr(step.status, 'value') else str(step.status),
            "propagation": propagation,
        }

    @staticmethod
    def update_stage_status(
        stage_id: UUID,
        new_status: str,
        assigned_to: UUID = None,
        db: Session = None,
    ) -> dict:
        """Update stage status manually and propagate upward."""
        stage = db.query(AssignmentWorkflowStage).filter(
            AssignmentWorkflowStage.id == stage_id
        ).first()

        if not stage:
            raise ValueError("Stage not found")

        stage.status = new_status
        if new_status == "completed":
            stage.completed_date = datetime.utcnow()
        if assigned_to:
            stage.assigned_to = assigned_to
        stage.updated_at = datetime.utcnow()

        # If stage marked completed, cascade to all steps and tasks
        if new_status == "completed":
            steps = db.query(AssignmentWorkflowStep).filter(
                AssignmentWorkflowStep.stage_id == stage_id
            ).all()
            for step in steps:
                step_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
                if step_status != "completed":
                    step.status = "completed"
                    step.completed_date = datetime.utcnow()
                    step.updated_at = datetime.utcnow()
                tasks = db.query(AssignmentWorkflowTask).filter(
                    AssignmentWorkflowTask.step_id == step.id
                ).all()
                for task in tasks:
                    task_status = task.status.value if hasattr(task.status, 'value') else str(task.status)
                    if task_status != "completed":
                        task.status = "completed"
                        task.completed_date = datetime.utcnow()
                        task.updated_at = datetime.utcnow()

            # Notify stage completed
            _assgn_for_stage = db.query(WorkflowAssignment).filter(
                WorkflowAssignment.id == stage.assignment_id
            ).first()
            notify_user = stage.assigned_to or assigned_to
            if _assgn_for_stage and notify_user:
                NotificationService.notify_stage_completed(
                    db=db,
                    stage_name=stage.name,
                    assignment_name=_assgn_for_stage.name,
                    assigned_to=notify_user,
                    assignment_id=_assgn_for_stage.id,
                )

        db.flush()

        # Propagate to assignment level
        propagation = {"stage": new_status, "assignment": None}
        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == stage.assignment_id
        ).first()

        if assignment:
            all_stages = db.query(AssignmentWorkflowStage).filter(
                AssignmentWorkflowStage.assignment_id == assignment.id
            ).all()
            stage_statuses = [
                s.status.value if hasattr(s.status, 'value') else str(s.status)
                for s in all_stages
            ]
            if all(s == "completed" for s in stage_statuses):
                assignment.status = "completed"
                propagation["assignment"] = "completed"
            elif any(s in ("in_progress", "completed") for s in stage_statuses):
                assignment.status = "in_progress"
                propagation["assignment"] = "in_progress"
            assignment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(stage)

        return {
            "id": str(stage.id),
            "name": stage.name,
            "status": stage.status.value if hasattr(stage.status, 'value') else str(stage.status),
            "propagation": propagation,
        }
