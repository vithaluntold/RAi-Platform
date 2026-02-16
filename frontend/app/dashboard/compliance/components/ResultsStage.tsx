"use client";

import React, { useState } from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceSession, ComplianceResultItem } from "@/types/compliance";

type ResultFilter = "all" | "YES" | "NO" | "N/A" | "ERROR";

const STATUS_COLOR_MAP: Record<string, string> = {
  YES: "text-emerald-400 bg-emerald-600/20 border-emerald-600/30",
  NO: "text-red-400 bg-red-600/20 border-red-600/30",
  "N/A": "text-gray-400 bg-gray-600/20 border-gray-600/30",
  ERROR: "text-orange-400 bg-orange-600/20 border-orange-600/30",
};

const STATUS_LABEL_MAP: Record<string, string> = {
  YES: "COMPLIANT",
  NO: "NON-COMPLIANT",
  "N/A": "NOT APPLICABLE",
};

function statusColor(s: string): string {
  return STATUS_COLOR_MAP[s] || "text-blue-400 bg-blue-600/20 border-blue-600/30";
}

function statusLabel(s: string): string {
  return STATUS_LABEL_MAP[s] || s;
}

interface ResultsStageProps {
  theme: ComplianceTheme;
  session: ComplianceSession;
  results: ComplianceResultItem[];
  loadingResults: boolean;
  onReAnalyze: (questionIds: string[]) => void;
  onOverride: (result: ComplianceResultItem) => void;
  onExportCSV: () => void;
}

export default function ResultsStage({
  theme,
  session,
  results,
  loadingResults,
  onReAnalyze,
  onOverride,
  onExportCSV,
}: ResultsStageProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted, hoverBg, inputBg } = theme;

  const [resultFilter, setResultFilter] = useState<ResultFilter>("all");
  const [resultStandardFilter, setResultStandardFilter] = useState<string>("all");
  const [expandedResult, setExpandedResult] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"list" | "evidence">("list");

  const filteredResults = results.filter((r) => {
    if (resultFilter !== "all" && r.status !== resultFilter) return false;
    if (resultStandardFilter !== "all" && r.standard !== resultStandardFilter) return false;
    return true;
  });

  const standards = [...new Set(results.map((r) => r.standard))].sort();

  return (
    <div className="p-6 space-y-4 h-full overflow-y-auto">
      {/* Summary cards */}
      <div className={`${surface} border ${border} rounded-xl p-5`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold ${textPrimary}`}>Compliance Results</h3>
          <button
            onClick={onExportCSV}
            disabled={results.length === 0}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg border ${border} ${textSecondary} ${hoverBg} transition-colors disabled:opacity-40`}
          >
            Export CSV
          </button>
        </div>

        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className={`${surfaceAlt} rounded-lg p-3 text-center`}>
            <p className="text-2xl font-bold text-emerald-400">{session.compliant_count || 0}</p>
            <p className={`text-[10px] ${textMuted} mt-1`}>Compliant</p>
          </div>
          <div className={`${surfaceAlt} rounded-lg p-3 text-center`}>
            <p className="text-2xl font-bold text-red-400">{session.non_compliant_count || 0}</p>
            <p className={`text-[10px] ${textMuted} mt-1`}>Non-Compliant</p>
          </div>
          <div className={`${surfaceAlt} rounded-lg p-3 text-center`}>
            <p className="text-2xl font-bold text-gray-400">{session.not_applicable_count || 0}</p>
            <p className={`text-[10px] ${textMuted} mt-1`}>N/A</p>
          </div>
          <div className={`${surfaceAlt} rounded-lg p-3 text-center`}>
            <p className="text-2xl font-bold text-[#1f6feb]">{session.compliance_score ?? "—"}%</p>
            <p className={`text-[10px] ${textMuted} mt-1`}>Score</p>
          </div>
        </div>
      </div>

      {/* Tabs + Filter bar */}
      <div className={`${surface} border ${border} rounded-xl p-3`}>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Tabs */}
          <div className="flex gap-1 mr-3">
            <button
              onClick={() => setActiveTab("list")}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                activeTab === "list"
                  ? "bg-[#1f6feb]/20 text-[#1f6feb] border border-[#1f6feb]/40"
                  : `${textSecondary} border border-transparent ${hoverBg}`
              }`}
            >
              Results List
            </button>
            <button
              onClick={() => setActiveTab("evidence")}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                activeTab === "evidence"
                  ? "bg-[#1f6feb]/20 text-[#1f6feb] border border-[#1f6feb]/40"
                  : `${textSecondary} border border-transparent ${hoverBg}`
              }`}
            >
              Evidence Table
            </button>
          </div>

          <span className={`text-xs font-medium ${textMuted} shrink-0`}>Filter:</span>
          {(["all", "YES", "NO", "N/A", "ERROR"] as ResultFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => setResultFilter(f)}
              className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
                resultFilter === f
                  ? "bg-[#1f6feb]/20 text-[#1f6feb] border-[#1f6feb]/40"
                  : `${textSecondary} border-transparent ${hoverBg}`
              }`}
            >
              {f === "all" ? "All" : statusLabel(f)}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2">
            <select
              title="Filter by standard"
              value={resultStandardFilter}
              onChange={(e) => setResultStandardFilter(e.target.value)}
              className={`px-2 py-1 text-xs ${inputBg} ${textPrimary} border ${border} rounded-lg outline-none`}
            >
              <option value="all">All Standards</option>
              {standards.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <span className={`text-xs ${textMuted}`}>{filteredResults.length} results</span>
          </div>
        </div>
      </div>

      {/* Results content */}
      {activeTab === "list" ? (
        /* Results list */
        loadingResults ? (
          <div className={`text-center py-12 ${textMuted} text-sm`}>Loading results...</div>
        ) : filteredResults.length === 0 ? (
          <div className={`text-center py-12 ${textMuted} text-sm`}>
            {results.length === 0 ? "No analysis results yet. Run analysis from Stage 6." : "No results match the current filters."}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredResults.map((r) => {
              const isExpanded = expandedResult === r.question_id;
              return (
                <div key={r.question_id} className={`${surface} border ${border} rounded-xl overflow-hidden`}>
                  <button
                    onClick={() => setExpandedResult(isExpanded ? null : r.question_id)}
                    className={`w-full text-left p-4 flex items-start gap-3 ${hoverBg} transition-colors`}
                  >
                    <span className={`shrink-0 px-2 py-0.5 text-[10px] font-bold rounded border ${statusColor(r.status)}`}>
                      {statusLabel(r.status)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${textPrimary} line-clamp-2`}>{r.question}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className={`text-[10px] ${textMuted}`}>{r.standard}</span>
                        {r.reference && <span className={`text-[10px] ${textMuted}`}>Ref: {r.reference}</span>}
                        <span className={`text-[10px] ${textMuted}`}>Confidence: {Math.round(r.confidence * 100)}%</span>
                      </div>
                    </div>
                    <svg className={`w-4 h-4 ${textMuted} shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>

                  {isExpanded && (
                    <div className={`px-4 pb-4 space-y-3 border-t ${border}`}>
                      {r.explanation && (
                        <div className="pt-3">
                          <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Explanation</p>
                          <p className={`text-sm ${textSecondary}`}>{r.explanation}</p>
                        </div>
                      )}
                      {r.evidence && (
                        <div>
                          <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Evidence</p>
                          <div className={`${surfaceAlt} rounded-lg p-3 text-xs ${textSecondary} whitespace-pre-wrap max-h-40 overflow-y-auto`}>
                            {r.evidence}
                          </div>
                        </div>
                      )}
                      {r.suggested_disclosure && (
                        <div>
                          <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Suggested Disclosure</p>
                          <div className={`${surfaceAlt} rounded-lg p-3 text-xs ${textSecondary} border-l-2 border-[#1f6feb]`}>
                            {r.suggested_disclosure}
                          </div>
                        </div>
                      )}
                      {r.context_used && (Array.isArray(r.context_used) ? r.context_used.length > 0 : r.context_used) && (
                        <div>
                          <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Context Used</p>
                          <div className={`${surfaceAlt} rounded-lg p-3 text-xs ${textSecondary} max-h-32 overflow-y-auto`}>
                            {Array.isArray(r.context_used) ? r.context_used.join("\n\n---\n\n") : r.context_used}
                          </div>
                        </div>
                      )}
                      {r.decision_tree_path && r.decision_tree_path.length > 0 && (
                        <div>
                          <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Decision Tree Path</p>
                          <div className="flex flex-wrap gap-1">
                            {r.decision_tree_path.map((step, i) => (
                              <span key={i} className={`text-[10px] px-1.5 py-0.5 rounded ${surfaceAlt} ${textMuted}`}>
                                {step}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {r.error && (
                        <div>
                          <p className="text-[10px] font-semibold text-red-400 uppercase tracking-wider mb-1">Error</p>
                          <p className="text-xs text-red-400">{r.error}</p>
                        </div>
                      )}
                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={() => onReAnalyze([r.question_id])}
                          className={`px-3 py-1.5 text-xs font-medium rounded-lg border ${border} ${textSecondary} ${hoverBg} transition-colors`}
                        >
                          Re-analyze
                        </button>
                        <button
                          onClick={() => onOverride(r)}
                          className={`px-3 py-1.5 text-xs font-medium rounded-lg border ${border} ${textSecondary} ${hoverBg} transition-colors`}
                        >
                          Override
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )
      ) : (
        /* Evidence Table tab */
        <div className={`${surface} border ${border} rounded-xl overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className={`${surfaceAlt} border-b ${border}`}>
                  <th className={`text-left px-3 py-2 ${textMuted} font-medium`}>Standard</th>
                  <th className={`text-left px-3 py-2 ${textMuted} font-medium`}>Question</th>
                  <th className={`text-left px-3 py-2 ${textMuted} font-medium`}>Status</th>
                  <th className={`text-left px-3 py-2 ${textMuted} font-medium`}>Evidence</th>
                  <th className={`text-left px-3 py-2 ${textMuted} font-medium`}>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filteredResults.map((r) => (
                  <tr key={r.question_id} className={`border-b ${border} ${hoverBg} transition-colors`}>
                    <td className={`px-3 py-2 ${textSecondary} whitespace-nowrap`}>{r.standard}</td>
                    <td className={`px-3 py-2 ${textPrimary} max-w-xs truncate`}>{r.question}</td>
                    <td className="px-3 py-2">
                      <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded border ${statusColor(r.status)}`}>
                        {statusLabel(r.status)}
                      </span>
                    </td>
                    <td className={`px-3 py-2 ${textSecondary} max-w-sm truncate`}>{r.evidence || "—"}</td>
                    <td className={`px-3 py-2 ${textMuted} whitespace-nowrap`}>{Math.round(r.confidence * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredResults.length === 0 && (
            <div className={`text-center py-8 ${textMuted} text-sm`}>No results to display.</div>
          )}
        </div>
      )}
    </div>
  );
}
