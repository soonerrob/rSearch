from datetime import datetime
from typing import List, Optional

from sqlmodel import (ARRAY, Column, Field, ForeignKey, Integer, SQLModel,
                      String)


class PostAnalysis(SQLModel, table=True):
    """Stores analysis results for a Reddit post."""
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(sa_column=Column(Integer, ForeignKey("redditpost.id", ondelete="CASCADE")))
    matching_themes: List[str] = Field(sa_type=ARRAY(String))  # List of theme categories this post matches
    keywords: List[str] = Field(sa_type=ARRAY(String))  # Extracted keywords from post
    analyzed_at: datetime = Field(default_factory=datetime.utcnow) 