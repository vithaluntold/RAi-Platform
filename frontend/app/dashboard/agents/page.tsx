"use client";

import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

interface AgentItem {
  id: string;
  name: string;
  description: string | null;
  agent_type: string;
  backend_provider: string;
  status: string;
  is_system: boolean;
  capabilities: Record<string, unknown> | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

const AGENT_TYPES = [
  { value: "document_intelligence", label: "Document Intelligence" },
  { value: "search", label: "Search" },
  { value: "extraction", label: "Extraction" },
  { value: "validation", label: "Validation" },
  { value: "custom", label: "Custom" },
];

const BACKEND_PROVIDERS = [
  { value: "azure", label: "Azure AI" },
  { value: "cyloid", label: "Cyloid" },
  { value: "openai", label: "OpenAI" },
  { value: "custom", label: "Custom" },
];

const typeBadge = (type: string) => {
  const map: Record<string, string> = {
    document_intelligence: "bg-purple-50 text-purple-700 border-purple-200",
    search: "bg-blue-50 text-blue-700 border-blue-200",
    extraction: "bg-amber-50 text-amber-700 border-amber-200",
    validation: "bg-emerald-50 text-emerald-700 border-emerald-200",
    custom: "bg-gray-50 text-gray-700 border-gray-200",
  };
  return map[type] || map.custom;
};

const statusBadge = (status: string) => {
  const map: Record<string, string> = {
    active: "bg-emerald-50 text-emerald-700 border-emerald-200",
    inactive: "bg-gray-50 text-gray-600 border-gray-200",
    deprecated: "bg-red-50 text-red-700 border-red-200",
  };
  return map[status] || map.active;
};

const providerBadge = (provider: string) => {
  const map: Record<string, string> = {
    azure: "bg-sky-50 text-sky-700",
    cyloid: "bg-indigo-50 text-indigo-700",
    openai: "bg-green-50 text-green-700",
    custom: "bg-gray-50 text-gray-600",
  };
  return map[provider] || map.custom;
};

const typeLabel = (type: string) =>
  AGENT_TYPES.find((t) => t.value === type)?.label || type;

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentItem | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [detailAgent, setDetailAgent] = useState<AgentItem | null>(null);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formType, setFormType] = useState("custom");
  const [formProvider, setFormProvider] = useState("azure");
  const [formStatus, setFormStatus] = useState("active");
  const [formCapabilities, setFormCapabilities] = useState("");
  const [formInputSchema, setFormInputSchema] = useState("");
  const [formOutputSchema, setFormOutputSchema] = useState("");

  const fetchAgents = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterType) params.set("agent_type", filterType);
      if (filterStatus) params.set("status", filterStatus);
      const qs = params.toString();
      const data = await apiCall<AgentItem[]>(
        `${API_ENDPOINTS.AGENTS}${qs ? `?${qs}` : ""}`
      );
      setAgents(data);
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    } finally {
      setLoading(false);
    }
  }, [filterType, filterStatus]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const resetForm = () => {
    setFormName("");
    setFormDescription("");
    setFormType("custom");
    setFormProvider("azure");
    setFormStatus("active");
    setFormCapabilities("");
    setFormInputSchema("");
    setFormOutputSchema("");
    setEditingAgent(null);
  };

  const openEditModal = (agent: AgentItem) => {
    setEditingAgent(agent);
    setFormName(agent.name);
    setFormDescription(agent.description || "");
    setFormType(agent.agent_type);
    setFormProvider(agent.backend_provider);
    setFormStatus(agent.status);
    setFormCapabilities(agent.capabilities ? JSON.stringify(agent.capabilities, null, 2) : "");
    setFormInputSchema("");
    setFormOutputSchema("");
    setShowModal(true);
  };

  const openDetail = (agent: AgentItem) => {
    setDetailAgent(agent);
    setShowDetail(true);
  };

  const parseJsonSafe = (str: string): Record<string, unknown> | null => {
    if (!str.trim()) return null;
    try {
      return JSON.parse(str);
    } catch {
      return null;
    }
  };

  const handleSave = async () => {
    if (!formName.trim()) return;
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        name: formName.trim(),
        description: formDescription || null,
        agent_type: formType,
        backend_provider: formProvider,
      };

      if (formCapabilities.trim()) body.capabilities = parseJsonSafe(formCapabilities);
      if (formInputSchema.trim()) body.input_schema = parseJsonSafe(formInputSchema);
      if (formOutputSchema.trim()) body.output_schema = parseJsonSafe(formOutputSchema);

      if (!editingAgent) return;
      body.status = formStatus;
      await apiCall(API_ENDPOINTS.AGENT(editingAgent.id), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setShowModal(false);
      resetForm();
      fetchAgents();
    } catch (error) {
      console.error("Failed to save agent:", error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
          <p className="text-sm text-gray-500 mt-1">
            View and configure integrated AI agents attached to workflow tasks
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          title="Filter by type"
          className="h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Types</option>
          {AGENT_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          title="Filter by status"
          className="h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="deprecated">Deprecated</option>
        </select>
      </div>

      {/* Loading / Empty / Table */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
        </div>
      ) : agents.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-gray-200">
          <div className="w-16 h-16 mx-auto mb-4 bg-purple-50 rounded-full flex items-center justify-center">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
              <path d="M16 14H8a4 4 0 0 0-4 4v2h16v-2a4 4 0 0 0-4-4z" />
              <circle cx="19" cy="5" r="2" />
              <line x1="19" y1="8" x2="19" y2="11" />
              <line x1="17" y1="9.5" x2="21" y2="9.5" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">No agents available</h3>
          <p className="text-sm text-gray-500">Agents are seeded during system setup. Contact your administrator to integrate agents.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Agent</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Backend</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Created</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {agents.map((agent) => (
                <tr key={agent.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-4">
                    <button onClick={() => openDetail(agent)} className="text-left group">
                      <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors">{agent.name}</p>
                      {agent.description && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-1 max-w-xs">{agent.description}</p>
                      )}
                    </button>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${typeBadge(agent.agent_type)}`}>
                      {typeLabel(agent.agent_type)}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${providerBadge(agent.backend_provider)}`}>
                      {agent.backend_provider}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${statusBadge(agent.status)}`}>
                      {agent.status}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-xs text-gray-500">
                      {new Date(agent.created_at).toLocaleDateString()}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => openEditModal(agent)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 transition-colors rounded-lg hover:bg-blue-50"
                        title="Edit agent"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
                        </svg>
                      </button>

                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Modal */}
      {showDetail && detailAgent && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Agent Details</h2>
              <button onClick={() => setShowDetail(false)} className="text-gray-400 hover:text-gray-600" title="Close details">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase">Name</label>
                <p className="text-sm text-gray-900 mt-1">{detailAgent.name}</p>
              </div>
              {detailAgent.description && (
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase">Description</label>
                  <p className="text-sm text-gray-700 mt-1">{detailAgent.description}</p>
                </div>
              )}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase">Type</label>
                  <p className="mt-1">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${typeBadge(detailAgent.agent_type)}`}>
                      {typeLabel(detailAgent.agent_type)}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase">Backend</label>
                  <p className="mt-1">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${providerBadge(detailAgent.backend_provider)}`}>
                      {detailAgent.backend_provider}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase">Status</label>
                  <p className="mt-1">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${statusBadge(detailAgent.status)}`}>
                      {detailAgent.status}
                    </span>
                  </p>
                </div>
              </div>
              {detailAgent.capabilities && (
                <div>
                  <label className="text-xs font-semibold text-gray-500 uppercase">Capabilities</label>
                  <pre className="mt-1 text-xs bg-gray-50 p-3 rounded-lg overflow-auto max-h-40 text-gray-700">
                    {JSON.stringify(detailAgent.capabilities, null, 2)}
                  </pre>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
                <div>
                  <span className="font-semibold uppercase">Created</span>
                  <p className="mt-0.5 text-gray-700">{new Date(detailAgent.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <span className="font-semibold uppercase">Updated</span>
                  <p className="mt-0.5 text-gray-700">{new Date(detailAgent.updated_at).toLocaleString()}</p>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => { setShowDetail(false); openEditModal(detailAgent); }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
              >
                Edit
              </button>
              <button
                onClick={() => setShowDetail(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Edit Agent
              </h2>
              <button onClick={() => { setShowModal(false); resetForm(); }} className="text-gray-400 hover:text-gray-600" title="Close modal">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Name *</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. Document Intelligence Agent"
                  className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
                <textarea
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="What does this agent do?"
                  rows={3}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>
              {/* Type + Provider */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Agent Type</label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value)}
                    title="Agent type"
                    className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {AGENT_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Backend Provider</label>
                  <select
                    value={formProvider}
                    onChange={(e) => setFormProvider(e.target.value)}
                    title="Backend provider"
                    className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {BACKEND_PROVIDERS.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              {/* Status */}
              <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Status</label>
                  <select
                    value={formStatus}
                    onChange={(e) => setFormStatus(e.target.value)}
                    title="Agent status"
                    className="w-full h-10 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="deprecated">Deprecated</option>
                  </select>
              </div>
              {/* Capabilities JSON */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Capabilities (JSON, optional)</label>
                <textarea
                  value={formCapabilities}
                  onChange={(e) => setFormCapabilities(e.target.value)}
                  placeholder='{"supports_pdf": true, "supports_images": true}'
                  rows={3}
                  className="w-full px-3 py-2 text-xs font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => { setShowModal(false); resetForm(); }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !formName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? "Saving..." : "Update"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
