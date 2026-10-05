"""Authentication router handling user registration, login, and token refresh flows"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from data.db_manager import db_manager
from data.models.auth import AuthResponse, LoginRequest, RefreshTokenRequest, Token
from data.models.user import UserCreate, UserRead
from data.repositories import UserRepository, UserSessionRepository
from data.schemas.user_session import UserSession
from system.logs import logger
from structlog.contextvars import bind_contextvars
from system.rate_limiting import limiter

from utils.auth import (
    create_token_pair,
    hash_password,
    verify_password,
    verify_token,
    get_current_session,
    get_current_user,
    get_session_id_from_claim,
)

router = APIRouter()


async def _start_session(user_id: UUID, db_session: AsyncSession) -> UserSession:
    """Mint a new session family for a fresh login.

    Args:
        db_session: Injected async database session.
        user_id: Owner of the new session.

    Returns:
        The newly created live ''UserSession''
    """
    now = datetime.now(UTC)
    return await UserSessionRepository(db_session=db_session).create(
        user_id=user_id,
        family_created_at=now,
        family_id=uuid4(),
        expires_at=now
        + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),  # Example expiration, adjust as needed
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limits(settings.RATE_LIMIT_REGISTER)
async def register(payload: UserCreate, db_session: AsyncSession = Depends(db_manager.get_db_session), request: Request, response: Response):
    """Register a new user account and return an authenticated session.

    Args:
        payload: Registration data including name, email, and password.
        db_session: Injected async database session.

    Returns:
        AuthResponse containing the created user and a JWT token pair.

    Raises:
        HTTPException: 409 if the email address is already registered.
    """
    repo = UserRepository(db_session=db_session)

    # check user exists?
    if await repo.get_by_email(payload.email):
        logger.warning("registration_failed", email=payload.email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # create user
    user = await repo.create(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        hashed_password=hash_password(payload.password.get_secret_value()),
    )
    session = await _start_session(user_id=user.id, db_session=db_session)
    bind_contextvars(user_id=str(user.id), session_id=str(session.id))

    token = create_token_pair(str(user.id), str(session.id))
    logger.info("user_registered", user_id=str(user.id))
    return AuthResponse(user=UserRead.model_validate(user), token=token)


@router.post("/login", response_model=AuthResponse)
@limiter.limits(settings.RATE_LIMIT_LOGIN)
async def login(payload: LoginRequest, db_session: AsyncSession = Depends(db_manager.get_db_session), request: Request, response: Response):
    """Authenticate with email/password and return a token pair.

    Args:
        payload: Login credentials - email and password.
        db_session: Injected async database session.

    Returns:
        AuthResponse containing the authenticated user and a JWT token pair.

    Raises:
        HTTPException: 401 if credentials are invalid.
        HTTPException: 403 if the account is inactive.
    """
    repo = UserRepository(db_session=db_session)
    user = await repo.get_by_email(payload.email)

    if user is None or not verify_password(payload.password.get_secret_value(), user.hashed_password):
        logger.warning("login_failed", email=payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Wuthenticatie": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account distabled")

    session = await _start_session(user_id=user.id, db_session=db_session)
    token = create_token_pair(str(user.id), str(session.id))
    logger.info("login_success", user_id=str(user.id))
    return AuthResponse(user=UserRead.model_validate(user), token=token)


@router.post("/refresh", response_model=Token)
@limiter.limits(settings.RATE_LIMIT_REFRESH)
async def refresh(payload: RefreshTokenRequest, db_session: AsyncSession = Depends(db_manager.get_db_session), request: Request, response: Response):
    """Exchange a valid refresh token for a new token pair.

    Args:
        payload: Request body containing the refresh token.
        db_session: Injected async database session.

    Returns:
        A new JWT token pair.

    Raises:
        HTTPException: 401 if the token is invalid or expired.
        HTTPException: 403 if the account is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    claims = verify_token(payload.refresh_token, token_type="refresh")
    if claims is None:
        raise credentials_exception

    session_id = get_session_id_from_claim(claims)
    if session_id is None:
        raise credentials_exception

    repo = UserSessionRepository(db_session=db_session)
    session = await repo.get_live(session_id)
    if session is None:
        existing_session = await repo.get(session_id)
        if existing_session is not None and existing_session.revoked_at is not None:
            await repo.revoke_family(existing_session.family_id)
            logger.warning("refresh_token_revoked", session_id=str(session_id), family_id=str(existing_session.family_id))
        raise credentials_exception

    user = session.user
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await repo.revoke(session.id)
    new_session = await repo.create(
        user_id=user.id,
        family_id=session.family_id,
        family_created_at=session.family_created_at,
        expires_at=datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )

    logger.info("refresh_token_success", user_id=str(user.id), old_session_id=str(session.id), new_session_id=str(new_session.id))
    bind_contextvars(user_id=str(user.id), session_id=str(new_session.id))
    return create_token_pair(str(user.id), str(new_session.id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limits(settings.RATE_LIMIT_DEFAULT)
async def logout(session: UserSession = Depends(get_current_session), db_session: AsyncSession = Depends(db_manager.get_db_session), request: Request, response: Response) -> Response:
    """End the current device's session, leaving the user's others running.

    The whole rotation chain is revoked rather than just the current row, so a
    stale refresh token from this device later reads as an ordinary dead session
    instead of raising a reuse alarm.

    Args:
        request: Incoming request, required by the rate limiter.
        session: The live session behind the request.
        db_session: Injected async database session.

    Returns:
        An empty 204 response.
    """

    revoked = await UserSessionRepository(db_session=db_session).revoke_family(session.family_id)
    logger.info("logout_success", user_id=str(session.user_id), session_id=str(session.id), family_id=str(session.family_id), revoked_count=revoked)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limits(settings.RATE_LIMIT_DEFAULT)
async def logout_all(
    user: UserSession = Depends(get_current_user), db_session: AsyncSession = Depends(db_manager.get_db_session), request: Request, response: Response
) -> Response:
    """End the current user's sessions.

    Args:
        request: Incoming request, required by the rate limiter.
        user: The current user.
        db_session: Injected async database session.

    Returns:
        An empty 204 response.
    """

    revoked = await UserSessionRepository(db_session=db_session).revoke_all(user.id)
    logger.info(
        "all_sessions_closed",
        user_id=str(user.id),
        revoked_count=revoked,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
@limiter.limits(settings.RATE_LIMIT_DEFAULT)
async def get_me(user: UserSession = Depends(get_current_user), request: Request, response: Response) -> UserRead:
    """Return the current user's profile.

    Args:
        user: The current user, injected by FastAPI.

    Returns:
        The current user's profile.
    """
    return UserRead.model_validate(user)

