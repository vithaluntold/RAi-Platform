"""
Document Schemas - Pydantic models for document CRUD operations
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    name: str
    category: Optional[str] = "other"
    description: Optional[str] = None
    version: Optional[str] = "1.0"
    tags: Optional[str] = None


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[str] = None


class DocumentResponse(BaseModel):
    id: UUID
    name: str
    original_filename: str
    file_type: str
    file_size: int
    content_type: Optional[str] = None
    status: str
    category: str
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    uploaded_by: UUID
    uploaded_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: UUID
    name: str
    file_type: str
    file_size: int
    status: str
    category: str
    uploaded_by: UUID
    uploaded_by_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
