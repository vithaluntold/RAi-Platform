"use client";

import React from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceSession, ExtractedMetadata } from "@/types/compliance";

interface MetadataStageProps {
  theme: ComplianceTheme;
  session: ComplianceSession;
  extractingMetadata: boolean;
  onExtractMetadata: () => void;
  onAdvance: () => void;
}

export default function MetadataStage({
  theme,
  session,
  extractingMetadata,
  onExtractMetadata,
  onAdvance,
}: MetadataStageProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted } = theme;

  const meta: ExtractedMetadata | null = session.extracted_metadata;
  const metaFields: [string, string][] = meta && !meta.error
    ? (
        [
          ["Company", meta.company_name],
          ["Period", meta.reporting_period],
          ["Currency", meta.currency],
          ["Industry", meta.industry],
          ["Auditor", meta.auditor],
          ["Framework", meta.reporting_framework],
          ["Consolidated", meta.consolidated != null ? (meta.consolidated ? "Yes" : "No") : null],
          ["Document Type", meta.document_type],
        ] as [string, string | null | undefined][]
      ).filter((pair): pair is [string, string] => pair[1] != null)
    : [];

  return (
    <div className="p-6 space-y-6">
      <div className={`${surface} border ${border} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textPrimary} mb-4`}>Metadata Review</h3>
        <p className={`text-sm ${textSecondary} mb-6`}>
          Review the extracted metadata from your uploaded documents.
        </p>

        <div className={`${surfaceAlt} rounded-lg p-4 space-y-3`}>
          <div className="flex justify-between">
            <span className={`text-sm ${textMuted}`}>Financial Statements</span>
            <span className={`text-sm ${textPrimary}`}>{session.financial_statements_filename || "\u2014"}</span>
          </div>
          <div className="flex justify-between">
            <span className={`text-sm ${textMuted}`}>Notes to Accounts</span>
            <span className={`text-sm ${textPrimary}`}>{session.notes_filename || "\u2014"}</span>
          </div>
        </div>

        {metaFields.length > 0 && (
          <div className={`${surfaceAlt} rounded-lg p-4 space-y-3 mt-4`}>
            <h4 className={`text-sm font-semibold ${textPrimary} mb-2`}>Extracted Metadata</h4>
            {metaFields.map(([label, value]) => (
              <div key={label} className="flex justify-between">
                <span className={`text-sm ${textMuted}`}>{label}</span>
                <span className={`text-sm ${textPrimary}`}>{value}</span>
              </div>
            ))}
          </div>
        )}

        {!meta && (
          <button
            onClick={onExtractMetadata}
            disabled={extractingMetadata}
            className="mt-4 px-5 py-2 text-sm font-medium border border-[#1f6feb]/40 text-[#1f6feb] rounded-lg hover:bg-[#1f6feb]/10 transition-colors disabled:opacity-50"
          >
            {extractingMetadata ? "Extracting..." : "Extract Metadata (AI)"}
          </button>
        )}

        <button
          onClick={onAdvance}
          className="mt-6 px-6 py-2.5 bg-[#1f6feb] text-white text-sm font-medium rounded-lg hover:bg-[#1a5fd4] transition-colors"
        >
          Proceed to Framework Selection
        </button>
      </div>
    </div>
  );
}
