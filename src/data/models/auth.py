from datetime import datetime
from pydantic import BaseModel, EmailStr, SecretStr, Field
from data.models.user import UserRead


class LoginRequest(BaseModel):
    """Credentials submitted at login.

    Attributes:
        email: User's email address.
        password: Plain-text password submitted by the user.
    """

    email: EmailStr = Field(..., description="User's Mail Address")
    password: SecretStr = Field(..., description="user password")


class Token(BaseModel):
    """JWT token pair returned after successful authentication.

    Attributes:
        access_token: Short-Lived JWT access token.
        refresh_token: Long-Lived JWT refresh token.
        token_type: Token scheme, always '"bearer"'
        expires_at: UTC datetime when the access token expires.
    """

    access_token: str = Field(..., description="short-lived JWT access token.")
    refresh_token: str = Field(..., description="long-lived JWT refresh token")
    token_type: str = Field("bearer", description="token scheme")
    expires_at: datetime = Field(..., description="when the token expires")


class AuthResponse(BaseModel):
    """Full response on successful login or token refresh.

    Attributes:
        user: Authenticated user's public profile.
        token: Issued token pair.
    """
    user: UserRead = Field(..., description="authenticated user profile")
    token: Token = Field(..., description="Issued tooken pair")


class RefreshTokenRequest(BaseModel):
    """Payload submitted to obtain a new access token.

    Attributes:
        refresh_token: Long-lived JWT refresh token.
    """
    refresh_token: str = Field(..., description="long-lived JWT refresh token")

