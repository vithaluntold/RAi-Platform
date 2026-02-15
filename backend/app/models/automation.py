"""
Workflow Automation Models
Dependencies, Triggers, Actions, Conditions, SOPs, Recurring Schedules, Parallel Execution
"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text,
    Enum as SQLEnum, JSON, Index, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


# ────────────────────────────────────────────────────────────────────
#  ENUMS
# ────────────────────────────────────────────────────────────────────

class DependencyType(str, Enum):
    """Type of dependency relationship."""
    INTRA_FIRM = "intra_firm"          # Team member A must finish before B starts
    CLIENT_FIRM = "client_firm"        # Client must act before firm proceeds
    TASK_TO_TASK = "task_to_task"      # Task B blocked until Task A completes
    STEP_TO_STEP = "step_to_step"     # Step B blocked until Step A completes
    STAGE_TO_STAGE = "stage_to_stage" # Stage B blocked until Stage A completes


class TriggerEvent(str, Enum):
    """Events that can fire an automation trigger."""
    STAGE_ENTERED = "stage_entered"
    STAGE_COMPLETED = "stage_completed"
    STEP_ENTERED = "step_entered"
    STEP_COMPLETED = "step_completed"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_ACTIVATED = "assignment_activated"
    ASSIGNMENT_COMPLETED = "assignment_completed"
    DUE_DATE_APPROACHING = "due_date_approaching"


class ActionType(str, Enum):
    """Types of automated actions."""
    SEND_EMAIL = "send_email"
    SEND_IN_APP = "send_in_app"
    ASSIGN_TASK = "assign_task"
    UPDATE_STATUS = "update_status"
    CREATE_TASK = "create_task"
    NOTIFY_TEAM = "notify_team"
    WEBHOOK = "webhook"


class ConditionOperator(str, Enum):
    """Operators for condition evaluation."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_LIST = "in_list"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class ExecutionMode(str, Enum):
    """How stages/steps execute relative to each other."""
    SEQUENTIAL = "sequential"  # Default - one after another
    PARALLEL = "parallel"      # Can run simultaneously


class RecurrenceFrequency(str, Enum):
    """Frequency for recurring assignments."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"
    CUSTOM = "custom"


class AutomationRuleStatus(str, Enum):
    """Status of an automation rule."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


# ────────────────────────────────────────────────────────────────────
#  DEPENDENCY MODEL (Template Level)
# ────────────────────────────────────────────────────────────────────

class WorkflowDependency(Base):
    """
    Defines dependency relationships between entities in a workflow template.
    E.g., Task B cannot start until Task A completes.
    """
    __tablename__ = "workflow_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Dependency type
    dependency_type = Column(
        SQLEnum(DependencyType),
        nullable=False,
    )

    # Source entity (must complete first)
    source_entity_type = Column(String(50), nullable=False)  # stage, step, task
    source_entity_id = Column(UUID(as_uuid=True), nullable=False)

    # Target entity (blocked until source completes)
    target_entity_type = Column(String(50), nullable=False)  # stage, step, task
    target_entity_id = Column(UUID(as_uuid=True), nullable=False)

    # Optional: description of the dependency
    description = Column(String(500), nullable=True)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index('idx_wf_dep_workflow', 'workflow_id'),
        Index('idx_wf_dep_source', 'source_entity_type', 'source_entity_id'),
        Index('idx_wf_dep_target', 'target_entity_type', 'target_entity_id'),
    )


# ────────────────────────────────────────────────────────────────────
#  DEPENDENCY MODEL (Assignment / Instance Level)
# ────────────────────────────────────────────────────────────────────

class AssignmentDependency(Base):
    """
    Cloned dependency for an assignment instance.
    Points to the cloned (assignment-level) entity IDs.
    """
    __tablename__ = "assignment_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Reference back to template dependency
    template_dependency_id = Column(UUID(as_uuid=True), nullable=True)

    dependency_type = Column(
        SQLEnum(DependencyType),
        nullable=False,
    )

    # Source (must complete first) — assignment-level entity IDs
    source_entity_type = Column(String(50), nullable=False)
    source_entity_id = Column(UUID(as_uuid=True), nullable=False)

    # Target (blocked until source completes) — assignment-level entity IDs
    target_entity_type = Column(String(50), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), nullable=False)

    # Whether this dependency is satisfied
    is_satisfied = Column(Boolean, default=False, nullable=False)
    satisfied_at = Column(DateTime, nullable=True)

    description = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_asgn_dep_assignment', 'assignment_id'),
        Index('idx_asgn_dep_target', 'target_entity_type', 'target_entity_id'),
    )


# ────────────────────────────────────────────────────────────────────
#  AUTOMATION RULE (Template Level)
# ────────────────────────────────────────────────────────────────────

class AutomationRule(Base):
    """
    IF/THEN automation attached to a workflow template.
    When a trigger event fires and conditions are met, actions execute.
    Supports conditional logic and automated communication.
    """
    __tablename__ = "automation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Status
    status = Column(
        SQLEnum(AutomationRuleStatus),
        default=AutomationRuleStatus.ACTIVE,
        nullable=False,
    )

    # Trigger: WHEN this event occurs...
    trigger_event = Column(
        SQLEnum(TriggerEvent),
        nullable=False,
    )

    # Optional: scope the trigger to a specific entity
    trigger_entity_type = Column(String(50), nullable=True)  # stage, step, task
    trigger_entity_id = Column(UUID(as_uuid=True), nullable=True)

    # Execution order (if multiple rules fire on same event)
    priority = Column(Integer, default=0, nullable=False)

    # Audit trail
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index('idx_auto_rules_workflow', 'workflow_id'),
        Index('idx_auto_rules_trigger', 'trigger_event'),
    )


# ────────────────────────────────────────────────────────────────────
#  AUTOMATION CONDITION (IF-clause of a rule)
# ────────────────────────────────────────────────────────────────────

class AutomationCondition(Base):
    """
    Condition that must be true for a rule's actions to fire.
    Multiple conditions per rule are evaluated with AND logic.
    E.g., IF client_type == 'corporate' AND priority == 'high'
    """
    __tablename__ = "automation_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # What field to evaluate
    field = Column(String(255), nullable=False)  # e.g. "assignment.priority", "client.type"

    # Operator
    operator = Column(
        SQLEnum(ConditionOperator),
        nullable=False,
    )

    # Value to compare against (stored as JSON for flexibility)
    value = Column(JSON, nullable=True)

    # Evaluation order
    position = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_auto_cond_rule', 'rule_id'),
    )


# ────────────────────────────────────────────────────────────────────
#  AUTOMATION ACTION (THEN-clause of a rule)
# ────────────────────────────────────────────────────────────────────

class AutomationAction(Base):
    """
    Action to execute when a rule's trigger fires and conditions are met.
    Multiple actions per rule execute in order.
    """
    __tablename__ = "automation_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Action type
    action_type = Column(
        SQLEnum(ActionType),
        nullable=False,
    )

    # Action configuration (type-specific payload)
    # For SEND_EMAIL: {"to": "assigned_user|client|specific_user_id", "subject": "...", "body_template": "..."}
    # For ASSIGN_TASK: {"task_entity_id": "...", "assign_to_user_id": "..."}
    # For UPDATE_STATUS: {"entity_type": "stage", "entity_id": "...", "new_status": "in_progress"}
    # For NOTIFY_TEAM: {"message_template": "...", "target_roles": ["manager", "admin"]}
    # For CREATE_TASK: {"step_id": "...", "name": "...", "assigned_to": "..."}
    config = Column(JSON, nullable=False, default=dict)

    # Execution order within the rule
    position = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_auto_action_rule', 'rule_id'),
    )


# ────────────────────────────────────────────────────────────────────
#  SOP EMBEDDING
# ────────────────────────────────────────────────────────────────────

class WorkflowSOP(Base):
    """
    Standard Operating Procedure attached to a workflow entity.
    Provides instructions, checklists, and documentation for team members.
    """
    __tablename__ = "workflow_sops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which entity this SOP is attached to
    entity_type = Column(String(50), nullable=False)  # workflow, stage, step, task
    entity_id = Column(UUID(as_uuid=True), nullable=False)

    # SOP content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)           # Markdown/rich text
    checklist = Column(JSON, nullable=True)           # Optional checklist items

    # Ordering when multiple SOPs on same entity
    position = Column(Integer, default=0, nullable=False)

    # Audit trail
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index('idx_wf_sop_workflow', 'workflow_id'),
        Index('idx_wf_sop_entity', 'entity_type', 'entity_id'),
    )


# ────────────────────────────────────────────────────────────────────
#  RECURRING SCHEDULE
# ────────────────────────────────────────────────────────────────────

class RecurringSchedule(Base):
    """
    Defines a recurring schedule for auto-creating assignments.
    When the schedule fires, a new assignment is created from the template.
    """
    __tablename__ = "recurring_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)

    # Recurrence settings
    frequency = Column(
        SQLEnum(RecurrenceFrequency),
        nullable=False,
    )
    custom_interval_days = Column(Integer, nullable=True)  # Only used when frequency=CUSTOM

    # Target client (null = applies to all active clients in org)
    client_id = Column(UUID(as_uuid=True), nullable=True)

    # Assignment defaults
    default_priority = Column(String(50), default="medium", nullable=False)
    auto_activate = Column(Boolean, default=False, nullable=False)  # Auto-activate assignments

    # Schedule timing
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)          # null = runs indefinitely
    next_run_at = Column(DateTime, nullable=False)       # Next scheduled execution
    last_run_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Counters
    total_runs = Column(Integer, default=0, nullable=False)

    # Audit trail
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index('idx_rec_sched_workflow', 'workflow_id'),
        Index('idx_rec_sched_org', 'organization_id'),
        Index('idx_rec_sched_next_run', 'is_active', 'next_run_at'),
    )


# ────────────────────────────────────────────────────────────────────
#  AUTOMATION EXECUTION LOG
# ────────────────────────────────────────────────────────────────────

class AutomationExecutionLog(Base):
    """
    Audit trail for automation rule executions.
    Records every time a rule fires, whether conditions passed, and action results.
    """
    __tablename__ = "automation_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assignment_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Trigger context
    trigger_event = Column(String(100), nullable=False)
    trigger_entity_type = Column(String(50), nullable=True)
    trigger_entity_id = Column(UUID(as_uuid=True), nullable=True)

    # Evaluation result
    conditions_met = Column(Boolean, nullable=False)
    condition_details = Column(JSON, nullable=True)  # Details of each condition evaluation

    # Action results
    actions_executed = Column(JSON, nullable=True)  # List of action results

    # Status
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_auto_exec_log_rule', 'rule_id'),
        Index('idx_auto_exec_log_assignment', 'assignment_id'),
    )
