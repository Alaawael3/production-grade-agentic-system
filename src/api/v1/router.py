"""V1 aPI routeer aggregating all versioning sub-routers"""

from fastapi import APIRouter

from .routers import base_router, auth_router, chat_session_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(base_router, tags=["health"])
v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
v1_router.include_router(chat_session_router, prefix="/chat-sessions", tags=["chat-sessions"])
