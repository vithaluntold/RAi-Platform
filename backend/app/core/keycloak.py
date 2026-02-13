import json
import base64
import logging
from keycloak import KeycloakOpenID, KeycloakError
from app.core.config import settings

logger = logging.getLogger(__name__)

_keycloak_openid: KeycloakOpenID | None = None


def get_keycloak_client() -> KeycloakOpenID:
    """Lazy-initialize and return the KeycloakOpenID singleton."""
    global _keycloak_openid
    if _keycloak_openid is None:
        _keycloak_openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
        )
    return _keycloak_openid


def validate_keycloak_token(token: str) -> dict:
    """
    Validate a Keycloak access token using token introspection.
    Returns the introspection result if active. Raises ValueError otherwise.
    """
    kc = get_keycloak_client()
    try:
        token_info = kc.introspect(token)
    except KeycloakError as e:
        logger.error(f"Keycloak introspection failed: {e}")
        raise ValueError(f"Keycloak introspection error: {e}")

    if not token_info.get("active"):
        raise ValueError("Keycloak token is not active")

    return token_info


def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload from a JWT without signature verification (already validated via introspection)."""
    payload_b64 = token.split(".")[1]
    # Add padding if needed
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def get_keycloak_user_info(token: str) -> dict:
    """
    Get user info from Keycloak. Tries the userinfo endpoint first,
    falls back to decoding the JWT payload (which contains the same claims).
    """
    kc = get_keycloak_client()
    try:
        return kc.userinfo(token)
    except KeycloakError as e:
        logger.warning(f"Keycloak userinfo endpoint failed ({e}), falling back to JWT decode")

    # Fallback: decode user info directly from the JWT payload
    try:
        return _decode_jwt_payload(token)
    except Exception as e:
        logger.error(f"Failed to decode JWT payload: {e}")
        raise ValueError(f"Could not extract user info from Keycloak token: {e}")
