from datetime import datetime
from typing import List, Optional

from sqlmodel import Column, Field, ForeignKey, Relationship, SQLModel, String

from .subreddit import Subreddit


class RedditPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reddit_id: str = Field(unique=True, index=True)
    subreddit_name: str = Field(sa_column=Column(String, ForeignKey("subreddits.name", ondelete="CASCADE")))
    title: str
    content: str
    author: str
    score: int = Field(default=0)
    num_comments: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    subreddit: Subreddit = Relationship(back_populates="reddit_posts")
    theme_posts: List["ThemePost"] = Relationship(back_populates="post") 