from datetime import datetime
from typing import List, Optional

from sqlmodel import Column, Field, ForeignKey, Integer, Relationship, SQLModel

from .audience import Audience
from .theme_question import ThemeQuestion


class ThemePost(SQLModel, table=True):
    theme_id: int = Field(sa_column=Column(Integer, ForeignKey("theme.id", ondelete="CASCADE"), primary_key=True))
    post_id: int = Field(sa_column=Column(Integer, ForeignKey("redditpost.id", ondelete="CASCADE"), primary_key=True))
    relevance_score: float = Field(default=0.0)  # AI-generated relevance score
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    theme: "Theme" = Relationship(back_populates="theme_posts")
    post: "RedditPost" = Relationship(back_populates="theme_posts")


class Theme(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    audience_id: int = Field(sa_column=Column(Integer, ForeignKey("audiences.id", ondelete="CASCADE")))
    category: str = Field(index=True)  # e.g., "Hot Discussions", "Advice Requests", etc.
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    audience: Audience = Relationship(back_populates="themes")
    theme_posts: List[ThemePost] = Relationship(back_populates="theme")
    questions: List[ThemeQuestion] = Relationship(back_populates="theme") 