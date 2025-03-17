from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class TimestampedBase(SQLModel):
    """Base model with created_at and updated_at fields"""
    __abstract__ = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP"}
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP", "onupdate": lambda: datetime.now(timezone.utc)}
    ) 