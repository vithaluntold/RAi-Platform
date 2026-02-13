// API configuration
export const API_BASE_URL = typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL : "http://localhost:8000";

export const API_ENDPOINTS = {
  // Auth
  LOGIN: "/api/v1/login/access-token",
  LOGOUT: "/api/v1/logout",
  REFRESH: "/api/v1/refresh",
  AD_LOGIN: "/api/v1/login/ad",
  AD_CALLBACK: "/api/v1/ad-callback",

  // Users
  USERS: "/api/v1/users",
  USER: (id: string) => `/api/v1/users/${id}`,

  // Documents
  DOCUMENTS: "/api/v1/documents",
  DOCUMENT: (id: string) => `/api/v1/documents/${id}`,

  // Workflows
  WORKFLOWS: "/api/v1/workflows",
  WORKFLOW: (id: string) => `/api/v1/workflows/${id}`,
  WORKFLOW_STAGES: (workflowId: string) => `/api/v1/workflows/${workflowId}/stages`,
  WORKFLOW_STAGE: (stageId: string) => `/api/v1/workflows/stages/${stageId}`,
  WORKFLOW_STAGE_STEPS: (stageId: string) => `/api/v1/workflows/stages/${stageId}/steps`,
  WORKFLOW_STEP: (stepId: string) => `/api/v1/workflows/steps/${stepId}`,
  WORKFLOW_STEP_TASKS: (stepId: string) => `/api/v1/workflows/steps/${stepId}/tasks`,
  WORKFLOW_TASK: (taskId: string) => `/api/v1/workflows/tasks/${taskId}`,
  WORKFLOW_STAGES_REORDER: (workflowId: string) => `/api/v1/workflows/${workflowId}/stages/reorder`,

  // Projects
  PROJECTS: "/api/v1/projects",
  PROJECT: (id: string) => `/api/v1/projects/${id}`,

  // Assignments
  ASSIGNMENTS: "/api/v1/assignments",
  ASSIGNMENT: (id: string) => `/api/v1/assignments/${id}`,

  // Clients
  CLIENTS: "/api/v1/clients",
  CLIENT: (id: string) => `/api/v1/clients/${id}`,
  CLIENT_CONTACTS: (id: string) => `/api/v1/clients/${id}/contacts`,

  // Contacts
  CONTACTS: "/api/v1/contacts",
  CONTACT: (id: string) => `/api/v1/contacts/${id}`,

  // Agents
  AGENTS: "/api/v1/agents",
  AGENT: (id: string) => `/api/v1/agents/${id}`,
  WORKFLOW_TASK_AGENTS: (taskId: string) => `/api/v1/agents/workflow-tasks/${taskId}/agents`,
  ASSIGNMENT_TASK_AGENTS: (taskId: string) => `/api/v1/agents/assignment-tasks/${taskId}/agents`,
  ASSIGNMENT_TASK_AGENT: (ataId: string) => `/api/v1/agents/assignment-task-agents/${ataId}`,
  AGENT_EXECUTE: (ataId: string) => `/api/v1/agents/assignment-task-agents/${ataId}/execute`,
  AGENT_EXECUTIONS: (ataId: string) => `/api/v1/agents/assignment-task-agents/${ataId}/executions`,

  // Dashboard
  DASHBOARD_ANALYTICS: "/api/v1/dashboard/analytics",

  // Notifications
  NOTIFICATIONS: "/api/v1/notifications",
  NOTIFICATIONS_COUNT: "/api/v1/notifications/count",
  NOTIFICATIONS_READ: "/api/v1/notifications/read",
  NOTIFICATIONS_READ_ALL: "/api/v1/notifications/read-all",
  NOTIFICATIONS_PREFERENCES: "/api/v1/notifications/preferences",
  NOTIFICATIONS_SETTINGS: "/api/v1/notifications/settings",
  NOTIFICATIONS_ADMIN_USER_PREFERENCES: "/api/v1/notifications/admin/user-preferences",

  // Reminders
  REMINDERS: "/api/v1/reminders",
  REMINDERS_COUNTS: "/api/v1/reminders/counts",
  REMINDER: (id: string) => `/api/v1/reminders/${id}`,
  REMINDER_SNOOZE: (id: string) => `/api/v1/reminders/${id}/snooze`,
  REMINDER_DISMISS: (id: string) => `/api/v1/reminders/${id}/dismiss`,
};

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER: "user",
};
