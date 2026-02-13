"use client";

import { useEffect, useState, useCallback } from "react";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

/* ─── Types ─── */

interface Reminder {
  id: string;
  user_id: string;
  entity_type: string;
  entity_id: string;
  entity_name: string | null;
  reminder_type: string;
  offset_label: string | null;
  title: string;
  message: string;
  link: string | null;
  remind_at: string;
  status: string;
  sent_at: string | null;
  snoozed_until: string | null;
  dismissed_at: string | null;
  snooze_count: number;
  created_at: string;
  updated_at: string;
  created_by: string | null;
}

interface ReminderCounts {
  pending: number;
  overdue: number;
  total: number;
}

type StatusFilter = "all" | "pending" | "sent" | "snoozed" | "dismissed";
type SnoozeOption = "1h" | "3h" | "1d" | "3d" | "custom";

/* ─── Helpers ─── */

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusBadge(status: string) {
  const map: Record<string, { bg: string; text: string; label: string }> = {
    pending: { bg: "bg-yellow-500/10", text: "text-yellow-500", label: "Pending" },
    sent: { bg: "bg-green-500/10", text: "text-green-500", label: "Sent" },
    snoozed: { bg: "bg-blue-500/10", text: "text-blue-500", label: "Snoozed" },
    dismissed: { bg: "bg-gray-500/10", text: "text-gray-400", label: "Dismissed" },
  };
  const s = map[status] ?? { bg: "bg-gray-500/10", text: "text-gray-400", label: status };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  );
}

function entityBadge(type: string) {
  const map: Record<string, string> = {
    assignment: "bg-purple-500/10 text-purple-400",
    stage: "bg-cyan-500/10 text-cyan-400",
    step: "bg-indigo-500/10 text-indigo-400",
    task: "bg-orange-500/10 text-orange-400",
  };
  const cls = map[type] ?? "bg-gray-500/10 text-gray-400";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${cls}`}>
      {type}
    </span>
  );
}

function getSnoozeDate(option: SnoozeOption, customDate?: string): string {
  const now = new Date();
  switch (option) {
    case "1h": return new Date(now.getTime() + 3600_000).toISOString();
    case "3h": return new Date(now.getTime() + 10800_000).toISOString();
    case "1d": return new Date(now.getTime() + 86400_000).toISOString();
    case "3d": return new Date(now.getTime() + 259200_000).toISOString();
    case "custom": return customDate ? new Date(customDate).toISOString() : now.toISOString();
  }
}

/* ─── Component ─── */

export default function RemindersPage() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [counts, setCounts] = useState<ReminderCounts>({ pending: 0, overdue: 0, total: 0 });
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Create modal state
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    entity_type: "assignment",
    entity_id: "",
    entity_name: "",
    title: "",
    message: "",
    remind_at: "",
    link: "",
  });
  const [creating, setCreating] = useState(false);

  // Snooze modal state
  const [snoozeTarget, setSnoozeTarget] = useState<Reminder | null>(null);
  const [snoozeOption, setSnoozeOption] = useState<SnoozeOption>("1h");
  const [snoozeCustom, setSnoozeCustom] = useState("");

  // ─── Data loading ───

  const fetchReminders = useCallback(async () => {
    try {
      setLoading(true);
      const query = filter !== "all" ? `?status=${filter}` : "";
      const data = await apiCall<Reminder[]>(`${API_ENDPOINTS.REMINDERS}${query}`);
      setReminders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reminders");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const fetchCounts = useCallback(async () => {
    try {
      const data = await apiCall<ReminderCounts>(API_ENDPOINTS.REMINDERS_COUNTS);
      setCounts(data);
    } catch {
      // silently fail — counts are non-critical
    }
  }, []);

  useEffect(() => {
    fetchReminders();
    fetchCounts();
  }, [fetchReminders, fetchCounts]);

  // ─── Actions ───

  const handleCreate = async () => {
    if (!createForm.title || !createForm.remind_at || !createForm.entity_id) return;
    try {
      setCreating(true);
      await apiCall(API_ENDPOINTS.REMINDERS, {
        method: "POST",
        body: JSON.stringify({
          ...createForm,
          link: createForm.link || null,
          entity_name: createForm.entity_name || null,
        }),
      });
      setShowCreate(false);
      setCreateForm({ entity_type: "assignment", entity_id: "", entity_name: "", title: "", message: "", remind_at: "", link: "" });
      fetchReminders();
      fetchCounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create reminder");
    } finally {
      setCreating(false);
    }
  };

  const handleSnooze = async () => {
    if (!snoozeTarget) return;
    try {
      const snoozeUntil = getSnoozeDate(snoozeOption, snoozeCustom);
      await apiCall(API_ENDPOINTS.REMINDER_SNOOZE(snoozeTarget.id), {
        method: "POST",
        body: JSON.stringify({ snooze_until: snoozeUntil }),
      });
      setSnoozeTarget(null);
      fetchReminders();
      fetchCounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to snooze reminder");
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      await apiCall(API_ENDPOINTS.REMINDER_DISMISS(id), { method: "POST" });
      fetchReminders();
      fetchCounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to dismiss reminder");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiCall(API_ENDPOINTS.REMINDER(id), { method: "DELETE" });
      fetchReminders();
      fetchCounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete reminder");
    }
  };

  // ─── Render ───

  const filters: { key: StatusFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "pending", label: "Pending" },
    { key: "sent", label: "Sent" },
    { key: "snoozed", label: "Snoozed" },
    { key: "dismissed", label: "Dismissed" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Reminders</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage task and assignment reminders
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-accent text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-accent/90 transition-colors"
        >
          + New Reminder
        </button>
      </div>

      {/* Counts */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-surface border border-border rounded-xl p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider">Pending</p>
          <p className="text-2xl font-bold text-yellow-500 mt-1">{counts.pending}</p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider">Overdue</p>
          <p className="text-2xl font-bold text-red-500 mt-1">{counts.overdue}</p>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider">Total</p>
          <p className="text-2xl font-bold text-text-primary mt-1">{counts.total}</p>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-sm rounded-lg px-4 py-3 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError("")} className="text-danger hover:text-danger/80" title="Close error">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-1 bg-surface-alt rounded-lg p-1 w-fit">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            title={`Filter by ${f.label}`}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              filter === f.key
                ? "bg-surface text-text-primary shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Reminders list */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-text-muted">Loading reminders...</div>
        ) : reminders.length === 0 ? (
          <div className="p-12 text-center">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-4 text-text-muted">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <p className="text-text-secondary">No reminders found</p>
            <p className="text-xs text-text-muted mt-1">
              {filter !== "all"
                ? `No ${filter} reminders — try a different filter.`
                : "Create a manual reminder or auto-reminders will appear when tasks have due dates."}
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-surface-alt/50 text-xs text-text-muted uppercase tracking-wider">
                <th className="text-left px-4 py-3 font-medium">Title</th>
                <th className="text-left px-4 py-3 font-medium">Entity</th>
                <th className="text-left px-4 py-3 font-medium">Type</th>
                <th className="text-left px-4 py-3 font-medium">Remind At</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-right px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {reminders.map((r) => (
                <tr key={r.id} className="border-t border-border/50 hover:bg-surface-alt/30 transition-colors">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-text-primary">{r.title}</p>
                    {r.message && (
                      <p className="text-xs text-text-muted mt-0.5 line-clamp-1">{r.message}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      {entityBadge(r.entity_type)}
                      {r.entity_name && (
                        <span className="text-xs text-text-muted truncate max-w-35">{r.entity_name}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-text-secondary capitalize">
                      {r.reminder_type === "auto_due_date" ? "Auto" : "Manual"}
                    </span>
                    {r.offset_label && (
                      <span className="block text-xs text-text-muted">{r.offset_label.replace(/_/g, " ")}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-sm ${new Date(r.remind_at) < new Date() && r.status === "pending" ? "text-red-400 font-medium" : "text-text-secondary"}`}>
                      {formatDate(r.remind_at)}
                    </span>
                    {r.snooze_count > 0 && (
                      <span className="block text-xs text-text-muted">Snoozed {r.snooze_count}x</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {statusBadge(r.status)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {(r.status === "pending" || r.status === "snoozed") && (
                        <>
                          <button
                            onClick={() => setSnoozeTarget(r)}
                            title="Snooze reminder"
                            className="p-1.5 rounded-md text-text-muted hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M4 12h8l-4 4" />
                              <path d="M4 12l4-4" />
                              <circle cx="17" cy="12" r="5" />
                              <path d="M17 10v2l1 1" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDismiss(r.id)}
                            title="Dismiss reminder"
                            className="p-1.5 rounded-md text-text-muted hover:text-yellow-400 hover:bg-yellow-500/10 transition-colors"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                              <line x1="1" y1="1" x2="23" y2="23" />
                            </svg>
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDelete(r.id)}
                        title="Delete reminder"
                        className="p-1.5 rounded-md text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ─── Create Reminder Modal ─── */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl w-full max-w-lg mx-4 shadow-xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="text-lg font-semibold text-text-primary">Create Reminder</h2>
              <button onClick={() => setShowCreate(false)} title="Close modal" className="text-text-muted hover:text-text-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              </button>
            </div>

            <div className="px-6 py-4 space-y-4">
              {/* Entity type */}
              <div>
                <label htmlFor="create-entity-type" className="block text-sm font-medium text-text-secondary mb-1">Entity Type</label>
                <select
                  id="create-entity-type"
                  value={createForm.entity_type}
                  onChange={(e) => setCreateForm({ ...createForm, entity_type: e.target.value })}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent"
                >
                  <option value="assignment">Assignment</option>
                  <option value="stage">Stage</option>
                  <option value="step">Step</option>
                  <option value="task">Task</option>
                </select>
              </div>

              {/* Entity ID */}
              <div>
                <label htmlFor="create-entity-id" className="block text-sm font-medium text-text-secondary mb-1">Entity ID</label>
                <input
                  id="create-entity-id"
                  type="text"
                  placeholder="UUID of the entity"
                  value={createForm.entity_id}
                  onChange={(e) => setCreateForm({ ...createForm, entity_id: e.target.value })}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent"
                />
              </div>

              {/* Entity Name */}
              <div>
                <label htmlFor="create-entity-name" className="block text-sm font-medium text-text-secondary mb-1">Entity Name (optional)</label>
                <input
                  id="create-entity-name"
                  type="text"
                  placeholder="e.g. Q4 Tax Filing"
                  value={createForm.entity_name}
                  onChange={(e) => setCreateForm({ ...createForm, entity_name: e.target.value })}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent"
                />
              </div>

              {/* Title */}
              <div>
                <label htmlFor="create-title" className="block text-sm font-medium text-text-secondary mb-1">Title</label>
                <input
                  id="create-title"
                  type="text"
                  placeholder="Reminder title"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent"
                />
              </div>

              {/* Message */}
              <div>
                <label htmlFor="create-message" className="block text-sm font-medium text-text-secondary mb-1">Message</label>
                <textarea
                  id="create-message"
                  rows={2}
                  placeholder="Reminder details"
                  value={createForm.message}
                  onChange={(e) => setCreateForm({ ...createForm, message: e.target.value })}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent resize-none"
                />
              </div>

              {/* Remind At */}
              <div>
                <label htmlFor="create-remind-at" className="block text-sm font-medium text-text-secondary mb-1">Remind At</label>
                <input
                  id="create-remind-at"
                  type="datetime-local"
                  value={createForm.remind_at}
                  onChange={(e) => setCreateForm({ ...createForm, remind_at: e.target.value })}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent"
                />
              </div>

              {/* Link */}
              <div>
                <label htmlFor="create-link" className="block text-sm font-medium text-text-secondary mb-1">Link (optional)</label>
                <input
                  id="create-link"
                  type="text"
                  placeholder="/dashboard/assignments/..."
                  value={createForm.link}
                  onChange={(e) => setCreateForm({ ...createForm, link: e.target.value })}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={creating || !createForm.title || !createForm.remind_at || !createForm.entity_id}
                className="bg-accent text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? "Creating..." : "Create Reminder"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Snooze Modal ─── */}
      {snoozeTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-surface border border-border rounded-xl w-full max-w-sm mx-4 shadow-xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="text-lg font-semibold text-text-primary">Snooze Reminder</h2>
              <button onClick={() => setSnoozeTarget(null)} title="Close snooze modal" className="text-text-muted hover:text-text-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              </button>
            </div>

            <div className="px-6 py-4 space-y-3">
              <p className="text-sm text-text-secondary">
                Snooze &ldquo;{snoozeTarget.title}&rdquo;
              </p>

              {(["1h", "3h", "1d", "3d", "custom"] as SnoozeOption[]).map((opt) => {
                const labels: Record<SnoozeOption, string> = {
                  "1h": "1 Hour",
                  "3h": "3 Hours",
                  "1d": "1 Day",
                  "3d": "3 Days",
                  "custom": "Custom Date/Time",
                };
                return (
                  <label key={opt} className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="snooze-option"
                      checked={snoozeOption === opt}
                      onChange={() => setSnoozeOption(opt)}
                      className="accent-accent"
                    />
                    <span className="text-sm text-text-primary">{labels[opt]}</span>
                  </label>
                );
              })}

              {snoozeOption === "custom" && (
                <input
                  type="datetime-local"
                  title="Custom snooze date and time"
                  value={snoozeCustom}
                  onChange={(e) => setSnoozeCustom(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-alt border border-border rounded-lg text-text-primary text-sm focus:ring-2 focus:ring-accent/20 focus:border-accent mt-2"
                />
              )}
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
              <button
                onClick={() => setSnoozeTarget(null)}
                className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSnooze}
                disabled={snoozeOption === "custom" && !snoozeCustom}
                className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Snooze
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
