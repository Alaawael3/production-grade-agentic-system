"""fastapi application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.v1 import v1_router
from config.settings import settings
from data.db_manager import db_manager
from system.logs import logger
from system.rate_limiting import limiter
from system.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application stardtup and shutdown lifecycle"""

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


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_VERSION}/openapi.json",
    lifespan=lifespan,
)


app.include_router(v1_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestContextMiddleware)

def main():
    print("Hello from production-grade-agentic-system!")


if __name__ == "__main__":
    main()
