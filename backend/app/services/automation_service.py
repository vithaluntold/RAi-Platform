"""
Automation Engine Service
Handles dependencies, trigger evaluation, condition checking, action execution,
recurring schedules, and automated team communication.
"""
import logging
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.automation import (
    WorkflowDependency,
    AssignmentDependency,
    DependencyType,
    AutomationRule,
    AutomationCondition,
    AutomationAction,
    AutomationExecutionLog,
    TriggerEvent,
    ActionType,
    ConditionOperator,
    AutomationRuleStatus,
    WorkflowSOP,
    RecurringSchedule,
    RecurrenceFrequency,
)
from app.models import (
    WorkflowAssignment,
    AssignmentWorkflowStage,
    AssignmentWorkflowStep,
    AssignmentWorkflowTask,
    Client,
)
from app.models.user import User, UserRole
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType

logger = logging.getLogger(__name__)


class DependencyService:
    """Manages workflow dependencies at template and assignment level."""

    # ── Template-Level Dependency CRUD ──

    @staticmethod
    def create_dependency(
        workflow_id: UUID,
        dependency_type: str,
        source_entity_type: str,
        source_entity_id: UUID,
        target_entity_type: str,
        target_entity_id: UUID,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None,
        db: Session = None,
    ) -> WorkflowDependency:
        dep = WorkflowDependency(
            workflow_id=workflow_id,
            dependency_type=DependencyType(dependency_type),
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            description=description,
            created_by=created_by,
        )
        db.add(dep)
        db.commit()
        db.refresh(dep)
        return dep

    @staticmethod
    def list_dependencies(workflow_id: UUID, db: Session) -> list[WorkflowDependency]:
        return db.query(WorkflowDependency).filter(
            WorkflowDependency.workflow_id == workflow_id
        ).all()

    @staticmethod
    def delete_dependency(dependency_id: UUID, db: Session) -> bool:
        dep = db.query(WorkflowDependency).filter(
            WorkflowDependency.id == dependency_id
        ).first()
        if not dep:
            return False
        db.delete(dep)
        db.commit()
        return True

    # ── Clone Dependencies on Activation ──

    @staticmethod
    def clone_dependencies_for_assignment(
        assignment_id: UUID,
        workflow_id: UUID,
        entity_id_map: dict,
        db: Session,
    ) -> list[AssignmentDependency]:
        """
        Clone template dependencies into assignment-level dependencies.
        entity_id_map: {template_entity_id: cloned_entity_id}
        """
        template_deps = db.query(WorkflowDependency).filter(
            WorkflowDependency.workflow_id == workflow_id
        ).all()

        cloned = []
        for dep in template_deps:
            source_id = entity_id_map.get(dep.source_entity_id)
            target_id = entity_id_map.get(dep.target_entity_id)
            if not source_id or not target_id:
                continue

            cloned_dep = AssignmentDependency(
                assignment_id=assignment_id,
                template_dependency_id=dep.id,
                dependency_type=dep.dependency_type,
                source_entity_type=dep.source_entity_type,
                source_entity_id=source_id,
                target_entity_type=dep.target_entity_type,
                target_entity_id=target_id,
                is_satisfied=False,
                description=dep.description,
            )
            db.add(cloned_dep)
            cloned.append(cloned_dep)

        db.flush()
        return cloned

    # ── Dependency Evaluation ──

    @staticmethod
    def check_dependencies_satisfied(
        assignment_id: UUID,
        target_entity_type: str,
        target_entity_id: UUID,
        db: Session,
    ) -> dict:
        """
        Check if all dependencies for a target entity are satisfied.
        Returns {satisfied: bool, blocking: [{source_type, source_id, dep_type}]}
        """
        deps = db.query(AssignmentDependency).filter(
            AssignmentDependency.assignment_id == assignment_id,
            AssignmentDependency.target_entity_type == target_entity_type,
            AssignmentDependency.target_entity_id == target_entity_id,
            AssignmentDependency.is_satisfied == False,
        ).all()

        blocking = []
        for dep in deps:
            source_completed = DependencyService._is_entity_completed(
                dep.source_entity_type, dep.source_entity_id, db
            )
            if source_completed:
                dep.is_satisfied = True
                dep.satisfied_at = datetime.utcnow()
            else:
                blocking.append({
                    "dependency_id": str(dep.id),
                    "source_entity_type": dep.source_entity_type,
                    "source_entity_id": str(dep.source_entity_id),
                    "dependency_type": dep.dependency_type.value,
                    "description": dep.description,
                })

        db.flush()
        return {
            "satisfied": len(blocking) == 0,
            "blocking": blocking,
        }

    @staticmethod
    def mark_dependencies_satisfied_by_source(
        assignment_id: UUID,
        source_entity_type: str,
        source_entity_id: UUID,
        db: Session,
    ) -> list[dict]:
        """
        When a source entity completes, mark all its downstream dependencies as satisfied.
        Returns the list of unblocked target entities.
        """
        deps = db.query(AssignmentDependency).filter(
            AssignmentDependency.assignment_id == assignment_id,
            AssignmentDependency.source_entity_type == source_entity_type,
            AssignmentDependency.source_entity_id == source_entity_id,
            AssignmentDependency.is_satisfied == False,
        ).all()

        unblocked = []
        for dep in deps:
            dep.is_satisfied = True
            dep.satisfied_at = datetime.utcnow()
            unblocked.append({
                "target_entity_type": dep.target_entity_type,
                "target_entity_id": str(dep.target_entity_id),
                "dependency_type": dep.dependency_type.value,
            })

        db.flush()
        return unblocked

    @staticmethod
    def get_assignment_dependencies(
        assignment_id: UUID, db: Session
    ) -> list[AssignmentDependency]:
        return db.query(AssignmentDependency).filter(
            AssignmentDependency.assignment_id == assignment_id
        ).all()

    @staticmethod
    def _is_entity_completed(entity_type: str, entity_id: UUID, db: Session) -> bool:
        """Check if an assignment-level entity is completed."""
        if entity_type == "stage":
            entity = db.query(AssignmentWorkflowStage).filter(
                AssignmentWorkflowStage.id == entity_id
            ).first()
        elif entity_type == "step":
            entity = db.query(AssignmentWorkflowStep).filter(
                AssignmentWorkflowStep.id == entity_id
            ).first()
        elif entity_type == "task":
            entity = db.query(AssignmentWorkflowTask).filter(
                AssignmentWorkflowTask.id == entity_id
            ).first()
        else:
            return False

        if not entity:
            return False

        status = entity.status.value if hasattr(entity.status, 'value') else str(entity.status)
        return status == "completed"


class AutomationEngine:
    """
    Evaluates IF/THEN rules and executes actions.
    Handles trigger points, conditional logic, and automated communication.
    """

    @staticmethod
    def fire_trigger(
        trigger_event: str,
        assignment_id: UUID,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        context: Optional[dict] = None,
        db: Session = None,
    ) -> list[dict]:
        """
        Fire a trigger event and evaluate all matching automation rules.
        Returns list of execution results.
        """
        if not db:
            return []

        assignment = db.query(WorkflowAssignment).filter(
            WorkflowAssignment.id == assignment_id
        ).first()
        if not assignment:
            return []

        # Find matching rules for this workflow
        rules = db.query(AutomationRule).filter(
            AutomationRule.workflow_id == assignment.workflow_id,
            AutomationRule.trigger_event == trigger_event,
            AutomationRule.status == AutomationRuleStatus.ACTIVE,
        ).order_by(AutomationRule.priority).all()

        results = []
        for rule in rules:
            # Check if rule is scoped to a specific entity
            if rule.trigger_entity_id and entity_id:
                if rule.trigger_entity_id != entity_id:
                    continue

            result = AutomationEngine._evaluate_and_execute(
                rule=rule,
                assignment=assignment,
                entity_type=entity_type,
                entity_id=entity_id,
                context=context or {},
                db=db,
            )
            results.append(result)

        db.commit()
        return results

    @staticmethod
    def _evaluate_and_execute(
        rule: AutomationRule,
        assignment: WorkflowAssignment,
        entity_type: Optional[str],
        entity_id: Optional[UUID],
        context: dict,
        db: Session,
    ) -> dict:
        """Evaluate conditions and execute actions for a single rule."""

        # Evaluate conditions
        conditions = db.query(AutomationCondition).filter(
            AutomationCondition.rule_id == rule.id
        ).order_by(AutomationCondition.position).all()

        conditions_met = True
        condition_details = []

        for cond in conditions:
            field_value = AutomationEngine._resolve_field(
                cond.field, assignment, context, db
            )
            passed = AutomationEngine._evaluate_condition(
                field_value, cond.operator, cond.value
            )
            condition_details.append({
                "field": cond.field,
                "operator": cond.operator.value,
                "expected": cond.value,
                "actual": field_value,
                "passed": passed,
            })
            if not passed:
                conditions_met = False

        # Execute actions if conditions met
        action_results = []
        if conditions_met:
            actions = db.query(AutomationAction).filter(
                AutomationAction.rule_id == rule.id
            ).order_by(AutomationAction.position).all()

            for action in actions:
                result = AutomationEngine._execute_action(
                    action=action,
                    assignment=assignment,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    context=context,
                    db=db,
                )
                action_results.append(result)

        # Log execution
        log = AutomationExecutionLog(
            rule_id=rule.id,
            assignment_id=assignment.id,
            trigger_event=rule.trigger_event.value,
            trigger_entity_type=entity_type,
            trigger_entity_id=entity_id,
            conditions_met=conditions_met,
            condition_details=condition_details,
            actions_executed=action_results,
            success=all(r.get("success", False) for r in action_results) if action_results else True,
        )
        db.add(log)
        db.flush()

        return {
            "rule_id": str(rule.id),
            "rule_name": rule.name,
            "conditions_met": conditions_met,
            "actions_executed": len(action_results),
            "success": log.success,
        }

    @staticmethod
    def _resolve_field(
        field: str,
        assignment: WorkflowAssignment,
        context: dict,
        db: Session,
    ) -> object:
        """Resolve a field path to its actual value."""
        parts = field.split(".")
        if len(parts) < 2:
            return context.get(field)

        domain, attr = parts[0], parts[1]

        if domain == "assignment":
            return getattr(assignment, attr, None)
        elif domain == "client":
            client = db.query(Client).filter(Client.id == assignment.client_id).first()
            if client:
                val = getattr(client, attr, None)
                return val.value if hasattr(val, 'value') else val
        elif domain == "context":
            return context.get(attr)

        return None

    @staticmethod
    def _evaluate_condition(
        actual_value: object,
        operator: ConditionOperator,
        expected_value: object,
    ) -> bool:
        """Evaluate a single condition."""
        # Normalize enums
        if hasattr(actual_value, 'value'):
            actual_value = actual_value.value

        if operator == ConditionOperator.EQUALS:
            return str(actual_value) == str(expected_value)
        elif operator == ConditionOperator.NOT_EQUALS:
            return str(actual_value) != str(expected_value)
        elif operator == ConditionOperator.CONTAINS:
            return str(expected_value) in str(actual_value)
        elif operator == ConditionOperator.GREATER_THAN:
            return float(actual_value or 0) > float(expected_value or 0)
        elif operator == ConditionOperator.LESS_THAN:
            return float(actual_value or 0) < float(expected_value or 0)
        elif operator == ConditionOperator.IN_LIST:
            return str(actual_value) in (expected_value if isinstance(expected_value, list) else [])
        elif operator == ConditionOperator.IS_EMPTY:
            return actual_value is None or actual_value == ""
        elif operator == ConditionOperator.IS_NOT_EMPTY:
            return actual_value is not None and actual_value != ""

        return False

    @staticmethod
    def _execute_action(
        action: AutomationAction,
        assignment: WorkflowAssignment,
        entity_type: Optional[str],
        entity_id: Optional[UUID],
        context: dict,
        db: Session,
    ) -> dict:
        """Execute a single automation action."""
        config = action.config or {}
        action_type = action.action_type

        try:
            if action_type == ActionType.SEND_EMAIL:
                return AutomationEngine._action_send_email(
                    config, assignment, context, db
                )
            elif action_type == ActionType.SEND_IN_APP:
                return AutomationEngine._action_send_in_app(
                    config, assignment, context, db
                )
            elif action_type == ActionType.ASSIGN_TASK:
                return AutomationEngine._action_assign_task(
                    config, assignment, db
                )
            elif action_type == ActionType.UPDATE_STATUS:
                return AutomationEngine._action_update_status(
                    config, assignment, db
                )
            elif action_type == ActionType.NOTIFY_TEAM:
                return AutomationEngine._action_notify_team(
                    config, assignment, context, db
                )
            elif action_type == ActionType.CREATE_TASK:
                return AutomationEngine._action_create_task(
                    config, assignment, db
                )
            elif action_type == ActionType.WEBHOOK:
                return {"success": True, "action": "webhook", "detail": "Webhook placeholder"}
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"success": False, "error": str(e)}

    # ── Action Implementations ──

    @staticmethod
    def _action_send_email(
        config: dict, assignment: WorkflowAssignment, context: dict, db: Session
    ) -> dict:
        """Send email to a target user/role."""
        target = config.get("to", "assigned_by")
        subject = config.get("subject", "Workflow Update")
        body_template = config.get("body_template", "An automated update from your workflow.")

        # Resolve merge fields
        from app.models.workflow import Workflow
        workflow = db.query(Workflow).filter(Workflow.id == assignment.workflow_id).first()
        client = db.query(Client).filter(Client.id == assignment.client_id).first()

        body = body_template.replace(
            "{{workflow_name}}", workflow.name if workflow else ""
        ).replace(
            "{{client_name}}", client.name if client else ""
        ).replace(
            "{{assignment_id}}", str(assignment.id)
        ).replace(
            "{{due_date}}", str(assignment.due_date) if assignment.due_date else "Not set"
        )

        subject = subject.replace(
            "{{workflow_name}}", workflow.name if workflow else ""
        ).replace(
            "{{client_name}}", client.name if client else ""
        )

        # Resolve recipient
        user_id = None
        if target == "assigned_by":
            user_id = assignment.assigned_by
        elif target == "client":
            pass  # Future: email client directly
        else:
            try:
                user_id = UUID(target)
            except (ValueError, AttributeError):
                pass

        if user_id:
            NotificationService.create_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.GENERAL,
                title=subject,
                message=body,
                link=f"/dashboard/assignments/{assignment.id}",
            )

        return {"success": True, "action": "send_email", "to": str(user_id)}

    @staticmethod
    def _action_send_in_app(
        config: dict, assignment: WorkflowAssignment, context: dict, db: Session
    ) -> dict:
        """Send in-app notification."""
        target = config.get("to", "assigned_by")
        message = config.get("message", "Automated notification")

        user_id = None
        if target == "assigned_by":
            user_id = assignment.assigned_by
        else:
            try:
                user_id = UUID(target)
            except (ValueError, AttributeError):
                pass

        if user_id:
            NotificationService.create_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.GENERAL,
                title="Workflow Update",
                message=message,
                link=f"/dashboard/assignments/{assignment.id}",
            )

        return {"success": True, "action": "send_in_app", "to": str(user_id)}

    @staticmethod
    def _action_assign_task(
        config: dict, assignment: WorkflowAssignment, db: Session
    ) -> dict:
        """Auto-assign a task to a specific user."""
        task_entity_id = config.get("task_entity_id")
        assign_to = config.get("assign_to_user_id")

        if not task_entity_id or not assign_to:
            return {"success": False, "error": "Missing task_entity_id or assign_to_user_id"}

        task = db.query(AssignmentWorkflowTask).filter(
            AssignmentWorkflowTask.id == UUID(task_entity_id)
        ).first()

        if task:
            task.assigned_to = UUID(assign_to)
            task.updated_at = datetime.utcnow()
            db.flush()

            NotificationService.notify_task_assigned(
                db=db,
                task_name=task.name,
                assignment_name=f"Assignment {assignment.id}",
                assigned_to=UUID(assign_to),
                assignment_id=assignment.id,
            )

        return {"success": True, "action": "assign_task", "task_id": task_entity_id}

    @staticmethod
    def _action_update_status(
        config: dict, assignment: WorkflowAssignment, db: Session
    ) -> dict:
        """Update the status of an entity."""
        entity_type = config.get("entity_type")
        entity_id = config.get("entity_id")
        new_status = config.get("new_status")

        if not all([entity_type, entity_id, new_status]):
            return {"success": False, "error": "Missing entity_type, entity_id, or new_status"}

        if entity_type == "stage":
            entity = db.query(AssignmentWorkflowStage).filter(
                AssignmentWorkflowStage.id == UUID(entity_id)
            ).first()
        elif entity_type == "step":
            entity = db.query(AssignmentWorkflowStep).filter(
                AssignmentWorkflowStep.id == UUID(entity_id)
            ).first()
        elif entity_type == "task":
            entity = db.query(AssignmentWorkflowTask).filter(
                AssignmentWorkflowTask.id == UUID(entity_id)
            ).first()
        else:
            return {"success": False, "error": f"Unknown entity_type: {entity_type}"}

        if entity:
            entity.status = new_status
            entity.updated_at = datetime.utcnow()
            db.flush()

        return {"success": True, "action": "update_status", "entity": entity_type, "new_status": new_status}

    @staticmethod
    def _action_notify_team(
        config: dict, assignment: WorkflowAssignment, context: dict, db: Session
    ) -> dict:
        """Send notification to all team members with specified roles."""
        message_template = config.get("message_template", "Workflow update")
        target_roles = config.get("target_roles", ["manager", "admin"])

        # Resolve merge fields
        from app.models.workflow import Workflow
        workflow = db.query(Workflow).filter(Workflow.id == assignment.workflow_id).first()
        client = db.query(Client).filter(Client.id == assignment.client_id).first()

        message = message_template.replace(
            "{{workflow_name}}", workflow.name if workflow else ""
        ).replace(
            "{{client_name}}", client.name if client else ""
        ).replace(
            "{{assignment_id}}", str(assignment.id)
        )

        # Find users with matching roles
        role_map = {
            "admin": UserRole.ADMIN,
            "manager": UserRole.MANAGER,
            "enduser": UserRole.ENDUSER,
            "client": UserRole.CLIENT,
        }

        notified = 0
        for role_str in target_roles:
            role_enum = role_map.get(role_str.lower())
            if not role_enum:
                continue
            users = db.query(User).filter(
                User.role == role_enum,
                User.is_active == True,
            ).all()
            for user in users:
                NotificationService.create_notification(
                    db=db,
                    user_id=user.id,
                    notification_type=NotificationType.GENERAL,
                    title="Team Notification",
                    message=message,
                    link=f"/dashboard/assignments/{assignment.id}",
                )
                notified += 1

        return {"success": True, "action": "notify_team", "notified_count": notified}

    @staticmethod
    def _action_create_task(
        config: dict, assignment: WorkflowAssignment, db: Session
    ) -> dict:
        """Dynamically create a new task in a step."""
        step_id = config.get("step_id")
        task_name = config.get("name", "Auto-created task")
        assigned_to = config.get("assigned_to")

        if not step_id:
            return {"success": False, "error": "Missing step_id"}

        # Get max order in step
        from sqlalchemy import func
        max_order = db.query(func.max(AssignmentWorkflowTask.order)).filter(
            AssignmentWorkflowTask.step_id == UUID(step_id)
        ).scalar() or 0

        new_task = AssignmentWorkflowTask(
            step_id=UUID(step_id),
            template_task_id=UUID("00000000-0000-0000-0000-000000000000"),
            name=task_name,
            description=config.get("description"),
            order=max_order + 1,
            status="not_started",
            assigned_to=UUID(assigned_to) if assigned_to else None,
        )
        db.add(new_task)
        db.flush()

        return {"success": True, "action": "create_task", "task_id": str(new_task.id)}


class SOPService:
    """Manages Standard Operating Procedures attached to workflow entities."""

    @staticmethod
    def create_sop(
        workflow_id: UUID,
        entity_type: str,
        entity_id: UUID,
        title: str,
        content: str,
        checklist: Optional[list] = None,
        position: int = 0,
        created_by: Optional[UUID] = None,
        db: Session = None,
    ) -> WorkflowSOP:
        sop = WorkflowSOP(
            workflow_id=workflow_id,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            content=content,
            checklist=checklist,
            position=position,
            created_by=created_by,
        )
        db.add(sop)
        db.commit()
        db.refresh(sop)
        return sop

    @staticmethod
    def list_sops(
        entity_type: str, entity_id: UUID, db: Session
    ) -> list[WorkflowSOP]:
        return db.query(WorkflowSOP).filter(
            WorkflowSOP.entity_type == entity_type,
            WorkflowSOP.entity_id == entity_id,
        ).order_by(WorkflowSOP.position).all()

    @staticmethod
    def list_workflow_sops(workflow_id: UUID, db: Session) -> list[WorkflowSOP]:
        return db.query(WorkflowSOP).filter(
            WorkflowSOP.workflow_id == workflow_id,
        ).order_by(WorkflowSOP.entity_type, WorkflowSOP.position).all()

    @staticmethod
    def get_sop(sop_id: UUID, db: Session) -> Optional[WorkflowSOP]:
        return db.query(WorkflowSOP).filter(WorkflowSOP.id == sop_id).first()

    @staticmethod
    def update_sop(
        sop_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        checklist: Optional[list] = None,
        position: Optional[int] = None,
        db: Session = None,
    ) -> Optional[WorkflowSOP]:
        sop = db.query(WorkflowSOP).filter(WorkflowSOP.id == sop_id).first()
        if not sop:
            return None
        if title is not None:
            sop.title = title
        if content is not None:
            sop.content = content
        if checklist is not None:
            sop.checklist = checklist
        if position is not None:
            sop.position = position
        sop.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(sop)
        return sop

    @staticmethod
    def delete_sop(sop_id: UUID, db: Session) -> bool:
        sop = db.query(WorkflowSOP).filter(WorkflowSOP.id == sop_id).first()
        if not sop:
            return False
        db.delete(sop)
        db.commit()
        return True


class RecurringScheduleService:
    """Manages recurring workflow assignment schedules."""

    @staticmethod
    def create_schedule(
        workflow_id: UUID,
        organization_id: UUID,
        name: str,
        frequency: str,
        start_date: datetime,
        client_id: Optional[UUID] = None,
        description: Optional[str] = None,
        default_priority: str = "medium",
        auto_activate: bool = False,
        end_date: Optional[datetime] = None,
        custom_interval_days: Optional[int] = None,
        created_by: Optional[UUID] = None,
        db: Session = None,
    ) -> RecurringSchedule:
        next_run = RecurringScheduleService._calculate_next_run(
            start_date, RecurrenceFrequency(frequency), custom_interval_days
        )
        schedule = RecurringSchedule(
            workflow_id=workflow_id,
            organization_id=organization_id,
            name=name,
            description=description,
            frequency=RecurrenceFrequency(frequency),
            custom_interval_days=custom_interval_days,
            client_id=client_id,
            default_priority=default_priority,
            auto_activate=auto_activate,
            start_date=start_date,
            end_date=end_date,
            next_run_at=next_run,
            is_active=True,
            created_by=created_by,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def list_schedules(
        organization_id: Optional[UUID] = None,
        workflow_id: Optional[UUID] = None,
        db: Session = None,
    ) -> list[RecurringSchedule]:
        query = db.query(RecurringSchedule)
        if organization_id:
            query = query.filter(RecurringSchedule.organization_id == organization_id)
        if workflow_id:
            query = query.filter(RecurringSchedule.workflow_id == workflow_id)
        return query.order_by(RecurringSchedule.next_run_at).all()

    @staticmethod
    def get_schedule(schedule_id: UUID, db: Session) -> Optional[RecurringSchedule]:
        return db.query(RecurringSchedule).filter(
            RecurringSchedule.id == schedule_id
        ).first()

    @staticmethod
    def update_schedule(
        schedule_id: UUID,
        db: Session,
        name: Optional[str] = None,
        frequency: Optional[str] = None,
        is_active: Optional[bool] = None,
        end_date: Optional[datetime] = None,
        default_priority: Optional[str] = None,
        auto_activate: Optional[bool] = None,
        custom_interval_days: Optional[int] = None,
    ) -> Optional[RecurringSchedule]:
        schedule = db.query(RecurringSchedule).filter(
            RecurringSchedule.id == schedule_id
        ).first()
        if not schedule:
            return None
        if name is not None:
            schedule.name = name
        if frequency is not None:
            schedule.frequency = RecurrenceFrequency(frequency)
        if is_active is not None:
            schedule.is_active = is_active
        if end_date is not None:
            schedule.end_date = end_date
        if default_priority is not None:
            schedule.default_priority = default_priority
        if auto_activate is not None:
            schedule.auto_activate = auto_activate
        if custom_interval_days is not None:
            schedule.custom_interval_days = custom_interval_days
        schedule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def delete_schedule(schedule_id: UUID, db: Session) -> bool:
        schedule = db.query(RecurringSchedule).filter(
            RecurringSchedule.id == schedule_id
        ).first()
        if not schedule:
            return False
        db.delete(schedule)
        db.commit()
        return True

    @staticmethod
    def process_due_schedules(db: Session) -> list[dict]:
        """
        Process all schedules that are due to run.
        Creates assignments and advances next_run_at.
        Called by a background scheduler / cron job.
        """
        now = datetime.utcnow()
        due_schedules = db.query(RecurringSchedule).filter(
            RecurringSchedule.is_active == True,
            RecurringSchedule.next_run_at <= now,
        ).all()

        results = []
        for schedule in due_schedules:
            # Check end date
            if schedule.end_date and now > schedule.end_date:
                schedule.is_active = False
                db.flush()
                continue

            # Determine target clients
            clients = []
            if schedule.client_id:
                client = db.query(Client).filter(Client.id == schedule.client_id).first()
                if client:
                    clients = [client]
            else:
                clients = db.query(Client).filter(
                    Client.status == "active",
                ).all()

            created_assignments = []
            for client in clients:
                assignment = WorkflowAssignment(
                    workflow_id=schedule.workflow_id,
                    client_id=client.id,
                    organization_id=schedule.organization_id,
                    assigned_by=schedule.created_by,
                    status="draft",
                    priority=schedule.default_priority,
                    notes=f"Auto-created by recurring schedule: {schedule.name}",
                )
                db.add(assignment)
                db.flush()

                if schedule.auto_activate:
                    from app.services.assignment_service import AssignmentService
                    AssignmentService.activate_assignment(assignment.id, db)
                    assignment.status = "active"

                created_assignments.append(str(assignment.id))

            # Update schedule
            schedule.last_run_at = now
            schedule.total_runs += 1
            schedule.next_run_at = RecurringScheduleService._calculate_next_run(
                now, schedule.frequency, schedule.custom_interval_days
            )
            db.flush()

            results.append({
                "schedule_id": str(schedule.id),
                "schedule_name": schedule.name,
                "assignments_created": created_assignments,
                "next_run_at": schedule.next_run_at.isoformat(),
            })

        db.commit()
        return results

    @staticmethod
    def _calculate_next_run(
        from_date: datetime,
        frequency: RecurrenceFrequency,
        custom_interval_days: Optional[int] = None,
    ) -> datetime:
        """Calculate the next run date based on frequency."""
        if frequency == RecurrenceFrequency.DAILY:
            return from_date + timedelta(days=1)
        elif frequency == RecurrenceFrequency.WEEKLY:
            return from_date + timedelta(weeks=1)
        elif frequency == RecurrenceFrequency.BIWEEKLY:
            return from_date + timedelta(weeks=2)
        elif frequency == RecurrenceFrequency.MONTHLY:
            return from_date + timedelta(days=30)
        elif frequency == RecurrenceFrequency.QUARTERLY:
            return from_date + timedelta(days=91)
        elif frequency == RecurrenceFrequency.SEMI_ANNUALLY:
            return from_date + timedelta(days=182)
        elif frequency == RecurrenceFrequency.ANNUALLY:
            return from_date + timedelta(days=365)
        elif frequency == RecurrenceFrequency.CUSTOM:
            days = custom_interval_days or 30
            return from_date + timedelta(days=days)
        return from_date + timedelta(days=30)


class AutomationRuleService:
    """CRUD operations for automation rules, conditions, and actions."""

    @staticmethod
    def create_rule(
        workflow_id: UUID,
        name: str,
        trigger_event: str,
        trigger_entity_type: Optional[str] = None,
        trigger_entity_id: Optional[UUID] = None,
        description: Optional[str] = None,
        priority: int = 0,
        created_by: Optional[UUID] = None,
        db: Session = None,
    ) -> AutomationRule:
        rule = AutomationRule(
            workflow_id=workflow_id,
            name=name,
            description=description,
            trigger_event=TriggerEvent(trigger_event),
            trigger_entity_type=trigger_entity_type,
            trigger_entity_id=trigger_entity_id,
            priority=priority,
            created_by=created_by,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def list_rules(
        workflow_id: UUID, db: Session
    ) -> list[AutomationRule]:
        return db.query(AutomationRule).filter(
            AutomationRule.workflow_id == workflow_id
        ).order_by(AutomationRule.priority).all()

    @staticmethod
    def get_rule(rule_id: UUID, db: Session) -> Optional[AutomationRule]:
        return db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()

    @staticmethod
    def update_rule(
        rule_id: UUID,
        db: Session,
        name: Optional[str] = None,
        description: Optional[str] = None,
        trigger_event: Optional[str] = None,
        trigger_entity_type: Optional[str] = None,
        trigger_entity_id: Optional[UUID] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Optional[AutomationRule]:
        rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
        if not rule:
            return None
        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if trigger_event is not None:
            rule.trigger_event = TriggerEvent(trigger_event)
        if trigger_entity_type is not None:
            rule.trigger_entity_type = trigger_entity_type
        if trigger_entity_id is not None:
            rule.trigger_entity_id = trigger_entity_id
        if priority is not None:
            rule.priority = priority
        if status is not None:
            rule.status = AutomationRuleStatus(status)
        rule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete_rule(rule_id: UUID, db: Session) -> bool:
        rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
        if not rule:
            return False
        # Delete associated conditions and actions
        db.query(AutomationCondition).filter(AutomationCondition.rule_id == rule_id).delete()
        db.query(AutomationAction).filter(AutomationAction.rule_id == rule_id).delete()
        db.delete(rule)
        db.commit()
        return True

    # ── Conditions ──

    @staticmethod
    def add_condition(
        rule_id: UUID,
        field: str,
        operator: str,
        value: object = None,
        position: int = 0,
        db: Session = None,
    ) -> AutomationCondition:
        condition = AutomationCondition(
            rule_id=rule_id,
            field=field,
            operator=ConditionOperator(operator),
            value=value,
            position=position,
        )
        db.add(condition)
        db.commit()
        db.refresh(condition)
        return condition

    @staticmethod
    def list_conditions(
        rule_id: UUID, db: Session
    ) -> list[AutomationCondition]:
        return db.query(AutomationCondition).filter(
            AutomationCondition.rule_id == rule_id
        ).order_by(AutomationCondition.position).all()

    @staticmethod
    def delete_condition(condition_id: UUID, db: Session) -> bool:
        cond = db.query(AutomationCondition).filter(
            AutomationCondition.id == condition_id
        ).first()
        if not cond:
            return False
        db.delete(cond)
        db.commit()
        return True

    # ── Actions ──

    @staticmethod
    def add_action(
        rule_id: UUID,
        action_type: str,
        config: dict,
        position: int = 0,
        db: Session = None,
    ) -> AutomationAction:
        action = AutomationAction(
            rule_id=rule_id,
            action_type=ActionType(action_type),
            config=config,
            position=position,
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def list_actions(
        rule_id: UUID, db: Session
    ) -> list[AutomationAction]:
        return db.query(AutomationAction).filter(
            AutomationAction.rule_id == rule_id
        ).order_by(AutomationAction.position).all()

    @staticmethod
    def delete_action(action_id: UUID, db: Session) -> bool:
        action = db.query(AutomationAction).filter(
            AutomationAction.id == action_id
        ).first()
        if not action:
            return False
        db.delete(action)
        db.commit()
        return True

    # ── Execution Logs ──

    @staticmethod
    def get_execution_logs(
        rule_id: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
        limit: int = 50,
        db: Session = None,
    ) -> list[AutomationExecutionLog]:
        query = db.query(AutomationExecutionLog)
        if rule_id:
            query = query.filter(AutomationExecutionLog.rule_id == rule_id)
        if assignment_id:
            query = query.filter(AutomationExecutionLog.assignment_id == assignment_id)
        return query.order_by(AutomationExecutionLog.executed_at.desc()).limit(limit).all()
