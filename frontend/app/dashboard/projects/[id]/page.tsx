/**
 * KanbanBoard - Project management with drag-drop task columns
 */
'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiCall } from '../../../lib';

interface ProjectTask {
  id: string;
  title: string;
  description?: string;
  priority: string;
  status: string;
  assignee_id?: string;
  due_date?: string;
  estimated_hours?: number;
}



interface ProjectStats {
  total: number;
  completed: number;
  in_progress: number;
}

export default function KanbanBoardPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [columns, setColumns] = useState<Record<string, ProjectTask[]>>({});
  const [stats, setStats] = useState<ProjectStats>({ total: 0, completed: 0, in_progress: 0 });
  const [loading, setLoading] = useState(true);
  const [draggedTask, setDraggedTask] = useState<string | null>(null);
  const [newTaskColumn, setNewTaskColumn] = useState<string>('');
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);

  const columnOrder = ['todo', 'in_progress', 'review', 'completed'];
  const columnLabels: Record<string, string> = {
    todo: 'To Do',
    in_progress: 'In Progress',
    review: 'Review',
    completed: 'Completed',
  };

  // Fetch Kanban board
  useEffect(() => {
    const fetchBoard = async () => {
      try {
        const data = await apiCall<{ columns: Record<string, ProjectTask[]>; stats: ProjectStats }>(`/api/v1/projects/${projectId}/kanban`);
        setColumns(data.columns);
        setStats(data.stats);
      } catch (error) {
        console.error('Failed to fetch Kanban board:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBoard();
  }, [projectId]);

  const handleDragStart = (taskId: string) => {
    setDraggedTask(taskId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (newStatus: string) => {
    if (!draggedTask) return;

    try {
      // Find the task to get its position
      let fromStatus = '';
      let taskIndex = 0;

      for (const status of columnOrder) {
        const index = (columns[status] || []).findIndex((t) => t.id === draggedTask);
        if (index !== -1) {
          fromStatus = status;
          taskIndex = index;
          break;
        }
      }

      // Call API to move task
      const moveResponse = await apiCall<{ success: boolean }>(`/api/v1/projects/tasks/${draggedTask}/move`, {
        method: 'PATCH',
        body: JSON.stringify({
          status: newStatus,
          position: (columns[newStatus] || []).length,
        }),
      });

      if (moveResponse.success) {
        // Update local state
        const updatedColumns = { ...columns };
        const task = updatedColumns[fromStatus][taskIndex];
        
        updatedColumns[fromStatus] = updatedColumns[fromStatus].filter((_, i) => i !== taskIndex);
        updatedColumns[newStatus] = [...(updatedColumns[newStatus] || []), task];
        
        setColumns(updatedColumns);
      }
    } catch (error) {
      console.error('Failed to move task:', error);
    } finally {
      setDraggedTask(null);
    }
  };

  const priorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'border-l-4 border-red-500 bg-red-50';
      case 'medium':
        return 'border-l-4 border-yellow-500 bg-yellow-50';
      case 'low':
        return 'border-l-4 border-green-500 bg-green-50';
      default:
        return 'border-l-4 border-gray-500 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Project Kanban Board</h1>
          
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <label className="text-xs font-semibold text-gray-600 uppercase">Total Tasks</label>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <label className="text-xs font-semibold text-gray-600 uppercase">In Progress</label>
              <p className="text-2xl font-bold text-blue-600">{stats.in_progress}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <label className="text-xs font-semibold text-gray-600 uppercase">Completed</label>
              <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
            </div>
          </div>
        </div>

        {/* Kanban Columns */}
        <div className="grid grid-cols-4 gap-6">
          {columnOrder.map((status) => (
            <div
              key={status}
              className="bg-white rounded-lg shadow-sm min-h-96 flex flex-col"
            >
              {/* Column Header */}
              <div className="p-4 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900 mb-1">
                  {columnLabels[status]}
                </h2>
                <p className="text-sm text-gray-600">
                  {(columns[status] || []).length} tasks
                </p>
              </div>

              {/* Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDrop={() => handleDrop(status)}
                className="flex-1 p-4 space-y-3"
              >
                {(columns[status] || []).map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={() => handleDragStart(task.id)}
                    className={`p-3 rounded-lg cursor-move hover:shadow-md transition-shadow ${priorityColor(task.priority)}`}
                  >
                    <h3 className="font-medium text-gray-900 text-sm mb-2">
                      {task.title}
                    </h3>
                    {task.description && (
                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                        {task.description}
                      </p>
                    )}
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">
                        {task.priority.charAt(0).toUpperCase()}
                      </span>
                      {task.estimated_hours && (
                        <span className="text-gray-600">
                          {task.estimated_hours}h
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Add Task Button */}
              <div className="p-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setNewTaskColumn(status);
                    setShowNewTaskForm(true);
                  }}
                  className="w-full py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg font-medium"
                >
                  + Add Task
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* New Task Modal */}
      {showNewTaskForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              Create New Task in {columnLabels[newTaskColumn]}
            </h3>
            
            <form onSubmit={(e) => {
              e.preventDefault();
              // TODO: Implement create task API call with form data
              setShowNewTaskForm(false);
            }}>
              <input
                type="text"
                name="title"
                placeholder="Task title"
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
              />
              
              <textarea
                name="description"
                placeholder="Task description (optional)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
                rows={3}
              />

              <select
                aria-label="Task priority"
                name="priority"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
              </select>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => setShowNewTaskForm(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
