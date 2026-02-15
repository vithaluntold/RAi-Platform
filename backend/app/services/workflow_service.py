"""
Workflow Template Business Logic Service
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID, uuid4
from typing import Optional, List

from app.models.workflow import (
    Workflow,
    WorkflowStatus,
    WorkflowStage,
    WorkflowStep,
    WorkflowTask,
)
from app.models.agent import WorkflowTaskAgent, Agent


class WorkflowService:
    """Service for managing workflow templates and their hierarchy."""

    # ── Workflow CRUD ───────────────────────────────────────────────

    @staticmethod
    def create_workflow(
        name: str,
        created_by: UUID,
        description: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        db: Session = None,
    ) -> Workflow:
        org_id = organization_id or uuid4()
        workflow = Workflow(
            name=name,
            description=description,
            organization_id=org_id,
            created_by=created_by,
            status=WorkflowStatus.DRAFT,
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def get_workflow(workflow_id: UUID, db: Session) -> Optional[Workflow]:
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()

    @staticmethod
    def list_workflows(
        db: Session,
        status: Optional[str] = None,
    ) -> List[Workflow]:
        query = db.query(Workflow)
        if status:
            query = query.filter(Workflow.status == status)
        return query.order_by(Workflow.name).all()

    @staticmethod
    def update_workflow(
        workflow_id: UUID,
        db: Session,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Workflow]:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return None
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if status is not None:
            workflow.status = WorkflowStatus(status)
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def delete_workflow(workflow_id: UUID, db: Session) -> bool:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return False
        # Delete all children first (tasks → steps → stages)
        stages = db.query(WorkflowStage).filter(
            WorkflowStage.workflow_id == workflow_id
        ).all()
        for stage in stages:
            steps = db.query(WorkflowStep).filter(
                WorkflowStep.stage_id == stage.id
            ).all()
            for step in steps:
                tasks = db.query(WorkflowTask).filter(
                    WorkflowTask.step_id == step.id
                ).all()
                for task in tasks:
                    # Remove agents attached to template task
                    db.query(WorkflowTaskAgent).filter(
                        WorkflowTaskAgent.task_id == task.id
                    ).delete()
                    db.delete(task)
                db.delete(step)
            db.delete(stage)
        db.delete(workflow)
        db.commit()
        return True

    # ── Stage CRUD ──────────────────────────────────────────────────

    @staticmethod
    def create_stage(
        workflow_id: UUID,
        name: str,
        db: Session,
        description: Optional[str] = None,
        position: Optional[int] = None,
        execution_mode: Optional[str] = "sequential",
    ) -> WorkflowStage:
        if position is None:
            max_pos = db.query(func.max(WorkflowStage.position)).filter(
                WorkflowStage.workflow_id == workflow_id
            ).scalar()
            position = (max_pos or 0) + 1
        stage = WorkflowStage(
            workflow_id=workflow_id,
            name=name,
            description=description,
            position=position,
            execution_mode=execution_mode or "sequential",
        )
        db.add(stage)
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def list_stages(workflow_id: UUID, db: Session) -> List[WorkflowStage]:
        return (
            db.query(WorkflowStage)
            .filter(WorkflowStage.workflow_id == workflow_id)
            .order_by(WorkflowStage.position)
            .all()
        )

    @staticmethod
    def update_stage(
        stage_id: UUID,
        db: Session,
        name: Optional[str] = None,
        description: Optional[str] = None,
        position: Optional[int] = None,
        execution_mode: Optional[str] = None,
    ) -> Optional[WorkflowStage]:
        stage = db.query(WorkflowStage).filter(WorkflowStage.id == stage_id).first()
        if not stage:
            return None
        if name is not None:
            stage.name = name
        if description is not None:
            stage.description = description
        if position is not None:
            stage.position = position
        if execution_mode is not None:
            stage.execution_mode = execution_mode
        stage.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(stage)
        return stage

    @staticmethod
    def delete_stage(stage_id: UUID, db: Session) -> bool:
        stage = db.query(WorkflowStage).filter(WorkflowStage.id == stage_id).first()
        if not stage:
            return False
        # Delete children
        steps = db.query(WorkflowStep).filter(WorkflowStep.stage_id == stage_id).all()
        for step in steps:
            tasks = db.query(WorkflowTask).filter(WorkflowTask.step_id == step.id).all()
            for task in tasks:
                db.query(WorkflowTaskAgent).filter(
                    WorkflowTaskAgent.task_id == task.id
                ).delete()
                db.delete(task)
            db.delete(step)
        db.delete(stage)
        db.commit()
        return True

    @staticmethod
    def reorder_stages(workflow_id: UUID, stage_ids: List[UUID], db: Session) -> bool:
        stages = db.query(WorkflowStage).filter(
            WorkflowStage.workflow_id == workflow_id
        ).all()
        stage_map = {s.id: s for s in stages}
        for idx, sid in enumerate(stage_ids):
            if sid in stage_map:
                stage_map[sid].position = idx + 1
        db.commit()
        return True

    # ── Step CRUD ───────────────────────────────────────────────────

    @staticmethod
    def create_step(
        stage_id: UUID,
        name: str,
        db: Session,
        description: Optional[str] = None,
        position: Optional[int] = None,
        execution_mode: Optional[str] = "sequential",
    ) -> WorkflowStep:
        if position is None:
            max_pos = db.query(func.max(WorkflowStep.position)).filter(
                WorkflowStep.stage_id == stage_id
            ).scalar()
            position = (max_pos or 0) + 1
        step = WorkflowStep(
            stage_id=stage_id,
            name=name,
            description=description,
            position=position,
            execution_mode=execution_mode or "sequential",
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def list_steps(stage_id: UUID, db: Session) -> List[WorkflowStep]:
        return (
            db.query(WorkflowStep)
            .filter(WorkflowStep.stage_id == stage_id)
            .order_by(WorkflowStep.position)
            .all()
        )

    @staticmethod
    def update_step(
        step_id: UUID,
        db: Session,
        name: Optional[str] = None,
        description: Optional[str] = None,
        position: Optional[int] = None,
        execution_mode: Optional[str] = None,
    ) -> Optional[WorkflowStep]:
        step = db.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
        if not step:
            return None
        if name is not None:
            step.name = name
        if description is not None:
            step.description = description
        if position is not None:
            step.position = position
        if execution_mode is not None:
            step.execution_mode = execution_mode
        step.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def delete_step(step_id: UUID, db: Session) -> bool:
        step = db.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
        if not step:
            return False
        tasks = db.query(WorkflowTask).filter(WorkflowTask.step_id == step_id).all()
        for task in tasks:
            db.query(WorkflowTaskAgent).filter(
                WorkflowTaskAgent.task_id == task.id
            ).delete()
            db.delete(task)
        db.delete(step)
        db.commit()
        return True

    # ── Task CRUD ───────────────────────────────────────────────────

    @staticmethod
    def create_task(
        step_id: UUID,
        name: str,
        db: Session,
        description: Optional[str] = None,
        position: Optional[int] = None,
    ) -> WorkflowTask:
        if position is None:
            max_pos = db.query(func.max(WorkflowTask.position)).filter(
                WorkflowTask.step_id == step_id
            ).scalar()
            position = (max_pos or 0) + 1
        task = WorkflowTask(
            step_id=step_id,
            name=name,
            description=description,
            position=position,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def list_tasks(step_id: UUID, db: Session) -> List[WorkflowTask]:
        return (
            db.query(WorkflowTask)
            .filter(WorkflowTask.step_id == step_id)
            .order_by(WorkflowTask.position)
            .all()
        )

    @staticmethod
    def update_task(
        task_id: UUID,
        db: Session,
        name: Optional[str] = None,
        description: Optional[str] = None,
        position: Optional[int] = None,
    ) -> Optional[WorkflowTask]:
        task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            return None
        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        if position is not None:
            task.position = position
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(task_id: UUID, db: Session) -> bool:
        task = db.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            return False
        db.query(WorkflowTaskAgent).filter(
            WorkflowTaskAgent.task_id == task_id
        ).delete()
        db.delete(task)
        db.commit()
        return True

    # ── Full hierarchy ──────────────────────────────────────────────

    @staticmethod
    def get_workflow_hierarchy(workflow_id: UUID, db: Session) -> Optional[dict]:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return None

        stages = (
            db.query(WorkflowStage)
            .filter(WorkflowStage.workflow_id == workflow_id)
            .order_by(WorkflowStage.position)
            .all()
        )

        stages_data = []
        for stage in stages:
            steps = (
                db.query(WorkflowStep)
                .filter(WorkflowStep.stage_id == stage.id)
                .order_by(WorkflowStep.position)
                .all()
            )

            steps_data = []
            for step in steps:
                tasks = (
                    db.query(WorkflowTask)
                    .filter(WorkflowTask.step_id == step.id)
                    .order_by(WorkflowTask.position)
                    .all()
                )

                tasks_data = []
                for task in tasks:
                    # Get agents attached to this template task
                    task_agents = (
                        db.query(WorkflowTaskAgent)
                        .filter(WorkflowTaskAgent.task_id == task.id)
                        .order_by(WorkflowTaskAgent.position)
                        .all()
                    )
                    agents_list = []
                    for ta in task_agents:
                        agent = db.query(Agent).filter(Agent.id == ta.agent_id).first()
                        agents_list.append({
                            "id": str(ta.id),
                            "agent_id": str(ta.agent_id),
                            "agent_name": agent.name if agent else "Unknown",
                            "agent_type": agent.agent_type.value if agent else "custom",
                            "is_required": ta.is_required,
                            "position": ta.position,
                            "instructions": ta.instructions,
                        })

                    tasks_data.append({
                        "id": str(task.id),
                        "name": task.name,
                        "description": task.description,
                        "position": task.position,
                        "agents": agents_list,
                    })

                steps_data.append({
                    "id": str(step.id),
                    "name": step.name,
                    "description": step.description,
                    "position": step.position,
                    "execution_mode": step.execution_mode or "sequential",
                    "tasks": tasks_data,
                })

            stages_data.append({
                "id": str(stage.id),
                "name": stage.name,
                "description": stage.description,
                "position": stage.position,
                "execution_mode": stage.execution_mode or "sequential",
                "steps": steps_data,
            })

        return {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value if hasattr(workflow.status, "value") else str(workflow.status),
            "organization_id": str(workflow.organization_id),
            "created_by": str(workflow.created_by),
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "stages": stages_data,
        }
