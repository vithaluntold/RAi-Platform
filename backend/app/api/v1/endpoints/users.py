from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io
import uuid

from app.api.deps import get_db, get_current_active_admin, get_current_active_user
from app.core.security import get_password_hash
from app.models.user import User
from app.models.notification import Notification, UserNotificationPreference
from app.models.reminder import Reminder
from app.schemas.user import UserOnboard, BulkOnboardRequest, UserResponse, UserUpdate, UserListResponse
from app.constants.user_enums import UserRole

router = APIRouter()


# -------------------------------
# List Users (with search, filter, pagination)
# -------------------------------
@router.get("", response_model=UserListResponse)
def list_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status: active, inactive"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    query = db.query(User)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (User.first_name.ilike(term))
            | (User.last_name.ilike(term))
            | (User.email.ilike(term))
        )

    if role:
        try:
            role_enum = UserRole(role.lower())
            query = query.filter(User.role == role_enum)
        except ValueError:
            pass

    if status:
        if status.lower() == "active":
            query = query.filter(User.is_active == True)
        elif status.lower() == "inactive":
            query = query.filter(User.is_active == False)

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


# -------------------------------
# Get Single User
# -------------------------------
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


# -------------------------------
# Update User
# -------------------------------
@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = db.query(User).filter(User.email == update_data["email"], User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    if "role" in update_data:
        try:
            update_data["role"] = UserRole(update_data["role"].lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {update_data['role']}")

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


# -------------------------------
# Delete User
# -------------------------------
@router.delete("/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Clean up related records (DB has ON DELETE CASCADE but ORM intercepts)
    db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.query(UserNotificationPreference).filter(UserNotificationPreference.user_id == user_id).delete()
    db.query(Reminder).filter(Reminder.user_id == user_id).delete()

    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}


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
