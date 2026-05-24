"""Credential management endpoints."""

from datetime import datetime
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_session
from src.models.application import Application
from src.models.credential import Credential
from src.services.credential_service import (
    store_credential,
    retrieve_credential,
    list_credentials,
    delete_credential,
)
from src.services.audit_service import log_access
from src.utils.exceptions import ApplicationNotFound, ApplicationRevoked

router = APIRouter(prefix="/v1/credentials", tags=["credentials"])


async def _get_current_app(request: Request, session: AsyncSession = Depends(get_session)) -> Application:
    app_id = getattr(request.state, "app_id", None)
    if not app_id:
        raise ApplicationNotFound("unknown")

    result = await session.execute(
        select(Application).where(Application.id == app_id)
    )
    app = result.scalar_one_or_none()

    if app is None:
        raise ApplicationNotFound(app_id)
    if app.status == "revoked":
        raise ApplicationRevoked(app_id)

    return app


class StoreCredentialRequest(BaseModel):
    type: str = Field(..., description="Credential type: api_key, db_password, ssh_key, cloud_key, generic")
    name: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, description="The plaintext credential value to encrypt and store")
    tags: str | None = None


class CredentialResponse(BaseModel):
    id: str
    name: str
    type: str
    tags: str | None
    encrypted_data: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CredentialListItem(BaseModel):
    id: str
    name: str
    type: str
    tags: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", status_code=201, response_model=CredentialResponse)
async def store(
    req: StoreCredentialRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    app = await _get_current_app(request, session)
    credential = await store_credential(
        session=session,
        app=app,
        type_=req.type,
        name=req.name,
        plaintext=req.value,
        tags=req.tags,
    )
    await log_access(
        session=session,
        application_id=app.id,
        action="store",
        ip_address=request.client.host if request.client else "unknown",
        credential_id=credential.id,
    )
    await session.commit()
    return credential


@router.get("", response_model=list[CredentialListItem])
async def list_all(
    request: Request,
    type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    app = await _get_current_app(request, session)
    credentials = await list_credentials(session=session, app=app, type_=type)
    await log_access(
        session=session,
        application_id=app.id,
        action="list",
        ip_address=request.client.host if request.client else "unknown",
    )
    await session.commit()
    return credentials


@router.get("/{credential_id}", response_model=CredentialResponse)
async def retrieve(
    credential_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    app = await _get_current_app(request, session)
    credential = await retrieve_credential(
        session=session, app=app, credential_id=credential_id
    )
    await log_access(
        session=session,
        application_id=app.id,
        action="retrieve",
        ip_address=request.client.host if request.client else "unknown",
        credential_id=credential.id,
    )
    await session.commit()
    return credential


@router.delete("/{credential_id}", status_code=204)
async def delete(
    credential_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    is_admin = getattr(request.state, "is_admin", False)
    if is_admin:
        # Admin bypass: delete directly without app ownership check
        result = await session.execute(
            select(Credential).where(Credential.id == credential_id)
        )
        cred = result.scalar_one_or_none()
        if cred is None:
            raise CredentialNotFound(credential_id)
        await session.delete(cred)
        await log_access(
            session=session,
            application_id=cred.application_id,
            action="delete",
            ip_address=request.client.host if request.client else "unknown",
            credential_id=credential_id,
        )
    else:
        app = await _get_current_app(request, session)
        await delete_credential(session=session, app=app, credential_id=credential_id)
        await log_access(
            session=session,
            application_id=app.id,
            action="delete",
            ip_address=request.client.host if request.client else "unknown",
            credential_id=credential_id,
        )
    await session.commit()
    return None
