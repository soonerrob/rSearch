from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, ForeignKey, Integer, Relationship, SQLModel


class Audience(SQLModel, table=True):
    """Model for storing audience information"""
    __tablename__ = "audiences"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_collection_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True)),
        default=None
    )
    timeframe: str = Field(default="year")  # Options: hour, day, week, month, year, all
    posts_per_subreddit: int = Field(default=300)  # Number of posts to fetch per subreddit
    is_collecting: bool = Field(default=False)  # Track if initial data collection is in progress
    collection_progress: float = Field(default=0.0)  # Track collection progress from 0 to 100
    
    # Relationships
    subreddits: List["AudienceSubreddit"] = Relationship(back_populates="audience", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    themes: List["Theme"] = Relationship(back_populates="audience", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }
        from_attributes = True


class AudienceSubreddit(SQLModel, table=True):
    """Junction table for many-to-many relationship between audiences and subreddits"""
    __tablename__ = "audience_subreddits"

    audience_id: int = Field(sa_column=Column(Integer, ForeignKey("audiences.id", ondelete="CASCADE"), primary_key=True))
    subreddit_name: str = Field(foreign_key="subreddits.name", primary_key=True)
    added_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    audience: Audience = Relationship(back_populates="subreddits")
    subreddit: "Subreddit" = Relationship(back_populates="audiences")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }
        from_attributes = True 