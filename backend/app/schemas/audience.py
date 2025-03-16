from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AudienceBase(BaseModel):
    name: str
    description: Optional[str] = None
    timeframe: str = Field(
        default="year",
        description="Time period for collecting posts",
        pattern="^(hour|day|week|month|year|all)$"
    )

class AudienceCreate(AudienceBase):
    subreddit_names: List[str]
    posts_per_subreddit: int = 500  # Default to 500 posts per subreddit

class AudienceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subreddit_names: Optional[List[str]] = None
    timeframe: Optional[str] = Field(
        default=None,
        pattern="^(hour|day|week|month|year|all)$"
    )
    posts_per_subreddit: Optional[int] = None

class AudienceResponse(AudienceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    posts_per_subreddit: int = 100
    is_collecting: bool = False
    post_count: int = 0  # Total number of posts in the audience

class AudienceWithSubreddits(AudienceResponse):
    subreddit_names: List[str] 