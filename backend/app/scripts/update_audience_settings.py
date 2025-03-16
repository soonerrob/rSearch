import asyncio
from datetime import datetime

from app.core.config import get_settings
from app.models import Audience
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select


async def update_audience_settings():
    """Update audience settings to include timeframe and posts_per_subreddit."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with AsyncSession(engine) as session:
        try:
            # Get all audiences
            result = await session.execute(select(Audience))
            audiences = result.scalars().all()
            
            # Update each audience
            for audience in audiences:
                if not hasattr(audience, 'timeframe') or not audience.timeframe:
                    audience.timeframe = 'week'  # Default timeframe
                if not hasattr(audience, 'posts_per_subreddit') or not audience.posts_per_subreddit:
                    audience.posts_per_subreddit = 100  # Default number of posts
                audience.updated_at = datetime.utcnow()
            
            await session.commit()
            print("Successfully updated audience settings")
            
        except Exception as e:
            await session.rollback()
            print(f"Error updating audience settings: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(update_audience_settings()) 