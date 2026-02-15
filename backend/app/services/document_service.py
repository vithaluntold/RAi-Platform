"""
Document Service - Business logic for document management
"""
import os
import shutil
from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import UploadFile

from app.models.document import Document, DocumentStatus, DocumentCategory
from app.models.user import User

UPLOAD_DIR = "uploads"


class DocumentService:

    @staticmethod
    def _ensure_upload_dir():
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR, exist_ok=True)

    @staticmethod
    def _extract_file_type(filename: str) -> str:
        """Extract file extension as uppercase type."""
        _, ext = os.path.splitext(filename)
        return ext.lstrip(".").upper() if ext else "UNKNOWN"

    @staticmethod
    def _get_user_name(user_id: UUID, db: Session) -> Optional[str]:
        """Look up a user's display name."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        parts = []
        if user.first_name:
            parts.append(user.first_name)
        if user.last_name:
            parts.append(user.last_name)
        return " ".join(parts) if parts else user.email

    @staticmethod
    def _serialize_document(doc: Document, db: Session) -> dict:
        """Convert a Document model to a response dict with uploader name."""
        return {
            "id": str(doc.id),
            "name": doc.name,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "content_type": doc.content_type,
            "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
            "category": doc.category.value if hasattr(doc.category, "value") else doc.category,
            "description": doc.description,
            "version": doc.version,
            "tags": doc.tags,
            "reviewed_by": str(doc.reviewed_by) if doc.reviewed_by else None,
            "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
            "uploaded_by": str(doc.uploaded_by),
            "uploaded_by_name": DocumentService._get_user_name(doc.uploaded_by, db),
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
        }

    @staticmethod
    async def upload_document(
        file: UploadFile,
        metadata: dict,
        uploaded_by: UUID,
        db: Session,
    ) -> Document:
        """Upload a file and create a document record."""
        DocumentService._ensure_upload_dir()

        file_type = DocumentService._extract_file_type(file.filename or "unknown")
        safe_filename = f"{UUID.__class__.__name__}_{file.filename}"
        # Use UUID prefix for unique storage path
        import uuid as uuid_mod
        storage_name = f"{uuid_mod.uuid4().hex}_{file.filename}"
        storage_path = os.path.join(UPLOAD_DIR, storage_name)

        # Save file to disk
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(storage_path)

        category_value = metadata.get("category", "other")
        try:
            category = DocumentCategory(category_value)
        except ValueError:
            category = DocumentCategory.OTHER

        doc = Document(
            name=metadata.get("name") or file.filename or "Untitled",
            original_filename=file.filename or "unknown",
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
            content_type=file.content_type,
            status=DocumentStatus.PENDING_REVIEW,
            category=category,
            description=metadata.get("description"),
            version=metadata.get("version", "1.0"),
            tags=metadata.get("tags"),
            uploaded_by=uploaded_by,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_document(document_id: UUID, db: Session) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id).first()

    @staticmethod
    def get_documents(
        db: Session,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """List documents with optional filtering, search, and pagination."""
        query = db.query(Document)

        if status:
            try:
                status_enum = DocumentStatus(status)
                query = query.filter(Document.status == status_enum)
            except ValueError:
                pass

        if category:
            try:
                category_enum = DocumentCategory(category)
                query = query.filter(Document.category == category_enum)
            except ValueError:
                pass

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Document.name.ilike(search_pattern),
                    Document.original_filename.ilike(search_pattern),
                    Document.description.ilike(search_pattern),
                    Document.tags.ilike(search_pattern),
                )
            )

        total = query.count()
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

        result = []
        for doc in documents:
            result.append(DocumentService._serialize_document(doc, db))

        return {"documents": result, "total": total, "skip": skip, "limit": limit}

    @staticmethod
    def update_document(document_id: UUID, data: dict, db: Session, reviewer_id: Optional[UUID] = None) -> Optional[Document]:
        """Update document metadata and/or status."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return None

        for key, value in data.items():
            if value is not None and hasattr(doc, key):
                if key == "status":
                    new_status = DocumentStatus(value)
                    setattr(doc, key, new_status)
                    # Auto-set reviewer when status changes to reviewed
                    if new_status == DocumentStatus.REVIEWED and reviewer_id:
                        doc.reviewed_by = reviewer_id
                        doc.reviewed_at = datetime.utcnow()
                elif key == "category":
                    setattr(doc, key, DocumentCategory(value))
                else:
                    setattr(doc, key, value)

        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(document_id: UUID, db: Session) -> bool:
        """Delete a document record and its file from disk."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False

        # Remove file from disk if it exists
        if doc.storage_path and os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except OSError:
                pass

        db.delete(doc)
        db.commit()
        return True

    @staticmethod
    def get_document_stats(db: Session) -> dict:
        """Get aggregate document statistics."""
        total = db.query(func.count(Document.id)).scalar() or 0
        pending = db.query(func.count(Document.id)).filter(
            Document.status == DocumentStatus.PENDING_REVIEW
        ).scalar() or 0
        in_review = db.query(func.count(Document.id)).filter(
            Document.status == DocumentStatus.IN_REVIEW
        ).scalar() or 0
        reviewed = db.query(func.count(Document.id)).filter(
            Document.status == DocumentStatus.REVIEWED
        ).scalar() or 0

        # Category breakdown
        category_counts = (
            db.query(Document.category, func.count(Document.id))
            .group_by(Document.category)
            .all()
        )
        categories = {
            (c.value if hasattr(c, "value") else c): count
            for c, count in category_counts
        }

        return {
            "total": total,
            "pending_review": pending,
            "in_review": in_review,
            "reviewed": reviewed,
            "categories": categories,
        }
