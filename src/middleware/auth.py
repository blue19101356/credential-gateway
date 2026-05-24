"""Ed25519 signature verification middleware.

Extracts X-App-Id and X-Signature headers, verifies the Ed25519 signature
against SHA256(request_body), and stores the authenticated application ID
in request.state for downstream route handlers.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import async_session_factory
from src.config import settings
from src.services.auth_service import authenticate
from src.utils.exceptions import AppException

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health, docs, and admin UI
        if request.url.path in EXEMPT_PATHS or request.url.path.startswith('/admin') or request.url.path.startswith('/portal'):
            return await call_next(request)

        # Skip auth for application registration
        if request.method == "POST" and request.url.path == "/v1/applications":
            return await call_next(request)

        app_id = request.headers.get("X-App-Id")
        signature = request.headers.get("X-Signature")

        # Admin token bypass
        admin_token = request.headers.get("X-Admin-Token")
        if admin_token and admin_token == settings.admin_token:
            request.state.is_admin = True
            return await call_next(request)

        if not app_id or not signature:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "authentication_error", "message": "Missing X-App-Id or X-Signature header"}},
            )

        body = await request.body()

        async with async_session_factory() as session:
            try:
                app = await authenticate(
                    session=session,
                    app_id=app_id,
                    signature_hex=signature,
                    body=body,
                )
                request.state.app_id = app.id
                request.state.app_name = app.name
            except AppException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"error": {"code": e.code, "message": e.message}},
                )

        return await call_next(request)
