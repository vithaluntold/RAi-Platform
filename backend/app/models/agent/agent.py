"""
Agent Model - defines available agents in the system
An agent is a reusable AI capability that can be attached to workflow tasks.
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class AgentType(str, Enum):
    """Types of agents available in the system"""
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    SEARCH = "search"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent availability status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class Agent(Base):
    """
    Agent definition - a reusable AI capability.
    Agents are created at the platform level and can be attached
    to workflow template tasks (like checklists) and then assigned
    at the assignment/project level (like user assignments).
    """
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Organization scope
    organization_id = Column(UUID(as_uuid=True), nullable=True)

    # Agent identity
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    agent_type = Column(
        SQLEnum(AgentType),
        default=AgentType.CUSTOM,
        nullable=False
    )

    # Backend configuration (Azure, Cyloid, etc.)
    backend_provider = Column(String(100), nullable=False, default="azure")
    backend_config = Column(JSON, nullable=True)

    # Capabilities and input/output schema
    capabilities = Column(JSON, nullable=True)
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)

    # Status
    status = Column(
        SQLEnum(AgentStatus),
        default=AgentStatus.ACTIVE,
        nullable=False
    )
    is_system = Column(Boolean, default=False, nullable=False)

    # Who created it
    created_by = Column(UUID(as_uuid=True), nullable=False)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index('idx_agents_org', 'organization_id'),
        Index('idx_agents_type', 'agent_type'),
        Index('idx_agents_status', 'status'),
    )

    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, type={self.agent_type})>"
