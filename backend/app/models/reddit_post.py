from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlmodel import Field, ForeignKey, Relationship, SQLModel

from .subreddit import Subreddit


class RedditPost(SQLModel, table=True):
    """Reddit post model."""
    __tablename__ = "redditpost"

    id: Optional[int] = Field(default=None, primary_key=True)
    reddit_id: str = Field(unique=True, index=True)
    subreddit_name: str = Field(sa_column=Column(String, ForeignKey("subreddits.name", ondelete="CASCADE")))
    title: str
    content: str
    url: str
    author: str
    score: int = Field(default=0)
    num_comments: int = Field(default=0)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    collected_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    # New fields for enhanced post collection
    is_self: bool = Field(default=True)
    upvote_ratio: float = Field(default=1.0)
    is_original_content: bool = Field(default=False)
    distinguished: Optional[str] = Field(default=None)
    stickied: bool = Field(default=False)
    collection_source: Optional[str] = Field(default=None)
    engagement_score: float = Field(default=0.0)
    awards: dict = Field(default={}, sa_column=Column(JSON))
    
    # Relationships
    subreddit: Subreddit = Relationship(back_populates="reddit_posts")
    theme_posts: List["ThemePost"] = Relationship(back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    comments: List["Comment"] = Relationship(back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    def dict(self) -> Dict:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'reddit_id': self.reddit_id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'author': self.author,
            'score': self.score,
            'num_comments': self.num_comments,
            'created_at': self.created_at,
            'collected_at': self.collected_at,
            'subreddit_name': self.subreddit_name,
            'is_self': self.is_self,
            'upvote_ratio': self.upvote_ratio,
            'is_original_content': self.is_original_content,
            'distinguished': self.distinguished,
            'stickied': self.stickied,
            'collection_source': self.collection_source,
            'engagement_score': self.engagement_score,
            'awards': self.awards
        }

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True 