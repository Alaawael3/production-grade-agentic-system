"""Chat session router - CRUD endpoints protected by JWT auth."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from data.db_manager import db_manager
from data.models.session import ChatSessionCreate, ChatSessionRead, ChatSessionUpdate
from data.repositories import ChatSessionRepository
from data.schemas.user import User
from system.logs import logger
from system.rate_limiting import limiter
from utils.auth import get_current_user


router = APIRouter()

@router.post("", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_CREATE_CHAT_SESSION)
async def create_chat_session(
    request: Request,
    response: Response,
    payload: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(db_manager.get_db_session),
) -> ChatSessionRead:
    """Create a new chat session for the authenticated user.

    Args:
        payload: Request body containing the session title.
        current_user: Authenticated user from JWT dependency.
        db_session: Injected async database session.

    Returns:
        ChatSessionRead: The newly created chat session.
    """
    chat_session = await ChatSessionRepository(db_session).create(
        user_id=current_user.id, title=payload.title
    )
    logger.info(
        "chat_session_created",
        chat_session_id=chat_session.id,
        title=payload.title,
    )

    return ChatSessionRead.model_validate(chat_session)


@router.get("", response_model=list[ChatSessionRead])
@limiter.limit(settings.RATE_LIMIT_GET_CHAT_SESSIONS)
async def get_chat_sessions(
    request: Request,
    response: Response,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(db_manager.get_db_session),
) -> list[ChatSessionRead]:
    """List all chat sessions belonging to the authenticated user.

    Args:
        page: 1-based page number (default 1).
        page_size: Number of sessions per page (default 20).
        current_user: Authenticated user from JWT dependency.
        db_session: Injected async database session.

    Returns:
        list[ChatSessionRead]: Paginated list of chat sessions owned by the current user.
    """
    chat_sessions = await ChatSessionRepository(db_session).get_all(
        user_id=current_user.id, page=page, page_size=page_size
    )
    logger.info(
        "chat_sessions_retrieved",
        count=len(chat_sessions),
    )
    return [ChatSessionRead.model_validate(session) for session in chat_sessions]


@router.get("/{session_id}", response_model=ChatSessionRead)
@limiter.limit(settings.RATE_LIMIT_GET_CHAT_SESSION)
async def get_chat_session(
    request: Request,
    response: Response,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(db_manager.get_db_session),
) -> ChatSessionRead:
    """get chat session belonging to the authenticated user.

    Args:
        current_user: Authenticated user from JWT dependency.
        db_session: Injected async database session.

    Returns:
        ChatSessionRead: The requested chat session.
    """

    chat_session = await ChatSessionRepository(db_session).get(session_id=session_id)
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session with ID {session_id} not found.",
        )

    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )
    
    logger.info(
        "chat_session_retrieved",
        session_id=session_id
    )
    return ChatSessionRead.model_validate(chat_session)


@router.patch("/{session_id}", response_model=ChatSessionRead)
@limiter.limit(settings.RATE_LIMIT_UPDATE_CHAT_SESSION)
async def update_chat_session(
    request: Request,
    response: Response,
    session_id: UUID,
    payload: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(db_manager.get_db_session),
) -> ChatSessionRead:
    """Partially update a chat session's title.

    Args:
        session_id: UUID of the chat session to update.
        payload: Request body with the optional new title.
        current_user: Authenticated user from JWT dependency.
        db_session: Injected async database session.

    Returns:
        ChatSessionRead: The updated chat session.

    Raises:
        HTTPException: 404 if the session does not exist.
        HTTPException: 403 if the session belongs to another user.
    """

    repo = ChatSessionRepository(db_session)

    chat_session = await repo.get(session_id=session_id)

    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session with ID {session_id} not found.",
        )

    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )

    chat_session = await repo.update(session_id,**payload.model_dump(exclude_unset=True))
    logger.info(
        "chat_session_updated",
        session_id=session_id,
        updated_fields=list(payload.model_dump(exclude_unset=True).keys()),
    )
    return ChatSessionRead.model_validate(chat_session)


@router.delete("/{session_id}", response_model=ChatSessionRead)
@limiter.limit(settings.RATE_LIMIT_DELETE_CHAT_SESSION)
async def delete_chat_session(
    request: Request,
    response: Response,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(db_manager.get_db_session),
) -> None:
    """Delete a chat session permanently.

    Args :
        session_id: UUID of the chat session to delete.
        current_user: Authenticated user from JWT dependency.
        db_session: Injected async database session.

    Raises:
        HTTPException: 404 if the session does not exist.
        HTTPException: 403 if the session belongs to another user.
    """
    repo = ChatSessionRepository(db_session)
    chat_session = await repo.get(session_id=session_id)

    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session with ID {session_id} not found.",
        )

    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )

    await repo.delete(session_id=session_id)
    logger.info(
        "chat_session_deleted",
        session_id=session_id,
    )

    