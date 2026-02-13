"""
Client Service - Business logic for client management
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.client import Client, ClientStatus
from app.models.client_contact import ClientContact


class ClientService:

    @staticmethod
    def create_client(
        data: dict,
        created_by: UUID,
        db: Session,
        organization_id: Optional[UUID] = None,
    ) -> Client:
        client = Client(
            name=data["name"],
            industry=data.get("industry"),
            status=ClientStatus(data.get("status", "active")),
            email=data.get("email"),
            phone=data.get("phone"),
            website=data.get("website"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country"),
            postal_code=data.get("postal_code"),
            tax_id=data.get("tax_id"),
            notes=data.get("notes"),
            created_by=created_by,
            organization_id=organization_id,
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def get_client(client_id: UUID, db: Session) -> Optional[Client]:
        return db.query(Client).filter(Client.id == client_id).first()

    @staticmethod
    def get_clients(
        db: Session,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        query = db.query(Client)

        if status:
            query = query.filter(Client.status == status)
        if search:
            query = query.filter(Client.name.ilike(f"%{search}%"))

        total = query.count()
        clients = query.order_by(Client.name).offset(skip).limit(limit).all()

        # Attach contact counts
        result = []
        for client in clients:
            count = db.query(func.count(ClientContact.id)).filter(
                ClientContact.client_id == client.id
            ).scalar() or 0
            result.append({
                "id": client.id,
                "name": client.name,
                "industry": client.industry,
                "status": client.status.value if hasattr(client.status, "value") else client.status,
                "email": client.email,
                "phone": client.phone,
                "contact_count": count,
                "created_at": client.created_at,
            })

        return {"clients": result, "total": total}

    @staticmethod
    def update_client(client_id: UUID, data: dict, db: Session) -> Optional[Client]:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None

        for key, value in data.items():
            if value is not None and hasattr(client, key):
                if key == "status":
                    setattr(client, key, ClientStatus(value))
                else:
                    setattr(client, key, value)

        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def delete_client(client_id: UUID, db: Session) -> bool:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False

        # Remove associations first
        db.query(ClientContact).filter(ClientContact.client_id == client_id).delete()
        db.delete(client)
        db.commit()
        return True

    @staticmethod
    def link_contact(client_id: UUID, contact_id: UUID, role: Optional[str], is_primary: bool, db: Session) -> ClientContact:
        # Check if link already exists
        existing = db.query(ClientContact).filter(
            ClientContact.client_id == client_id,
            ClientContact.contact_id == contact_id,
        ).first()
        if existing:
            existing.role = role
            existing.is_primary = is_primary
            db.commit()
            db.refresh(existing)
            return existing

        link = ClientContact(
            client_id=client_id,
            contact_id=contact_id,
            role=role,
            is_primary=is_primary,
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def unlink_contact(client_id: UUID, contact_id: UUID, db: Session) -> bool:
        deleted = db.query(ClientContact).filter(
            ClientContact.client_id == client_id,
            ClientContact.contact_id == contact_id,
        ).delete()
        db.commit()
        return deleted > 0

    @staticmethod
    def get_client_contacts(client_id: UUID, db: Session) -> list:
        from app.models.contact import Contact
        links = db.query(ClientContact).filter(
            ClientContact.client_id == client_id
        ).all()

        result = []
        for link in links:
            contact = db.query(Contact).filter(Contact.id == link.contact_id).first()
            if contact:
                result.append({
                    "id": str(contact.id),
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "email": contact.email,
                    "phone": contact.phone,
                    "designation": contact.designation,
                    "role": link.role,
                    "is_primary": link.is_primary,
                    "status": contact.status.value if hasattr(contact.status, "value") else contact.status,
                })
        return result

    @staticmethod
    def get_client_name(client_id: UUID, db: Session) -> Optional[str]:
        """Quick lookup for client name - used by assignment/project views."""
        client = db.query(Client).filter(Client.id == client_id).first()
        return client.name if client else None
