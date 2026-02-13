"use client";

import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

// ── Types ──────────────────────────────────────────────────────────
interface AgentOnTask {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  is_required: boolean;
  position: number;
  instructions: string | null;
}

interface TaskItem {
  id: string;
  name: string;
  description: string | null;
  position: number;
  agents: AgentOnTask[];
}

interface StepItem {
  id: string;
  name: string;
  description: string | null;
  position: number;
  tasks: TaskItem[];
}

interface StageItem {
  id: string;
  name: string;
  description: string | null;
  position: number;
  steps: StepItem[];
}

interface WorkflowDetail {
  id: string;
  name: string;
  description: string | null;
  status: string;
  organization_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  stages: StageItem[];
}

interface WorkflowListItem {
  id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface AgentItem {
  id: string;
  name: string;
  agent_type: string;
  status: string;
}

// ── Constants ──────────────────────────────────────────────────────
const STATUS_BADGE: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  active: "bg-emerald-100 text-emerald-700",
  archived: "bg-amber-100 text-amber-700",
};

const AGENT_TYPE_BADGE: Record<string, string> = {
  document_intelligence: "bg-purple-50 text-purple-700",
  search: "bg-blue-50 text-blue-700",
  extraction: "bg-amber-50 text-amber-700",
  validation: "bg-emerald-50 text-emerald-700",
  custom: "bg-gray-50 text-gray-700",
};

const AGENT_TYPE_LABEL: Record<string, string> = {
  document_intelligence: "Doc Intel",
  search: "Search",
  extraction: "Extraction",
  validation: "Validation",
  custom: "Custom",
};

// ── Shared styles ──────────────────────────────────────────────────
const inputClass =
  "w-full h-9 px-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none";
const textareaClass =
  "w-full px-3 py-2 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none resize-y min-h-18";

// ── Icons ──────────────────────────────────────────────────────────
const PlusIcon = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

const TrashIcon = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
);

const EditIcon = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);

const BackIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12" />
    <polyline points="12 19 5 12 12 5" />
  </svg>
);

const RobotIcon = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <path d="M12 7v4" />
    <line x1="8" y1="16" x2="8" y2="16" />
    <line x1="16" y1="16" x2="16" y2="16" />
  </svg>
);

const XIcon = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

// ── Modal wrapper ──────────────────────────────────────────────────
function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 animate-fade-in">
      <div className="bg-surface rounded-2xl border border-border w-full max-w-md mx-4 shadow-xl animate-fade-in-up">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="text-base font-semibold text-text-primary">{title}</h2>
          <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-alt transition-colors" title="Close">
            <XIcon />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────
export default function WorkflowPage() {
  // ── List state ──
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "draft" | "active" | "archived">("all");

  // ── Detail state ──
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<WorkflowDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // ── Create workflow modal ──
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  // ── Edit workflow modal ──
  const [showEdit, setShowEdit] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  // ── Add stage modal ──
  const [showStageModal, setShowStageModal] = useState(false);
  const [stageName, setStageName] = useState("");
  const [stageDesc, setStageDesc] = useState("");

  // ── Add step modal ──
  const [showStepModal, setShowStepModal] = useState(false);
  const [stepStageId, setStepStageId] = useState<string | null>(null);
  const [stepName, setStepName] = useState("");
  const [stepDesc, setStepDesc] = useState("");

  // ── Add task modal ──
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskStepId, setTaskStepId] = useState<string | null>(null);
  const [taskName, setTaskName] = useState("");
  const [taskDesc, setTaskDesc] = useState("");

  // ── Agent config modal ──
  const [showAgentModal, setShowAgentModal] = useState(false);
  const [agentTaskId, setAgentTaskId] = useState<string | null>(null);
  const [availableAgents, setAvailableAgents] = useState<AgentItem[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [agentRequired, setAgentRequired] = useState(false);
  const [agentInstructions, setAgentInstructions] = useState("");
  const [agentsLoading, setAgentsLoading] = useState(false);

  // ── Saving indicator ──
  const [saving, setSaving] = useState(false);

  // ── Drag state ──
  const [draggedStage, setDraggedStage] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);

  // ── Fetch workflows list ──
  const fetchWorkflows = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiCall<WorkflowListItem[]>(API_ENDPOINTS.WORKFLOWS, { method: "GET" });
      setWorkflows(data);
    } catch {
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  // ── Fetch workflow detail (hierarchy) ──
  const fetchDetail = useCallback(async (id: string) => {
    try {
      setDetailLoading(true);
      const data = await apiCall<WorkflowDetail>(API_ENDPOINTS.WORKFLOW(id), { method: "GET" });
      setDetail(data);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId) fetchDetail(selectedId);
    else setDetail(null);
  }, [selectedId, fetchDetail]);

  // ── Fetch available agents (for agent config modal) ──
  const fetchAgents = useCallback(async () => {
    try {
      setAgentsLoading(true);
      const data = await apiCall<AgentItem[]>(API_ENDPOINTS.AGENTS, { method: "GET" });
      setAvailableAgents(data);
    } catch {
      setAvailableAgents([]);
    } finally {
      setAgentsLoading(false);
    }
  }, []);

  // ── Filtered list ──
  const filtered = workflows.filter((w) => {
    if (filter !== "all" && w.status !== filter) return false;
    if (search && !w.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  // ── Counts ──
  const countByStatus = (s: string) => workflows.filter((w) => w.status === s).length;

  // ── Workflow CRUD handlers ──

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOWS, {
        method: "POST",
        body: JSON.stringify({ name: newName.trim(), description: newDesc.trim() || null }),
      });
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
      await fetchWorkflows();
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this workflow and all its stages, steps, and tasks?")) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW(id), { method: "DELETE" });
      if (selectedId === id) { setSelectedId(null); setDetail(null); }
      await fetchWorkflows();
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleToggleStatus = async (id: string, currentStatus: string) => {
    const newStatus = currentStatus === "active" ? "draft" : "active";
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW(id), {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });
      await fetchWorkflows();
      if (selectedId === id && detail) {
        setDetail({ ...detail, status: newStatus });
      }
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!detail || !editName.trim()) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW(detail.id), {
        method: "PATCH",
        body: JSON.stringify({ name: editName.trim(), description: editDesc.trim() || null }),
      });
      setShowEdit(false);
      await fetchWorkflows();
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const openEdit = () => {
    if (!detail) return;
    setEditName(detail.name);
    setEditDesc(detail.description || "");
    setShowEdit(true);
  };

  // ── Stage handlers ──

  const handleAddStage = async () => {
    if (!detail || !stageName.trim()) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_STAGES(detail.id), {
        method: "POST",
        body: JSON.stringify({ name: stageName.trim(), description: stageDesc.trim() || null }),
      });
      setStageName("");
      setStageDesc("");
      setShowStageModal(false);
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteStage = async (stageId: string) => {
    if (!detail || !confirm("Delete this stage and all its steps and tasks?")) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_STAGE(stageId), { method: "DELETE" });
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  // Stage drag-and-drop reorder
  const handleDropStage = async (targetId: string) => {
    if (!detail || !draggedStage || draggedStage === targetId) {
      setDraggedStage(null);
      setDropTarget(null);
      return;
    }
    const stages = [...detail.stages];
    const fromIdx = stages.findIndex((s) => s.id === draggedStage);
    const toIdx = stages.findIndex((s) => s.id === targetId);
    if (fromIdx < 0 || toIdx < 0) return;
    const [moved] = stages.splice(fromIdx, 1);
    stages.splice(toIdx, 0, moved);
    // Optimistic update
    setDetail({ ...detail, stages });
    setDraggedStage(null);
    setDropTarget(null);
    // Persist reorder
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_STAGES_REORDER(detail.id), {
        method: "PUT",
        body: JSON.stringify(stages.map((s) => s.id)),
      });
      await fetchDetail(detail.id);
    } catch {
      await fetchDetail(detail.id);
    }
  };

  // ── Step handlers ──

  const openAddStep = (stageId: string) => {
    setStepStageId(stageId);
    setStepName("");
    setStepDesc("");
    setShowStepModal(true);
  };

  const handleAddStep = async () => {
    if (!detail || !stepStageId || !stepName.trim()) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_STAGE_STEPS(stepStageId), {
        method: "POST",
        body: JSON.stringify({ name: stepName.trim(), description: stepDesc.trim() || null }),
      });
      setStepName("");
      setStepDesc("");
      setStepStageId(null);
      setShowStepModal(false);
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteStep = async (stepId: string) => {
    if (!detail) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_STEP(stepId), { method: "DELETE" });
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  // ── Task handlers ──

  const openAddTask = (stepId: string) => {
    setTaskStepId(stepId);
    setTaskName("");
    setTaskDesc("");
    setShowTaskModal(true);
  };

  const handleAddTask = async () => {
    if (!detail || !taskStepId || !taskName.trim()) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_STEP_TASKS(taskStepId), {
        method: "POST",
        body: JSON.stringify({ name: taskName.trim(), description: taskDesc.trim() || null }),
      });
      setTaskName("");
      setTaskDesc("");
      setTaskStepId(null);
      setShowTaskModal(false);
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!detail) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_TASK(taskId), { method: "DELETE" });
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  // ── Agent config handlers ──

  const openAgentModal = (taskId: string) => {
    setAgentTaskId(taskId);
    setSelectedAgentId("");
    setAgentRequired(false);
    setAgentInstructions("");
    setShowAgentModal(true);
    fetchAgents();
  };

  const handleAttachAgent = async () => {
    if (!detail || !agentTaskId || !selectedAgentId) return;
    setSaving(true);
    try {
      await apiCall(API_ENDPOINTS.WORKFLOW_TASK_AGENTS(agentTaskId), {
        method: "POST",
        body: JSON.stringify({
          agent_id: selectedAgentId,
          is_required: agentRequired,
          instructions: agentInstructions.trim() || null,
        }),
      });
      setShowAgentModal(false);
      setSelectedAgentId("");
      setAgentRequired(false);
      setAgentInstructions("");
      setAgentTaskId(null);
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  const handleDetachAgent = async (wtaId: string) => {
    if (!detail || !confirm("Remove this agent from the task?")) return;
    setSaving(true);
    try {
      // The endpoint is /api/v1/agents/workflow-task-agents/{wta_id}
      await apiCall(`/api/v1/agents/workflow-task-agents/${wtaId}`, { method: "DELETE" });
      await fetchDetail(detail.id);
    } catch {
      // silently fail
    } finally {
      setSaving(false);
    }
  };

  // ───────────────────────────────────────────────────────────────
  // DETAIL VIEW
  // ───────────────────────────────────────────────────────────────
  if (selectedId) {
    if (detailLoading || !detail) {
      return (
        <div className="flex items-center justify-center min-h-100">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      );
    }

    return (
      <div>
        {/* Back */}
        <button onClick={() => setSelectedId(null)} className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary transition-colors mb-5 animate-fade-in">
          <BackIcon /> Back to Workflows
        </button>

        {/* Header card */}
        <div className="bg-surface rounded-xl border border-border p-5 mb-5 flex items-start justify-between animate-fade-in">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-text-primary">{detail.name}</h1>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase ${STATUS_BADGE[detail.status] || STATUS_BADGE.draft}`}>
                {detail.status}
              </span>
            </div>
            <p className="text-sm text-text-muted mt-1">{detail.description || "No description"}</p>
            <p className="text-xs text-text-muted mt-2">
              {detail.stages.length} stage{detail.stages.length !== 1 ? "s" : ""} · {detail.stages.reduce((a, s) => a + s.steps.length, 0)} step{detail.stages.reduce((a, s) => a + s.steps.length, 0) !== 1 ? "s" : ""} · {detail.stages.reduce((a, s) => a + s.steps.reduce((b, st) => b + st.tasks.length, 0), 0)} task{detail.stages.reduce((a, s) => a + s.steps.reduce((b, st) => b + st.tasks.length, 0), 0) !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button onClick={() => handleToggleStatus(detail.id, detail.status)} className="h-9 px-4 bg-surface hover:bg-surface-alt border border-border text-text-secondary text-sm font-medium rounded-lg transition-colors">
              {detail.status === "active" ? "Set Draft" : "Activate"}
            </button>
            <button onClick={openEdit} className="h-9 px-4 bg-surface hover:bg-surface-alt border border-border text-text-secondary text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
              <EditIcon /> Edit
            </button>
            <button onClick={() => { setStageName(""); setStageDesc(""); setShowStageModal(true); }} className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
              <PlusIcon /> Add Stage
            </button>
          </div>
        </div>

        {/* Stages */}
        {detail.stages.length === 0 ? (
          <div className="bg-surface rounded-xl border border-dashed border-border min-h-75 flex flex-col items-center justify-center animate-fade-in-up">
            <svg className="text-text-muted mb-4" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
            <h3 className="text-base font-semibold text-text-primary mb-1">No stages yet</h3>
            <p className="text-sm text-text-muted text-center max-w-md mb-5">
              Break down your workflow into stages. Each stage contains steps, and each step contains tasks.
            </p>
            <button onClick={() => { setStageName(""); setStageDesc(""); setShowStageModal(true); }} className="h-10 px-5 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
              <PlusIcon size={16} /> Create First Stage
            </button>
          </div>
        ) : (
          <div className="flex gap-4 overflow-x-auto pb-4 animate-fade-in-up">
            {detail.stages.map((stage, stageIdx) => (
              <div
                key={stage.id}
                draggable
                onDragStart={() => setDraggedStage(stage.id)}
                onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; }}
                onDrop={() => handleDropStage(stage.id)}
                onDragEnter={() => draggedStage && draggedStage !== stage.id && setDropTarget(stage.id)}
                onDragLeave={() => setDropTarget(null)}
                className={`w-85 shrink-0 bg-surface rounded-xl border overflow-hidden transition-all cursor-move ${draggedStage === stage.id ? "opacity-50" : ""} ${dropTarget === stage.id ? "border-accent border-2" : "border-border"}`}
              >
                {/* Stage header */}
                <div className="px-4 py-3.5 border-b border-border-light flex items-start justify-between">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded bg-accent/10 text-accent text-[10px] font-bold flex items-center justify-center shrink-0">
                        {stageIdx + 1}
                      </span>
                      <h3 className="text-sm font-semibold text-text-primary truncate">{stage.name}</h3>
                    </div>
                    {stage.description && <p className="text-xs text-text-muted mt-0.5 truncate">{stage.description}</p>}
                    <span className="inline-block mt-1.5 px-2 py-0.5 text-[10px] font-medium bg-surface-alt text-text-muted rounded">
                      {stage.steps.length} step{stage.steps.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={() => openAddStep(stage.id)} className="w-7 h-7 flex items-center justify-center rounded-lg text-text-muted hover:text-accent hover:bg-accent/5 transition-colors" title="Add step">
                      <PlusIcon />
                    </button>
                    <button onClick={() => handleDeleteStage(stage.id)} className="w-7 h-7 flex items-center justify-center rounded-lg text-text-muted hover:text-rose-500 hover:bg-rose-50 transition-colors" title="Delete stage">
                      <TrashIcon />
                    </button>
                  </div>
                </div>

                {/* Steps */}
                <div className="p-3 space-y-2 max-h-150 overflow-y-auto">
                  {stage.steps.length === 0 ? (
                    <p className="text-xs text-text-muted text-center py-3">No steps — click + to add one</p>
                  ) : (
                    stage.steps.map((step, stepIdx) => (
                      <div key={step.id} className="bg-surface-alt/50 rounded-lg overflow-hidden">
                        {/* Step header */}
                        <div className="flex items-start gap-2 px-3 py-2.5 group/step">
                          <span className="w-5 h-5 rounded-full bg-accent/10 text-accent text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                            {stepIdx + 1}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-text-primary">{step.name}</p>
                            {step.description && <p className="text-[11px] text-text-muted">{step.description}</p>}
                            {step.tasks.length > 0 && (
                              <span className="text-[10px] text-text-muted mt-1 inline-block">
                                {step.tasks.length} task{step.tasks.length !== 1 ? "s" : ""}
                              </span>
                            )}
                          </div>
                          <div className="flex gap-1 opacity-0 group-hover/step:opacity-100 shrink-0">
                            <button onClick={() => openAddTask(step.id)} className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-accent transition-colors" title="Add task">
                              <PlusIcon size={12} />
                            </button>
                            <button onClick={() => handleDeleteStep(step.id)} className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-rose-500 transition-colors" title="Delete step">
                              <XIcon size={12} />
                            </button>
                          </div>
                        </div>

                        {/* Tasks */}
                        {step.tasks.length > 0 && (
                          <div className="px-3 pb-2 space-y-1.5">
                            {step.tasks.map((task) => (
                              <div key={task.id} className="bg-white rounded-lg border border-border-light overflow-hidden">
                                {/* Task row */}
                                <div className="px-2.5 py-2 flex items-start gap-2 group/task">
                                  <div className="w-1.5 h-1.5 rounded-full bg-accent/40 mt-1.5 shrink-0" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-[11px] font-medium text-text-primary">{task.name}</p>
                                    {task.description && <p className="text-[10px] text-text-muted">{task.description}</p>}
                                  </div>
                                  <div className="flex gap-1 opacity-0 group-hover/task:opacity-100 shrink-0">
                                    <button onClick={() => openAgentModal(task.id)} className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-purple-600 transition-colors" title="Configure agents">
                                      <RobotIcon size={12} />
                                    </button>
                                    <button onClick={() => handleDeleteTask(task.id)} className="w-5 h-5 flex items-center justify-center rounded text-text-muted hover:text-rose-500 transition-colors" title="Delete task">
                                      <XIcon size={12} />
                                    </button>
                                  </div>
                                </div>

                                {/* Agent badges on task */}
                                {task.agents.length > 0 && (
                                  <div className="px-2.5 pb-2 flex flex-wrap gap-1">
                                    {task.agents.map((agent) => (
                                      <span
                                        key={agent.id}
                                        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-medium ${AGENT_TYPE_BADGE[agent.agent_type] || AGENT_TYPE_BADGE.custom}`}
                                      >
                                        <RobotIcon size={9} />
                                        {agent.agent_name}
                                        {agent.is_required && <span className="text-rose-500">*</span>}
                                        <button
                                          onClick={() => handleDetachAgent(agent.id)}
                                          className="ml-0.5 hover:text-rose-500 transition-colors"
                                          title="Remove agent"
                                        >
                                          <XIcon size={8} />
                                        </button>
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Add task inline button */}
                        <div className="px-3 pb-2">
                          <button
                            onClick={() => openAddTask(step.id)}
                            className="w-full h-7 flex items-center justify-center gap-1 text-[10px] text-text-muted hover:text-accent hover:bg-accent/5 rounded-md border border-dashed border-border-light transition-colors"
                          >
                            <PlusIcon size={10} /> Add Task
                          </button>
                        </div>
                      </div>
                    ))
                  )}

                  {/* Add step inline button */}
                  <button
                    onClick={() => openAddStep(stage.id)}
                    className="w-full h-9 flex items-center justify-center gap-1.5 text-xs text-text-muted hover:text-accent hover:bg-accent/5 rounded-lg border border-dashed border-border transition-colors"
                  >
                    <PlusIcon size={12} /> Add Step
                  </button>
                </div>
              </div>
            ))}

            {/* Add stage column */}
            <div className="w-85 shrink-0">
              <button
                onClick={() => { setStageName(""); setStageDesc(""); setShowStageModal(true); }}
                className="w-full h-full min-h-50 flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border text-text-muted hover:text-accent hover:border-accent/30 hover:bg-accent/5 transition-all"
              >
                <PlusIcon size={24} />
                <span className="text-sm font-medium">Add Stage</span>
              </button>
            </div>
          </div>
        )}

        {/* ── Modals ── */}

        {/* Edit workflow modal */}
        <Modal open={showEdit} onClose={() => setShowEdit(false)} title="Edit Workflow">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Name</label>
              <input className={inputClass} value={editName} onChange={(e) => setEditName(e.target.value)} placeholder="Workflow name" />
            </div>
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Description</label>
              <textarea className={textareaClass} value={editDesc} onChange={(e) => setEditDesc(e.target.value)} placeholder="Optional description" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowEdit(false)} className="h-9 px-4 bg-surface border border-border text-text-secondary text-sm font-medium rounded-lg hover:bg-surface-alt transition-colors">Cancel</button>
              <button onClick={handleSaveEdit} disabled={saving || !editName.trim()} className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50">
                {saving ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </Modal>

        {/* Add stage modal */}
        <Modal open={showStageModal} onClose={() => setShowStageModal(false)} title="Add Stage">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Stage Name</label>
              <input className={inputClass} value={stageName} onChange={(e) => setStageName(e.target.value)} placeholder="e.g. Planning, Execution, Review" />
            </div>
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Description</label>
              <textarea className={textareaClass} value={stageDesc} onChange={(e) => setStageDesc(e.target.value)} placeholder="Optional description" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowStageModal(false)} className="h-9 px-4 bg-surface border border-border text-text-secondary text-sm font-medium rounded-lg hover:bg-surface-alt transition-colors">Cancel</button>
              <button onClick={handleAddStage} disabled={saving || !stageName.trim()} className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50">
                {saving ? "Adding…" : "Add Stage"}
              </button>
            </div>
          </div>
        </Modal>

        {/* Add step modal */}
        <Modal open={showStepModal} onClose={() => setShowStepModal(false)} title="Add Step">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Step Name</label>
              <input className={inputClass} value={stepName} onChange={(e) => setStepName(e.target.value)} placeholder="e.g. Data Collection, Analysis" />
            </div>
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Description</label>
              <textarea className={textareaClass} value={stepDesc} onChange={(e) => setStepDesc(e.target.value)} placeholder="Optional description" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowStepModal(false)} className="h-9 px-4 bg-surface border border-border text-text-secondary text-sm font-medium rounded-lg hover:bg-surface-alt transition-colors">Cancel</button>
              <button onClick={handleAddStep} disabled={saving || !stepName.trim()} className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50">
                {saving ? "Adding…" : "Add Step"}
              </button>
            </div>
          </div>
        </Modal>

        {/* Add task modal */}
        <Modal open={showTaskModal} onClose={() => setShowTaskModal(false)} title="Add Task">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Task Name</label>
              <input className={inputClass} value={taskName} onChange={(e) => setTaskName(e.target.value)} placeholder="e.g. Review document, Verify compliance" />
            </div>
            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">Description</label>
              <textarea className={textareaClass} value={taskDesc} onChange={(e) => setTaskDesc(e.target.value)} placeholder="Optional description" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowTaskModal(false)} className="h-9 px-4 bg-surface border border-border text-text-secondary text-sm font-medium rounded-lg hover:bg-surface-alt transition-colors">Cancel</button>
              <button onClick={handleAddTask} disabled={saving || !taskName.trim()} className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50">
                {saving ? "Adding…" : "Add Task"}
              </button>
            </div>
          </div>
        </Modal>

        {/* Agent config modal */}
        <Modal open={showAgentModal} onClose={() => setShowAgentModal(false)} title="Attach AI Agent">
          <div className="space-y-4">
            {agentsLoading ? (
              <div className="flex items-center justify-center py-6">
                <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            ) : availableAgents.length === 0 ? (
              <div className="text-center py-6">
                <RobotIcon size={32} />
                <p className="text-sm text-text-muted mt-2">No agents available. Create agents first in the Agents page.</p>
              </div>
            ) : (
              <>
                <div>
                  <label className="text-xs font-medium text-text-secondary block mb-1.5">Select Agent</label>
                  <select
                    className={inputClass}
                    value={selectedAgentId}
                    onChange={(e) => setSelectedAgentId(e.target.value)}
                    title="Select agent"
                  >
                    <option value="">Choose an agent…</option>
                    {availableAgents
                      .filter((a) => a.status === "active")
                      .map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name} ({AGENT_TYPE_LABEL[a.agent_type] || a.agent_type})
                        </option>
                      ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-text-secondary block mb-1.5">Instructions</label>
                  <textarea
                    className={textareaClass}
                    value={agentInstructions}
                    onChange={(e) => setAgentInstructions(e.target.value)}
                    placeholder="Optional instructions for this agent on this task"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="agent-required"
                    checked={agentRequired}
                    onChange={(e) => setAgentRequired(e.target.checked)}
                    className="w-4 h-4 rounded border-border text-accent focus:ring-accent/20"
                  />
                  <label htmlFor="agent-required" className="text-xs text-text-secondary">Required — task cannot complete without this agent running</label>
                </div>
              </>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setShowAgentModal(false)} className="h-9 px-4 bg-surface border border-border text-text-secondary text-sm font-medium rounded-lg hover:bg-surface-alt transition-colors">Cancel</button>
              <button
                onClick={handleAttachAgent}
                disabled={saving || !selectedAgentId}
                className="h-9 px-4 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <RobotIcon size={14} />
                {saving ? "Attaching…" : "Attach Agent"}
              </button>
            </div>
          </div>
        </Modal>
      </div>
    );
  }

  // ───────────────────────────────────────────────────────────────
  // LIST VIEW
  // ───────────────────────────────────────────────────────────────
  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6 animate-fade-in">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Workflow Templates</h1>
          <p className="text-sm text-text-muted mt-0.5">Design reusable workflow templates with stages, steps, and tasks</p>
        </div>
        <button onClick={() => { setNewName(""); setNewDesc(""); setShowCreate(true); }} className="h-10 px-5 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
          <PlusIcon size={16} /> New Workflow
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6 animate-fade-in">
        {[
          { label: "Total", count: workflows.length, color: "bg-blue-50 text-blue-700" },
          { label: "Draft", count: countByStatus("draft"), color: "bg-gray-50 text-gray-600" },
          { label: "Active", count: countByStatus("active"), color: "bg-emerald-50 text-emerald-700" },
          { label: "Archived", count: countByStatus("archived"), color: "bg-amber-50 text-amber-700" },
        ].map((s) => (
          <div key={s.label} className="bg-surface rounded-xl border border-border p-4">
            <p className="text-xs text-text-muted mb-1">{s.label}</p>
            <p className="text-2xl font-bold text-text-primary">{s.count}</p>
          </div>
        ))}
      </div>

      {/* Search & filter */}
      <div className="flex items-center gap-3 mb-4 animate-fade-in">
        <div className="relative flex-1 max-w-xs">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input className="w-full h-9 pl-9 pr-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none" placeholder="Search workflows…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="flex bg-surface border border-border rounded-lg overflow-hidden">
          {(["all", "draft", "active", "archived"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`h-9 px-3.5 text-xs font-medium transition-colors capitalize ${filter === f ? "bg-accent text-white" : "text-text-muted hover:text-text-primary hover:bg-surface-alt"}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center min-h-50">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-surface rounded-xl border border-dashed border-border flex flex-col items-center justify-center py-16 animate-fade-in-up">
          <svg className="text-text-muted mb-4" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <h3 className="text-base font-semibold text-text-primary mb-1">
            {workflows.length === 0 ? "No workflows yet" : "No matching workflows"}
          </h3>
          <p className="text-sm text-text-muted mb-5">
            {workflows.length === 0 ? "Create your first workflow template to get started." : "Try adjusting your search or filter."}
          </p>
          {workflows.length === 0 && (
            <button onClick={() => { setNewName(""); setNewDesc(""); setShowCreate(true); }} className="h-10 px-5 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
              <PlusIcon size={16} /> Create Workflow
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2 animate-fade-in-up">
          {filtered.map((w) => (
            <div key={w.id} className="bg-surface rounded-xl border border-border p-4 flex items-center justify-between hover:border-accent/30 transition-colors group">
              <button onClick={() => setSelectedId(w.id)} className="flex-1 text-left min-w-0">
                <div className="flex items-center gap-3">
                  <h3 className="text-sm font-semibold text-text-primary group-hover:text-accent transition-colors">{w.name}</h3>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${STATUS_BADGE[w.status] || STATUS_BADGE.draft}`}>
                    {w.status}
                  </span>
                </div>
                <p className="text-xs text-text-muted mt-0.5 truncate">{w.description || "No description"}</p>
              </button>
              <div className="flex items-center gap-2 shrink-0 ml-4">
                <button onClick={() => handleToggleStatus(w.id, w.status)} className="h-8 px-3 text-xs font-medium bg-surface-alt hover:bg-surface border border-border rounded-lg text-text-secondary transition-colors">
                  {w.status === "active" ? "Draft" : "Activate"}
                </button>
                <button onClick={() => handleDelete(w.id)} className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-rose-500 hover:bg-rose-50 transition-colors" title="Delete workflow">
                  <TrashIcon />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create workflow modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Workflow">
        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-text-secondary block mb-1.5">Workflow Name</label>
            <input className={inputClass} value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="e.g. Annual Audit, Risk Assessment" />
          </div>
          <div>
            <label className="text-xs font-medium text-text-secondary block mb-1.5">Description</label>
            <textarea className={textareaClass} value={newDesc} onChange={(e) => setNewDesc(e.target.value)} placeholder="Optional description of this workflow template" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={() => setShowCreate(false)} className="h-9 px-4 bg-surface border border-border text-text-secondary text-sm font-medium rounded-lg hover:bg-surface-alt transition-colors">Cancel</button>
            <button onClick={handleCreate} disabled={saving || !newName.trim()} className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50">
              {saving ? "Creating…" : "Create Workflow"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
