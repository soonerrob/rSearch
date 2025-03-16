from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ThemeQuestionBase(BaseModel):
    question: str


class ThemeQuestionCreate(ThemeQuestionBase):
    theme_id: int


class ThemeQuestionUpdate(ThemeQuestionBase):
    answer: Optional[str] = None
    last_recalculated_at: Optional[datetime] = None


class ThemeQuestion(ThemeQuestionBase):
    id: int
    theme_id: int
    answer: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_recalculated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 