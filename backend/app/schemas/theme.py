from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ThemeBase(BaseModel):
    category: str
    summary: str

class ThemeCreate(ThemeBase):
    audience_id: int

class ThemeUpdate(BaseModel):
    category: Optional[str] = None
    summary: Optional[str] = None

class ThemeResponse(ThemeBase):
    id: int
    audience_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ThemeWithPosts(ThemeResponse):
    posts: List[dict]  # List of posts with relevance scores 