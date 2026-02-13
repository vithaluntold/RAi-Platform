// Workflow types
export interface Workflow {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  status: WorkflowStatus;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export enum WorkflowStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  ARCHIVED = "archived",
}
