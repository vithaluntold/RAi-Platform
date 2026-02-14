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


def seed_database():
    """Create / update seed users and display credentials."""

    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("\n" + "=" * 64)
        print("  RAi-Platform — Database Seeding")
        print("=" * 64)

        for entry in SEED_USERS:
            user = _upsert_user(db, entry)
            token = create_access_token(subject=str(user.id))

            status = "updated" if db.query(User).filter(User.email == entry["email"]).count() else "created"
            print(f"\n  ✅ {entry['role'].value.upper()} user ({status})")
            print(f"     Email:    {entry['email']}")
            print(f"     Password: {entry['password']}")
            print(f"     Role:     {entry['role'].value}")
            print(f"     Token:    {token[:40]}...")

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
