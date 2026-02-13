from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
import uuid

from app.api.deps import get_db, get_current_active_admin
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserOnboard, BulkOnboardRequest, UserResponse

router = APIRouter()


# -------------------------------
# Single User Onboarding
# -------------------------------
@router.post("/onboard", response_model=UserResponse)
def onboard_user(
    user_in: UserOnboard,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    # Check if user already exists
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        id=uuid.uuid4(),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role,
        is_active=new_user.is_active
    )


# -------------------------------
# Bulk User Onboarding via CSV
# -------------------------------
@router.post("/onboard/bulk", response_model=List[UserResponse])
def bulk_onboard(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Bulk onboard users via CSV (Admin only)
    CSV Columns: first_name,last_name,email,password,role
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be CSV.")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    required_columns = {"first_name", "last_name", "email", "password"}
    users = []

    for row in reader:
        # Ensure all required fields exist
        if not required_columns.issubset(row.keys()):
            continue  # skip invalid rows

        # Clean values (strip whitespace)
        first_name = row["first_name"].strip()
        last_name = row["last_name"].strip()
        email = row["email"].strip()
        password = row["password"].strip()
        role = row.get("role", "worker").strip().upper()

        # Skip existing users
        if db.query(User).filter(User.email == email).first():
            continue

        user = User(
            id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=True
        )
        db.add(user)
        users.append(user)

    db.commit()
    for user in users:
        db.refresh(user)

    # Return list of response schemas
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active
        )
        for user in users
    ]
