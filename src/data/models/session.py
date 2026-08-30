import re
from dataclasses import field
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatSessionBase(BaseModel):
    """Shared fields present on every chat session schema.

    Attributes:
        title: Chat session title, max 255 characters.
    """

    title: str = Field(..., min_length=1, max_length=255, description="chat session title")


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating a new chat session.

    Inherits ''title'' from 'ChatSessionBase'' with no additional fields.
    """

    @field_validator
    @classmethod
    def validate_title(cls, value: str) -> str:
        if len(value) > 255:
            raise ValueError("title length exceeded it have to be less then 255 characters")


class ChatSessionUpdate(ChatSessionBase):
    """Schema for partial chat session updates.

    All fields are optional - only provided fields are applied.

    Attributes:
    title: Updated chat session title, max 255 characters.
    """

    title: str | None = Field(None, min_length=1, max_length=255, description="update chat session title")


class ChatSessionRead(ChatSessionBase):
    """Schema for returning chat session data to callers.

    Adds server-managed fields (''id'', ''user_id'').

    Attributes:
        id: Unique chat session identifier (UUID).
        user_id: UUID of the owning user.
    """

    id: UUID = Field(..., description="Unique chat session id")
    user_id: UUID = Field(..., description="unique user who owns the chat id")

    model_config = {"from_attributes": True} # when the row come from the database it extracts the needed infor from it (id, user_id)
