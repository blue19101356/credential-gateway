"""Credential CRUD operations with ECIES encryption."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.models.credential import Credential
from src.models.application import Application
from src.crypto.encryption import encrypt_string, load_x25519_public_key
from src.utils.validators import validate_credential_name, validate_credential_type
from src.utils.exceptions import CredentialNotFound
from src.services.processors import get_processor


async def store_credential(
    session: AsyncSession,
    app: Application,
    type_: str,
    name: str,
    plaintext: str,
    tags: str | None = None,
) -> Credential:
    name = validate_credential_name(name)
    type_ = validate_credential_type(type_)

    processor = get_processor(type_)
    if not processor.validate(plaintext):
        raise ValueError(f"Invalid {type_} credential format")

    recipient_pub = load_x25519_public_key(app.x25519_public_key)
    encrypted_data = encrypt_string(plaintext, recipient_pub)

    credential = Credential(
        application_id=app.id,
        name=name,
        type=type_,
        encrypted_data=encrypted_data,
        tags=tags,
    )
    session.add(credential)
    await session.flush()
    await session.refresh(credential)
    return credential


async def retrieve_credential(
    session: AsyncSession,
    app: Application,
    credential_id: str,
) -> Credential:
    result = await session.execute(
        select(Credential).where(
            Credential.id == credential_id,
            Credential.application_id == app.id,
        )
    )
    cred = result.scalar_one_or_none()
    if cred is None:
        raise CredentialNotFound(credential_id)
    return cred


async def list_credentials(
    session: AsyncSession,
    app: Application,
    type_: str | None = None,
) -> list[Credential]:
    stmt = select(Credential).where(Credential.application_id == app.id)
    if type_:
        type_ = validate_credential_type(type_)
        stmt = stmt.where(Credential.type == type_)
    stmt = stmt.order_by(Credential.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_credential(
    session: AsyncSession,
    app: Application,
    credential_id: str,
) -> None:
    result = await session.execute(
        delete(Credential).where(
            Credential.id == credential_id,
            Credential.application_id == app.id,
        )
    )
    if result.rowcount == 0:
        raise CredentialNotFound(credential_id)
