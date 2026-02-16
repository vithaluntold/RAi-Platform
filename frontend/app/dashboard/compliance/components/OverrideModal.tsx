"use client";

import React from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceResultItem } from "@/types/compliance";

interface OverrideModalProps {
  theme: ComplianceTheme;
  target: ComplianceResultItem;
  overrideStatus: string;
  overrideReason: string;
  onStatusChange: (status: string) => void;
  onReasonChange: (reason: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function OverrideModal({
  theme,
  target,
  overrideStatus,
  overrideReason,
  onStatusChange,
  onReasonChange,
  onConfirm,
  onCancel,
}: OverrideModalProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted, inputBg, hoverBg } = theme;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className={`${surface} border ${border} rounded-xl p-6 max-w-md w-full mx-4`}>
        <h4 className={`text-sm font-semibold ${textPrimary} mb-3`}>Override Result</h4>
        <p className={`text-xs ${textSecondary} mb-4 line-clamp-3`}>{target.question}</p>
        <div className="space-y-3">
          <div>
            <label className={`text-xs font-medium ${textMuted} block mb-1`}>New Status</label>
            <select
              title="Override status"
              value={overrideStatus}
              onChange={(e) => onStatusChange(e.target.value)}
              className={`w-full px-3 py-2 text-sm ${inputBg} ${textPrimary} border ${border} rounded-lg outline-none`}
            >
              <option value="YES">Compliant</option>
              <option value="NO">Non-Compliant</option>
              <option value="N/A">Not Applicable</option>
            </select>
          </div>
          <div>
            <label className={`text-xs font-medium ${textMuted} block mb-1`}>Reason (required)</label>
            <textarea
              value={overrideReason}
              onChange={(e) => onReasonChange(e.target.value)}
              placeholder="Explain why this result should be overridden..."
              rows={3}
              className={`w-full px-3 py-2 text-sm ${inputBg} ${textPrimary} border ${border} rounded-lg outline-none resize-none`}
            />
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <button
            onClick={onConfirm}
            disabled={!overrideReason.trim()}
            className="flex-1 py-2 bg-[#1f6feb] text-white text-xs font-medium rounded-lg hover:bg-[#1a5fd4] disabled:opacity-50 transition-colors"
          >
            Confirm Override
          </button>
          <button
            onClick={onCancel}
            className={`flex-1 py-2 ${surfaceAlt} ${textSecondary} text-xs font-medium rounded-lg border ${border} ${hoverBg} transition-colors`}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
