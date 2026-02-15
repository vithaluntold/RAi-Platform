"""
Automation API Endpoints
Dependencies, IF/THEN Rules, SOPs, Recurring Schedules, Execution Logs
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.services.automation_service import (
    DependencyService,
    AutomationEngine,
    AutomationRuleService,
    SOPService,
    RecurringScheduleService,
)
from app.schemas.automation import (
    DependencyCreate,
    AutomationRuleCreate,
    AutomationRuleUpdate,
    ConditionCreate,
    ActionCreate,
    SOPCreate,
    SOPUpdate,
    RecurringScheduleCreate,
    RecurringScheduleUpdate,
)

router = APIRouter()


# ════════════════════════════════════════════════════════════════════
#  DEPENDENCIES
# ════════════════════════════════════════════════════════════════════

@router.post("/dependencies/{workflow_id}")
def create_dependency(
    workflow_id: UUID,
    payload: DependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Add a dependency between workflow entities."""
    dep = DependencyService.create_dependency(
        workflow_id=workflow_id,
        dependency_type=payload.dependency_type,
        source_entity_type=payload.source_entity_type,
        source_entity_id=payload.source_entity_id,
        target_entity_type=payload.target_entity_type,
        target_entity_id=payload.target_entity_id,
        description=payload.description,
        created_by=current_user.id,
        db=db,
    )
    return _serialize_dependency(dep)


@router.get("/dependencies/{workflow_id}")
def list_dependencies(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all dependencies for a workflow template."""
    deps = DependencyService.list_dependencies(workflow_id, db)
    return [_serialize_dependency(d) for d in deps]


@router.delete("/dependencies/item/{dependency_id}")
def delete_dependency(
    dependency_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a workflow dependency."""
    if not DependencyService.delete_dependency(dependency_id, db):
        raise HTTPException(status_code=404, detail="Dependency not found")
    return {"detail": "Dependency deleted"}


@router.get("/dependencies/assignment/{assignment_id}")
def get_assignment_dependencies(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.ENDUSER)),
):
    """View all dependencies for an active assignment."""
    deps = DependencyService.get_assignment_dependencies(assignment_id, db)
    return [
        {
            "id": str(d.id),
            "assignment_id": str(d.assignment_id),
            "dependency_type": d.dependency_type.value if hasattr(d.dependency_type, 'value') else str(d.dependency_type),
            "source_entity_type": d.source_entity_type,
            "source_entity_id": str(d.source_entity_id),
            "target_entity_type": d.target_entity_type,
            "target_entity_id": str(d.target_entity_id),
            "is_satisfied": d.is_satisfied,
            "satisfied_at": d.satisfied_at,
            "description": d.description,
        }
        for d in deps
    ]


@router.get("/dependencies/assignment/{assignment_id}/check")
def check_dependency(
    assignment_id: UUID,
    target_entity_type: str = Query(...),
    target_entity_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.ENDUSER)),
):
    """Check if dependencies are satisfied for a target entity in an assignment."""
    return DependencyService.check_dependencies_satisfied(
        assignment_id, target_entity_type, target_entity_id, db
    )


# ════════════════════════════════════════════════════════════════════
#  AUTOMATION RULES
# ════════════════════════════════════════════════════════════════════

@router.post("/rules/{workflow_id}")
def create_rule(
    workflow_id: UUID,
    payload: AutomationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Create a new automation rule (IF/THEN logic)."""
    rule = AutomationRuleService.create_rule(
        workflow_id=workflow_id,
        name=payload.name,
        trigger_event=payload.trigger_event,
        trigger_entity_type=payload.trigger_entity_type,
        trigger_entity_id=payload.trigger_entity_id,
        description=payload.description,
        priority=payload.priority,
        created_by=current_user.id,
        db=db,
    )
    return _serialize_rule(rule)


@router.get("/rules/{workflow_id}")
def list_rules(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all automation rules for a workflow."""
    rules = AutomationRuleService.list_rules(workflow_id, db)
    return [_serialize_rule(r) for r in rules]


@router.get("/rules/detail/{rule_id}")
def get_rule_detail(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get a rule with its conditions and actions."""
    rule = AutomationRuleService.get_rule(rule_id, db)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    conditions = AutomationRuleService.list_conditions(rule_id, db)
    actions = AutomationRuleService.list_actions(rule_id, db)
    result = _serialize_rule(rule)
    result["conditions"] = [_serialize_condition(c) for c in conditions]
    result["actions"] = [_serialize_action(a) for a in actions]
    return result


@router.patch("/rules/detail/{rule_id}")
def update_rule(
    rule_id: UUID,
    payload: AutomationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Update an automation rule."""
    rule = AutomationRuleService.update_rule(
        rule_id=rule_id,
        db=db,
        name=payload.name,
        description=payload.description,
        trigger_event=payload.trigger_event,
        trigger_entity_type=payload.trigger_entity_type,
        trigger_entity_id=payload.trigger_entity_id,
        priority=payload.priority,
        status=payload.status,
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _serialize_rule(rule)


@router.delete("/rules/detail/{rule_id}")
def delete_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete an automation rule and its conditions/actions."""
    if not AutomationRuleService.delete_rule(rule_id, db):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"detail": "Rule deleted"}


# ── Conditions ──────────────────────────────────────────────────────

@router.post("/rules/{rule_id}/conditions")
def add_condition(
    rule_id: UUID,
    payload: ConditionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Add a condition (IF-clause) to an automation rule."""
    condition = AutomationRuleService.add_condition(
        rule_id=rule_id,
        field=payload.field,
        operator=payload.operator,
        value=payload.value,
        position=payload.position,
        db=db,
    )
    return _serialize_condition(condition)


@router.get("/rules/{rule_id}/conditions")
def list_conditions(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List conditions for a rule."""
    conditions = AutomationRuleService.list_conditions(rule_id, db)
    return [_serialize_condition(c) for c in conditions]


@router.delete("/conditions/{condition_id}")
def delete_condition(
    condition_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Delete a condition."""
    if not AutomationRuleService.delete_condition(condition_id, db):
        raise HTTPException(status_code=404, detail="Condition not found")
    return {"detail": "Condition deleted"}


# ── Actions ─────────────────────────────────────────────────────────

@router.post("/rules/{rule_id}/actions")
def add_action(
    rule_id: UUID,
    payload: ActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Add an action (THEN-clause) to an automation rule."""
    action = AutomationRuleService.add_action(
        rule_id=rule_id,
        action_type=payload.action_type,
        config=payload.config,
        position=payload.position,
        db=db,
    )
    return _serialize_action(action)


@router.get("/rules/{rule_id}/actions")
def list_actions(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List actions for a rule."""
    actions = AutomationRuleService.list_actions(rule_id, db)
    return [_serialize_action(a) for a in actions]


@router.delete("/actions/{action_id}")
def delete_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Delete an action."""
    if not AutomationRuleService.delete_action(action_id, db):
        raise HTTPException(status_code=404, detail="Action not found")
    return {"detail": "Action deleted"}


# ── Execution Logs ──────────────────────────────────────────────────

@router.get("/logs")
def get_logs(
    rule_id: Optional[UUID] = Query(None),
    assignment_id: Optional[UUID] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """View automation execution logs."""
    logs = AutomationRuleService.get_execution_logs(
        rule_id=rule_id, assignment_id=assignment_id, limit=limit, db=db
    )
    return [
        {
            "id": str(log.id),
            "rule_id": str(log.rule_id),
            "assignment_id": str(log.assignment_id) if log.assignment_id else None,
            "trigger_event": log.trigger_event,
            "trigger_entity_type": log.trigger_entity_type,
            "trigger_entity_id": str(log.trigger_entity_id) if log.trigger_entity_id else None,
            "conditions_met": log.conditions_met,
            "condition_details": log.condition_details,
            "actions_executed": log.actions_executed,
            "success": log.success,
            "error_message": log.error_message,
            "executed_at": log.executed_at,
        }
        for log in logs
    ]


# ════════════════════════════════════════════════════════════════════
#  SOPs (Standard Operating Procedures)
# ════════════════════════════════════════════════════════════════════

@router.post("/sops/{workflow_id}")
def create_sop(
    workflow_id: UUID,
    payload: SOPCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Attach an SOP to a workflow entity (stage, step, task, or workflow)."""
    sop = SOPService.create_sop(
        workflow_id=workflow_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        title=payload.title,
        content=payload.content,
        checklist=payload.checklist,
        position=payload.position,
        created_by=current_user.id,
        db=db,
    )
    return _serialize_sop(sop)


@router.get("/sops/{workflow_id}")
def list_workflow_sops(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.ENDUSER)),
):
    """List all SOPs for a workflow."""
    sops = SOPService.list_workflow_sops(workflow_id, db)
    return [_serialize_sop(s) for s in sops]


@router.get("/sops/entity/{entity_type}/{entity_id}")
def list_entity_sops(
    entity_type: str,
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.ENDUSER)),
):
    """List SOPs attached to a specific entity."""
    sops = SOPService.list_sops(entity_type, entity_id, db)
    return [_serialize_sop(s) for s in sops]


@router.patch("/sops/item/{sop_id}")
def update_sop(
    sop_id: UUID,
    payload: SOPUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Update an SOP."""
    sop = SOPService.update_sop(
        sop_id=sop_id,
        title=payload.title,
        content=payload.content,
        checklist=payload.checklist,
        position=payload.position,
        db=db,
    )
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")
    return _serialize_sop(sop)


@router.delete("/sops/item/{sop_id}")
def delete_sop(
    sop_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete an SOP."""
    if not SOPService.delete_sop(sop_id, db):
        raise HTTPException(status_code=404, detail="SOP not found")
    return {"detail": "SOP deleted"}


# ════════════════════════════════════════════════════════════════════
#  RECURRING SCHEDULES
# ════════════════════════════════════════════════════════════════════

@router.post("/schedules")
def create_schedule(
    payload: RecurringScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Create a recurring assignment schedule."""
    schedule = RecurringScheduleService.create_schedule(
        workflow_id=payload.workflow_id,
        organization_id=payload.organization_id,
        name=payload.name,
        frequency=payload.frequency,
        start_date=payload.start_date,
        client_id=payload.client_id,
        description=payload.description,
        default_priority=payload.default_priority,
        auto_activate=payload.auto_activate,
        end_date=payload.end_date,
        custom_interval_days=payload.custom_interval_days,
        created_by=current_user.id,
        db=db,
    )
    return _serialize_schedule(schedule)


@router.get("/schedules")
def list_schedules(
    workflow_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List recurring schedules."""
    schedules = RecurringScheduleService.list_schedules(
        organization_id=None,
        workflow_id=workflow_id,
        db=db,
    )
    return [_serialize_schedule(s) for s in schedules]


@router.get("/schedules/{schedule_id}")
def get_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get a specific recurring schedule."""
    schedule = RecurringScheduleService.get_schedule(schedule_id, db)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _serialize_schedule(schedule)


@router.patch("/schedules/{schedule_id}")
def update_schedule(
    schedule_id: UUID,
    payload: RecurringScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Update a recurring schedule."""
    schedule = RecurringScheduleService.update_schedule(
        schedule_id=schedule_id,
        db=db,
        name=payload.name,
        frequency=payload.frequency,
        is_active=payload.is_active,
        end_date=payload.end_date,
        default_priority=payload.default_priority,
        auto_activate=payload.auto_activate,
        custom_interval_days=payload.custom_interval_days,
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _serialize_schedule(schedule)


@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a recurring schedule."""
    if not RecurringScheduleService.delete_schedule(schedule_id, db):
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"detail": "Schedule deleted"}


@router.post("/schedules/process")
def process_due_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Manually trigger processing of all due recurring schedules."""
    results = RecurringScheduleService.process_due_schedules(db)
    return {"processed": len(results), "results": results}


# ════════════════════════════════════════════════════════════════════
#  TRIGGER (manual fire for testing)
# ════════════════════════════════════════════════════════════════════

@router.post("/trigger")
def manual_trigger(
    trigger_event: str = Query(...),
    assignment_id: UUID = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Manually fire a trigger event for testing automation rules."""
    results = AutomationEngine.fire_trigger(
        trigger_event=trigger_event,
        assignment_id=assignment_id,
        entity_type=entity_type,
        entity_id=entity_id,
        context={"user_id": str(current_user.id), "user_role": current_user.role.value},
        db=db,
    )
    return {"trigger_event": trigger_event, "rules_evaluated": len(results), "results": results}


# ════════════════════════════════════════════════════════════════════
#  SERIALIZERS
# ════════════════════════════════════════════════════════════════════

def _serialize_dependency(dep) -> dict:
    return {
        "id": str(dep.id),
        "workflow_id": str(dep.workflow_id),
        "dependency_type": dep.dependency_type.value if hasattr(dep.dependency_type, 'value') else str(dep.dependency_type),
        "source_entity_type": dep.source_entity_type,
        "source_entity_id": str(dep.source_entity_id),
        "target_entity_type": dep.target_entity_type,
        "target_entity_id": str(dep.target_entity_id),
        "description": dep.description,
        "created_at": dep.created_at,
        "created_by": str(dep.created_by) if dep.created_by else None,
    }


def _serialize_rule(rule) -> dict:
    return {
        "id": str(rule.id),
        "workflow_id": str(rule.workflow_id),
        "name": rule.name,
        "description": rule.description,
        "status": rule.status.value if hasattr(rule.status, 'value') else str(rule.status),
        "trigger_event": rule.trigger_event.value if hasattr(rule.trigger_event, 'value') else str(rule.trigger_event),
        "trigger_entity_type": rule.trigger_entity_type,
        "trigger_entity_id": str(rule.trigger_entity_id) if rule.trigger_entity_id else None,
        "priority": rule.priority,
        "created_by": str(rule.created_by) if rule.created_by else None,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


def _serialize_condition(cond) -> dict:
    return {
        "id": str(cond.id),
        "rule_id": str(cond.rule_id),
        "field": cond.field,
        "operator": cond.operator.value if hasattr(cond.operator, 'value') else str(cond.operator),
        "value": cond.value,
        "position": cond.position,
        "created_at": cond.created_at,
    }


def _serialize_action(action) -> dict:
    return {
        "id": str(action.id),
        "rule_id": str(action.rule_id),
        "action_type": action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type),
        "config": action.config,
        "position": action.position,
        "created_at": action.created_at,
    }


def _serialize_sop(sop) -> dict:
    return {
        "id": str(sop.id),
        "workflow_id": str(sop.workflow_id),
        "entity_type": sop.entity_type,
        "entity_id": str(sop.entity_id),
        "title": sop.title,
        "content": sop.content,
        "checklist": sop.checklist,
        "position": sop.position,
        "created_by": str(sop.created_by) if sop.created_by else None,
        "created_at": sop.created_at,
        "updated_at": sop.updated_at,
    }


def _serialize_schedule(schedule) -> dict:
    return {
        "id": str(schedule.id),
        "workflow_id": str(schedule.workflow_id),
        "organization_id": str(schedule.organization_id),
        "name": schedule.name,
        "description": schedule.description,
        "frequency": schedule.frequency.value if hasattr(schedule.frequency, 'value') else str(schedule.frequency),
        "custom_interval_days": schedule.custom_interval_days,
        "client_id": str(schedule.client_id) if schedule.client_id else None,
        "default_priority": schedule.default_priority,
        "auto_activate": schedule.auto_activate,
        "start_date": schedule.start_date,
        "end_date": schedule.end_date,
        "next_run_at": schedule.next_run_at,
        "last_run_at": schedule.last_run_at,
        "is_active": schedule.is_active,
        "total_runs": schedule.total_runs,
        "created_by": str(schedule.created_by) if schedule.created_by else None,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
    }
