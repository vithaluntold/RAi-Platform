"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  status: string;
  lastActive: string;
}

interface BulkRow {
  name: string;
  email: string;
  role: string;
}

const ROLES = ["Compliance Officer", "Risk Analyst", "Auditor", "Admin", "Viewer"];

const initialUsers: User[] = [
  { id: 1, name: "Sarah Chen", email: "sarah.chen@technsure.com", role: "Compliance Officer", status: "Active", lastActive: "2 min ago" },
  { id: 2, name: "David Kim", email: "david.kim@technsure.com", role: "Risk Analyst", status: "Active", lastActive: "15 min ago" },
  { id: 3, name: "Lisa Park", email: "lisa.park@technsure.com", role: "Auditor", status: "Active", lastActive: "1 hour ago" },
  { id: 4, name: "Mark Wilson", email: "mark.wilson@technsure.com", role: "Admin", status: "Active", lastActive: "3 hours ago" },
  { id: 5, name: "Emily Johnson", email: "emily.j@technsure.com", role: "Compliance Officer", status: "Inactive", lastActive: "2 days ago" },
  { id: 6, name: "James Brown", email: "james.b@technsure.com", role: "Risk Analyst", status: "Active", lastActive: "5 hours ago" },
  { id: 7, name: "Anna Martinez", email: "anna.m@technsure.com", role: "Auditor", status: "Pending", lastActive: "Never" },
  { id: 8, name: "Robert Taylor", email: "robert.t@technsure.com", role: "Viewer", status: "Active", lastActive: "1 day ago" },
];

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>(initialUsers);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);

  // Add User form state
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newRole, setNewRole] = useState(ROLES[0]);

  // Bulk Add rows state
  const [bulkRows, setBulkRows] = useState<BulkRow[]>([{ name: "", email: "", role: ROLES[0] }]);
  const [bulkTab, setBulkTab] = useState<"manual" | "csv">("manual");

  // CSV upload state
  const [csvRows, setCsvRows] = useState<BulkRow[]>([]);
  const [csvFileName, setCsvFileName] = useState("");
  const [csvError, setCsvError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const nextId = () => Math.max(...users.map((u) => u.id), 0) + 1;

  const parseCSV = (text: string): BulkRow[] => {
    const lines = text.split(/\r?\n/).filter((l) => l.trim());
    if (lines.length === 0) return [];
    // detect header row
    const first = lines[0].toLowerCase();
    const startIdx = first.includes("name") || first.includes("email") ? 1 : 0;
    const rows: BulkRow[] = [];
    for (let i = startIdx; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c) => c.trim().replace(/^["']|["']$/g, ""));
      if (cols.length < 2) continue;
      const name = cols[0];
      const email = cols[1];
      const roleRaw = cols[2] || "";
      const matchedRole = ROLES.find((r) => r.toLowerCase() === roleRaw.toLowerCase()) || ROLES[0];
      if (name && email) rows.push({ name, email, role: matchedRole });
    }
    return rows;
  };

  const handleCSVFile = (file: File) => {
    setCsvError("");
    if (!file.name.endsWith(".csv")) {
      setCsvError("Please upload a .csv file");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const parsed = parseCSV(text);
      if (parsed.length === 0) {
        setCsvError("No valid rows found. Ensure your CSV has Name, Email columns.");
        return;
      }
      setCsvRows(parsed);
      setCsvFileName(file.name);
    };
    reader.readAsText(file);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleCSVFile(file);
  };

  const onFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleCSVFile(file);
    e.target.value = "";
  };

  const handleCsvUpload = () => {
    if (csvRows.length === 0) return;
    let id = nextId();
    const newUsers = csvRows.map((r) => ({
      id: id++,
      name: r.name,
      email: r.email,
      role: r.role,
      status: "Active",
      lastActive: "Just now",
    }));
    setUsers((prev) => [...prev, ...newUsers]);
    setCsvRows([]);
    setCsvFileName("");
    setCsvError("");
    setShowBulkModal(false);
  };

  const resetCsv = () => {
    setCsvRows([]);
    setCsvFileName("");
    setCsvError("");
  };

  const handleAddUser = () => {
    if (!newName.trim() || !newEmail.trim()) return;
    setUsers((prev) => [
      ...prev,
      { id: nextId(), name: newName.trim(), email: newEmail.trim(), role: newRole, status: "Active", lastActive: "Just now" },
    ]);
    setNewName("");
    setNewEmail("");
    setNewRole(ROLES[0]);
    setShowAddModal(false);
  };

  const handleBulkAdd = () => {
    const validRows = bulkRows.filter((r) => r.name.trim() && r.email.trim());
    if (validRows.length === 0) return;
    let id = nextId();
    const newUsers = validRows.map((r) => ({
      id: id++,
      name: r.name.trim(),
      email: r.email.trim(),
      role: r.role,
      status: "Active",
      lastActive: "Just now",
    }));
    setUsers((prev) => [...prev, ...newUsers]);
    setBulkRows([{ name: "", email: "", role: ROLES[0] }]);
    setShowBulkModal(false);
  };

  const updateBulkRow = (index: number, field: keyof BulkRow, value: string) => {
    setBulkRows((prev) => prev.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  };

  const addBulkRow = () => {
    setBulkRows((prev) => [...prev, { name: "", email: "", role: ROLES[0] }]);
  };

  const removeBulkRow = (index: number) => {
    setBulkRows((prev) => prev.filter((_, i) => i !== index));
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case "Active":
        return "bg-emerald-50 text-emerald-700";
      case "Inactive":
        return "bg-gray-100 text-gray-500";
      case "Pending":
        return "bg-amber-50 text-amber-700";
      default:
        return "bg-gray-100 text-gray-500";
    }
  };

  const getInitials = (name: string) =>
    name.split(" ").map((n) => n[0]).join("");

  const getAvatarColor = (name: string) => {
    const colors = [
      "bg-blue-100 text-blue-600",
      "bg-violet-100 text-violet-600",
      "bg-emerald-100 text-emerald-600",
      "bg-amber-100 text-amber-600",
      "bg-rose-100 text-rose-600",
      "bg-cyan-100 text-cyan-600",
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return colors[Math.abs(hash) % colors.length];
  };

  const inputClass = "w-full h-9 px-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none";
  const selectClass = "w-full h-9 px-3 text-sm bg-surface border border-border rounded-lg text-text-primary focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none";

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl text-text-primary font-semibold tracking-tight">Users</h1>
          <p className="text-sm text-text-secondary mt-1">Manage team members and their access</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBulkModal(true)}
            className="h-10 px-4 bg-surface hover:bg-surface-alt border border-border text-text-secondary text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <line x1="19" y1="8" x2="19" y2="14" />
              <line x1="22" y1="11" x2="16" y2="11" />
            </svg>
            Bulk Add Users
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="h-10 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add User
          </button>
        </div>
      </div>

      {/* Filters row */}
      <div className="flex items-center gap-3 mb-5 animate-fade-in-up stagger-1">
        <div className="relative flex-1 max-w-xs">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
            width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search users..."
            className="w-full h-9 pl-9 pr-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all"
          />
        </div>
        {["All", "Active", "Inactive", "Pending"].map((filter) => (
          <button
            key={filter}
            className={`h-9 px-3.5 text-sm rounded-lg border transition-colors ${
              filter === "All"
                ? "bg-accent/5 border-accent/20 text-accent font-medium"
                : "bg-surface border-border text-text-secondary hover:border-accent/30 hover:text-text-primary"
            }`}
          >
            {filter}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-surface rounded-xl border border-border overflow-hidden animate-fade-in-up stagger-2">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-light">
                <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">User</th>
                <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">Role</th>
                <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">Status</th>
                <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">Last Active</th>
                <th className="text-right text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-light">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-surface-alt/50 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${getAvatarColor(user.name)}`}>
                        {getInitials(user.name)}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-text-primary">{user.name}</p>
                        <p className="text-xs text-text-muted">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-sm text-text-secondary">{user.role}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(user.status)}`}>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-sm text-text-muted">{user.lastActive}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button title="More actions" className="w-8 h-8 inline-flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="1" />
                        <circle cx="19" cy="12" r="1" />
                        <circle cx="5" cy="12" r="1" />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Table footer */}
        <div className="px-5 py-3.5 border-t border-border-light flex items-center justify-between">
          <p className="text-xs text-text-muted">Showing {users.length} of 1,284 users</p>
          <div className="flex items-center gap-1">
            <button title="Previous page" className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </button>
            <button className="w-8 h-8 flex items-center justify-center rounded-lg bg-accent text-white text-xs font-medium">1</button>
            <button className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-alt text-xs transition-colors">2</button>
            <button className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-alt text-xs transition-colors">3</button>
            <button title="Next page" className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowAddModal(false)}>
          <div className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-md p-6 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-text-primary">Add User</h2>
              <button onClick={() => setShowAddModal(false)} title="Close" className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. John Doe"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Email</label>
                <input
                  type="email"
                  placeholder="e.g. john.doe@technsure.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Role</label>
                <select value={newRole} onChange={(e) => setNewRole(e.target.value)} title="Role" className={selectClass}>
                  {ROLES.map((role) => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowAddModal(false)} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">
                Cancel
              </button>
              <button onClick={handleAddUser} className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors">
                Add User
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Add Users Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowBulkModal(false)}>
          <div className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-2xl p-6 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-text-primary">Bulk Add Users</h2>
              <button onClick={() => setShowBulkModal(false)} title="Close" className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {/* Tabs */}
            <div className="flex rounded-lg bg-surface-alt/70 p-0.5 mb-5">
              <button
                onClick={() => setBulkTab("manual")}
                className={`flex-1 py-2 text-xs font-medium rounded-md transition-colors flex items-center justify-center gap-1.5 ${
                  bulkTab === "manual" ? "bg-surface text-text-primary shadow-sm" : "text-text-muted hover:text-text-secondary"
                }`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                Manual Entry
              </button>
              <button
                onClick={() => setBulkTab("csv")}
                className={`flex-1 py-2 text-xs font-medium rounded-md transition-colors flex items-center justify-center gap-1.5 ${
                  bulkTab === "csv" ? "bg-surface text-text-primary shadow-sm" : "text-text-muted hover:text-text-secondary"
                }`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                CSV Upload
              </button>
            </div>

            {/* Manual Entry Tab */}
            {bulkTab === "manual" && (
              <>
                {/* Column headers */}
                <div className="grid grid-cols-[1fr_1fr_1fr_40px] gap-3 mb-2">
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Name</span>
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Email</span>
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Role</span>
                  <span />
                </div>

                {/* Dynamic rows */}
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {bulkRows.map((row, index) => (
                    <div key={index} className="grid grid-cols-[1fr_1fr_1fr_40px] gap-3 items-center">
                      <input
                        type="text"
                        placeholder="Full name"
                        value={row.name}
                        onChange={(e) => updateBulkRow(index, "name", e.target.value)}
                        className={inputClass}
                      />
                      <input
                        type="email"
                        placeholder="Email"
                        value={row.email}
                        onChange={(e) => updateBulkRow(index, "email", e.target.value)}
                        className={inputClass}
                      />
                      <select
                        value={row.role}
                        onChange={(e) => updateBulkRow(index, "role", e.target.value)}
                        title="Role"
                        className={selectClass}
                      >
                        {ROLES.map((role) => (
                          <option key={role} value={role}>{role}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => removeBulkRow(index)}
                        disabled={bulkRows.length === 1}
                        title="Remove row"
                        className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-rose-500 hover:bg-rose-50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:text-text-muted disabled:hover:bg-transparent"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>

                {/* Add Row button */}
                <button
                  onClick={addBulkRow}
                  className="mt-3 h-8 px-3 text-sm text-accent hover:text-accent-light font-medium flex items-center gap-1.5 transition-colors"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  Add Row
                </button>

                <div className="flex justify-end gap-2 mt-5 pt-4 border-t border-border-light">
                  <button onClick={() => setShowBulkModal(false)} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">
                    Cancel
                  </button>
                  <button onClick={handleBulkAdd} className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors">
                    Add All Users
                  </button>
                </div>
              </>
            )}

            {/* CSV Upload Tab */}
            {bulkTab === "csv" && (
              <>
                {csvRows.length === 0 ? (
                  <>
                    {/* Drop zone */}
                    <div
                      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                      onDragLeave={() => setIsDragging(false)}
                      onDrop={onDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                        isDragging
                          ? "border-accent bg-accent/5"
                          : "border-border hover:border-accent/30 hover:bg-surface-alt/30"
                      }`}
                    >
                      <input ref={fileInputRef} type="file" accept=".csv" onChange={onFileSelect} title="Upload CSV" className="hidden" />
                      <svg className="mx-auto mb-3 text-text-muted" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                      <p className="text-sm font-medium text-text-primary mb-1">
                        {isDragging ? "Drop your file here" : "Drag & drop a CSV file here"}
                      </p>
                      <p className="text-xs text-text-muted mb-3">or click to browse</p>
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-alt text-xs text-text-muted">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="16" x2="12" y2="12" />
                          <line x1="12" y1="8" x2="12.01" y2="8" />
                        </svg>
                        Format: Name, Email, Role (header row optional)
                      </span>
                    </div>

                    {csvError && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-rose-500">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="15" y1="9" x2="9" y2="15" />
                          <line x1="9" y1="9" x2="15" y2="15" />
                        </svg>
                        {csvError}
                      </div>
                    )}

                    <div className="flex justify-end gap-2 mt-5 pt-4 border-t border-border-light">
                      <button onClick={() => setShowBulkModal(false)} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">
                        Cancel
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    {/* File info + clear */}
                    <div className="flex items-center justify-between mb-4 px-3 py-2.5 bg-surface-alt/50 rounded-lg">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-text-primary">{csvFileName}</p>
                          <p className="text-xs text-text-muted">{csvRows.length} user{csvRows.length !== 1 ? "s" : ""} found</p>
                        </div>
                      </div>
                      <button onClick={resetCsv} className="text-xs text-text-muted hover:text-rose-500 font-medium transition-colors">
                        Remove
                      </button>
                    </div>

                    {/* Preview table */}
                    <div className="border border-border rounded-lg overflow-hidden mb-1">
                      <div className="grid grid-cols-[1fr_1fr_1fr] gap-0 text-xs font-semibold text-text-muted uppercase tracking-wider bg-surface-alt/50">
                        <span className="px-3 py-2.5">Name</span>
                        <span className="px-3 py-2.5">Email</span>
                        <span className="px-3 py-2.5">Role</span>
                      </div>
                      <div className="max-h-56 overflow-y-auto divide-y divide-border-light">
                        {csvRows.map((row, i) => (
                          <div key={i} className="grid grid-cols-[1fr_1fr_1fr] gap-0 text-sm">
                            <span className="px-3 py-2.5 text-text-primary truncate">{row.name}</span>
                            <span className="px-3 py-2.5 text-text-muted truncate">{row.email}</span>
                            <span className="px-3 py-2.5 text-text-secondary truncate">{row.role}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <p className="text-[11px] text-text-muted mb-4">
                      {csvRows.length > 10 ? `Showing all ${csvRows.length} rows. ` : ""}Unmatched roles default to {ROLES[0]}.
                    </p>

                    <div className="flex justify-end gap-2 pt-4 border-t border-border-light">
                      <button onClick={() => { resetCsv(); }} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">
                        Back
                      </button>
                      <button onClick={handleCsvUpload} className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors">
                        Import {csvRows.length} User{csvRows.length !== 1 ? "s" : ""}
                      </button>
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
