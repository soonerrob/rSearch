import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.models.audience import Audience, AudienceSubreddit
from app.models.comment import Comment
from app.models.post_analysis import PostAnalysis
from app.models.reddit_post import RedditPost
from app.models.theme import Theme, ThemePost
from app.models.theme_question import ThemeQuestion
from app.services.openai_service import analyze_theme_content
from app.services.reddit import RedditService
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import and_, delete, select, text

logger = logging.getLogger(__name__)

class ThemeService:
    def __init__(self, db=None):
        """Initialize the theme service."""
        self.db = db
        self.settings = get_settings()
        self.reddit_service = RedditService(db=db)
        
        # Define theme categories with their criteria and keywords
        self.theme_categories = {
            # Metric-based themes
            "Hot Discussions": {
                "type": "metric",
                "criteria": lambda p: p.score > 10 and p.num_comments > 5,
                "sort_key": lambda p: (p.score * 0.6 + p.num_comments * 0.4),
                "description": "Active discussions with high engagement"
            },
            "Top Content": {
                "type": "metric",
                "criteria": lambda p: True,  # All posts eligible
                "sort_key": lambda p: p.score,
                "description": "Highest-rated content"
            },
            # Keyword-based themes
            "Advice Requests": {
                "type": "keyword",
                "keywords": ["advice", "help", "question", "how do", "how to", "need help", "beginner", "learning", "technique", "tips", "practice"],
                "description": "Posts seeking guidance and assistance"
            },
            "Solution Requests": {
                "type": "keyword",
                "keywords": ["looking for", "recommend", "suggestion", "alternative", "which", "vs", "or", "setup", "kit", "pedal", "cymbal", "snare"],
                "description": "Posts seeking specific solutions or recommendations"
            },
            "Pain & Anger": {
                "type": "keyword",
                "keywords": ["frustrated", "angry", "annoyed", "hate", "problem", "issue", "broken", "noise", "loud", "neighbor", "complaint"],
                "description": "Posts expressing frustration or problems"
            },
            "Money Talk": {
                "type": "keyword",
                "keywords": ["price", "cost", "money", "paid", "expensive", "cheap", "worth", "budget", "deal", "sale", "used", "new"],
                "description": "Discussions about costs and value"
            },
            "Self-Promotion": {
                "type": "keyword",
                "keywords": ["i made", "my project", "check out", "launching", "just released", "my band", "my cover", "my setup", "my kit", "nfd", "new drum day"],
                "description": "Users sharing their own content"
            },
            "News": {
                "type": "keyword",
                "keywords": ["news", "announcement", "update", "release", "launched", "tour", "concert", "show", "performance", "competition"],
                "description": "News and announcements"
            },
            "Ideas": {
                "type": "keyword",
                "keywords": ["idea", "creative", "inspiration", "groove", "fill", "pattern", "style", "sound", "tone", "tuning"],
                "description": "Creative and inspirational content"
            },
            "Opportunities": {
                "type": "keyword",
                "keywords": ["opportunity", "job", "gig", "audition", "looking for drummer", "band", "project", "collaboration", "session", "studio"],
                "description": "Job and collaboration opportunities"
            }
        }

    async def _ensure_db_session(self):
        """Ensure we have a valid database session."""
        if not self.db or not self.db.is_active:
            self.db = AsyncSessionLocal()
        return self.db

    async def collect_posts_for_audience(self, audience_id: int, is_initial_collection: bool = False) -> None:
        """Collect posts and comments for an audience."""
        try:
            # Ensure we have a valid session
            self.db = await self._ensure_db_session()
            
            # Get audience
            result = await self.db.execute(
                select(Audience).where(Audience.id == audience_id)
            )
            audience = result.scalar_one_or_none()
            if not audience:
                raise ValueError(f"Audience with id {audience_id} not found")

            # Check if already collecting
            if audience.is_collecting:
                logger.warning(f"Audience {audience_id} is already being collected, skipping")
                return

            # Mark collection as started
            audience.is_collecting = True
            audience.collection_progress = 0
            await self.db.commit()

            try:
                # Get subreddits for this audience
                result = await self.db.execute(
                    select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience_id)
                )
                subreddits = result.scalars().all()

                total_subreddits = len(subreddits)
                if total_subreddits == 0:
                    raise ValueError("No subreddits found for this audience")

                for i, subreddit in enumerate(subreddits, 1):
                    # Update progress (50% for posts, 50% for comments)
                    audience.collection_progress = int((i / total_subreddits) * 50)
                    await self.db.commit()

                    # Determine collection parameters based on whether this is initial collection or update
                    if is_initial_collection:
                        # For initial collection, get all posts according to timeframe
                        posts = await self.reddit_service.get_subreddit_posts(
                            subreddit.subreddit_name,
                            limit=audience.posts_per_subreddit,
                            timeframe=audience.timeframe
                        )
                    else:
                        # For hourly updates, only get posts newer than last collection
                        if audience.last_collection_time:
                            posts = await self.reddit_service.get_subreddit_posts(
                                subreddit.subreddit_name,
                                limit=audience.posts_per_subreddit,
                                timeframe="hour",  # Always use "hour" for updates
                                min_created_at=audience.last_collection_time
                            )
                        else:
                            # If no last_collection_time, treat as initial collection
                            posts = await self.reddit_service.get_subreddit_posts(
                                subreddit.subreddit_name,
                                limit=audience.posts_per_subreddit,
                                timeframe=audience.timeframe
                            )

                    # Process each post and collect comments
                    total_posts = len(posts)
                    for post_idx, post in enumerate(posts, 1):
                        try:
                            # Check if post exists
                            result = await self.db.execute(
                                select(RedditPost).where(RedditPost.reddit_id == post.reddit_id)
                            )
                            existing_post = result.scalar_one_or_none()
                            
                            if not existing_post:
                                # Add new post
                                self.db.add(post)
                                await self.db.commit()
                                await self.db.refresh(post)
                                post_to_use = post
                            else:
                                # Update existing post
                                post_dict = post.dict()
                                post_dict.pop('id', None)  # Remove ID if present
                                for key, value in post_dict.items():
                                    setattr(existing_post, key, value)
                                await self.db.commit()
                                post_to_use = existing_post
                                
                            # Collect comments for all posts
                            try:
                                comments = await self.reddit_service.collect_post_comments(
                                    post_to_use.reddit_id,
                                    max_depth=5,
                                    min_score={
                                        0: 1,  # Top-level comments
                                        1: 1,  # First-level replies
                                        2: 1,  # Second-level replies
                                        'default': 1  # All deeper levels
                                    }
                                )
                                
                                # Set post_id for all comments
                                for comment in comments:
                                    comment.post_id = post_to_use.id
                                
                                # Bulk save comments
                                if comments:
                                    self.db.add_all(comments)
                                    await self.db.commit()
                            except Exception as e:
                                logger.error(f"Error collecting comments for post {post_to_use.reddit_id}: {str(e)}")
                                # Continue with next post even if comment collection fails
                                continue
                            
                            # Analyze the post
                            await self._analyze_post(post_to_use)
                            
                            # Update progress for this subreddit's posts
                            post_progress = int((post_idx / total_posts) * (50 / total_subreddits))
                            audience.collection_progress = 50 + post_progress
                            await self.db.commit()
                        except Exception as e:
                            logger.error(f"Error processing post: {str(e)}")
                            continue  # Continue with next post even if this one fails

                # Update last_collection_time and mark collection as complete
                audience.last_collection_time = datetime.now(timezone.utc)
                audience.collection_progress = 100
                audience.is_collecting = False
                await self.db.commit()
                
                if is_initial_collection:
                    # Generate themes after initial collection
                    await self.analyze_themes(audience_id)

            except Exception as e:
                # Inner try-catch to ensure we reset collection state
                logger.error(f"Error during collection: {str(e)}")
                audience.is_collecting = False
                audience.collection_progress = 0
                await self.db.commit()
                raise

        except Exception as e:
            logger.error(f"Error collecting posts: {str(e)}")
            # Ensure we mark collection as complete even if there's an error
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(Audience).where(Audience.id == audience_id)
                    )
                    audience = result.scalar_one_or_none()
                    if audience:
                        audience.is_collecting = False
                        audience.collection_progress = 0
                        await db.commit()
            except Exception as inner_e:
                logger.error(f"Error resetting collection state: {str(inner_e)}")
            raise

    async def _analyze_post(self, post: RedditPost) -> None:
        """Analyze a post and store its analysis results."""
        # Check if already analyzed
        result = await self.db.execute(
            select(PostAnalysis).where(PostAnalysis.post_id == post.id)
        )
        if result.scalar_one_or_none():
            return

        # Find matching themes
        matching_themes = []
        text_content = (post.title + " " + post.content).lower()
        
        # Check each theme category
        for category, config in self.theme_categories.items():
            if config["type"] == "metric":
                # For metric-based themes
                if config["criteria"](post):
                    matching_themes.append({
                        "category": category,
                        "score": config["sort_key"](post),
                        "type": "metric"
                    })
            else:
                # For keyword-based themes
                matched_keywords = [k for k in config["keywords"] if k in text_content]
                if matched_keywords:
                    matching_themes.append({
                        "category": category,
                        "score": len(matched_keywords) / len(config["keywords"]),
                        "type": "keyword",
                        "matched_keywords": matched_keywords
                    })

        # Extract all matched keywords
        all_keywords = []
        for theme in matching_themes:
            if theme["type"] == "keyword" and "matched_keywords" in theme:
                all_keywords.extend(theme["matched_keywords"])
        all_keywords = list(set(all_keywords))  # Remove duplicates

        # Calculate theme scores
        theme_scores = {}
        for theme in matching_themes:
            base_score = theme["score"]
            
            # Apply theme-specific adjustments
            if theme["category"] == "Hot Discussions":
                # Boost score for posts with high comment/score ratio
                comment_ratio = post.num_comments / max(post.score, 1)
                base_score *= (1 + min(comment_ratio, 1))
            elif theme["category"] == "Advice Requests":
                # Boost score for longer, detailed posts
                content_length = len(text_content)
                base_score *= (1 + min(content_length / 1000, 0.5))
            
            theme_scores[theme["category"]] = min(base_score, 1.0)  # Normalize to 0-1

        # Store analysis
        analysis = PostAnalysis(post_id=post.id)
        analysis.set_matching_themes([t["category"] for t in matching_themes])
        analysis.set_theme_scores(theme_scores)
        analysis.set_keywords(all_keywords)
        analysis.analyzed_at = datetime.now(timezone.utc)
        
        self.db.add(analysis)
        await self.db.commit()

    async def analyze_themes(self, audience_id: int) -> List[Theme]:
        """Analyze themes from posts and their comments."""
        try:
            # Get recent posts for the audience
            posts = await self._get_recent_posts(audience_id)
            if not posts:
                raise ValueError("No posts found for analysis")

            # Get existing post analyses
            post_ids = [post.id for post in posts]
            post_analyses = await self._get_post_analyses(post_ids)
            
            # Get comments for all posts
            comments = await self._get_comments_for_posts(post_ids)
            comments_by_post = defaultdict(list)
            for comment in comments:
                comments_by_post[comment.post_id].append(comment)

            # Group posts by themes
            theme_groups = defaultdict(list)
            theme_scores = defaultdict(float)
            
            # Process each post
            for post in posts:
                post_comments = comments_by_post.get(post.id, [])
                
                # Calculate engagement metrics
                engagement_score = post.score + sum(c.score for c in post_comments)
                comment_count = len(post_comments)
                
                # Process metric-based themes
                for theme_name, theme_config in self.theme_categories.items():
                    if theme_config["type"] == "metric":
                        if theme_config["criteria"](post):
                            theme_groups[theme_name].append(post)
                            theme_scores[theme_name] += theme_config["sort_key"](post)
                    
                    elif theme_config["type"] == "keyword":
                        # Check post title and content for keywords
                        content = f"{post.title} {post.content}".lower()
                        keyword_matches = sum(1 for keyword in theme_config["keywords"] if keyword.lower() in content)
                        
                        # Check comments for keywords
                        for comment in post_comments:
                            if comment.content:
                                comment_matches = sum(1 for keyword in theme_config["keywords"] if keyword.lower() in comment.content.lower())
                                keyword_matches += comment_matches * 0.5  # Comments count for half
                        
                        if keyword_matches > 0:
                            theme_groups[theme_name].append(post)
                            # Score is based on keyword matches and engagement
                            theme_scores[theme_name] += keyword_matches * (1 + (engagement_score * 0.1))

            # Filter and sort themes
            valid_themes = []
            for theme_name, posts in theme_groups.items():
                if len(posts) >= 3:  # Require at least 3 posts per theme
                    # Sort posts within theme by engagement and relevance
                    sorted_posts = sorted(
                        posts,
                        key=lambda p: (
                            p.score + sum(c.score for c in comments_by_post.get(p.id, [])),
                            len(comments_by_post.get(p.id, []))
                        ),
                        reverse=True
                    )
                    
                    # Create theme
                    theme = Theme(
                        category=theme_name,
                        summary=self.theme_categories[theme_name]["description"],
                        audience_id=audience_id
                    )
                    
                    # Save theme first to get its ID
                    self.db.add(theme)
                    await self.db.commit()
                    await self.db.refresh(theme)
                    
                    # Add top posts to theme
                    for post in sorted_posts[:10]:  # Limit to top 10 posts per theme
                        theme_post = ThemePost(
                            theme_id=theme.id,
                            post_id=post.id,
                            relevance_score=post.score + sum(c.score for c in comments_by_post.get(post.id, []))
                        )
                        self.db.add(theme_post)
                    await self.db.commit()
                    
                    valid_themes.append(theme)
            
            if not valid_themes:
                raise ValueError("No themes could be generated from the available posts")
            
            # Sort themes by their theme_scores
            valid_themes.sort(key=lambda t: theme_scores[t.category], reverse=True)
            
            # Save themes to database using the existing session
            for theme in valid_themes:
                self.db.add(theme)
            await self.db.commit()
            
            return valid_themes

        except Exception as e:
            logger.error(f"Error in analyze_themes: {str(e)}")
            raise ValueError(f"Error analyzing themes: {str(e)}")

    def _calculate_relevance_score(self, post: RedditPost, category: str, comments: List[Comment]) -> float:
        """
        Calculate relevance score for a post in a theme category, incorporating comment data.
        
        Args:
            post: The RedditPost to score
            category: Theme category name
            comments: List of comments for this post
        
        Returns:
            Float between 0 and 1 indicating relevance
        """
        # Base score from post metrics
        base_score = post.engagement_score
        
        # Add comment contribution
        if comments:
            # Calculate average comment engagement
            avg_comment_engagement = sum(c.engagement_score for c in comments) / len(comments)
            
            # Weight comments more heavily for discussion-based themes
            comment_weight = 0.6 if category in ["Hot Discussions", "Advice Requests"] else 0.4
            
            # Combine post and comment scores
            combined_score = (base_score * (1 - comment_weight) + 
                            avg_comment_engagement * comment_weight)
        else:
            combined_score = base_score
        
        # Apply theme-specific boosts
        if category == "Hot Discussions":
            # Boost posts with high comment engagement
            if len(comments) > 10 and any(c.score > 50 for c in comments):
                combined_score *= 1.2
        
        elif category == "Advice Requests":
            # Boost posts where OP is active in comments
            op_comments = [c for c in comments if c.is_submitter]
            if op_comments:
                op_engagement = sum(c.engagement_score for c in op_comments) / len(op_comments)
                combined_score *= (1 + op_engagement * 0.3)
        
        elif category == "Pain & Anger":
            # Boost posts with high-scoring deep discussion
            deep_comments = [c for c in comments if c.depth > 1 and c.score > 10]
            if deep_comments:
                combined_score *= 1.15
        
        # Normalize to 0-1 range
        return min(1.0, combined_score)

    async def _generate_theme_summary(self, category: str, enhanced_posts: List[Dict]) -> str:
        """Generate a summary for a theme category using posts and their comments."""
        # Extract key information from posts and comments
        total_posts = len(enhanced_posts)
        total_comments = sum(len(p['comments']) for p in enhanced_posts)
        avg_score = sum(p['post'].score for p in enhanced_posts) / total_posts if total_posts > 0 else 0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0
        
        # Get top comments for context
        top_comments = []
        for post in enhanced_posts:
            top_comments.extend(post['top_comments'][:2])  # Take top 2 comments from each post
        top_comments.sort(key=lambda c: c.engagement_score, reverse=True)
        top_comments = top_comments[:5]  # Keep overall top 5 comments
        
        # TODO: Use OpenAI API to generate a more insightful summary using posts and comments
        summary = (
            f"Analysis of {total_posts} posts in {category} with {total_comments} comments. "
            f"Average post score: {avg_score:.1f}, Average comments per post: {avg_comments:.1f}. "
            f"Key discussion points from top comments: {', '.join(c.content[:100] + '...' for c in top_comments[:3])}"
        )
        
        return summary

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
                FROM redditposts rp
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

    async def analyze_posts(self, audience_id: int) -> None:
        """Analyze all posts for an audience."""
        if not self.db:
            raise ValueError("Database session not initialized")

        try:
            # Get recent posts
            posts = await self._get_recent_posts(audience_id)
            
            if not posts:
                raise ValueError("No posts found for this audience")
            
            # Analyze each post
            for post in posts:
                await self._analyze_post(post)
                
        except Exception as e:
            logger.error(f"Error analyzing posts: {str(e)}")
            raise 

    async def _get_post_analyses(self, post_ids: List[int]) -> List[PostAnalysis]:
        """Get post analyses for the given post IDs."""
        if not self.db:
            raise ValueError("Database session not initialized")

        try:
            result = await self.db.execute(
                select(PostAnalysis).where(PostAnalysis.post_id.in_(post_ids))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting post analyses: {str(e)}")
            return []

    async def _get_comments_for_posts(self, post_ids: List[int]) -> List[Comment]:
        """Get comments for the given post IDs."""
        if not self.db:
            raise ValueError("Database session not initialized")

        try:
            result = await self.db.execute(
                select(Comment)
                .where(Comment.post_id.in_(post_ids))
                .order_by(Comment.score.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return [] 