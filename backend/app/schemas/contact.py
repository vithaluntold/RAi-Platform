"""
Contact Schemas - Pydantic models for contact CRUD operations
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = "active"
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    clients: Optional[List[dict]] = []

    model_config = {"from_attributes": True}


class ContactListItem(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    status: str
    created_at: datetime
    client_count: int = 0

    model_config = {"from_attributes": True}
