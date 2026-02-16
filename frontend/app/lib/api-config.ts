// API configuration — resolved at RUNTIME to avoid stale cached URLs
function resolveApiBaseUrl(): string {
  // Client-side: detect environment from hostname at runtime
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // Railway production — proxy through same origin (Next.js rewrites)
    if (hostname === 'rai-platform-prod.up.railway.app') {
      return '';
    }
    // Any other non-localhost domain — use same-origin proxy
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return '';
    }
  }
  // Local development or server-side rendering
  if (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  return 'http://localhost:8000';
}

export const API_BASE_URL = resolveApiBaseUrl();

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
  USER_ONBOARD: "/api/v1/users/onboard",
  USER_ONBOARD_BULK: "/api/v1/users/onboard/bulk",

  // Documents
  DOCUMENTS: "/api/v1/documents",
  DOCUMENT: (id: string) => `/api/v1/documents/${id}`,
  DOCUMENT_UPLOAD: "/api/v1/documents/upload",
  DOCUMENT_STATS: "/api/v1/documents/stats",
  DOCUMENT_DOWNLOAD: (id: string) => `/api/v1/documents/${id}/download`,

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

  // Compliance
  COMPLIANCE_SESSIONS: "/api/v1/compliance/sessions",
  COMPLIANCE_SESSION: (id: string) => `/api/v1/compliance/sessions/${id}`,
  COMPLIANCE_SESSION_UPLOAD: (id: string) => `/api/v1/compliance/sessions/${id}/upload`,
  COMPLIANCE_SESSION_MESSAGES: (id: string) => `/api/v1/compliance/sessions/${id}/messages`,
  COMPLIANCE_SESSION_EXTRACT_METADATA: (id: string) => `/api/v1/compliance/sessions/${id}/extract-metadata`,
  COMPLIANCE_SESSION_SUGGEST_STANDARDS: (id: string) => `/api/v1/compliance/sessions/${id}/suggest-standards`,
  COMPLIANCE_SESSION_ANALYZE: (id: string) => `/api/v1/compliance/sessions/${id}/analyze`,
  COMPLIANCE_SESSION_ANALYZE_STREAM: (id: string) => `/api/v1/compliance/sessions/${id}/analyze-stream`,
  COMPLIANCE_SESSION_RESULTS: (id: string) => `/api/v1/compliance/sessions/${id}/results`,
  COMPLIANCE_SESSION_REANALYZE: (id: string) => `/api/v1/compliance/sessions/${id}/re-analyze`,
  COMPLIANCE_SESSION_OVERRIDE: (id: string) => `/api/v1/compliance/sessions/${id}/override`,
  COMPLIANCE_SESSION_CHUNKS: (id: string) => `/api/v1/compliance/sessions/${id}/chunks`,
  COMPLIANCE_SESSION_CHUNKS_REVALIDATE: (id: string) => `/api/v1/compliance/sessions/${id}/chunks/revalidate`,
  COMPLIANCE_SESSION_VALIDATE_FINANCIALS: (id: string) => `/api/v1/compliance/sessions/${id}/validate-financials`,
  COMPLIANCE_SESSION_FILTER_QUESTIONS: (id: string) => `/api/v1/compliance/sessions/${id}/filter-questions`,
  COMPLIANCE_SESSION_CONVERSATIONS: (id: string) => `/api/v1/compliance/sessions/${id}/conversations`,
  COMPLIANCE_SESSION_CONVERSATION_MESSAGES: (id: string, convId: string) => `/api/v1/compliance/sessions/${id}/conversations/${convId}/messages`,
  COMPLIANCE_SESSION_CONVERSATION_SEND: (id: string, convId: string) => `/api/v1/compliance/sessions/${id}/conversations/${convId}/send`,
  COMPLIANCE_SESSION_SAVED_RESULTS: (id: string) => `/api/v1/compliance/sessions/${id}/saved-results`,
  COMPLIANCE_SESSION_SAVE_RESULTS: (id: string) => `/api/v1/compliance/sessions/${id}/save-results`,
  COMPLIANCE_SESSION_JOB_STATUS: (id: string) => `/api/v1/compliance/sessions/${id}/job-status`,
  COMPLIANCE_STANDARDS: "/api/v1/compliance/standards",
  COMPLIANCE_STANDARD: (key: string) => `/api/v1/compliance/standards/${key}`,
  COMPLIANCE_STANDARDS_SEARCH: "/api/v1/compliance/standards-search",
  COMPLIANCE_STANDARDS_RELOAD: "/api/v1/compliance/standards/reload",
  COMPLIANCE_HEALTH: "/api/v1/compliance/health",

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
