import logging
from datetime import datetime
from typing import List

from app.core.database import get_session
from app.models import Theme, ThemePost, ThemeQuestion
from app.schemas.theme_question import ThemeQuestion as ThemeQuestionSchema
from app.schemas.theme_question import ThemeQuestionCreate
from app.services.openai_service import analyze_posts_for_answer
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
        # Check if theme exists with eager loading of theme_posts and posts
        result = await db.execute(
            select(Theme)
            .options(joinedload(Theme.theme_posts).joinedload(ThemePost.post))
            .where(Theme.id == question.theme_id)
        )
        theme = result.unique().scalar_one_or_none()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        # Convert posts to dictionaries and limit to 20 most relevant posts
        posts = [
            {
                "title": theme_post.post.title,
                "selftext": theme_post.post.content,
                "score": theme_post.post.score,
                "num_comments": theme_post.post.num_comments
            }
            for theme_post in sorted(
                theme.theme_posts,
                key=lambda x: x.post.score + x.post.num_comments,
                reverse=True
            )[:20]
        ]

        # Get theme posts and generate answer
        try:
            answer = await analyze_posts_for_answer(
                question=question.question,
                posts=posts,
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

        # Create question with answer
        db_question = ThemeQuestion(
            theme_id=question.theme_id,
            question=question.question,
            answer=answer,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_recalculated_at=datetime.utcnow()
        )
        db.add(db_question)
        await db.commit()
        await db.refresh(db_question)

        return db_question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating theme question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create question. Please try again later."
        )

@router.get("/theme/{theme_id}", response_model=List[ThemeQuestionSchema])
async def get_theme_questions(theme_id: int, db: AsyncSession = Depends(get_session)):
    try:
        # Get theme first to verify it exists
        result = await db.execute(select(Theme).where(Theme.id == theme_id))
        theme = result.scalar_one_or_none()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")
            
        # Get questions for this theme, ordered by most recent first
        result = await db.execute(
            select(ThemeQuestion)
            .where(ThemeQuestion.theme_id == theme_id)
            .order_by(ThemeQuestion.created_at.desc())
        )
        questions = result.scalars().all()
        
        return questions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching theme questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch questions. Please try again."
        )

@router.post("/{question_id}/recalculate", response_model=ThemeQuestionSchema)
async def recalculate_answer(
    question_id: int,
    db: AsyncSession = Depends(get_session)
) -> ThemeQuestion:
    try:
        # Get question
        result = await db.execute(select(ThemeQuestion).where(ThemeQuestion.id == question_id))
        question = result.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Get theme and posts with eager loading
        result = await db.execute(
            select(Theme)
            .options(joinedload(Theme.theme_posts).joinedload(ThemePost.post))
            .where(Theme.id == question.theme_id)
        )
        theme = result.unique().scalar_one_or_none()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        # Convert posts to dictionaries and limit to 20 most relevant posts
        posts = [
            {
                "title": theme_post.post.title,
                "selftext": theme_post.post.content,
                "score": theme_post.post.score,
                "num_comments": theme_post.post.num_comments
            }
            for theme_post in sorted(
                theme.theme_posts,
                key=lambda x: x.post.score + x.post.num_comments,
                reverse=True
            )[:20]
        ]

        try:
            # Generate new answer
            answer = await analyze_posts_for_answer(
                question=question.question,
                posts=posts,
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

        # Update question
        question.answer = answer
        question.last_recalculated_at = datetime.utcnow()
        question.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(question)

        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating answer: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to recalculate answer. Please try again later."
        )

@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_session)
) -> None:
    # Get question
    result = await db.execute(select(ThemeQuestion).where(ThemeQuestion.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Delete question
    await db.delete(question)
    await db.commit() 