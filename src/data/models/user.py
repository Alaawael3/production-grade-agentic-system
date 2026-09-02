import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


class UserBase(BaseModel):
    """Shared fields present on every user schema.

    Attributes:
        first_name: User's first name, max 100 characters.
        last_name: User's last name, max 100 characters.
        email: User's unique email address.
    """

    first_name: str = Field(..., max_length=100, description="user's first name")
    last_name: str = Field(..., max_length=100, description="user's last name")
    email: EmailStr = Field(..., description="user's unique email address")


class UserCreate(UserBase):
    """Schema for creating a new user account.

    Extends ''UserBase'' with a plain-text password that is validated
    before being hashed and persisted.

    Attributes:
        password: Plain-text password (8-64 chars). Must contain uppercase,
        Lowercase, digit, and special character. Hashed before persistence.
    """

    password: SecretStr = Field(..., min_length=8, max_length=64, description="plain_text password (8-64) character")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        """Enforce password complexity rules.

        Raises 'ValueError' if the password is missing any required
        character class: lowercase, uppercase, digit, or special character.
        """
        password = value.get_secret_value()

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if len(password) > 64:
            raise ValueError("Password must be at less than 64 characters")

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must at least one uppercase character")

        if not re.search(r"[a-z]", password):
            raise ValueError("Password must at least one lowercase character")

        if not re.search(r"[0-9]", password):
            raise ValueError("Password must at least one digit")

        if not re.search(r"[@#$%^&*(),.?:{}|<>]", password):
            raise ValueError("Password must at least one speecial character")

        return value


class UpdateUser(UserBase):
    """Schema for partial user profile updates.

    All fields are optional - only provided fields are applied.

    Attributes:
        first_name: Updated first name, max 100 characters.
        last_name: Updated last name, max 100 characters.
        email: Updated email address.
    """

    first_name: str | None = Field(None, max_length=100, description="Updated first name")
    last_name: str | None = Field(None, max_length=100, description="Updated last name")
    email: EmailStr | None = Field(None, description="Updated email")


class UserRead(UserBase):
    """Schema for returning user data to callers.

    Adds server-managed fields .(``id``, ``is_active``, ``is_verified``).
    Never includes ``hashed_password``

    Attributes:
        id: Unique user identifier (UUID).
        is_active: Whether the account is active.
        is_verified: Whether the email .address has been verified.
    """

    id: UUID = Field(..., description="unique user identifier")
    is_active: bool = Field(..., description="whether the account is active")
    is_verified: bool = Field(..., description="whether the accountt is verified")

    model_config = {
        "from_attributes": True
    }  # when the row come from the database it extracts the needed infor from it (id, is_active, is_verified)
