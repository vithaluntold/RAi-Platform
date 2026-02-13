"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { getAuthToken, apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

interface NotificationItem {
  id: string;
  type: string;
  title: string;
  message: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

interface NotificationCount {
  unread_count: number;
  total_count: number;
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Notification state
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  const fetchNotificationCount = useCallback(async () => {
    try {
      const data = await apiCall<NotificationCount>(API_ENDPOINTS.NOTIFICATIONS_COUNT);
      setUnreadCount(data.unread_count);
    } catch {
      // Silently fail — user may not be authenticated yet
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await apiCall<NotificationItem[]>(API_ENDPOINTS.NOTIFICATIONS + "?limit=20");
      setNotifications(data);
    } catch {
      // Silently fail
    }
  }, []);

  const markAsRead = useCallback(async (ids: string[]) => {
    try {
      await apiCall(API_ENDPOINTS.NOTIFICATIONS_READ, {
        method: "PATCH",
        body: JSON.stringify({ notification_ids: ids }),
      });
      setNotifications((prev) =>
        prev.map((n) => (ids.includes(n.id) ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - ids.length));
    } catch {
      // Silently fail
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await apiCall(API_ENDPOINTS.NOTIFICATIONS_READ_ALL, { method: "PATCH" });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.push("/");
    } else {
      setIsAuthorized(true);
    }
    setIsLoading(false);
  }, [router]);

  // Poll notification count every 30 seconds
  useEffect(() => {
    if (!isAuthorized) return;
    fetchNotificationCount();
    const interval = setInterval(fetchNotificationCount, 30000);
    return () => clearInterval(interval);
  }, [isAuthorized, fetchNotificationCount]);

  // Fetch notifications when dropdown opens
  useEffect(() => {
    if (showNotifications) {
      fetchNotifications();
    }
  }, [showNotifications, fetchNotifications]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block animate-spin">
            <svg className="h-8 w-8 text-accent" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
          <p className="mt-4 text-text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar collapsed={sidebarCollapsed} />
      <main className={`flex-1 ${sidebarCollapsed ? "ml-18" : "ml-65"} transition-all duration-200`}>
        {/* Top bar */}
        <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-8 sticky top-0 z-20">
          <div className="flex items-center gap-2">
            {/* Sidebar toggle */}
            <button
              onClick={() => setSidebarCollapsed((prev) => !prev)}
              className="w-9 h-9 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-alt transition-colors"
              title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {sidebarCollapsed ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <line x1="9" y1="3" x2="9" y2="21" />
                  <polyline points="14 9 17 12 14 15" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <line x1="9" y1="3" x2="9" y2="21" />
                  <polyline points="16 9 13 12 16 15" />
                </svg>
              )}
            </button>

            {/* Search */}
            <div className="relative">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
                width="16"
                height="16"
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
                placeholder="Search..."
                className="h-9 w-64 pl-9 pr-3 text-sm text-text-primary bg-surface-alt border-none rounded-lg
                  placeholder:text-text-muted focus:ring-2 focus:ring-accent/10 transition-all"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Notification bell */}
            <div className="relative" ref={notifRef}>
              <button
                aria-label="View notifications"
                onClick={() => setShowNotifications((prev) => !prev)}
                className="relative w-9 h-9 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-alt transition-colors"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 min-w-4 h-4 flex items-center justify-center bg-danger text-white text-xs font-bold rounded-full px-1">
                    {unreadCount > 99 ? "99+" : unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 top-11 w-96 max-h-96 bg-surface border border-border rounded-xl shadow-lg z-50 flex flex-col overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                    <h3 className="text-sm font-semibold text-text-primary">Notifications</h3>
                    {unreadCount > 0 && (
                      <button
                        onClick={markAllAsRead}
                        className="text-xs text-accent hover:underline"
                      >
                        Mark all as read
                      </button>
                    )}
                  </div>
                  <div className="overflow-y-auto flex-1">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-8 text-center text-text-muted text-sm">
                        No notifications yet
                      </div>
                    ) : (
                      notifications.map((n) => (
                        <button
                          key={n.id}
                          onClick={() => {
                            if (!n.is_read) markAsRead([n.id]);
                            if (n.link) router.push(n.link);
                            setShowNotifications(false);
                          }}
                          className={`w-full text-left px-4 py-3 border-b border-border/50 hover:bg-surface-alt transition-colors ${
                            !n.is_read ? "bg-accent/5" : ""
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${!n.is_read ? "bg-accent" : "bg-transparent"}`} />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-text-primary truncate">{n.title}</p>
                              <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">{n.message}</p>
                              <p className="text-xs text-text-muted mt-1">
                                {formatTimeAgo(n.created_at)}
                              </p>
                            </div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="w-px h-6 bg-border" />

            {/* User */}
            <div className="flex items-center gap-2.5 cursor-pointer">
              <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent text-xs font-semibold">
                JD
              </div>
              <div className="hidden sm:block">
                <p className="text-sm text-text-primary font-medium leading-tight">John Doe</p>
                <p className="text-xs text-text-muted leading-tight">Admin</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
