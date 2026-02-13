from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.user import User, AuthProvider

router = APIRouter()

@router.post("/login/access-token")
def login(db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # Fetch user by email
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Block local login for AD users
    if user.auth_provider == AuthProvider.KEYCLOAK_AD:
        raise HTTPException(
            status_code=400,
            detail="This account uses Active Directory authentication. "
                   "Please use the AD login option.",
        )

    if not user.hashed_password or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Generate JWT token using 'subject' argument
    access_token = security.create_access_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
