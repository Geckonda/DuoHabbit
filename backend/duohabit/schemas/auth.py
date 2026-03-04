"""Auth schemas."""

from pydantic import BaseModel


class AccessTokenClaim(BaseModel):
    """Access token claims."""

    user_id: int
    account_is_platform_admin: bool
