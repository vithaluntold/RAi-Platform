"""
Pydantic Schemas for Automation, Dependencies, SOPs, Recurring Schedules
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


# ── Dependencies ────────────────────────────────────────────────────

class DependencyCreate(BaseModel):
    dependency_type: str = Field(..., description="intra_firm | client_firm | task_to_task | step_to_step | stage_to_stage")
    source_entity_type: str = Field(..., description="stage | step | task")
    source_entity_id: UUID
    target_entity_type: str = Field(..., description="stage | step | task")
    target_entity_id: UUID
    description: Optional[str] = None


class DependencyResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    dependency_type: str
    source_entity_type: str
    source_entity_id: UUID
    target_entity_type: str
    target_entity_id: UUID
    description: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class AssignmentDependencyResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    dependency_type: str
    source_entity_type: str
    source_entity_id: UUID
    target_entity_type: str
    target_entity_id: UUID
    is_satisfied: bool
    satisfied_at: Optional[datetime]
    description: Optional[str]

    class Config:
        from_attributes = True


class DependencyCheckResult(BaseModel):
    satisfied: bool
    blocking: List[dict] = []


# ── Automation Rules ────────────────────────────────────────────────

class AutomationRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_event: str = Field(..., description="stage_entered | stage_completed | step_completed | task_completed | assignment_activated | ...")
    trigger_entity_type: Optional[str] = None
    trigger_entity_id: Optional[UUID] = None
    priority: int = 0


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_event: Optional[str] = None
    trigger_entity_type: Optional[str] = None
    trigger_entity_id: Optional[UUID] = None
    priority: Optional[int] = None
    status: Optional[str] = None


class AutomationRuleResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    name: str
    description: Optional[str]
    status: str
    trigger_event: str
    trigger_entity_type: Optional[str]
    trigger_entity_id: Optional[UUID]
    priority: int
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Conditions ──────────────────────────────────────────────────────

class ConditionCreate(BaseModel):
    field: str = Field(..., description="Dot-path like assignment.status, client.type, context.user_role")
    operator: str = Field(..., description="equals | not_equals | contains | greater_than | less_than | in_list | is_empty | is_not_empty")
    value: Optional[Any] = None
    position: int = 0


class ConditionResponse(BaseModel):
    id: UUID
    rule_id: UUID
    field: str
    operator: str
    value: Optional[Any]
    position: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Actions ─────────────────────────────────────────────────────────

class ActionCreate(BaseModel):
    action_type: str = Field(..., description="send_email | send_in_app | assign_task | update_status | create_task | notify_team | webhook")
    config: dict = Field(default_factory=dict, description="Action-specific config")
    position: int = 0


class ActionResponse(BaseModel):
    id: UUID
    rule_id: UUID
    action_type: str
    config: dict
    position: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Rule with nested conditions/actions ─────────────────────────────

class AutomationRuleDetail(BaseModel):
    id: UUID
    workflow_id: UUID
    name: str
    description: Optional[str]
    status: str
    trigger_event: str
    trigger_entity_type: Optional[str]
    trigger_entity_id: Optional[UUID]
    priority: int
    conditions: List[ConditionResponse] = []
    actions: List[ActionResponse] = []
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── SOPs ────────────────────────────────────────────────────────────

class SOPCreate(BaseModel):
    entity_type: str = Field(..., description="stage | step | task | workflow")
    entity_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    checklist: Optional[List[dict]] = None
    position: int = 0


class SOPUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    checklist: Optional[List[dict]] = None
    position: Optional[int] = None


class SOPResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    entity_type: str
    entity_id: UUID
    title: str
    content: str
    checklist: Optional[List[dict]]
    position: int
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Recurring Schedules ─────────────────────────────────────────────

class RecurringScheduleCreate(BaseModel):
    workflow_id: UUID
    organization_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    frequency: str = Field(..., description="daily | weekly | biweekly | monthly | quarterly | semi_annually | annually | custom")
    custom_interval_days: Optional[int] = None
    client_id: Optional[UUID] = None
    default_priority: str = "medium"
    auto_activate: bool = False
    start_date: datetime
    end_date: Optional[datetime] = None


class RecurringScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    frequency: Optional[str] = None
    custom_interval_days: Optional[int] = None
    is_active: Optional[bool] = None
    default_priority: Optional[str] = None
    auto_activate: Optional[bool] = None
    end_date: Optional[datetime] = None


class RecurringScheduleResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    frequency: str
    custom_interval_days: Optional[int]
    client_id: Optional[UUID]
    default_priority: str
    auto_activate: bool
    start_date: datetime
    end_date: Optional[datetime]
    next_run_at: datetime
    last_run_at: Optional[datetime]
    is_active: bool
    total_runs: int
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Execution Logs ──────────────────────────────────────────────────

class ExecutionLogResponse(BaseModel):
    id: UUID
    rule_id: UUID
    assignment_id: Optional[UUID]
    trigger_event: str
    trigger_entity_type: Optional[str]
    trigger_entity_id: Optional[UUID]
    conditions_met: bool
    condition_details: Optional[List[dict]]
    actions_executed: Optional[List[dict]]
    success: bool
    error_message: Optional[str]
    executed_at: datetime

    class Config:
        from_attributes = True
