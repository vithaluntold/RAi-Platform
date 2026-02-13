"""
Project Business Logic Service - Kanban Operations
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from uuid import UUID
from typing import Dict, List

from app.models import (
    Project,
    ProjectTask,
    ProjectCollaborator,
)


class ProjectService:
    """Service for managing projects and Kanban boards"""

    @staticmethod
    def get_project_tasks_grouped(project_id: UUID, db: Session) -> Dict[str, List]:
        """
        Get all tasks for a project, grouped by status columns.
        Returns dict with keys: todo, in_progress, review, completed
        """
        tasks = db.query(ProjectTask).filter(
            ProjectTask.project_id == project_id
        ).order_by(ProjectTask.position).all()

        grouped = {
            "todo": [],
            "in_progress": [],
            "review": [],
            "completed": [],
        }

        for task in tasks:
            task_dict = {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "status": task.status.value if task.status else "todo",
                "priority": task.priority.value if task.priority else "medium",
                "assignee_id": str(task.assignee_id) if task.assignee_id else None,
                "due_date": task.due_date,
                "position": task.position,
                "estimated_hours": float(task.estimated_hours) if task.estimated_hours else None,
                "actual_hours": float(task.actual_hours) if task.actual_hours else None,
            }

            status = task.status.value if task.status else "todo"
            if status in grouped:
                grouped[status].append(task_dict)

        return grouped

    @staticmethod
    def move_task(
        task_id: UUID,
        new_status: str,
        new_position: int,
        db: Session,
    ) -> dict:
        """
        Move task to new status column and position.
        Handles reordering of affected tasks.
        """
        task = db.query(ProjectTask).filter(
            ProjectTask.id == task_id
        ).first()

        if not task:
            raise ValueError("Task not found")

        old_status = task.status.value if task.status else "todo"
        old_position = task.position
        project_id = task.project_id

        # If moving to same status, just update position
        if old_status == new_status:
            # Reorder tasks in same status
            if new_position < old_position:
                # Moving up - increment positions below new position
                affected = db.query(ProjectTask).filter(
                    and_(
                        ProjectTask.project_id == project_id,
                        ProjectTask.status == new_status,
                        ProjectTask.position >= new_position,
                        ProjectTask.position < old_position,
                    )
                ).all()
                for t in affected:
                    t.position += 1
            else:
                # Moving down - decrement positions above new position
                affected = db.query(ProjectTask).filter(
                    and_(
                        ProjectTask.project_id == project_id,
                        ProjectTask.status == new_status,
                        ProjectTask.position > old_position,
                        ProjectTask.position <= new_position,
                    )
                ).all()
                for t in affected:
                    t.position -= 1
        else:
            # Moving to different status - handle both columns
            # Remove from old position
            db.query(ProjectTask).filter(
                and_(
                    ProjectTask.project_id == project_id,
                    ProjectTask.status == old_status,
                    ProjectTask.position > old_position,
                )
            ).all()
            for t in db.query(ProjectTask).filter(
                and_(
                    ProjectTask.project_id == project_id,
                    ProjectTask.status == old_status,
                    ProjectTask.position > old_position,
                )
            ).all():
                t.position -= 1

            # Increment positions in new column at and after new position
            for t in db.query(ProjectTask).filter(
                and_(
                    ProjectTask.project_id == project_id,
                    ProjectTask.status == new_status,
                    ProjectTask.position >= new_position,
                )
            ).all():
                t.position += 1

        # Update task
        task.status = new_status
        task.position = new_position
        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        return {
            "id": str(task.id),
            "title": task.title,
            "status": task.status.value if task.status else "todo",
            "position": task.position,
        }

    @staticmethod
    def get_project_stats(project_id: UUID, db: Session) -> dict:
        """Calculate project statistics"""
        total = db.query(ProjectTask).filter(
            ProjectTask.project_id == project_id
        ).count()

        completed = db.query(ProjectTask).filter(
            and_(
                ProjectTask.project_id == project_id,
                ProjectTask.status == "completed",
            )
        ).count()

        in_progress = db.query(ProjectTask).filter(
            and_(
                ProjectTask.project_id == project_id,
                ProjectTask.status == "in_progress",
            )
        ).count()

        pending = db.query(ProjectTask).filter(
            and_(
                ProjectTask.project_id == project_id,
                ProjectTask.status.in_(["todo", "review"]),
            )
        ).count()

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
        }

    @staticmethod
    def get_projects_paginated(
        organization_id: UUID = None,
        db: Session = None,
        status: str = None,
        owner_id: UUID = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple:
        """
        Get paginated list of projects.
        Returns (projects, total_count)
        """
        query = db.query(Project)

        if organization_id:
            query = query.filter(
                Project.organization_id == organization_id
            )

        if status:
            query = query.filter(Project.status == status)

        if owner_id:
            query = query.filter(Project.owner_id == owner_id)

        total_count = query.count()

        offset = (page - 1) * limit
        projects = (
            query.order_by(desc(Project.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return projects, total_count

    @staticmethod
    def check_project_access(
        user_id: UUID,
        project_id: UUID,
        min_role: str,
        db: Session,
    ) -> bool:
        """
        Check if user has access to project with minimum role.
        min_role: 'owner', 'editor', 'viewer', 'commenter'
        """
        collaborator = db.query(ProjectCollaborator).filter(
            and_(
                ProjectCollaborator.project_id == project_id,
                ProjectCollaborator.user_id == user_id,
            )
        ).first()

        if not collaborator:
            return False

        role_hierarchy = ["viewer", "commenter", "editor", "owner"]
        user_role_index = role_hierarchy.index(collaborator.role.value)
        min_role_index = role_hierarchy.index(min_role)

        return user_role_index >= min_role_index

    @staticmethod
    def add_collaborator(
        project_id: UUID,
        user_id: UUID,
        role: str,
        db: Session,
    ) -> dict:
        """Add or update collaborator on project"""
        # Check if already exists
        existing = db.query(ProjectCollaborator).filter(
            and_(
                ProjectCollaborator.project_id == project_id,
                ProjectCollaborator.user_id == user_id,
            )
        ).first()

        if existing:
            existing.role = role
            db.commit()
            db.refresh(existing)
            collab = existing
        else:
            collab = ProjectCollaborator(
                project_id=project_id,
                user_id=user_id,
                role=role,
            )
            db.add(collab)
            db.commit()
            db.refresh(collab)

        return {
            "id": str(collab.id),
            "project_id": str(collab.project_id),
            "user_id": str(collab.user_id),
            "role": collab.role.value,
            "joined_at": collab.joined_at,
        }
