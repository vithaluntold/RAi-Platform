"""
Agent Model - defines available agents in the system.
An agent is a reusable AI capability that can be attached to workflow tasks.

Provider abstraction:
  - ProviderType.EXTERNAL  → cloud-hosted services (Azure OpenAI, Azure AI Search, etc.)
  - ProviderType.ON_PREM   → self-hosted models via LLMLite / vLLM / Ollama
  - ProviderType.HYBRID    → mix of external + on-prem components

backend_config JSON is provider-agnostic.  Each provider type defines its own
expected keys inside backend_config so the runtime can dispatch correctly.
See app/schemas/agent.py → ProviderConfig* models for the validated shapes.
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class AgentType(str, Enum):
    """Functional type of agent — what kind of AI task it performs"""
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    SEARCH = "search"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent availability status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class ProviderType(str, Enum):
    """
    Where the agent's AI services run.
    EXTERNAL  – cloud APIs (Azure, AWS, GCP, OpenAI direct)
    ON_PREM   – self-hosted via LLMLite / vLLM / Ollama / TGI
    HYBRID    – some services external, some on-prem
    """
    EXTERNAL = "external"
    ON_PREM = "on_prem"
    HYBRID = "hybrid"


class Agent(Base):
    """
    Agent definition — a reusable AI capability.
    Agents are created at the platform level and can be attached
    to workflow template tasks (like checklists) and then assigned
    at the assignment/project level (like user assignments).

    The provider_type + backend_provider + backend_config triple lets the
    platform route to the correct runtime without hard-coding any single
    cloud vendor.  When we migrate to LLMLite on-prem, only
    provider_type and backend_config change — no schema migration needed.
    """
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Organization scope
    organization_id = Column(UUID(as_uuid=True), nullable=True)

    # ── Agent identity ──────────────────────────────────────────────
    name = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=True)
    version = Column(String(50), nullable=False, default="1.0.0")
    agent_type = Column(
        SQLEnum(AgentType),
        default=AgentType.CUSTOM,
        nullable=False
    )

    # ── Provider abstraction ────────────────────────────────────────
    # provider_type: broad category (external / on_prem / hybrid)
    provider_type = Column(
        SQLEnum(ProviderType),
        default=ProviderType.EXTERNAL,
        nullable=False,
        server_default="external",
    )
    # backend_provider: specific vendor key ("azure", "llmlite", "ollama", …)
    backend_provider = Column(String(100), nullable=False, default="azure")
    # backend_config: provider-specific JSON blob (endpoints, keys, models, etc.)
    backend_config = Column(JSON, nullable=True)
    # external_url: where the agent's own API lives (e.g. Railway micro-service)
    external_url = Column(String(500), nullable=True)

    # ── Capabilities and I/O contract ───────────────────────────────
    capabilities = Column(JSON, nullable=True)
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)

    # ── Status ──────────────────────────────────────────────────────
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
        Index('idx_agents_provider', 'provider_type'),
    )

    def __repr__(self):
        return (
            f"<Agent(id={self.id}, name={self.name}, "
            f"type={self.agent_type}, provider={self.provider_type})>"
        )
