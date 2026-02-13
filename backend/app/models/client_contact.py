"""
ClientContact - Join table linking standalone contacts to clients (many-to-many)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class ClientContact(Base):
    """
    Many-to-many association between clients and contacts.
    A contact can represent multiple clients; a client can have multiple contacts.
    """
    __tablename__ = "client_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role this contact plays for this particular client
    role = Column(String(100), nullable=True)  # e.g., "Primary", "Billing", "Technical"
    is_primary = Column(Boolean, default=False, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("client_id", "contact_id", name="uq_client_contact"),
        Index("ix_client_contacts_client", "client_id"),
        Index("ix_client_contacts_contact", "contact_id"),
    )
