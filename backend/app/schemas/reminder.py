from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ─── Request Schemas ───


class ReminderCreate(BaseModel):
    """Create a manual reminder on an entity."""
    entity_type: str = Field(..., description="assignment | stage | step | task")
    entity_id: UUID
    entity_name: str = Field(..., max_length=255)
    title: str = Field(..., max_length=255)
    message: str
    remind_at: datetime
    link: Optional[str] = None


class ReminderSnooze(BaseModel):
    """Snooze a reminder to a new time."""
    snooze_until: datetime


class ReminderUpdate(BaseModel):
    """Update reminder details."""
    title: Optional[str] = None
    message: Optional[str] = None
    remind_at: Optional[datetime] = None


# ─── Response Schemas ───


class ReminderResponse(BaseModel):
    id: UUID
    user_id: UUID
    entity_type: str
    entity_id: UUID
    entity_name: str
    reminder_type: str
    offset_label: Optional[str] = None
    title: str
    message: str
    link: Optional[str] = None
    remind_at: datetime
    status: str
    sent_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    snooze_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None

    model_config = {"from_attributes": True}


class ReminderCountResponse(BaseModel):
    pending: int
    overdue: int
    total: int
