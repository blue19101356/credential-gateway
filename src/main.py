"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.database import engine, Base
from src.middleware.auth import AuthMiddleware
from src.middleware.ratelimit import RateLimitMiddleware
from src.middleware.logging import LoggingMiddleware
from src.api.v1.health import router as health_router
from src.api.v1.applications import router as applications_router
from src.api.v1.credentials import router as credentials_router
from src.utils.exceptions import AppException, app_exception_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("credential_gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} on {settings.app_host}:{settings.app_port}")

    # Auto-create tables for SQLite dev mode
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Created database tables (SQLite)")

    yield

    await engine.dispose()
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title="Credential Gateway",
    description="Zero-knowledge credential vault with Ed25519 auth and ECIES encryption",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=None)
app.add_middleware(AuthMiddleware)

app.add_exception_handler(AppException, app_exception_handler)

app.include_router(health_router)
app.include_router(applications_router)
app.include_router(credentials_router)

# Mount client portal and admin UI
try:
    app.mount("/portal", StaticFiles(directory="client_ui", html=True), name="portal")
except RuntimeError:
    pass

# Mount admin UI static files
try:
    app.mount("/admin", StaticFiles(directory="admin_ui", html=True), name="admin")
except RuntimeError:
    pass
