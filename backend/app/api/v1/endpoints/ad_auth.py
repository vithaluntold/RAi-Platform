import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.keycloak import validate_keycloak_token, get_keycloak_user_info
from app.services.ad_auth_service import find_or_create_ad_user
from app.schemas.ad_auth import ADLoginRequest, ADLoginResponse
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login/ad", response_model=ADLoginResponse)
def login_via_ad(
    payload: ADLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate via Active Directory through Keycloak.

    1. Frontend gets a Keycloak access token (via OIDC Auth Code flow).
    2. Frontend sends that token here.
    3. Backend validates it with Keycloak, provisions user if needed,
       and returns a LOCAL JWT for all subsequent API calls.
    """
    if not settings.KEYCLOAK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AD authentication is not enabled",
        )

    # Validate the Keycloak token
    try:
        validate_keycloak_token(payload.keycloak_token)
    except ValueError as e:
        logger.warning(f"AD login failed: invalid Keycloak token - {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Keycloak token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user info from Keycloak
    try:
        user_info = get_keycloak_user_info(payload.keycloak_token)
    except ValueError as e:
        logger.warning(f"AD login failed: could not fetch userinfo - {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user information from Keycloak",
        )

    keycloak_sub = user_info.get("sub")
    ad_username = user_info.get("preferred_username", "")
    email = user_info.get("email", "")
    first_name = user_info.get("given_name", "")
    last_name = user_info.get("family_name", "")

    if not keycloak_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Keycloak token missing 'sub' claim",
        )

    if not email:
        if ad_username:
            email = f"{ad_username}@rai.com"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot determine email from Keycloak token. "
                       "Ensure the 'email' LDAP mapper is configured.",
            )

    # Check if user already exists (for is_new_user flag)
    existing_user = db.query(User).filter(User.keycloak_sub == keycloak_sub).first()
    is_new = existing_user is None

    # Find or create the local user
    user = find_or_create_ad_user(
        db=db,
        keycloak_sub=keycloak_sub,
        ad_username=ad_username,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Issue a LOCAL JWT - same as existing login
    access_token = create_access_token(subject=str(user.id))

    logger.info(f"AD login successful: user={user.email}, id={user.id}, new={is_new}")

    return ADLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        is_new_user=is_new,
    )
