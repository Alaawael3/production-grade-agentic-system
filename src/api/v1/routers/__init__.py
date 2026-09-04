"""api v1 routers pachaeg"""

from .auth import router as auth_router
from .base import router as base_router

__all__ = ["base_router", "auth_router"]
