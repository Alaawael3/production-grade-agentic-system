"""ORM model for the 'user_sessions'' table. """

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID,uuid4

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy. dialects. postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data. schemas. base import SQLAlchemyBase

if TYPE_CHECKING:
    from data.schemas.user import User


class UserSession(SQLAlchemyBase):
    """ORM representation of the ``user_sessions`` table.

    Attributes:
        id (UUID): Primary key, auto-generated via ``uuid4``; shared as the
            ``sid`` claim of both tokens in the pair.
        family_id (UUID): Indexed id shared by every row descended from one
            Login; revoking a compromised chain is one update on this
            column.
        user_id (UUID): Foreign key referencing ``users.id``; indexed for
            fast lookup; cascades on delete.
        expires_at (datetime): When this token pair stops being valid.
        family_created_at (datetime): When the originating login happened;
            copied unchanged across rotations to cap the family's lifetime.
        revoked_at (datetime | None): When this row was revoked, if ever;
            ``None`` while still active.
        created_at (datetime): When this row (this rotation) was created.
        user (User): Many-to-one back-reference to the owning ``User``
    """

    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    family_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False) # the same login session will have the same family_id, even if the token is rotated

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    family_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_sessions", lazy="raise")

