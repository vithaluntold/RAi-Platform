"""Constants - user enums and roles."""
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    MANAGER = "manager"
    ENDUSER = "enduser"
    CLIENT = "client"


class AuthProvider(str, Enum):
    """Authentication provider types."""
    LOCAL = "local"
    KEYCLOAK_AD = "keycloak_ad"
