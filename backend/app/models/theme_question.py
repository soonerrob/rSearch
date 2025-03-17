from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Column, Field, ForeignKey, Integer, Relationship, SQLModel


class ThemeQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    theme_id: int = Field(sa_column=Column(Integer, ForeignKey("theme.id", ondelete="CASCADE"), index=True))
    question: str
    answer: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_recalculated_at: Optional[datetime] = None
    
    # Relationships
    theme: "Theme" = Relationship(back_populates="questions") 