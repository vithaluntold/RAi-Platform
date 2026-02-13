"""Default values and application constants."""

# Default user password for bulk uploads
DEFAULT_USER_PASSWORD = "Welcome123!"

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File upload limits
MAX_FILE_SIZE_MB = 50
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain",
]

# Workflow constraints
MIN_WORKFLOW_NAME_LENGTH = 3
MAX_WORKFLOW_NAME_LENGTH = 255

# Project constraints
MIN_PROJECT_NAME_LENGTH = 3
MAX_PROJECT_NAME_LENGTH = 255

__all__ = [
    "DEFAULT_USER_PASSWORD",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MAX_FILE_SIZE_MB",
    "ALLOWED_DOCUMENT_TYPES",
    "MIN_WORKFLOW_NAME_LENGTH",
    "MAX_WORKFLOW_NAME_LENGTH",
    "MIN_PROJECT_NAME_LENGTH",
    "MAX_PROJECT_NAME_LENGTH",
]
