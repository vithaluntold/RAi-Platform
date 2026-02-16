"use client";

import { useState, useEffect, useCallback } from "react";
import { apiCall } from "@/lib";
import { API_ENDPOINTS, API_BASE_URL, STORAGE_KEYS } from "@/lib/api-config";
import type {
  ComplianceSession,
  ComplianceSessionListItem,
  ComplianceResultItem,
  StandardsSummary,
} from "@/types/compliance";
import { useComplianceStateMachine } from "@/hooks/useComplianceStateMachine";
import {
  UploadStage,
  MetadataStage,
  FrameworkStage,
  StandardsStage,
  ContextPreviewStage,
  AnalysisStage,
  ResultsStage,
  SessionSidebar,
  WorkflowStepper,
  OverrideModal,
  ChatbotFAB,
  useComplianceTheme,
} from "./components";

/* ─── Types (local only) ─────────────────────────────────────────── */

interface AnalysisProgress {
  total_questions: number;
  completed_questions: number;
  phase: string;
  percentage: number;
}

/* ─── Status display ─────────────────────────────────────────────── */

const STATUS_LABELS: Record<string, string> = {
  awaiting_upload: "AWAITING UPLOAD",
  processing: "PROCESSING",
  metadata_review: "METADATA REVIEW",
  framework_selection: "FRAMEWORK SELECTION",
  standards_selection: "STANDARDS SELECTION",
  context_preview: "CONTEXT PREVIEW",
  analyzing: "ANALYZING",
  completed: "COMPLETED",
  failed: "FAILED",
};

const STATUS_COLORS: Record<string, string> = {
  awaiting_upload: "bg-yellow-600/20 text-yellow-400 border-yellow-600/30",
  processing: "bg-blue-600/20 text-blue-400 border-blue-600/30",
  metadata_review: "bg-purple-600/20 text-purple-400 border-purple-600/30",
  framework_selection: "bg-indigo-600/20 text-indigo-400 border-indigo-600/30",
  standards_selection: "bg-cyan-600/20 text-cyan-400 border-cyan-600/30",
  context_preview: "bg-teal-600/20 text-teal-400 border-teal-600/30",
  analyzing: "bg-orange-600/20 text-orange-400 border-orange-600/30",
  completed: "bg-emerald-600/20 text-emerald-400 border-emerald-600/30",
  failed: "bg-red-600/20 text-red-400 border-red-600/30",
};

/* ─── Component ──────────────────────────────────────────────────── */

export default function CompliancePage() {
  // Sessions
  const [sessions, setSessions] = useState<ComplianceSessionListItem[]>([]);
  const [activeSession, setActiveSession] = useState<ComplianceSession | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);

  // New session modal
  const [showNewSession, setShowNewSession] = useState(false);
  const [newClientName, setNewClientName] = useState("");
  const [newFramework, setNewFramework] = useState("IFRS");
  const [creating, setCreating] = useState(false);

  // File upload
  const [fsFile, setFsFile] = useState<File | null>(null);
  const [notesFile, setNotesFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Standards
  const [standardsSummary, setStandardsSummary] = useState<StandardsSummary | null>(null);
  const [selectedStandards, setSelectedStandards] = useState<Set<string>>(new Set());

  // Chat
  const [chatInput, setChatInput] = useState("");

  // Analysis state
  const [analysisProgress, setAnalysisProgress] = useState<AnalysisProgress | null>(null);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [extractingMetadata, setExtractingMetadata] = useState(false);

  // Results state
  const [results, setResults] = useState<ComplianceResultItem[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);

  // Error toast
  const [errorToast, setErrorToast] = useState<string | null>(null);

  // Override modal
  const [overrideTarget, setOverrideTarget] = useState<ComplianceResultItem | null>(null);
  const [overrideStatus, setOverrideStatus] = useState<string>("YES");
  const [overrideReason, setOverrideReason] = useState("");

  // Dark mode
  const [darkMode, setDarkMode] = useState(true);
  const theme = useComplianceTheme(darkMode);

  // State machine — provides stage validation guards
  const stateMachine = useComplianceStateMachine(activeSession);

  /* ─── API Calls ──────────────────────────────────────────────────── */

  const loadSessions = useCallback(async () => {
    try {
      setLoadingSessions(true);
      const data = await apiCall<ComplianceSessionListItem[]>(API_ENDPOINTS.COMPLIANCE_SESSIONS);
      setSessions(data);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  const loadSession = useCallback(async (id: string) => {
    try {
      const data = await apiCall<ComplianceSession>(API_ENDPOINTS.COMPLIANCE_SESSION(id));
      setActiveSession(data);
      stateMachine.syncFromSession(data);
      if (data.selected_standards) {
        setSelectedStandards(new Set(data.selected_standards));
      }
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to load session");
    }
  }, [stateMachine]);

  const loadStandards = useCallback(async () => {
    try {
      const data = await apiCall<StandardsSummary>(API_ENDPOINTS.COMPLIANCE_STANDARDS);
      setStandardsSummary(data);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to load standards");
    }
  }, []);

  useEffect(() => {
    loadSessions();
    loadStandards();
  }, [loadSessions, loadStandards]);

  /* ─── Handlers ───────────────────────────────────────────────────── */

  const handleCreateSession = async () => {
    if (!newClientName.trim()) return;
    setCreating(true);
    try {
      const data = await apiCall<ComplianceSession>(API_ENDPOINTS.COMPLIANCE_SESSIONS, {
        method: "POST",
        body: JSON.stringify({ client_name: newClientName, framework: newFramework }),
      });
      setSessions((prev) => [data as ComplianceSessionListItem, ...prev]);
      setActiveSession(data);
      setNewClientName("");
      setShowNewSession(false);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION(id), { method: "DELETE" });
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSession?.id === id) setActiveSession(null);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to delete session");
    }
  };

  const handleUpload = async () => {
    if (!activeSession || (!fsFile && !notesFile)) return;
    setUploading(true);
    try {
      const formData = new FormData();
      if (fsFile) formData.append("financial_statements", fsFile);
      if (notesFile) formData.append("notes", notesFile);
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION_UPLOAD(activeSession.id), {
        method: "POST",
        body: formData,
      });
      setFsFile(null);
      setNotesFile(null);
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "File upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleStageAdvance = async (stage: number, status: string) => {
    if (!activeSession) return;
    // Validate transition via state machine
    if (!stateMachine.canGoTo(stage)) {
      const error = stateMachine.goTo(stage);
      if (error) { setErrorToast(error); return; }
    }
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION(activeSession.id), {
        method: "PATCH",
        body: JSON.stringify({ current_stage: stage, status }),
      });
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to advance stage");
    }
  };

  const handleSelectFramework = async (fw: string) => {
    if (!activeSession) return;
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION(activeSession.id), {
        method: "PATCH",
        body: JSON.stringify({ framework: fw, current_stage: 4, status: "standards_selection" }),
      });
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to select framework");
    }
  };

  const handleToggleStandard = (key: string) => {
    setSelectedStandards((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleSelectAllStandards = () => {
    if (!standardsSummary) return;
    const allKeys = standardsSummary.standards.map((s) => s.section.replace(" ", "_"));
    setSelectedStandards(new Set(allKeys));
  };

  const handleConfirmStandards = async () => {
    if (!activeSession) return;
    const selected = Array.from(selectedStandards);
    const totalQuestions = standardsSummary?.standards
      .filter((s) => selectedStandards.has(s.section.replace(" ", "_")))
      .reduce((sum, s) => sum + s.item_count, 0) || 0;
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION(activeSession.id), {
        method: "PATCH",
        body: JSON.stringify({
          selected_standards: selected,
          total_standards: selected.length,
          total_questions: totalQuestions,
          current_stage: 5,
          status: "context_preview",
        }),
      });
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to confirm standards");
    }
  };

  const handleSendMessage = async () => {
    if (!activeSession || !chatInput.trim()) return;
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION_MESSAGES(activeSession.id), {
        method: "POST",
        body: JSON.stringify({ content: chatInput }),
      });
      setChatInput("");
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to send message");
    }
  };

  const handleExtractMetadata = async () => {
    if (!activeSession) return;
    setExtractingMetadata(true);
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION_EXTRACT_METADATA(activeSession.id), { method: "POST" });
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to extract metadata");
    } finally {
      setExtractingMetadata(false);
    }
  };

  /* ─── Analysis ───────────────────────────────────────────────────── */

  const handleStartAnalysis = async () => {
    if (!activeSession) return;
    setAnalysisRunning(true);
    setAnalysisError(null);
    setResults([]);
    setAnalysisProgress({ total_questions: activeSession.total_questions, completed_questions: 0, phase: "Starting...", percentage: 0 });

    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION(activeSession.id), {
        method: "PATCH",
        body: JSON.stringify({ current_stage: 6, status: "analyzing" }),
      });
      await loadSession(activeSession.id);

      const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
      const url = `${API_BASE_URL}${API_ENDPOINTS.COMPLIANCE_SESSION_ANALYZE_STREAM(activeSession.id)}`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      });

      if (!response.ok) throw new Error(`Analysis failed: ${response.statusText}`);

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);
            if (event.type === "progress") setAnalysisProgress(event.data);
            else if (event.type === "result") setResults((prev) => [...prev, event.data]);
            else if (event.type === "complete") {
              setAnalysisProgress({
                total_questions: event.data.total || activeSession.total_questions,
                completed_questions: event.data.total || activeSession.total_questions,
                phase: "Complete",
                percentage: 100,
              });
            } else if (event.type === "error") setAnalysisError(event.data?.message || "Analysis error occurred");
          } catch {
            // skip invalid JSON lines
          }
        }
      }

      await loadSession(activeSession.id);
      setAnalysisRunning(false);
      await handleStageAdvance(7, "completed");
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : "Analysis failed");
      setAnalysisRunning(false);
      try {
        await loadSession(activeSession.id);
      } catch {
        try {
          await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION(activeSession.id), {
            method: "PATCH",
            body: JSON.stringify({ current_stage: 5, status: "context_preview" }),
          });
          await loadSession(activeSession.id);
        } catch {
          // last resort
        }
      }
    }
  };

  const handleLoadResults = useCallback(async () => {
    if (!activeSession) return;
    setLoadingResults(true);
    try {
      const url = API_ENDPOINTS.COMPLIANCE_SESSION_RESULTS(activeSession.id);
      const data = await apiCall<{ results: ComplianceResultItem[] }>(url);
      setResults(data.results || []);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Failed to load results");
    } finally {
      setLoadingResults(false);
    }
  }, [activeSession]);

  const handleReAnalyze = async (questionIds: string[]) => {
    if (!activeSession) return;
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION_REANALYZE(activeSession.id), {
        method: "POST",
        body: JSON.stringify({ question_ids: questionIds }),
      });
      await handleLoadResults();
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Re-analysis failed");
    }
  };

  const handleOverrideSubmit = async () => {
    if (!activeSession || !overrideTarget) return;
    try {
      await apiCall(API_ENDPOINTS.COMPLIANCE_SESSION_OVERRIDE(activeSession.id), {
        method: "POST",
        body: JSON.stringify({ question_id: overrideTarget.question_id, new_status: overrideStatus, reason: overrideReason }),
      });
      setOverrideTarget(null);
      setOverrideReason("");
      await handleLoadResults();
      await loadSession(activeSession.id);
    } catch (err) {
      setErrorToast(err instanceof Error ? err.message : "Override failed");
    }
  };

  const handleExportResults = () => {
    if (!results.length || !activeSession) return;
    const headers = ["Standard", "Section", "Reference", "Question", "Status", "Confidence", "Explanation", "Evidence", "Suggested Disclosure"];
    const rows = results.map((r) => [
      r.standard, r.section, r.reference, `"${r.question.replace(/"/g, '""')}"`,
      r.status, String(r.confidence), `"${(r.explanation || "").replace(/"/g, '""')}"`,
      `"${(r.evidence || "").replace(/"/g, '""')}"`, `"${(r.suggested_disclosure || "").replace(/"/g, '""')}"`,
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeSession.session_code}_compliance_results.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (activeSession?.current_stage === 7) handleLoadResults();
  }, [activeSession?.current_stage, activeSession?.id, handleLoadResults]);

  /* ─── Stage Dispatch ─────────────────────────────────────────────── */

  const renderStageContent = () => {
    if (!activeSession) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <div className={`text-center ${theme.textSecondary}`}>
            <svg className="mx-auto mb-4 w-16 h-16 opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            <p className="text-lg font-medium mb-2">No session selected</p>
            <p className="text-sm">Create a new session or select one from the left panel</p>
          </div>
        </div>
      );
    }

    switch (activeSession.current_stage) {
      case 1:
        return (
          <UploadStage
            theme={theme}
            session={activeSession}
            fsFile={fsFile}
            notesFile={notesFile}
            uploading={uploading}
            chatInput={chatInput}
            onSetFsFile={setFsFile}
            onSetNotesFile={setNotesFile}
            onUpload={handleUpload}
            onChatInputChange={setChatInput}
            onSendMessage={handleSendMessage}
          />
        );
      case 2:
        return (
          <MetadataStage
            theme={theme}
            session={activeSession}
            extractingMetadata={extractingMetadata}
            onExtractMetadata={handleExtractMetadata}
            onAdvance={() => handleStageAdvance(3, "framework_selection")}
          />
        );
      case 3:
        return (
          <FrameworkStage
            theme={theme}
            currentFramework={activeSession.framework}
            darkMode={darkMode}
            onSelectFramework={handleSelectFramework}
          />
        );
      case 4:
        return (
          <StandardsStage
            theme={theme}
            standardsSummary={standardsSummary}
            selectedStandards={selectedStandards}
            onToggleStandard={handleToggleStandard}
            onSelectAll={handleSelectAllStandards}
            onClearAll={() => setSelectedStandards(new Set())}
            onConfirm={handleConfirmStandards}
          />
        );
      case 5:
        return (
          <ContextPreviewStage
            theme={theme}
            session={activeSession}
            onStartAnalysis={() => handleStageAdvance(6, "analyzing")}
          />
        );
      case 6:
        return (
          <AnalysisStage
            theme={theme}
            session={activeSession}
            progress={analysisProgress}
            analysisRunning={analysisRunning}
            analysisError={analysisError}
            results={results}
            onStartAnalysis={handleStartAnalysis}
            onSkipToResults={() => handleStageAdvance(7, "completed")}
          />
        );
      case 7:
        return (
          <ResultsStage
            theme={theme}
            session={activeSession}
            results={results}
            loadingResults={loadingResults}
            onReAnalyze={handleReAnalyze}
            onOverride={(r) => { setOverrideTarget(r); setOverrideStatus(r.status === "YES" ? "NO" : "YES"); }}
            onExportCSV={handleExportResults}
          />
        );
      default:
        return (
          <UploadStage
            theme={theme}
            session={activeSession}
            fsFile={fsFile}
            notesFile={notesFile}
            uploading={uploading}
            chatInput={chatInput}
            onSetFsFile={setFsFile}
            onSetNotesFile={setNotesFile}
            onUpload={handleUpload}
            onChatInputChange={setChatInput}
            onSendMessage={handleSendMessage}
          />
        );
    }
  };

  /* ─── Main Layout ────────────────────────────────────────────────── */

  return (
    <div className={`-m-8 flex h-[calc(100vh-4rem)] ${theme.bg} ${theme.textPrimary} font-[Exo_2,sans-serif]`}>
      {/* Error toast */}
      {errorToast && (
        <div className="fixed top-4 left-1/2 z-50 -translate-x-1/2 flex items-center gap-3 rounded-lg border border-red-600/40 bg-red-950/90 px-5 py-3 text-sm text-red-200 shadow-lg backdrop-blur">
          <span>{errorToast}</span>
          <button onClick={() => setErrorToast(null)} className="ml-2 text-red-400 hover:text-red-200">&times;</button>
        </div>
      )}
      {/* Left Panel: Sessions */}
      <SessionSidebar
        theme={theme}
        sessions={sessions}
        activeSessionId={activeSession?.id || null}
        loadingSessions={loadingSessions}
        showNewSession={showNewSession}
        newClientName={newClientName}
        newFramework={newFramework}
        creating={creating}
        onSetShowNewSession={setShowNewSession}
        onSetNewClientName={setNewClientName}
        onSetNewFramework={setNewFramework}
        onCreateSession={handleCreateSession}
        onSelectSession={loadSession}
        onDeleteSession={handleDeleteSession}
      />

      {/* Center Panel: Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className={`h-14 ${theme.surface} border-b ${theme.border} flex items-center justify-between px-6 shrink-0`}>
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold text-emerald-400 tracking-wide">Intellexion</span>
            <span className={`text-sm font-semibold ${theme.textPrimary}`}>Compliance Analysis</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              title="Toggle theme"
              onClick={() => setDarkMode(!darkMode)}
              className={`w-8 h-8 rounded-lg flex items-center justify-center ${theme.textSecondary} ${theme.hoverBg} transition-colors`}
            >
              {darkMode ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
              )}
            </button>
            {activeSession && (
              <span className={`text-xs px-3 py-1 rounded-full border font-medium ${STATUS_COLORS[activeSession.status] || "bg-gray-600/20 text-gray-400 border-gray-600/30"}`}>
                {STATUS_LABELS[activeSession.status] || activeSession.status.toUpperCase()}
              </span>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {renderStageContent()}
        </div>

        {/* Footer */}
        <div className={`h-10 border-t ${theme.border} flex items-center justify-center`}>
          <span className={`text-xs ${theme.textMuted} flex items-center gap-1.5`}>
            Powered by
            <span className="font-semibold text-[#1f6feb]">FinACEverse</span>
          </span>
        </div>
      </div>

      {/* Right Panel: Workflow Stages */}
      <WorkflowStepper
        theme={theme}
        currentStage={activeSession?.current_stage || 0}
        standardsSummary={standardsSummary}
      />

      {/* Override modal */}
      {overrideTarget && (
        <OverrideModal
          theme={theme}
          target={overrideTarget}
          overrideStatus={overrideStatus}
          overrideReason={overrideReason}
          onStatusChange={setOverrideStatus}
          onReasonChange={setOverrideReason}
          onConfirm={handleOverrideSubmit}
          onCancel={() => { setOverrideTarget(null); setOverrideReason(""); }}
        />
      )}

      {/* Chatbot FAB */}
      {activeSession && (
        <ChatbotFAB theme={theme} sessionId={activeSession.id} />
      )}
    </div>
  );
}
