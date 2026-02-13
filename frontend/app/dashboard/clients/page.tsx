"use client";

import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

interface ClientItem {
  id: string;
  name: string;
  industry: string | null;
  status: string;
  email: string | null;
  phone: string | null;
  contact_count: number;
  created_at: string;
}

interface ClientDetail {
  id: string;
  name: string;
  industry: string | null;
  status: string;
  email: string | null;
  phone: string | null;
  website: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  tax_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  contacts: ContactLink[];
}

interface ContactLink {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  designation: string | null;
  role: string | null;
  is_primary: boolean;
  status: string;
}

const STATUS_OPTIONS = ["active", "inactive", "prospect", "archived"];
const INDUSTRY_OPTIONS = [
  "Financial Services",
  "Banking",
  "Insurance",
  "Healthcare",
  "Technology",
  "Manufacturing",
  "Retail",
  "Real Estate",
  "Education",
  "Government",
  "Other",
];

const statusBadge = (status: string) => {
  const map: Record<string, string> = {
    active: "bg-emerald-50 text-emerald-700 border-emerald-200",
    inactive: "bg-gray-50 text-gray-600 border-gray-200",
    prospect: "bg-blue-50 text-blue-700 border-blue-200",
    archived: "bg-orange-50 text-orange-700 border-orange-200",
  };
  return map[status] || map.active;
};

export default function ClientsPage() {
  const [clients, setClients] = useState<ClientItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingClient, setEditingClient] = useState<ClientDetail | null>(null);
  const [detailClient, setDetailClient] = useState<ClientDetail | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [formName, setFormName] = useState("");
  const [formIndustry, setFormIndustry] = useState("");
  const [formStatus, setFormStatus] = useState("active");
  const [formEmail, setFormEmail] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formWebsite, setFormWebsite] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formCity, setFormCity] = useState("");
  const [formState, setFormState] = useState("");
  const [formCountry, setFormCountry] = useState("");
  const [formPostalCode, setFormPostalCode] = useState("");
  const [formTaxId, setFormTaxId] = useState("");
  const [formNotes, setFormNotes] = useState("");

  const fetchClients = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (filterStatus) params.set("status", filterStatus);
      const qs = params.toString();
      const data = await apiCall<{ clients: ClientItem[]; total: number }>(
        `${API_ENDPOINTS.CLIENTS}${qs ? `?${qs}` : ""}`
      );
      setClients(data.clients);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to fetch clients:", error);
    } finally {
      setLoading(false);
    }
  }, [search, filterStatus]);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  const resetForm = () => {
    setFormName("");
    setFormIndustry("");
    setFormStatus("active");
    setFormEmail("");
    setFormPhone("");
    setFormWebsite("");
    setFormAddress("");
    setFormCity("");
    setFormState("");
    setFormCountry("");
    setFormPostalCode("");
    setFormTaxId("");
    setFormNotes("");
    setEditingClient(null);
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  const openEditModal = async (clientId: string) => {
    try {
      const data = await apiCall<ClientDetail>(API_ENDPOINTS.CLIENT(clientId));
      setEditingClient(data);
      setFormName(data.name);
      setFormIndustry(data.industry || "");
      setFormStatus(data.status);
      setFormEmail(data.email || "");
      setFormPhone(data.phone || "");
      setFormWebsite(data.website || "");
      setFormAddress(data.address || "");
      setFormCity(data.city || "");
      setFormState(data.state || "");
      setFormCountry(data.country || "");
      setFormPostalCode(data.postal_code || "");
      setFormTaxId(data.tax_id || "");
      setFormNotes(data.notes || "");
      setShowModal(true);
    } catch (error) {
      console.error("Failed to load client:", error);
    }
  };

  const openDetail = async (clientId: string) => {
    try {
      const data = await apiCall<ClientDetail>(API_ENDPOINTS.CLIENT(clientId));
      setDetailClient(data);
      setShowDetail(true);
    } catch (error) {
      console.error("Failed to load client details:", error);
    }
  };

  const handleSave = async () => {
    if (!formName.trim()) return;
    setSaving(true);
    try {
      const body = {
        name: formName.trim(),
        industry: formIndustry || null,
        status: formStatus,
        email: formEmail || null,
        phone: formPhone || null,
        website: formWebsite || null,
        address: formAddress || null,
        city: formCity || null,
        state: formState || null,
        country: formCountry || null,
        postal_code: formPostalCode || null,
        tax_id: formTaxId || null,
        notes: formNotes || null,
      };

      if (editingClient) {
        await apiCall(API_ENDPOINTS.CLIENT(editingClient.id), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } else {
        await apiCall(API_ENDPOINTS.CLIENTS, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      }

      setShowModal(false);
      resetForm();
      await fetchClients();
    } catch (error) {
      console.error("Failed to save client:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (clientId: string) => {
    if (!confirm("Are you sure you want to delete this client?")) return;
    try {
      await apiCall(API_ENDPOINTS.CLIENT(clientId), { method: "DELETE" });
      await fetchClients();
      if (showDetail && detailClient?.id === clientId) {
        setShowDetail(false);
        setDetailClient(null);
      }
    } catch (error) {
      console.error("Failed to delete client:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-100">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-accent"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Clients</h1>
          <p className="text-sm text-text-muted mt-1">{total} client{total !== 1 ? "s" : ""} total</p>
        </div>
        <button
          onClick={openCreateModal}
          className="h-10 px-5 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors flex items-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Client
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1 max-w-xs">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search clients..."
            className="h-9 w-full pl-9 pr-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:ring-2 focus:ring-accent/20 focus:border-accent/40"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          title="Filter by status"
          className="h-9 px-3 text-sm bg-surface border border-border rounded-lg text-text-primary"
        >
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-surface-alt/50 text-left">
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Name</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Industry</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Status</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Email</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Contacts</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-light">
            {clients.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-text-muted text-sm">
                  No clients found. Click &ldquo;Add Client&rdquo; to create one.
                </td>
              </tr>
            ) : (
              clients.map((client) => (
                <tr key={client.id} className="hover:bg-surface-alt/30 transition-colors">
                  <td className="px-5 py-3">
                    <button onClick={() => openDetail(client.id)} className="text-sm font-medium text-text-primary hover:text-accent transition-colors text-left">
                      {client.name}
                    </button>
                  </td>
                  <td className="px-5 py-3 text-sm text-text-secondary">{client.industry || "-"}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadge(client.status)}`}>
                      {client.status}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-sm text-text-secondary">{client.email || "-"}</td>
                  <td className="px-5 py-3 text-sm text-text-secondary">{client.contact_count}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => openEditModal(client.id)}
                        className="p-1.5 text-text-muted hover:text-accent rounded transition-colors"
                        title="Edit"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(client.id)}
                        className="p-1.5 text-text-muted hover:text-red-500 rounded transition-colors"
                        title="Delete"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto p-6">
            <h2 className="text-lg font-bold text-text-primary mb-5">
              {editingClient ? "Edit Client" : "New Client"}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Name *</label>
                <input value={formName} onChange={(e) => setFormName(e.target.value)} className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" placeholder="Company name" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Industry</label>
                  <select value={formIndustry} onChange={(e) => setFormIndustry(e.target.value)} title="Industry" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg">
                    <option value="">Select</option>
                    {INDUSTRY_OPTIONS.map((i) => <option key={i} value={i}>{i}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Status</label>
                  <select value={formStatus} onChange={(e) => setFormStatus(e.target.value)} title="Status" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg">
                    {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Email</label>
                  <input value={formEmail} onChange={(e) => setFormEmail(e.target.value)} className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" placeholder="email@company.com" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Phone</label>
                  <input value={formPhone} onChange={(e) => setFormPhone(e.target.value)} className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" placeholder="+1 (555) 000-0000" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Website</label>
                <input value={formWebsite} onChange={(e) => setFormWebsite(e.target.value)} className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" placeholder="https://company.com" />
              </div>

              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Address</label>
                <input value={formAddress} onChange={(e) => setFormAddress(e.target.value)} className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" placeholder="Street address" />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">City</label>
                  <input value={formCity} onChange={(e) => setFormCity(e.target.value)} placeholder="City" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">State</label>
                  <input value={formState} onChange={(e) => setFormState(e.target.value)} placeholder="State" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Country</label>
                  <input value={formCountry} onChange={(e) => setFormCountry(e.target.value)} placeholder="Country" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Postal Code</label>
                  <input value={formPostalCode} onChange={(e) => setFormPostalCode(e.target.value)} placeholder="Postal code" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Tax ID</label>
                  <input value={formTaxId} onChange={(e) => setFormTaxId(e.target.value)} placeholder="Tax ID" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Notes</label>
                <textarea value={formNotes} onChange={(e) => setFormNotes(e.target.value)} rows={3} placeholder="Additional notes" className="w-full px-3 py-2 text-sm bg-surface-alt border border-border rounded-lg resize-none" />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border-light">
              <button onClick={() => { setShowModal(false); resetForm(); }} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">
                Cancel
              </button>
              <button onClick={handleSave} disabled={!formName.trim() || saving} className="h-9 px-5 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors disabled:opacity-50">
                {saving ? "Saving..." : editingClient ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Panel */}
      {showDetail && detailClient && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-text-primary">{detailClient.name}</h2>
              <button onClick={() => setShowDetail(false)} title="Close" className="p-1 text-text-muted hover:text-text-primary">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-text-muted">Status</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadge(detailClient.status)}`}>{detailClient.status}</span>
              </div>
              {detailClient.industry && <div className="flex justify-between"><span className="text-text-muted">Industry</span><span className="text-text-primary">{detailClient.industry}</span></div>}
              {detailClient.email && <div className="flex justify-between"><span className="text-text-muted">Email</span><span className="text-text-primary">{detailClient.email}</span></div>}
              {detailClient.phone && <div className="flex justify-between"><span className="text-text-muted">Phone</span><span className="text-text-primary">{detailClient.phone}</span></div>}
              {detailClient.website && <div className="flex justify-between"><span className="text-text-muted">Website</span><span className="text-text-primary">{detailClient.website}</span></div>}
              {detailClient.tax_id && <div className="flex justify-between"><span className="text-text-muted">Tax ID</span><span className="text-text-primary">{detailClient.tax_id}</span></div>}
              {(detailClient.address || detailClient.city) && (
                <div className="flex justify-between">
                  <span className="text-text-muted">Address</span>
                  <span className="text-text-primary text-right">
                    {[detailClient.address, detailClient.city, detailClient.state, detailClient.country, detailClient.postal_code].filter(Boolean).join(", ")}
                  </span>
                </div>
              )}
              {detailClient.notes && <div><span className="text-text-muted block mb-1">Notes</span><p className="text-text-primary bg-surface-alt p-3 rounded-lg">{detailClient.notes}</p></div>}
            </div>

            {/* Linked Contacts */}
            <div className="mt-6 pt-4 border-t border-border-light">
              <h3 className="text-sm font-semibold text-text-primary mb-3">
                Linked Contacts ({detailClient.contacts?.length || 0})
              </h3>
              {detailClient.contacts && detailClient.contacts.length > 0 ? (
                <div className="space-y-2">
                  {detailClient.contacts.map((c) => (
                    <div key={c.id} className="flex items-center justify-between p-3 bg-surface-alt rounded-lg">
                      <div>
                        <p className="text-sm font-medium text-text-primary">
                          {c.first_name} {c.last_name}
                          {c.is_primary && <span className="ml-2 text-xs text-accent font-medium">Primary</span>}
                        </p>
                        <p className="text-xs text-text-muted">{[c.designation, c.email].filter(Boolean).join(" | ")}</p>
                      </div>
                      {c.role && <span className="text-xs text-text-secondary bg-surface px-2 py-0.5 rounded">{c.role}</span>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-muted">No contacts linked yet.</p>
              )}
            </div>

            <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border-light">
              <button onClick={() => setShowDetail(false)} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">
                Close
              </button>
              <button onClick={() => { setShowDetail(false); openEditModal(detailClient.id); }} className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors">
                Edit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
