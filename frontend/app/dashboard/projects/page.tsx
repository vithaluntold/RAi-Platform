/**
 * ProjectList - Browse and manage projects
 */
'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { apiCall } from '../../lib';

interface Project {
  id: string;
  name: string;
  description?: string;
  status: string;
  owner_id: string;
  task_count: number;
  completed_count: number;
  in_progress_count: number;
  due_date?: string;
  created_at: string;
}

interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta>({
    total: 0,
    page: 1,
    limit: 20,
    pages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    page: 1,
  });

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: filters.page.toString(),
        limit: '20',
      });

      if (filters.status) params.append('status', filters.status);

      const data = await apiCall<{ data: Project[]; pagination: PaginationMeta }>(`/api/v1/projects?${params}`);

      setProjects(data.data);
      setPagination(data.pagination);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const statusColor = (status: string) => {
    switch (status) {
      case 'planning':
        return 'bg-gray-100 text-gray-800';
      case 'active':
        return 'bg-blue-100 text-blue-800';
      case 'review':
        return 'bg-purple-100 text-purple-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'archived':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressAccent = (completed: number, total: number) => {
    if (total === 0) return 'accent-gray-400';
    const percent = (completed / total) * 100;
    if (percent === 100) return 'accent-green-600';
    if (percent >= 75) return 'accent-blue-600';
    if (percent >= 50) return 'accent-yellow-500';
    return 'accent-orange-500';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <Link
            href="/projects/new"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            + New Project
          </Link>
        </div>

        {/* Filters */}
        <select
          aria-label="Filter by project status"
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Statuses</option>
          <option value="planning">Planning</option>
          <option value="active">Active</option>
          <option value="review">Review</option>
          <option value="completed">Completed</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No projects found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div
              key={project.id}
              className="bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-shadow overflow-hidden"
            >
              {/* Card Header */}
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-bold text-gray-900">{project.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColor(project.status)}`}>
                    {project.status}
                  </span>
                </div>
                {project.description && (
                  <p className="text-sm text-gray-600 line-clamp-2">{project.description}</p>
                )}
              </div>

              {/* Card Body */}
              <div className="p-6 space-y-4">
                {/* Task Progress */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-600 uppercase">Tasks</span>
                    <span className="text-sm font-medium text-gray-900">
                      {project.completed_count}/{project.task_count}
                    </span>
                  </div>
                  <progress
                    className={`w-full h-2 ${getProgressAccent(project.completed_count, project.task_count)}`}
                    value={project.task_count > 0 ? (project.completed_count / project.task_count) * 100 : 0}
                    max={100}
                  />
                </div>

                {/* Status Breakdown */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-blue-50 p-3 rounded">
                    <p className="text-xs text-gray-600">In Progress</p>
                    <p className="text-lg font-bold text-blue-600">{project.in_progress_count}</p>
                  </div>
                  <div className="bg-green-50 p-3 rounded">
                    <p className="text-xs text-gray-600">Completed</p>
                    <p className="text-lg font-bold text-green-600">{project.completed_count}</p>
                  </div>
                </div>

                {/* Due Date */}
                {project.due_date && (
                  <p className="text-xs text-gray-600">
                    Due: {new Date(project.due_date).toLocaleDateString()}
                  </p>
                )}
              </div>

              {/* Card Footer */}
              <div className="p-6 bg-gray-50 flex gap-2">
                <Link
                  href={`/dashboard/projects/${project.id}`}
                  className="flex-1 text-center px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                >
                  Kanban
                </Link>
                <Link
                  href={`/canvas/workflows/${project.id}`}
                  className="flex-1 text-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-100"
                >
                  Canvas
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-8 flex justify-center gap-2">
          <button
            onClick={() => setFilters({ ...filters, page: Math.max(1, filters.page - 1) })}
            disabled={filters.page === 1}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            Page {pagination.page} of {pagination.pages}
          </span>
          <button
            onClick={() => setFilters({ ...filters, page: Math.min(pagination.pages, filters.page + 1) })}
            disabled={filters.page === pagination.pages}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
