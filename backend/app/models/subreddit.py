from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel


class Subreddit(SQLModel, table=True):
    """Model for storing subreddit information"""
    __tablename__ = "subreddits"

    name: str = Field(primary_key=True)  # Using name as the primary key
    display_name: str
    description: Optional[str] = None
    subscribers: int = Field(default=0)
    active_users: Optional[int] = Field(default=0)  # Number of active users
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    # Metrics
    posts_per_day: Optional[float] = None
    comments_per_day: Optional[float] = None
    growth_rate: Optional[float] = None
    relevance_score: Optional[float] = Field(default=0.0)  # Score for search relevance
    last_updated: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    audiences: List["AudienceSubreddit"] = Relationship(back_populates="subreddit")
    reddit_posts: List["RedditPost"] = Relationship(back_populates="subreddit")
    
    def __repr__(self) -> str:
        return f"<Subreddit {self.name}>"
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }
        from_attributes = True
        populate_by_name = True 