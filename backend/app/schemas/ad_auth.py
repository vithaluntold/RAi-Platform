from pydantic import BaseModel


class ADLoginRequest(BaseModel):
    """Frontend sends the Keycloak access token obtained via OIDC flow."""
    keycloak_token: str


class ADLoginResponse(BaseModel):
    """Returns a LOCAL JWT (not the Keycloak token) plus basic user info."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_new_user: bool = False
