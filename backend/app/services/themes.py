from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.models import Audience, RedditPost, Theme, ThemePost, ThemeQuestion
from app.services.reddit import RedditService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import and_, delete, select, text

logger = get_logger(__name__)

class ThemeService:
    def __init__(self, db=None):
        """Initialize the theme service."""
        self.db = db
        self.settings = get_settings()
        self.reddit_service = RedditService(self.db)

    async def collect_posts_for_audience(self, audience_id: int, is_initial_collection: bool = False) -> None:
        """Collect posts for an audience."""
        try:
            # Create a new async session for this background task
            async with AsyncSessionLocal() as session:
                # Query audience with eager loading of subreddits
                result = await session.execute(
                    select(Audience)
                    .options(joinedload(Audience.subreddits))
                    .where(Audience.id == audience_id)
                )
                
                # Use unique() to handle the joined load and get a single result
                audience = result.unique().scalar_one_or_none()
                if not audience:
                    logger.error(f"Audience {audience_id} not found")
                    return

                # Store subreddit names to avoid accessing relationship after session close
                subreddit_names = [s.subreddit_name for s in audience.subreddits]
                total_subreddits = len(subreddit_names)
                
                if total_subreddits == 0:
                    logger.warning(f"No subreddits found for audience {audience_id}")
                    return

                # Update collection status
                audience.is_collecting = True
                audience.collection_progress = 0
                await session.commit()

                try:
                    # Process each subreddit
                    for idx, subreddit_name in enumerate(subreddit_names, 1):
                        logger.info(f"Collecting posts for subreddit {subreddit_name}")
                        
                        # Get posts from Reddit
                        posts = await self.reddit_service.get_subreddit_posts(
                            subreddit_name,
                            limit=audience.posts_per_subreddit,
                            timeframe=audience.timeframe
                        )
                        
                        # Process each post
                        for post in posts:
                            # Check if post exists
                            existing_post = await session.execute(
                                select(RedditPost).where(RedditPost.reddit_id == post.reddit_id)
                            )
                            existing_post = existing_post.scalar_one_or_none()
                            
                            if existing_post:
                                # Update existing post with new data
                                existing_post.title = post.title
                                existing_post.content = post.content
                                existing_post.author = post.author
                                existing_post.score = post.score
                                existing_post.num_comments = post.num_comments
                                existing_post.collected_at = post.collected_at
                            else:
                                # Create new post
                                session.add(post)
                            
                            # Commit in batches to avoid memory issues
                            if idx % 100 == 0:
                                await session.commit()
                        
                        # Update progress
                        audience.collection_progress = (idx / total_subreddits) * 100
                        await session.commit()

                    # Mark collection as complete
                    audience.collection_progress = 100
                    audience.is_collecting = False
                    await session.commit()
                    
                    if is_initial_collection:
                        # Analyze themes after initial collection
                        await self.analyze_themes(audience_id)

                except Exception as e:
                    logger.error(f"Error collecting posts: {str(e)}")
                    # Ensure we mark collection as complete even if there's an error
                    async with AsyncSessionLocal() as cleanup_session:
                        result = await cleanup_session.execute(
                            select(Audience).where(Audience.id == audience_id)
                        )
                        audience = result.scalar_one_or_none()
                        if audience:
                            audience.is_collecting = False
                            audience.collection_progress = 0
                            await cleanup_session.commit()
                    raise

        except Exception as e:
            logger.error(f"Error in collect_posts_for_audience: {str(e)}")
            raise

    async def analyze_themes(self, audience_id: int) -> List[Theme]:
        """Analyze posts and generate themes for an audience."""
        if not self.db:
            raise ValueError("Database session not initialized")

        try:
            # Get recent posts for the audience
            posts = await self._get_recent_posts(audience_id)
            
            if not posts:
                raise ValueError("No posts found for this audience. Please ensure the audience has subreddits and posts have been collected.")
            
            # Define theme categories
            theme_categories = {
                "Hot Discussions": self._analyze_hot_discussions,
                "Top Content": self._analyze_top_content,
                "Advice Requests": self._analyze_advice_requests,
                "Solution Requests": self._analyze_solution_requests,
                "Pain & Anger": self._analyze_pain_and_anger,
                "Money Talk": self._analyze_money_talk,
                "Self-Promotion": self._analyze_self_promotion,
                "News": self._analyze_news,
                "Ideas": self._analyze_ideas,
                "Opportunities": self._analyze_opportunities
            }

            # Generate themes
            themes = []
            for category, analyzer in theme_categories.items():
                try:
                    relevant_posts = analyzer(posts)
                    if relevant_posts:
                        theme = Theme(
                            audience_id=audience_id,
                            category=category,
                            summary=self._generate_theme_summary(category, relevant_posts),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        self.db.add(theme)
                        await self.db.commit()
                        await self.db.refresh(theme)

                        # Create theme-post associations
                        theme_posts = []
                        for post in relevant_posts:
                            theme_post = ThemePost(
                                theme_id=theme.id,
                                post_id=post.id,
                                relevance_score=self._calculate_relevance_score(post, category)
                            )
                            theme_posts.append(theme_post)
                        
                        # Bulk insert theme posts
                        if theme_posts:
                            self.db.add_all(theme_posts)
                            await self.db.commit()
                        
                        themes.append(theme)
                except Exception as e:
                    logger.error(f"Error analyzing theme category {category}: {str(e)}")
                    await self.db.rollback()
                    continue

            if not themes:
                raise ValueError("No themes could be generated from the available posts")

            return themes

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in analyze_themes: {str(e)}")
            raise ValueError(f"Error analyzing themes: {str(e)}")

    async def _get_recent_posts(self, audience_id: int) -> List[RedditPost]:
        """Get recent posts for an audience."""
        if not self.db:
            raise ValueError("Database session not initialized")

        try:
            # Get audience first
            result = await self.db.execute(select(Audience).where(Audience.id == audience_id))
            audience = result.scalar_one_or_none()
            if not audience:
                raise ValueError(f"Audience with id {audience_id} not found")

            # Map timeframe to days
            timeframe_to_days = {
                "hour": 1/24,
                "day": 1,
                "week": 7,
                "month": 30,
                "year": 365
            }
            
            days = timeframe_to_days.get(audience.timeframe)
            if days is None:
                raise ValueError(f"Invalid timeframe: {audience.timeframe}")
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get posts from all subreddits in the audience using proper join
            query = text("""
                SELECT DISTINCT rp.* 
                FROM redditpost rp
                INNER JOIN audience_subreddits asu 
                    ON rp.subreddit_name = asu.subreddit_name 
                    AND asu.audience_id = :audience_id
                WHERE rp.collected_at >= :cutoff_date
            """)
            
            result = await self.db.execute(
                query,
                {
                    "audience_id": audience_id,
                    "cutoff_date": cutoff_date
                }
            )
            posts = result.all()
            
            if not posts:
                raise ValueError("No posts found for this audience within the specified timeframe")
            
            # Convert raw results to RedditPost objects
            post_objects = []
            for post in posts:
                post_dict = {
                    column: value
                    for column, value in zip(post._mapping.keys(), post._mapping.values())
                }
                post_objects.append(RedditPost(**post_dict))
            
            return post_objects

        except Exception as e:
            logger.error(f"Error getting recent posts: {str(e)}")
            raise ValueError(f"Error getting recent posts: {str(e)}")

    def _generate_theme_summary(self, category: str, posts: List[RedditPost]) -> str:
        """Generate a summary for a theme category using the relevant posts."""
        # TODO: Implement AI-powered summarization using OpenAI API
        return f"Summary of {len(posts)} posts in {category}"

    def _calculate_relevance_score(self, post: RedditPost, category: str) -> float:
        """Calculate how relevant a post is to a theme category."""
        # TODO: Implement more sophisticated scoring
        base_score = post.score + post.num_comments
        return min(1.0, base_score / 1000)  # Normalize to 0-1

    # Theme analysis methods
    def _analyze_hot_discussions(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify hot discussions based on recent engagement."""
        return sorted(
            [p for p in posts if p.score > 10 and p.num_comments > 5],
            key=lambda p: p.score + p.num_comments,
            reverse=True
        )[:10]

    def _analyze_top_content(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify top performing content."""
        return sorted(posts, key=lambda p: p.score, reverse=True)[:10]

    def _analyze_advice_requests(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify posts seeking advice."""
        keywords = ["advice", "help", "question", "how do", "how to", "need help", "beginner", "learning", "technique", "tips", "practice"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    def _analyze_solution_requests(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify posts seeking specific solutions."""
        keywords = ["looking for", "recommend", "suggestion", "alternative", "which", "vs", "or", "setup", "kit", "pedal", "cymbal", "snare"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    def _analyze_pain_and_anger(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify posts expressing frustration or problems."""
        keywords = ["frustrated", "angry", "annoyed", "hate", "problem", "issue", "broken", "noise", "loud", "neighbor", "complaint"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    def _analyze_money_talk(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify posts discussing financial aspects."""
        keywords = ["price", "cost", "money", "paid", "expensive", "cheap", "worth", "budget", "deal", "sale", "used", "new"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    def _analyze_self_promotion(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify self-promotional posts."""
        keywords = ["i made", "my project", "check out", "launching", "just released", "my band", "my cover", "my setup", "my kit", "nfd", "new drum day"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    def _analyze_news(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify news and announcements."""
        keywords = ["news", "announcement", "update", "release", "launched", "tour", "concert", "show", "performance", "competition"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    def _analyze_ideas(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify posts about ideas and creativity."""
        keywords = ["idea", "creative", "inspiration", "groove", "fill", "pattern", "style", "sound", "tone", "tuning"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    def _analyze_opportunities(self, posts: List[RedditPost]) -> List[RedditPost]:
        """Identify posts about opportunities."""
        keywords = ["opportunity", "job", "gig", "audition", "looking for drummer", "band", "project", "collaboration", "session", "studio"]
        return [p for p in posts if any(k in p.title.lower() or k in p.content.lower() for k in keywords)]

    async def refresh_themes(self, audience_id: int) -> None:
        """Task to refresh themes for an audience."""
        try:
            # First get all theme IDs for this audience
            result = await self.db.execute(
                select(Theme.id).where(Theme.audience_id == audience_id)
            )
            theme_ids = [theme_id for theme_id, in result.all()]
            
            if theme_ids:
                # Store existing theme questions and their categories
                existing_questions = []
                for theme_id in theme_ids:
                    result = await self.db.execute(select(Theme).where(Theme.id == theme_id))
                    theme = result.scalar_one_or_none()
                    if theme:
                        result = await self.db.execute(
                            select(ThemeQuestion).where(ThemeQuestion.theme_id == theme_id)
                        )
                        questions = result.scalars().all()
                        for question in questions:
                            existing_questions.append({
                                'question': question,
                                'category': theme.category
                            })
                
                # Delete theme posts
                await self.db.execute(
                    delete(ThemePost).where(ThemePost.theme_id.in_(theme_ids))
                )
                
                # Delete themes
                await self.db.execute(
                    delete(Theme).where(Theme.id.in_(theme_ids))
                )
                
                await self.db.commit()
            
            # Collect new posts
            await self.collect_posts_for_audience(audience_id)
            # Analyze themes
            new_themes = await self.analyze_themes(audience_id)
            
            # Update theme questions with new theme IDs
            if existing_questions:
                # Create a mapping of categories to new theme IDs
                category_to_theme = {theme.category: theme.id for theme in new_themes}
                
                # Update questions with new theme IDs
                for question_data in existing_questions:
                    question = question_data['question']
                    category = question_data['category']
                    if category in category_to_theme:
                        question.theme_id = category_to_theme[category]
                        self.db.add(question)
                
                await self.db.commit()
                
        except Exception as e:
            await self.db.rollback()
            # Log error but don't raise since this is a background task
            print(f"Error refreshing themes for audience {audience_id}: {str(e)}")

    async def _analyze_themes(self, posts: List[Dict], audience_id: int) -> List[Dict]:
        """Analyze themes from a list of posts."""
        # Group posts by theme
        theme_groups = {}
        for post in posts:
            theme = await self._extract_theme(post)
            if theme not in theme_groups:
                theme_groups[theme] = []
            theme_groups[theme].append(post)
        
        # Convert theme groups to list of theme dictionaries
        themes = []
        for theme_name, theme_posts in theme_groups.items():
            theme = await self._create_theme_dict(theme_name, theme_posts, audience_id)
            themes.append(theme)
        
        return themes

    async def _extract_theme(self, post: Dict) -> str:
        """Extract theme from a post using title and content."""
        title = post.get('title', '').lower()
        content = post.get('selftext', '').lower()
        
        # Extract theme based on keywords and patterns
        theme = await self._identify_theme_from_text(title + ' ' + content)
        return theme

    async def _identify_theme_from_text(self, text: str) -> str:
        """Identify theme from text using keyword analysis."""
        # Add your theme identification logic here
        # This could involve NLP, keyword matching, or other analysis methods
        return "general"  # Placeholder

    async def _create_theme_dict(self, theme_name: str, posts: List[Dict], audience_id: int) -> Dict:
        """Create a theme dictionary with metadata."""
        total_score = sum(post.get('score', 0) for post in posts)
        total_comments = sum(post.get('num_comments', 0) for post in posts)
        
        return {
            'name': theme_name,
            'post_count': len(posts),
            'total_score': total_score,
            'total_comments': total_comments,
            'audience_id': audience_id,
            'posts': posts
        }

    async def _calculate_theme_metrics(self, theme: Dict) -> Dict:
        """Calculate metrics for a theme."""
        posts = theme.get('posts', [])
        if not posts:
            return {}
        
        # Calculate engagement metrics
        avg_score = sum(post.get('score', 0) for post in posts) / len(posts)
        avg_comments = sum(post.get('num_comments', 0) for post in posts) / len(posts)
        
        # Calculate temporal metrics
        timestamps = [post.get('created_utc', 0) for post in posts]
        if timestamps:
            newest_post = max(timestamps)
            oldest_post = min(timestamps)
            time_span = newest_post - oldest_post if newest_post > oldest_post else 0
            posts_per_day = len(posts) / (time_span / 86400) if time_span > 0 else 0
        else:
            posts_per_day = 0
        
        return {
            'avg_score': avg_score,
            'avg_comments': avg_comments,
            'posts_per_day': posts_per_day
        }

    async def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text."""
        # Add your sentiment analysis logic here
        # This could involve NLP libraries or API calls
        return {
            'sentiment': 'neutral',
            'confidence': 0.5
        }

    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Add your keyword extraction logic here
        # This could involve NLP libraries or API calls
        return []

    async def _categorize_theme(self, theme: Dict) -> str:
        """Categorize a theme based on its content."""
        # Add your theme categorization logic here
        # This could involve machine learning models or rule-based systems
        return "general"

    async def _calculate_theme_importance(self, theme: Dict) -> float:
        """Calculate importance score for a theme."""
        metrics = await self._calculate_theme_metrics(theme)
        
        # Weight different factors to determine importance
        engagement_weight = 0.4
        recency_weight = 0.3
        volume_weight = 0.3
        
        engagement_score = (metrics.get('avg_score', 0) + metrics.get('avg_comments', 0)) / 2
        recency_score = metrics.get('posts_per_day', 0)
        volume_score = theme.get('post_count', 0)
        
        # Normalize scores (you may want to adjust these normalizations based on your data)
        engagement_score = min(engagement_score / 100, 1)
        recency_score = min(recency_score / 10, 1)
        volume_score = min(volume_score / 50, 1)
        
        importance = (
            engagement_score * engagement_weight +
            recency_score * recency_weight +
            volume_score * volume_weight
        )
        
        return importance

    async def _analyze_theme_trends(self, theme: Dict) -> Dict:
        """Analyze trends within a theme over time."""
        posts = theme.get('posts', [])
        if not posts:
            return {}
        
        # Sort posts by timestamp
        sorted_posts = sorted(posts, key=lambda x: x.get('created_utc', 0))
        
        # Calculate metrics over time
        time_periods = []
        current_period = []
        period_start = sorted_posts[0].get('created_utc', 0)
        period_length = 86400  # 1 day in seconds
        
        for post in sorted_posts:
            timestamp = post.get('created_utc', 0)
            if timestamp - period_start > period_length:
                if current_period:
                    period_metrics = {
                        'start_time': period_start,
                        'post_count': len(current_period),
                        'avg_score': sum(p.get('score', 0) for p in current_period) / len(current_period),
                        'avg_comments': sum(p.get('num_comments', 0) for p in current_period) / len(current_period)
                    }
                    time_periods.append(period_metrics)
                period_start = timestamp
                current_period = []
            current_period.append(post)
        
        # Add final period
        if current_period:
            period_metrics = {
                'start_time': period_start,
                'post_count': len(current_period),
                'avg_score': sum(p.get('score', 0) for p in current_period) / len(current_period),
                'avg_comments': sum(p.get('num_comments', 0) for p in current_period) / len(current_period)
            }
            time_periods.append(period_metrics)
        
        return {
            'time_periods': time_periods,
            'total_periods': len(time_periods)
        } 