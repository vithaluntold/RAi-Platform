"use client";

import { useState } from "react";

type PermissionAction = "view" | "create" | "edit" | "delete" | "manage";

interface ModulePermission {
  module: string;
  view: boolean;
  create: boolean;
  edit: boolean;
  delete: boolean;
  manage: boolean;
}

interface Role {
  id: string;
  name: string;
  description: string;
  type: "system" | "custom";
  permissions: ModulePermission[];
}

const MODULES = [
  "Dashboard",
  "Users",
  "Documents",
  "Workflows",
  "AI Models",
  "Risk Assessments",
  "Compliance",
  "Audit Logs",
  "Reports",
  "Analytics",
  "Notifications",
  "Settings",
  "Billing",
  "API Access",
];

const ACTIONS: { key: PermissionAction; label: string }[] = [
  { key: "view", label: "View" },
  { key: "create", label: "Create" },
  { key: "edit", label: "Edit" },
  { key: "delete", label: "Delete" },
  { key: "manage", label: "Manage" },
];

function makePerms(overrides: Record<string, PermissionAction[]>): ModulePermission[] {
  return MODULES.map((mod) => {
    const actions = overrides[mod] || [];
    return {
      module: mod,
      view: actions.includes("view"),
      create: actions.includes("create"),
      edit: actions.includes("edit"),
      delete: actions.includes("delete"),
      manage: actions.includes("manage"),
    };
  });
}

const initialRoles: Role[] = [
  {
    id: "super-admin",
    name: "Super Admin",
    description: "Full system access with all permissions",
    type: "system",
    permissions: makePerms(
      Object.fromEntries(MODULES.map((m) => [m, ["view", "create", "edit", "delete", "manage"] as PermissionAction[]]))
    ),
  },
  {
    id: "compliance-officer",
    name: "Compliance Officer",
    description: "Manages compliance policies, audits, and regulatory reports",
    type: "system",
    permissions: makePerms({
      Dashboard: ["view"],
      Users: ["view"],
      Documents: ["view", "create", "edit"],
      Workflows: ["view", "create", "edit"],
      "AI Models": ["view"],
      "Risk Assessments": ["view", "create", "edit", "delete"],
      Compliance: ["view", "create", "edit", "delete", "manage"],
      "Audit Logs": ["view"],
      Reports: ["view", "create"],
      Analytics: ["view"],
      Notifications: ["view", "manage"],
      Settings: ["view"],
      Billing: [],
      "API Access": ["view"],
    }),
  },
  {
    id: "risk-analyst",
    name: "Risk Analyst",
    description: "Analyzes AI model risks and generates risk reports",
    type: "system",
    permissions: makePerms({
      Dashboard: ["view"],
      Users: ["view"],
      Documents: ["view", "create"],
      Workflows: ["view"],
      "AI Models": ["view", "create", "edit"],
      "Risk Assessments": ["view", "create", "edit", "manage"],
      Compliance: ["view"],
      "Audit Logs": ["view"],
      Reports: ["view", "create", "edit"],
      Analytics: ["view", "create"],
      Notifications: ["view"],
      Settings: [],
      Billing: [],
      "API Access": ["view"],
    }),
  },
  {
    id: "auditor",
    name: "Auditor",
    description: "Read-only access for auditing and review purposes",
    type: "system",
    permissions: makePerms({
      Dashboard: ["view"],
      Users: ["view"],
      Documents: ["view"],
      Workflows: ["view"],
      "AI Models": ["view"],
      "Risk Assessments": ["view"],
      Compliance: ["view"],
      "Audit Logs": ["view", "manage"],
      Reports: ["view"],
      Analytics: ["view"],
      Notifications: ["view"],
      Settings: [],
      Billing: [],
      "API Access": [],
    }),
  },
  {
    id: "viewer",
    name: "Viewer",
    description: "Basic read-only access to dashboards and reports",
    type: "system",
    permissions: makePerms({
      Dashboard: ["view"],
      Users: [],
      Documents: ["view"],
      Workflows: ["view"],
      "AI Models": [],
      "Risk Assessments": ["view"],
      Compliance: [],
      "Audit Logs": [],
      Reports: ["view"],
      Analytics: ["view"],
      Notifications: ["view"],
      Settings: [],
      Billing: [],
      "API Access": [],
    }),
  },
];

function getPermissionStatus(perm: ModulePermission): { label: string; color: string } {
  const count = [perm.view, perm.create, perm.edit, perm.delete, perm.manage].filter(Boolean).length;
  if (count === 5) return { label: "Full", color: "text-emerald-500" };
  if (count === 0) return { label: "None", color: "text-text-muted" };
  return { label: "Partial", color: "text-amber-500" };
}

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>(initialRoles);
  const [selectedRoleId, setSelectedRoleId] = useState(initialRoles[0].id);
  const [activeTab, setActiveTab] = useState<"system" | "custom">("system");
  const [showAddRole, setShowAddRole] = useState(false);
  const [newRoleName, setNewRoleName] = useState("");
  const [newRoleDesc, setNewRoleDesc] = useState("");

  const selectedRole = roles.find((r) => r.id === selectedRoleId)!;
  const filteredRoles = roles.filter((r) => r.type === activeTab);

  const togglePermission = (moduleIndex: number, action: PermissionAction) => {
    if (selectedRole.type === "system") return;
    setRoles((prev) =>
      prev.map((role) => {
        if (role.id !== selectedRoleId) return role;
        const updated = [...role.permissions];
        updated[moduleIndex] = { ...updated[moduleIndex], [action]: !updated[moduleIndex][action] };
        return { ...role, permissions: updated };
      })
    );
  };

  const handleAddRole = () => {
    if (!newRoleName.trim()) return;
    const id = newRoleName.trim().toLowerCase().replace(/\s+/g, "-");
    const newRole: Role = {
      id,
      name: newRoleName.trim(),
      description: newRoleDesc.trim() || "Custom role",
      type: "custom",
      permissions: MODULES.map((mod) => ({
        module: mod,
        view: false,
        create: false,
        edit: false,
        delete: false,
        manage: false,
      })),
    };
    setRoles((prev) => [...prev, newRole]);
    setActiveTab("custom");
    setSelectedRoleId(id);
    setNewRoleName("");
    setNewRoleDesc("");
    setShowAddRole(false);
  };

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl text-text-primary font-semibold tracking-tight">Roles & Permissions</h1>
          <p className="text-sm text-text-secondary mt-1">Manage roles and configure module-level access</p>
        </div>
        <button
          onClick={() => setShowAddRole(true)}
          className="h-10 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Custom Role
        </button>
      </div>

      {/* Two-column layout */}
      <div className="flex gap-6 animate-fade-in-up stagger-1">
        {/* Left panel — Role list */}
        <div className="w-72 flex-shrink-0">
          <div className="bg-surface rounded-xl border border-border overflow-hidden">
            <div className="px-5 pt-5 pb-4">
              <h2 className="text-sm font-semibold text-text-primary">Roles</h2>
              <p className="text-xs text-text-muted mt-0.5">Select a role to manage permissions</p>
            </div>

            {/* System / Custom tabs */}
            <div className="mx-4 mb-3 flex rounded-lg bg-surface-alt/70 p-0.5">
              {(["system", "custom"] as const).map((tab) => {
                const count = roles.filter((r) => r.type === tab).length;
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 py-2 text-xs font-medium rounded-md transition-colors capitalize ${
                      activeTab === tab
                        ? "bg-surface text-text-primary shadow-sm"
                        : "text-text-muted hover:text-text-secondary"
                    }`}
                  >
                    {tab} ({count})
                  </button>
                );
              })}
            </div>

            {/* Role list */}
            <div className="px-3 pb-3 space-y-0.5 max-h-[calc(100vh-340px)] overflow-y-auto">
              {filteredRoles.length === 0 && (
                <p className="text-xs text-text-muted text-center py-6">No {activeTab} roles yet</p>
              )}
              {filteredRoles.map((role) => (
                <button
                  key={role.id}
                  onClick={() => setSelectedRoleId(role.id)}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-all ${
                    selectedRoleId === role.id
                      ? "bg-accent/10 border border-accent/20"
                      : "hover:bg-surface-alt border border-transparent"
                  }`}
                >
                  {/* Radio indicator */}
                  <span
                    className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                      selectedRoleId === role.id ? "border-accent" : "border-border"
                    }`}
                  >
                    {selectedRoleId === role.id && <span className="w-2 h-2 rounded-full bg-accent" />}
                  </span>
                  <div className="min-w-0">
                    <p className={`text-sm font-medium truncate ${selectedRoleId === role.id ? "text-accent" : "text-text-primary"}`}>
                      {role.name}
                    </p>
                    <span className={`inline-block mt-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded capitalize ${
                      role.type === "system"
                        ? "bg-blue-50 text-blue-600"
                        : "bg-violet-50 text-violet-600"
                    }`}>
                      {role.type}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right panel — Permissions matrix */}
        <div className="flex-1 min-w-0">
          <div className="bg-surface rounded-xl border border-border overflow-hidden animate-fade-in-up stagger-2">
            {/* Header */}
            <div className="px-6 py-5 border-b border-border-light flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-text-primary">{selectedRole.name} Permissions</h2>
                <p className="text-sm text-text-muted mt-0.5">{selectedRole.description}</p>
              </div>
              <span className={`flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                selectedRole.type === "system"
                  ? "bg-blue-50 text-blue-600 border-blue-100"
                  : "bg-violet-50 text-violet-600 border-violet-100"
              }`}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                {selectedRole.type === "system" ? "System Role (Read Only)" : "Custom Role (Editable)"}
              </span>
            </div>

            {/* Permissions table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border-light">
                    <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-6 py-3.5 w-56">
                      Module / Resource
                    </th>
                    {ACTIONS.map((a) => (
                      <th key={a.key} className="text-center text-xs font-semibold text-text-muted uppercase tracking-wider px-4 py-3.5 w-24">
                        {a.label}
                      </th>
                    ))}
                    <th className="text-right text-xs font-semibold text-text-muted uppercase tracking-wider px-6 py-3.5 w-24">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-light">
                  {selectedRole.permissions.map((perm, idx) => {
                    const status = getPermissionStatus(perm);
                    return (
                      <tr key={perm.module} className="hover:bg-surface-alt/50 transition-colors">
                        <td className="px-6 py-4">
                          <span className="text-sm font-medium text-text-primary">{perm.module}</span>
                        </td>
                        {ACTIONS.map((a) => (
                          <td key={a.key} className="px-4 py-4 text-center">
                            <label className="inline-flex items-center justify-center">
                              <input
                                type="checkbox"
                                checked={perm[a.key]}
                                onChange={() => togglePermission(idx, a.key)}
                                disabled={selectedRole.type === "system"}
                                className="sr-only peer"
                              />
                              <span
                                className={`w-5 h-5 rounded flex items-center justify-center border transition-all ${
                                  perm[a.key]
                                    ? "bg-accent border-accent text-white"
                                    : "border-border bg-surface"
                                } ${
                                  selectedRole.type === "custom"
                                    ? "cursor-pointer peer-focus-visible:ring-2 peer-focus-visible:ring-accent/30"
                                    : "cursor-default opacity-90"
                                }`}
                              >
                                {perm[a.key] && (
                                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="20 6 9 17 4 12" />
                                  </svg>
                                )}
                              </span>
                            </label>
                          </td>
                        ))}
                        <td className="px-6 py-4 text-right">
                          <span className={`inline-flex items-center gap-1 text-xs font-medium ${status.color}`}>
                            {status.label === "Full" && (
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12" />
                              </svg>
                            )}
                            {status.label === "Partial" && (
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="5" y1="12" x2="19" y2="12" />
                              </svg>
                            )}
                            {status.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Add Custom Role Modal */}
      {showAddRole && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowAddRole(false)}>
          <div className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-md p-6 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-text-primary">Add Custom Role</h2>
              <button onClick={() => setShowAddRole(false)} className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Role Name</label>
                <input
                  type="text"
                  placeholder="e.g. Content Reviewer"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  className="w-full h-9 px-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Description</label>
                <input
                  type="text"
                  placeholder="Brief description of this role"
                  value={newRoleDesc}
                  onChange={(e) => setNewRoleDesc(e.target.value)}
                  className="w-full h-9 px-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none"
                />
              </div>
            </div>

            <p className="text-xs text-text-muted mt-3">You can configure permissions after creating the role.</p>

            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShowAddRole(false)} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">
                Cancel
              </button>
              <button onClick={handleAddRole} className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors">
                Create Role
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
