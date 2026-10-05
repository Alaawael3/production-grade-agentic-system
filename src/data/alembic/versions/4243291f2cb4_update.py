"""update

Revision ID: 4243291f2cb4
Revises: efd5158db782
Create Date: 2026-10-06 00:38:52.753152

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4243291f2cb4"
down_revision: Union[str, Sequence[str], None] = "efd5158db782"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ------------------------------------------------------------------
    # Create user_sessions table
    # ------------------------------------------------------------------
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "family_created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_user_sessions_family_id"),
        "user_sessions",
        ["family_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_sessions_user_id"),
        "user_sessions",
        ["user_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # sessions.created_at
    #
    # Existing rows may contain NULL, so populate them before adding
    # the NOT NULL constraint.
    # ------------------------------------------------------------------
    op.execute(sa.text("""
            UPDATE sessions
            SET created_at = NOW()
            WHERE created_at IS NULL
            """))

    op.add_column(
        "sessions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.alter_column(
        "sessions",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # users.updated_at
    # ------------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # ------------------------------------------------------------------
    # users.created_at
    #
    # Existing rows may contain NULL, so populate them before adding
    # the NOT NULL constraint.
    # ------------------------------------------------------------------
    op.execute(sa.text("""
            UPDATE users
            SET created_at = NOW()
            WHERE created_at IS NULL
            """))

    op.alter_column(
        "users",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "users",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )

    op.drop_column(
        "users",
        "updated_at",
    )

    op.alter_column(
        "sessions",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )

    op.drop_column(
        "sessions",
        "updated_at",
    )

    op.drop_index(
        op.f("ix_user_sessions_user_id"),
        table_name="user_sessions",
    )

    op.drop_index(
        op.f("ix_user_sessions_family_id"),
        table_name="user_sessions",
    )

    op.drop_table("user_sessions")
