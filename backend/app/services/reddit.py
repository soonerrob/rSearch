"""Service for interacting with Reddit API.

@doc https://www.reddit.com/dev/api/
@doc https://asyncpraw.readthedocs.io/en/stable/
"""

import asyncio
import logging
from datetime import datetime, timezone
from math import ceil
from typing import Dict, List, Optional, Set, Tuple, Union

import asyncpraw
import asyncprawcore
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.models import Comment, RedditPost, Subreddit
from app.schemas.subreddit import KeywordSuggestionResponse
from asyncpraw.models import Comment as PrawComment
from asyncpraw.models import Subreddit as AsyncPrawSubreddit
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
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
                read_only=True,
                ratelimit_seconds=60  # Reduce to 1 minute since we'll handle our own rate limiting
            )
            # Rate limit configuration
            self.request_delay = 1.0  # Base delay between requests
            self.batch_size = 10  # Number of items to process before delay
            self.max_retries = 3  # Maximum number of retries for rate-limited requests
            logger.info("Successfully initialized Reddit API client")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {str(e)}")
            raise
    
    async def _ensure_db_session(self):
        """Ensure we have a valid database session."""
        if not self.db or self.db.is_active:
            self.db = AsyncSessionLocal()
        return self.db

    async def get_subreddit_posts(
        self,
        subreddit_name: str,
        limit: int = 500,
        timeframe: str = "year",
        sort: str = "hot",
        min_score: int = 0,
        min_created_at: Optional[datetime] = None,
        progress_callback=None
    ) -> List[RedditPost]:
        """Get posts from a subreddit with enhanced filtering and sorting."""
        try:
            # Get subreddit with rate limiting
            subreddit = await self._rate_limited_request(
                self.reddit.subreddit(subreddit_name),
                context=f"get_subreddit {subreddit_name}"
            )
            
            # Get posts based on sort method
            if sort == "hot":
                submissions = subreddit.hot(limit=limit)
            elif sort == "top":
                submissions = subreddit.top(time_filter=timeframe, limit=limit)
            elif sort == "rising":
                submissions = subreddit.rising(limit=limit)
            elif sort == "controversial":
                submissions = subreddit.controversial(time_filter=timeframe, limit=limit)
            else:
                raise ValueError(f"Invalid sort method: {sort}")

            async def process_submission(submission):
                """Process a single submission with rate limiting."""
                # Load full submission data
                await submission.load()
                
                # Apply filters
                if submission.score < min_score:
                    return None
                    
                if min_created_at:
                    created_at = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                    if created_at <= min_created_at:
                        return None
                
                # Calculate engagement score
                engagement_score = self._calculate_engagement_score(submission)
                
                # Extract awards
                awards = self._extract_awards(submission)
                
                # Create post model
                post = RedditPost(
                    reddit_id=submission.id,
                    title=submission.title,
                    content=submission.selftext,
                    url=submission.url,
                    author=submission.author.name if submission.author else "[deleted]",
                    score=submission.score,
                    num_comments=submission.num_comments,
                    created_at=datetime.fromtimestamp(submission.created_utc).replace(tzinfo=timezone.utc),
                    collected_at=datetime.now(timezone.utc),
                    subreddit_name=subreddit_name,
                    is_self=submission.is_self,
                    upvote_ratio=submission.upvote_ratio,
                    is_original_content=getattr(submission, 'is_original_content', False),
                    distinguished=submission.distinguished,
                    stickied=submission.stickied,
                    awards=awards,
                    engagement_score=engagement_score,
                    collection_source=sort
                )
                
                return post

            # Process submissions in batches with rate limiting
            posts = await self._batch_process(
                submissions,
                process_submission,
                context=f"process_posts {subreddit_name}"
            )
            
            # Filter out None results (from filtered submissions)
            posts = [p for p in posts if p is not None]
            
            # Update progress if callback provided
            if progress_callback:
                await progress_callback(len(posts), limit)
            
            # Save posts to database in batches
            for i in range(0, len(posts), self.batch_size):
                batch = posts[i:i + self.batch_size]
                
                for post in batch:
                    # Check if post exists
                    result = await self.db.execute(
                        select(RedditPost).where(RedditPost.reddit_id == post.reddit_id)
                    )
                    existing_post = result.scalar_one_or_none()
                    
                    if not existing_post:
                        self.db.add(post)
                    else:
                        # Update existing post
                        post_dict = post.dict()
                        post_dict.pop('id', None)  # Remove ID if present
                        for key, value in post_dict.items():
                            setattr(existing_post, key, value)
                
                # Commit batch
                await self.db.commit()
                
                # Add delay between database batches
                await asyncio.sleep(self.request_delay)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting posts from r/{subreddit_name}: {str(e)}")
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
                    name=subreddit.display_name.lower(),  # Always use lowercase display_name
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
            search_results = self.reddit.subreddits.search(query, limit=limit * 2)  # Double the limit to account for filtered results
            
            # Collect all results first
            results = []
            async for subreddit in search_results:
                results.append(subreddit)
            
            # Then process them
            for subreddit in results:
                try:
                    model = await self._convert_to_model(subreddit)
                    
                    # Skip subreddits with 0 subscribers (likely private/banned/non-existent)
                    if not model.subscribers:
                        continue
                    
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
                    
                    # Break if we have enough results
                    if len(subreddits) >= limit:
                        break
                        
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

    def _calculate_engagement_score(self, submission) -> float:
        """Calculate an engagement score for a post based on various metrics."""
        base_score = submission.score + (submission.num_comments * 2)  # Comments weighted more heavily
        
        # Multiply by upvote ratio to favor quality
        weighted_score = base_score * submission.upvote_ratio
        
        # Boost score for distinguished/stickied content
        if submission.distinguished or submission.stickied:
            weighted_score *= 1.2
            
        # Boost for original content
        if submission.is_original_content:
            weighted_score *= 1.1
            
        # Normalize to 0-1 range (assuming most posts won't exceed 10000 total engagement)
        return min(1.0, weighted_score / 10000)

    def _extract_awards(self, submission) -> dict:
        """Extract awards information from a submission."""
        try:
            if hasattr(submission, "all_awardings"):
                return {
                    award["name"]: award["count"]
                    for award in submission.all_awardings
                }
            return {}
        except Exception as e:
            logger.error(f"Error extracting awards: {str(e)}")
            return {}

    async def collect_post_comments(
        self,
        post_id: str,
        max_depth: int = 5,
        min_score: Dict[int, int] = None,
        sort: str = "best"
    ) -> List[Comment]:
        """Collect comments for a specific post."""
        if min_score is None:
            min_score = {
                0: 1,  # Top-level comments
                1: 1,  # First-level replies
                2: 1,  # Second-level replies
                3: 1,  # Third-level replies
                'default': 1  # Default for deeper levels
            }

        try:
            # Ensure we have a valid session
            self.db = await self._ensure_db_session()

            # Get post from Reddit with rate limiting
            submission = await self._rate_limited_request(
                self.reddit.submission(id=post_id),
                context=f"get_submission {post_id}"
            )
            
            # Load full submission data with rate limiting
            await self._rate_limited_request(
                submission.load(),
                context=f"load_submission {post_id}"
            )
            
            # Replace MoreComments objects with a lower limit to avoid rate limiting
            await self._rate_limited_request(
                submission.comments.replace_more(limit=5),
                context=f"replace_more {post_id}"
            )
            
            # Sort comments
            if sort == "best":
                submission.comment_sort = "confidence"
            else:
                submission.comment_sort = sort
            
            # Get post from database
            result = await self.db.execute(
                select(RedditPost).where(RedditPost.reddit_id == post_id)
            )
            db_post = result.scalar_one_or_none()
            if not db_post:
                logger.error(f"Post {post_id} not found in database")
                return []
            
            # Process comments recursively
            comments = []
            comment_map = {}  # Map Reddit IDs to Comment objects
            
            # First, get all existing comments for this post
            result = await self.db.execute(
                select(Comment).where(Comment.post_id == db_post.id)
            )
            existing_comments = {c.reddit_id: c for c in result.scalars().all()}
            
            # Process comments in batches
            async def process_comment(comment_data):
                """Process a single comment with rate limiting."""
                try:
                    # Ensure comment is fully loaded
                    await self._rate_limited_request(
                        comment_data.load(),
                        context=f"load_comment {comment_data.id}"
                    )
                    
                    # Skip invalid comments
                    if (not hasattr(comment_data, 'author') or 
                        comment_data.author is None or 
                        not hasattr(comment_data, 'body') or 
                        not comment_data.body or  # Check for empty body
                        comment_data.body in ["[deleted]", "[removed]"]):
                        return None
                    
                    # Get created_utc timestamp safely
                    created_utc = getattr(comment_data, 'created_utc', None)
                    if created_utc is None:
                        return None  # Skip comments without creation time
                    
                    # Check score threshold
                    min_score_at_depth = min_score.get(comment_data.depth, min_score.get('default', 1))
                    if not hasattr(comment_data, 'score') or comment_data.score < min_score_at_depth:
                        return None
                    
                    # Calculate engagement score
                    engagement_score = self._calculate_comment_engagement(comment_data, comment_data.depth)
                    
                    # Extract awards
                    awards = self._extract_awards(comment_data)
                    
                    # Ensure all required fields have valid values
                    try:
                        comment = Comment(
                            reddit_id=comment_data.id,
                            post_id=db_post.id,  # Ensure post_id is set
                            content=comment_data.body.strip(),  # We already checked it's not empty above
                            author=str(comment_data.author) if hasattr(comment_data, 'author') and comment_data.author else '[deleted]',
                            score=max(0, getattr(comment_data, 'score', 0)),  # Ensure non-negative score
                            depth=max(0, getattr(comment_data, 'depth', 0)),  # Ensure non-negative depth
                            is_submitter=bool(getattr(comment_data, 'is_submitter', False)),
                            distinguished=getattr(comment_data, 'distinguished', None),
                            stickied=bool(getattr(comment_data, 'stickied', False)),
                            awards=awards or {},
                            edited=bool(getattr(comment_data, 'edited', False)),
                            engagement_score=float(engagement_score or 0.0),  # Ensure valid float
                            path=[],  # Will be updated after parent IDs are set
                            created_at=datetime.fromtimestamp(created_utc, tz=timezone.utc),
                            collected_at=datetime.now(timezone.utc)
                        )
                    except Exception as e:
                        logger.error(f"Error creating comment object for {comment_data.id}: {str(e)}")
                        return None

                    # Set parent ID if this is a reply
                    if hasattr(comment_data, 'parent_id'):
                        if comment_data.parent_id.startswith('t1_'):  # t1_ prefix indicates a comment
                            comment.reddit_parent_id = comment_data.parent_id[3:]  # Remove t1_ prefix
                        elif comment_data.parent_id.startswith('t3_'):  # t3_ prefix indicates a post
                            comment.reddit_parent_id = None  # This is a top-level comment

                    return comment
                except Exception as e:
                    logger.error(f"Error processing comment {comment_data.id}: {str(e)}")
                    return None

            # Process comments recursively with rate limiting
            async def process_comment_tree(comments_list, depth=0):
                """Process a list of comments recursively."""
                if depth > max_depth:
                    return []
                
                processed = []
                for comment_data in comments_list:
                    comment = await process_comment(comment_data)
                    if comment:
                        comment.post_id = db_post.id
                        if comment.reddit_id in existing_comments:
                            # Update existing comment
                            existing_comment = existing_comments[comment.reddit_id]
                            comment_dict = comment.dict(exclude={'id', 'parent', 'replies'})
                            for key, value in comment_dict.items():
                                setattr(existing_comment, key, value)
                            comment_map[comment.reddit_id] = existing_comment
                            processed.append(existing_comment)
                        else:
                            # Add new comment
                            processed.append(comment)
                            comment_map[comment.reddit_id] = comment
                    
                    # Process replies if they exist
                    if hasattr(comment_data, 'replies') and comment_data.replies:
                        child_comments = await process_comment_tree(comment_data.replies, depth + 1)
                        processed.extend(child_comments)
                
                return processed

            # Process all comments
            comments = await process_comment_tree(submission.comments)
            
            # Save new comments in batches
            new_comments = [c for c in comments if c.reddit_id not in existing_comments]
            if new_comments:
                for i in range(0, len(new_comments), self.batch_size):
                    batch = new_comments[i:i + self.batch_size]
                    self.db.add_all(batch)
                    await self.db.commit()
                    
                    # Refresh all new comments to get their IDs
                    for comment in batch:
                        await self.db.refresh(comment)
                    
                    # Add delay between batches
                    await asyncio.sleep(self.request_delay)
            
            # Update parent IDs in batches
            try:
                for i in range(0, len(comments), self.batch_size):
                    batch = comments[i:i + self.batch_size]
                    for comment in batch:
                        if hasattr(comment, 'reddit_parent_id') and comment.reddit_parent_id:
                            parent_comment = comment_map.get(comment.reddit_parent_id)
                            if parent_comment and parent_comment.id:  # Ensure parent has an ID
                                comment.parent_id = parent_comment.id
                
                # Commit parent ID updates
                await self.db.commit()
                
                # Add delay between batches
                await asyncio.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"Error updating parent IDs: {str(e)}")
                # Continue even if parent ID updates fail
            
            logger.info(f"Successfully collected {len(comments)} comments for post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error collecting comments for post {post_id}: {str(e)}")
            raise

    def _calculate_comment_engagement(self, comment: PrawComment, depth: int) -> float:
        """Calculate engagement score for a comment."""
        base_score = comment.score / (depth + 1)  # Score decreases with depth
        
        # Apply multipliers for special properties
        multipliers = 1.0
        if comment.is_submitter:
            multipliers *= 1.5  # OP's comments are more relevant
        if comment.distinguished:
            multipliers *= 1.3  # Distinguished comments (e.g., mod comments)
        if hasattr(comment, 'all_awardings') and comment.all_awardings:
            multipliers *= 1.2  # Awarded comments
            
        engagement = base_score * multipliers
        
        # Normalize to 0-1 range
        return min(1.0, engagement / 100)  # Assuming 100 is a good high score

    async def _get_comment_path(self, comment: PrawComment) -> str:
        """Get the full path of parent comment IDs as a comma-separated string."""
        path = []
        current = comment
        
        while hasattr(current, 'parent_id'):
            if current.parent_id.startswith('t1_'):
                parent_id = current.parent_id.split('_')[1]
                path.append(parent_id)
                try:
                    current = await self.reddit.comment(parent_id)
                except Exception:
                    break
            else:
                break
            
        return ','.join(reversed(path))

    async def _rate_limited_request(self, coroutine, context=""):
        """Execute a request with rate limit handling and exponential backoff.
        
        Args:
            coroutine: The async operation to execute
            context: Optional context string for logging
        """
        for attempt in range(self.max_retries):
            try:
                # Add base delay between requests
                await asyncio.sleep(self.request_delay)
                return await coroutine
            except asyncprawcore.exceptions.TooManyRequests as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Rate limit exceeded after {self.max_retries} retries for {context}")
                    raise
                
                # Calculate exponential backoff
                delay = self.request_delay * (2 ** attempt)
                logger.warning(f"Rate limit hit for {context}, waiting {delay:.1f} seconds (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Error during rate limited request ({context}): {str(e)}")
                raise

    async def _batch_process(self, items, process_func, batch_size=None, context=""):
        """Process items in batches with rate limiting.
        
        Args:
            items: Iterator of items to process
            process_func: Async function to process each item
            batch_size: Optional override for batch size
            context: Context string for logging
        """
        batch_size = batch_size or self.batch_size
        results = []
        current_batch = []
        
        async for item in items:
            current_batch.append(item)
            
            if len(current_batch) >= batch_size:
                # Process batch
                for batch_item in current_batch:
                    try:
                        result = await self._rate_limited_request(
                            process_func(batch_item),
                            context=f"{context} (batch item)"
                        )
                        if result is not None:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing batch item: {str(e)}")
                        # Continue with next item instead of failing entire batch
                        continue
                
                current_batch = []
                # Add delay between batches
                await asyncio.sleep(self.request_delay * 2)
        
        # Process remaining items
        if current_batch:
            for batch_item in current_batch:
                try:
                    result = await self._rate_limited_request(
                        process_func(batch_item),
                        context=f"{context} (final batch item)"
                    )
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error processing final batch item: {str(e)}")
                    continue
        
        return results 