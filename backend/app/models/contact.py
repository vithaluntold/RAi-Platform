"""
Contact Model - People/individuals who can be linked to one or more clients
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class ContactStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Contact(Base):
    """
    Represents a person (standalone) who can be linked to one or more clients
    via the client_contacts association table. Contacts are independent entities.
    """
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Organization context
    organization_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Person details
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)

    # Professional info
    designation = Column(String(200), nullable=True)  # e.g., "CFO", "Finance Manager"
    department = Column(String(200), nullable=True)

    # Status
    status = Column(
        SQLEnum(ContactStatus),
        default=ContactStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Notes
    notes = Column(String(2000), nullable=True)

    # Audit
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_contacts_name", "first_name", "last_name"),
        Index("ix_contacts_org_status", "organization_id", "status"),
    )
