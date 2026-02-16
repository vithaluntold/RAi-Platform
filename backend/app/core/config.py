# app/core/config.py
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []

    # Keycloak / AD integration
    KEYCLOAK_ENABLED: bool = False
    KEYCLOAK_SERVER_URL: str = ""
    KEYCLOAK_REALM: str = "cyloid"
    KEYCLOAK_CLIENT_ID: str = "cyloid-backend"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_AD_DEFAULT_ROLE: str = "worker"

    # Azure OpenAI — primary LLM endpoints (comma-separated for round-robin)
    AZURE_OPENAI_ENDPOINTS: str = ""
    AZURE_OPENAI_API_KEYS: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"

    # Azure OpenAI — fallback endpoints
    AZURE_OPENAI_FALLBACK_ENDPOINTS: str = ""
    AZURE_OPENAI_FALLBACK_API_KEYS: str = ""
    AZURE_OPENAI_FALLBACK_DEPLOYMENT: str = "gpt-4o-mini"

    # Azure Document Intelligence
    AZURE_DOC_INTELLIGENCE_ENDPOINT: str = ""
    AZURE_DOC_INTELLIGENCE_KEY: str = ""

    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_ADMIN_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "compliance-chunks"
    AZURE_SEARCH_SEMANTIC_CONFIG: str = "compliance-semantic"

    # Compliance analysis tuning
    RESULT_CACHE_TTL_HOURS: int = 72
    MAX_ANALYSIS_WORKERS: int = 6
    ANALYSIS_BATCH_SIZE: int = 5
    MAX_CONTEXT_CHARS: int = 200000

    # Pydantic settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

# Create a settings instance
settings = Settings()
