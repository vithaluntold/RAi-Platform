import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class ReminderType(str, enum.Enum):
    """Type of reminder — auto-generated vs manually created."""
    AUTO_DUE_DATE = "auto_due_date"
    MANUAL = "manual"


class ReminderStatus(str, enum.Enum):
    """Lifecycle status of a reminder."""
    PENDING = "pending"
    SENT = "sent"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"


class ReminderEntityType(str, enum.Enum):
    """Which entity this reminder is attached to."""
    ASSIGNMENT = "assignment"
    STAGE = "stage"
    STEP = "step"
    TASK = "task"


class ReminderOffset(str, enum.Enum):
    """Pre-defined offset labels for auto due-date reminders."""
    THREE_DAYS_BEFORE = "3_days_before"
    ONE_DAY_BEFORE = "1_day_before"
    ON_DUE_DATE = "on_due_date"
    ONE_DAY_OVERDUE = "1_day_overdue"


class Reminder(Base):
    """
    Persisted reminder — all state lives in DB so server restarts never
    cause duplicate or lost notifications.
    """
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who should receive this reminder
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What entity this reminder is about
    entity_type = Column(Enum(ReminderEntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entity_name = Column(String(255), nullable=False)

    # Reminder metadata
    reminder_type = Column(Enum(ReminderType), nullable=False, default=ReminderType.MANUAL)
    offset_label = Column(Enum(ReminderOffset), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)

    # When to fire the reminder (UTC)
    remind_at = Column(DateTime, nullable=False, index=True)

    # Lifecycle tracking — all persisted in DB, never in-memory
    status = Column(Enum(ReminderStatus), nullable=False, default=ReminderStatus.PENDING)
    sent_at = Column(DateTime, nullable=True)
    snoozed_until = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)

    # How many times this reminder has been snoozed
    snooze_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="reminders", lazy="joined")
