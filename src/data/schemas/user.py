"""User Table"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.schemas import chat_session
from data.schemas.base import SQLAlchemyBase

if TYPE_CHECKING:
    from data.schemas.chat_session import ChatSession


class User(SQLAlchemyBase):
    """ORM representation of the ``users`` table

    Attributes:
        id (UUID): Primary key, auto-generated via ''uuid4''
        first_name (str): User's first name, max 100 characters.
        last_name (str): User's last name, max 100 characters.
        email (str): Unique, indexed email address, max 255 characters.
        hashed_password (str): Bcrypt-hashed password, never plain-text.
        is_active (bool): Whether the account is active; defaults to
            True
        is_verified (bool): Whether the email has been verified; defaults
            to 'False
        chat_sessions (list[ChatSession]): One-to-many relationship to
            'ChatSession''; cascades delete-orphan.
    """

    __tablename__ = "users"  # CREATE TABLE users (...);

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)

    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    hashed_passwird: Mapped[str] = mapped_column(String(100), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    chat_session: Mapped[list["ChatSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
