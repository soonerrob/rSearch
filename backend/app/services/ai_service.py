"""Service for AI-powered analysis of themed content."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.models.audience import Audience
from app.models.post_analysis import PostAnalysis
from app.models.reddit_post import RedditPost
from app.models.theme import Theme, ThemePost
from app.models.theme_question import ThemeQuestion
from app.schemas.ai import AIResponse, Source
from app.services.openai_service import analyze_posts_for_answer
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered analysis of themed content."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the AI service."""
        self.db = db
        self.settings = get_settings()
    
    async def analyze_question(
        self,
        question: str,
        audience_id: int,
        theme_id: Optional[int] = None
    ) -> AIResponse:
        """Analyze a question about an audience or specific theme."""
        try:
            # 1. Get relevant content
            posts = await self._get_relevant_posts(audience_id, theme_id)
            if not posts:
                raise ValueError("No relevant posts found for analysis")
            
            # 2. Get post analyses for context
            post_ids = [post.id for post in posts]
            analyses = await self._get_post_analyses(post_ids)
            
            # 3. Prepare context for AI
            context = self._prepare_context(posts, analyses)
            
            # 4. Get AI response using OpenAI service
            response_dict = await analyze_posts_for_answer(
                question=question,
                posts=[{
                    "title": post.title,
                    "content": post.content,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "engagement_score": post.engagement_score
                } for post in posts]
            )
            
            # 5. Convert to AIResponse schema
            sources = [
                Source(
                    title=post.title,
                    score=post.score,
                    url=f"https://reddit.com{post.reddit_id}"
                )
                for post in posts[:3]  # Include top 3 posts as sources
            ]
            
            response = AIResponse(
                answer=response_dict["answer"],
                sources=sources,
                confidence=response_dict.get("confidence", 0.8),
                metadata={"analyzed_at": datetime.utcnow().isoformat()}
            )
            
            # 6. Save question if theme-specific
            if theme_id:
                await self._save_theme_question(question, response, theme_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing question: {e}")
            raise
    
    async def _get_relevant_posts(
        self,
        audience_id: int,
        theme_id: Optional[int] = None,
        limit: int = 50
    ) -> List[RedditPost]:
        """Get the most relevant posts for an audience."""
        try:
            # Build query starting with RedditPost and join through ThemePost to Theme
            query = (
                select(RedditPost)
                .select_from(RedditPost)
                .join(ThemePost, RedditPost.id == ThemePost.post_id)
                .join(Theme, Theme.id == ThemePost.theme_id)
                .where(Theme.audience_id == audience_id)
                .distinct()
            )

            # Add theme filter if specified
            if theme_id:
                query = query.where(Theme.id == theme_id)

            # Order by relevance and limit results
            query = (
                query.order_by(desc(ThemePost.relevance_score))
                .limit(limit)
            )

            result = await self.db.execute(query)
            posts = result.scalars().all()
            return posts

        except Exception as e:
            logger.error(f"Error getting relevant posts: {e}")
            return []
    
    async def _get_post_analyses(self, post_ids: List[int]) -> List[PostAnalysis]:
        """Get post analyses for a list of posts."""
        try:
            result = await self.db.execute(
                select(PostAnalysis)
                .where(PostAnalysis.post_id.in_(post_ids))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting post analyses: {e}")
            raise
    
    def _prepare_context(self, posts: List[RedditPost], analyses: List[PostAnalysis]) -> Dict:
        """Prepare context for AI analysis."""
        # Create lookup of post_id to analysis
        analysis_by_post = {
            analysis.post_id: analysis
            for analysis in analyses
        }
        
        # Prepare context with post content and metadata
        context = {
            "posts": [
                {
                    "title": post.title,
                    "content": post.content,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "themes": analysis_by_post.get(post.id).get_matching_themes() if post.id in analysis_by_post else [],
                    "keywords": analysis_by_post.get(post.id).get_keywords() if post.id in analysis_by_post else [],
                    "theme_scores": analysis_by_post.get(post.id).get_theme_scores() if post.id in analysis_by_post else {}
                }
                for post in posts
            ]
        }
        
        return context
    
    async def _save_theme_question(
        self,
        question: str,
        response: AIResponse,
        theme_id: int
    ) -> None:
        """Save a theme-specific question and its answer."""
        try:
            theme_question = ThemeQuestion(
                theme_id=theme_id,
                question=question,
                answer=response.answer,
                sources=[s.dict() for s in response.sources],
                confidence=response.confidence,
                metadata=response.metadata
            )
            self.db.add(theme_question)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error saving theme question: {e}")
            raise 