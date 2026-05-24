"""Application authentication and Ed25519 signature verification."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.application import Application
from src.crypto.ecc_manager import load_public_key, verify
from src.crypto.hashing import sha256
from src.utils.exceptions import (
    AuthenticationError,
    ApplicationNotFound,
    ApplicationRevoked,
)


async def authenticate(
    session: AsyncSession,
    app_id: str,
    signature_hex: str,
    body: bytes,
    timestamp: int | None = None,
    nonce: str | None = None,
) -> Application:
    result = await session.execute(
        select(Application).where(Application.id == app_id)
    )
    app = result.scalar_one_or_none()

    if app is None:
        raise ApplicationNotFound(app_id)

    if app.status == "revoked":
        raise ApplicationRevoked(app_id)

    try:
        signature_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        raise AuthenticationError("Invalid signature encoding")

    public_key = load_public_key(app.ed25519_public_key)
    digest = sha256(body)

    if not verify(public_key, signature_bytes, digest):
        raise AuthenticationError("Signature verification failed")

    return app
