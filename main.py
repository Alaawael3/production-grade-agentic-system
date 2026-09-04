"""fastapi application"""

from contextlib import asynccontextmanager
from sys import version

from fastapi import FastAPI
from data.db_manager import db_manager
from config.settings import settings
from system.logs import logger
from api.v1 import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown lifecycle"""

    # Startup
    logger.info("application_startup", project_name=settings.PROJECT_NAME, version=settings.VERSION)

    await db_manager.check_connection()
    logger.info("database_connection_successful")
    
    try:
        yield
        # running
    finally:
        logger.info("qpplication_shutdown")
        # Shutdown


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, openapi_url=f"{settings.API_VERSION}/openapi.json", lifespan=lifespan)


app.include_router(v1_router)

def main():
    print("Hello from production-grade-agentic-system!")


if __name__ == "__main__":
    main()
