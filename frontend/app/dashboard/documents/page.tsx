"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { apiCall, getAuthToken, API_BASE_URL } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";
import { formatDate, formatFileSize } from "@/lib/utils";

/* ─── Types ──────────────────────────────────────────────────────────── */

interface DocumentItem {
  id: string;
  name: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  content_type: string | null;
  status: string;
  category: string;
  description: string | null;
  version: string | null;
  tags: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  uploaded_by: string;
  uploaded_by_name: string | null;
  created_at: string;
  updated_at: string;
}

interface DocumentStats {
  total: number;
  pending_review: number;
  in_review: number;
  reviewed: number;
  categories: Record<string, number>;
}

interface ListResponse {
  documents: DocumentItem[];
  total: number;
  skip: number;
  limit: number;
}

/* ─── Constants ──────────────────────────────────────────────────────── */

const STATUSES = [
  { value: "pending_review", label: "Pending Review" },
  { value: "in_review", label: "In Review" },
  { value: "reviewed", label: "Reviewed" },
  { value: "rejected", label: "Rejected" },
  { value: "archived", label: "Archived" },
];

const CATEGORIES = [
  { value: "compliance", label: "Compliance" },
  { value: "policy", label: "Policy" },
  { value: "audit", label: "Audit" },
  { value: "regulatory", label: "Regulatory" },
  { value: "risk", label: "Risk" },
  { value: "operations", label: "Operations" },
  { value: "governance", label: "Governance" },
  { value: "security", label: "Security" },
  { value: "financial", label: "Financial" },
  { value: "legal", label: "Legal" },
  { value: "hr", label: "HR" },
  { value: "other", label: "Other" },
];

const PAGE_SIZE = 20;

const inputClass =
  "w-full h-10 px-3 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all outline-none";
const selectClass =
  "h-10 px-3 text-sm bg-surface border border-border rounded-lg text-text-secondary focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all outline-none appearance-none cursor-pointer";
const textareaClass =
  "w-full px-3 py-2 text-sm bg-surface border border-border rounded-lg placeholder:text-text-muted focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all outline-none resize-none";

/* ─── Icons ──────────────────────────────────────────────────────────── */

function UploadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

function EditIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function DocIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

/* ─── Helpers ────────────────────────────────────────────────────────── */

function getFileTypeStyle(type: string): string {
  const map: Record<string, string> = {
    PDF: "bg-red-50 text-red-500",
    DOCX: "bg-blue-50 text-blue-500",
    DOC: "bg-blue-50 text-blue-500",
    XLSX: "bg-emerald-50 text-emerald-500",
    XLS: "bg-emerald-50 text-emerald-500",
    CSV: "bg-emerald-50 text-emerald-500",
    PPTX: "bg-orange-50 text-orange-500",
    PPT: "bg-orange-50 text-orange-500",
    TXT: "bg-gray-50 text-gray-500",
    PNG: "bg-purple-50 text-purple-500",
    JPG: "bg-purple-50 text-purple-500",
    JPEG: "bg-purple-50 text-purple-500",
  };
  return map[type] || "bg-gray-50 text-gray-500";
}

function getStatusStyle(status: string): string {
  switch (status) {
    case "reviewed":
      return "bg-emerald-50 text-emerald-700";
    case "in_review":
      return "bg-blue-50 text-blue-700";
    case "pending_review":
      return "bg-amber-50 text-amber-700";
    case "rejected":
      return "bg-red-50 text-red-700";
    case "archived":
      return "bg-gray-100 text-gray-600";
    default:
      return "bg-gray-100 text-gray-500";
  }
}

function statusLabel(status: string): string {
  return STATUSES.find((s) => s.value === status)?.label || status;
}

function categoryLabel(cat: string): string {
  return CATEGORIES.find((c) => c.value === cat)?.label || cat;
}

/* ─── Modal Component ────────────────────────────────────────────────── */

function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface rounded-xl border border-border shadow-lg w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-light">
          <h3 className="text-base font-semibold text-text-primary">{title}</h3>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-alt text-text-muted transition-colors" aria-label="Close">
            <XIcon />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

/* ─── Page Component ─────────────────────────────────────────────────── */

export default function DocumentsPage() {
  // List state
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterCategory, setFilterCategory] = useState("");

  // Stats
  const [stats, setStats] = useState<DocumentStats | null>(null);

  // Upload modal
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadName, setUploadName] = useState("");
  const [uploadCategory, setUploadCategory] = useState("other");
  const [uploadDescription, setUploadDescription] = useState("");
  const [uploadTags, setUploadTags] = useState("");
  const [uploading, setUploading] = useState(false);

  // Edit modal
  const [editDoc, setEditDoc] = useState<DocumentItem | null>(null);
  const [editName, setEditName] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editTags, setEditTags] = useState("");
  const [saving, setSaving] = useState(false);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<DocumentItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Drag state
  const [dragOver, setDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  /* ── Fetch documents ────────────────────────────────────────────────── */

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("skip", String(page * PAGE_SIZE));
      params.set("limit", String(PAGE_SIZE));
      if (search) params.set("search", search);
      if (filterStatus) params.set("status", filterStatus);
      if (filterCategory) params.set("category", filterCategory);

      const data = await apiCall<ListResponse>(`${API_ENDPOINTS.DOCUMENTS}?${params}`);
      setDocuments(data.documents);
      setTotal(data.total);
    } catch {
      setDocuments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, search, filterStatus, filterCategory]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await apiCall<DocumentStats>(API_ENDPOINTS.DOCUMENT_STATS);
      setStats(data);
    } catch {
      /* stats are non-critical */
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  /* ── Debounced search ───────────────────────────────────────────────── */

  const handleSearchChange = (value: string) => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setSearch(value);
      setPage(0);
    }, 300);
  };

  /* ── Upload ─────────────────────────────────────────────────────────── */

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    setUploadFiles(Array.from(files));
    if (!uploadOpen) setUploadOpen(true);
  };

  const handleUpload = async () => {
    if (uploadFiles.length === 0) return;
    setUploading(true);
    try {
      for (const file of uploadFiles) {
        const formData = new FormData();
        formData.append("file", file);
        if (uploadName) formData.append("name", uploadName);
        formData.append("category", uploadCategory);
        if (uploadDescription) formData.append("description", uploadDescription);
        if (uploadTags) formData.append("tags", uploadTags);

        const token = getAuthToken();
        await fetch(`${API_BASE_URL}${API_ENDPOINTS.DOCUMENT_UPLOAD}`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        });
      }
      resetUploadForm();
      fetchDocuments();
      fetchStats();
    } catch {
      /* upload error */
    } finally {
      setUploading(false);
    }
  };

  const resetUploadForm = () => {
    setUploadOpen(false);
    setUploadFiles([]);
    setUploadName("");
    setUploadCategory("other");
    setUploadDescription("");
    setUploadTags("");
  };

  /* ── Edit ────────────────────────────────────────────────────────────── */

  const openEdit = (doc: DocumentItem) => {
    setEditDoc(doc);
    setEditName(doc.name);
    setEditStatus(doc.status);
    setEditCategory(doc.category);
    setEditDescription(doc.description || "");
    setEditTags(doc.tags || "");
  };

  const handleUpdate = async () => {
    if (!editDoc) return;
    setSaving(true);
    try {
      const params = new URLSearchParams();
      if (editName !== editDoc.name) params.set("name", editName);
      if (editStatus !== editDoc.status) params.set("status", editStatus);
      if (editCategory !== editDoc.category) params.set("category", editCategory);
      if (editDescription !== (editDoc.description || "")) params.set("description", editDescription);
      if (editTags !== (editDoc.tags || "")) params.set("tags", editTags);

      if ([...params].length === 0) {
        setEditDoc(null);
        return;
      }

      await apiCall(API_ENDPOINTS.DOCUMENT(editDoc.id) + "?" + params.toString(), { method: "PATCH" });
      setEditDoc(null);
      fetchDocuments();
      fetchStats();
    } catch {
      /* update error */
    } finally {
      setSaving(false);
    }
  };

  /* ── Delete ──────────────────────────────────────────────────────────── */

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await apiCall(API_ENDPOINTS.DOCUMENT(deleteTarget.id), { method: "DELETE" });
      setDeleteTarget(null);
      fetchDocuments();
      fetchStats();
    } catch {
      /* delete error */
    } finally {
      setDeleting(false);
    }
  };

  /* ── Download ────────────────────────────────────────────────────────── */

  const handleDownload = (doc: DocumentItem) => {
    const token = getAuthToken();
    const url = `${API_BASE_URL}${API_ENDPOINTS.DOCUMENT_DOWNLOAD(doc.id)}`;
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((res) => res.blob())
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = doc.original_filename;
        a.click();
        URL.revokeObjectURL(blobUrl);
      });
  };

  /* ── Drag & Drop ─────────────────────────────────────────────────────── */

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };
  const handleDragLeave = () => setDragOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  /* ── Pagination ──────────────────────────────────────────────────────── */

  const totalPages = Math.ceil(total / PAGE_SIZE);

  /* ── Render ──────────────────────────────────────────────────────────── */

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl text-text-primary font-semibold tracking-tight">Documents</h1>
          <p className="text-sm text-text-secondary mt-1">Manage regulatory documents and filings</p>
        </div>
        <button
          onClick={() => setUploadOpen(true)}
          className="h-10 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
        >
          <UploadIcon />
          Upload Document
        </button>
      </div>

      {/* Upload drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 mb-6 text-center transition-all cursor-pointer animate-fade-in-up stagger-1 ${
          dragOver ? "border-accent bg-accent/5" : "border-border hover:border-accent/30 hover:bg-accent/2"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          multiple
          aria-label="Select files to upload"
          accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.ppt,.pptx,.txt,.png,.jpg,.jpeg,.gif,.zip"
          onChange={(e) => handleFileSelect(e.target.files)}
        />
        <div className="w-12 h-12 bg-surface-alt rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-text-muted">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p className="text-sm text-text-secondary font-medium">
          {dragOver ? "Drop files here" : "Drag & drop files here, or click to browse"}
        </p>
        <p className="text-xs text-text-muted mt-1">Supports PDF, DOCX, XLSX, CSV, PPTX, images up to 25MB</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6 animate-fade-in-up stagger-2">
        {[
          { label: "Total Documents", value: stats?.total ?? 0, color: "bg-blue-50 text-blue-500" },
          { label: "Pending Review", value: stats?.pending_review ?? 0, color: "bg-amber-50 text-amber-500" },
          { label: "In Review", value: stats?.in_review ?? 0, color: "bg-info/10 text-info" },
          { label: "Reviewed", value: stats?.reviewed ?? 0, color: "bg-emerald-50 text-emerald-500" },
        ].map((stat) => (
          <div key={stat.label} className="bg-surface rounded-xl border border-border px-5 py-4 flex items-center gap-4">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${stat.color}`}>
              <DocIcon />
            </div>
            <div>
              <p className="text-xl font-semibold text-text-primary">{stat.value.toLocaleString()}</p>
              <p className="text-xs text-text-muted">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Document list */}
      <div className="bg-surface rounded-xl border border-border overflow-hidden animate-fade-in-up stagger-3">
        {/* Toolbar */}
        <div className="px-5 py-4 border-b border-border-light flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-text-primary">All Documents</h2>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Search */}
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"><SearchIcon /></span>
              <input
                type="text"
                placeholder="Search documents..."
                defaultValue={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="h-8 w-48 pl-8 pr-3 text-xs bg-surface-alt border-none rounded-lg placeholder:text-text-muted focus:ring-2 focus:ring-accent/10 transition-all outline-none"
              />
            </div>
            {/* Status filter */}
            <select
              value={filterStatus}
              onChange={(e) => { setFilterStatus(e.target.value); setPage(0); }}
              aria-label="Filter by status"
              className="h-8 px-2 text-xs bg-surface-alt border-none rounded-lg text-text-secondary focus:ring-2 focus:ring-accent/10 transition-all outline-none cursor-pointer"
            >
              <option value="">All Statuses</option>
              {STATUSES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
            {/* Category filter */}
            <select
              value={filterCategory}
              onChange={(e) => { setFilterCategory(e.target.value); setPage(0); }}
              aria-label="Filter by category"
              className="h-8 px-2 text-xs bg-surface-alt border-none rounded-lg text-text-secondary focus:ring-2 focus:ring-accent/10 transition-all outline-none cursor-pointer"
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-14 h-14 bg-surface-alt rounded-xl flex items-center justify-center mx-auto mb-3">
              <DocIcon />
            </div>
            <p className="text-sm text-text-secondary font-medium">No documents found</p>
            <p className="text-xs text-text-muted mt-1">Upload a document to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-light">
                  <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3">Document</th>
                  <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3">Category</th>
                  <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3">Status</th>
                  <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3">Uploaded By</th>
                  <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3">Date</th>
                  <th className="text-right text-xs font-semibold text-text-muted uppercase tracking-wider px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-light">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-surface-alt/50 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${getFileTypeStyle(doc.file_type)}`}>
                          <span className="text-[10px] font-bold">{doc.file_type}</span>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-text-primary">{doc.name}</p>
                          <p className="text-xs text-text-muted">{formatFileSize(doc.file_size)}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-xs font-medium text-text-secondary bg-surface-alt px-2.5 py-1 rounded-md">
                        {categoryLabel(doc.category)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(doc.status)}`}>
                        {statusLabel(doc.status)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-sm text-text-secondary">{doc.uploaded_by_name || "—"}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-sm text-text-muted">{formatDate(doc.created_at)}</span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleDownload(doc)}
                          className="w-8 h-8 inline-flex items-center justify-center rounded-lg text-text-muted hover:text-accent hover:bg-accent/5 transition-colors"
                          title="Download"
                          aria-label="Download"
                        >
                          <DownloadIcon />
                        </button>
                        <button
                          onClick={() => openEdit(doc)}
                          className="w-8 h-8 inline-flex items-center justify-center rounded-lg text-text-muted hover:text-blue-600 hover:bg-blue-50 transition-colors"
                          title="Edit"
                          aria-label="Edit"
                        >
                          <EditIcon />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(doc)}
                          className="w-8 h-8 inline-flex items-center justify-center rounded-lg text-text-muted hover:text-danger hover:bg-red-50 transition-colors"
                          title="Delete"
                          aria-label="Delete"
                        >
                          <TrashIcon />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 0 && (
          <div className="px-5 py-3.5 border-t border-border-light flex items-center justify-between">
            <p className="text-xs text-text-muted">
              Showing {documents.length} of {total.toLocaleString()} documents
            </p>
            <div className="flex items-center gap-1">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                aria-label="Previous page"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                const start = Math.max(0, Math.min(page - 2, totalPages - 5));
                const pageNum = start + i;
                if (pageNum >= totalPages) return null;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs transition-colors ${
                      pageNum === page
                        ? "bg-accent text-white font-medium"
                        : "text-text-secondary hover:bg-surface-alt"
                    }`}
                  >
                    {pageNum + 1}
                  </button>
                );
              })}
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                aria-label="Next page"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Upload Modal ──────────────────────────────────────────────────── */}
      <Modal open={uploadOpen} onClose={resetUploadForm} title="Upload Document">
        <div className="space-y-4">
          {/* File picker */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">File{uploadFiles.length > 1 ? "s" : ""}</label>
            {uploadFiles.length > 0 ? (
              <div className="space-y-2">
                {uploadFiles.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 bg-surface-alt rounded-lg px-3 py-2 text-xs text-text-secondary">
                    <span className="truncate flex-1">{f.name}</span>
                    <span className="text-text-muted shrink-0">{formatFileSize(f.size)}</span>
                    <button
                      onClick={() => setUploadFiles((prev) => prev.filter((_, j) => j !== i))}
                      className="text-text-muted hover:text-danger transition-colors"
                      aria-label="Remove file"
                    >
                      <XIcon />
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs text-accent hover:underline"
                >
                  + Add more files
                </button>
              </div>
            ) : (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full h-20 border-2 border-dashed border-border rounded-lg flex items-center justify-center text-sm text-text-muted hover:border-accent/30 transition-all"
              >
                Click to select files
              </button>
            )}
          </div>

          {/* Name */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Document Name (optional)</label>
            <input
              type="text"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              placeholder="Uses filename if empty"
              className={inputClass}
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Category</label>
            <select value={uploadCategory} onChange={(e) => setUploadCategory(e.target.value)} aria-label="Category" className={selectClass + " w-full"}>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Description (optional)</label>
            <textarea
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              rows={3}
              placeholder="Brief description of this document..."
              className={textareaClass}
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Tags (optional)</label>
            <input
              type="text"
              value={uploadTags}
              onChange={(e) => setUploadTags(e.target.value)}
              placeholder="Comma-separated: compliance, q4, 2026"
              className={inputClass}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={resetUploadForm} className="h-9 px-4 text-sm text-text-secondary hover:bg-surface-alt rounded-lg transition-colors">
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={uploadFiles.length === 0 || uploading}
              className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {uploading && <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              {uploading ? "Uploading..." : `Upload ${uploadFiles.length > 0 ? `(${uploadFiles.length})` : ""}`}
            </button>
          </div>
        </div>
      </Modal>

      {/* ── Edit Modal ────────────────────────────────────────────────────── */}
      <Modal open={!!editDoc} onClose={() => setEditDoc(null)} title="Edit Document">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Name</label>
            <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)} placeholder="Document name" className={inputClass} />
          </div>
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Status</label>
            <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)} aria-label="Status" className={selectClass + " w-full"}>
              {STATUSES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Category</label>
            <select value={editCategory} onChange={(e) => setEditCategory(e.target.value)} aria-label="Category" className={selectClass + " w-full"}>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Description</label>
            <textarea value={editDescription} onChange={(e) => setEditDescription(e.target.value)} rows={3} placeholder="Description" className={textareaClass} />
          </div>
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Tags</label>
            <input type="text" value={editTags} onChange={(e) => setEditTags(e.target.value)} placeholder="Comma-separated" className={inputClass} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={() => setEditDoc(null)} className="h-9 px-4 text-sm text-text-secondary hover:bg-surface-alt rounded-lg transition-colors">
              Cancel
            </button>
            <button
              onClick={handleUpdate}
              disabled={saving}
              className="h-9 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {saving && <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </Modal>

      {/* ── Delete Confirmation ───────────────────────────────────────────── */}
      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Document">
        <div>
          <p className="text-sm text-text-secondary mb-1">Are you sure you want to delete this document?</p>
          <p className="text-sm font-medium text-text-primary mb-4">{deleteTarget?.name}</p>
          <p className="text-xs text-text-muted mb-6">This action cannot be undone. The file will be permanently removed.</p>
          <div className="flex justify-end gap-3">
            <button onClick={() => setDeleteTarget(null)} className="h-9 px-4 text-sm text-text-secondary hover:bg-surface-alt rounded-lg transition-colors">
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="h-9 px-4 bg-danger hover:bg-red-600 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {deleting && <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              {deleting ? "Deleting..." : "Delete"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
