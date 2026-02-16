from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


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


# Update user request (all fields optional)
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# Response schema for users
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    is_active: bool
    auth_provider: Optional[str] = "local"
    ad_username: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Paginated list response
class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
