"use client";

import { useState, useEffect, useCallback, useRef, DragEvent, ChangeEvent } from "react";
import { apiCall, getAuthToken, API_BASE_URL } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

/* ─── Types ──────────────────────────────────────────────────────────── */

interface UserItem {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  auth_provider: string | null;
  ad_username: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface UserListResponse {
  users: UserItem[];
  total: number;
  page: number;
  per_page: number;
}

interface BulkRow {
  name: string;
  email: string;
  role: string;
}

/* ─── Constants ──────────────────────────────────────────────────────── */

const ROLES = ["admin", "manager", "enduser", "client"];
const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  manager: "Manager",
  enduser: "End User",
  client: "Client",
};
const PER_PAGE = 20;

/* ─── Helpers ────────────────────────────────────────────────────────── */

function roleLabel(role: string): string {
  return ROLE_LABELS[role.toLowerCase()] || role;
}

function getInitials(first: string, last: string): string {
  return `${(first || "")[0] || ""}${(last || "")[0] || ""}`.toUpperCase();
}

function getAvatarColor(name: string): string {
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
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? "s" : ""} ago`;
}

/* ─── Shared classes ─────────────────────────────────────────────────── */

const inputClass =
  "w-full h-9 px-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none";
const selectClass =
  "w-full h-9 px-3 text-sm bg-surface border border-border rounded-lg text-text-primary focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none";

/* ─── Component ──────────────────────────────────────────────────────── */

export default function UsersPage() {
  /* ── State ── */
  const [users, setUsers] = useState<UserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [roleFilter, setRoleFilter] = useState("");

  // Add user modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newFirstName, setNewFirstName] = useState("");
  const [newLastName, setNewLastName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("enduser");
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState("");

  // Edit user modal
  const [editUser, setEditUser] = useState<UserItem | null>(null);
  const [editFirstName, setEditFirstName] = useState("");
  const [editLastName, setEditLastName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editRole, setEditRole] = useState("");
  const [editActive, setEditActive] = useState(true);
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState("");

  // Delete confirmation
  const [deleteUser, setDeleteUser] = useState<UserItem | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Bulk add modal
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkTab, setBulkTab] = useState<"manual" | "csv">("manual");
  const [bulkRows, setBulkRows] = useState<BulkRow[]>([{ name: "", email: "", role: "enduser" }]);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkError, setBulkError] = useState("");
  const [csvRows, setCsvRows] = useState<BulkRow[]>([]);
  const [csvFileName, setCsvFileName] = useState("");
  const [csvError, setCsvError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Actions menu
  const [openActionId, setOpenActionId] = useState<string | null>(null);

  // Debounce timer
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /* ── Fetch users ── */
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", String(PER_PAGE));
      if (search.trim()) params.set("search", search.trim());
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (roleFilter) params.set("role", roleFilter);

      const data = await apiCall<UserListResponse>(
        `${API_ENDPOINTS.USERS}?${params.toString()}`
      );
      setUsers(data.users);
      setTotal(data.total);
    } catch {
      setUsers([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter, roleFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  /* ── Debounced search ── */
  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      setPage(1);
    }, 300);
  };

  /* ── Add single user ── */
  const handleAddUser = async () => {
    if (!newFirstName.trim() || !newEmail.trim() || !newPassword.trim()) return;
    setAddLoading(true);
    setAddError("");
    try {
      await apiCall(API_ENDPOINTS.USER_ONBOARD, {
        method: "POST",
        body: JSON.stringify({
          first_name: newFirstName.trim(),
          last_name: newLastName.trim(),
          email: newEmail.trim(),
          password: newPassword.trim(),
          role: newRole,
        }),
      });
      setShowAddModal(false);
      setNewFirstName("");
      setNewLastName("");
      setNewEmail("");
      setNewPassword("");
      setNewRole("enduser");
      fetchUsers();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to add user");
    } finally {
      setAddLoading(false);
    }
  };

  /* ── Edit user ── */
  const openEdit = (user: UserItem) => {
    setEditUser(user);
    setEditFirstName(user.first_name);
    setEditLastName(user.last_name);
    setEditEmail(user.email);
    setEditRole(user.role);
    setEditActive(user.is_active);
    setEditError("");
    setOpenActionId(null);
  };

  const handleEditSave = async () => {
    if (!editUser) return;
    setEditLoading(true);
    setEditError("");
    try {
      await apiCall(API_ENDPOINTS.USER(editUser.id), {
        method: "PATCH",
        body: JSON.stringify({
          first_name: editFirstName.trim(),
          last_name: editLastName.trim(),
          email: editEmail.trim(),
          role: editRole,
          is_active: editActive,
        }),
      });
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Failed to update user");
    } finally {
      setEditLoading(false);
    }
  };

  /* ── Delete user ── */
  const handleDelete = async () => {
    if (!deleteUser) return;
    setDeleteLoading(true);
    try {
      await apiCall(API_ENDPOINTS.USER(deleteUser.id), { method: "DELETE" });
      setDeleteUser(null);
      fetchUsers();
    } catch {
      /* silently handle */
    } finally {
      setDeleteLoading(false);
    }
  };

  /* ── Bulk add (manual) ── */
  const handleBulkAdd = async () => {
    const validRows = bulkRows.filter((r) => r.name.trim() && r.email.trim());
    if (validRows.length === 0) return;
    setBulkLoading(true);
    setBulkError("");
    try {
      for (const row of validRows) {
        const parts = row.name.trim().split(" ", 2);
        await apiCall(API_ENDPOINTS.USER_ONBOARD, {
          method: "POST",
          body: JSON.stringify({
            first_name: parts[0],
            last_name: parts[1] || "",
            email: row.email.trim(),
            password: "Welcome@123",
            role: row.role,
          }),
        });
      }
      setShowBulkModal(false);
      setBulkRows([{ name: "", email: "", role: "enduser" }]);
      fetchUsers();
    } catch (err) {
      setBulkError(err instanceof Error ? err.message : "Some users failed to add");
    } finally {
      setBulkLoading(false);
    }
  };

  /* ── CSV parsing ── */
  const parseCSV = (text: string): BulkRow[] => {
    const lines = text.split(/\r?\n/).filter((l) => l.trim());
    if (lines.length === 0) return [];
    const first = lines[0].toLowerCase();
    const startIdx = first.includes("name") || first.includes("email") ? 1 : 0;
    const rows: BulkRow[] = [];
    for (let i = startIdx; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c) => c.trim().replace(/^["']|["']$/g, ""));
      if (cols.length < 2) continue;
      const name = cols[0];
      const email = cols[1];
      const roleRaw = cols[2] || "";
      const matchedRole =
        ROLES.find((r) => r.toLowerCase() === roleRaw.toLowerCase()) || "enduser";
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

  const handleCsvUpload = async () => {
    if (csvRows.length === 0) return;
    setBulkLoading(true);
    setBulkError("");
    try {
      const csvContent = [
        "first_name,last_name,email,password,role",
        ...csvRows.map((r) => {
          const parts = r.name.split(" ", 2);
          return `${parts[0]},${parts[1] || ""},${r.email},Welcome@123,${r.role}`;
        }),
      ].join("\n");

      const blob = new Blob([csvContent], { type: "text/csv" });
      const formData = new FormData();
      formData.append("file", blob, "bulk_users.csv");

      const token = getAuthToken();
      const resp = await fetch(`${API_BASE_URL}${API_ENDPOINTS.USER_ONBOARD_BULK}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!resp.ok) {
        throw new Error(`Upload failed: ${resp.status}`);
      }

      setShowBulkModal(false);
      setCsvRows([]);
      setCsvFileName("");
      fetchUsers();
    } catch (err) {
      setBulkError(err instanceof Error ? err.message : "CSV upload failed");
    } finally {
      setBulkLoading(false);
    }
  };

  const resetCsv = () => {
    setCsvRows([]);
    setCsvFileName("");
    setCsvError("");
  };

  const updateBulkRow = (index: number, field: keyof BulkRow, value: string) => {
    setBulkRows((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    );
  };
  const addBulkRow = () =>
    setBulkRows((prev) => [...prev, { name: "", email: "", role: "enduser" }]);
  const removeBulkRow = (index: number) =>
    setBulkRows((prev) => prev.filter((_, i) => i !== index));

  /* ── Pagination ── */
  const totalPages = Math.ceil(total / PER_PAGE) || 1;
  const pageNumbers = (): number[] => {
    const pages: number[] = [];
    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, start + 4);
    for (let i = start; i <= end; i++) pages.push(i);
    return pages;
  };

  /* ── Status helpers ── */
  const getStatusStyle = (active: boolean) =>
    active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500";
  const getStatusLabel = (active: boolean) => (active ? "Active" : "Inactive");

  /* ── Close action menus on outside click ── */
  useEffect(() => {
    const handler = () => setOpenActionId(null);
    if (openActionId) document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [openActionId]);

  /* ── Render ── */
  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl text-text-primary font-semibold tracking-tight">
            Users
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage team members and their access
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBulkModal(true)}
            className="h-10 px-4 bg-surface hover:bg-surface-alt border border-border text-text-secondary text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <line x1="19" y1="8" x2="19" y2="14" />
              <line x1="22" y1="11" x2="16" y2="11" />
            </svg>
            Bulk Add Users
          </button>
          <button
            onClick={() => {
              setShowAddModal(true);
              setAddError("");
            }}
            className="h-10 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
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
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search users..."
            aria-label="Search users"
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full h-9 pl-9 pr-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all"
          />
        </div>
        {(["all", "active", "inactive"] as const).map((f) => (
          <button
            key={f}
            onClick={() => {
              setStatusFilter(f);
              setPage(1);
            }}
            className={`h-9 px-3.5 text-sm rounded-lg border transition-colors ${
              statusFilter === f
                ? "bg-accent/5 border-accent/20 text-accent font-medium"
                : "bg-surface border-border text-text-secondary hover:border-accent/30 hover:text-text-primary"
            }`}
          >
            {f === "all" ? "All" : f === "active" ? "Active" : "Inactive"}
          </button>
        ))}
        <select
          aria-label="Filter by role"
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(1);
          }}
          className="h-9 px-3 text-sm bg-surface border border-border rounded-lg text-text-secondary focus:border-accent focus:ring-2 focus:ring-accent/10 transition-all outline-none"
        >
          <option value="">All Roles</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {roleLabel(r)}
            </option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-accent/20 border-t-accent rounded-full animate-spin" />
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-20 text-text-muted">
          <p className="text-lg font-medium mb-1">No users found</p>
          <p className="text-sm">Try adjusting your search or filters</p>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="bg-surface rounded-xl border border-border overflow-hidden animate-fade-in-up stagger-2">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border-light">
                    <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">
                      User
                    </th>
                    <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">
                      Role
                    </th>
                    <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">
                      Status
                    </th>
                    <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">
                      Last Active
                    </th>
                    <th className="text-right text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3.5">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-light">
                  {users.map((user) => {
                    const fullName =
                      `${user.first_name} ${user.last_name}`.trim();
                    return (
                      <tr
                        key={user.id}
                        className="hover:bg-surface-alt/50 transition-colors"
                      >
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-3">
                            <div
                              className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${getAvatarColor(fullName)}`}
                            >
                              {getInitials(user.first_name, user.last_name)}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-text-primary">
                                {fullName}
                              </p>
                              <p className="text-xs text-text-muted">
                                {user.email}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="text-sm text-text-secondary">
                            {roleLabel(user.role)}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(user.is_active)}`}
                          >
                            {getStatusLabel(user.is_active)}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="text-sm text-text-muted">
                            {timeAgo(user.updated_at)}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right relative">
                          <button
                            title="More actions"
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenActionId(
                                openActionId === user.id ? null : user.id
                              );
                            }}
                            className="w-8 h-8 inline-flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors"
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <circle cx="12" cy="12" r="1" />
                              <circle cx="19" cy="12" r="1" />
                              <circle cx="5" cy="12" r="1" />
                            </svg>
                          </button>
                          {openActionId === user.id && (
                            <div className="absolute right-5 top-12 bg-surface border border-border rounded-lg shadow-lg z-10 w-36 py-1">
                              <button
                                onClick={() => openEdit(user)}
                                className="w-full text-left px-3 py-2 text-sm text-text-primary hover:bg-surface-alt transition-colors"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => {
                                  setDeleteUser(user);
                                  setOpenActionId(null);
                                }}
                                className="w-full text-left px-3 py-2 text-sm text-rose-600 hover:bg-rose-50 transition-colors"
                              >
                                Delete
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Table footer */}
            <div className="px-5 py-3.5 border-t border-border-light flex items-center justify-between">
              <p className="text-xs text-text-muted">
                Showing {(page - 1) * PER_PAGE + 1}
                &ndash;{Math.min(page * PER_PAGE, total)} of {total} users
              </p>
              <div className="flex items-center gap-1">
                <button
                  aria-label="Previous page"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors disabled:opacity-30"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                </button>
                {pageNumbers().map((p) => (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs font-medium transition-colors ${
                      p === page
                        ? "bg-accent text-white"
                        : "text-text-secondary hover:bg-surface-alt"
                    }`}
                  >
                    {p}
                  </button>
                ))}
                <button
                  aria-label="Next page"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors disabled:opacity-30"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ══ Add User Modal ══ */}
      {showAddModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={() => setShowAddModal(false)}
        >
          <div
            className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-md p-6 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-text-primary">
                Add User
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                title="Close"
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {addError && (
              <p className="text-sm text-rose-500 mb-3">{addError}</p>
            )}

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1.5">
                    First Name
                  </label>
                  <input
                    type="text"
                    placeholder="John"
                    value={newFirstName}
                    onChange={(e) => setNewFirstName(e.target.value)}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1.5">
                    Last Name
                  </label>
                  <input
                    type="text"
                    placeholder="Doe"
                    value={newLastName}
                    onChange={(e) => setNewLastName(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  placeholder="john@company.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  placeholder="Min 8 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">
                  Role
                </label>
                <select
                  aria-label="Select role"
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className={selectClass}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {roleLabel(r)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddUser}
                disabled={addLoading}
                className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors disabled:opacity-50"
              >
                {addLoading ? "Adding..." : "Add User"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ══ Edit User Modal ══ */}
      {editUser && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={() => setEditUser(null)}
        >
          <div
            className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-md p-6 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-text-primary">
                Edit User
              </h2>
              <button
                onClick={() => setEditUser(null)}
                title="Close"
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {editError && (
              <p className="text-sm text-rose-500 mb-3">{editError}</p>
            )}

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1.5">
                    First Name
                  </label>
                  <input
                    type="text"
                    placeholder="First name"
                    value={editFirstName}
                    onChange={(e) => setEditFirstName(e.target.value)}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1.5">
                    Last Name
                  </label>
                  <input
                    type="text"
                    placeholder="Last name"
                    value={editLastName}
                    onChange={(e) => setEditLastName(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  placeholder="email@company.com"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">
                  Role
                </label>
                <select
                  aria-label="Select role"
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value)}
                  className={selectClass}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {roleLabel(r)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium text-text-secondary">
                  Active
                </label>
                <button
                  type="button"
                  onClick={() => setEditActive(!editActive)}
                  className={`relative w-10 h-5 rounded-full transition-colors ${
                    editActive ? "bg-accent" : "bg-gray-300"
                  }`}
                  aria-label="Toggle active status"
                >
                  <span
                    className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                      editActive ? "left-5.5" : "left-0.5"
                    }`}
                  />
                </button>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setEditUser(null)}
                className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleEditSave}
                disabled={editLoading}
                className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors disabled:opacity-50"
              >
                {editLoading ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ══ Delete Confirmation ══ */}
      {deleteUser && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={() => setDeleteUser(null)}
        >
          <div
            className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-sm p-6 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold text-text-primary mb-2">
              Delete User
            </h2>
            <p className="text-sm text-text-secondary mb-5">
              Are you sure you want to delete{" "}
              <strong>
                {deleteUser.first_name} {deleteUser.last_name}
              </strong>{" "}
              ({deleteUser.email})? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteUser(null)}
                className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteLoading}
                className="h-9 px-4 text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {deleteLoading ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ══ Bulk Add Users Modal ══ */}
      {showBulkModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={() => setShowBulkModal(false)}
        >
          <div
            className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-2xl p-6 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-text-primary">
                Bulk Add Users
              </h2>
              <button
                onClick={() => setShowBulkModal(false)}
                title="Close"
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {bulkError && (
              <p className="text-sm text-rose-500 mb-3">{bulkError}</p>
            )}

            {/* Tabs */}
            <div className="flex rounded-lg bg-surface-alt/70 p-0.5 mb-5">
              <button
                onClick={() => setBulkTab("manual")}
                className={`flex-1 py-2 text-xs font-medium rounded-md transition-colors flex items-center justify-center gap-1.5 ${
                  bulkTab === "manual"
                    ? "bg-surface text-text-primary shadow-sm"
                    : "text-text-muted hover:text-text-secondary"
                }`}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                Manual Entry
              </button>
              <button
                onClick={() => setBulkTab("csv")}
                className={`flex-1 py-2 text-xs font-medium rounded-md transition-colors flex items-center justify-center gap-1.5 ${
                  bulkTab === "csv"
                    ? "bg-surface text-text-primary shadow-sm"
                    : "text-text-muted hover:text-text-secondary"
                }`}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
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
                <div className="grid grid-cols-[1fr_1fr_1fr_40px] gap-3 mb-2">
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">
                    Name
                  </span>
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">
                    Email
                  </span>
                  <span className="text-xs font-medium text-text-muted uppercase tracking-wider">
                    Role
                  </span>
                  <span />
                </div>
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {bulkRows.map((row, index) => (
                    <div
                      key={index}
                      className="grid grid-cols-[1fr_1fr_1fr_40px] gap-3 items-center"
                    >
                      <input
                        type="text"
                        placeholder="Full name"
                        value={row.name}
                        onChange={(e) =>
                          updateBulkRow(index, "name", e.target.value)
                        }
                        className={inputClass}
                      />
                      <input
                        type="email"
                        placeholder="Email"
                        value={row.email}
                        onChange={(e) =>
                          updateBulkRow(index, "email", e.target.value)
                        }
                        className={inputClass}
                      />
                      <select
                        aria-label="Role"
                        value={row.role}
                        onChange={(e) =>
                          updateBulkRow(index, "role", e.target.value)
                        }
                        className={selectClass}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {roleLabel(r)}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => removeBulkRow(index)}
                        disabled={bulkRows.length === 1}
                        title="Remove row"
                        className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-rose-500 hover:bg-rose-50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:text-text-muted disabled:hover:bg-transparent"
                      >
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={addBulkRow}
                  className="mt-3 h-8 px-3 text-sm text-accent hover:text-accent-light font-medium flex items-center gap-1.5 transition-colors"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  Add Row
                </button>
                <p className="text-[11px] text-text-muted mt-2">
                  Default password: Welcome@123
                </p>
                <div className="flex justify-end gap-2 mt-5 pt-4 border-t border-border-light">
                  <button
                    onClick={() => setShowBulkModal(false)}
                    className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleBulkAdd}
                    disabled={bulkLoading}
                    className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors disabled:opacity-50"
                  >
                    {bulkLoading ? "Adding..." : "Add All Users"}
                  </button>
                </div>
              </>
            )}

            {/* CSV Upload Tab */}
            {bulkTab === "csv" && (
              <>
                {csvRows.length === 0 ? (
                  <>
                    <div
                      onDragOver={(e) => {
                        e.preventDefault();
                        setIsDragging(true);
                      }}
                      onDragLeave={() => setIsDragging(false)}
                      onDrop={onDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                        isDragging
                          ? "border-accent bg-accent/5"
                          : "border-border hover:border-accent/30 hover:bg-surface-alt/30"
                      }`}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv"
                        onChange={onFileSelect}
                        aria-label="Upload CSV file"
                        className="hidden"
                      />
                      <svg
                        className="mx-auto mb-3 text-text-muted"
                        width="40"
                        height="40"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                      <p className="text-sm font-medium text-text-primary mb-1">
                        {isDragging
                          ? "Drop your file here"
                          : "Drag & drop a CSV file here"}
                      </p>
                      <p className="text-xs text-text-muted mb-3">
                        or click to browse
                      </p>
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-alt text-xs text-text-muted">
                        <svg
                          width="12"
                          height="12"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="16" x2="12" y2="12" />
                          <line x1="12" y1="8" x2="12.01" y2="8" />
                        </svg>
                        Format: Name, Email, Role (header row optional)
                      </span>
                    </div>

                    {csvError && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-rose-500">
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <line x1="15" y1="9" x2="9" y2="15" />
                          <line x1="9" y1="9" x2="15" y2="15" />
                        </svg>
                        {csvError}
                      </div>
                    )}

                    <div className="flex justify-end gap-2 mt-5 pt-4 border-t border-border-light">
                      <button
                        onClick={() => setShowBulkModal(false)}
                        className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center justify-between mb-4 px-3 py-2.5 bg-surface-alt/50 rounded-lg">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                          <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="#059669"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-text-primary">
                            {csvFileName}
                          </p>
                          <p className="text-xs text-text-muted">
                            {csvRows.length} user
                            {csvRows.length !== 1 ? "s" : ""} found
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={resetCsv}
                        className="text-xs text-text-muted hover:text-rose-500 font-medium transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                    <div className="border border-border rounded-lg overflow-hidden mb-1">
                      <div className="grid grid-cols-[1fr_1fr_1fr] gap-0 text-xs font-semibold text-text-muted uppercase tracking-wider bg-surface-alt/50">
                        <span className="px-3 py-2.5">Name</span>
                        <span className="px-3 py-2.5">Email</span>
                        <span className="px-3 py-2.5">Role</span>
                      </div>
                      <div className="max-h-56 overflow-y-auto divide-y divide-border-light">
                        {csvRows.map((row, i) => (
                          <div
                            key={i}
                            className="grid grid-cols-[1fr_1fr_1fr] gap-0 text-sm"
                          >
                            <span className="px-3 py-2.5 text-text-primary truncate">
                              {row.name}
                            </span>
                            <span className="px-3 py-2.5 text-text-muted truncate">
                              {row.email}
                            </span>
                            <span className="px-3 py-2.5 text-text-secondary truncate">
                              {roleLabel(row.role)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <p className="text-[11px] text-text-muted mb-4">
                      Default password: Welcome@123
                    </p>
                    <div className="flex justify-end gap-2 pt-4 border-t border-border-light">
                      <button
                        onClick={resetCsv}
                        className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors"
                      >
                        Back
                      </button>
                      <button
                        onClick={handleCsvUpload}
                        disabled={bulkLoading}
                        className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors disabled:opacity-50"
                      >
                        {bulkLoading
                          ? "Importing..."
                          : `Import ${csvRows.length} User${csvRows.length !== 1 ? "s" : ""}`}
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
