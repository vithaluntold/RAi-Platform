/**
 * Compliance Module Types — TypeScript interfaces for the RAI Compliance Analysis Platform.
 *
 * Covers: sessions, analysis results, chunks, chatbot, standards, validation,
 * job tracking, and state machine stages.
 */

// ─── Enums / Constants ────────────────────────────────────────────────────

export type ComplianceSessionStatus =
  | "awaiting_upload"
  | "processing"
  | "metadata_review"
  | "framework_selection"
  | "standards_selection"
  | "context_preview"
  | "analyzing"
  | "completed"
  | "failed";

export type ComplianceFramework = "IFRS" | "US GAAP" | "Ind AS";

export type ComplianceResultStatus =
  | "YES"
  | "NO"
  | "N/A"
  | "PENDING"
  | "ERROR";

export type ChatMessageRole = "user" | "assistant" | "system";

export type AnalysisProgressStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed";

/**
 * Ordered stage definitions for the compliance analysis state machine.
 * Each stage has a numeric key, label, description, and associated status.
 */
export const COMPLIANCE_STAGES = {
  1: {
    label: "Upload Documents",
    description: "Upload financial statements and notes",
    status: "awaiting_upload" as ComplianceSessionStatus,
  },
  2: {
    label: "Metadata Review",
    description: "Review extracted document metadata",
    status: "metadata_review" as ComplianceSessionStatus,
  },
  3: {
    label: "Framework Selection",
    description: "Select compliance framework (IFRS, US GAAP, Ind AS)",
    status: "framework_selection" as ComplianceSessionStatus,
  },
  4: {
    label: "Standards Selection",
    description: "Choose which standards to analyze",
    status: "standards_selection" as ComplianceSessionStatus,
  },
  5: {
    label: "Context Preview",
    description: "Preview document chunks and validate coverage",
    status: "context_preview" as ComplianceSessionStatus,
  },
  6: {
    label: "Analysis",
    description: "AI-powered compliance analysis in progress",
    status: "analyzing" as ComplianceSessionStatus,
  },
  7: {
    label: "Results",
    description: "Review compliance analysis results",
    status: "completed" as ComplianceSessionStatus,
  },
} as const;

export type StageNumber = keyof typeof COMPLIANCE_STAGES;

// ─── Session Types ────────────────────────────────────────────────────────

export interface ComplianceSession {
  id: string;
  session_code: string;
  client_name: string;
  framework: string;
  status: ComplianceSessionStatus;
  current_stage: number;
  financial_statements_filename: string | null;
  notes_filename: string | null;
  selected_standards: string[] | null;
  total_standards: number;
  total_questions: number;
  extracted_metadata: ExtractedMetadata | null;
  analysis_results: AnalysisResults | null;
  compliance_score: number | null;
  compliant_count: number;
  non_compliant_count: number;
  not_applicable_count: number;
  messages: ChatLogMessage[] | null;
  agent_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ComplianceSessionListItem {
  id: string;
  session_code: string;
  client_name: string;
  framework: string;
  status: ComplianceSessionStatus;
  current_stage: number;
  compliance_score: number | null;
  created_at: string;
}

export interface ComplianceSessionCreate {
  client_name: string;
  framework?: string;
  agent_id?: string;
}

export interface ComplianceSessionUpdate {
  client_name?: string;
  framework?: string;
  status?: string;
  current_stage?: number;
  selected_standards?: string[];
  extracted_metadata?: Record<string, unknown>;
  analysis_results?: Record<string, unknown>;
  compliance_score?: number;
  total_standards?: number;
  total_questions?: number;
  compliant_count?: number;
  non_compliant_count?: number;
  not_applicable_count?: number;
}

// ─── Metadata Types ───────────────────────────────────────────────────────

export interface ExtractedMetadata {
  company_name?: string;
  reporting_period?: string;
  reporting_year?: string;
  currency?: string;
  industry?: string;
  auditor?: string;
  reporting_framework?: string;
  consolidated?: boolean;
  interim?: boolean;
  document_type?: string;
  key_accounting_policies?: string[];
  error?: string;
}

// ─── Analysis Result Types ────────────────────────────────────────────────

export interface ComplianceResultItem {
  question_id: string;
  standard: string;
  section: string;
  reference: string;
  question: string;
  status: ComplianceResultStatus;
  confidence: number;
  explanation: string;
  evidence: string;
  suggested_disclosure: string;
  decision_tree_path: string[];
  context_used: string[];
  sequence: number;
  analysis_time_ms: number;
  error: string | null;
  // Override fields (present when overridden)
  original_status?: string;
  override_reason?: string;
  overridden_by?: string;
}

export interface AnalysisSummary {
  total: number;
  compliant: number;
  non_compliant: number;
  not_applicable: number;
  errors: number;
  compliance_score: number;
  avg_confidence: number;
  by_standard?: Record<
    string,
    {
      total: number;
      compliant: number;
      non_compliant: number;
      not_applicable: number;
      errors: number;
      avg_confidence: number;
    }
  >;
}

export interface AnalysisResults {
  summary: AnalysisSummary;
  results: ComplianceResultItem[];
  document_hash: string;
  analysis_time_seconds: number;
}

export interface AnalysisResponse {
  session_id: string;
  status: string;
  compliance_score: number;
  summary: AnalysisSummary;
  total_results: number;
  analysis_time_seconds: number;
}

// ─── Streaming Types ──────────────────────────────────────────────────────

export interface StreamEvent {
  type: "status" | "progress" | "result" | "complete" | "error";
  data: Record<string, unknown>;
}

export interface StreamProgress {
  total_questions: number;
  completed_questions: number;
  percentage: number;
  current_standard: string;
  current_question: string;
  phase: string;
  errors: string[];
}

// ─── Decision Tree / Standards Types ──────────────────────────────────────

export interface ComplianceItem {
  id: string;
  section: string;
  reference: string;
  question: string;
  question_type?: string;
  source_question?: string;
  source_trigger?: string;
  context_required?: string;
  original_question?: string;
  decision_tree?: Record<string, unknown>;
}

export interface ComplianceStandard {
  section: string;
  title: string;
  description?: string;
  item_count: number;
  file_name: string;
}

export interface StandardsSummary {
  total_standards: number;
  total_questions: number;
  frameworks: string[];
  standards: ComplianceStandard[];
}

export interface StandardDetail {
  section: string;
  title: string;
  description?: string;
  items: ComplianceItem[];
}

// ─── Chunk Types ──────────────────────────────────────────────────────────

export interface ChunkPreviewItem {
  chunk_id: string;
  chunk_index: number;
  content: string;
  taxonomy: string;
  has_table: boolean;
  char_count: number;
}

export interface ChunkPreviewResponse {
  session_id: string;
  total_chunks: number;
  chunks: ChunkPreviewItem[];
  taxonomy_summary: Record<string, number>;
}

export interface ChunkRevalidateRequest {
  chunk_ids?: string[];
  reclassify?: boolean;
}

export interface ChunkRevalidateResponse {
  session_id: string;
  revalidated_count: number;
  taxonomy_changes: number;
  status: string;
}

// ─── Financial Validation Types ───────────────────────────────────────────

export interface FinancialValidationResult {
  is_valid: boolean;
  detected_statements: string[];
  missing_statements: string[];
  warnings: string[];
  confidence: number;
}

export interface FinancialValidationResponse {
  session_id: string;
  validation: FinancialValidationResult;
  status: string;
}

// ─── Question Filter Types ───────────────────────────────────────────────

export interface QuestionFilterRequest {
  standards: string[];
  instructions?: string;
  exclude_question_ids?: string[];
}

export interface QuestionFilterResponse {
  session_id: string;
  total_before: number;
  total_after: number;
  filtered_questions: ComplianceItem[];
  applied_instructions?: string;
}

// ─── Chatbot Types ────────────────────────────────────────────────────────

export interface ChatConversation {
  id: string;
  session_id: string;
  title: string | null;
  context_question_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: ChatMessageRole;
  content: string;
  citations: ChatCitation[] | null;
  created_at: string;
}

export interface ChatCitation {
  text: string;
  source: string;
}

export interface ChatSendResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
}

// ─── Saved Results / Cache Types ──────────────────────────────────────────

export interface SavedResult {
  id: string;
  document_hash: string;
  framework: string;
  questions_hash: string;
  results: Record<string, unknown>;
  metadata: Record<string, unknown> | null;
  access_count: number;
  last_accessed_at: string;
  created_at: string;
}

// ─── Job Tracking Types ──────────────────────────────────────────────────

export interface AnalysisProgressItem {
  question_id: string;
  status: AnalysisProgressStatus;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface AnalysisJobStatus {
  job_id: string;
  session_id: string;
  total_questions: number;
  completed: number;
  failed: number;
  in_progress: number;
  pending: number;
  progress_percent: number;
  items: AnalysisProgressItem[];
}

// ─── Health Check Types ──────────────────────────────────────────────────

export interface ComplianceHealthCheck {
  status: string;
  azure_openai: string;
  azure_search: string;
  azure_doc_intelligence: string;
  decision_trees_loaded: number;
  total_questions: number;
}

// ─── Chat Log (session-level messages) ───────────────────────────────────

export interface ChatLogMessage {
  role: string;
  content: string;
  timestamp: string;
}

// ─── File Upload Types ───────────────────────────────────────────────────

export interface FileUploadResponse {
  session_id: string;
  financial_statements_uploaded: boolean;
  notes_uploaded: boolean;
  status: string;
  message: string;
}

// ─── Metadata Extraction Response ────────────────────────────────────────

export interface MetadataExtractionResponse {
  session_id: string;
  metadata: ExtractedMetadata;
  status: string;
}

// ─── Standard Suggestion Response ────────────────────────────────────────

export interface StandardSuggestionResponse {
  session_id: string;
  suggested_standards: string[];
  total_suggested: number;
}
