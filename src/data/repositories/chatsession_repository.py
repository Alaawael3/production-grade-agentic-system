from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.schemas import chat_session
from data.schemas.chat_session import ChatSession


class ChatSessionRepository:
    """Encapsulates all database operations for the 'ChatSession'' ORM model.

    Receives an ''AsyncSession'' so multiple repositories can share a single
    transaction per request.

    Args:
        db_session: Active async database session.
    """

    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def get(self, session_id: UUID) -> ChatSession:
        """Fetch a single chat session by primary key.

        Args :
        chat_session_id: UUID of the chat session to retrieve.

        Returns:
        The 'ChatSession'' instance, or 'None'' if not found.
        """
        return self._db_session.get(ChatSession, session_id)

    async def get_all(self, user_id: UUID, page: int = 1, page_size: int = 20) -> list[ChatSession]:
        """Fetch a paginated list of chat sessions belonging to a user.

        Args:
        user_id: UUID of the owning user.
        page: 1-based page number.
        page_size: Number of records per page.

        Returns:

        list of ``ChatSession`` instances for the requested page; empty list if none exist.
        """
        offset = (page - 1) * page_size
        result = await self._db_session.execute(
            select(ChatSession).where(ChatSession.user_id == user_id).offset(offset).limit(page_size)
        )

        return list(result.scalars().all())

    async def create(self, **kwargs) -> ChatSession:
        """Insert a new chat session row.

        Args
            ** kwargs: Column values matching ''ChatSession'' ORM fields
            (e.g. ''title'', ''user_id'').

        Returns :
            The newly created 'ChatSession'' instance after flush.
        """
        chat_session = ChatSession(**kwargs)
        self._db_session.add(chat_session)
        await self._db_session.flush()
        return chat_session

    async def update(self, session_id: UUID, **kwargs) -> ChatSession | None:
        """Apply a partial update to an existing chat session.

        Only keys present in 'kwargs'' are written; ''None'' values are
        skipped so callers can pass 'ChatSessionUpdate. model_dump(exclude_unset=True)'

        Args:
            chat_session_id: UUID of the chat session to update.
            ** kwargs: Column-value pairs to update.

        Returns:
            The updated 'ChatSession'' instance, or 'None'' if not found.
        """
        chat_session = await self.get(session_id=session_id)
        if chat_session is None:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(chat_session, key, value)

        await self._db_session.flush()
        return chat_session

    async def delete(self, session_id: UUID) -> bool:
        """Delete a chat session by primary key.

        Args:
        chat_session_id: UUID of the chat session to delete.

        Returns :
        True  'if the chat session was deleted, ''False'' if not found.
        """
        chat_session = self.get(session_id=session_id)
        if chat_session is None:
            return False

        self._db_session.delete(chat_session)
        await self._db_session.flush()
        return True
