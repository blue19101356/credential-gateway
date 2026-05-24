"""Application / client registration model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ed25519_public_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    x25519_public_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_applications_status_name", "status", "name"),
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} name={self.name!r} status={self.status!r}>"
