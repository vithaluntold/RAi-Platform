from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

# Single user onboarding request
class UserOnboard(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: Optional[str] = "enduser"  # default role if not specified

# Bulk onboarding request
class BulkOnboardRequest(BaseModel):
    users: list[UserOnboard]

# Response schema for users
class UserResponse(BaseModel):
    id: UUID         # UUID matches the database
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    is_active: bool
    auth_provider: Optional[str] = "local"
    ad_username: Optional[str] = None

    class Config:
        from_attributes = True  # production-level: replace old orm_mode
