"""Encrypted credential storage model."""

import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import String, DateTime, Text, ForeignKey, func, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    encrypted_data: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_credentials_app_name", "application_id", "name"),
        Index("ix_credentials_app_type", "application_id", "type"),
    )

    def __repr__(self) -> str:
        return f"<Credential id={self.id} name={self.name!r} type={self.type!r}>"
