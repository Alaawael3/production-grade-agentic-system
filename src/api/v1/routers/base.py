"""check endpoints health"""

from datetime import datetime, UTC

from fastapi import APIRouter
from config.settings import settings
from system.logs import logger

router = APIRouter()

@router.get("/health")
async def health_check():
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