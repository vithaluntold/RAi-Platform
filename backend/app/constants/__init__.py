"""Constants module - centralized enums and mappings."""
from .user_enums import UserRole, AuthProvider
from .financial_mappings import FINANCIAL_STATEMENT_MAPPINGS, FINANCIAL_STATEMENT_CATEGORIES
from .defaults import (
    DEFAULT_USER_PASSWORD,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_FILE_SIZE_MB,
    ALLOWED_DOCUMENT_TYPES,
)

__all__ = [
    "UserRole",
    "AuthProvider",
    "FINANCIAL_STATEMENT_MAPPINGS",
    "FINANCIAL_STATEMENT_CATEGORIES",
    "DEFAULT_USER_PASSWORD",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MAX_FILE_SIZE_MB",
    "ALLOWED_DOCUMENT_TYPES",
]
