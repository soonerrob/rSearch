from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (ARRAY, JSON, Boolean, Column, DateTime, Float,
                        ForeignKey, Integer, String)
from sqlalchemy.orm import foreign
from sqlmodel import Field, Relationship, SQLModel

from .reddit_post import RedditPost


class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    
    id: Optional[int] = Field(default=None, sa_column=Column(Integer, primary_key=True))
    reddit_id: str = Field(unique=True, index=True)
    post_id: int = Field(sa_column=Column(Integer, ForeignKey("redditpost.id", ondelete="CASCADE")))
    parent_id: Optional[int] = Field(default=None, sa_column=Column(Integer, ForeignKey("comments.id")))
    content: str
    author: str
    score: int = Field(default=0, ge=0)
    depth: int = Field(default=0, ge=0)
    path: List[int] = Field(sa_column=Column(ARRAY(Integer), server_default="{}"))
    is_submitter: bool = Field(default=False)
    distinguished: Optional[str] = Field(default=None)
    stickied: bool = Field(default=False)
    awards: dict = Field(default_factory=dict, sa_column=Column(JSON))
    edited: bool = Field(default=False)
    engagement_score: float = Field(default=0.0)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    collected_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    # Temporary field to store Reddit parent ID during collection
    reddit_parent_id: Optional[str] = Field(default=None, exclude=True)
    
    # Relationships
    post: RedditPost = Relationship(back_populates="comments")
    parent: Optional["Comment"] = Relationship(
        back_populates="replies",
        sa_relationship_kwargs={
            "remote_side": "Comment.id"
        }
    )
    replies: List["Comment"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

    def __repr__(self):
        return f"<Comment {self.reddit_id}>" 