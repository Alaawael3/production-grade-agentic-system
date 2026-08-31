"""fastapi application"""

from contextlib import asynccontextmanager
from sys import version

from fastapi import FastAPI

from config.settings import settings
from system.logs import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown lifecycle"""

    # Startup
    logger.info("application_startup", project_name=settings.PROJECT_NAME, version=settings.VERSION)

    try:
        yield
        # running
    finally:
        logger.info("qpplication_shutdown")
        # Shutdown


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)


def main():
    print("Hello from production-grade-agentic-system!")


if __name__ == "__main__":
    main()
