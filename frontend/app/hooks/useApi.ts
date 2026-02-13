/**
 * API Hooks for Data Fetching
 * Centralized hooks for fetching data from the backend API
 */

import { useState, useEffect } from 'react';
import { apiCall } from '../lib';

// Type definitions
interface AssignmentFilter {
  status?: string;
  client_id?: string;
  page?: number;
  limit?: number;
}

interface ProjectFilter {
  status?: string;
  owner_id?: string;
  page?: number;
  limit?: number;
}

export interface Assignment {
  id: string;
  name: string;
  status: string;
  priority: string;
  progress?: number;
  client_id?: string;
  due_date?: string;
}

export interface Project {
  id: string;
  name: string;
  status: string;
  task_count: number;
  completed_count: number;
  owner_id?: string;
  created_at?: string;
}

export interface KanbanBoardData {
  columns: Record<string, unknown>;
}

export interface CanvasData {
  nodes: Array<{
    id: string;
    position: { x: number; y: number };
    data: Record<string, unknown>;
    style?: Record<string, string>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
  }>;
}

export interface ApiResponse<T> {
  data: T;
  status: string;
}

// Response types
interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface TaskUpdatePayload {
  status: string;
  actual_hours?: number;
}

interface TaskMovePayload {
  status: string;
  position: number;
}

/**
 * Fetch assignments with optional filtering
 */
export function useAssignments(
  organizationId: string,
  filters?: AssignmentFilter
): UseApiResult<Assignment[]> {
  const [data, setData] = useState<Assignment[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams({
          organization_id: organizationId,
          page: filters?.page?.toString() || '1',
          limit: filters?.limit?.toString() || '20',
        });

        if (filters?.status) params.append('status', filters.status);
        if (filters?.client_id) params.append('client_id', filters.client_id);

        const result = await apiCall<ApiResponse<Assignment[]>>(`/api/v1/assignments?${params}`);
        setData(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [organizationId, filters]);

  return { data, loading, error };
}

/**
 * Fetch single assignment with full hierarchy
 */
export function useAssignmentDetail(
  assignmentId: string
): UseApiResult<Assignment> {
  const [data, setData] = useState<Assignment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await apiCall<ApiResponse<Assignment>>(`/api/v1/assignments/${assignmentId}`);
        setData(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [assignmentId]);

  return { data, loading, error };
}

/**
 * Fetch projects with optional filtering
 */
export function useProjects(
  organizationId: string,
  filters?: ProjectFilter
): UseApiResult<Project[]> {
  const [data, setData] = useState<Project[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams({
          organization_id: organizationId,
          page: filters?.page?.toString() || '1',
          limit: filters?.limit?.toString() || '20',
        });

        if (filters?.status) params.append('status', filters.status);
        if (filters?.owner_id) params.append('owner_id', filters.owner_id);

        const result = await apiCall<ApiResponse<Project[]>>(`/api/v1/projects?${params}`);
        setData(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [organizationId, filters]);

  return { data, loading, error };
}

/**
 * Fetch Kanban board for a project
 */
export function useKanbanBoard(projectId: string): UseApiResult<KanbanBoardData> {
  const [data, setData] = useState<KanbanBoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await apiCall<ApiResponse<KanbanBoardData>>(`/api/v1/projects/${projectId}/kanban`);
        setData(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [projectId]);

  return { data, loading, error };
}

/**
 * Fetch workflow canvas visualization
 */
export function useWorkflowCanvas(workflowId: string): UseApiResult<CanvasData> {
  const [data, setData] = useState<CanvasData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await apiCall<ApiResponse<CanvasData>>(`/api/v1/canvas/workflows/${workflowId}`);
        setData(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [workflowId]);

  return { data, loading, error };
}

/**
 * Fetch assignment canvas visualization
 */
export function useAssignmentCanvas(
  assignmentId: string
): UseApiResult<CanvasData> {
  const [data, setData] = useState<CanvasData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await apiCall<ApiResponse<CanvasData>>(`/api/v1/canvas/assignments/${assignmentId}`);
        setData(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [assignmentId]);

  return { data, loading, error };
}

/**
 * Update assignment status
 */
export async function updateAssignmentStatus(
  assignmentId: string,
  status: string
): Promise<ApiResponse<Assignment>> {
  return apiCall<ApiResponse<Assignment>>(`/api/v1/assignments/${assignmentId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

/**
 * Update task status
 */
export async function updateTaskStatus(
  assignmentId: string,
  taskId: string,
  status: string,
  hours?: number
): Promise<ApiResponse<unknown>> {
  const payload: TaskUpdatePayload = { status };
  if (hours !== undefined) {
    payload.actual_hours = hours;
  }

  return apiCall<ApiResponse<unknown>>(`/api/v1/assignments/${assignmentId}/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

/**
 * Move project task to different column
 */
export async function moveProjectTask(
  taskId: string,
  newStatus: string,
  position: number
): Promise<ApiResponse<unknown>> {
  const payload: TaskMovePayload = { status: newStatus, position };
  return apiCall<ApiResponse<unknown>>(`/api/v1/projects/tasks/${taskId}/move`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

/**
 * Create project task
 */
export async function createProjectTask(
  projectId: string,
  taskData: Record<string, string | number | boolean>
): Promise<ApiResponse<unknown>> {
  return apiCall<ApiResponse<unknown>>(`/api/v1/projects/${projectId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(taskData),
  });
}
