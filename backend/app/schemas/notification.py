from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


# ─── Notification ───
class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    email_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationMarkRead(BaseModel):
    notification_ids: list[UUID]


class NotificationCountResponse(BaseModel):
    unread_count: int
    total_count: int


# ─── Notification Settings (Admin) ───
class NotificationSettingCreate(BaseModel):
    outlook_email: EmailStr
    outlook_client_id: str
    outlook_client_secret: str
    outlook_tenant_id: str
    is_enabled: bool = True


class NotificationSettingUpdate(BaseModel):
    outlook_email: Optional[EmailStr] = None
    outlook_client_id: Optional[str] = None
    outlook_client_secret: Optional[str] = None
    outlook_tenant_id: Optional[str] = None
    is_enabled: Optional[bool] = None


class NotificationSettingResponse(BaseModel):
    id: UUID
    outlook_email: str
    outlook_client_id: str
    outlook_tenant_id: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── User Notification Preferences ───
class UserNotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None


class UserNotificationPreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    email_enabled: bool
    in_app_enabled: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminUserPreferenceUpdate(BaseModel):
    """Admin updating a specific user's notification preferences."""
    user_id: UUID
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
