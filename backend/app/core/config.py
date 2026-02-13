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

    # Pydantic settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

# Create a settings instance
settings = Settings()
