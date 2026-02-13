#!/usr/bin/env python3
"""
Database seeding script for development.
Creates a test user and generates a valid JWT token for authentication.
"""

import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal, engine, Base
from app.models.user import User
from app.core.config import settings
from app.constants.user_enums import UserRole, AuthProvider
from app.core.security import get_password_hash, create_access_token
from jose import jwt

def seed_database():
    """Create test user and display JWT token for development."""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        test_email = "test@example.com"
        existing_user = db.query(User).filter(User.email == test_email).first()
        
        if existing_user:
            user = existing_user
            print(f"\n✓ Test user already exists: {test_email}")
        else:
            # Create test user
            user = User(
                id=uuid4(),
                first_name="Test",
                last_name="User",
                email=test_email,
                hashed_password=get_password_hash("test123456"),
                role=UserRole.ADMIN,
                is_active=True,
                auth_provider=AuthProvider.LOCAL,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"\n✓ Created test user: {test_email}")
        
        # Generate JWT token
        access_token = create_access_token(subject=str(user.id))
        
        print("\n" + "="*60)
        print("DEVELOPMENT CREDENTIALS")
        print("="*60)
        print(f"Email:    {test_email}")
        print(f"Password: test123456")
        print(f"\nAccess Token (valid for {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes):")
        print(f"{access_token}")
        print("\n" + "="*60)
        print("\nTo use this token in development:")
        print("1. Open browser console")
        print("2. Run: localStorage.setItem('access_token', '<paste-token-above>')")
        print("3. Refresh the page")
        print("="*60 + "\n")
        
        # Also return the token for use in tests
        return access_token
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
