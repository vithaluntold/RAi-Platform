"use client";

import React from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceSessionListItem } from "@/types/compliance";

const FRAMEWORKS = ["IFRS", "US GAAP", "Ind AS"];

interface SessionSidebarProps {
  theme: ComplianceTheme;
  sessions: ComplianceSessionListItem[];
  activeSessionId: string | null;
  loadingSessions: boolean;
  showNewSession: boolean;
  newClientName: string;
  newFramework: string;
  creating: boolean;
  onSetShowNewSession: (show: boolean) => void;
  onSetNewClientName: (name: string) => void;
  onSetNewFramework: (fw: string) => void;
  onCreateSession: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
}

function formatDate(d: string): string {
  const date = new Date(d);
  return date.toLocaleDateString("en-US", { month: "numeric", day: "numeric", year: "numeric" });
}

function truncateCode(code: string): string {
  return code.length > 18 ? code.slice(0, 18) + "..." : code;
}

export default function SessionSidebar({
  theme,
  sessions,
  activeSessionId,
  loadingSessions,
  showNewSession,
  newClientName,
  newFramework,
  creating,
  onSetShowNewSession,
  onSetNewClientName,
  onSetNewFramework,
  onCreateSession,
  onSelectSession,
  onDeleteSession,
}: SessionSidebarProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted, hoverBg, inputBg, activeBg } = theme;

  return (
    <div className={`w-65 shrink-0 ${surface} border-r ${border} flex flex-col`}>
      <div className="p-4">
        <h2 className={`text-sm font-semibold ${textPrimary} mb-3`}>Sessions</h2>
        <button
          onClick={() => onSetShowNewSession(true)}
          className="w-full py-2.5 bg-[#1f6feb] text-white text-sm font-medium rounded-lg hover:bg-[#1a5fd4] transition-colors flex items-center justify-center gap-2"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
          New Session
        </button>
      </div>

      {/* New session form */}
      {showNewSession && (
        <div className={`mx-4 mb-3 p-3 ${surfaceAlt} border ${border} rounded-lg`}>
          <input
            type="text"
            value={newClientName}
            onChange={(e) => onSetNewClientName(e.target.value)}
            placeholder="Client name"
            className={`w-full px-3 py-2 text-sm ${inputBg} ${textPrimary} border ${border} rounded-lg mb-2 outline-none focus:border-[#1f6feb]/50`}
          />
          <select
            title="Framework"
            value={newFramework}
            onChange={(e) => onSetNewFramework(e.target.value)}
            className={`w-full px-3 py-2 text-sm ${inputBg} ${textPrimary} border ${border} rounded-lg mb-3 outline-none`}
          >
            {FRAMEWORKS.map((fw) => (
              <option key={fw} value={fw}>{fw}</option>
            ))}
          </select>
          <div className="flex gap-2">
            <button
              onClick={onCreateSession}
              disabled={!newClientName.trim() || creating}
              className="flex-1 py-2 bg-[#1f6feb] text-white text-xs font-medium rounded-lg hover:bg-[#1a5fd4] disabled:opacity-50 transition-colors"
            >
              {creating ? "Creating..." : "Create"}
            </button>
            <button
              onClick={() => onSetShowNewSession(false)}
              className={`flex-1 py-2 ${surfaceAlt} ${textSecondary} text-xs font-medium rounded-lg border ${border} ${hoverBg} transition-colors`}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Session list */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1.5">
        {loadingSessions ? (
          <div className={`text-center py-8 ${textMuted} text-sm`}>Loading...</div>
        ) : sessions.length === 0 ? (
          <div className={`text-center py-8 ${textMuted} text-sm`}>No sessions yet</div>
        ) : (
          sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => onSelectSession(s.id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                activeSessionId === s.id
                  ? activeBg
                  : `border-transparent ${hoverBg}`
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <span className={`text-xs font-mono font-semibold ${textPrimary} truncate`}>
                  {truncateCode(s.session_code)}
                </span>
                <div className="flex items-center gap-1 shrink-0 ml-1">
                  <button
                    title="Delete session"
                    onClick={(e) => onDeleteSession(s.id, e)}
                    className={`w-5 h-5 rounded flex items-center justify-center ${textMuted} hover:text-red-400 transition-colors`}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6" /><path d="M14 11v6" /><path d="M9 6V4h6v2" /></svg>
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                  s.status === "completed"
                    ? "bg-emerald-600/20 text-emerald-400"
                    : s.status === "failed"
                    ? "bg-red-600/20 text-red-400"
                    : "bg-blue-600/20 text-blue-400"
                }`}>
                  {s.status === "awaiting_upload" ? "in progress" : s.status.replace(/_/g, " ")}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className={`text-xs ${textMuted} truncate`}>
                  {s.client_name.length > 10 ? s.client_name.slice(0, 10) + "..." : s.client_name}
                </span>
                <span className={`text-xs ${textMuted}`}>{formatDate(s.created_at)}</span>
              </div>
              <div className={`text-[10px] ${textMuted} mt-1`}>Framework: {s.framework}</div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
