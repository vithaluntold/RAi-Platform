from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.reminder import (
    ReminderCreate,
    ReminderSnooze,
    ReminderUpdate,
    ReminderResponse,
    ReminderCountResponse,
)
from app.services.reminder_service import ReminderService

router = APIRouter()


# ─── List my reminders ───

@router.get("/", response_model=list[ReminderResponse])
def list_reminders(
    status: Optional[str] = Query(None, description="Filter: pending | sent | snoozed | dismissed"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all reminders for the current user."""
    return ReminderService.get_user_reminders(
        db, user_id=current_user.id, status_filter=status, skip=skip, limit=limit
    )


# ─── Reminder counts ───

@router.get("/counts", response_model=ReminderCountResponse)
def get_reminder_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending/overdue counts for the badge in the UI."""
    return ReminderService.get_reminder_counts(db, user_id=current_user.id)


# ─── Create manual reminder ───

@router.post("/", response_model=ReminderResponse, status_code=201)
def create_reminder(
    body: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a manual reminder on an entity."""
    valid_types = {"assignment", "stage", "step", "task"}
    if body.entity_type not in valid_types:
        raise HTTPException(400, f"entity_type must be one of {valid_types}")

    return ReminderService.create_manual_reminder(
        db=db,
        user_id=current_user.id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        entity_name=body.entity_name,
        title=body.title,
        message=body.message,
        remind_at=body.remind_at,
        link=body.link,
        created_by=current_user.id,
    )


# ─── Get single reminder ───

@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = ReminderService.get_reminder_by_id(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    return reminder


# ─── Update reminder ───

@router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: UUID,
    body: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = body.model_dump(exclude_unset=True)
    reminder = ReminderService.update_reminder(db, reminder_id, current_user.id, data)
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    return reminder


# ─── Snooze reminder ───

@router.post("/{reminder_id}/snooze", response_model=ReminderResponse)
def snooze_reminder(
    reminder_id: UUID,
    body: ReminderSnooze,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Snooze a reminder — resets to pending at the new time. State in DB."""
    reminder = ReminderService.snooze_reminder(
        db, reminder_id, current_user.id, body.snooze_until
    )
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    return reminder


# ─── Dismiss reminder ───

@router.post("/{reminder_id}/dismiss", response_model=ReminderResponse)
def dismiss_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss a reminder permanently."""
    reminder = ReminderService.dismiss_reminder(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    return reminder


# ─── Delete reminder ───

@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hard delete a reminder."""
    deleted = ReminderService.delete_reminder(db, reminder_id, current_user.id)
    if not deleted:
        raise HTTPException(404, "Reminder not found")
