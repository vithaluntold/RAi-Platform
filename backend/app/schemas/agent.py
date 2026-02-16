"""
Agent Schemas — Pydantic models for agent CRUD, configuration, and execution.

Provider abstraction philosophy:
  backend_config is a free-form JSON blob whose *shape* varies by provider.
  The ProviderConfig* classes below document (and optionally validate) the
  expected shapes for each provider, but they are NOT enforced at the DB level
  — only at the API level when the caller asks for validation.

  This means:
    • Azure today  → backend_config contains endpoint URLs, API keys, model pools
    • LLMLite later → backend_config contains llmlite_base_url, model_id, context_length
    • No schema migration required — only the JSON payload changes.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ─── Provider-Specific Config Shapes (documentation + optional validation) ──

class AzureOpenAIEndpoint(BaseModel):
    """One Azure OpenAI resource endpoint"""
    endpoint_url: str
    api_key: str
    deployment_name: str
    api_version: str = "2024-10-21"


class AzureSearchConfig(BaseModel):
    """Azure AI Search service config"""
    endpoint: str
    admin_key: str
    index_name: Optional[str] = None


class AzureDocIntelligenceConfig(BaseModel):
    """Azure Document Intelligence config"""
    endpoint: str
    api_key: str


class ProviderConfigAzure(BaseModel):
    """
    backend_config shape when backend_provider='azure'.
    Used by the RAI Compliance Analysis agent and similar Azure-hosted agents.
    """
    # Primary LLM endpoints (round-robin pools)
    llm_endpoints: Optional[List[AzureOpenAIEndpoint]] = None
    # Fallback LLM endpoints (used on 429 / rate-limit)
    fallback_endpoints: Optional[List[AzureOpenAIEndpoint]] = None
    # Fast / cheap LLM endpoints (metadata, chat, tagging)
    fast_endpoints: Optional[List[AzureOpenAIEndpoint]] = None

    # Document extraction
    document_intelligence: Optional[AzureDocIntelligenceConfig] = None

    # Semantic search
    search: Optional[AzureSearchConfig] = None

    # Database for agent-internal state (e.g. Neon PostgreSQL for compliance sessions)
    agent_database_url: Optional[str] = None

    # Model parameters
    temperature: float = 0.0
    max_tokens: int = 16384


class ProviderConfigLLMLite(BaseModel):
    """
    backend_config shape when backend_provider='llmlite'.
    For future on-prem LLM deployment via LiteLLM / LLMLite proxy.
    """
    # LLMLite proxy base URL
    base_url: str
    # API key for the proxy (if auth enabled)
    api_key: Optional[str] = None
    # Model identifier on the proxy (e.g. "mistral-7b", "llama-3-70b")
    model_id: str
    # Fallback model
    fallback_model_id: Optional[str] = None
    # Context window size (affects chunking strategy)
    context_length: int = 8192
    # Model parameters
    temperature: float = 0.0
    max_tokens: int = 4096

    # Optional: on-prem document extraction service URL
    document_extraction_url: Optional[str] = None
    # Optional: on-prem vector search URL (e.g. Qdrant, Milvus, Weaviate)
    vector_search_url: Optional[str] = None
    vector_search_api_key: Optional[str] = None
    vector_search_collection: Optional[str] = None


class ProviderConfigHybrid(BaseModel):
    """
    backend_config shape when provider_type='hybrid'.
    Mix of external + on-prem components — e.g. Azure Search + on-prem LLM.
    """
    azure: Optional[ProviderConfigAzure] = None
    llmlite: Optional[ProviderConfigLLMLite] = None
    # Routing: which operations go where
    routing: Optional[dict] = Field(
        default=None,
        description=(
            "Maps operation types to providers. "
            "e.g. {'analysis': 'llmlite', 'search': 'azure', 'extraction': 'azure'}"
        ),
    )


# ─── Agent Definition Schemas ──────────────────────────────────────────────

class AgentCreate(BaseModel):
    """Create a new agent definition"""
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    agent_type: str = "custom"
    provider_type: str = "external"
    backend_provider: str = "azure"
    backend_config: Optional[dict] = None
    external_url: Optional[str] = None
    capabilities: Optional[dict] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    organization_id: Optional[UUID] = None


class AgentUpdate(BaseModel):
    """Update an agent definition"""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    agent_type: Optional[str] = None
    provider_type: Optional[str] = None
    backend_provider: Optional[str] = None
    backend_config: Optional[dict] = None
    external_url: Optional[str] = None
    capabilities: Optional[dict] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent definition response"""
    id: UUID
    name: str
    description: Optional[str] = None
    version: str
    agent_type: str
    provider_type: str
    backend_provider: str
    backend_config: Optional[dict] = None
    external_url: Optional[str] = None
    capabilities: Optional[dict] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    status: str
    is_system: bool
    organization_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Workflow Task Agent (Template Level) ──────────────────────────────────

class WorkflowTaskAgentCreate(BaseModel):
    """Attach an agent to a workflow template task"""
    agent_id: UUID
    position: int = 0
    is_required: bool = False
    task_config: Optional[dict] = None
    instructions: Optional[str] = None


class WorkflowTaskAgentUpdate(BaseModel):
    """Update agent configuration on a workflow template task"""
    position: Optional[int] = None
    is_required: Optional[bool] = None
    task_config: Optional[dict] = None
    instructions: Optional[str] = None


class WorkflowTaskAgentResponse(BaseModel):
    """Workflow task agent response"""
    id: UUID
    task_id: UUID
    agent_id: UUID
    position: int
    is_required: bool
    task_config: Optional[dict] = None
    instructions: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Assignment Task Agent (Instance Level) ────────────────────────────────

class AssignmentTaskAgentCreate(BaseModel):
    """Assign an agent to an assignment task"""
    agent_id: UUID
    order: int = 0
    is_required: bool = False
    task_config: Optional[dict] = None
    instructions: Optional[str] = None


class AssignmentTaskAgentUpdate(BaseModel):
    """Update agent assignment on an assignment task"""
    order: Optional[int] = None
    is_required: Optional[bool] = None
    task_config: Optional[dict] = None
    instructions: Optional[str] = None
    status: Optional[str] = None


class AssignmentTaskAgentResponse(BaseModel):
    """Assignment task agent response"""
    id: UUID
    task_id: UUID
    agent_id: UUID
    template_agent_id: Optional[UUID] = None
    order: int
    status: str
    is_required: bool
    task_config: Optional[dict] = None
    instructions: Optional[str] = None
    assigned_by: Optional[UUID] = None
    last_execution_id: Optional[UUID] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Agent Execution Schemas ───────────────────────────────────────────────

class AgentExecutionCreate(BaseModel):
    """Trigger an agent execution"""
    input_data: Optional[dict] = None


class AgentExecutionResponse(BaseModel):
    """Agent execution result"""
    id: UUID
    assignment_task_agent_id: UUID
    agent_id: UUID
    task_id: UUID
    triggered_by: UUID
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    error_details: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    backend_provider: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
