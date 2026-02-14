"""
Contact API Endpoints - CRUD operations for contact management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse, ContactListItem
from app.services.contact_service import ContactService

router = APIRouter()


@router.get("/", response_model=dict)
async def list_contacts(
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all contacts with optional filtering and search."""
    return ContactService.get_contacts(db, status=status, search=search, skip=skip, limit=limit)


@router.post("/", response_model=dict, status_code=201)
async def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new contact."""
    contact = ContactService.create_contact(
        data=payload.model_dump(),
        created_by=current_user.id,
        db=db,
    )
    return {
        "id": str(contact.id),
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "message": "Contact created successfully",
    }


@router.get("/{contact_id}", response_model=dict)
async def get_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get contact details including linked clients."""
    result = ContactService.get_contact_with_clients(UUID(contact_id), db)
    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")
    return result


@router.patch("/{contact_id}", response_model=dict)
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update contact details."""
    contact = ContactService.update_contact(
        UUID(contact_id),
        payload.model_dump(exclude_unset=True),
        db,
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return {
        "id": str(contact.id),
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "message": "Contact updated successfully",
    }


@router.delete("/{contact_id}", response_model=dict)
async def delete_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a contact and all its client associations."""
    deleted = ContactService.delete_contact(UUID(contact_id), db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}
