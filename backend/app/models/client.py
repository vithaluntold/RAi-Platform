"""
Client Model - Organizations/companies that receive workflow assignments
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    ARCHIVED = "archived"


class Client(Base):
    """
    Represents an organization or company that receives workflow assignments.
    A client can have multiple contacts (people representing the client).
    """
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Organization context
    organization_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Core fields
    name = Column(String(255), nullable=False)
    industry = Column(String(150), nullable=True)
    status = Column(
        SQLEnum(ClientStatus),
        default=ClientStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)

    # Address
    address = Column(String(500), nullable=True)
    city = Column(String(150), nullable=True)
    state = Column(String(150), nullable=True)
    country = Column(String(150), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Business identifiers
    tax_id = Column(String(100), nullable=True)

    # Notes
    notes = Column(String(2000), nullable=True)

    # Audit
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_clients_name", "name"),
        Index("ix_clients_org_status", "organization_id", "status"),
    )
