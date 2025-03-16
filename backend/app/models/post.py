from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from .base import TimestampedBase
from .comment import Comment


class Post(TimestampedBase, table=True):
    """Model for storing Reddit posts"""
    __tablename__ = "posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    reddit_id: str = Field(unique=True, index=True)
    title: str = Field(max_length=500)
    content: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None, max_length=2000)
    
    # Metrics
    score: int = Field(default=0)
    upvote_ratio: float = Field(default=1.0)
    num_comments: int = Field(default=0)
    is_original_content: bool = Field(default=False)
    
    # Relationships
    subreddit_name: str = Field(foreign_key="subreddits.name")
    subreddit: "Subreddit" = Relationship(back_populates="posts")
    comments: List["Comment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def __repr__(self) -> str:
        return f"<Post {self.reddit_id}>" 