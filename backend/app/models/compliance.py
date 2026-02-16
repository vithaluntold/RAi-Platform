"""
Compliance Session Model — tracks compliance analysis sessions.

Each session represents a single compliance analysis run:
  1. User uploads Financial Statements + Notes
  2. System extracts metadata
  3. User selects framework (IFRS / US GAAP / Ind AS)
  4. User selects which standards to check
  5. System previews context
  6. Agent runs compliance analysis against decision trees
  7. User reviews results

Session codes follow: RAI-{CLIENT_PREFIX}-{MMDDYYYY}-{SEQ}
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean,
    Enum as SQLEnum, JSON, Text, Index, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class ComplianceSessionStatus(str, Enum):
    AWAITING_UPLOAD = "awaiting_upload"
    PROCESSING = "processing"
    METADATA_REVIEW = "metadata_review"
    FRAMEWORK_SELECTION = "framework_selection"
    STANDARDS_SELECTION = "standards_selection"
    CONTEXT_PREVIEW = "context_preview"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ComplianceFramework(str, Enum):
    IFRS = "IFRS"
    US_GAAP = "US GAAP"
    IND_AS = "Ind AS"


class ComplianceResultStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    ERROR = "error"


class AnalysisProgressStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DocumentExtractionStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    INDEXED = "indexed"
    FAILED = "failed"


class ComplianceSession(Base):
    __tablename__ = "compliance_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_code = Column(String(50), unique=True, nullable=False, index=True)
    client_name = Column(String(255), nullable=False)
    framework = Column(String(50), default="IFRS")
    status = Column(
        SQLEnum(ComplianceSessionStatus),
        default=ComplianceSessionStatus.AWAITING_UPLOAD,
        nullable=False,
    )
    current_stage = Column(Integer, default=1, nullable=False)

    # File references
    financial_statements_file = Column(String(500), nullable=True)
    financial_statements_filename = Column(String(255), nullable=True)
    notes_file = Column(String(500), nullable=True)
    notes_filename = Column(String(255), nullable=True)

    # Analysis configuration
    selected_standards = Column(JSON, nullable=True)
    total_standards = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)

    # Extracted metadata
    extracted_metadata = Column(JSON, nullable=True)

    # Analysis results
    analysis_results = Column(JSON, nullable=True)
    compliance_score = Column(Integer, nullable=True)
    compliant_count = Column(Integer, default=0)
    non_compliant_count = Column(Integer, default=0)
    not_applicable_count = Column(Integer, default=0)

    # Messages / chat log
    messages = Column(JSON, nullable=True)

    # Linked agent
    agent_id = Column(UUID(as_uuid=True), nullable=True)

    # Audit
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_compliance_sessions_status", "status"),
        Index("idx_compliance_sessions_created_by", "created_by"),
        Index("idx_compliance_sessions_framework", "framework"),
    )

    def __repr__(self):
        return (
            f"<ComplianceSession(code={self.session_code}, "
            f"status={self.status}, framework={self.framework})>"
        )

    # Relationships
    results = relationship(
        "ComplianceResult", back_populates="session",
        cascade="all, delete-orphan", lazy="dynamic",
    )
    documents = relationship(
        "ComplianceDocument", back_populates="session",
        cascade="all, delete-orphan", lazy="dynamic",
    )


class ComplianceDocument(Base):
    """Tracks each uploaded/extracted document within a compliance session."""

    __tablename__ = "compliance_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=True)  # financial_statements | notes
    extraction_status = Column(
        SQLEnum(DocumentExtractionStatus),
        default=DocumentExtractionStatus.PENDING,
        nullable=False,
    )
    total_pages = Column(Integer, nullable=True)
    document_hash = Column(String(64), nullable=True)
    extracted_text_length = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    extraction_metadata = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    session = relationship("ComplianceSession", back_populates="documents")

    __table_args__ = (
        Index("idx_compliance_docs_session", "session_id"),
        Index("idx_compliance_docs_status", "extraction_status"),
    )

    def __repr__(self):
        return f"<ComplianceDocument(filename={self.filename}, status={self.extraction_status})>"


class ComplianceResult(Base):
    """
    Individual compliance analysis result for a single question.

    Normalized from the JSON blob to enable per-question querying,
    filtering, overrides, and audit trails.
    """

    __tablename__ = "compliance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id = Column(String(100), nullable=False)
    standard = Column(String(100), nullable=False)
    section = Column(String(255), nullable=True)
    reference = Column(String(100), nullable=True)
    question_text = Column(Text, nullable=False)
    sequence = Column(Integer, default=1)

    # Analysis outcome
    status = Column(
        SQLEnum(ComplianceResultStatus),
        default=ComplianceResultStatus.PENDING,
        nullable=False,
    )
    confidence = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    suggested_disclosure = Column(Text, nullable=True)
    decision_tree_path = Column(JSON, nullable=True)
    context_used = Column(Text, nullable=True)
    analysis_time_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)

    # Override support
    is_overridden = Column(Boolean, default=False, nullable=False)
    override_status = Column(SQLEnum(ComplianceResultStatus), nullable=True)
    override_reason = Column(Text, nullable=True)
    overridden_by = Column(UUID(as_uuid=True), nullable=True)
    overridden_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    session = relationship("ComplianceSession", back_populates="results")

    __table_args__ = (
        Index("idx_compliance_results_session", "session_id"),
        Index("idx_compliance_results_standard", "standard"),
        Index("idx_compliance_results_status", "status"),
        Index("idx_compliance_results_session_std", "session_id", "standard"),
    )

    def __repr__(self):
        return (
            f"<ComplianceResult(question={self.question_id}, "
            f"status={self.status}, confidence={self.confidence})>"
        )


class CachedAnalysisResult(Base):
    """
    Cache layer for previously analyzed document+framework+question combos.

    Composite uniqueness on (document_hash, framework, questions_hash)
    allows cache hits when the same document is re-analyzed with the
    same set of questions, avoiding redundant LLM calls.
    """

    __tablename__ = "cached_analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_hash = Column(String(64), nullable=False, index=True)
    framework = Column(String(50), nullable=False)
    questions_hash = Column(String(64), nullable=False)
    results = Column(JSON, nullable=False)
    result_metadata = Column(JSON, nullable=True)
    access_count = Column(Integer, default=1, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index(
            "idx_cached_results_lookup",
            "document_hash", "framework", "questions_hash",
            unique=True,
        ),
    )

    def __repr__(self):
        return (
            f"<CachedAnalysisResult(doc_hash={self.document_hash[:12]}..., "
            f"framework={self.framework}, accesses={self.access_count})>"
        )


class AnalysisProgress(Base):
    """
    Per-question progress tracking for long-running analysis jobs.

    Enables resume-from-failure: if a session analysis crashes mid-way,
    completed questions are retained and only pending ones are re-run.
    """

    __tablename__ = "analysis_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(50), nullable=False, index=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id = Column(String(100), nullable=False)
    status = Column(
        SQLEnum(AnalysisProgressStatus),
        default=AnalysisProgressStatus.PENDING,
        nullable=False,
    )
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_analysis_progress_session", "session_id"),
        Index("idx_analysis_progress_job_question", "job_id", "question_id", unique=True),
    )

    def __repr__(self):
        return (
            f"<AnalysisProgress(job={self.job_id}, "
            f"question={self.question_id}, status={self.status})>"
        )


class QuestionLearningData(Base):
    """
    Stores user corrections and feedback on analysis results.

    When a user overrides a result or provides additional context,
    this data can be used to improve future analysis accuracy
    for similar documents and questions.
    """

    __tablename__ = "question_learning_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_hash = Column(String(64), nullable=False, index=True)
    framework = Column(String(50), nullable=False)
    question_id = Column(String(100), nullable=False)
    original_result = Column(JSON, nullable=False)
    corrected_result = Column(JSON, nullable=False)
    user_comments = Column(Text, nullable=True)
    corrected_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_learning_data_lookup", "document_hash", "framework", "question_id"),
    )

    def __repr__(self):
        return (
            f"<QuestionLearningData(question={self.question_id}, "
            f"framework={self.framework})>"
        )


class ComplianceConversation(Base):
    """
    Chat conversation thread linked to a compliance session.

    Each session can have multiple conversations (e.g. per-standard
    or per-question context discussions).
    """

    __tablename__ = "compliance_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=True)
    context_question_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    messages = relationship(
        "ComplianceMessage", back_populates="conversation",
        cascade="all, delete-orphan", lazy="dynamic",
    )

    __table_args__ = (
        Index("idx_conversations_session", "session_id"),
    )

    def __repr__(self):
        return f"<ComplianceConversation(session={self.session_id}, title={self.title})>"


class ComplianceMessage(Base):
    """
    Individual chat message within a compliance conversation.

    Stores role (user/assistant/system), content, and optional
    citation references to specific document chunks or results.
    """

    __tablename__ = "compliance_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(
        SQLEnum(ChatMessageRole),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("ComplianceConversation", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
    )

    def __repr__(self):
        return f"<ComplianceMessage(role={self.role}, len={len(self.content)})>"
