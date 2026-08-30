"""CahtSession Table"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.schemas import chat_session, user
from data.schemas.base import SQLAlchemyBase

if TYPE_CHECKING:
    from data.schemas.user import User


class ChatSession(SQLAlchemyBase):
    """ORM representation of the 'sessions'' table.

    Each chat session belongs to exactly one ''User'' and is deleted
    automatically when its owner is deleted ('ICASCADE'').

    Attributes:
        id (UUID): Primary key, auto-generated via ``uuid4``.
        title (str): Display title of the chat session, max 255 characters.
        user_id (UUID): Foreign key referencing 'users.id'';
            indexed for fast lookup; cascades on delete.
        user (User): Many-to-one back-reference to the owning ''User''
    """

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="chat_sessions")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
