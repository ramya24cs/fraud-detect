
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"

    
    __table_args__ = (
        Index("idx_transactions_external_id", "external_id"),
        Index("ix_transactions_user_id", "user_id"),
        UniqueConstraint(
            "user_id",
            "external_id",
            name="uq_transactions_user_external_id",
        ),
    )


    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    external_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
