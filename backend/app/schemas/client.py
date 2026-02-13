"""
Client Schemas - Pydantic models for client CRUD operations
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr


class ClientCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    status: Optional[str] = "active"
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(BaseModel):
    id: UUID
    name: str
    industry: Optional[str] = None
    status: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    contact_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class ClientListItem(BaseModel):
    id: UUID
    name: str
    industry: Optional[str] = None
    status: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkContactToClient(BaseModel):
    contact_id: UUID
    role: Optional[str] = None
    is_primary: bool = False
