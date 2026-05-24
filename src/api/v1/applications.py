"""Application management endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_session
from src.models.application import Application
from src.utils.validators import validate_ed25519_public_key, validate_x25519_public_key
from src.utils.exceptions import ApplicationNotFound

router = APIRouter(prefix="/v1/applications", tags=["applications"])


class RegisterApplicationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    ed25519_public_key: str = Field(..., description="Ed25519 public key in PEM format")
    x25519_public_key: str = Field(..., description="X25519 public key in PEM format")


class ApplicationResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """List all applications. Requires admin token."""
    result = await session.execute(select(Application).order_by(Application.created_at.desc()))
    return list(result.scalars().all())


@router.post("", status_code=201, response_model=ApplicationResponse)
async def register_application(
    req: RegisterApplicationRequest,
    session: AsyncSession = Depends(get_session),
):
    validate_ed25519_public_key(req.ed25519_public_key)
    validate_x25519_public_key(req.x25519_public_key)

    app = Application(
        name=req.name,
        ed25519_public_key=req.ed25519_public_key.strip(),
        x25519_public_key=req.x25519_public_key.strip(),
    )
    session.add(app)
    await session.commit()
    await session.refresh(app)
    return app


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Application).where(Application.id == app_id)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise ApplicationNotFound(app_id)
    return app


@router.delete("/{app_id}", status_code=204)
async def revoke_application(
    app_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Application).where(Application.id == app_id)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise ApplicationNotFound(app_id)

    app.status = "revoked"
    await session.commit()
    return None
