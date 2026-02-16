#!/usr/bin/env python3
"""
Database seeding script.
Creates one user per role (admin, manager, enduser, client) using upsert logic.
Safe to run multiple times — existing users are updated, not duplicated.
"""

import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal, engine, Base
from app.models.user import User
from app.models.agent import Agent, AgentType, AgentStatus, ProviderType
from app.core.config import settings
from app.constants.user_enums import UserRole, AuthProvider
from app.core.security import get_password_hash, create_access_token


# ── Seed users: one per role ────────────────────────────────────────

SEED_USERS = [
    {
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@rai-platform.com",
        "password": "Admin@123456",
        "role": UserRole.ADMIN,
    },
    {
        "first_name": "Manager",
        "last_name": "User",
        "email": "manager@rai-platform.com",
        "password": "Manager@123456",
        "role": UserRole.MANAGER,
    },
    {
        "first_name": "End",
        "last_name": "User",
        "email": "enduser@rai-platform.com",
        "password": "Enduser@123456",
        "role": UserRole.ENDUSER,
    },
    {
        "first_name": "Client",
        "last_name": "User",
        "email": "client@rai-platform.com",
        "password": "Client@123456",
        "role": UserRole.CLIENT,
    },
]


def _upsert_user(db, data: dict) -> User:
    """Insert or update a user by email (idempotent)."""
    now = datetime.now(timezone.utc)
    existing = db.query(User).filter(User.email == data["email"]).first()

    if existing:
        existing.first_name = data["first_name"]
        existing.last_name = data["last_name"]
        existing.hashed_password = get_password_hash(data["password"])
        existing.role = data["role"]
        existing.is_active = True
        existing.auth_provider = AuthProvider.LOCAL
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        return existing

    user = User(
        id=uuid4(),
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        hashed_password=get_password_hash(data["password"]),
        role=data["role"],
        is_active=True,
        auth_provider=AuthProvider.LOCAL,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _upsert_compliance_agent(db, admin_user_id: uuid4) -> Agent:
    """Insert or update the system compliance agent (idempotent)."""
    now = datetime.now(timezone.utc)
    agent_name = "Compliance Analysis Agent"

    existing = db.query(Agent).filter(
        Agent.name == agent_name,
        Agent.agent_type == AgentType.COMPLIANCE_ANALYSIS,
        Agent.is_system == True,
    ).first()

    backend_config = {
        "azure_openai_endpoints": settings.AZURE_OPENAI_ENDPOINTS,
        "azure_openai_deployment": settings.AZURE_OPENAI_DEPLOYMENT,
        "azure_doc_intelligence_endpoint": settings.AZURE_DOC_INTELLIGENCE_ENDPOINT,
        "azure_search_endpoint": settings.AZURE_SEARCH_ENDPOINT,
        "azure_search_index_name": settings.AZURE_SEARCH_INDEX_NAME,
    }

    if existing:
        existing.description = "System agent for financial compliance analysis (IFRS, US GAAP, Ind AS). Analyzes financial statements and notes against regulatory standards."
        existing.status = AgentStatus.ACTIVE
        existing.backend_provider = "azure"
        existing.backend_config = backend_config
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        return existing

    agent = Agent(
        id=uuid4(),
        name=agent_name,
        description="System agent for financial compliance analysis (IFRS, US GAAP, Ind AS). Analyzes financial statements and notes against regulatory standards.",
        version="1.0.0",
        agent_type=AgentType.COMPLIANCE_ANALYSIS,
        provider_type=ProviderType.EXTERNAL,
        backend_provider="azure",
        backend_config=backend_config,
        status=AgentStatus.ACTIVE,
        is_system=True,
        capabilities={
            "frameworks": ["IFRS", "US GAAP", "Ind AS"],
            "document_types": ["financial_statements", "notes"],
            "analysis_types": ["compliance_check", "disclosure_validation", "standard_mapping"],
        },
        created_by=admin_user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def seed_database():
    """Create / update seed users, agents, and display credentials."""

    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("\n" + "=" * 64)
        print("  RAi-Platform — Database Seeding")
        print("=" * 64)

        admin_user = None
        for entry in SEED_USERS:
            user = _upsert_user(db, entry)
            token = create_access_token(subject=str(user.id))

            if entry["role"] == UserRole.ADMIN:
                admin_user = user

            status = "updated" if db.query(User).filter(User.email == entry["email"]).count() else "created"
            print(f"\n  ✅ {entry['role'].value.upper()} user ({status})")
            print(f"     Email:    {entry['email']}")
            print(f"     Password: {entry['password']}")
            print(f"     Role:     {entry['role'].value}")
            print(f"     Token:    {token[:40]}...")

        # Seed system agents
        if admin_user:
            print("\n" + "-" * 64)
            print("  System Agents")
            print("-" * 64)
            compliance_agent = _upsert_compliance_agent(db, admin_user.id)
            print(f"  ✅ {compliance_agent.name}")
            print(f"     Type:   {compliance_agent.agent_type.value}")
            print(f"     Status: {compliance_agent.status.value}")

        print("\n" + "-" * 64)
        print("  RBAC Access Matrix")
        print("-" * 64)
        print("  Admin   → Full access (all endpoints)")
        print("  Manager → Read workflows/assignments/clients/contacts/agents,")
        print("            update assignment tasks/steps, execute agents,")
        print("            projects, canvas, documents, reminders, notifications")
        print("  Enduser → Login, own reminders, own notifications only")
        print("  Client  → Login, own reminders, own notifications only")
        print("=" * 64 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
