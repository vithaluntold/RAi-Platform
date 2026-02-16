import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.db.session import Base


class NotificationType(str, enum.Enum):
    TASK_COMPLETED = "task_completed"
    STEP_COMPLETED = "step_completed"
    STAGE_COMPLETED = "stage_completed"
    ASSIGNMENT_COMPLETED = "assignment_completed"
    TASK_ASSIGNED = "task_assigned"
    TASK_CREATED = "task_created"
    GENERAL = "general"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.GENERAL)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    email_sent = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref=backref("notifications", passive_deletes=True), lazy="joined")


class NotificationSetting(Base):
    """Admin-configured email settings for sending notification emails via Outlook."""
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlook_email = Column(String(255), nullable=False)
    outlook_client_id = Column(String(255), nullable=False)
    outlook_client_secret = Column(String(500), nullable=False)
    outlook_tenant_id = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserNotificationPreference(Base):
    """Per-user notification preferences. Admin or user can toggle."""
    __tablename__ = "user_notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref=backref("notification_preference", uselist=False, passive_deletes=True))
