from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpraw
from asyncpraw.exceptions import PRAWException
from asyncpraw.models import Comment, Submission, Subreddit

from ..core.config import settings
from ..models.comment import Comment as CommentModel


class RedditClient:
    def __init__(self):
        self.reddit = asyncpraw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT
        )
    
    async def get_post_comments(
        self,
        post_id: str,
        limit: int = 15,
        min_score: int = 5,
        sort: str = "top"
    ) -> List[Dict[str, Any]]:
        """
        Fetch comments for a post with filtering
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of top-level comments to fetch
            min_score: Minimum score threshold for comments
            sort: Sort method ("top", "best", "new", "controversial")
            
        Returns:
            List of comment data dictionaries
        """
        try:
            submission = await self.reddit.submission(id=post_id)
            
            # Replace MoreComments objects with actual comments
            await submission.comments.replace_more(limit=0)
            
            # Sort comments
            if sort == "top":
                submission.comments.sort = "top"
            elif sort == "new":
                submission.comments.sort = "new"
            elif sort == "controversial":
                submission.comments.sort = "controversial"
            else:
                submission.comments.sort = "confidence"  # "best" sort
            
            comments = []
            for comment in submission.comments[:limit]:
                if comment.score < min_score:
                    continue
                    
                comment_data = await self._parse_comment(comment)
                if comment_data:
                    comments.append(comment_data)
            
            return comments
            
        except PRAWException as e:
            # Log error and return empty list
            print(f"Error fetching comments for post {post_id}: {str(e)}")
            return []
    
    async def get_comment(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single comment by ID
        
        Args:
            comment_id: Reddit comment ID
            
        Returns:
            Comment data dictionary or None if not found
        """
        try:
            comment = await self.reddit.comment(id=comment_id)
            await comment.load()
            return await self._parse_comment(comment)
            
        except PRAWException as e:
            print(f"Error fetching comment {comment_id}: {str(e)}")
            return None
    
    async def _parse_comment(self, comment: Comment) -> Dict[str, Any]:
        """
        Parse a PRAW comment into a dictionary
        
        Args:
            comment: PRAW comment object
            
        Returns:
            Dictionary with comment data
        """
        # Get basic comment data
        data = {
            "id": comment.id,
            "content": comment.body,
            "author": str(comment.author) if comment.author else "[deleted]",
            "score": comment.score,
            "created_at": datetime.fromtimestamp(comment.created_utc),
            "edited": bool(comment.edited),
            "awards": len(getattr(comment, "all_awardings", [])),
            "replies": []
        }
        
        # Get replies if they exist
        if hasattr(comment, "replies") and comment.replies:
            for reply in comment.replies:
                if isinstance(reply, Comment):
                    reply_data = await self._parse_comment(reply)
                    if reply_data:
                        data["replies"].append(reply_data)
        
        return data 