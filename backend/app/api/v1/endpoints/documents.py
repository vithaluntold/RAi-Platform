"""
Document API Endpoints - Full CRUD with file upload, search, filtering, and download
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("/", response_model=dict)
async def list_documents(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name, description, or tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all documents with optional filtering, search, and pagination."""
    return DocumentService.get_documents(db, status=status, category=category, search=search, skip=skip, limit=limit)


@router.get("/stats", response_model=dict)
async def get_document_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get aggregate document statistics."""
    return DocumentService.get_document_stats(db)


@router.post("/upload", response_model=dict, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    category: Optional[str] = Form("other"),
    description: Optional[str] = Form(None),
    version: Optional[str] = Form("1.0"),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.ENDUSER)),
):
    """Upload a new document with optional metadata."""
    metadata = {
        "name": name,
        "category": category,
        "description": description,
        "version": version,
        "tags": tags,
    }
    doc = await DocumentService.upload_document(file=file, metadata=metadata, uploaded_by=current_user.id, db=db)
    return DocumentService._serialize_document(doc, db)


@router.get("/{document_id}", response_model=dict)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a single document's details."""
    doc = DocumentService.get_document(UUID(document_id), db)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentService._serialize_document(doc, db)


@router.patch("/{document_id}", response_model=dict)
async def update_document(
    document_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    tags: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Update document metadata or status."""
    data = {}
    if name is not None:
        data["name"] = name
    if status is not None:
        data["status"] = status
    if category is not None:
        data["category"] = category
    if description is not None:
        data["description"] = description
    if version is not None:
        data["version"] = version
    if tags is not None:
        data["tags"] = tags

    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    doc = DocumentService.update_document(UUID(document_id), data, db, reviewer_id=current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentService._serialize_document(doc, db)


@router.delete("/{document_id}", response_model=dict)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Delete a document and its associated file."""
    deleted = DocumentService.delete_document(UUID(document_id), db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully", "id": document_id}


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download the document file."""
    import os
    doc = DocumentService.get_document(UUID(document_id), db)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.storage_path or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        path=doc.storage_path,
        filename=doc.original_filename,
        media_type=doc.content_type or "application/octet-stream",
    )