import logging
from datetime import datetime
from uuid import UUID
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationType,
    NotificationSetting,
    UserNotificationPreference,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating in-app notifications and sending Outlook emails."""

    # ─── In-App Notifications ───

    @staticmethod
    def create_notification(
        db: Session,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        link: Optional[str] = None,
    ) -> Optional[Notification]:
        """Create an in-app notification if user preferences allow it."""
        pref = NotificationService._get_or_create_preference(db, user_id)
        if not pref.in_app_enabled:
            return None

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            link=link,
            is_read=False,
            email_sent=False,
        )
        db.add(notification)
        db.flush()
        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_unread_count(db: Session, user_id: UUID) -> int:
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()

    @staticmethod
    def mark_as_read(db: Session, notification_ids: list[UUID], user_id: UUID) -> int:
        count = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
        ).update({"is_read": True}, synchronize_session="fetch")
        db.commit()
        return count

    @staticmethod
    def mark_all_as_read(db: Session, user_id: UUID) -> int:
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True}, synchronize_session="fetch")
        db.commit()
        return count

    # ─── Email via Microsoft Graph API ───

    @staticmethod
    async def send_email_notification(
        db: Session,
        user_id: UUID,
        subject: str,
        body: str,
    ) -> bool:
        """Send email via Microsoft Graph API using admin-configured Outlook credentials."""
        pref = NotificationService._get_or_create_preference(db, user_id)
        if not pref.email_enabled:
            return False

        settings = db.query(NotificationSetting).first()
        if not settings or not settings.is_enabled:
            logger.info("Email notifications disabled or no settings configured")
            return False

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            return False

        try:
            access_token = await NotificationService._get_graph_access_token(
                settings.outlook_client_id,
                settings.outlook_client_secret,
                settings.outlook_tenant_id,
            )
            if not access_token:
                return False

            await NotificationService._send_via_graph(
                access_token=access_token,
                from_email=settings.outlook_email,
                to_email=user.email,
                subject=subject,
                body=body,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    @staticmethod
    async def _get_graph_access_token(
        client_id: str, client_secret: str, tenant_id: str
    ) -> Optional[str]:
        """Get OAuth2 access token from Microsoft identity platform."""
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                return response.json().get("access_token")
        except Exception as e:
            logger.error(f"Failed to get Graph API access token: {e}")
            return None

    @staticmethod
    async def _send_via_graph(
        access_token: str,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        """Send email using Microsoft Graph API sendMail endpoint."""
        url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body,
                },
                "toRecipients": [
                    {"emailAddress": {"address": to_email}}
                ],
            },
            "saveToSentItems": "true",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Email sent to {to_email} from {from_email}")

    # ─── Notification Triggers ───

    @staticmethod
    def notify_task_completed(
        db: Session,
        task_name: str,
        assignment_name: str,
        assigned_to: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
    ) -> None:
        """Trigger notification when a task is completed."""
        if not assigned_to:
            return
        link = f"/dashboard/assignments/{assignment_id}" if assignment_id else None
        notification = NotificationService.create_notification(
            db=db,
            user_id=assigned_to,
            notification_type=NotificationType.TASK_COMPLETED,
            title="Task Completed",
            message=f'Task "{task_name}" in assignment "{assignment_name}" has been completed.',
            link=link,
        )
        if notification:
            notification.email_sent = False
            db.flush()

    @staticmethod
    def notify_step_completed(
        db: Session,
        step_name: str,
        assignment_name: str,
        assigned_to: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
    ) -> None:
        """Trigger notification when a step is completed."""
        if not assigned_to:
            return
        link = f"/dashboard/assignments/{assignment_id}" if assignment_id else None
        NotificationService.create_notification(
            db=db,
            user_id=assigned_to,
            notification_type=NotificationType.STEP_COMPLETED,
            title="Step Completed",
            message=f'Step "{step_name}" in assignment "{assignment_name}" has been completed.',
            link=link,
        )

    @staticmethod
    def notify_stage_completed(
        db: Session,
        stage_name: str,
        assignment_name: str,
        assigned_to: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
    ) -> None:
        """Trigger notification when a stage is completed."""
        if not assigned_to:
            return
        link = f"/dashboard/assignments/{assignment_id}" if assignment_id else None
        NotificationService.create_notification(
            db=db,
            user_id=assigned_to,
            notification_type=NotificationType.STAGE_COMPLETED,
            title="Stage Completed",
            message=f'Stage "{stage_name}" in assignment "{assignment_name}" has been completed.',
            link=link,
        )

    @staticmethod
    def notify_assignment_completed(
        db: Session,
        assignment_name: str,
        assigned_to: Optional[UUID] = None,
        assignment_id: Optional[UUID] = None,
    ) -> None:
        """Trigger notification when an entire assignment is completed."""
        if not assigned_to:
            return
        link = f"/dashboard/assignments/{assignment_id}" if assignment_id else None
        NotificationService.create_notification(
            db=db,
            user_id=assigned_to,
            notification_type=NotificationType.ASSIGNMENT_COMPLETED,
            title="Assignment Completed",
            message=f'Assignment "{assignment_name}" has been fully completed.',
            link=link,
        )

    @staticmethod
    def notify_task_assigned(
        db: Session,
        task_name: str,
        assignment_name: str,
        assigned_to: UUID,
        assignment_id: Optional[UUID] = None,
    ) -> None:
        """Trigger notification when a task is assigned to a user."""
        link = f"/dashboard/assignments/{assignment_id}" if assignment_id else None
        NotificationService.create_notification(
            db=db,
            user_id=assigned_to,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="Task Assigned",
            message=f'You have been assigned task "{task_name}" in assignment "{assignment_name}".',
            link=link,
        )

    @staticmethod
    def notify_task_created(
        db: Session,
        task_name: str,
        workflow_name: str,
        created_by: UUID,
    ) -> None:
        """Trigger notification when a new task is created in a workflow."""
        NotificationService.create_notification(
            db=db,
            user_id=created_by,
            notification_type=NotificationType.TASK_CREATED,
            title="Task Created",
            message=f'Task "{task_name}" has been created in workflow "{workflow_name}".',
            link=None,
        )

    # ─── Notification Settings (Admin) ───

    @staticmethod
    def get_settings(db: Session) -> Optional[NotificationSetting]:
        return db.query(NotificationSetting).first()

    @staticmethod
    def upsert_settings(db: Session, data: dict) -> NotificationSetting:
        settings = db.query(NotificationSetting).first()
        if settings:
            for key, value in data.items():
                if value is not None:
                    setattr(settings, key, value)
            settings.updated_at = datetime.utcnow()
        else:
            settings = NotificationSetting(**data)
            db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    # ─── User Notification Preferences ───

    @staticmethod
    def _get_or_create_preference(
        db: Session, user_id: UUID
    ) -> UserNotificationPreference:
        pref = db.query(UserNotificationPreference).filter(
            UserNotificationPreference.user_id == user_id
        ).first()
        if not pref:
            pref = UserNotificationPreference(
                user_id=user_id,
                email_enabled=True,
                in_app_enabled=True,
            )
            db.add(pref)
            db.flush()
        return pref

    @staticmethod
    def get_user_preference(
        db: Session, user_id: UUID
    ) -> UserNotificationPreference:
        return NotificationService._get_or_create_preference(db, user_id)

    @staticmethod
    def update_user_preference(
        db: Session,
        user_id: UUID,
        data: dict,
        updated_by: Optional[UUID] = None,
    ) -> UserNotificationPreference:
        pref = NotificationService._get_or_create_preference(db, user_id)
        if "email_enabled" in data and data["email_enabled"] is not None:
            pref.email_enabled = data["email_enabled"]
        if "in_app_enabled" in data and data["in_app_enabled"] is not None:
            pref.in_app_enabled = data["in_app_enabled"]
        pref.updated_by = updated_by
        pref.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def get_all_user_preferences(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[dict]:
        """Get all users with their notification preferences (admin view)."""
        users = db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
        result = []
        for user in users:
            pref = NotificationService._get_or_create_preference(db, user.id)
            result.append({
                "user_id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "email_enabled": pref.email_enabled,
                "in_app_enabled": pref.in_app_enabled,
            })
        db.commit()
        return result

    # ─── Async email dispatch (called after commit) ───

    @staticmethod
    async def dispatch_pending_emails(db: Session) -> None:
        """Send emails for notifications that haven't been emailed yet."""
        pending = db.query(Notification).filter(
            Notification.email_sent == False,
            Notification.is_read == False,
        ).limit(50).all()

        for notification in pending:
            sent = await NotificationService.send_email_notification(
                db=db,
                user_id=notification.user_id,
                subject=notification.title,
                body=notification.message,
            )
            if sent:
                notification.email_sent = True
        db.commit()
