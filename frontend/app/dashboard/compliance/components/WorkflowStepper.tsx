"use client";

import React from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { StandardsSummary } from "@/types/compliance";

const WORKFLOW_STAGES = [
  { id: 1, label: "Document Upload & Processing" },
  { id: 2, label: "Metadata Review" },
  { id: 3, label: "Framework Selection" },
  { id: 4, label: "Standards Selection" },
  { id: 5, label: "Context Preview" },
  { id: 6, label: "Compliance Analysis" },
  { id: 7, label: "Results Review" },
];

interface WorkflowStepperProps {
  theme: ComplianceTheme;
  currentStage: number;
  standardsSummary: StandardsSummary | null;
}

export default function WorkflowStepper({
  theme,
  currentStage,
  standardsSummary,
}: WorkflowStepperProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted } = theme;

  return (
    <div className={`w-70 shrink-0 ${surface} border-l ${border} flex flex-col`}>
      <div className={`p-4 border-b ${border}`}>
        <div className="flex items-center gap-2 mb-1">
          <svg className={textSecondary} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" /></svg>
          <h2 className={`text-sm font-semibold ${textPrimary}`}>Analysis &amp; Workflow</h2>
        </div>
      </div>

      <div className="p-4 space-y-1">
        <h3 className={`text-xs font-semibold ${textSecondary} uppercase tracking-wider mb-3`}>Workflow Stages</h3>
        {WORKFLOW_STAGES.map((stage) => {
          const isActive = stage.id === currentStage;
          const isComplete = stage.id < currentStage;
          return (
            <div key={stage.id} className="flex items-center gap-3 py-2">
              <div
                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                  isComplete
                    ? "border-emerald-500 bg-emerald-500"
                    : isActive
                    ? "border-[#1f6feb] bg-transparent"
                    : "border-gray-600 bg-transparent"
                }`}
              >
                {isComplete && (
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
                )}
              </div>
              <span
                className={`text-sm ${
                  isActive
                    ? "text-[#1f6feb] font-medium"
                    : isComplete
                    ? "text-emerald-400"
                    : textMuted
                }`}
              >
                {stage.id}. {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Standards info */}
      {standardsSummary && (
        <div className={`mx-4 mt-auto mb-4 p-3 ${surfaceAlt} rounded-lg`}>
          <p className={`text-xs font-semibold ${textSecondary} mb-2`}>Available Standards</p>
          <p className={`text-lg font-bold ${textPrimary}`}>{standardsSummary.total_standards}</p>
          <p className={`text-xs ${textMuted}`}>{standardsSummary.total_questions} total questions</p>
        </div>
      )}
    </div>
  );
}
