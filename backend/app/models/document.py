"""
Document Model - File/document management with metadata and review workflow
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class DocumentStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class DocumentCategory(str, Enum):
    COMPLIANCE = "compliance"
    POLICY = "policy"
    AUDIT = "audit"
    REGULATORY = "regulatory"
    RISK = "risk"
    OPERATIONS = "operations"
    GOVERNANCE = "governance"
    SECURITY = "security"
    FINANCIAL = "financial"
    LEGAL = "legal"
    HR = "hr"
    OTHER = "other"


class Document(Base):
    """
    Represents an uploaded document with metadata, review status, and categorization.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    storage_path = Column(String(1000), nullable=False)
    content_type = Column(String(255), nullable=True)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING_REVIEW, nullable=False, index=True)
    category = Column(SQLEnum(DocumentCategory), default=DocumentCategory.OTHER, nullable=False, index=True)
    description = Column(String(2000), nullable=True)
    version = Column(String(20), nullable=True, default="1.0")
    tags = Column(String(1000), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_documents_name", "name"),
        Index("ix_documents_status_category", "status", "category"),
        Index("ix_documents_uploaded_by", "uploaded_by"),
    )
