/**
 * AssignmentDetail - Show assignment hierarchy (stages → steps → tasks)
 * Includes AI agent badges, run buttons, and execution history per task.
 */
'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { apiCall } from '../../lib';
import { API_ENDPOINTS } from '../../lib/api-config';

/* ─── Types ─────────────────────────────────────────────── */

interface AgentOnTask {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  status: string;
  is_required: boolean;
  order: number;
  last_run_at?: string;
}

interface AgentExecution {
  id: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  output_data?: Record<string, unknown>;
}

interface Task {
  id: string;
  name: string;
  status: string;
  assigned_to?: string;
  actual_hours?: number;
  agents?: AgentOnTask[];
}

interface Step {
  id: string;
  name: string;
  status: string;
  tasks: Task[];
}

interface Stage {
  id: string;
  name: string;
  status: string;
  steps: Step[];
}

interface AssignmentDetail {
  id: string;
  status: string;
  priority: string;
  client_id: string;
  client_name?: string;
  progress: number;
  due_date?: string;
  stages: Stage[];
}

/* ─── Agent helpers ─────────────────────────────────────── */

const AGENT_TYPE_COLORS: Record<string, string> = {
  document_intelligence: 'bg-purple-100 text-purple-700 border-purple-200',
  search: 'bg-cyan-100 text-cyan-700 border-cyan-200',
  extraction: 'bg-amber-100 text-amber-700 border-amber-200',
  validation: 'bg-teal-100 text-teal-700 border-teal-200',
  custom: 'bg-gray-100 text-gray-700 border-gray-200',
};

const AGENT_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  ready: 'bg-blue-100 text-blue-700',
  running: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  skipped: 'bg-gray-100 text-gray-400',
};

const agentTypeIcon = (type: string) => {
  switch (type) {
    case 'document_intelligence':
      return '📄';
    case 'search':
      return '🔍';
    case 'extraction':
      return '⛏️';
    case 'validation':
      return '✅';
    default:
      return '🤖';
  }
};

/* ─── Component ─────────────────────────────────────────── */

export default function AssignmentDetailPage() {
  const params = useParams();
  const assignmentId = params.id as string;
  const [assignment, setAssignment] = useState<AssignmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set());
  const [updatingTask, setUpdatingTask] = useState<string | null>(null);

  // Agent state
  const [runningAgent, setRunningAgent] = useState<string | null>(null);
  const [executionModal, setExecutionModal] = useState<{ agentName: string; ataId: string } | null>(null);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [loadingExecutions, setLoadingExecutions] = useState(false);

  const fetchAssignment = useCallback(async () => {
    try {
      const data = await apiCall<AssignmentDetail>(`/api/v1/assignments/${assignmentId}`);
      setAssignment(data);
      // Expand first stage by default on initial load
      if (data.stages?.length > 0) {
        setExpandedStages((prev) => prev.size === 0 ? new Set([data.stages[0].id]) : prev);
      }
    } catch (error) {
      console.error('Failed to fetch assignment:', error);
    } finally {
      setLoading(false);
    }
  }, [assignmentId]);

  useEffect(() => {
    fetchAssignment();
  }, [fetchAssignment]);

  /* ─── Task status toggle ────────────────────────────── */

  const toggleTaskStatus = async (taskId: string, currentStatus: string) => {
    setUpdatingTask(taskId);
    try {
      const newStatus = currentStatus === 'completed' || currentStatus === 'COMPLETED'
        ? 'not_started'
        : 'completed';
      await apiCall(`/api/v1/assignments/${assignmentId}/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      await fetchAssignment();
    } catch (error) {
      console.error('Failed to update task:', error);
    } finally {
      setUpdatingTask(null);
    }
  };

  const toggleStage = (stageId: string) => {
    const newExpanded = new Set(expandedStages);
    if (newExpanded.has(stageId)) {
      newExpanded.delete(stageId);
    } else {
      newExpanded.add(stageId);
    }
    setExpandedStages(newExpanded);
  };

  /* ─── Agent actions ─────────────────────────────────── */

  const runAgent = async (ataId: string) => {
    setRunningAgent(ataId);
    try {
      await apiCall(API_ENDPOINTS.AGENT_EXECUTE(ataId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      await fetchAssignment();
    } catch (error) {
      console.error('Failed to execute agent:', error);
    } finally {
      setRunningAgent(null);
    }
  };

  const openExecutionHistory = async (ataId: string, agentName: string) => {
    setExecutionModal({ ataId, agentName });
    setLoadingExecutions(true);
    try {
      const data = await apiCall<AgentExecution[]>(API_ENDPOINTS.AGENT_EXECUTIONS(ataId));
      setExecutions(data);
    } catch (error) {
      console.error('Failed to fetch executions:', error);
      setExecutions([]);
    } finally {
      setLoadingExecutions(false);
    }
  };

  /* ─── Status helper ─────────────────────────────────── */

  const statusColor = (status: string) => {
    switch (status) {
      case 'not_started':
        return 'bg-gray-100 text-gray-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'blocked':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  /* ─── Loading / Empty ───────────────────────────────── */

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Assignment not found</p>
      </div>
    );
  }

  /* ─── Render ────────────────────────────────────────── */

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">Assignment Details</h1>
          <div className="flex gap-2">
            <span className={`px-4 py-2 rounded-lg font-medium text-sm ${statusColor(assignment.status)}`}>
              {assignment.status}
            </span>
            <span className={`px-4 py-2 rounded-lg font-medium text-sm ${statusColor(assignment.priority)}`}>
              {assignment.priority}
            </span>
          </div>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase">Client</label>
            <p className="text-lg font-medium text-gray-900">{assignment.client_name || 'Unlinked'}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase">Progress</label>
            <div className="mt-2">
              <progress
                className="w-full h-2 accent-green-600"
                value={assignment.progress}
                max={100}
              />
              <p className="text-lg font-medium text-gray-900">{assignment.progress}%</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase">Due Date</label>
            <p className="text-lg font-medium text-gray-900">
              {assignment.due_date
                ? new Date(assignment.due_date).toLocaleDateString()
                : '-'}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase">Stages</label>
            <p className="text-lg font-medium text-gray-900">{assignment.stages.length}</p>
          </div>
        </div>
      </div>

      {/* Stages → Steps → Tasks Hierarchy */}
      <div className="space-y-4">
        {assignment.stages.map((stage) => (
          <div key={stage.id} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* Stage Header */}
            <button
              onClick={() => toggleStage(stage.id)}
              className="w-full px-6 py-4 bg-linear-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColor(stage.status)}`}>
                  {stage.status}
                </span>
                <h3 className="text-lg font-semibold text-gray-900">{stage.name}</h3>
              </div>
              <svg
                className={`w-5 h-5 text-gray-600 transform transition-transform ${
                  expandedStages.has(stage.id) ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </button>

            {/* Stage Content */}
            {expandedStages.has(stage.id) && (
              <div className="bg-white p-6 space-y-4">
                {stage.steps.map((step) => (
                  <div key={step.id} className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                    {/* Step */}
                    <div className="mb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor(step.status)}`}>
                            {step.status}
                          </span>
                          <h4 className="font-medium text-gray-900">{step.name}</h4>
                        </div>
                      </div>
                    </div>

                    {/* Tasks */}
                    {step.tasks && step.tasks.length > 0 && (
                      <div className="ml-4 space-y-2">
                        {step.tasks.map((task) => (
                          <div key={task.id} className="bg-white rounded border border-gray-200">
                            {/* Task row */}
                            <div className="flex items-center justify-between px-3 py-2">
                              <div className="flex items-center gap-3">
                                <input
                                  type="checkbox"
                                  checked={task.status === 'completed' || task.status === 'COMPLETED'}
                                  onChange={() => toggleTaskStatus(task.id, task.status)}
                                  disabled={updatingTask === task.id}
                                  title="Toggle task completion"
                                  className="w-4 h-4 text-blue-600 cursor-pointer disabled:cursor-wait"
                                />
                                <span className="text-sm text-gray-700">{task.name}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {task.actual_hours != null && task.actual_hours > 0 && (
                                  <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                                    {task.actual_hours}h
                                  </span>
                                )}
                                <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor(task.status)}`}>
                                  {task.status}
                                </span>
                              </div>
                            </div>

                            {/* Agent badges row */}
                            {task.agents && task.agents.length > 0 && (
                              <div className="px-3 pb-2 pt-0 border-t border-gray-100">
                                <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                                  <span className="text-xs text-gray-400 mr-1">Agents:</span>
                                  {task.agents.map((agent) => (
                                    <div key={agent.id} className="flex items-center gap-1">
                                      {/* Agent badge */}
                                      <button
                                        type="button"
                                        onClick={() => openExecutionHistory(agent.id, agent.agent_name)}
                                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border cursor-pointer hover:opacity-80 transition-opacity ${AGENT_TYPE_COLORS[agent.agent_type] || AGENT_TYPE_COLORS.custom}`}
                                        title={`${agent.agent_name} — ${agent.status} (click for history)`}
                                      >
                                        <span>{agentTypeIcon(agent.agent_type)}</span>
                                        <span>{agent.agent_name}</span>
                                        {agent.is_required && <span className="text-red-500">*</span>}
                                      </button>

                                      {/* Status pill */}
                                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${AGENT_STATUS_COLORS[agent.status] || AGENT_STATUS_COLORS.pending}`}>
                                        {agent.status}
                                      </span>

                                      {/* Run button */}
                                      <button
                                        type="button"
                                        onClick={() => runAgent(agent.id)}
                                        disabled={runningAgent === agent.id || agent.status === 'running'}
                                        className="p-0.5 rounded hover:bg-green-50 text-green-600 disabled:text-gray-300 disabled:cursor-wait"
                                        title={`Run ${agent.agent_name}`}
                                      >
                                        {runningAgent === agent.id ? (
                                          <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                          </svg>
                                        ) : (
                                          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M8 5v14l11-7z" />
                                          </svg>
                                        )}
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ─── Execution History Modal ─── */}
      {executionModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setExecutionModal(null)}>
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Execution History</h3>
                <p className="text-sm text-gray-500">{executionModal.agentName}</p>
              </div>
              <button onClick={() => setExecutionModal(null)} title="Close" className="text-gray-400 hover:text-gray-600 p-1">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4">
              {loadingExecutions ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : executions.length === 0 ? (
                <p className="text-center text-gray-400 py-8">No executions yet</p>
              ) : (
                <div className="space-y-3">
                  {executions.map((exec) => (
                    <div key={exec.id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          exec.status === 'completed' ? 'bg-green-100 text-green-700' :
                          exec.status === 'failed' ? 'bg-red-100 text-red-700' :
                          exec.status === 'running' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {exec.status}
                        </span>
                        {exec.duration_seconds != null && (
                          <span className="text-xs text-gray-500">{exec.duration_seconds.toFixed(1)}s</span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {exec.started_at && (
                          <span>Started: {new Date(exec.started_at).toLocaleString()}</span>
                        )}
                        {exec.completed_at && (
                          <span className="ml-3">Ended: {new Date(exec.completed_at).toLocaleString()}</span>
                        )}
                      </div>
                      {exec.error_message && (
                        <p className="text-xs text-red-600 mt-1 bg-red-50 p-2 rounded">{exec.error_message}</p>
                      )}
                      {exec.output_data && Object.keys(exec.output_data).length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs text-blue-600 cursor-pointer hover:underline">Output</summary>
                          <pre className="text-xs bg-gray-50 p-2 rounded mt-1 overflow-auto max-h-40">{JSON.stringify(exec.output_data, null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
