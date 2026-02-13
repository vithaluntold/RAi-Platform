"""Custom exception classes for API responses."""

from fastapi import HTTPException, status


class FinancialStatementMissingError(HTTPException):
    """Raised when an expected financial statement is not found."""
    
    def __init__(self, statement_name: str, detail: str = None):
        if detail is None:
            detail = f"Expected financial statement '{statement_name}' not found in submission."
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class InvalidFinancialDataError(HTTPException):
    """Raised when financial data format is invalid."""
    
    def __init__(self, detail: str = "Invalid financial data format."):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class DuplicateEmailError(HTTPException):
    """Raised when attempting to create a user with an existing email."""
    
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{email}' already exists."
        )


class UserNotFoundError(HTTPException):
    """Raised when a user cannot be found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )


class UnauthorizedError(HTTPException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


__all__ = [
    "FinancialStatementMissingError",
    "InvalidFinancialDataError",
    "DuplicateEmailError",
    "UserNotFoundError",
    "UnauthorizedError",
]
