"use client";

import React from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { StandardsSummary } from "@/types/compliance";

interface StandardsStageProps {
  theme: ComplianceTheme;
  standardsSummary: StandardsSummary | null;
  selectedStandards: Set<string>;
  onToggleStandard: (key: string) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  onConfirm: () => void;
}

export default function StandardsStage({
  theme,
  standardsSummary,
  selectedStandards,
  onToggleStandard,
  onSelectAll,
  onClearAll,
  onConfirm,
}: StandardsStageProps) {
  const { surface, border, textPrimary, textSecondary, textMuted, hoverBg, activeBg } = theme;

  return (
    <div className="p-6 space-y-4">
      <div className={`${surface} border ${border} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className={`text-lg font-semibold ${textPrimary}`}>Select Standards</h3>
            <p className={`text-sm ${textSecondary} mt-1`}>
              {selectedStandards.size} of {standardsSummary?.total_standards || 0} standards selected
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onSelectAll}
              className="px-3 py-1.5 text-xs font-medium text-[#1f6feb] border border-[#1f6feb]/30 rounded-lg hover:bg-[#1f6feb]/10 transition-colors"
            >
              Select All
            </button>
            <button
              onClick={onClearAll}
              className={`px-3 py-1.5 text-xs font-medium ${textMuted} border ${border} rounded-lg ${hoverBg} transition-colors`}
            >
              Clear
            </button>
          </div>
        </div>

        <div className="max-h-100 overflow-y-auto space-y-2 pr-2">
          {(standardsSummary?.standards || []).map((std) => {
            const key = std.section.replace(" ", "_");
            const checked = selectedStandards.has(key);
            return (
              <label
                key={key}
                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                  checked ? activeBg : `${hoverBg} border border-transparent`
                } border`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggleStandard(key)}
                  className="w-4 h-4 rounded border-gray-500 text-[#1f6feb] focus:ring-[#1f6feb]/20"
                />
                <div className="flex-1 min-w-0">
                  <span className={`text-sm font-medium ${textPrimary}`}>{std.section}</span>
                  <span className={`text-sm ${textSecondary} ml-2`}>— {std.title}</span>
                </div>
                <span className={`text-xs ${textMuted} shrink-0`}>{std.item_count} items</span>
              </label>
            );
          })}
        </div>

        <button
          onClick={onConfirm}
          disabled={selectedStandards.size === 0}
          className={`mt-6 px-6 py-2.5 text-sm font-medium rounded-lg transition-colors ${
            selectedStandards.size > 0
              ? "bg-[#1f6feb] text-white hover:bg-[#1a5fd4]"
              : `${theme.surfaceAlt} ${textMuted} cursor-not-allowed`
          }`}
        >
          Confirm Selection ({selectedStandards.size} standards)
        </button>
      </div>
    </div>
  );
}
