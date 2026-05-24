"""Audit logging for all credential access operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.access_log import AccessLog


async def log_access(
    session: AsyncSession,
    application_id: str,
    action: str,
    ip_address: str,
    credential_id: str | None = None,
) -> AccessLog:
    log_entry = AccessLog(
        application_id=application_id,
        credential_id=credential_id,
        action=action,
        ip_address=ip_address,
    )
    session.add(log_entry)
    return log_entry
