from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.schemas.user import UserOnboard
from app.core.security import get_password_hash

def onboard_multiple_users(db: Session, user_list: list[UserOnboard]):
    created_emails = []
    errors = []

    for user_data in user_list:
        # Check if email is already taken
        user_exists = db.query(User).filter(User.email == user_data.email).first()
        if user_exists:
            errors.append({"email": user_data.email, "detail": "User already exists"})
            continue

        # Split full_name into first_name / last_name (basic handling)
        if user_data.full_name:
            name_parts = user_data.full_name.strip().split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        else:
            first_name = "First"
            last_name = "Last"

        # Create the new user object
        hashed_password = get_password_hash(user_data.password or "Welcome123!")

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=user_data.email,
            role=UserRole.ENDUSER,  # default role for onboarding
            hashed_password=hashed_password,
            is_active=True
        )

        db.add(new_user)
        created_emails.append(user_data.email)

    db.commit()
    return {
        "status": "success",
        "onboarded_count": len(created_emails),
        "created": created_emails,
        "errors": errors
    }
