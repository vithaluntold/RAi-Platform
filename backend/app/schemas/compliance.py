"""
Compliance Schemas — Pydantic models for compliance session CRUD,
decision tree responses, and analysis results.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ─── Session Schemas ───────────────────────────────────────────────────────

class ComplianceSessionCreate(BaseModel):
    """Create a new compliance analysis session"""
    client_name: str
    framework: str = "IFRS"
    agent_id: Optional[UUID] = None


class ComplianceSessionUpdate(BaseModel):
    """Update a compliance session"""
    client_name: Optional[str] = None
    framework: Optional[str] = None
    status: Optional[str] = None
    current_stage: Optional[int] = None
    selected_standards: Optional[List[str]] = None
    extracted_metadata: Optional[dict] = None
    analysis_results: Optional[dict] = None
    compliance_score: Optional[int] = None
    total_standards: Optional[int] = None
    total_questions: Optional[int] = None
    compliant_count: Optional[int] = None
    non_compliant_count: Optional[int] = None
    not_applicable_count: Optional[int] = None


class ComplianceSessionResponse(BaseModel):
    """Compliance session response"""
    id: UUID
    session_code: str
    client_name: str
    framework: str
    status: str
    current_stage: int
    financial_statements_filename: Optional[str] = None
    notes_filename: Optional[str] = None
    selected_standards: Optional[List[str]] = None
    total_standards: int = 0
    total_questions: int = 0
    extracted_metadata: Optional[dict] = None
    analysis_results: Optional[dict] = None
    compliance_score: Optional[int] = None
    compliant_count: int = 0
    non_compliant_count: int = 0
    not_applicable_count: int = 0
    messages: Optional[list] = None
    agent_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplianceSessionListResponse(BaseModel):
    """Lightweight session for list views"""
    id: UUID
    session_code: str
    client_name: str
    framework: str
    status: str
    current_stage: int
    compliance_score: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Decision Tree Schemas ─────────────────────────────────────────────────

class DecisionTreeNode(BaseModel):
    """A node in the decision tree"""
    question: str
    guidance: Optional[str] = None
    yes_case: Optional[object] = None
    no_case: Optional[object] = None


class ComplianceItem(BaseModel):
    """A single compliance check item from a standard"""
    id: str
    section: str
    reference: str
    question: str
    question_type: Optional[str] = None
    source_question: Optional[str] = None
    source_trigger: Optional[str] = None
    context_required: Optional[str] = None
    original_question: Optional[str] = None
    decision_tree: Optional[dict] = None


class ComplianceStandard(BaseModel):
    """A compliance standard with its items"""
    section: str
    title: str
    description: Optional[str] = None
    item_count: int
    file_name: str


class ComplianceStandardDetail(BaseModel):
    """Full standard with all items"""
    section: str
    title: str
    description: Optional[str] = None
    items: List[ComplianceItem]


class StandardsSummary(BaseModel):
    """Summary of all available standards"""
    total_standards: int
    total_questions: int
    frameworks: List[str]
    standards: List[ComplianceStandard]


# ─── File Upload Response ──────────────────────────────────────────────────

class FileUploadResponse(BaseModel):
    """Response after file upload"""
    session_id: UUID
    financial_statements_uploaded: bool
    notes_uploaded: bool
    status: str
    message: str


# ─── Analysis Result Schemas ───────────────────────────────────────────────

class ComplianceResultItem(BaseModel):
    """A single compliance analysis result"""
    question_id: str
    standard: str
    section: str
    reference: str
    question: str
    status: str  # YES, NO, N/A, ERROR
    confidence: float = 0.0
    explanation: str = ""
    evidence: str = ""
    suggested_disclosure: str = ""
    decision_tree_path: List[str] = Field(default_factory=list)
    sequence: int = 1
    analysis_time_ms: int = 0
    error: Optional[str] = None


class AnalysisSummary(BaseModel):
    """Aggregated analysis results summary"""
    total: int
    compliant: int
    non_compliant: int
    not_applicable: int
    errors: int = 0
    compliance_score: int = 0
    avg_confidence: float = 0.0
    by_standard: Optional[dict] = None


class AnalysisResponse(BaseModel):
    """Full analysis response"""
    session_id: UUID
    status: str
    compliance_score: int
    summary: AnalysisSummary
    total_results: int
    analysis_time_seconds: float


class MetadataExtractionResponse(BaseModel):
    """Response from metadata extraction"""
    session_id: UUID
    metadata: dict
    status: str


class StandardSuggestionResponse(BaseModel):
    """Response from AI standard suggestion"""
    session_id: UUID
    suggested_standards: List[str]
    total_suggested: int


# ─── Chunk Management Schemas ──────────────────────────────────────────────

class ChunkPreviewItem(BaseModel):
    """A single chunk for preview display"""
    chunk_id: str
    chunk_index: int
    content: str
    taxonomy: str = "general"
    has_table: bool = False
    char_count: int = 0


class ChunkPreviewResponse(BaseModel):
    """Response with chunk previews for a session"""
    session_id: UUID
    total_chunks: int
    chunks: List[ChunkPreviewItem]
    taxonomy_summary: dict = Field(default_factory=dict)


class ChunkRevalidateRequest(BaseModel):
    """Request to re-validate/re-classify specific chunks"""
    chunk_ids: List[str] = Field(default_factory=list)
    reclassify: bool = False


class ChunkRevalidateResponse(BaseModel):
    """Response after chunk revalidation"""
    session_id: UUID
    revalidated_count: int
    taxonomy_changes: int
    status: str


# ─── Financial Statement Validation Schemas ────────────────────────────────

class FinancialValidationResult(BaseModel):
    """Result of financial statement validation"""
    is_valid: bool
    detected_statements: List[str] = Field(default_factory=list)
    missing_statements: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class FinancialValidationResponse(BaseModel):
    """Response from financial statement validation"""
    session_id: UUID
    validation: FinancialValidationResult
    status: str


# ─── Question Filter Schemas ──────────────────────────────────────────────

class QuestionFilterRequest(BaseModel):
    """Request to filter questions with optional NLP instructions"""
    standards: List[str]
    instructions: Optional[str] = None
    exclude_question_ids: List[str] = Field(default_factory=list)


class QuestionFilterResponse(BaseModel):
    """Response with filtered questions"""
    session_id: UUID
    total_before: int
    total_after: int
    filtered_questions: List[ComplianceItem]
    applied_instructions: Optional[str] = None


# ─── Chatbot Schemas ───────────────────────────────────────────────────────

class ChatConversationCreate(BaseModel):
    """Create a new chat conversation"""
    title: Optional[str] = None
    context_question_id: Optional[str] = None


class ChatConversationResponse(BaseModel):
    """Chat conversation response"""
    id: UUID
    session_id: UUID
    title: Optional[str] = None
    context_question_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    """Send a new chat message"""
    content: str


class ChatMessageResponse(BaseModel):
    """Chat message response"""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    citations: Optional[List[dict]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSendResponse(BaseModel):
    """Response after sending a chat message (includes AI reply)"""
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


# ─── Saved Results Schemas ─────────────────────────────────────────────────

class SavedResultResponse(BaseModel):
    """Response for cached/saved analysis result"""
    id: UUID
    document_hash: str
    framework: str
    questions_hash: str
    results: dict
    metadata: Optional[dict] = None
    access_count: int
    last_accessed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Job Tracking Schemas ─────────────────────────────────────────────────

class AnalysisProgressItem(BaseModel):
    """Single question progress"""
    question_id: str
    status: str
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalysisJobStatus(BaseModel):
    """Overall job status with per-question progress"""
    job_id: str
    session_id: UUID
    total_questions: int
    completed: int
    failed: int
    in_progress: int
    pending: int
    progress_percent: float
    items: List[AnalysisProgressItem] = Field(default_factory=list)


# ─── Health Check Schema ──────────────────────────────────────────────────

class HealthCheckResponse(BaseModel):
    """Health check response for compliance subsystem"""
    status: str
    azure_openai: str
    azure_search: str
    azure_doc_intelligence: str
    decision_trees_loaded: int
    total_questions: int

