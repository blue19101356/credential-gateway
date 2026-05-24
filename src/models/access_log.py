"""Access / audit log model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    credential_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("credentials.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("ix_access_logs_app_timestamp", "application_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AccessLog id={self.id} action={self.action!r}>"
