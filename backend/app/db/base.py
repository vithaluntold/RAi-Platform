# Import the Base and all models here for Alembic/Database discovery
from app.db.session import Base  # noqa
from app.models.user import User  # noqa
from app.models.workflow import (  # noqa
    Workflow,
    WorkflowStatus,
    WorkflowStage,
    WorkflowStep,
    WorkflowTask,
)
from app.models.assignment import (  # noqa
    WorkflowAssignment,
    AssignmentStatus,
    AssignmentPriority,
    AssignmentWorkflowStage,
    StageStatus,
    AssignmentWorkflowStep,
    AssignmentWorkflowTask,
    TaskStatus,
)
from app.models.project import (  # noqa
    Project,
    ProjectStatus,
    ProjectVisibility,
    ProjectPriority,
    ProjectTask,
    ProjectTaskStatus,
    ProjectTaskPriority,
    ProjectCollaborator,
    CollaboratorRole,
)
from app.models.client import Client, ClientStatus  # noqa
from app.models.contact import Contact, ContactStatus  # noqa
from app.models.client_contact import ClientContact  # noqa
from app.models.agent import (  # noqa
    Agent,
    AgentType,
    AgentStatus,
    WorkflowTaskAgent,
    AssignmentTaskAgent,
    AgentAssignmentStatus,
    AgentExecution,
    ExecutionStatus,
)
from app.models.notification import (  # noqa
    Notification,
    NotificationType,
    NotificationSetting,
    UserNotificationPreference,
)
from app.models.reminder import (  # noqa
    Reminder,
    ReminderType,
    ReminderStatus,
    ReminderEntityType,
    ReminderOffset,
)
from app.models.document import Document, DocumentStatus, DocumentCategory  # noqa
from app.models.automation import (  # noqa
    WorkflowDependency,
    AssignmentDependency,
    DependencyType,
    AutomationRule,
    AutomationCondition,
    AutomationAction,
    AutomationExecutionLog,
    TriggerEvent,
    ActionType,
    ConditionOperator,
    AutomationRuleStatus,
    WorkflowSOP,
    RecurringSchedule,
    RecurrenceFrequency,
    ExecutionMode,
)