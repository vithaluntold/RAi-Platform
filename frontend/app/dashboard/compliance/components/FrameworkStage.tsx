"use client";

import React from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceFramework } from "@/types/compliance";

const FRAMEWORKS: ComplianceFramework[] = ["IFRS", "US GAAP", "Ind AS"];

const FRAMEWORK_DESCRIPTIONS: Record<ComplianceFramework, string> = {
  "IFRS": "International Financial Reporting Standards",
  "US GAAP": "US Generally Accepted Accounting Principles",
  "Ind AS": "Indian Accounting Standards",
};

interface FrameworkStageProps {
  theme: ComplianceTheme;
  currentFramework: string | null;
  darkMode: boolean;
  onSelectFramework: (fw: string) => void;
}

export default function FrameworkStage({
  theme,
  currentFramework,
  darkMode,
  onSelectFramework,
}: FrameworkStageProps) {
  const { surface, border, textPrimary, textSecondary, textMuted, hoverBg } = theme;

  return (
    <div className="p-6 space-y-6">
      <div className={`${surface} border ${border} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textPrimary} mb-2`}>Select Compliance Framework</h3>
        <p className={`text-sm ${textSecondary} mb-6`}>Choose the regulatory framework for your compliance analysis.</p>
        <div className="grid grid-cols-3 gap-4">
          {FRAMEWORKS.map((fw) => (
            <button
              key={fw}
              onClick={() => onSelectFramework(fw)}
              className={`p-6 rounded-xl border-2 text-center transition-all ${
                currentFramework === fw
                  ? `border-[#1f6feb] ${darkMode ? "bg-[#1f6feb]/10" : "bg-blue-50"}`
                  : `${border} ${hoverBg}`
              }`}
            >
              <p className={`text-lg font-semibold ${textPrimary}`}>{fw}</p>
              <p className={`text-xs ${textMuted} mt-1`}>{FRAMEWORK_DESCRIPTIONS[fw]}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
