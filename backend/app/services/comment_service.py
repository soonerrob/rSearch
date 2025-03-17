from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..clients.reddit import RedditClient
from ..core.config import settings
from ..models.comment import Comment
from ..models.reddit_post import RedditPost


class CommentCollectionConfig:
    """Configuration for comment collection"""
    def __init__(
        self,
        limit_top: int = 25,
        max_depth: int = 5,
        min_score: int = 2,
        min_length: int = 20,
        max_age_days: int = 365
    ):
        self.limit_top = limit_top
        self.max_depth = max_depth
        self.min_score = min_score
        self.min_length = min_length
        self.max_age_days = max_age_days


async def process_comment_tree(
    comment_data: dict,
    post_id: int,
    depth: int,
    parent_comment: Optional[Comment],
    config: CommentCollectionConfig,
    comment_map: Dict[str, Comment]
) -> List[Comment]:
    """Process a comment and its replies recursively"""
    if depth > config.max_depth:
        return []
        
    # Skip if comment is too short or score too low
    if (len(comment_data.get("body", "")) < config.min_length or 
        comment_data.get("score", 0) < config.min_score):
        return []
    
    comments = []
    
    # Get parent comment from map if it exists
    reddit_parent_id = comment_data.get("parent_id", "")
    parent = None
    
    # Handle comment parent (t1_*) vs post parent (t3_*)
    if reddit_parent_id.startswith("t1_"):
        reddit_parent_id = reddit_parent_id.replace("t1_", "")
        parent = parent_comment or comment_map.get(reddit_parent_id)
    
    # Create comment
    comment = Comment(
        reddit_id=comment_data["id"],
        post_id=post_id,
        parent_id=parent.id if parent else None,
        content=comment_data.get("body", ""),
        author=comment_data.get("author", "[deleted]"),
        score=comment_data.get("score", 0),
        depth=depth,
        path=(parent.path + [parent.id]) if parent else [],
        is_submitter=comment_data.get("is_submitter", False),
        distinguished=comment_data.get("distinguished"),
        stickied=comment_data.get("stickied", False),
        awards=comment_data.get("all_awardings", {}),
        edited=bool(comment_data.get("edited", False)),
        created_at=datetime.fromtimestamp(
            comment_data.get("created_utc", 0),
            tz=timezone.utc
        ),
        reddit_parent_id=reddit_parent_id
    )
    comments.append(comment)
    comment_map[comment.reddit_id] = comment
    
    # Process replies
    replies = comment_data.get("replies", {}).get("data", {}).get("children", [])
    if replies and isinstance(replies, list):
        for reply in replies:
            if reply["kind"] == "t1":  # t1 is comment type
                reply_comments = await process_comment_tree(
                    reply["data"],
                    post_id,
                    depth + 1,
                    comment,
                    config,
                    comment_map
                )
                comments.extend(reply_comments)
    
    return comments


async def collect_comments_for_post(
    post_id: str,
    session: AsyncSession,
    reddit_client: RedditClient,
    config: Optional[CommentCollectionConfig] = None
) -> List[Comment]:
    """
    Collect comments for a post with threading support
    
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
    stmt = select(RedditPost).where(RedditPost.reddit_id == post_id)
    result = await session.execute(stmt)
    post = result.scalar_one_or_none()
    
    if not post:
        raise ValueError(f"Post {post_id} not found in database")
    
    # Get existing comments to avoid duplicates
    stmt = select(Comment).where(Comment.post_id == post.id)
    result = await session.execute(stmt)
    existing_comments = {c.reddit_id: c for c in result.scalars().all()}
    
    # Get comments from Reddit
    comments_data = await reddit_client.get_post_comments(post_id)
    
    # Process all comments
    comment_map = {}  # Track comments by reddit_id for path building
    collected_comments = []
    
    for comment_data in comments_data:
        if comment_data["kind"] == "t1":  # t1 is comment type
            comments = await process_comment_tree(
                comment_data["data"],
                post.id,
                0,  # depth
                None,  # parent_comment
                config,
                comment_map
            )
            collected_comments.extend(comments)
    
    # Filter out existing comments
    new_comments = [c for c in collected_comments if c.reddit_id not in existing_comments]
    
    if new_comments:
        # Create new session for bulk insert to avoid conflicts
        async with session.begin():
            session.add_all(new_comments)
    
    return new_comments


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