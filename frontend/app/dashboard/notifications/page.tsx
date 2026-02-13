"use client";

import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

interface NotificationSettings {
  id: string;
  outlook_email: string;
  outlook_client_id: string;
  outlook_tenant_id: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface UserPreference {
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  email_enabled: boolean;
  in_app_enabled: boolean;
}

interface MyPreference {
  id: string;
  user_id: string;
  email_enabled: boolean;
  in_app_enabled: boolean;
  updated_at: string;
}

type ActiveTab = "my-preferences" | "admin-settings" | "user-management";

export default function NotificationsPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("my-preferences");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // My preferences
  const [myPref, setMyPref] = useState<MyPreference | null>(null);

  // Admin settings
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [settingsForm, setSettingsForm] = useState({
    outlook_email: "",
    outlook_client_id: "",
    outlook_client_secret: "",
    outlook_tenant_id: "",
    is_enabled: true,
  });
  const [settingsExist, setSettingsExist] = useState(false);

  // User management (admin)
  const [userPreferences, setUserPreferences] = useState<UserPreference[]>([]);

  const showMessage = (msg: string, type: "error" | "success") => {
    if (type === "error") {
      setError(msg);
      setSuccess("");
    } else {
      setSuccess(msg);
      setError("");
    }
    setTimeout(() => {
      setError("");
      setSuccess("");
    }, 4000);
  };

  // ─── Fetch My Preferences ───
  const fetchMyPreferences = useCallback(async () => {
    try {
      const data = await apiCall<MyPreference>(API_ENDPOINTS.NOTIFICATIONS_PREFERENCES);
      setMyPref(data);
    } catch {
      // May not exist yet — that's ok
    }
  }, []);

  const updateMyPreferences = async (field: "email_enabled" | "in_app_enabled", value: boolean) => {
    try {
      const data = await apiCall<MyPreference>(API_ENDPOINTS.NOTIFICATIONS_PREFERENCES, {
        method: "PATCH",
        body: JSON.stringify({ [field]: value }),
      });
      setMyPref(data);
      showMessage("Preferences updated", "success");
    } catch {
      showMessage("Failed to update preferences", "error");
    }
  };

  // ─── Fetch Admin Settings ───
  const fetchSettings = useCallback(async () => {
    try {
      const data = await apiCall<NotificationSettings>(API_ENDPOINTS.NOTIFICATIONS_SETTINGS);
      setSettings(data);
      setSettingsForm({
        outlook_email: data.outlook_email,
        outlook_client_id: data.outlook_client_id,
        outlook_client_secret: "",
        outlook_tenant_id: data.outlook_tenant_id,
        is_enabled: data.is_enabled,
      });
      setSettingsExist(true);
    } catch {
      setSettingsExist(false);
    }
  }, []);

  const saveSettings = async () => {
    setLoading(true);
    try {
      const method = settingsExist ? "PATCH" : "POST";
      const body = settingsExist
        ? JSON.stringify(Object.fromEntries(
            Object.entries(settingsForm).filter(([, v]) => v !== "" && v !== undefined)
          ))
        : JSON.stringify(settingsForm);

      const data = await apiCall<NotificationSettings>(API_ENDPOINTS.NOTIFICATIONS_SETTINGS, {
        method,
        body,
      });
      setSettings(data);
      setSettingsExist(true);
      showMessage("Outlook settings saved", "success");
    } catch {
      showMessage("Failed to save settings", "error");
    } finally {
      setLoading(false);
    }
  };

  // ─── Fetch User Preferences (Admin) ───
  const fetchUserPreferences = useCallback(async () => {
    try {
      const data = await apiCall<UserPreference[]>(API_ENDPOINTS.NOTIFICATIONS_ADMIN_USER_PREFERENCES);
      setUserPreferences(data);
    } catch {
      // Not admin or error
    }
  }, []);

  const toggleUserPreference = async (
    userId: string,
    field: "email_enabled" | "in_app_enabled",
    value: boolean
  ) => {
    try {
      await apiCall(API_ENDPOINTS.NOTIFICATIONS_ADMIN_USER_PREFERENCES, {
        method: "PATCH",
        body: JSON.stringify({ user_id: userId, [field]: value }),
      });
      setUserPreferences((prev) =>
        prev.map((u) => (u.user_id === userId ? { ...u, [field]: value } : u))
      );
      showMessage("User preference updated", "success");
    } catch {
      showMessage("Failed to update user preference", "error");
    }
  };

  useEffect(() => {
    if (activeTab === "my-preferences") fetchMyPreferences();
    else if (activeTab === "admin-settings") fetchSettings();
    else if (activeTab === "user-management") fetchUserPreferences();
  }, [activeTab, fetchMyPreferences, fetchSettings, fetchUserPreferences]);

  const tabs: { key: ActiveTab; label: string }[] = [
    { key: "my-preferences", label: "My Preferences" },
    { key: "admin-settings", label: "Outlook Email Settings" },
    { key: "user-management", label: "User Notification Control" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Notification Settings</h1>
        <p className="text-sm text-text-secondary mt-1">
          Manage your notification preferences and email configuration
        </p>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/10 border border-green-500/20 text-green-600 px-4 py-3 rounded-lg text-sm">
          {success}
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-surface-alt rounded-lg p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-surface text-text-primary shadow-sm"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "my-preferences" && (
        <div className="bg-surface border border-border rounded-xl p-6 space-y-6">
          <h2 className="text-lg font-semibold text-text-primary">My Notification Preferences</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-border/50">
              <div>
                <p className="text-sm font-medium text-text-primary">Email Notifications</p>
                <p className="text-xs text-text-secondary mt-0.5">
                  Receive email alerts when tasks, steps, or stages are completed
                </p>
              </div>
              <button
                onClick={() => updateMyPreferences("email_enabled", !(myPref?.email_enabled ?? true))}
                title="Toggle email notifications"
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  myPref?.email_enabled !== false ? "bg-accent" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    myPref?.email_enabled !== false ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium text-text-primary">In-App Notifications</p>
                <p className="text-xs text-text-secondary mt-0.5">
                  Show notification badges and alerts within the application
                </p>
              </div>
              <button
                onClick={() => updateMyPreferences("in_app_enabled", !(myPref?.in_app_enabled ?? true))}
                title="Toggle in-app notifications"
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  myPref?.in_app_enabled !== false ? "bg-accent" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    myPref?.in_app_enabled !== false ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === "admin-settings" && (
        <div className="bg-surface border border-border rounded-xl p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">Outlook Email Configuration</h2>
            <p className="text-xs text-text-secondary mt-1">
              Configure the Microsoft Outlook account used to send notification emails via Microsoft Graph API.
              Register an app in Azure AD to get Client ID, Client Secret, and Tenant ID.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                Outlook Email Address
              </label>
              <input
                type="email"
                value={settingsForm.outlook_email}
                onChange={(e) => setSettingsForm((prev) => ({ ...prev, outlook_email: e.target.value }))}
                placeholder="notifications@company.com"
                className="w-full px-3 py-2 text-sm bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                Tenant ID
              </label>
              <input
                type="text"
                value={settingsForm.outlook_tenant_id}
                onChange={(e) => setSettingsForm((prev) => ({ ...prev, outlook_tenant_id: e.target.value }))}
                placeholder="Azure AD Tenant ID"
                className="w-full px-3 py-2 text-sm bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                Client ID
              </label>
              <input
                type="text"
                value={settingsForm.outlook_client_id}
                onChange={(e) => setSettingsForm((prev) => ({ ...prev, outlook_client_id: e.target.value }))}
                placeholder="Azure AD Application Client ID"
                className="w-full px-3 py-2 text-sm bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                Client Secret
              </label>
              <input
                type="password"
                value={settingsForm.outlook_client_secret}
                onChange={(e) => setSettingsForm((prev) => ({ ...prev, outlook_client_secret: e.target.value }))}
                placeholder={settingsExist ? "••••••• (leave blank to keep)" : "Azure AD Client Secret"}
                className="w-full px-3 py-2 text-sm bg-surface-alt border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-accent/20 focus:border-accent outline-none transition-all"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-text-primary">Email Sending Enabled</label>
              <button
                onClick={() => setSettingsForm((prev) => ({ ...prev, is_enabled: !prev.is_enabled }))}
                title="Toggle email sending"
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settingsForm.is_enabled ? "bg-accent" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settingsForm.is_enabled ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
            <button
              onClick={saveSettings}
              disabled={loading}
              className="px-5 py-2 bg-accent text-white text-sm font-medium rounded-lg hover:bg-accent/90 disabled:opacity-50 transition-colors"
            >
              {loading ? "Saving..." : settingsExist ? "Update Settings" : "Save Settings"}
            </button>
          </div>

          {settings && (
            <div className="mt-4 pt-4 border-t border-border/50">
              <p className="text-xs text-text-muted">
                Status: {settings.is_enabled ? "Enabled" : "Disabled"} · Last updated: {new Date(settings.updated_at).toLocaleString()}
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === "user-management" && (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-border">
            <h2 className="text-lg font-semibold text-text-primary">User Notification Control</h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Enable or disable notifications for individual users
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-alt/50">
                  <th className="text-left px-6 py-3 text-xs font-semibold text-text-secondary uppercase tracking-wider">User</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-text-secondary uppercase tracking-wider">Email</th>
                  <th className="text-center px-6 py-3 text-xs font-semibold text-text-secondary uppercase tracking-wider">Email Notif</th>
                  <th className="text-center px-6 py-3 text-xs font-semibold text-text-secondary uppercase tracking-wider">In-App Notif</th>
                </tr>
              </thead>
              <tbody>
                {userPreferences.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-text-muted text-sm">
                      No users found
                    </td>
                  </tr>
                ) : (
                  userPreferences.map((u) => (
                    <tr key={u.user_id} className="border-t border-border/50 hover:bg-surface-alt/30 transition-colors">
                      <td className="px-6 py-3 text-sm text-text-primary font-medium">
                        {u.first_name} {u.last_name}
                      </td>
                      <td className="px-6 py-3 text-sm text-text-secondary">{u.email}</td>
                      <td className="px-6 py-3 text-center">
                        <button
                          onClick={() => toggleUserPreference(u.user_id, "email_enabled", !u.email_enabled)}
                          title="Toggle user email notifications"
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                            u.email_enabled ? "bg-accent" : "bg-gray-300"
                          }`}
                        >
                          <span
                            className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                              u.email_enabled ? "translate-x-4.5" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                      </td>
                      <td className="px-6 py-3 text-center">
                        <button
                          onClick={() => toggleUserPreference(u.user_id, "in_app_enabled", !u.in_app_enabled)}
                          title="Toggle user in-app notifications"
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                            u.in_app_enabled ? "bg-accent" : "bg-gray-300"
                          }`}
                        >
                          <span
                            className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                              u.in_app_enabled ? "translate-x-4.5" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
