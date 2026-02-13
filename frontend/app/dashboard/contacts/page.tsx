"use client";

import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

interface ContactItem {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  designation: string | null;
  status: string;
  created_at: string;
  client_count: number;
}

interface ContactDetail {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  designation: string | null;
  department: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  clients: ClientLink[];
}

interface ClientLink {
  id: string;
  name: string;
  industry: string | null;
  role: string | null;
  is_primary: boolean;
}

interface ClientOption {
  id: string;
  name: string;
}

const STATUS_OPTIONS = ["active", "inactive", "archived"];

const statusBadge = (status: string) => {
  const map: Record<string, string> = {
    active: "bg-emerald-50 text-emerald-700 border-emerald-200",
    inactive: "bg-gray-50 text-gray-600 border-gray-200",
    archived: "bg-orange-50 text-orange-700 border-orange-200",
  };
  return map[status] || map.active;
};

export default function ContactsPage() {
  const [contacts, setContacts] = useState<ContactItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingContact, setEditingContact] = useState<ContactDetail | null>(null);
  const [detailContact, setDetailContact] = useState<ContactDetail | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [saving, setSaving] = useState(false);

  // Link to client
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkContactId, setLinkContactId] = useState("");
  const [availableClients, setAvailableClients] = useState<ClientOption[]>([]);
  const [selectedClientId, setSelectedClientId] = useState("");
  const [linkRole, setLinkRole] = useState("");
  const [linkPrimary, setLinkPrimary] = useState(false);

  // Form fields
  const [formFirstName, setFormFirstName] = useState("");
  const [formLastName, setFormLastName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formMobile, setFormMobile] = useState("");
  const [formDesignation, setFormDesignation] = useState("");
  const [formDepartment, setFormDepartment] = useState("");
  const [formStatus, setFormStatus] = useState("active");
  const [formNotes, setFormNotes] = useState("");

  const fetchContacts = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (filterStatus) params.set("status", filterStatus);
      const qs = params.toString();
      const data = await apiCall<{ contacts: ContactItem[]; total: number }>(
        `${API_ENDPOINTS.CONTACTS}${qs ? `?${qs}` : ""}`
      );
      setContacts(data.contacts);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to fetch contacts:", error);
    } finally {
      setLoading(false);
    }
  }, [search, filterStatus]);

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  const resetForm = () => {
    setFormFirstName("");
    setFormLastName("");
    setFormEmail("");
    setFormPhone("");
    setFormMobile("");
    setFormDesignation("");
    setFormDepartment("");
    setFormStatus("active");
    setFormNotes("");
    setEditingContact(null);
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  const openEditModal = async (contactId: string) => {
    try {
      const data = await apiCall<ContactDetail>(API_ENDPOINTS.CONTACT(contactId));
      setEditingContact(data);
      setFormFirstName(data.first_name);
      setFormLastName(data.last_name);
      setFormEmail(data.email || "");
      setFormPhone(data.phone || "");
      setFormMobile(data.mobile || "");
      setFormDesignation(data.designation || "");
      setFormDepartment(data.department || "");
      setFormStatus(data.status);
      setFormNotes(data.notes || "");
      setShowModal(true);
    } catch (error) {
      console.error("Failed to load contact:", error);
    }
  };

  const openDetail = async (contactId: string) => {
    try {
      const data = await apiCall<ContactDetail>(API_ENDPOINTS.CONTACT(contactId));
      setDetailContact(data);
      setShowDetail(true);
    } catch (error) {
      console.error("Failed to load contact details:", error);
    }
  };

  const handleSave = async () => {
    if (!formFirstName.trim() || !formLastName.trim()) return;
    setSaving(true);
    try {
      const body = {
        first_name: formFirstName.trim(),
        last_name: formLastName.trim(),
        email: formEmail || null,
        phone: formPhone || null,
        mobile: formMobile || null,
        designation: formDesignation || null,
        department: formDepartment || null,
        status: formStatus,
        notes: formNotes || null,
      };

      if (editingContact) {
        await apiCall(API_ENDPOINTS.CONTACT(editingContact.id), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } else {
        await apiCall(API_ENDPOINTS.CONTACTS, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      }

      setShowModal(false);
      resetForm();
      await fetchContacts();
    } catch (error) {
      console.error("Failed to save contact:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (contactId: string) => {
    if (!confirm("Are you sure you want to delete this contact?")) return;
    try {
      await apiCall(API_ENDPOINTS.CONTACT(contactId), { method: "DELETE" });
      await fetchContacts();
      if (showDetail && detailContact?.id === contactId) {
        setShowDetail(false);
        setDetailContact(null);
      }
    } catch (error) {
      console.error("Failed to delete contact:", error);
    }
  };

  const openLinkToClient = async (contactId: string) => {
    setLinkContactId(contactId);
    setSelectedClientId("");
    setLinkRole("");
    setLinkPrimary(false);
    try {
      const data = await apiCall<{ clients: ClientOption[]; total: number }>(API_ENDPOINTS.CLIENTS);
      setAvailableClients(data.clients);
    } catch (error) {
      console.error("Failed to load clients:", error);
    }
    setShowLinkModal(true);
  };

  const handleLinkToClient = async () => {
    if (!selectedClientId || !linkContactId) return;
    try {
      await apiCall(API_ENDPOINTS.CLIENT_CONTACTS(selectedClientId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contact_id: linkContactId,
          role: linkRole || null,
          is_primary: linkPrimary,
        }),
      });
      setShowLinkModal(false);
      await fetchContacts();
      // Refresh detail if open
      if (showDetail && detailContact?.id === linkContactId) {
        const data = await apiCall<ContactDetail>(API_ENDPOINTS.CONTACT(linkContactId));
        setDetailContact(data);
      }
    } catch (error) {
      console.error("Failed to link contact to client:", error);
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
          <h1 className="text-2xl font-bold text-text-primary">Contacts</h1>
          <p className="text-sm text-text-muted mt-1">{total} contact{total !== 1 ? "s" : ""} total</p>
        </div>
        <button
          onClick={openCreateModal}
          className="h-10 px-5 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors flex items-center gap-2"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Contact
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
            placeholder="Search contacts..."
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
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Designation</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Email</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Status</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Clients</th>
              <th className="px-5 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-light">
            {contacts.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-text-muted text-sm">
                  No contacts found. Click &ldquo;Add Contact&rdquo; to create one.
                </td>
              </tr>
            ) : (
              contacts.map((contact) => (
                <tr key={contact.id} className="hover:bg-surface-alt/30 transition-colors">
                  <td className="px-5 py-3">
                    <button onClick={() => openDetail(contact.id)} className="text-sm font-medium text-text-primary hover:text-accent transition-colors text-left">
                      {contact.first_name} {contact.last_name}
                    </button>
                  </td>
                  <td className="px-5 py-3 text-sm text-text-secondary">{contact.designation || "-"}</td>
                  <td className="px-5 py-3 text-sm text-text-secondary">{contact.email || "-"}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadge(contact.status)}`}>
                      {contact.status}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-sm text-text-secondary">{contact.client_count}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <button onClick={() => openLinkToClient(contact.id)} className="p-1.5 text-text-muted hover:text-accent rounded transition-colors" title="Link to Client">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                        </svg>
                      </button>
                      <button onClick={() => openEditModal(contact.id)} className="p-1.5 text-text-muted hover:text-accent rounded transition-colors" title="Edit">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                      </button>
                      <button onClick={() => handleDelete(contact.id)} className="p-1.5 text-text-muted hover:text-red-500 rounded transition-colors" title="Delete">
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
              {editingContact ? "Edit Contact" : "New Contact"}
            </h2>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">First Name *</label>
                  <input value={formFirstName} onChange={(e) => setFormFirstName(e.target.value)} placeholder="First name" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Last Name *</label>
                  <input value={formLastName} onChange={(e) => setFormLastName(e.target.value)} placeholder="Last name" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Email</label>
                  <input value={formEmail} onChange={(e) => setFormEmail(e.target.value)} placeholder="email@example.com" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Phone</label>
                  <input value={formPhone} onChange={(e) => setFormPhone(e.target.value)} placeholder="+1 (555) 000-0000" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Mobile</label>
                <input value={formMobile} onChange={(e) => setFormMobile(e.target.value)} placeholder="Mobile number" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Designation</label>
                  <input value={formDesignation} onChange={(e) => setFormDesignation(e.target.value)} placeholder="e.g., CFO" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">Department</label>
                  <input value={formDepartment} onChange={(e) => setFormDepartment(e.target.value)} placeholder="e.g., Finance" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Status</label>
                <select value={formStatus} onChange={(e) => setFormStatus(e.target.value)} title="Status" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg">
                  {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                </select>
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
              <button onClick={handleSave} disabled={!formFirstName.trim() || !formLastName.trim() || saving} className="h-9 px-5 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors disabled:opacity-50">
                {saving ? "Saving..." : editingContact ? "Update" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Panel */}
      {showDetail && detailContact && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-text-primary">{detailContact.first_name} {detailContact.last_name}</h2>
              <button onClick={() => setShowDetail(false)} title="Close" className="p-1 text-text-muted hover:text-text-primary">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-text-muted">Status</span><span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusBadge(detailContact.status)}`}>{detailContact.status}</span></div>
              {detailContact.designation && <div className="flex justify-between"><span className="text-text-muted">Designation</span><span className="text-text-primary">{detailContact.designation}</span></div>}
              {detailContact.department && <div className="flex justify-between"><span className="text-text-muted">Department</span><span className="text-text-primary">{detailContact.department}</span></div>}
              {detailContact.email && <div className="flex justify-between"><span className="text-text-muted">Email</span><span className="text-text-primary">{detailContact.email}</span></div>}
              {detailContact.phone && <div className="flex justify-between"><span className="text-text-muted">Phone</span><span className="text-text-primary">{detailContact.phone}</span></div>}
              {detailContact.mobile && <div className="flex justify-between"><span className="text-text-muted">Mobile</span><span className="text-text-primary">{detailContact.mobile}</span></div>}
              {detailContact.notes && <div><span className="text-text-muted block mb-1">Notes</span><p className="text-text-primary bg-surface-alt p-3 rounded-lg">{detailContact.notes}</p></div>}
            </div>

            {/* Linked Clients */}
            <div className="mt-6 pt-4 border-t border-border-light">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-text-primary">
                  Linked Clients ({detailContact.clients?.length || 0})
                </h3>
                <button onClick={() => { setShowDetail(false); openLinkToClient(detailContact.id); }} className="text-xs text-accent hover:underline">
                  + Link to Client
                </button>
              </div>
              {detailContact.clients && detailContact.clients.length > 0 ? (
                <div className="space-y-2">
                  {detailContact.clients.map((c) => (
                    <div key={c.id} className="flex items-center justify-between p-3 bg-surface-alt rounded-lg">
                      <div>
                        <p className="text-sm font-medium text-text-primary">
                          {c.name}
                          {c.is_primary && <span className="ml-2 text-xs text-accent font-medium">Primary</span>}
                        </p>
                        <p className="text-xs text-text-muted">{c.industry || "No industry"}</p>
                      </div>
                      {c.role && <span className="text-xs text-text-secondary bg-surface px-2 py-0.5 rounded">{c.role}</span>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-muted">Not linked to any client yet.</p>
              )}
            </div>

            <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border-light">
              <button onClick={() => setShowDetail(false)} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">Close</button>
              <button onClick={() => { setShowDetail(false); openEditModal(detailContact.id); }} className="h-9 px-4 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors">Edit</button>
            </div>
          </div>
        </div>
      )}

      {/* Link to Client Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-lg font-bold text-text-primary mb-5">Link to Client</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Client *</label>
                <select value={selectedClientId} onChange={(e) => setSelectedClientId(e.target.value)} title="Select client" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg">
                  <option value="">Select a client...</option>
                  {availableClients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Role</label>
                <input value={linkRole} onChange={(e) => setLinkRole(e.target.value)} placeholder="e.g., Primary, Billing, Technical" className="w-full h-9 px-3 text-sm bg-surface-alt border border-border rounded-lg" />
              </div>
              <label className="flex items-center gap-2 text-sm text-text-primary cursor-pointer">
                <input type="checkbox" checked={linkPrimary} onChange={(e) => setLinkPrimary(e.target.checked)} className="w-4 h-4" />
                Primary contact for this client
              </label>
            </div>

            <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border-light">
              <button onClick={() => setShowLinkModal(false)} className="h-9 px-4 text-sm font-medium text-text-secondary bg-surface border border-border rounded-lg hover:bg-surface-alt transition-colors">Cancel</button>
              <button onClick={handleLinkToClient} disabled={!selectedClientId} className="h-9 px-5 text-sm font-medium text-white bg-accent hover:bg-accent-light rounded-lg transition-colors disabled:opacity-50">Link</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
