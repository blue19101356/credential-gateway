"""Sliding window rate limiting middleware using Redis."""

import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import settings

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or self.redis is None:
            return await call_next(request)

        if request.url.path in EXEMPT_PATHS or request.url.path.startswith("/admin"):
            return await call_next(request)

        app_id = getattr(request.state, "app_id", "anonymous")
        key = f"ratelimit:{app_id}:{request.url.path}"

        now = time.time()
        window_start = now - settings.rate_limit_window_seconds

        try:
            async with self.redis.pipeline() as pipe:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, settings.rate_limit_window_seconds + 1)
                _, count, _, _ = await pipe.execute()

            if count >= settings.rate_limit_default:
                return JSONResponse(
                    status_code=429,
                    content={"error": {"code": "rate_limit_exceeded", "message": "Rate limit exceeded. Try again later."}},
                )
        except Exception:
            pass

        return await call_next(request)
