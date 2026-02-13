export default function DashboardPage() {
  const stats = [
    {
      label: "Total Users",
      value: "1,284",
      change: "+12%",
      changeType: "positive" as const,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      ),
    },
    {
      label: "Documents Processed",
      value: "3,847",
      change: "+24%",
      changeType: "positive" as const,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
    },
    {
      label: "Active Workflows",
      value: "47",
      change: "+3",
      changeType: "neutral" as const,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      ),
    },
    {
      label: "Compliance Score",
      value: "94.2%",
      change: "+1.8%",
      changeType: "positive" as const,
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      ),
    },
  ];

  const recentActivity = [
    { action: "Document uploaded", detail: "Q4 Compliance Report.pdf", user: "Sarah Chen", time: "2 min ago", type: "document" },
    { action: "Workflow completed", detail: "Annual Audit Review", user: "System", time: "15 min ago", type: "workflow" },
    { action: "User added", detail: "mark.wilson@technsure.com", user: "John Doe", time: "1 hour ago", type: "user" },
    { action: "Document reviewed", detail: "Insurance Policy Amendment", user: "Lisa Park", time: "2 hours ago", type: "document" },
    { action: "Workflow started", detail: "Regulatory Filing Q1", user: "David Kim", time: "3 hours ago", type: "workflow" },
    { action: "Compliance alert", detail: "New regulation update detected", user: "System", time: "5 hours ago", type: "alert" },
  ];

  return (
    <div>
      {/* Page header */}
      <div className="mb-8 animate-fade-in">
        <h1 className="text-2xl text-text-primary font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-text-secondary mt-1">Overview of your regulatory compliance platform</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className={`bg-surface rounded-xl border border-border p-5 hover:shadow-(--shadow-md) transition-shadow duration-200 animate-fade-in-up stagger-${i + 1}`}
          >
            <div className="flex items-start justify-between mb-4">
              <span className="text-text-muted">{stat.icon}</span>
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  stat.changeType === "positive"
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-blue-50 text-blue-600"
                }`}
              >
                {stat.change}
              </span>
            </div>
            <p className="text-2xl font-semibold text-text-primary tracking-tight">{stat.value}</p>
            <p className="text-sm text-text-secondary mt-0.5">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="xl:col-span-2 bg-surface rounded-xl border border-border animate-fade-in-up stagger-5">
          <div className="px-5 py-4 border-b border-border-light flex items-center justify-between">
            <h2 className="text-sm font-semibold text-text-primary">Recent Activity</h2>
            <button className="text-xs text-accent hover:text-accent-light font-medium transition-colors">
              View all
            </button>
          </div>
          <div className="divide-y divide-border-light">
            {recentActivity.map((item, i) => (
              <div key={i} className="px-5 py-3.5 flex items-center gap-4 hover:bg-surface-alt/50 transition-colors">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                    item.type === "document"
                      ? "bg-blue-50 text-blue-500"
                      : item.type === "workflow"
                      ? "bg-emerald-50 text-emerald-500"
                      : item.type === "user"
                      ? "bg-violet-50 text-violet-500"
                      : "bg-amber-50 text-amber-500"
                  }`}
                >
                  {item.type === "document" ? (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  ) : item.type === "workflow" ? (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                    </svg>
                  ) : item.type === "user" ? (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                  ) : (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                      <line x1="12" y1="9" x2="12" y2="13" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-primary font-medium">{item.action}</p>
                  <p className="text-xs text-text-muted truncate">{item.detail}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-text-muted">{item.time}</p>
                  <p className="text-xs text-text-secondary">{item.user}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Compliance Overview */}
        <div className="bg-surface rounded-xl border border-border animate-fade-in-up stagger-6">
          <div className="px-5 py-4 border-b border-border-light">
            <h2 className="text-sm font-semibold text-text-primary">Compliance Status</h2>
          </div>
          <div className="p-5 space-y-5">
            {[
              { label: "Regulatory Filings", progress: 92, color: "bg-emerald-500" },
              { label: "Document Reviews", progress: 78, color: "bg-blue-500" },
              { label: "Policy Updates", progress: 65, color: "bg-amber-500" },
              { label: "Audit Readiness", progress: 88, color: "bg-violet-500" },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-text-secondary">{item.label}</span>
                  <span className="text-sm font-semibold text-text-primary">{item.progress}%</span>
                </div>
                <div className="h-2 bg-surface-alt rounded-full overflow-hidden">
                  <progress
                    className={`w-full h-2 ${item.color === 'bg-amber-500' ? 'accent-amber-500' : item.color === 'bg-violet-500' ? 'accent-violet-500' : item.color === 'bg-emerald-500' ? 'accent-emerald-500' : 'accent-blue-500'}`}
                    value={item.progress}
                    max={100}
                  />
                </div>
              </div>
            ))}

            <div className="pt-3 border-t border-border-light">
              <div className="flex items-center gap-2 text-sm text-text-secondary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-accent">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                Last updated: Today, 2:45 PM
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
