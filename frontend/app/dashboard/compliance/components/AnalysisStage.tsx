"use client";

import React from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceSession, ComplianceResultItem } from "@/types/compliance";

interface AnalysisProgress {
  total_questions: number;
  completed_questions: number;
  phase: string;
  percentage: number;
}

interface AnalysisStageProps {
  theme: ComplianceTheme;
  session: ComplianceSession;
  progress: AnalysisProgress | null;
  analysisRunning: boolean;
  analysisError: string | null;
  results: ComplianceResultItem[];
  onStartAnalysis: () => void;
  onSkipToResults: () => void;
}

export default function AnalysisStage({
  theme,
  session,
  progress,
  analysisRunning,
  analysisError,
  results,
  onStartAnalysis,
  onSkipToResults,
}: AnalysisStageProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted } = theme;
  const pct = progress?.percentage ?? 0;

  return (
    <div className="flex flex-col items-center justify-center h-full p-6">
      <div className={`${surface} border ${border} rounded-xl p-8 text-center max-w-lg w-full`}>
        {/* Spinner or checkmark */}
        {analysisRunning ? (
          <div className="inline-block animate-spin mb-4">
            <svg className="w-10 h-10 text-[#1f6feb]" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : analysisError ? (
          <div className="mb-4">
            <svg className="w-10 h-10 text-red-400 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
        ) : (
          <div className="mb-4">
            <svg className="w-10 h-10 text-[#1f6feb] mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
        )}

        <h3 className={`text-lg font-semibold ${textPrimary} mb-2`}>
          {analysisRunning ? "Compliance Analysis in Progress" : analysisError ? "Analysis Failed" : "Ready to Analyze"}
        </h3>

        {/* Progress bar */}
        {analysisRunning && progress && (
          <div className="mb-4">
            <div className="flex justify-between text-xs mb-1">
              <span className={textSecondary}>{progress.phase}</span>
              <span className={textMuted}>{progress.completed_questions}/{progress.total_questions}</span>
            </div>
            <div className={`w-full h-2 ${surfaceAlt} rounded-full overflow-hidden`}>
              <div
                className="progress-bar h-full bg-[#1f6feb] rounded-full transition-all duration-300"
                {...{ style: { "--progress": pct } as React.CSSProperties }}
              />
            </div>
            <p className={`text-xs ${textMuted} mt-2`}>{Math.round(pct)}% complete</p>
          </div>
        )}

        {/* Live results counter */}
        {analysisRunning && results.length > 0 && (
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className={`${surfaceAlt} rounded-lg p-2`}>
              <p className="text-lg font-bold text-emerald-400">{results.filter(r => r.status === "YES").length}</p>
              <p className={`text-[10px] ${textMuted}`}>Compliant</p>
            </div>
            <div className={`${surfaceAlt} rounded-lg p-2`}>
              <p className="text-lg font-bold text-red-400">{results.filter(r => r.status === "NO").length}</p>
              <p className={`text-[10px] ${textMuted}`}>Non-Compliant</p>
            </div>
            <div className={`${surfaceAlt} rounded-lg p-2`}>
              <p className="text-lg font-bold text-gray-400">{results.filter(r => r.status === "N/A").length}</p>
              <p className={`text-[10px] ${textMuted}`}>N/A</p>
            </div>
          </div>
        )}

        {analysisError && (
          <p className="text-sm text-red-400 mb-4">{analysisError}</p>
        )}

        <p className={`text-sm ${textSecondary} mb-4`}>
          {analysisRunning
            ? `Analyzing ${session.total_questions} questions across ${session.total_standards} standards...`
            : analysisError
            ? "You can retry the analysis."
            : `Ready to analyze ${session.total_questions} questions across ${session.total_standards} standards.`
          }
        </p>

        {!analysisRunning && (
          <div className="flex gap-3 justify-center">
            <button
              onClick={onStartAnalysis}
              className="px-6 py-2.5 bg-[#1f6feb] text-white text-sm font-medium rounded-lg hover:bg-[#1a5fd4] transition-colors"
            >
              {analysisError ? "Retry Analysis" : "Start Analysis"}
            </button>
            <button
              onClick={onSkipToResults}
              className={`px-4 py-2 text-xs ${textSecondary} border ${border} rounded-lg ${theme.hoverBg} transition-colors`}
            >
              Skip to Results
            </button>
          </div>
        )}

        <p className={`text-xs ${textMuted} mt-4`}>This may take several minutes for large document sets.</p>
      </div>
    </div>
  );
}
