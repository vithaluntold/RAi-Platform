// Project types
export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export enum ProjectStatus {
  PLANNING = "planning",
  ACTIVE = "active",
  REVIEW = "review",
  COMPLETED = "completed",
  ARCHIVED = "archived",
}

export enum ProjectPriority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  URGENT = "urgent",
}
