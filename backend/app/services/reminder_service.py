import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.reminder import (
    Reminder,
    ReminderType,
    ReminderStatus,
    ReminderEntityType,
    ReminderOffset,
)
from app.models.notification import Notification, NotificationType
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Mapping from offset label → timedelta BEFORE due date (negative = after)
OFFSET_DELTAS = {
    ReminderOffset.THREE_DAYS_BEFORE: timedelta(days=3),
    ReminderOffset.ONE_DAY_BEFORE: timedelta(days=1),
    ReminderOffset.ON_DUE_DATE: timedelta(days=0),
    ReminderOffset.ONE_DAY_OVERDUE: timedelta(days=-1),
}


class ReminderService:
    """
    All reminder state is persisted in DB — no in-memory tracking.
    Safe across server restarts.
    """

    # ─── Manual Reminders (user-created) ───

    @staticmethod
    def create_manual_reminder(
        db: Session,
        user_id: UUID,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        title: str,
        message: str,
        remind_at: datetime,
        link: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> Reminder:
        """Create a user-defined reminder. State is fully in DB."""
        reminder = Reminder(
            user_id=user_id,
            entity_type=ReminderEntityType(entity_type),
            entity_id=entity_id,
            entity_name=entity_name,
            reminder_type=ReminderType.MANUAL,
            title=title,
            message=message,
            remind_at=remind_at,
            link=link,
            status=ReminderStatus.PENDING,
            created_by=created_by or user_id,
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    # ─── Auto Due-Date Reminders ───

    @staticmethod
    def generate_due_date_reminders(
        db: Session,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        due_date: datetime,
        assigned_to: UUID,
        assignment_id: Optional[UUID] = None,
    ) -> list[Reminder]:
        """
        Generate standard auto-reminders for a due date:
        - 3 days before
        - 1 day before
        - On due date
        - 1 day overdue

        Idempotent: skips if a reminder with the same entity + offset already exists.
        All state persisted in DB.
        """
        created = []
        link = f"/dashboard/assignments/{assignment_id}" if assignment_id else None

        for offset_label, delta in OFFSET_DELTAS.items():
            remind_at = due_date - delta  # subtract: positive delta = before due

            # Skip past reminders only if they were already sent
            # (allows generating reminders for items whose due date is approaching)

            # Idempotency: check if this exact reminder already exists
            existing = db.query(Reminder).filter(
                Reminder.entity_type == ReminderEntityType(entity_type),
                Reminder.entity_id == entity_id,
                Reminder.offset_label == offset_label,
                Reminder.reminder_type == ReminderType.AUTO_DUE_DATE,
            ).first()

            if existing:
                # If due date changed, update the remind_at time
                if existing.remind_at != remind_at:
                    existing.remind_at = remind_at
                    existing.updated_at = datetime.utcnow()
                    # If it was already sent but the new time is in the future, reset to pending
                    if existing.status == ReminderStatus.SENT and remind_at > datetime.utcnow():
                        existing.status = ReminderStatus.PENDING
                        existing.sent_at = None
                    db.flush()
                continue

            reminder = Reminder(
                user_id=assigned_to,
                entity_type=ReminderEntityType(entity_type),
                entity_id=entity_id,
                entity_name=entity_name,
                reminder_type=ReminderType.AUTO_DUE_DATE,
                offset_label=offset_label,
                title=ReminderService._offset_title(offset_label, entity_type, entity_name),
                message=ReminderService._offset_message(offset_label, entity_type, entity_name, due_date),
                remind_at=remind_at,
                link=link,
                status=ReminderStatus.PENDING,
            )
            db.add(reminder)
            created.append(reminder)

        db.commit()
        return created

    @staticmethod
    def remove_auto_reminders_for_entity(
        db: Session, entity_type: str, entity_id: UUID
    ) -> int:
        """Remove all auto due-date reminders when due date is cleared or entity is completed."""
        count = db.query(Reminder).filter(
            Reminder.entity_type == ReminderEntityType(entity_type),
            Reminder.entity_id == entity_id,
            Reminder.reminder_type == ReminderType.AUTO_DUE_DATE,
            Reminder.status == ReminderStatus.PENDING,
        ).update(
            {"status": ReminderStatus.DISMISSED, "dismissed_at": datetime.utcnow()},
            synchronize_session="fetch",
        )
        db.commit()
        return count

    # ─── Process Pending Reminders (called by background scheduler) ───

    @staticmethod
    def process_pending_reminders(db: Session) -> int:
        """
        Find all pending reminders whose remind_at has passed, send notifications,
        and mark them as sent. ALL state is in DB — restart-safe.
        """
        now = datetime.utcnow()
        pending = db.query(Reminder).filter(
            Reminder.status == ReminderStatus.PENDING,
            Reminder.remind_at <= now,
        ).all()

        sent_count = 0
        for reminder in pending:
            try:
                # Create in-app notification via existing notification service
                NotificationService.create_notification(
                    db=db,
                    user_id=reminder.user_id,
                    notification_type=NotificationType.GENERAL,
                    title=reminder.title,
                    message=reminder.message,
                    link=reminder.link,
                )

                # Mark as sent in DB — this is the guard against duplicates
                reminder.status = ReminderStatus.SENT
                reminder.sent_at = now
                reminder.updated_at = now
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to process reminder {reminder.id}: {e}")

        db.commit()
        logger.info(f"Processed {sent_count}/{len(pending)} pending reminders")
        return sent_count

    # ─── Snooze / Dismiss ───

    @staticmethod
    def snooze_reminder(
        db: Session, reminder_id: UUID, user_id: UUID, snooze_until: datetime
    ) -> Optional[Reminder]:
        """Snooze a reminder — sets new remind_at, resets to pending. All in DB."""
        reminder = db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        ).first()
        if not reminder:
            return None

        reminder.status = ReminderStatus.PENDING
        reminder.remind_at = snooze_until
        reminder.snoozed_until = snooze_until
        reminder.sent_at = None
        reminder.snooze_count += 1
        reminder.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(reminder)
        return reminder

    @staticmethod
    def dismiss_reminder(
        db: Session, reminder_id: UUID, user_id: UUID
    ) -> Optional[Reminder]:
        """Dismiss a reminder so it never fires again."""
        reminder = db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        ).first()
        if not reminder:
            return None

        reminder.status = ReminderStatus.DISMISSED
        reminder.dismissed_at = datetime.utcnow()
        reminder.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(reminder)
        return reminder

    # ─── Query ───

    @staticmethod
    def get_user_reminders(
        db: Session,
        user_id: UUID,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Reminder]:
        """Get reminders for a user, optionally filtered by status."""
        query = db.query(Reminder).filter(Reminder.user_id == user_id)
        if status_filter:
            query = query.filter(Reminder.status == ReminderStatus(status_filter))
        return query.order_by(Reminder.remind_at.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_reminder_by_id(
        db: Session, reminder_id: UUID, user_id: UUID
    ) -> Optional[Reminder]:
        return db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        ).first()

    @staticmethod
    def get_reminder_counts(db: Session, user_id: UUID) -> dict:
        """Get counts of pending and overdue reminders for a user."""
        now = datetime.utcnow()
        pending = db.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.status == ReminderStatus.PENDING,
        ).count()

        overdue = db.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.status == ReminderStatus.PENDING,
            Reminder.remind_at <= now,
        ).count()

        total = db.query(Reminder).filter(
            Reminder.user_id == user_id,
        ).count()

        return {"pending": pending, "overdue": overdue, "total": total}

    @staticmethod
    def update_reminder(
        db: Session,
        reminder_id: UUID,
        user_id: UUID,
        data: dict,
    ) -> Optional[Reminder]:
        """Update a manual reminder's title, message, or remind_at."""
        reminder = db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        ).first()
        if not reminder:
            return None

        for key in ("title", "message", "remind_at"):
            if key in data and data[key] is not None:
                setattr(reminder, key, data[key])
                # If remind_at changed and reminder was already sent, reset to pending
                if key == "remind_at" and reminder.status == ReminderStatus.SENT:
                    if data[key] > datetime.utcnow():
                        reminder.status = ReminderStatus.PENDING
                        reminder.sent_at = None

        reminder.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(reminder)
        return reminder

    @staticmethod
    def delete_reminder(
        db: Session, reminder_id: UUID, user_id: UUID
    ) -> bool:
        """Delete a reminder (hard delete)."""
        reminder = db.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        ).first()
        if not reminder:
            return False
        db.delete(reminder)
        db.commit()
        return True

    # ─── Helper: Generate title/message for auto-reminders ───

    @staticmethod
    def _offset_title(offset: ReminderOffset, entity_type: str, entity_name: str) -> str:
        labels = {
            ReminderOffset.THREE_DAYS_BEFORE: f"{entity_type.title()} due in 3 days",
            ReminderOffset.ONE_DAY_BEFORE: f"{entity_type.title()} due tomorrow",
            ReminderOffset.ON_DUE_DATE: f"{entity_type.title()} due today",
            ReminderOffset.ONE_DAY_OVERDUE: f"{entity_type.title()} is overdue",
        }
        return labels.get(offset, f"Reminder: {entity_name}")

    @staticmethod
    def _offset_message(
        offset: ReminderOffset,
        entity_type: str,
        entity_name: str,
        due_date: datetime,
    ) -> str:
        due_str = due_date.strftime("%b %d, %Y")
        messages = {
            ReminderOffset.THREE_DAYS_BEFORE: (
                f'"{entity_name}" is due on {due_str} — 3 days from now.'
            ),
            ReminderOffset.ONE_DAY_BEFORE: (
                f'"{entity_name}" is due tomorrow ({due_str}). Please review.'
            ),
            ReminderOffset.ON_DUE_DATE: (
                f'"{entity_name}" is due today ({due_str}). Take action now.'
            ),
            ReminderOffset.ONE_DAY_OVERDUE: (
                f'"{entity_name}" was due on {due_str} and is now overdue!'
            ),
        }
        return messages.get(offset, f'Reminder for "{entity_name}"')
