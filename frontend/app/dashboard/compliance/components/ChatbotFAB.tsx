"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import type { ComplianceTheme } from "./useComplianceTheme";
import type { ChatConversation, ChatMessage } from "@/types/compliance";
import { apiCall } from "@/lib";
import { API_ENDPOINTS } from "@/lib/api-config";

interface ChatbotFABProps {
  theme: ComplianceTheme;
  sessionId: string;
}

export default function ChatbotFAB({ theme, sessionId }: ChatbotFABProps) {
  const { surface, surfaceAlt, border, textPrimary, textSecondary, textMuted, hoverBg, inputBg } = theme;

  const [open, setOpen] = useState(false);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadConversations = useCallback(async () => {
    try {
      const data = await apiCall<ChatConversation[]>(API_ENDPOINTS.COMPLIANCE_SESSION_CONVERSATIONS(sessionId));
      setConversations(data);
    } catch {
      // silently fail
    }
  }, [sessionId]);

  const loadMessages = useCallback(async (convId: string) => {
    setLoading(true);
    try {
      const data = await apiCall<ChatMessage[]>(
        API_ENDPOINTS.COMPLIANCE_SESSION_CONVERSATION_MESSAGES(sessionId, convId)
      );
      setMessages(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (open) {
      loadConversations();
    }
  }, [open, loadConversations]);

  useEffect(() => {
    if (activeConvId) {
      loadMessages(activeConvId);
    }
  }, [activeConvId, loadMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewConversation = async () => {
    try {
      const data = await apiCall<ChatConversation>(
        API_ENDPOINTS.COMPLIANCE_SESSION_CONVERSATIONS(sessionId),
        { method: "POST", body: JSON.stringify({ title: null }) }
      );
      setConversations((prev) => [data, ...prev]);
      setActiveConvId(data.id);
      setMessages([]);
    } catch {
      // silently fail
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !activeConvId || sending) return;
    const messageText = input;
    setInput("");
    setSending(true);

    try {
      const data = await apiCall<{ user_message: ChatMessage; assistant_message: ChatMessage }>(
        API_ENDPOINTS.COMPLIANCE_SESSION_CONVERSATION_SEND(sessionId, activeConvId),
        { method: "POST", body: JSON.stringify({ content: messageText }) }
      );
      setMessages((prev) => [...prev, data.user_message, data.assistant_message]);
    } catch {
      // silently fail
    } finally {
      setSending(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        title="Open AI Chat"
        className="fixed bottom-6 right-6 z-40 w-14 h-14 bg-[#1f6feb] text-white rounded-full shadow-lg hover:bg-[#1a5fd4] transition-all flex items-center justify-center"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
      </button>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 z-40 w-96 h-128 flex flex-col rounded-xl shadow-2xl overflow-hidden border ${border}`}>
      {/* Header */}
      <div className={`${surface} border-b ${border} p-3 flex items-center justify-between shrink-0`}>
        <div className="flex items-center gap-2">
          {activeConvId && (
            <button
              title="Back to conversations"
              onClick={() => { setActiveConvId(null); setMessages([]); }}
              className={`w-6 h-6 rounded flex items-center justify-center ${textMuted} ${hoverBg}`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
            </button>
          )}
          <span className={`text-sm font-semibold ${textPrimary}`}>
            {activeConvId ? "Chat" : "Conversations"}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {!activeConvId && (
            <button
              onClick={handleNewConversation}
              title="New conversation"
              className={`w-7 h-7 rounded flex items-center justify-center ${textSecondary} ${hoverBg}`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
            </button>
          )}
          <button
            onClick={() => setOpen(false)}
            title="Close chat"
            className={`w-7 h-7 rounded flex items-center justify-center ${textMuted} ${hoverBg}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>
      </div>

      {/* Body */}
      <div className={`flex-1 ${surface} overflow-y-auto`}>
        {!activeConvId ? (
          /* Conversation list */
          <div className="p-3 space-y-2">
            {conversations.length === 0 ? (
              <div className={`text-center py-8 ${textMuted} text-sm`}>
                <p>No conversations yet.</p>
                <button
                  onClick={handleNewConversation}
                  className="mt-2 px-4 py-1.5 text-xs bg-[#1f6feb] text-white rounded-lg hover:bg-[#1a5fd4]"
                >
                  Start New Chat
                </button>
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setActiveConvId(conv.id)}
                  className={`w-full text-left p-3 rounded-lg ${surfaceAlt} border ${border} ${hoverBg} transition-colors`}
                >
                  <p className={`text-sm ${textPrimary} truncate`}>{conv.title || "Untitled"}</p>
                  <p className={`text-[10px] ${textMuted} mt-1`}>{conv.message_count} messages</p>
                </button>
              ))
            )}
          </div>
        ) : (
          /* Messages */
          <div className="p-3 space-y-3">
            {loading ? (
              <div className={`text-center py-8 ${textMuted} text-sm`}>Loading messages...</div>
            ) : messages.length === 0 ? (
              <div className={`text-center py-8 ${textMuted} text-sm`}>
                Start a conversation about your compliance analysis.
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                      msg.role === "user"
                        ? "bg-[#1f6feb] text-white"
                        : `${surfaceAlt} ${textPrimary} border ${border}`
                    }`}
                  >
                    {msg.content}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {msg.citations.map((c, i) => (
                          <div key={i} className={`text-[10px] ${msg.role === "user" ? "text-blue-200" : textMuted} border-l-2 border-blue-400 pl-2`}>
                            <span className="font-medium">{c.source}:</span> {c.text}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      {activeConvId && (
        <div className={`${surface} border-t ${border} p-3 shrink-0`}>
          <div className={`flex items-center gap-2 ${inputBg} border ${border} rounded-lg px-3 py-2`}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about your compliance results..."
              className={`flex-1 bg-transparent text-sm ${textPrimary} outline-none`}
              disabled={sending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sending}
              className={`w-7 h-7 rounded flex items-center justify-center ${input.trim() ? "text-[#1f6feb]" : textMuted} transition-colors disabled:opacity-50`}
            >
              {sending ? (
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
