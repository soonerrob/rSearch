from datetime import datetime
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..clients.reddit import RedditClient
from ..core.config import settings
from ..models.comment import Comment
from ..models.post import Post


class CommentCollectionConfig:
    """Configuration for comment collection"""
    def __init__(
        self,
        limit_top: int = 15,
        limit_replies: int = 3,
        min_score: int = 5,
        min_length: int = 20,
        max_age_days: int = 365
    ):
        self.limit_top = limit_top
        self.limit_replies = limit_replies
        self.min_score = min_score
        self.min_length = min_length
        self.max_age_days = max_age_days


async def collect_comments_for_post(
    post_id: str,
    session: AsyncSession,
    reddit_client: RedditClient,
    config: Optional[CommentCollectionConfig] = None
) -> List[Comment]:
    """
    Collect comments for a post with smart filtering
    
    Args:
        post_id: Reddit post ID
        session: Database session
        reddit_client: Reddit API client
        config: Collection configuration
        
    Returns:
        List of collected comments
    """
    if config is None:
        config = CommentCollectionConfig()
    
    # Get post from database
    stmt = select(Post).where(Post.reddit_id == post_id)
    result = await session.execute(stmt)
    post = result.scalar_one_or_none()
    
    if not post:
        raise ValueError(f"Post {post_id} not found in database")
    
    # Get comments from Reddit
    comments_data = await reddit_client.get_post_comments(
        post_id,
        limit=config.limit_top,
        min_score=config.min_score
    )
    
    collected_comments = []
    
    for comment_data in comments_data:
        # Skip if comment is too short
        if len(comment_data.content) < config.min_length:
            continue
            
        # Create top-level comment
        comment = Comment(
            reddit_id=comment_data.id,
            content=comment_data.content,
            author=comment_data.author,
            score=comment_data.score,
            level=0,
            post_id=post.id,
            awards_received=comment_data.awards,
            is_edited=comment_data.edited
        )
        collected_comments.append(comment)
        
        # Process replies if they exist
        if comment_data.replies:
            top_replies = sorted(
                comment_data.replies,
                key=lambda x: x.score,
                reverse=True
            )[:config.limit_replies]
            
            # Filter replies
            filtered_replies = [
                r for r in top_replies 
                if r.score >= config.min_score 
                and len(r.content) >= config.min_length
            ]
            
            for reply_data in filtered_replies:
                reply = Comment(
                    reddit_id=reply_data.id,
                    content=reply_data.content,
                    author=reply_data.author,
                    score=reply_data.score,
                    level=1,
                    post_id=post.id,
                    parent_id=comment_data.id,
                    awards_received=reply_data.awards,
                    is_edited=reply_data.edited
                )
                collected_comments.append(reply)
    
    # Bulk save comments
    session.add_all(collected_comments)
    await session.commit()
    
    return collected_comments


async def update_comments(
    post_id: str,
    session: AsyncSession,
    reddit_client: RedditClient,
    min_age_hours: int = 24
) -> List[Comment]:
    """
    Update existing comments for a post
    
    Args:
        post_id: Reddit post ID
        session: Database session
        reddit_client: Reddit API client
        min_age_hours: Minimum age in hours before updating
        
    Returns:
        List of updated comments
    """
    # Get existing comments
    stmt = select(Comment).join(Post).where(Post.reddit_id == post_id)
    result = await session.execute(stmt)
    comments = result.scalars().all()
    
    now = datetime.utcnow()
    updated_comments = []
    
    for comment in comments:
        # Skip if comment was recently updated
        age = now - comment.last_updated
        if age.total_seconds() < min_age_hours * 3600:
            continue
            
        # Get updated comment data
        updated_data = await reddit_client.get_comment(comment.reddit_id)
        if updated_data:
            comment.score = updated_data.score
            comment.content = updated_data.content
            comment.is_edited = updated_data.edited
            comment.awards_received = updated_data.awards
            comment.last_updated = now
            updated_comments.append(comment)
    
    if updated_comments:
        await session.commit()
    
    return updated_comments 