from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TimestampedBase(SQLModel):
    """Base model with created_at and updated_at fields"""
    __abstract__ = True

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        nullable=True,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    ) 