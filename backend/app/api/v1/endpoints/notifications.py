from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_active_admin
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationMarkRead,
    NotificationCountResponse,
    NotificationSettingCreate,
    NotificationSettingUpdate,
    NotificationSettingResponse,
    UserNotificationPreferenceUpdate,
    UserNotificationPreferenceResponse,
    AdminUserPreferenceUpdate,
)
from app.services.notification_service import NotificationService

router = APIRouter()


# ─── User Notifications ───

@router.get("/", response_model=list[NotificationResponse])
def get_my_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's notifications."""
    return NotificationService.get_user_notifications(
        db=db, user_id=current_user.id, unread_only=unread_only, skip=skip, limit=limit
    )


@router.get("/count", response_model=NotificationCountResponse)
def get_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get unread notification count for current user."""
    unread = NotificationService.get_unread_count(db=db, user_id=current_user.id)
    from app.models.notification import Notification
    total = db.query(Notification).filter(Notification.user_id == current_user.id).count()
    return {"unread_count": unread, "total_count": total}


@router.patch("/read")
def mark_notifications_read(
    body: NotificationMarkRead,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark specific notifications as read."""
    count = NotificationService.mark_as_read(
        db=db, notification_ids=body.notification_ids, user_id=current_user.id
    )
    return {"marked_read": count}


@router.patch("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark all notifications as read for current user."""
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return {"marked_read": count}


# ─── User Notification Preferences ───

@router.get("/preferences", response_model=UserNotificationPreferenceResponse)
def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's notification preferences."""
    pref = NotificationService.get_user_preference(db=db, user_id=current_user.id)
    return pref


@router.patch("/preferences", response_model=UserNotificationPreferenceResponse)
def update_my_preferences(
    body: UserNotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update current user's notification preferences."""
    pref = NotificationService.update_user_preference(
        db=db,
        user_id=current_user.id,
        data=body.model_dump(exclude_unset=True),
        updated_by=current_user.id,
    )
    return pref


# ─── Admin: Notification Settings (Outlook Config) ───

@router.get("/settings", response_model=NotificationSettingResponse)
def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """Get admin notification settings (Outlook email config)."""
    settings = NotificationService.get_settings(db=db)
    if not settings:
        raise HTTPException(status_code=404, detail="No notification settings configured")
    return settings


@router.post("/settings", response_model=NotificationSettingResponse)
def create_or_update_notification_settings(
    body: NotificationSettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """Create or update admin notification settings (Outlook email config)."""
    settings = NotificationService.upsert_settings(db=db, data=body.model_dump())
    return settings


@router.patch("/settings", response_model=NotificationSettingResponse)
def patch_notification_settings(
    body: NotificationSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """Partially update admin notification settings."""
    settings = NotificationService.upsert_settings(
        db=db, data=body.model_dump(exclude_unset=True)
    )
    return settings


# ─── Admin: Per-User Notification Preferences ───

@router.get("/admin/user-preferences")
def get_all_user_preferences(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """Get all users' notification preferences (admin view)."""
    return NotificationService.get_all_user_preferences(db=db, skip=skip, limit=limit)


@router.patch("/admin/user-preferences", response_model=UserNotificationPreferenceResponse)
def admin_update_user_preferences(
    body: AdminUserPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """Admin updates a specific user's notification preferences."""
    pref = NotificationService.update_user_preference(
        db=db,
        user_id=body.user_id,
        data=body.model_dump(exclude_unset=True, exclude={"user_id"}),
        updated_by=current_user.id,
    )
    return pref
