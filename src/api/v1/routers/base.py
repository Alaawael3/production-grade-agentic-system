"""check endpoints health"""

from datetime import datetime, UTC

from fastapi import APIRouter, Request
from config.settings import settings
from system.logs import logger
from system.rate_limiting import limiter

router = APIRouter()


@router.get("/health")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def health_check(request: Request):
    """Return application health status.

    Returns:
        dict: App name, version, current UTC datetime, and status string.
    """
    logger.info("health check called")
    return {
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "current_datetime": datetime.now(UTC),
        "status": "healthy"
    }
