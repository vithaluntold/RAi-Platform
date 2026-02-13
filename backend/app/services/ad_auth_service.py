import uuid
import logging
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, AuthProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


def find_or_create_ad_user(
    db: Session,
    keycloak_sub: str,
    ad_username: str,
    email: str,
    first_name: str,
    last_name: str,
) -> User:
    """
    Look up a user by keycloak_sub, then ad_username, then email.
    If not found, create a new user. Returns the User ORM object.
    """
    # Strategy 1: Match by Keycloak subject ID (most reliable)
    user = db.query(User).filter(User.keycloak_sub == keycloak_sub).first()
    if user:
        _update_ad_user_if_needed(db, user, ad_username, email, first_name, last_name)
        return user

    # Strategy 2: Match by AD username
    if ad_username:
        user = db.query(User).filter(User.ad_username == ad_username).first()
        if user:
            user.keycloak_sub = keycloak_sub
            _update_ad_user_if_needed(db, user, ad_username, email, first_name, last_name)
            db.commit()
            return user

    # Strategy 3: Match by email (handles pre-provisioned local users)
    if email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.keycloak_sub = keycloak_sub
            user.ad_username = ad_username
            user.auth_provider = AuthProvider.KEYCLOAK_AD
            db.commit()
            return user

    # Strategy 4: Auto-provision a new user
    logger.info(f"AD login: auto-provisioning new user ad_username={ad_username}, email={email}")

    default_role = UserRole(settings.KEYCLOAK_AD_DEFAULT_ROLE)

    new_user = User(
        id=uuid.uuid4(),
        first_name=first_name or "Unknown",
        last_name=last_name or "User",
        email=email,
        hashed_password=None,
        role=default_role,
        is_active=True,
        auth_provider=AuthProvider.KEYCLOAK_AD,
        ad_username=ad_username,
        keycloak_sub=keycloak_sub,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def _update_ad_user_if_needed(
    db: Session,
    user: User,
    ad_username: str,
    email: str,
    first_name: str,
    last_name: str,
):
    """Sync user attributes from AD/Keycloak on each login."""
    changed = False
    if ad_username and user.ad_username != ad_username:
        user.ad_username = ad_username
        changed = True
    if email and user.email != email:
        user.email = email
        changed = True
    if first_name and user.first_name != first_name:
        user.first_name = first_name
        changed = True
    if last_name and user.last_name != last_name:
        user.last_name = last_name
        changed = True
    if changed:
        db.commit()
