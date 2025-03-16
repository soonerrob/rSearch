"""Service for interacting with Reddit API.

@doc https://www.reddit.com/dev/api/
@doc https://asyncpraw.readthedocs.io/en/stable/
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

import asyncpraw
from app.core.config import get_settings
from app.models import Subreddit
from app.models.reddit_post import RedditPost
from app.schemas.subreddit import KeywordSuggestionResponse
from asyncpraw.models import Subreddit as AsyncPrawSubreddit
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

# Configure logging with more detail
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Common topic mappings for popular categories
TOPIC_MAPPINGS = {
    'dog': [
        ('training', ['dog training', 'puppy training', 'obedience', 'behavior', 'commands', 'leash training']),
        ('breeds', ['dog breeds', 'breed specific', 'purebred', 'mixed breed', 'breed recommendations']),
        ('health', ['dog health', 'veterinary', 'nutrition', 'diet', 'medical', 'vaccines', 'allergies']),
        ('care', ['dog care', 'grooming', 'exercise', 'pet care', 'bathing', 'nail trimming']),
        ('behavior', ['dog behavior', 'psychology', 'socialization', 'anxiety', 'aggression', 'barking']),
        ('activities', ['dog parks', 'agility', 'dog sports', 'walking', 'hiking', 'swimming']),
        ('products', ['dog food', 'toys', 'supplies', 'accessories', 'beds', 'crates', 'collars']),
        ('adoption', ['rescue', 'shelter', 'adoption', 'fostering', 'rehoming', 'puppies']),
        ('services', ['dog walking', 'boarding', 'daycare', 'pet sitting', 'training classes', 'grooming services']),
    ],
    'food': [
        ('cuisine', ['recipes', 'cooking', 'baking', 'meal prep', 'restaurants', 'takeout']),
        ('dietary', ['vegetarian', 'vegan', 'gluten-free', 'keto', 'paleo', 'low-carb']),
        ('meal types', ['breakfast', 'lunch', 'dinner', 'snacks', 'desserts', 'appetizers']),
        ('techniques', ['grilling', 'baking', 'slow cooking', 'air fryer', 'instant pot', 'smoking']),
        ('ingredients', ['meat', 'vegetables', 'fruits', 'spices', 'herbs', 'seafood']),
    ],
    'gaming': [
        ('genres', ['rpg', 'fps', 'mmorpg', 'strategy', 'simulation', 'sports games', 'racing']),
        ('platforms', ['pc gaming', 'playstation', 'xbox', 'nintendo switch', 'mobile gaming']),
        ('esports', ['competitive', 'tournaments', 'streaming', 'professional gaming']),
        ('communities', ['gaming discussion', 'game recommendations', 'gaming news', 'reviews']),
        ('technical', ['gaming setup', 'pc building', 'graphics cards', 'performance']),
    ],
    'tech': [
        ('hardware', ['computers', 'smartphones', 'tablets', 'accessories', 'peripherals']),
        ('software', ['applications', 'operating systems', 'programming', 'development']),
        ('services', ['cloud computing', 'streaming', 'web services', 'hosting']),
        ('news', ['tech news', 'product launches', 'industry trends', 'reviews']),
        ('support', ['troubleshooting', 'technical support', 'how-to guides', 'tips']),
    ],
}

class RedditService:
    """Service for interacting with Reddit API"""
    
    def __init__(self, db: AsyncSession):
        """Initialize the Reddit service with AsyncPRAW client."""
        self.db = db
        try:
            settings = get_settings()
            self.reddit = asyncpraw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
                read_only=True,  # Add read_only mode
                ratelimit_seconds=600  # Increase rate limit timeout to 10 minutes
            )
            logger.info("Successfully initialized Reddit API client")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {str(e)}")
            raise
    
    async def get_subreddit_posts(self, subreddit_name: str, limit: int = 500, timeframe: str = "year", progress_callback=None) -> List[RedditPost]:
        """Get posts from a subreddit."""
        try:
            logger.info(f"Getting posts from {subreddit_name}")
            subreddit = await self.reddit.subreddit(subreddit_name)
            posts = []
            posts_iterator = subreddit.top(time_filter=timeframe, limit=limit)
            
            # Process posts in batches
            async for submission in posts_iterator:
                try:
                    post = RedditPost(
                        reddit_id=submission.id,
                        title=submission.title,
                        content=submission.selftext,
                        author=str(submission.author) if submission.author else "[deleted]",
                        score=submission.score,
                        num_comments=submission.num_comments,
                        created_at=datetime.fromtimestamp(submission.created_utc),
                        subreddit_name=subreddit_name,
                        collected_at=datetime.utcnow()
                    )
                    posts.append(post)
                    
                    if progress_callback:
                        await progress_callback(len(posts), limit)
                        
                except Exception as e:
                    logger.error(f"Error processing post {submission.id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully collected {len(posts)} posts from {subreddit_name}")
            return posts
            
        except Exception as e:
            logger.error(f"Error getting posts from {subreddit_name}: {str(e)}")
            raise
    
    async def sync_subreddit_to_db(self, subreddit: AsyncPrawSubreddit, session: AsyncSession) -> Subreddit:
        """Sync subreddit information to the database."""
        try:
            # Check if subreddit exists in database
            result = await session.execute(
                select(Subreddit).where(Subreddit.name == subreddit.display_name.lower())
            )
            db_subreddit = result.scalar_one_or_none()

            # Get active users count if available, otherwise use a placeholder
            active_users = getattr(subreddit, 'active_user_count', None)
            if active_users is None:
                # If active_user_count is not available, estimate based on subscribers
                active_users = int(subreddit.subscribers * 0.01)  # Assume 1% of subscribers are active

            if db_subreddit:
                # Update existing subreddit
                db_subreddit.display_name = subreddit.display_name
                db_subreddit.description = subreddit.description
                db_subreddit.subscribers = subreddit.subscribers
                db_subreddit.active_users = active_users
                db_subreddit.updated_at = datetime.utcnow()
            else:
                # Create new subreddit
                db_subreddit = Subreddit(
                    name=subreddit.display_name.lower(),
                    display_name=subreddit.display_name,
                    description=subreddit.description,
                    subscribers=subreddit.subscribers,
                    active_users=active_users
                )
                session.add(db_subreddit)

            await session.commit()
            await session.refresh(db_subreddit)
            return db_subreddit

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error syncing subreddit to database: {str(e)}")
    
    async def get_trending_subreddits(self, limit: int = 25) -> List[Subreddit]:
        """Get trending subreddits."""
        try:
            subreddits = []
            async for subreddit in self.reddit.subreddits.popular(limit=limit):
                await subreddit.load()
                subreddits.append(subreddit)
            return subreddits
        except Exception as e:
            logger.error(f"Error getting trending subreddits: {str(e)}")
            raise
    
    async def search_subreddits(
        self, 
        query: str, 
        limit: int = 10,
        min_subscribers: Optional[int] = None,
        max_subscribers: Optional[int] = None,
        min_active_users: Optional[int] = None,
        max_active_users: Optional[int] = None
    ) -> List[Subreddit]:
        """Search for subreddits matching the query."""
        try:
            logger.debug(f"Searching subreddits with query: {query}, limit: {limit}, filters: min_subscribers={min_subscribers}, max_subscribers={max_subscribers}, min_active_users={min_active_users}, max_active_users={max_active_users}")
            subreddits = []
            search_results = self.reddit.subreddits.search(query, limit=limit)
            
            # Collect all results first
            results = []
            async for subreddit in search_results:
                results.append(subreddit)
            
            # Then process them
            for subreddit in results:
                try:
                    model = await self._convert_to_model(subreddit)
                    
                    # Apply filters
                    if min_subscribers is not None and model.subscribers < min_subscribers:
                        continue
                    if max_subscribers is not None and model.subscribers > max_subscribers:
                        continue
                    if min_active_users is not None and model.active_users < min_active_users:
                        continue
                    if max_active_users is not None and model.active_users > max_active_users:
                        continue
                    
                    subreddits.append(model)
                except Exception as e:
                    logger.error(f"Error converting subreddit {subreddit.display_name}: {str(e)}")
                    continue
            return subreddits
        except Exception as e:
            logger.error(f"Error searching subreddits: {str(e)}")
            raise
    
    async def get_subreddit_info(self, subreddit_name: str) -> Subreddit:
        """Get information about a subreddit."""
        try:
            logger.debug(f"Fetching info for subreddit: {subreddit_name}")
            subreddit = await self.reddit.subreddit(subreddit_name)
            await subreddit.load()

            # Calculate posts and comments per day
            posts_per_day = subreddit.subscribers * 0.01  # Placeholder calculation
            comments_per_day = posts_per_day * 10  # Placeholder calculation

            # Create response
            response = Subreddit(
                name=subreddit.display_name.lower(),
                display_name=subreddit.display_name,
                description=subreddit.description,
                subscribers=subreddit.subscribers,
                active_users=subreddit.active_user_count,
                posts_per_day=posts_per_day,
                comments_per_day=comments_per_day,
                growth_rate=0.0,  # Placeholder
                relevance_score=0.0,  # Placeholder
                created_at=datetime.fromtimestamp(subreddit.created_utc, tz=timezone.utc),
                updated_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )

            logger.info(f"Successfully fetched info for subreddit: {subreddit_name}")
            return response
        except Exception as e:
            logger.error(f"Error getting subreddit info: {str(e)}")
            raise

    async def _convert_to_model(self, subreddit: AsyncPrawSubreddit) -> Subreddit:
        """Convert a AsyncPRAW subreddit object to our Subreddit model."""
        try:
            logger.debug(f"Converting subreddit {subreddit.display_name} to model")
            
            # Fetch full subreddit info to get active users
            try:
                full_subreddit = await self.reddit.subreddit(subreddit.display_name)
                await full_subreddit.load()
                active_users = full_subreddit.active_user_count
                logger.debug(f"Active users for {subreddit.display_name}: {active_users}")
                
                # Calculate posts per day from recent posts
                try:
                    recent_posts = []
                    async for post in full_subreddit.new(limit=100):  # Get 100 most recent posts
                        recent_posts.append(post)
                    
                    if recent_posts:
                        newest_post_time = recent_posts[0].created_utc
                        oldest_post_time = recent_posts[-1].created_utc
                        time_span = newest_post_time - oldest_post_time
                        days = time_span / (24 * 3600)  # Convert seconds to days
                        posts_per_day = len(recent_posts) / max(days, 1)  # Avoid division by zero
                        logger.debug(f"Calculated {posts_per_day:.1f} posts/day for {subreddit.display_name}")
                    else:
                        posts_per_day = 0
                except Exception as e:
                    logger.error(f"Error calculating posts per day for {subreddit.display_name}: {str(e)}")
                    posts_per_day = None
            except Exception as e:
                logger.error(f"Error fetching active users for {subreddit.display_name}: {str(e)}")
                active_users = None
                posts_per_day = None
            
            # Convert created_utc to datetime
            created_at = datetime.fromtimestamp(subreddit.created_utc) if hasattr(subreddit, 'created_utc') else datetime.utcnow()
            
            return Subreddit(
                name=subreddit.display_name.lower(),
                display_name=subreddit.display_name,
                description=getattr(subreddit, 'description', None),
                subscribers=getattr(subreddit, 'subscribers', 0),
                active_users=active_users,
                posts_per_day=posts_per_day,
                comments_per_day=None,
                growth_rate=None,
                relevance_score=0.0,  # Initialize with default score
                created_at=created_at,
                updated_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error converting subreddit {subreddit.display_name} to model: {str(e)}")
            raise

    async def get_keyword_suggestions(self, query: str, limit: int = 10) -> List[KeywordSuggestionResponse]:
        """Get keyword suggestions based on the query."""
        try:
            # Get base suggestions from topic mappings
            suggestions = []
            for topic, categories in TOPIC_MAPPINGS.items():
                if query.lower() in topic.lower():
                    for category, keywords in categories:
                        suggestions.extend(keywords)
            
            # Add subreddit search results
            try:
                search_results = await self.reddit.subreddits.search(query, limit=limit)
                async for subreddit in search_results:
                    suggestions.append(subreddit.display_name)
            except Exception as e:
                logger.error(f"Error getting subreddit suggestions: {str(e)}")
            
            # Filter and sort suggestions
            filtered = [s for s in suggestions if query.lower() in s.lower()]
            sorted_suggestions = sorted(filtered, key=lambda x: self._calculate_similarity(query, x), reverse=True)
            
            # Convert to KeywordSuggestionResponse objects
            return [
                KeywordSuggestionResponse(
                    keyword=s,
                    score=self._calculate_similarity(query, s),
                    subreddit_count=None  # We don't have this information yet
                )
                for s in sorted_suggestions[:limit]
            ]
        except Exception as e:
            logger.error(f"Error in get_keyword_suggestions: {str(e)}")
            return []

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity score between 0 and 1."""
        # Simple implementation using common substring
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # Count common characters
        common = set(str1) & set(str2)
        if not common:
            return 0.0
        
        # Calculate Jaccard similarity
        return len(common) / len(set(str1) | set(str2))

    async def close(self):
        """Close the Reddit client and clean up resources."""
        if hasattr(self, 'reddit') and self.reddit:
            await self.reddit.close()

    async def get_subreddit_suggestions(self, query: str) -> List[str]:
        """Get subreddit suggestions based on a search query."""
        try:
            logger.info(f"Getting subreddit suggestions for query: {query}")
            subreddits = self.reddit.subreddits.search(query, limit=5)
            suggestions = []
            async for subreddit in subreddits:
                suggestions.append(subreddit.display_name)
            return suggestions
        except Exception as e:
            logger.error(f"Error getting subreddit suggestions: {str(e)}")
            return [] 