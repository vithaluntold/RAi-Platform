"""
Import all models for easy access - reorganized by domain
"""
from app.models.user import User
from app.models.workflow import (
    Workflow,
    WorkflowStatus,
    WorkflowStage,
    WorkflowStep,
    WorkflowTask,
)
from app.models.assignment import (
    WorkflowAssignment,
    AssignmentStatus,
    AssignmentPriority,
    AssignmentWorkflowStage,
    StageStatus,
    AssignmentWorkflowStep,
    AssignmentWorkflowTask,
    TaskStatus,
)
from app.models.project import (
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
from app.models.client import Client, ClientStatus
from app.models.contact import Contact, ContactStatus
from app.models.client_contact import ClientContact
from app.models.agent import (
    Agent,
    AgentType,
    AgentStatus,
    WorkflowTaskAgent,
    AssignmentTaskAgent,
    AgentAssignmentStatus,
    AgentExecution,
    ExecutionStatus,
)
from app.models.notification import (
    Notification,
    NotificationType,
    NotificationSetting,
    UserNotificationPreference,
)
from app.models.reminder import (
    Reminder,
    ReminderType,
    ReminderStatus,
    ReminderEntityType,
    ReminderOffset,
)
from app.models.document import Document, DocumentStatus, DocumentCategory
from app.models.compliance import (
    ComplianceSession,
    ComplianceSessionStatus,
    ComplianceFramework,
    ComplianceResult,
    ComplianceResultStatus,
    ComplianceDocument,
    DocumentExtractionStatus,
    AnalysisProgressStatus,
    ChatMessageRole,
    CachedAnalysisResult,
    AnalysisProgress,
    QuestionLearningData,
    ComplianceConversation,
    ComplianceMessage,
)
from app.models.automation import (
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

__all__ = [
    # User models
    "User",
    # Workflow template models
    "Workflow",
    "WorkflowStatus",
    "WorkflowStage",
    "WorkflowStep",
    "WorkflowTask",
    # Assignment models
    "WorkflowAssignment",
    "AssignmentStatus",
    "AssignmentPriority",
    "AssignmentWorkflowStage",
    "StageStatus",
    "AssignmentWorkflowStep",
    "AssignmentWorkflowTask",
    "TaskStatus",
    # Project models
    "Project",
    "ProjectStatus",
    "ProjectVisibility",
    "ProjectPriority",
    "ProjectTask",
    "ProjectTaskStatus",
    "ProjectTaskPriority",
    "ProjectCollaborator",
    "CollaboratorRole",
    # Client & Contact models
    "Client",
    "ClientStatus",
    "Contact",
    "ContactStatus",
    "ClientContact",
    # Agent models
    "Agent",
    "AgentType",
    "AgentStatus",
    "WorkflowTaskAgent",
    "AssignmentTaskAgent",
    "AgentAssignmentStatus",
    "AgentExecution",
    "ExecutionStatus",
    # Notification models
    "Notification",
    "NotificationType",
    "NotificationSetting",
    "UserNotificationPreference",
    # Reminder models
    "Reminder",
    "ReminderType",
    "ReminderStatus",
    "ReminderEntityType",
    "ReminderOffset",
    # Document models
    "Document",
    "DocumentStatus",
    "DocumentCategory",
    # Compliance models
    "ComplianceSession",
    "ComplianceSessionStatus",
    "ComplianceFramework",
    "ComplianceResult",
    "ComplianceResultStatus",
    "ComplianceDocument",
    "DocumentExtractionStatus",
    "AnalysisProgressStatus",
    "ChatMessageRole",
    "CachedAnalysisResult",
    "AnalysisProgress",
    "QuestionLearningData",
    "ComplianceConversation",
    "ComplianceMessage",
    # Automation models
    "WorkflowDependency",
    "AssignmentDependency",
    "DependencyType",
    "AutomationRule",
    "AutomationCondition",
    "AutomationAction",
    "AutomationExecutionLog",
    "TriggerEvent",
    "ActionType",
    "ConditionOperator",
    "AutomationRuleStatus",
    "WorkflowSOP",
    "RecurringSchedule",
    "RecurrenceFrequency",
    "ExecutionMode",
]
