"use client";

import React, { useRef } from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ComplianceSession, ChatLogMessage } from "@/types/compliance";

interface UploadStageProps {
  theme: ComplianceTheme;
  session: ComplianceSession;
  fsFile: File | null;
  notesFile: File | null;
  uploading: boolean;
  chatInput: string;
  onSetFsFile: (file: File | null) => void;
  onSetNotesFile: (file: File | null) => void;
  onUpload: () => void;
  onChatInputChange: (value: string) => void;
  onSendMessage: () => void;
}

export default function UploadStage({
  theme,
  session,
  fsFile,
  notesFile,
  uploading,
  chatInput,
  onSetFsFile,
  onSetNotesFile,
  onUpload,
  onChatInputChange,
  onSendMessage,
}: UploadStageProps) {
  const chatEndRef = useRef<HTMLDivElement>(null);
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted, hoverBg } = theme;

  const messages: ChatLogMessage[] = session.messages || [];

  return (
    <div className="flex flex-col h-full">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-[#1f6feb] text-white"
                  : `${surfaceAlt} ${textPrimary} border ${border}`
              }`}
            >
              {msg.role === "system" && <span className="mr-1">👋</span>}
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* Upload card */}
      <div className="px-6 pb-4">
        <div className={`${surface} border ${border} rounded-xl p-6`}>
          <div className="flex items-center justify-between mb-4">
            <button title="Previous" className={`w-8 h-8 rounded-full ${surfaceAlt} ${textSecondary} flex items-center justify-center ${hoverBg}`}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
            </button>
            <div className="text-center">
              <h3 className={`text-base font-semibold ${textPrimary}`}>Upload Pre-Separated Files</h3>
              <p className={`text-xs ${textMuted} mt-1`}>Upload your Financial Statements and Notes as separate files</p>
            </div>
            <button title="Next" className={`w-8 h-8 rounded-full ${surfaceAlt} ${textSecondary} flex items-center justify-center ${hoverBg}`}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <div className={`flex items-center gap-2 mb-2 ${textSecondary} text-sm`}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="M7 16l4-8 4 4 4-6" /></svg>
                <span>Financial Statements (PDF/DOCX)</span>
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <span className="px-4 py-2 bg-[#1f6feb] text-white text-sm font-medium rounded-lg hover:bg-[#1a5fd4] transition-colors">
                  Choose File
                </span>
                <span className={`text-sm ${textMuted}`}>{fsFile ? fsFile.name : "No file chosen"}</span>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  className="hidden"
                  onChange={(e) => onSetFsFile(e.target.files?.[0] || null)}
                />
              </label>
            </div>

            <div>
              <div className={`flex items-center gap-2 mb-2 ${textSecondary} text-sm`}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                <span>Notes to Accounts (PDF/DOCX)</span>
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <span className="px-4 py-2 bg-[#1f6feb] text-white text-sm font-medium rounded-lg hover:bg-[#1a5fd4] transition-colors">
                  Choose File
                </span>
                <span className={`text-sm ${textMuted}`}>{notesFile ? notesFile.name : "No file chosen"}</span>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  className="hidden"
                  onChange={(e) => onSetNotesFile(e.target.files?.[0] || null)}
                />
              </label>
            </div>
          </div>

          <button
            onClick={onUpload}
            disabled={!fsFile || !notesFile || uploading}
            className={`w-full mt-5 py-3 rounded-lg text-sm font-medium transition-colors ${
              fsFile && notesFile
                ? "bg-[#1f6feb] text-white hover:bg-[#1a5fd4]"
                : `${surfaceAlt} ${textMuted} cursor-not-allowed`
            }`}
          >
            {uploading ? "Uploading..." : fsFile && notesFile ? "Upload & Continue" : "Select Both Files to Continue"}
          </button>
        </div>
      </div>

      {/* Chat input */}
      <div className="px-6 pb-4">
        <div className={`flex items-center gap-2 ${surface} border ${border} rounded-xl px-4 py-2`}>
          <svg className={textMuted} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          <input
            type="text"
            value={chatInput}
            onChange={(e) => onChatInputChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSendMessage()}
            placeholder="Ask a question or filter questions (e.g., 'Skip all pension questions')..."
            className={`flex-1 bg-transparent text-sm ${textPrimary} placeholder:${textMuted} outline-none`}
          />
          <button
            title="Send message"
            onClick={onSendMessage}
            className={`w-8 h-8 rounded-lg flex items-center justify-center ${chatInput ? "text-[#1f6feb]" : textMuted} transition-colors`}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
