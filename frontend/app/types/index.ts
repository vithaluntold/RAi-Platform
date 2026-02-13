// Types module - centralized TypeScript interfaces

// User-related types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'guest';
  created_at: string;
}

// Assignment types
export interface Assignment {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'completed';
  priority: 'high' | 'medium' | 'low';
  progress: number;
  client_id: string;
  due_date: string;
}

// Project types
export interface Project {
  id: string;
  name: string;
  status: 'planning' | 'in-progress' | 'completed';
  task_count: number;
  completed_count: number;
  owner_id: string;
  created_at: string;
}

// Pagination types
export interface PaginationMeta {
  page: number;
  pages: number;
  limit: number;
  total: number;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  status: string;
  pagination?: PaginationMeta;
}

// Canvas types
export interface CanvasNode {
  id: string;
  position: { x: number; y: number };
  data: {
    label: string;
    type: string;
    progress?: number;
    taskCount?: number;
  };
  style?: {
    backgroundColor?: string;
    borderColor?: string;
  };
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
}

export interface CanvasData {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
}
