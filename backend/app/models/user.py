import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from app.constants.user_enums import UserRole, AuthProvider


class User(Base):
    __tablename__ = "users"

    # Use UUID for security - prevents "ID enumeration" attacks
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # nullable for AD users

    role = Column(Enum(UserRole), default=UserRole.WORKER, nullable=False)
    is_active = Column(Boolean, default=True)

    # AD / Keycloak fields
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.LOCAL, nullable=False, server_default="LOCAL")
    ad_username = Column(String(255), unique=True, nullable=True, index=True)
    keycloak_sub = Column(String(255), unique=True, nullable=True, index=True)

    # Audit trail - critical for production
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)