"""Authentication router handling user registration, login, and token refresh flows"""

import email
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from data.db_manager import db_manager
from data.models.auth import AuthResponse, LoginRequest, RefreshTokenRequest, Token
from data.models.user import UserCreate, UserRead
from data.repositories.user_repository import UserRepository
from system.logs import logger
from utils.auth import create_token_pair, hash_password, verify_password, verify_token

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db_session: AsyncSession = Depends(db_manager.get_db_session)):
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

    token = create_token_pair(str(user.id))
    logger.info("user_registered", user_id=str(user.id))
    return AuthResponse(user=UserRead.model_validate(user), token=token)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db_session: AsyncSession = Depends(db_manager.get_db_session)):
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

    token = create_token_pair(str(user.id))
    logger.info("login_success", user_id=str(user.id))
    return AuthResponse(user=UserRead.model_validate(user), token=token)


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshTokenRequest, db_session: AsyncSession = Depends(db_manager.get_db_session)):
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

    user_id = verify_token(payload.refresh_token, token_type="refresh")

    if user_id is None:
        raise credentials_exception

    try:
        uid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = await UserRepository(db_session=db_session).get(uid)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    logger.info("token_refreshed", user_id=str(user.id))
    return create_token_pair(str(user.id))
