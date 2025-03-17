import logging
from datetime import datetime
from typing import List

from app.core.database import get_session
from app.models import Comment, Theme, ThemePost, ThemeQuestion
from app.schemas.theme_question import ThemeQuestion as ThemeQuestionSchema
from app.schemas.theme_question import ThemeQuestionCreate
from app.services.openai_service import (analyze_posts_for_answer,
                                         analyze_theme_content)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/theme-questions", tags=["theme-questions"])

@router.post("/", response_model=ThemeQuestionSchema)
async def create_theme_question(
    question: ThemeQuestionCreate,
    db: AsyncSession = Depends(get_session)
) -> ThemeQuestion:
    try:
        # Check if theme exists with eager loading of theme_posts, posts, and comments
        result = await db.execute(
            select(Theme)
            .options(
                joinedload(Theme.theme_posts)
                .joinedload(ThemePost.post)
                .joinedload(RedditPost.comments)
            )
            .where(Theme.id == question.theme_id)
        )
        theme = result.unique().scalar_one_or_none()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        # Convert posts and comments to dictionaries
        posts = []
        comments = []
        for theme_post in sorted(
            theme.theme_posts,
            key=lambda x: x.relevance_score,
            reverse=True
        )[:20]:  # Limit to 20 most relevant posts
            post = theme_post.post
            post_dict = {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "score": post.score,
                "num_comments": post.num_comments,
                "engagement_score": post.engagement_score,
                "relevance_score": theme_post.relevance_score
            }
            posts.append(post_dict)
            
            # Add comments for this post
            post_comments = sorted(
                post.comments,
                key=lambda x: x.engagement_score,
                reverse=True
            )[:10]  # Take top 10 comments per post
            
            for comment in post_comments:
                comment_dict = {
                    "id": comment.id,
                    "post_id": post.id,
                    "content": comment.content,
                    "score": comment.score,
                    "engagement_score": comment.engagement_score,
                    "is_submitter": comment.is_submitter,
                    "depth": comment.depth
                }
                comments.append(comment_dict)

        # Generate answer using enhanced analysis
        try:
            answer = await analyze_posts_for_answer(
                question=question.question,
                posts=posts,
                comments=comments
            )
        except Exception as e:
            error_msg = str(e)
            if "rate_limit_exceeded" in error_msg:
                raise HTTPException(
                    status_code=429,
                    detail="The question is too complex for the current rate limits. Please try a more specific question or try again later."
                )
            logger.error(f"Error generating answer: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate answer. Please try again later."
            )

        # Create and save the theme question
        theme_question = ThemeQuestion(
            theme_id=question.theme_id,
            question=question.question,
            answer=answer,
            created_at=datetime.utcnow()
        )
        db.add(theme_question)
        await db.commit()
        await db.refresh(theme_question)

        return theme_question

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating theme question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{theme_id}", response_model=List[ThemeQuestionSchema])
async def get_theme_questions(
    theme_id: int,
    db: AsyncSession = Depends(get_session)
) -> List[ThemeQuestion]:
    """Get all questions for a theme."""
    try:
        result = await db.execute(
            select(ThemeQuestion)
            .where(ThemeQuestion.theme_id == theme_id)
            .order_by(ThemeQuestion.created_at.desc())
        )
        questions = result.scalars().all()
        return questions
    except Exception as e:
        logger.error(f"Error getting theme questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{theme_id}/analyze", response_model=dict)
async def analyze_theme(
    theme_id: int,
    db: AsyncSession = Depends(get_session)
) -> dict:
    """Generate an AI-powered analysis of a theme's content."""
    try:
        # Get theme with posts and comments
        result = await db.execute(
            select(Theme)
            .options(
                joinedload(Theme.theme_posts)
                .joinedload(ThemePost.post)
                .joinedload(RedditPost.comments)
            )
            .where(Theme.id == theme_id)
        )
        theme = result.unique().scalar_one_or_none()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        # Prepare posts and comments data
        posts = []
        comments = []
        for theme_post in theme.theme_posts:
            post = theme_post.post
            posts.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "score": post.score,
                "num_comments": post.num_comments,
                "engagement_score": post.engagement_score,
                "relevance_score": theme_post.relevance_score
            })
            
            for comment in post.comments:
                comments.append({
                    "id": comment.id,
                    "post_id": post.id,
                    "content": comment.content,
                    "score": comment.score,
                    "engagement_score": comment.engagement_score,
                    "is_submitter": comment.is_submitter,
                    "depth": comment.depth
                })

        # Generate theme analysis
        analysis = await analyze_theme_content(
            theme_posts=posts,
            theme_comments=comments,
            category=theme.category
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing theme: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 