/**
 * AssignmentList - Display assignments with filtering, progress tracking, and creation
 */
'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { apiCall } from '../lib';

interface Assignment {
  id: string;
  workflow_id: string;
  client_id: string;
  client_name?: string;
  status: string;
  priority: string;
  due_date?: string;
  progress?: number;
  created_at: string;
}

interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  pages: number;
}

interface WorkflowOption {
  id: string;
  name: string;
  status: string;
}

interface ClientOption {
  id: string;
  name: string;
  status: string;
}

const PRIORITY_OPTIONS = ['low', 'medium', 'high', 'urgent'];

export default function AssignmentList() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta>({
    total: 0,
    page: 1,
    limit: 20,
    pages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    page: 1,
  });

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [workflows, setWorkflows] = useState<WorkflowOption[]>([]);
  const [clients, setClients] = useState<ClientOption[]>([]);
  const [creating, setCreating] = useState(false);

  // Form fields
  const [formWorkflowId, setFormWorkflowId] = useState('');
  const [formClientId, setFormClientId] = useState('');
  const [formPriority, setFormPriority] = useState('medium');
  const [formDueDate, setFormDueDate] = useState('');
  const [formStartDate, setFormStartDate] = useState('');
  const [formNotes, setFormNotes] = useState('');

  const resetForm = () => {
    setFormWorkflowId('');
    setFormClientId('');
    setFormPriority('medium');
    setFormDueDate('');
    setFormStartDate('');
    setFormNotes('');
  };

  // Fetch assignments from API
  const fetchAssignments = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: filters.page.toString(),
        limit: '20',
      });

      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);

      const data = await apiCall<{ data: Assignment[]; pagination: PaginationMeta }>(`/api/v1/assignments?${params}`);

      setAssignments(data.data);
      setPagination(data.pagination);
    } catch (error) {
      console.error('Failed to fetch assignments:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchAssignments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.status, filters.priority, filters.page]);

  // Fetch workflows and clients when modal opens
  const openCreateModal = async () => {
    setShowCreateModal(true);
    resetForm();
    try {
      const [wfData, clData] = await Promise.all([
        apiCall<WorkflowOption[]>('/api/v1/workflows'),
        apiCall<{ data: ClientOption[] }>('/api/v1/clients'),
      ]);
      setWorkflows(wfData);
      setClients(clData.data || []);
    } catch (error) {
      console.error('Failed to load form options:', error);
    }
  };

  const handleCreate = async () => {
    if (!formWorkflowId || !formClientId) return;
    setCreating(true);
    try {
      const payload: Record<string, unknown> = {
        workflow_id: formWorkflowId,
        client_id: formClientId,
        priority: formPriority,
      };
      if (formDueDate) payload.due_date = new Date(formDueDate).toISOString();
      if (formStartDate) payload.start_date = new Date(formStartDate).toISOString();
      if (formNotes.trim()) payload.notes = formNotes.trim();

      await apiCall('/api/v1/assignments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      setShowCreateModal(false);
      resetForm();
      fetchAssignments();
    } catch (error) {
      console.error('Failed to create assignment:', error);
    } finally {
      setCreating(false);
    }
  };

  const priorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'text-rose-700 bg-rose-50 border-rose-200';
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'active':
        return 'bg-blue-100 text-blue-800';
      case 'in_progress':
        return 'bg-indigo-100 text-indigo-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'on_hold':
        return 'bg-amber-100 text-amber-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Assignments</h1>
          <p className="text-sm text-gray-500 mt-1">
            {pagination.total} assignment{pagination.total !== 1 ? 's' : ''} total
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Assignment
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          aria-label="Filter by status"
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="on_hold">On Hold</option>
          <option value="cancelled">Cancelled</option>
        </select>

        <select
          aria-label="Filter by priority"
          value={filters.priority}
          onChange={(e) => setFilters({ ...filters, priority: e.target.value, page: 1 })}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
      </div>

      {/* Assignments Table */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : assignments.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-xl border border-gray-200">
          <svg className="mx-auto mb-4 text-gray-400" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="12" y1="18" x2="12" y2="12" />
            <line x1="9" y1="15" x2="15" y2="15" />
          </svg>
          <p className="text-gray-500 mb-3">No assignments yet</p>
          <button
            onClick={openCreateModal}
            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
          >
            Create your first assignment
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto bg-white rounded-xl border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {assignments.map((assignment) => (
                <tr key={assignment.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColor(assignment.status)}`}>
                      {assignment.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                    {assignment.client_name || 'Unlinked'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${priorityColor(assignment.priority)}`}>
                      {assignment.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <progress
                        className={`w-24 h-2 rounded-full ${
                          (assignment.progress || 0) === 100
                            ? 'accent-green-500'
                            : (assignment.progress || 0) >= 50
                            ? 'accent-blue-500'
                            : 'accent-gray-400'
                        }`}
                        value={assignment.progress || 0}
                        max={100}
                      />
                      <span className="text-xs text-gray-600 font-medium">{assignment.progress || 0}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {assignment.due_date
                      ? new Date(assignment.due_date).toLocaleDateString()
                      : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm space-x-3">
                    <Link
                      href={`/assignments/${assignment.id}`}
                      className="text-blue-600 hover:text-blue-900 font-medium"
                    >
                      View
                    </Link>
                    <Link
                      href={`/canvas/assignments/${assignment.id}`}
                      className="text-indigo-600 hover:text-indigo-900 font-medium"
                    >
                      Canvas
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex justify-center gap-2">
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

      {/* Create Assignment Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">New Assignment</h2>
              <button onClick={() => setShowCreateModal(false)} title="Close" className="p-1 text-gray-400 hover:text-gray-600">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <div className="space-y-5">
              {/* Workflow Picker */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Workflow Template <span className="text-red-500">*</span>
                </label>
                {workflows.length === 0 ? (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                    No workflows available. Create a workflow template first.
                  </div>
                ) : (
                  <select
                    value={formWorkflowId}
                    onChange={(e) => setFormWorkflowId(e.target.value)}
                    title="Select workflow"
                    className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select a workflow...</option>
                    {workflows.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name} ({w.status})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Client Picker */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Client <span className="text-red-500">*</span>
                </label>
                {clients.length === 0 ? (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                    No clients available.{' '}
                    <Link href="/dashboard/clients" className="text-blue-600 hover:underline font-medium">
                      Add a client first
                    </Link>.
                  </div>
                ) : (
                  <select
                    value={formClientId}
                    onChange={(e) => setFormClientId(e.target.value)}
                    title="Select client"
                    className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select a client...</option>
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Priority</label>
                <div className="flex gap-2">
                  {PRIORITY_OPTIONS.map((p) => (
                    <button
                      key={p}
                      onClick={() => setFormPriority(p)}
                      className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold capitalize border transition-colors ${
                        formPriority === p
                          ? priorityColor(p) + ' ring-2 ring-offset-1 ring-blue-400'
                          : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Start Date</label>
                  <input
                    type="date"
                    title="Start Date"
                    placeholder="Select start date"
                    value={formStartDate}
                    onChange={(e) => setFormStartDate(e.target.value)}
                    className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Due Date</label>
                  <input
                    type="date"
                    title="Due Date"
                    placeholder="Select due date"
                    value={formDueDate}
                    onChange={(e) => setFormDueDate(e.target.value)}
                    className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Notes</label>
                <textarea
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  rows={3}
                  placeholder="Optional notes about this assignment"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
              <button
                onClick={() => { setShowCreateModal(false); resetForm(); }}
                className="h-10 px-5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!formWorkflowId || !formClientId || creating}
                className="h-10 px-6 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? 'Creating...' : 'Create Assignment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
