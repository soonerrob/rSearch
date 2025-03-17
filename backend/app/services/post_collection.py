"""Service for collecting posts from Reddit."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.core.collection_config import POST_COLLECTION_CONFIG
from app.models.reddit_post import RedditPost
from app.services.reddit import RedditService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class PostCollectionService:
    """Service for collecting posts from Reddit."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the post collection service."""
        self.db = db
        self.reddit_service = RedditService(db)
    
    async def collect_posts(
        self,
        subreddit_name: str,
        limit: int = 500,
        timeframe: str = "year",
        progress_callback=None
    ) -> List[RedditPost]:
        """
        Collect posts from a subreddit using enhanced collection strategy.
        
        Args:
            subreddit_name: Name of the subreddit to collect from
            limit: Maximum number of posts to collect
            timeframe: Time period to collect posts from ("hour", "day", "week", "month", "year")
            progress_callback: Optional callback function to report progress
            
        Returns:
            List of collected posts
        """
        try:
            logger.info(f"Collecting posts from r/{subreddit_name}")
            
            # Calculate distribution limits
            distribution = self._calculate_distribution_limits(limit)
            collected_posts = []
            
            # Collect posts from different sorting methods based on distribution
            for sort_method, config in POST_COLLECTION_CONFIG['distribution'].items():
                if sort_method == 'top':
                    # Handle top posts with multiple timeframes
                    for tf in config['time_filters']:
                        posts = await self.reddit_service.get_subreddit_posts(
                            subreddit_name=subreddit_name,
                            limit=int(distribution[sort_method] * config['weight']),
                            timeframe=tf,
                            sort=sort_method,
                            min_score=config['min_score'],
                            progress_callback=progress_callback
                        )
                        collected_posts.extend(self._filter_posts(posts))
                else:
                    posts = await self.reddit_service.get_subreddit_posts(
                        subreddit_name=subreddit_name,
                        limit=distribution[sort_method],
                        timeframe=timeframe,
                        sort=sort_method,
                        min_score=config['min_score'],
                        progress_callback=progress_callback
                    )
                    collected_posts.extend(self._filter_posts(posts))
            
            return collected_posts[:limit]  # Ensure we don't exceed the requested limit
            
        except Exception as e:
            logger.error(f"Error collecting posts from r/{subreddit_name}: {str(e)}")
            raise
    
    def _calculate_distribution_limits(self, total_limit: int) -> Dict[str, int]:
        """Calculate post limits for each sorting method based on weights."""
        distribution = {}
        for method, config in POST_COLLECTION_CONFIG['distribution'].items():
            distribution[method] = int(total_limit * config['weight'])
        return distribution
    
    def _filter_posts(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Apply quality filters to posts."""
        filters = POST_COLLECTION_CONFIG['quality_filters']
        return [
            post for post in posts
            if (post.upvote_ratio >= filters['min_upvote_ratio'] and
                post.num_comments >= filters['min_comments'] and
                (not filters['exclude_removed'] or not post.removed))
        ]
    
    async def get_post(self, post_id: str) -> Optional[RedditPost]:
        """
        Get a post by its Reddit ID.
        
        Args:
            post_id: Reddit post ID
            
        Returns:
            RedditPost if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(RedditPost).where(RedditPost.reddit_id == post_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {str(e)}")
            return None
    
    async def close(self):
        """Close the Reddit service connection."""
        await self.reddit_service.close() 