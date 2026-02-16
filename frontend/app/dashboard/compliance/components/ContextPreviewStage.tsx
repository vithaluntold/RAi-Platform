"use client";

import React, { useState, useEffect, useCallback } from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceSession, ChunkPreviewItem, FinancialValidationResult } from "@/types/compliance";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

interface ContextPreviewStageProps {
  theme: ComplianceTheme;
  session: ComplianceSession;
  onStartAnalysis: () => void;
}

export default function ContextPreviewStage({
  theme,
  session,
  onStartAnalysis,
}: ContextPreviewStageProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted, hoverBg } = theme;

  const [chunks, setChunks] = useState<ChunkPreviewItem[]>([]);
  const [taxonomySummary, setTaxonomySummary] = useState<Record<string, number>>({});
  const [totalChunks, setTotalChunks] = useState(0);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<string>("all");

  const [validation, setValidation] = useState<FinancialValidationResult | null>(null);
  const [validating, setValidating] = useState(false);

  const loadChunks = useCallback(async () => {
    setLoadingChunks(true);
    try {
      const params = new URLSearchParams();
      if (selectedTaxonomy !== "all") params.set("taxonomy", selectedTaxonomy);
      const url = `${API_ENDPOINTS.COMPLIANCE_SESSION_CHUNKS(session.id)}?${params}`;
      const data = await apiCall<{ total_chunks: number; chunks: ChunkPreviewItem[]; taxonomy_summary: Record<string, number> }>(url);
      setChunks(data.chunks);
      setTotalChunks(data.total_chunks);
      setTaxonomySummary(data.taxonomy_summary);
    } catch {
      // silently fail
    } finally {
      setLoadingChunks(false);
    }
  }, [session.id, selectedTaxonomy]);

  useEffect(() => {
    loadChunks();
  }, [loadChunks]);

  const handleValidateFinancials = async () => {
    setValidating(true);
    try {
      const data = await apiCall<{ validation: FinancialValidationResult }>(
        API_ENDPOINTS.COMPLIANCE_SESSION_VALIDATE_FINANCIALS(session.id),
        { method: "POST" }
      );
      setValidation(data.validation);
    } catch {
      // silently fail
    } finally {
      setValidating(false);
    }
  };

  const taxonomyKeys = Object.keys(taxonomySummary).sort();

  return (
    <div className="p-6 space-y-6 h-full overflow-y-auto">
      {/* Summary card */}
      <div className={`${surface} border ${border} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textPrimary} mb-4`}>Context Preview</h3>
        <p className={`text-sm ${textSecondary} mb-6`}>
          Review the analysis configuration and document chunks before starting the compliance check.
        </p>
        <div className={`${surfaceAlt} rounded-lg p-4 space-y-3`}>
          <div className="flex justify-between">
            <span className={`text-sm ${textMuted}`}>Framework</span>
            <span className={`text-sm font-medium ${textPrimary}`}>{session.framework}</span>
          </div>
          <div className="flex justify-between">
            <span className={`text-sm ${textMuted}`}>Standards Selected</span>
            <span className={`text-sm font-medium ${textPrimary}`}>{session.total_standards}</span>
          </div>
          <div className="flex justify-between">
            <span className={`text-sm ${textMuted}`}>Total Questions</span>
            <span className={`text-sm font-medium ${textPrimary}`}>{session.total_questions}</span>
          </div>
          <div className="flex justify-between">
            <span className={`text-sm ${textMuted}`}>Documents</span>
            <span className={`text-sm font-medium ${textPrimary}`}>
              {session.financial_statements_filename}, {session.notes_filename}
            </span>
          </div>
        </div>
      </div>

      {/* Financial Validation card */}
      <div className={`${surface} border ${border} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h4 className={`text-sm font-semibold ${textPrimary}`}>Financial Statement Validation</h4>
          <button
            onClick={handleValidateFinancials}
            disabled={validating}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg border ${border} ${textSecondary} ${hoverBg} transition-colors disabled:opacity-50`}
          >
            {validating ? "Validating..." : validation ? "Re-validate" : "Validate Coverage"}
          </button>
        </div>

        {validation && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {validation.is_valid ? (
                <svg className="w-5 h-5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
              ) : (
                <svg className="w-5 h-5 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
              )}
              <span className={`text-sm font-medium ${validation.is_valid ? "text-emerald-400" : "text-amber-400"}`}>
                {validation.is_valid ? "All expected statements detected" : "Some statements may be missing"}
              </span>
              <span className={`text-xs ${textMuted} ml-auto`}>Confidence: {Math.round(validation.confidence * 100)}%</span>
            </div>

            {validation.detected_statements.length > 0 && (
              <div>
                <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Detected</p>
                <div className="flex flex-wrap gap-1">
                  {validation.detected_statements.map((s) => (
                    <span key={s} className="text-[10px] px-2 py-0.5 rounded bg-emerald-600/20 text-emerald-400 border border-emerald-600/30">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {validation.missing_statements.length > 0 && (
              <div>
                <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Missing</p>
                <div className="flex flex-wrap gap-1">
                  {validation.missing_statements.map((s) => (
                    <span key={s} className="text-[10px] px-2 py-0.5 rounded bg-red-600/20 text-red-400 border border-red-600/30">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {validation.warnings.length > 0 && (
              <div>
                <p className={`text-[10px] font-semibold ${textMuted} uppercase tracking-wider mb-1`}>Warnings</p>
                <ul className="space-y-1">
                  {validation.warnings.map((w, i) => (
                    <li key={i} className={`text-xs ${textSecondary} flex items-start gap-1`}>
                      <span className="text-amber-400 shrink-0">⚠</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chunk preview card */}
      <div className={`${surface} border ${border} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h4 className={`text-sm font-semibold ${textPrimary}`}>Document Chunks ({totalChunks})</h4>
          <div className="flex items-center gap-2">
            <select
              title="Filter by taxonomy"
              value={selectedTaxonomy}
              onChange={(e) => setSelectedTaxonomy(e.target.value)}
              className={`px-2 py-1 text-xs ${theme.inputBg} ${textPrimary} border ${border} rounded-lg outline-none`}
            >
              <option value="all">All Categories</option>
              {taxonomyKeys.map((t) => (
                <option key={t} value={t}>{t} ({taxonomySummary[t]})</option>
              ))}
            </select>
          </div>
        </div>

        {loadingChunks ? (
          <div className={`text-center py-8 ${textMuted} text-sm`}>Loading chunks...</div>
        ) : chunks.length === 0 ? (
          <div className={`text-center py-8 ${textMuted} text-sm`}>No chunks available.</div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {chunks.map((chunk) => (
              <div key={chunk.chunk_id} className={`${surfaceAlt} rounded-lg p-3 border ${border}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-medium ${textMuted}`}>Chunk #{chunk.chunk_index + 1}</span>
                  <div className="flex items-center gap-2">
                    {chunk.has_table && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-600/20 text-purple-400 border border-purple-600/30">Table</span>
                    )}
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-600/20 text-blue-400 border border-blue-600/30">{chunk.taxonomy}</span>
                    <span className={`text-[10px] ${textMuted}`}>{chunk.char_count} chars</span>
                  </div>
                </div>
                <p className={`text-xs ${textSecondary} line-clamp-3`}>{chunk.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Start analysis button */}
      <div className="flex justify-center pb-4">
        <button
          onClick={onStartAnalysis}
          className="px-8 py-3 bg-[#1f6feb] text-white text-sm font-medium rounded-lg hover:bg-[#1a5fd4] transition-colors"
        >
          Start Compliance Analysis
        </button>
      </div>
    </div>
  );
}
