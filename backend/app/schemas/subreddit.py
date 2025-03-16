from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SubredditResponse(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    subscribers: Optional[int] = None
    active_users: Optional[int] = None
    posts_per_day: Optional[float] = None
    comments_per_day: Optional[float] = None
    growth_rate: Optional[float] = None
    relevance_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    )


class KeywordSuggestionResponse(BaseModel):
    keyword: str
    score: float  # Relevance score
    subreddit_count: Optional[int] = None  # Number of subreddits matching this keyword

    class Config:
        from_attributes = True 