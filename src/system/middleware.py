"""ASGI middleware for request-scoped logging context.

Ensures structlog contextvars do not leak between requests.
"""

import os
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from fastapi import Request
from starlette.responses import Response
from structlog.contextvars import clear_contextvars
from system.logs import logger

class RequestContextMiddleware(BaseHTTPMiddleware):
    """ASGI middleware for request-scoped logging context.

    Ensures structlog contextvars do not leak between requests.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Clear contextvars before and after handling a request.

        Args:
            request: Incoming ASGI request.
            call_next: Callable that forwards the request to the next
                middleware/handler and returns its response.

        Returns:
            Response: The response produced downstream.
        """
        logger.debug("RequestContextMiddleware: Clearing contextvars before request")
        clear_contextvars()
        try:    
            logger.debug("RequestContextMiddleware: clearing contextvars before request 2nd time")
            response = await call_next(request)
        finally: # run whatever try happens or not
            clear_contextvars()
        return response

