"""
Contact Service - Business logic for contact management
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.contact import Contact, ContactStatus
from app.models.client_contact import ClientContact
from app.models.client import Client


class ContactService:

    @staticmethod
    def create_contact(
        data: dict,
        created_by: UUID,
        db: Session,
        organization_id: Optional[UUID] = None,
    ) -> Contact:
        contact = Contact(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email"),
            phone=data.get("phone"),
            mobile=data.get("mobile"),
            designation=data.get("designation"),
            department=data.get("department"),
            status=ContactStatus(data.get("status", "active")),
            notes=data.get("notes"),
            created_by=created_by,
            organization_id=organization_id,
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    @staticmethod
    def get_contact(contact_id: UUID, db: Session) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.id == contact_id).first()

    @staticmethod
    def get_contacts(
        db: Session,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        query = db.query(Contact)

        if status:
            query = query.filter(Contact.status == status)
        if search:
            query = query.filter(
                (Contact.first_name.ilike(f"%{search}%")) |
                (Contact.last_name.ilike(f"%{search}%")) |
                (Contact.email.ilike(f"%{search}%"))
            )

        total = query.count()
        contacts = query.order_by(Contact.last_name, Contact.first_name).offset(skip).limit(limit).all()

        result = []
        for contact in contacts:
            client_count = db.query(func.count(ClientContact.id)).filter(
                ClientContact.contact_id == contact.id
            ).scalar() or 0
            result.append({
                "id": contact.id,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "phone": contact.phone,
                "designation": contact.designation,
                "status": contact.status.value if hasattr(contact.status, "value") else contact.status,
                "created_at": contact.created_at,
                "client_count": client_count,
            })

        return {"contacts": result, "total": total}

    @staticmethod
    def update_contact(contact_id: UUID, data: dict, db: Session) -> Optional[Contact]:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return None

        for key, value in data.items():
            if value is not None and hasattr(contact, key):
                if key == "status":
                    setattr(contact, key, ContactStatus(value))
                else:
                    setattr(contact, key, value)

        db.commit()
        db.refresh(contact)
        return contact

    @staticmethod
    def delete_contact(contact_id: UUID, db: Session) -> bool:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return False

        # Remove associations first
        db.query(ClientContact).filter(ClientContact.contact_id == contact_id).delete()
        db.delete(contact)
        db.commit()
        return True

    @staticmethod
    def get_contact_with_clients(contact_id: UUID, db: Session) -> Optional[dict]:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return None

        links = db.query(ClientContact).filter(
            ClientContact.contact_id == contact_id
        ).all()

        clients = []
        for link in links:
            client = db.query(Client).filter(Client.id == link.client_id).first()
            if client:
                clients.append({
                    "id": str(client.id),
                    "name": client.name,
                    "industry": client.industry,
                    "role": link.role,
                    "is_primary": link.is_primary,
                })

        return {
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "phone": contact.phone,
            "mobile": contact.mobile,
            "designation": contact.designation,
            "department": contact.department,
            "status": contact.status.value if hasattr(contact.status, "value") else contact.status,
            "notes": contact.notes,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "clients": clients,
        }
