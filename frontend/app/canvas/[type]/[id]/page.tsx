/**
 * WorkflowCanvas - Canvas mode visualization for workflows and assignments
 * 
 * Features (per PROJECT_ARCHITECTURE.md):
 * - SVG-based rendering for performance
 * - Zoom/pan controls (mouse wheel, drag)
 * - Node selection and inspection
 * - Status overlays (for assignments)
 * - Interactive status updates from canvas (assignment mode)
 * - Hierarchical node display (stages → steps → tasks)
 */
'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiCall } from '../../../lib';

// ─── Types ───────────────────────────────────────────────

interface TaskAgent {
  id: string;
  agent_name: string;
  agent_type: string;
  status: string;
}

interface TaskNode {
  id: string;
  name: string;
  status: string;
  assigned_to?: string;
  order: number;
  agents?: TaskAgent[];
}

interface StepNode {
  id: string;
  name: string;
  status: string;
  tasks: TaskNode[];
  order: number;
}

interface CanvasNode {
  id: string;
  type: 'stage' | 'step';
  data: {
    label: string;
    description?: string;
    status?: string;
    progress?: string;
    taskCount?: number;
    completedCount?: number;
    stepCount?: number;
    steps?: StepNode[];
    assignedTo?: string;
  };
  position: { x: number; y: number };
  style?: {
    backgroundColor?: string;
    borderColor?: string;
    borderWidth?: number;
  };
}

interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  animated?: boolean;
}

interface CanvasData {
  workflow?: { id: string; name: string; description?: string; status?: string };
  assignment?: { id: string; status: string; priority: string; progress: number; due_date?: string };
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  entityMap?: Record<string, { type: string; dbId: string }>;
  viewport: { x: number; y: number; zoom: number };
}

// ─── Status Helpers ──────────────────────────────────────

const AGENT_TYPE_DOT_COLORS: Record<string, string> = {
  document_intelligence: '#7c3aed',
  search: '#0891b2',
  extraction: '#d97706',
  validation: '#0d9488',
  custom: '#6b7280',
};

const AGENT_TYPE_DOT_CLASSES: Record<string, string> = {
  document_intelligence: 'bg-violet-600',
  search: 'bg-cyan-600',
  extraction: 'bg-amber-600',
  validation: 'bg-teal-600',
  custom: 'bg-gray-500',
};

const AGENT_STATUS_DOT_COLORS: Record<string, string> = {
  completed: '#10b981',
  running: '#f59e0b',
  failed: '#ef4444',
  pending: '#9ca3af',
  ready: '#3b82f6',
  skipped: '#d1d5db',
};

const AGENT_STATUS_CLASSES: Record<string, string> = {
  completed: 'bg-emerald-500 text-white',
  running: 'bg-amber-500 text-white',
  failed: 'bg-red-500 text-white',
  pending: 'bg-gray-400 text-white',
  ready: 'bg-blue-500 text-white',
  skipped: 'bg-gray-300 text-white',
};

const STATUS_CLASSES: Record<string, { badge: string; btnActive: string; btnInactive: string }> = {
  not_started: {
    badge: 'bg-gray-100 text-gray-700 border border-gray-300',
    btnActive: 'bg-gray-400 text-white border border-gray-300',
    btnInactive: 'bg-gray-100 text-gray-700 border border-gray-300',
  },
  NOT_STARTED: {
    badge: 'bg-gray-100 text-gray-700 border border-gray-300',
    btnActive: 'bg-gray-400 text-white border border-gray-300',
    btnInactive: 'bg-gray-100 text-gray-700 border border-gray-300',
  },
  in_progress: {
    badge: 'bg-amber-50 text-amber-800 border border-amber-400',
    btnActive: 'bg-amber-500 text-white border border-amber-400',
    btnInactive: 'bg-amber-50 text-amber-800 border border-amber-400',
  },
  IN_PROGRESS: {
    badge: 'bg-amber-50 text-amber-800 border border-amber-400',
    btnActive: 'bg-amber-500 text-white border border-amber-400',
    btnInactive: 'bg-amber-50 text-amber-800 border border-amber-400',
  },
  completed: {
    badge: 'bg-emerald-100 text-emerald-800 border border-emerald-500',
    btnActive: 'bg-emerald-500 text-white border border-emerald-500',
    btnInactive: 'bg-emerald-100 text-emerald-800 border border-emerald-500',
  },
  COMPLETED: {
    badge: 'bg-emerald-100 text-emerald-800 border border-emerald-500',
    btnActive: 'bg-emerald-500 text-white border border-emerald-500',
    btnInactive: 'bg-emerald-100 text-emerald-800 border border-emerald-500',
  },
  blocked: {
    badge: 'bg-red-100 text-red-800 border border-red-400',
    btnActive: 'bg-red-500 text-white border border-red-400',
    btnInactive: 'bg-red-100 text-red-800 border border-red-400',
  },
  BLOCKED: {
    badge: 'bg-red-100 text-red-800 border border-red-400',
    btnActive: 'bg-red-500 text-white border border-red-400',
    btnInactive: 'bg-red-100 text-red-800 border border-red-400',
  },
};

const getStatusClasses = (status?: string) =>
  STATUS_CLASSES[status || 'not_started'] || STATUS_CLASSES.not_started;

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  not_started: { bg: '#f3f4f6', border: '#d1d5db', text: '#374151', dot: '#9ca3af' },
  NOT_STARTED: { bg: '#f3f4f6', border: '#d1d5db', text: '#374151', dot: '#9ca3af' },
  in_progress: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', dot: '#f59e0b' },
  IN_PROGRESS: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', dot: '#f59e0b' },
  completed: { bg: '#d1fae5', border: '#10b981', text: '#065f46', dot: '#10b981' },
  COMPLETED: { bg: '#d1fae5', border: '#10b981', text: '#065f46', dot: '#10b981' },
  blocked: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', dot: '#ef4444' },
  BLOCKED: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', dot: '#ef4444' },
};

const getStatusStyle = (status?: string) =>
  STATUS_COLORS[status || 'not_started'] || STATUS_COLORS.not_started;

const STATUS_OPTIONS = ['not_started', 'in_progress', 'completed', 'blocked'];

// ─── Component ───────────────────────────────────────────

export default function WorkflowCanvasPage() {
  const params = useParams();
  const router = useRouter();
  const isAssignment = params.type === 'assignments';
  const resourceId = params.id as string;
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [canvas, setCanvas] = useState<CanvasData | null>(null);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 50, y: 50 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [updatingNode, setUpdatingNode] = useState<string | null>(null);

  // ─── Fetch Canvas Data ─────────────────────────────────

  const fetchCanvas = useCallback(async () => {
    try {
      const endpoint = isAssignment
        ? `/api/v1/canvas/assignments/${resourceId}`
        : `/api/v1/canvas/workflows/${resourceId}`;
      const data = await apiCall<CanvasData>(endpoint);
      setCanvas(data);
    } catch (error) {
      console.error('Failed to fetch canvas:', error);
    } finally {
      setLoading(false);
    }
  }, [resourceId, isAssignment]);

  useEffect(() => {
    fetchCanvas();
  }, [fetchCanvas]);

  // ─── Pan & Zoom Handlers ──────────────────────────────

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const tag = (e.target as Element).tagName;
    if (e.button === 0 && (tag === 'svg' || tag === 'rect' && (e.target as Element).classList.contains('canvas-bg'))) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  }, [pan]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) {
      setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
    }
  }, [isPanning, panStart]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prev) => Math.max(0.3, Math.min(3, prev * delta)));
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('wheel', handleWheel, { passive: false });
      return () => container.removeEventListener('wheel', handleWheel);
    }
  }, [handleWheel]);

  const handleZoom = (direction: 'in' | 'out') => {
    setZoom((prev) => {
      const newZoom = direction === 'in' ? prev * 1.2 : prev / 1.2;
      return Math.max(0.3, Math.min(3, newZoom));
    });
  };

  const fitToScreen = () => {
    setZoom(1);
    setPan({ x: 50, y: 50 });
  };

  // ─── Node Interactions ─────────────────────────────────

  const toggleExpand = (nodeId: string) => {
    const next = new Set(expandedNodes);
    if (next.has(nodeId)) {
      next.delete(nodeId);
    } else {
      next.add(nodeId);
    }
    setExpandedNodes(next);
  };

  const handleNodeClick = (nodeId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedNode(selectedNode === nodeId ? null : nodeId);
  };

  // ─── Canvas Status Update (Assignment Mode) ───────────

  const updateNodeStatus = async (nodeType: string, nodeId: string, newStatus: string) => {
    if (!isAssignment) return;
    setUpdatingNode(nodeId);
    try {
      await apiCall(`/api/v1/canvas/assignments/${resourceId}/nodes`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_type: nodeType,
          node_id: nodeId,
          status: newStatus,
        }),
      });
      await fetchCanvas();
    } catch (error) {
      console.error('Failed to update node status:', error);
    } finally {
      setUpdatingNode(null);
    }
  };

  // ─── Render Helpers ────────────────────────────────────

  const NODE_W = 220;
  const NODE_H = 80;
  const STEP_H = 50;
  const TASK_H = 32;

  const getStageHeight = (node: CanvasNode): number => {
    if (!expandedNodes.has(node.id)) return NODE_H;
    const steps = node.data.steps || [];
    let h = NODE_H + 10;
    for (const step of steps) {
      h += STEP_H + 6;
      if (expandedNodes.has(step.id)) {
        h += step.tasks.length * (TASK_H + 4) + 4;
      }
    }
    return h + 10;
  };

  // ─── Determine entity type for selected node ──────────

  const getSelectedNodeType = (): string | undefined => {
    if (!selectedNode || !canvas) return undefined;
    const entityEntry = canvas.entityMap?.[selectedNode];
    if (entityEntry) return entityEntry.type;
    const node = canvas.nodes.find((n) => n.id === selectedNode);
    return node?.type;
  };

  // ─── Render ────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading canvas...</p>
        </div>
      </div>
    );
  }

  if (!canvas) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
        <p className="text-gray-500 text-lg mb-4">Canvas not found</p>
        <button onClick={() => router.back()} className="text-blue-600 hover:underline">Go back</button>
      </div>
    );
  }

  const title = canvas.workflow?.name || canvas.assignment?.id || 'Canvas';
  const subtitle = isAssignment
    ? `Assignment  |  ${canvas.assignment?.status || ''}  |  ${canvas.assignment?.progress ?? 0}% complete`
    : `Workflow Template  |  ${canvas.workflow?.status || ''}`;

  const selectedNodeData = canvas.nodes.find((n) => n.id === selectedNode);
  const entityType = getSelectedNodeType();

  // Find task-level agent info when a task node is selected
  const getSelectedTask = (): TaskNode | undefined => {
    if (!selectedNode || !canvas) return undefined;
    for (const node of canvas.nodes) {
      for (const step of node.data.steps || []) {
        const task = step.tasks.find((t) => t.id === selectedNode);
        if (task) return task;
      }
    }
    return undefined;
  };
  const selectedTask = getSelectedTask();

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* ─── Toolbar ─── */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm z-10">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"
            title="Go back"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{title}</h1>
            <p className="text-xs text-gray-500">{subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={() => handleZoom('out')} className="p-2 hover:bg-gray-100 rounded-lg" title="Zoom out">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M19 13H5v-2h14v2z" /></svg>
          </button>
          <span className="text-xs font-mono text-gray-600 w-12 text-center">{Math.round(zoom * 100)}%</span>
          <button onClick={() => handleZoom('in')} className="p-2 hover:bg-gray-100 rounded-lg" title="Zoom in">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" /></svg>
          </button>
          <div className="w-px h-6 bg-gray-200 mx-1" />
          <button onClick={fitToScreen} className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-lg">
            Fit
          </button>
        </div>
      </div>

      {/* ─── Canvas Area ─── */}
      <div className="flex-1 flex overflow-hidden">
        <div
          ref={containerRef}
          className={`flex-1 overflow-hidden relative ${isPanning ? 'cursor-grabbing' : 'cursor-grab'}`}
          role="application"
          aria-label="Canvas area"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <svg ref={svgRef} width="100%" height="100%" className="absolute inset-0">
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" />
              </marker>
              <marker id="arrowhead-active" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6" />
              </marker>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="0.5" />
              </pattern>
            </defs>

            <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
              {/* Background grid */}
              <rect className="canvas-bg" x="-2000" y="-2000" width="6000" height="6000" fill="url(#grid)" />

              {/* ─── Edges ─── */}
              {canvas.edges.map((edge) => {
                const src = canvas.nodes.find((n) => n.id === edge.source);
                const tgt = canvas.nodes.find((n) => n.id === edge.target);
                if (!src || !tgt) return null;

                const srcH = getStageHeight(src);
                const tgtH = getStageHeight(tgt);

                const x1 = src.position.x + NODE_W;
                const y1 = src.position.y + srcH / 2;
                const x2 = tgt.position.x;
                const y2 = tgt.position.y + tgtH / 2;
                const cx1 = x1 + 60;
                const cx2 = x2 - 60;

                return (
                  <path
                    key={edge.id}
                    d={`M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`}
                    fill="none"
                    stroke={edge.animated ? '#3b82f6' : '#9ca3af'}
                    strokeWidth={edge.animated ? 2.5 : 1.5}
                    strokeDasharray={edge.animated ? '8,4' : 'none'}
                    markerEnd={edge.animated ? 'url(#arrowhead-active)' : 'url(#arrowhead)'}
                  >
                    {edge.animated && (
                      <animate attributeName="stroke-dashoffset" from="24" to="0" dur="1s" repeatCount="indefinite" />
                    )}
                  </path>
                );
              })}

              {/* ─── Stage Nodes ─── */}
              {canvas.nodes.filter(n => n.type === 'stage').map((node) => {
                const style = getStatusStyle(node.data.status);
                const isSelected = selectedNode === node.id;
                const isExpanded = expandedNodes.has(node.id);
                const stageH = getStageHeight(node);
                const steps = node.data.steps || [];

                return (
                  <g key={node.id} className="cursor-pointer">
                    {/* Stage container */}
                    <rect
                      x={node.position.x}
                      y={node.position.y}
                      width={NODE_W}
                      height={stageH}
                      rx={10}
                      fill={style.bg}
                      stroke={isSelected ? '#3b82f6' : style.border}
                      strokeWidth={isSelected ? 2.5 : 1.5}
                      onClick={(e) => handleNodeClick(node.id, e)}
                      filter={isSelected ? 'drop-shadow(0 4px 12px rgba(59,130,246,0.25))' : 'drop-shadow(0 1px 3px rgba(0,0,0,0.08))'}
                    />

                    {/* Status dot */}
                    <circle cx={node.position.x + 16} cy={node.position.y + 20} r={5} fill={style.dot} />

                    {/* Stage label */}
                    <text
                      x={node.position.x + 28}
                      y={node.position.y + 24}
                      fontSize="13"
                      fontWeight="600"
                      fill={style.text}
                      onClick={(e) => handleNodeClick(node.id, e)}
                    >
                      {node.data.label.length > 22 ? node.data.label.substring(0, 22) + '...' : node.data.label}
                    </text>

                    {/* Progress text */}
                    {node.data.progress && (
                      <text x={node.position.x + 28} y={node.position.y + 42} fontSize="11" fill="#6b7280">
                        {node.data.progress} ({node.data.completedCount || 0}/{node.data.taskCount || 0} tasks)
                      </text>
                    )}
                    {!node.data.progress && node.data.taskCount !== undefined && (
                      <text x={node.position.x + 28} y={node.position.y + 42} fontSize="11" fill="#6b7280">
                        {node.data.stepCount || 0} steps, {node.data.taskCount} tasks
                      </text>
                    )}

                    {/* Expand/collapse toggle */}
                    {steps.length > 0 && (
                      <g onClick={(e) => { e.stopPropagation(); toggleExpand(node.id); }} className="cursor-pointer">
                        <rect x={node.position.x + NODE_W - 30} y={node.position.y + 8} width={22} height={22} rx={4} fill="white" stroke="#d1d5db" strokeWidth={1} opacity={0.8} />
                        <text x={node.position.x + NODE_W - 19} y={node.position.y + 24} fontSize="14" textAnchor="middle" fill="#6b7280">
                          {isExpanded ? '\u2212' : '+'}
                        </text>
                      </g>
                    )}

                    {/* Progress bar */}
                    {node.data.taskCount != null && node.data.taskCount > 0 && (
                      <g>
                        <rect x={node.position.x + 14} y={node.position.y + 54} width={NODE_W - 28} height={4} rx={2} fill="#e5e7eb" />
                        <rect
                          x={node.position.x + 14}
                          y={node.position.y + 54}
                          width={Math.max(0, (NODE_W - 28) * ((node.data.completedCount || 0) / node.data.taskCount))}
                          height={4}
                          rx={2}
                          fill="#10b981"
                        />
                      </g>
                    )}

                    {/* ─── Expanded: Steps & Tasks ─── */}
                    {isExpanded && steps.length > 0 && (() => {
                      let yOff = node.position.y + NODE_H + 6;
                      return steps.map((step) => {
                        const stepStyle = getStatusStyle(step.status);
                        const stepExpanded = expandedNodes.has(step.id);
                        const stepY = yOff;
                        yOff += STEP_H + 6;
                        if (stepExpanded) {
                          yOff += step.tasks.length * (TASK_H + 4) + 4;
                        }

                        return (
                          <g key={step.id}>
                            {/* Step box */}
                            <rect
                              x={node.position.x + 10}
                              y={stepY}
                              width={NODE_W - 20}
                              height={STEP_H}
                              rx={6}
                              fill="white"
                              stroke={selectedNode === step.id ? '#3b82f6' : stepStyle.border}
                              strokeWidth={selectedNode === step.id ? 2 : 1}
                              onClick={(e) => handleNodeClick(step.id, e)}
                              className="cursor-pointer"
                            />
                            <circle cx={node.position.x + 24} cy={stepY + 18} r={4} fill={stepStyle.dot} />
                            <text
                              x={node.position.x + 34}
                              y={stepY + 22}
                              fontSize="11"
                              fontWeight="500"
                              fill={stepStyle.text}
                              onClick={(e) => handleNodeClick(step.id, e)}
                              className="cursor-pointer"
                            >
                              {step.name.length > 20 ? step.name.substring(0, 20) + '...' : step.name}
                            </text>
                            <text x={node.position.x + 34} y={stepY + 38} fontSize="9" fill="#9ca3af">
                              {step.tasks.length} tasks
                            </text>

                            {/* Step expand toggle */}
                            {step.tasks.length > 0 && (
                              <g onClick={(e) => { e.stopPropagation(); toggleExpand(step.id); }} className="cursor-pointer">
                                <text x={node.position.x + NODE_W - 24} y={stepY + 24} fontSize="11" textAnchor="middle" fill="#9ca3af">
                                  {stepExpanded ? '\u25BE' : '\u25B8'}
                                </text>
                              </g>
                            )}

                            {/* Tasks inside step */}
                            {stepExpanded && step.tasks.map((task, tIdx) => {
                              const taskY = stepY + STEP_H + 4 + tIdx * (TASK_H + 4);
                              const taskStyle = getStatusStyle(task.status);
                              return (
                                <g key={task.id}>
                                  <rect
                                    x={node.position.x + 20}
                                    y={taskY}
                                    width={NODE_W - 40}
                                    height={TASK_H}
                                    rx={4}
                                    fill={taskStyle.bg}
                                    stroke={selectedNode === task.id ? '#3b82f6' : taskStyle.border}
                                    strokeWidth={selectedNode === task.id ? 1.5 : 0.5}
                                    onClick={(e) => handleNodeClick(task.id, e)}
                                    className="cursor-pointer"
                                  />
                                  <circle cx={node.position.x + 32} cy={taskY + 16} r={3} fill={taskStyle.dot} />
                                  <text
                                    x={node.position.x + 42}
                                    y={taskY + (task.agents && task.agents.length > 0 ? 14 : 20)}
                                    fontSize="10"
                                    fill={taskStyle.text}
                                    onClick={(e) => handleNodeClick(task.id, e)}
                                    className="cursor-pointer"
                                  >
                                    {task.name.length > 18 ? task.name.substring(0, 18) + '...' : task.name}
                                  </text>
                                  {/* Agent indicator dots */}
                                  {task.agents && task.agents.length > 0 && (
                                    <g>
                                      {task.agents.map((agent, aIdx) => (
                                        <g key={agent.id}>
                                          <circle
                                            cx={node.position.x + 36 + aIdx * 14}
                                            cy={taskY + 26}
                                            r={4}
                                            fill={AGENT_TYPE_DOT_COLORS[agent.agent_type] || AGENT_TYPE_DOT_COLORS.custom}
                                            stroke={AGENT_STATUS_DOT_COLORS[agent.status] || AGENT_STATUS_DOT_COLORS.pending}
                                            strokeWidth={1.5}
                                          >
                                            <title>{`${agent.agent_name} (${agent.status})`}</title>
                                          </circle>
                                        </g>
                                      ))}
                                    </g>
                                  )}
                                </g>
                              );
                            })}
                          </g>
                        );
                      });
                    })()}
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* ─── Details Panel ─── */}
        {selectedNode && selectedNodeData && (
          <div className="w-80 bg-white border-l border-gray-200 p-5 overflow-y-auto shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">
                {entityType || selectedNodeData.type} Details
              </h3>
              <button onClick={() => setSelectedNode(null)} title="Close details" className="text-gray-400 hover:text-gray-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Name</label>
                <p className="text-sm font-semibold text-gray-900 mt-0.5">{selectedNodeData.data.label}</p>
              </div>

              {selectedNodeData.data.status && (
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">Status</label>
                  <div className="mt-1">
                    <span
                      className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${getStatusClasses(selectedNodeData.data.status).badge}`}
                      data-status={selectedNodeData.data.status}
                    >
                      {selectedNodeData.data.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
              )}

              {selectedNodeData.data.progress && (
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">Progress</label>
                  <p className="text-sm text-gray-900 mt-0.5">{selectedNodeData.data.progress}</p>
                </div>
              )}

              {selectedNodeData.data.taskCount !== undefined && (
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">Tasks</label>
                  <p className="text-sm text-gray-900 mt-0.5">
                    {selectedNodeData.data.completedCount || 0} / {selectedNodeData.data.taskCount} completed
                  </p>
                </div>
              )}

              {/* Agents on selected task */}
              {selectedTask?.agents && selectedTask.agents.length > 0 && (
                <div className="pt-3 border-t border-gray-100">
                  <label className="text-xs font-medium text-gray-500 uppercase mb-2 block">AI Agents</label>
                  <div className="space-y-2">
                    {selectedTask.agents.map((agent) => (
                      <div key={agent.id} className="flex items-center justify-between bg-gray-50 rounded p-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2.5 h-2.5 rounded-full ${AGENT_TYPE_DOT_CLASSES[agent.agent_type] || AGENT_TYPE_DOT_CLASSES.custom}`}
                          />
                          <span className="text-xs font-medium text-gray-800">{agent.agent_name}</span>
                        </div>
                        <span
                          className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${AGENT_STATUS_CLASSES[agent.status] || AGENT_STATUS_CLASSES.pending}`}
                        >
                          {agent.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status update (assignment mode only) */}
              {isAssignment && selectedNodeData.data.status && (
                <div className="pt-3 border-t border-gray-100">
                  <label className="text-xs font-medium text-gray-500 uppercase mb-2 block">Update Status</label>
                  <div className="grid grid-cols-2 gap-2">
                    {STATUS_OPTIONS.map((status) => {
                      const nodeType = entityType || selectedNodeData.type;
                      const isCurrent = selectedNodeData.data.status === status ||
                        selectedNodeData.data.status === status.toUpperCase();
                      const sc = getStatusClasses(status);
                      return (
                        <button
                          key={status}
                          disabled={isCurrent || updatingNode === selectedNode}
                          onClick={() => updateNodeStatus(nodeType, selectedNode!, status)}
                          className={`px-2 py-1.5 rounded text-xs font-medium transition-all disabled:opacity-40 ${isCurrent ? sc.btnActive : sc.btnInactive}`}
                        >
                          {updatingNode === selectedNode ? '...' : status.replace(/_/g, ' ')}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ─── Legend ─── */}
      <div className="bg-white border-t border-gray-200 px-6 py-2 flex items-center gap-6 text-xs text-gray-500">
        <span className="font-medium text-gray-700">Legend:</span>
        {Object.entries({ 'Not Started': 'not_started', 'In Progress': 'in_progress', 'Completed': 'completed', 'Blocked': 'blocked' }).map(([label, key]) => {
          const dotClass: Record<string, string> = {
            not_started: 'bg-gray-400',
            in_progress: 'bg-amber-500',
            completed: 'bg-emerald-500',
            blocked: 'bg-red-500',
          };
          return (
            <span key={key} className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${dotClass[key] || 'bg-gray-400'}`} />
              {label}
            </span>
          );
        })}
        <span className="ml-auto text-gray-400">Scroll to zoom  |  Drag to pan  |  Click nodes to inspect</span>
        <span className="flex items-center gap-1.5 ml-4">
          <span className="w-2.5 h-2.5 rounded-full bg-violet-600" />
          <span>Agent</span>
        </span>
      </div>
    </div>
  );
}
