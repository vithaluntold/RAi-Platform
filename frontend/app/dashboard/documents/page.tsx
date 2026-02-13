export default function DocumentsPage() {
  const documents = [
    { id: 1, name: "Q4 Compliance Report", type: "PDF", size: "2.4 MB", status: "Reviewed", uploadedBy: "Sarah Chen", date: "Jan 15, 2026", category: "Compliance" },
    { id: 2, name: "Insurance Policy Amendment v3", type: "DOCX", size: "1.1 MB", status: "Pending Review", uploadedBy: "David Kim", date: "Jan 14, 2026", category: "Policy" },
    { id: 3, name: "Annual Audit Checklist", type: "XLSX", size: "845 KB", status: "Reviewed", uploadedBy: "Lisa Park", date: "Jan 13, 2026", category: "Audit" },
    { id: 4, name: "Regulatory Update - State Filing", type: "PDF", size: "3.2 MB", status: "In Review", uploadedBy: "Mark Wilson", date: "Jan 12, 2026", category: "Regulatory" },
    { id: 5, name: "Risk Assessment Framework", type: "PDF", size: "5.7 MB", status: "Reviewed", uploadedBy: "Emily Johnson", date: "Jan 11, 2026", category: "Risk" },
    { id: 6, name: "Claims Processing Guidelines", type: "PDF", size: "1.8 MB", status: "Pending Review", uploadedBy: "James Brown", date: "Jan 10, 2026", category: "Operations" },
    { id: 7, name: "Board Meeting Minutes", type: "DOCX", size: "420 KB", status: "Reviewed", uploadedBy: "Anna Martinez", date: "Jan 9, 2026", category: "Governance" },
    { id: 8, name: "IT Security Policy 2026", type: "PDF", size: "2.1 MB", status: "In Review", uploadedBy: "Robert Taylor", date: "Jan 8, 2026", category: "Security" },
  ];

  const getFileIcon = (type: string) => {
    const colors: Record<string, string> = {
      PDF: "bg-red-50 text-red-500",
      DOCX: "bg-blue-50 text-blue-500",
      XLSX: "bg-emerald-50 text-emerald-500",
    };
    return colors[type] || "bg-gray-50 text-gray-500";
  };

  const getStatusStyle = (status: string) => {
    switch (status) {
      case "Reviewed":
        return "bg-emerald-50 text-emerald-700";
      case "In Review":
        return "bg-blue-50 text-blue-700";
      case "Pending Review":
        return "bg-amber-50 text-amber-700";
      default:
        return "bg-gray-100 text-gray-500";
    }
  };

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <h1 className="text-2xl text-text-primary font-semibold tracking-tight">Documents</h1>
          <p className="text-sm text-text-secondary mt-1">Manage regulatory documents and filings</p>
        </div>
        <button className="h-10 px-4 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Upload Document
        </button>
      </div>

      {/* Upload drop zone */}
      <div className="border-2 border-dashed border-border rounded-xl p-8 mb-6 text-center hover:border-accent/30 hover:bg-accent/[0.02] transition-all cursor-pointer animate-fade-in-up stagger-1">
        <div className="w-12 h-12 bg-surface-alt rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-text-muted">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p className="text-sm text-text-secondary font-medium">Drag & drop files here, or click to browse</p>
        <p className="text-xs text-text-muted mt-1">Supports PDF, DOCX, XLSX up to 25MB</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6 animate-fade-in-up stagger-2">
        {[
          { label: "Total Documents", value: "3,847", icon: "all" },
          { label: "Pending Review", value: "124", icon: "pending" },
          { label: "Reviewed This Month", value: "456", icon: "reviewed" },
        ].map((stat) => (
          <div key={stat.label} className="bg-surface rounded-xl border border-border px-5 py-4 flex items-center gap-4">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              stat.icon === "all" ? "bg-blue-50 text-blue-500" :
              stat.icon === "pending" ? "bg-amber-50 text-amber-500" :
              "bg-emerald-50 text-emerald-500"
            }`}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <div>
              <p className="text-xl font-semibold text-text-primary">{stat.value}</p>
              <p className="text-xs text-text-muted">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Document list */}
      <div className="bg-surface rounded-xl border border-border overflow-hidden animate-fade-in-up stagger-3">
        <div className="px-5 py-4 border-b border-border-light flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">All Documents</h2>
          <div className="flex items-center gap-2">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="text"
                placeholder="Search documents..."
                className="h-8 w-48 pl-8 pr-3 text-xs bg-surface-alt border-none rounded-lg placeholder:text-text-muted focus:ring-2 focus:ring-accent/10 transition-all"
              />
            </div>
          </div>
        </div>

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
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${getFileIcon(doc.type)}`}>
                        <span className="text-[10px] font-bold">{doc.type}</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-text-primary">{doc.name}</p>
                        <p className="text-xs text-text-muted">{doc.size}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-xs font-medium text-text-secondary bg-surface-alt px-2.5 py-1 rounded-md">{doc.category}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(doc.status)}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-sm text-text-secondary">{doc.uploadedBy}</span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-sm text-text-muted">{doc.date}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button className="w-8 h-8 inline-flex items-center justify-center rounded-lg text-text-muted hover:text-accent hover:bg-accent/5 transition-colors" title="Download">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="7 10 12 15 17 10" />
                          <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                      </button>
                      <button className="w-8 h-8 inline-flex items-center justify-center rounded-lg text-text-muted hover:text-text-secondary hover:bg-surface-alt transition-colors" title="More">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="1" />
                          <circle cx="19" cy="12" r="1" />
                          <circle cx="5" cy="12" r="1" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-5 py-3.5 border-t border-border-light flex items-center justify-between">
          <p className="text-xs text-text-muted">Showing 8 of 3,847 documents</p>
          <div className="flex items-center gap-1">
            <button className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </button>
            <button className="w-8 h-8 flex items-center justify-center rounded-lg bg-accent text-white text-xs font-medium">1</button>
            <button className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-alt text-xs transition-colors">2</button>
            <button className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-alt text-xs transition-colors">3</button>
            <button className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:bg-surface-alt transition-colors">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
