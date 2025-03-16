from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import TimestampedBase


class Comment(TimestampedBase, table=True):
    """Model for storing Reddit comments with smart filtering for AI analysis"""
    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    reddit_id: str = Field(unique=True, index=True)
    content: str
    author: str
    score: int = Field(default=0)
    
    # Hierarchy tracking
    parent_id: Optional[str] = Field(default=None, index=True)  # reddit_id of parent comment
    level: int = Field(default=0)  # 0 for top-level comments
    
    # Metrics
    awards_received: int = Field(default=0)
    is_edited: bool = Field(default=False)
    
    # Collection metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    post_id: int = Field(foreign_key="posts.id")
    post: "Post" = Relationship(back_populates="comments")
    
    # Hierarchy relationships
    parent_comment_id: Optional[int] = Field(default=None, foreign_key="comments.id")
    replies: List["Comment"] = Relationship(
        back_populates="parent"
    )
    parent: Optional["Comment"] = Relationship(
        back_populates="replies",
        sa_relationship_kwargs={
            "remote_side": "Comment.id",
            "cascade": "all, delete-orphan",
            "single_parent": True
        }
    )

    def __repr__(self) -> str:
        return f"<Comment {self.reddit_id}>"

    class Config:
        from_attributes = True 