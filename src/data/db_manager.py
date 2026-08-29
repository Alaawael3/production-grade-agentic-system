"""Async PostgreSQL engine and session management.

Provides a single entry point for engine creation, connection pooling,
session lifecycle, and table initialisation using SQLAlchemy async ORM.
"""

import os
from collections.abc import AsyncGenerator

from alembic import environment
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import Environment, settings
from system.logs import logger


class DatabaseManager:
    """Manages the async SQLAlchemy engine and session factory.

    Reads all connection and pool parameters from ``settings`` on
    construction. The single instance is intended to be shared across
    the application lifetime.

    Attributes:
        db_engine (AsyncEngine): The underlying async database engine.
        session_factory (async_sessionmaker): Factory for creating
        ``AsyncSession`` instances.
    """

    def __init__(self):
        """Initialise engine and session factory from application settings.

        Raises:
            SQLAlchemyError: If engine creation fails and the environment
            is not ''PRODUCTION''.
            Engine
            ↓
            manages connections

            Session Factory
            ↓
            creates sessions

            Session
            ↓
            does the actual database work
        """
        connection_url = (  # that connects on the database server
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        try:
            self.db_engine = create_async_engine(
                connection_url,
                pool_pre_ping=True,  # tells SQLAlchemy to check that a connection is still alive before using it.
                pool_size=settings.POSTGRES_POOL_SIZE,
                max_overflow=settings.POSTGRES_MAX_OVERFLOW,
                pool_timeout=30,  # Wait up to 30 seconds for a connection to become available.
                pool_recycle=1800,  # This tells SQLAlchemy to recycle connections that have been around for longer than roughly 30 minutes.
                echo=settings.DEBUG,  # This controls whether SQLAlchemy prints SQL statements to the logs/console.
            )

            self.session_factory = async_sessionmaker(
                self.db_engine,
                class_=AsyncSession,  # When you create a session, create an AsyncSession.
                expire_on_commit=False,
                autoflush=False,  # send the changes I've made in this Session to the database now so = False mean i will control it
            )
        except SQLAlchemyError as e:
            logger.error("database_engine_creation_failed", error=str(e), environment=str(settings.APP_ENV))
            if settings.APP_ENV != Environment.PRODUCTION:
                raise

    async def check_connection(self) -> None:
        """verify the database is reachable"""
        try:
            async with self.db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))  # returns 1
        except Exception:
            logger.criticaal("database_connection_failed")
            raise

    async def dispose(self) -> None:
        """Dispose the engine and close all pooled connections.

        Should be called on application shutdown to release database
        resources cleanly.
        """
        await self.db_engine.dispose()

    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a database session, rolling back automatically on error.

        Designed for use as a FastAPI dependency or async context manager
        The session is closed when the generator exits.

        Yields:
            AsyncSession: A transactional database session.

        Raises:
            Exception: Re-raises any exception after rolling back the
            session.
        """
        async with self.session_factory() as db_session:
            try:
                yield db_session  # return the session and after ending work with it continue the function and commit
                await db_session.commit()
            except Exception:
                await db_session.rollback()  # anything happens back it to its place
                raise


db_manager = DatabaseManager()


async def verify():
    db = DatabaseManager()
    await db.check_connection()
    print("connection is ok")
    await db.dispose()


def main():
    print(f"welcome from `{os.path.basename(__file__).split('.')[0]}` modeul, nothing to do ^___^!")

    import asyncio

    asyncio.run(verify())


if __name__ == "__main__":
    main()
