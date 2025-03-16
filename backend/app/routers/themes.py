from datetime import datetime
from typing import List

from app.dependencies import get_db_session
from app.models import Audience, Theme, ThemePost, ThemeQuestion
from app.schemas.theme import ThemeResponse
from app.services.themes import ThemeService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

router = APIRouter(
    prefix="/api/themes",
    tags=["themes"]
)

@router.get("/audience/{audience_id}", response_model=List[ThemeResponse])
async def get_audience_themes(
    audience_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get cached themes for a specific audience."""
    try:
        # Get the audience first to check its state
        result = await db.execute(select(Audience).where(Audience.id == audience_id))
        audience = result.scalar_one_or_none()
        if not audience:
            raise HTTPException(status_code=404, detail="Audience not found")
            
        if audience.is_collecting:
            raise HTTPException(
                status_code=202,
                detail="Initial data collection is in progress. Please wait."
            )
        
        # Get existing themes from database
        result = await db.execute(select(Theme).where(Theme.audience_id == audience_id))
        themes = result.scalars().all()
        
        if not themes:
            raise HTTPException(
                status_code=404,
                detail="No themes found. Initial data collection may have failed. Please try refreshing themes."
            )
        
        return themes
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audience/{audience_id}/refresh", response_model=List[ThemeResponse])
async def request_theme_refresh(
    audience_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Immediately reanalyze themes using existing posts with updated settings."""
    try:
        # First check if the audience exists
        result = await db.execute(select(Audience).where(Audience.id == audience_id))
        audience = result.scalar_one_or_none()
        if not audience:
            raise HTTPException(status_code=404, detail="Audience not found")
            
        if audience.is_collecting:
            raise HTTPException(
                status_code=202,
                detail="Initial data collection is in progress. Please wait."
            )
        
        # Get old theme IDs
        result = await db.execute(
            select(Theme.id).where(Theme.audience_id == audience_id)
        )
        old_theme_ids = [theme_id for theme_id, in result.all()]
        
        # Delete old themes and their associations
        if old_theme_ids:
            await db.execute(delete(ThemePost).where(ThemePost.theme_id.in_(old_theme_ids)))
            await db.execute(delete(Theme).where(Theme.id.in_(old_theme_ids)))
            await db.commit()
        
        # Create new themes
        theme_service = ThemeService(db)
        try:
            new_themes = await theme_service.analyze_themes(audience_id)
            return new_themes
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error refreshing themes: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in request_theme_refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))