"""Request logging middleware."""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("credential_gateway.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        app_id = getattr(request.state, "app_id", "-")
        logger.info(
            "method=%s path=%s status=%d app_id=%s elapsed_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            app_id,
            elapsed_ms,
        )
        return response
