"""
Client API Endpoints - CRUD operations for client management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientListItem, LinkContactToClient
from app.services.client_service import ClientService

router = APIRouter()


@router.get("/", response_model=dict)
async def list_clients(
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """List all clients with optional filtering and search."""
    return ClientService.get_clients(db, status=status, search=search, skip=skip, limit=limit)


@router.post("/", response_model=dict, status_code=201)
async def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new client."""
    client = ClientService.create_client(
        data=payload.model_dump(),
        created_by=current_user.id,
        db=db,
    )
    return {
        "id": str(client.id),
        "name": client.name,
        "status": client.status.value if hasattr(client.status, "value") else client.status,
        "message": "Client created successfully",
    }


@router.get("/{client_id}", response_model=dict)
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get client details including linked contacts."""
    client = ClientService.get_client(UUID(client_id), db)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    contacts = ClientService.get_client_contacts(UUID(client_id), db)

    return {
        "id": str(client.id),
        "name": client.name,
        "industry": client.industry,
        "status": client.status.value if hasattr(client.status, "value") else client.status,
        "email": client.email,
        "phone": client.phone,
        "website": client.website,
        "address": client.address,
        "city": client.city,
        "state": client.state,
        "country": client.country,
        "postal_code": client.postal_code,
        "tax_id": client.tax_id,
        "notes": client.notes,
        "created_at": client.created_at,
        "updated_at": client.updated_at,
        "contacts": contacts,
    }


@router.patch("/{client_id}", response_model=dict)
async def update_client(
    client_id: str,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update client details."""
    client = ClientService.update_client(
        UUID(client_id),
        payload.model_dump(exclude_unset=True),
        db,
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "id": str(client.id),
        "name": client.name,
        "status": client.status.value if hasattr(client.status, "value") else client.status,
        "message": "Client updated successfully",
    }


@router.delete("/{client_id}", response_model=dict)
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a client and all its contact associations."""
    deleted = ClientService.delete_client(UUID(client_id), db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}


@router.post("/{client_id}/contacts", response_model=dict, status_code=201)
async def link_contact_to_client(
    client_id: str,
    payload: LinkContactToClient,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Link a contact to this client."""
    client = ClientService.get_client(UUID(client_id), db)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    link = ClientService.link_contact(
        client_id=UUID(client_id),
        contact_id=payload.contact_id,
        role=payload.role,
        is_primary=payload.is_primary,
        db=db,
    )
    return {
        "client_id": str(client_id),
        "contact_id": str(payload.contact_id),
        "role": link.role,
        "is_primary": link.is_primary,
        "message": "Contact linked to client",
    }


@router.delete("/{client_id}/contacts/{contact_id}", response_model=dict)
async def unlink_contact_from_client(
    client_id: str,
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Remove a contact link from this client."""
    removed = ClientService.unlink_contact(UUID(client_id), UUID(contact_id), db)
    if not removed:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"message": "Contact unlinked from client"}


@router.get("/{client_id}/contacts", response_model=list)
async def get_client_contacts(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Get all contacts linked to this client."""
    client = ClientService.get_client(UUID(client_id), db)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientService.get_client_contacts(UUID(client_id), db)
